import json

import youtokentome as yttm
import sentencepiece as spm

def youtoken():
    bpe = yttm.BPE(model="statementPrediction.model")
    with open("../results/all_projects.json") as jsonf:
        logs = json.load(jsonf)
        with open("tokenizedExample.txt","w") as output:
            for log in logs:
                msg = log["msg"]
                tokenizedMsg = bpe.encode([msg], output_type=yttm.OutputType.SUBWORD)[0]
                output.write(f"{msg} ----> {str(tokenizedMsg)}\n")

def senterpiece():
    sp = spm.SentencePieceProcessor(model_file='spmModel.model')
    totalTokens = 0
    with open("../results/all_projects.json") as jsonf:
        logs = json.load(jsonf)
        with open("tokenizedExample.txt","w") as output:
            for log in logs:
                msg = log["msg"]
                tokenizedMsg = sp.encode([msg], out_type=str)[0]
                totalTokens += len(tokenizedMsg)
                output.write(f"{msg} ----> {str(tokenizedMsg)}\n")

if __name__ == "__main__":
    #youtoken()
    senterpiece()