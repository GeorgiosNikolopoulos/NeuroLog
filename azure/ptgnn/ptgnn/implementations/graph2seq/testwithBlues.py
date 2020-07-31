#!/usr/bin/env python
"""
Usage:
    test_model.py [options] MODEL_FILENAME TEST_DATA_PATH

Options:
    --azure-info=<path>        Azure authentication information file (JSON). Used to load data from Azure storage.
    --max-num-epochs=<epochs>  The maximum number of epochs to run training for. [default: 100]
    --minibatch-size=<size>    The minibatch size. [default: 100]
    --restore-path=<path>      The path to previous model file for starting from previous checkpoint.
    --quiet                    Do not show progress bar.
    -h --help                  Show this screen.
    --debug                    Enable debug routines. [default: False]
"""
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
from docopt import docopt
from dpu_utils.utils import RichPath, run_and_debug
from jellyfish import jaro_winkler
from ptgnn.implementations.graph2seq.graph2seq import Graph2Seq, Graph2SeqModule
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.bleu_score import SmoothingFunction

def run(arguments):
    azure_info_path = arguments.get("--azure-info", None)

    data_path = RichPath.create(arguments["TEST_DATA_PATH"], azure_info_path)
    data = list(data_path.read_as_jsonl())

    model_path = Path(arguments["MODEL_FILENAME"])
    model, nn = Graph2Seq.restore_model(
        model_path, device="cpu"
    )  # type: Tuple[Graph2Seq, Graph2SeqModule]
    nn.reset_metrics()

    all_responses = model.greedy_decode(data, nn, device="cpu")
    num_elements = 0
    bleuScores1 = []
    bleuScores4 = []

    for (res_tokens, res_logprob), actual_data in zip(all_responses, data):
        num_elements += 1

        smoother = SmoothingFunction()
        reference = [actual_data["method_name"]]
        candidate = res_tokens
        bleuScore4 = sentence_bleu(reference, candidate, smoothing_function=smoother.method4)
        bleuScore1 = sentence_bleu(reference, candidate, weights=(1, 0, 0, 0), smoothing_function=smoother.method4)
        print(f"{actual_data['method_name']} --> {res_tokens} (B1:{bleuScore1}, B4:{bleuScore4})")

        bleuScores1.append(bleuScore1)
        bleuScores4.append(bleuScore4)
    bleuScores4 = np.array(bleuScores4)
    bleuScores1 = np.array(bleuScores1)
    print(f"Number of elements tested: {num_elements}")
    print(f"Average bleu1 score: {np.average(bleuScores1)}")
    print(f"Average bleu4 score: {np.average(bleuScores4)}")


if __name__ == "__main__":
    args = docopt(__doc__)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s"
    )
    run_and_debug(lambda: run(args), args.get("--debug", False))
