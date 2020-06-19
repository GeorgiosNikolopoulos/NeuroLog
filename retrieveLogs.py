import os
import sys
import glob
import json
from tqdm import tqdm
from pathlib import Path
import argparse

from graph_pb2 import Graph
from graph_pb2 import FeatureNode



class Log:
    def __init__(self, severity, msg, lineLoc, fileLoc, rootID):
        self.severity = severity
        self.msg = msg
        self.lineLoc = lineLoc
        self.fileLoc = fileLoc
        self.rootId = rootID

    # Print the class correctly
    def __str__(self):
        return str(self.__dict__)


logLevels = [
    "trace",
    "debug",
    "info",
    "warn",
    "error",
    "fatal"
]


# Detects Log4j, LogBack,slf4j, Juli (Tomcat's custom implementation of java.util.logging) and Jboss (Hibernate)
def detectLogs(graph):
    nodes = graph.node
    # Using while loop to keep track of array index (its required)
    results = []
    length = len(nodes)
    for i in range(length):
        node = nodes[i]
        if node.contents == "logger" or node.contents == "log" or node.contents == "LOG":
            # get the log level by moving down two elements in the array (DOT followed by the level)
            severity = nodes[i + 2].contents
            # make it lower
            severity = severity.lower()
            # address jboss on this level instead of further down (makes life easier)
            severity = addressjBoss(severity)
            # verify the log level
            if verifyLogLevel(severity):
                # isolate the message
                msg = isolateMsg(nodes, i + 4)
                # Avoid false positives. If they occur, then the ENTIRE file (10k+ nodes) gets written.
                if len(msg) <= 1500:
                    fileLoc = graph.sourceFile
                    # remove false location data (and make it relative to the corpus)
                    fileLoc = fileLoc.replace('/local/data/Desktop/java-corpus-utils/java_projects-waiting/', '')
                    fileLoc = fileLoc.replace('/local/data/Desktop/java-corpus-utils/java_projects/', '')
                    lineLoc = node.startLineNumber
                    rootID = node.id
                    log = Log(severity, msg, lineLoc, fileLoc, rootID)
                    results.append(log)
    return results


# Converts the graph content markets into their respective string
def convertContentToString(content):
    if content == "PLUS":
        return " + "
    elif content == "DOT":
        return "."
    elif content == "COLON":
        return ":"
    elif content == "COMMA":
        return ","
    elif content == "LPAREN":
        return "("
    elif content == "RPAREN":
        return ")"
    else:
        return content


# Isolate the msg from the nodes provided
def isolateMsg(nodes, startOfStatement):
    # get the nodes STARTING at the msg
    startNodes = nodes[startOfStatement:]
    length = len(startNodes)
    endLocation = 0
    for i in range(length):
        node = startNodes[i]
        # found a semicolon, statemnt is over
        if node.contents == "SEMI":
            # go back an element from the semicolon
            endLocation = i - 1
            break
    # grab the nodes that contain the statement
    statementNodes = startNodes[0: endLocation]
    msg = ""
    # Extract the msg and return it
    for node in statementNodes:
        msg = msg + convertContentToString(node.contents)
    return msg


# Hibernate decided to have custom log functions. This parses them into standard log levels
def addressjBoss(logLevel):
    if logLevel == "debugf" or logLevel == "debufv":
        return "debug"
    elif logLevel == "errorf" or logLevel == "errorv":
        return "error"
    # fatal === error
    elif logLevel == "fatalf" or logLevel == "fatalv":
        return "fatal"
    elif logLevel == "infof" or logLevel == "infov":
        return "info"
    elif logLevel == "tracef" or logLevel == "tracev":
        return "trace"
    elif logLevel == "warnf" or logLevel == "warnv":
        return "warn"
    else:
        return logLevel


# Verify there is a valid log level
def verifyLogLevel(logLevel):
    # content is one of the log levels (and not a function, ex logger.isInfoEnabled())
    if logLevel in logLevels:
        return True
    else:
        return False


def main():
    # https://mkyong.com/python/python-how-to-list-all-files-in-a-directory/
    # Get all files within the directory of the path
    files = [f for f in glob.glob(str(path) + "/**/*.java.proto", recursive=True)]
    if len(files) == 0:
        print("No java.proto files found, are you inputing a correct folder?")
        exit(0)
    print("Found " + str(len(files)) + " proto files, starting analysis...")
    results = []

    # if we are using verbose, don't display the bar (everything will print)
    if verbose:
        for f in files:
            results = results + runAnalysis(f)
    else:
        # Use tqdm to dispay a nice progress bar, requires manual for loop instead of for f in files
        for file in tqdm(files, unit="files"):
            results = results + runAnalysis(file)
    if verbose:
        for result in results:
            print(result)
    print("Execution finished, number of logs found: " + str(len(results)))

    # Write to JSON
    if args.name is None:
        outputName = "result"
    else:
        outputName = args.name

    if args.output is None:
        print("No output location specified, writing to script location")
        output = outputName + ".json"
    else:
        output = str(Path(args.output)) + "/" + outputName + ".json"

    with open(output, 'w') as outfile:
        json.dump([ob.__dict__ for ob in results], outfile)
    print("Data written to file!")


def runAnalysis(fileLocation):
    with open(fileLocation, "rb") as f:
        if verbose:
            print("Opening " + fileLocation, end='')

        g = Graph()
        g.ParseFromString(f.read())
        logs = detectLogs(g)
        if verbose:
            print(" ------- Number of logs found: " + str(len(logs)))
        return logs


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(description="Detect log statements in java protocol buffer files")
    parser.add_argument("input_folder", help="Root folder containing all protocol buffer files. Please use full path", type=str)
    parser.add_argument("-o", "--output", help="Output folder to write to, will default to script location", type=str)
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action="store_true")
    parser.add_argument("-n", "--name", help="Name of output JSON file. Do not include extension")
    args = parser.parse_args()
    verbose = args.verbose
    path = Path(args.input_folder)
    main()
