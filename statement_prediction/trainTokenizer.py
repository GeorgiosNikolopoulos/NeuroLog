import json
from pathlib import Path

import argparse
import youtokentome as yttm


def main():
    trainDataPath = Path("trainData.txt")
    vocabSize = 20000
    print("Generating train text...", end="")
    with open(inputPath) as jsonf:
        logs = json.load(jsonf)
        with open(trainDataPath, "w") as trainData:
            for log in logs:
                trainData.write(log["msg"] + "\n")
    print("Done!")
    model_path = "statementPrediction.model"

    # Generating random text
    test_text = "\"prepending / to %s. It should be placed in the root of the classpath rather than in a package.\",configurationResourceName"
    # Training model
    yttm.BPE.train(data=str(trainDataPath), vocab_size=vocabSize, model=model_path)
    print("Model trained!")
    # Loading model
    bpe = yttm.BPE(model=model_path)
    print(f"Using following test string: {test_text}. Output follows.")
    print(bpe.encode([test_text], output_type=yttm.OutputType.SUBWORD)[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a tokenizer model that is used to convert the logging message to tokens that can be fed"
                    "to ptgnn.")
    parser.add_argument("input_json", help="Location of the modified corpus JSON file.",
                        type=str)
    args = parser.parse_args()
    inputPath = Path(args.input_json)
    main()
