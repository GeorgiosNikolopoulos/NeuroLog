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
    --predicting-statement     Set this if you are trying to predict statements instead of severity
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
    predictingStatement = arguments.get("--predicting-statement", None)

    azure_info_path = arguments.get("--azure-info", None)

    data_path = RichPath.create(arguments["TEST_DATA_PATH"], azure_info_path)
    data = list(data_path.read_as_jsonl())

    model_path = Path(arguments["MODEL_FILENAME"])
    model, nn = Graph2Seq.restore_model(
        model_path, device="cpu"
    )  # type: Tuple[Graph2Seq, Graph2SeqModule]
    nn.reset_metrics()

    all_responses = model.greedy_decode(data, nn, device="cpu")
    correct_elements, jw_sim, num_elements = 0, 0, 0
    sum_f1, sum_precision, sum_recall = 0.0, 0.0, 0.0


    bleuScores1 = []
    bleuScores4 = []
    for (res_tokens, res_logprob), actual_data in zip(all_responses, data):
        num_elements += 1

        if predictingStatement:
            smoother = SmoothingFunction()
            reference = [actual_data["method_name"]]
            candidate = res_tokens
            #Anything less than 2 will cause the smoother function to crash (division by 0). Use method 0, no smoothing
            #if this occurs.
            if(len(candidate) <= 1 or len(reference) <= 1):
                smoothingFunction = smoother.method0
            else:
                smoothingFunction = smoother.method4
            bleuScore4 = sentence_bleu(reference, candidate, smoothing_function=smoothingFunction)
            bleuScore1 = sentence_bleu(reference, candidate, weights=(1, 0, 0, 0), smoothing_function=smoothingFunction)
            bleuScores1.append(bleuScore1)
            bleuScores4.append(bleuScore4)

            print(f'{actual_data["method_name"]} -> {res_tokens} ({np.exp(res_logprob):.2f}, B1:{bleuScore1}, B4:{bleuScore4})')
        else:
            print(f'{actual_data["method_name"]} -> {res_tokens} ({np.exp(res_logprob):.2f})')

        jw_sim += jaro_winkler("".join(actual_data["method_name"]), "".join(res_tokens))
        if actual_data["method_name"] == res_tokens:
            correct_elements += 1
        res_tokens = set(res_tokens)
        res_tokens.discard("%UNK%")
        ground_tokens = set(actual_data["method_name"])
        if len(res_tokens) > 0:
            precision = len(res_tokens & ground_tokens) / len(res_tokens)
        else:
            precision = 0
        recall = len(res_tokens & ground_tokens) / len(ground_tokens)

        if precision + recall > 0:
            sum_f1 += 2 * recall * precision / (precision + recall)
            sum_precision += precision
            sum_recall += recall

    print(f"Acc {correct_elements / num_elements: %}  ({correct_elements}/{num_elements})")
    print(f"F1 {sum_f1 / num_elements}")
    print(f"Pr {sum_precision / num_elements}  Re {sum_recall / num_elements}")
    print(f"JW Sim {jw_sim / num_elements}")

    if predictingStatement:
        print("Statement Prediction:")
        bleuScores4 = np.array(bleuScores4)
        bleuScores1 = np.array(bleuScores1)
        print(f"Average bleu1 score: {np.average(bleuScores1)}")
        print(f"Average bleu4 score: {np.average(bleuScores4)}")


if __name__ == "__main__":
    args = docopt(__doc__)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)-15s %(name)-5s %(levelname)-8s %(message)s"
    )
    run_and_debug(lambda: run(args), args.get("--debug", False))
