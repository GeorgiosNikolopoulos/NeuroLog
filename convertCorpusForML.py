import re
import shutil
from enum import Enum
import multiprocessing
from graph_pb2 import Graph
import argparse
from pathlib import Path
import json
from tqdm import tqdm
import gzip
import numpy as np
import concurrent.futures


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
            msg = logs[args.debug][2]
            print(graphLoc)
            print(convertGraph(graphLoc, severity, msg))
        else:
            # set up the output Paths
            outputTrainLogs = outputFolder / "trainLogs.jsonl"
            outputValidationLogs = outputFolder / "validationLogs.jsonl"
            outputTestLogs = outputFolder / "testLogs.jsonl"

            # Modify all logs if the flag is true.
            if args.disallow_same_class is True:
                logs = modifyLogsForSmokeTest(logs)

            # limit our log count
            if args.limit is not None:
                logs = logs[0:args.limit]
            # split the logs into our sets
            trainLogs, validationLogs, testLogs = splitLogs(logs)
            print(
                f"Split the data into: {len(trainLogs)} training logs, {len(validationLogs)} validation logs and {len(testLogs)} test logs!")
            print(f"Will use {multiprocessing.cpu_count()} of threads (should be 1 per CPU available)")

            # The following three blocks convert the sets using as many threads as there are CPU cores
            print("Starting generation of training set.")
            convertLogsAsync(trainLogs, outputTrainLogs)

            print("Done. Starting generation of validation set.")
            convertLogsAsync(validationLogs, outputValidationLogs)

            print("Done. Starting generation of testing set.")
            convertLogsAsync(testLogs, outputTestLogs)
            # Handle auto-zipping of generated files
            if args.convert:
                print("Zipping into gz format.")
                zipJSONL(outputTrainLogs, "trainLogs.jsonl.gz")
                zipJSONL(outputValidationLogs, "validationLogs.jsonl.gz")
                zipJSONL(outputTestLogs, "testLogs.jsonl.gz")
                print("Done. Deleting raw jsonl files.")
                outputTrainLogs.unlink()
                outputValidationLogs.unlink()
                outputTestLogs.unlink()
                print("All done! You can insert the generated files directly into graph2Sequence now.")
            else:
                print("All done! Please remember to gzip these files before feeding them into graphToSequence")
                print("If on linux, please run 'gzip -k trainLogs.jsonl && gzip -k validationLogs.jsonl && gzip -k "
                      "testLogs.jsonl'")
            if amlCTX is not None:
                print("Uploading to azure Output")
                amlCTX.upload_file(name="trainLogs.jsonl.gz", path_or_stream=str(outputFolder / "trainLogs.jsonl.gz"))
                amlCTX.upload_file(name="validationLogs.jsonl.gz",
                                   path_or_stream=str(outputFolder / "validationLogs.jsonl.gz"))
                amlCTX.upload_file(name="testLogs.jsonl.gz", path_or_stream=str(outputFolder / "testLogs.jsonl.gz"))
                print("Done!")


# Converts a set of logs using multiple threads. Writes the result to an output file
def convertLogsAsync(logs, outputFile):
    # set up our Executor
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        # Manual tqdm implementation so we have a progress bar
        with tqdm(total=len(logs), unit="graphs") as progress:
            futures = []
            for [graphLoc, severity, msgToken] in logs:
                # here is where we convert the graph
                future = executor.submit(convertGraph, graphLoc, severity, msgToken)
                future.add_done_callback(lambda p: progress.update())
                futures.append(future)
            results = []
            for future in futures:
                result = future.result()
                results.append(result)
        # better way to handle async execution, but no progress bar!
        # results = list(executor.map(convertFromGraphs, logs))
    # write the output to our file, then clean up memory (automaticly) when the function is over.
    with open(outputFile, "w") as outFile:
        for jsonLog in results:
            outFile.write(jsonLog)
            outFile.write("\n")


# part of the better way to handle async
def convertFromGraphs(log):
    graphLoc, severity = log
    return convertGraph(graphLoc, severity)


def zipJSONL(location, targetName):
    with open(location, 'rb') as f_in:
        with gzip.open(outputFolder / targetName, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def modifyLogsForSmokeTest(logs):
    logDict = {}
    returnLogs = []
    for log in logs:
        locationNoNumber = re.sub("\d+", "", log[0])
        if locationNoNumber in logDict:
            pass
        else:
            logDict[locationNoNumber] = True
            returnLogs.append(log)
    return returnLogs


def splitLogs(logs):
    if amlCTX is not None:
        def modifyLogs(log):
            graphLoc, severity, msg = log
            return [graphLoc.replace("modified_corpus/", args.corpus_location), severity, msg]

        logs = list(map(modifyLogs, logs))

    # Use numpy to split our arrays into the correct percentage
    logs = np.array(logs, dtype=object)
    trainData, testData = np.split(logs, [int(args.training_percent * len(logs))])
    trainData, validationData = np.split(trainData, [int(1.0 - args.validation_percent * len(logs))])

    # The following 2 blocks will automatically ensure that two logs belonging to the same file are not
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


def convertGraph(graphLoc, severity, msgToken):
    # return JSON structure visualized.
    returnJSON = {
        "backbone_sequence": [],
        "node_labels": [],
        "edges": {},
        "method_name": [],
        "log_node": -1
    }
    with open(graphLoc, "rb") as graphFile:
        g = Graph()
        g.ParseFromString(graphFile.read())
        nodes = g.node
        edges = g.edge
        # make a map of all the backbone nodes by looping over the edges and getting any node that
        # has a NEXT_TOKEN pointing to/from it
        backboneNodes = {}
        for edge in edges:
            if edge.type == 2:
                # overwrite, but thats ok!
                backboneNodes[edge.destinationId] = True
                backboneNodes[edge.sourceId] = True
        # Map of nodeId->Index. Used in step 3
        IdIndexDict = {}
        # Used to get the index of our special node to put it to the JSON
        specialLogNodeIndex = -1
        for index, node in enumerate(nodes):
            # got the special node
            if node.type == 17:
                specialLogNodeIndex = index
            # add the node's index to the id map
            IdIndexDict[node.id] = index
            # STEP 1) Create backbone_sequence by first checking if the node is a backbone node and then appending its
            # index to the array
            if node.id in backboneNodes:
                returnJSON["backbone_sequence"].append(index)

            # STEP 2) Create node_labels by appending the node contents to the array
            returnJSON["node_labels"].append(node.contents)
        # STEP 3) Create edges by parsing the edge data into the correct format
        returnDict = {}
        for edge in edges:
            type = EdgeType(edge.type).name
            if type not in returnDict:
                returnDict[type] = []
            sourceIndex = IdIndexDict[edge.sourceId]
            destinationIndex = IdIndexDict[edge.destinationId]
            returnDict[type].append([sourceIndex, destinationIndex])
        returnJSON["edges"] = returnDict
        # STEP 4) If we are trying to predict the logging statement, add the tokenized msg to the
        # prediction variable (method_name). Also put the logging level inside as well.
        # If we are trying to predict the severity, add the severity to the prediction variable only.
        if args.statement_generation:
            returnJSON["method_name"] = msgToken
            # TODO check if severity should be here
            #returnJSON["severity"] = severity
        else:
            returnJSON["method_name"].append(severity)
        # STEP 5) Add the index of the log node to the JSON
        returnJSON["log_node"] = specialLogNodeIndex
        return json.dumps(returnJSON)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts the generated modified corpus into the jsonl.gz file accepted by ptgnn.")
    parser.add_argument("--corpus_location", help="Location of the modified corpus folder.",
                        type=str, required=True)
    parser.add_argument("--training_percent", help="The percent of data that will be the training data (ex. 0.8). The "
                                                   "other 20 will be testing data",
                        type=float, required=True)
    parser.add_argument("--validation_percent", help="The percent of the TRAINING data that will be the validation set"
                                                     "(ex. a 0.8 0.2 will take 20%% of the TRAINING set, which is 80%% of "
                                                     "the whole data)",
                        type=float, required=True)
    parser.add_argument("-s", "--statement_generation", help="If set, the output data is the training data for logging"
                                                       "statement prediction, if false then it's for logging severity"
                                                       "prediction", action="store_true")
    parser.add_argument("--debug", help="Generate a single json file from a single proto file, to check the script's "
                                        "functionality. Takes an index location of the JSON file",
                        type=int)
    parser.add_argument("--output_folder", help="Output folder", type=str, required=True)
    parser.add_argument("-l", "--limit", help="Limit the number of logs to use from the JSON by x logs. A value of 100"
                                              "will only take the first 100 logs and split them in the train/validation/"
                                              "test sets.", type=int)
    parser.add_argument("-c", "--convert", help="GZip the generated jsonl files to prepare them for Graph2Sequence",
                        action="store_true")
    parser.add_argument("--aml", help="Indicate usage of Azure", action="store_true")
    parser.add_argument("--disallow_same_class", help="At the start of execution, filter all logs to only allow one"
                                                      "log per unique graph file (so if two logs both originate from "
                                                      "the same file, only leave one existing. Done to generate a fully"
                                                      "unique corpus, for a 'smoke' test.",
                        action="store_true")
    args = parser.parse_args()
    inputJSON = Path(args.corpus_location) / "severities.json"
    outputFolder = Path(args.output_folder)
    amlCTX = None
    if args.aml:
        from azureml.core.run import Run

        amlCTX = Run.get_context()
    if args.statement_generation:
        print("Starting generation of statement ML input set.")
    else:
        print("Starting generation of severity ML input set.")
    main()
