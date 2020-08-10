import json
from pathlib import Path

import argparse
import youtokentome as yttm
import sentencepiece as spm



symbolsToTokenize = []

def trainYouToken():
    model_path = "statementPrediction.model"
    test_text = "\"prepending / to %s. It should be placed in the root of the classpath rather than in a package.\"," \
                "configurationResourceName "
    # Training model
    yttm.BPE.train(data=str(trainDataPath), vocab_size=vocabSize, model=model_path)
    print("Model trained!")
    # Loading model
    bpe = yttm.BPE(model=model_path)
    print(f"Using following test string: {test_text}. Output follows.")
    print(bpe.encode([test_text], output_type=yttm.OutputType.SUBWORD)[0])

def trainSenterpiece():
    spm.SentencePieceTrainer.train(input=str(trainDataPath), model_prefix="spmModel",vocab_size=vocabSize,
                                   user_defined_symbols=symbolsToTokenize)
    print("Model generated, test follows:")
    test_text = "\"prepending / to %s. It should be placed in the root of the classpath rather than in a package.\"," \
                "configurationResourceName "
    sp = spm.SentencePieceProcessor(model_file='spmModel.model')
    tokenizedMsg = sp.encode([test_text], out_type=str)[0]
    print(f"Using following test string: {test_text}. Output follows.")
    print(tokenizedMsg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train a tokenizer model that is used to convert the logging message to tokens that can be fed"
                    "to ptgnn.")
    parser.add_argument("train_file", help="Location of the train data txt file",
                        type=str)
    parser.add_argument("vocab_size", help="Vocabulary size to pass to senterpiece.", type=int)
    parser.add_argument("char_cover", help="Character coverage to pass to senterpiece, between 0.0 and 1.0",type=float)
    args = parser.parse_args()
    trainDataPath = Path(args.train_file)
    vocabSize = args.vocab_size
    charCover = args.char_cover
    trainSenterpiece()
