import re
import shutil
from enum import Enum

from graph_pb2 import Graph
import argparse
from pathlib import Path
import json
from tqdm import tqdm
import gzip
import numpy as np

# Class to help with Edge name conversion
class EdgeType(Enum):
    ASSOCIATED_TOKEN = 1
    NEXT_TOKEN = 2
    AST_CHILD = 3
    NONE = 4
    LAST_WRITE = 5
    LAST_USE = 6
    COMPUTED_FROM = 7
    RETURNS_TO = 8
    FORMAL_ARG_NAME = 9
    GUARDED_BY = 10
    GUARDED_BY_NEGATION = 11
    LAST_LEXICAL_USE = 12
    COMMENT = 13
    ASSOCIATED_SYMBOL = 14
    HAS_TYPE = 15
    ASSIGNABLE_TO = 16
    METHOD_SIGNATURE = 17


def main():
    # open our JSON
    with open(inputJSON) as jsonf:
        # load the logs
        logs = json.load(jsonf)
        # we're debugging
        if args.debug is not None:
            # get the single graph and convert it.
            graphLoc = logs[args.debug][0]
            severity = logs[args.debug][1]
            print(convertGraph(graphLoc, severity))
        else:
            # set up the output Paths
            outputTrainLogs = outputFolder / "trainLogs.jsonl"
            outputValidationLogs = outputFolder / "validationLogs.jsonl"
            outputTestLogs = outputFolder / "testLogs.jsonl"
            # limit our log count
            if args.limit is not None:
                logs = logs[0:args.limit]
            # split the logs into our sets
            trainLogs, validationLogs, testLogs = splitLogs(logs)
            print(
                f"Split the data into: {len(trainLogs)} training logs, {len(validationLogs)} validation logs and {len(testLogs)} test logs!")
            print("Starting generation of training set.")
            # Each  block handles calculating and writing of it's respective set to a jsonl file
            with open(outputTrainLogs, "w") as outFile:
                for [graphLoc, severity] in tqdm(trainLogs, unit="logs"):
                    result = convertGraph(graphLoc, severity)
                    outFile.write(result)
                    outFile.write("\n")
            print("Done. Starting generation of validation set.")
            with open(outputValidationLogs, "w") as outFile:
                for [graphLoc, severity] in tqdm(validationLogs, unit="logs"):
                    result = convertGraph(graphLoc, severity)
                    outFile.write(result)
                    outFile.write("\n")
            print("Done. Starting generation of testing set.")
            with open(outputTestLogs, "w") as outFile:
                for [graphLoc, severity] in tqdm(testLogs):
                    result = convertGraph(graphLoc, severity)
                    outFile.write(result)
                    outFile.write("\n")
            # Handle auto-zipping of generated files
            if args.convert:
                print("Zipping into gz format.")
                with open(outputTrainLogs, 'rb') as f_in:
                    with gzip.open(outputFolder / "trainLogs.jsonl.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                with open(outputValidationLogs, 'rb') as f_in:
                    with gzip.open(outputFolder / "validationLogs.jsonl.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                with open(outputTestLogs, 'rb') as f_in:
                    with gzip.open(outputFolder / "testLogs.jsonl.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print("Done. Deleting raw jsonl files.")
                outputTrainLogs.unlink()
                outputValidationLogs.unlink()
                outputTestLogs.unlink()
                print("All done! You can insert the generated files directly into graph2Sequence now.")
            else:
                print("All done! Please remember to gzip these files before feeding them into graphToSequence")
                print("If on linux, please run 'gzip -k trainLogs.jsonl && gzip -k validationLogs.jsonl && gzip -k "
                      "testLogs.jsonl'")


def splitLogs(logs):
    # Use numpy to split our arrays into the correct percentage
    logs = np.array(logs)
    trainData, testData = np.split(logs, [int(args.training_percent * len(logs))])
    trainData, validationData = np.split(trainData, [int(1.0 - args.validation_percent * len(logs))])

    # The following 2 blocks will automaticly ensure that two logs belonging to the same file are not
    # split across two sets (either train-validate or validate-test
    trainDataAdjusted = False
    validationDataAdjusted = False
    # while we are still adjusting
    while not trainDataAdjusted:
        # get the last file name of the train set...
        lastTrainFileName = re.sub("\d+", "", Path(trainData[-1][0]).name)
        # ...and the first file name of the validate set
        firstValidateFileName = re.sub("\d+", "", Path(validationData[0][0]).name)
        # if the name match (we've removed numbers)
        if lastTrainFileName in firstValidateFileName:
            # stack the train data tuple with the first element of the validation data tuple
            trainData = np.vstack((trainData, validationData[0]))
            # Remove the first element of hte validation tuple
            validationData = validationData[1:]
        # if teh names do not match, we are good to go!
        else:
            trainDataAdjusted = True
    # Same logic as above, only for the validate-test sets
    while not validationDataAdjusted:
        lastValidateFileName = re.sub("\d+", "", Path(validationData[-1][0]).name)
        firstTestFileName = re.sub("\d+", "", Path(testData[0][0]).name)
        if lastValidateFileName in firstTestFileName:
            validationData = np.vstack((validationData, testData[0]))
            testData = testData[1:]
        else:
            validationDataAdjusted = True
    # shuffle everything!
    np.random.shuffle(trainData)
    np.random.shuffle(validationData)
    np.random.shuffle(testData)
    return trainData, validationData, testData


def convertGraph(graphLoc, severity):
    # return JSON structure visualized.
    returnJSON = {
        "backbone_sequence": [],
        "node_labels": [],
        "edges": {},
        "method_name": []
    }
    with open(graphLoc, "rb") as graphFile:
        g = Graph()
        g.ParseFromString(graphFile.read())
        nodes = g.node
        edges = g.edge

        for index, node in enumerate(nodes):
            # STEP 1) Create backbone_sequence by first checking if the node is a backbone node and then appending its
            # index to the array
            if nodeIsBackbone(node, edges):
                returnJSON["backbone_sequence"].append(index)

            # STEP 2) Create node_labels by appending the node contents to the array
            returnJSON["node_labels"].append(node.contents)
        # STEP 3) Create edges by parsing the edge data into the correct format
        returnJSON["edges"] = convertEdges(nodes, edges)
        # STEP 4) Add the correct level that the AI should predict
        returnJSON["method_name"].append(severity)
        return json.dumps(returnJSON)


# checks if the node is a backbone node (does not belong to AST)
def nodeIsBackbone(node, edges):
    nextTokenEdges = list(
        filter(lambda edge: edge.type == 2 and (edge.destinationId == node.id or edge.sourceId == node.id),
               edges))
    return len(nextTokenEdges) != 0


def convertEdges(nodes, edges):
    returnDict = {}
    for edge in edges:
        type = EdgeType(edge.type).name
        if type not in returnDict:
            returnDict[type] = []
        # returnDict[type].append([edge.sourceId, edge.destinationId])
        sourceIndex = -1
        destinationIndex = -1
        for index, node in enumerate(nodes):
            if node.id == edge.sourceId:
                sourceIndex = index
            if node.id == edge.destinationId:
                destinationIndex = index
            if sourceIndex != -1 and destinationIndex != -1:
                break
        returnDict[type].append([sourceIndex, destinationIndex])
    return returnDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts the generated modified corpus into the jsonl.gz file accepted by ptgnn.")
    parser.add_argument("input_json", help="Location of the modified corpus JSON file.",
                        type=str)
    parser.add_argument("--debug", help="Generate a single json file from a single proto file, to check the script's "
                                        "functionality. Takes an index location of the JSON file",
                        type=int)
    parser.add_argument("-l", "--limit", help="Limit the number of logs to use from the JSON by x logs. A value of 100"
                                              "will only take the first 100 logs and split them in the train/validation/"
                                              "test sets.", type=int)
    parser.add_argument("-c", "--convert", help="GZip the generated jsonl files to prepare them for Graph2Sequence",
                        action="store_true")
    parser.add_argument("training_percent", help="The percent of data that will be the training data (ex. 0.8). The "
                                                 "other 20 will be testing data",
                        type=float)
    parser.add_argument("validation_percent", help="The percent of the TRAINING data that will be the validation set"
                                                   "(ex. a 0.8 0.2 will take 20% of the TRAINING set, which is 80% of "
                                                   "the whole data)",
                        type=float)
    parser.add_argument("output_folder", help="Output folder", type=str)
    args = parser.parse_args()
    inputJSON = Path(args.input_json)
    outputFolder = Path(args.output_folder)
    main()
