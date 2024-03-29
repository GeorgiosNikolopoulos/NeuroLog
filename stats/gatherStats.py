import json
from pathlib import Path
from statistics import mean
import argparse
import matplotlib.pyplot as plt
import numpy as np
import re


# open all projects and run the three methods
def main():
    with open(fileLoc) as json_file:
        logs = json.load(json_file)
        calculateGlobalStatistics(logs)
        calculateLevelStatistics(logs)
        calculateMsgStatistics(logs)


# is responsible for calculating all the Global level stats
def calculateGlobalStatistics(logs):
    listOfMsgLength = convertToListOfMsgLength(logs)
    # get all the logs that have less than 200 chars in them
    under200Length = list(filter(filterByMsgLengthUnder, logs))
    # plot them and save the graph
    plt.hist(convertToListOfMsgLength(under200Length))
    plt.ylabel("Number of logs")
    plt.xlabel("Msg length (chars)")
    plt.title("Distribution of Message length (< 200 chars)")
    plt.savefig("msgLength.png")
    # plt.show() # uncomment to show the interactive chart

    print("-----------------------------------------------")
    print("           GLOBAL   STATS FOLLOW               ")
    print("-----------------------------------------------")
    print("Total Number of Logs: " + str(len(logs)))
    print("Average Message Length: " + str(round(mean(listOfMsgLength), 2)))
    print("Min Message Length: " + str(min(listOfMsgLength)))
    print("Max Message Length: " + str(max(listOfMsgLength)))
    print("Histogram saved! " + str(len(under200Length)) + "/" + str(len(logs)) + " logs are displayed within it.")
    print("Quantile Stats: Q1:" + str(np.quantile(listOfMsgLength, 0.25)) + ", Q2: " + str(
        np.quantile(listOfMsgLength, 0.5)) + ", Q3: "
          + str(np.quantile(listOfMsgLength, 0.75)))


# Calculates stats based on log levels
def calculateLevelStatistics(logs):
    # use the filter functions to get subsections of the logs
    traceLogs = list(filter(filterByTrace, logs))
    debugLogs = list(filter(filterByDebug, logs))
    infoLogs = list(filter(filterByInfo, logs))
    warnLogs = list(filter(filterByWarn, logs))
    errorLogs = list(filter(filterByError, logs))
    fatalLogs = list(filter(filterByFatal, logs))

    print("-----------------------------------------------")
    print("              LEVEL STATS FOLLOW               ")
    print("-----------------------------------------------")
    print(
        f"Trace logs detected: {str(len(traceLogs))}. These represent {str(round(len(traceLogs) / len(logs)* 100,2) )}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(traceLogs)), 2))}.")
    print(
        f"Debug logs detected: {str(len(debugLogs))}. These represent {str(round(len(debugLogs) / len(logs) * 100, 2))}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(debugLogs)), 2))}.")
    print(
        f"Info logs detected: {str(len(infoLogs))}. These represent {str(round(len(infoLogs) / len(logs)* 100, 2))}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(infoLogs)), 2))}.")
    print(
        f"Warn logs detected: {str(len(warnLogs))}. These represent {str(round(len(warnLogs) / len(logs)* 100, 2))}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(warnLogs)), 2))}.")
    print(
        f"Error logs detected: {str(len(errorLogs))}. These represent {str(round(len(errorLogs) / len(logs)* 100, 2))}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(errorLogs)), 2))}.")
    print(
        f"Fatal logs detected: {str(len(fatalLogs))}. These represent {str(round(len(fatalLogs) / len(logs)* 100, 2))}"
        f"% of all logs. Average msg length for them: {str(round(mean(convertToListOfMsgLength(fatalLogs)), 2))}.")



def calculateMsgStatistics(logs):
    onlyTextLogs = list(filter(filterByMsgTextOnly, logs))
    onlyMethodLogs = list(filter(filterByContainsMethod, logs))
    print("-----------------------------------------------")
    print("                MSG STATS FOLLOW               ")
    print("-----------------------------------------------")
    print("Logs that have text only in their msg: " + str(len(onlyTextLogs)) + " (" + str(
        round((len(onlyTextLogs) / len(logs) * 100), 2)) + "%) of the whole data")
    print("Logs that have a method in their msg: " + str(len(onlyMethodLogs)) + " (" + str(
        round((len(onlyMethodLogs) / len(logs) * 100), 2)) + "%) of the whole data")


# returns a list containing ints, each int represents the length of a log msg
def convertToListOfMsgLength(logs):
    return list(map(lambda log: (len(log["msg"])), logs))


# Checks if the text contains a parenthesis (a method)
def filterByContainsMethod(log):
    pattern = "[\(\)]+"
    return bool(re.search(pattern, log["msg"]))


# Filters logs based on length (<200)
def filterByMsgLengthUnder(log):
    return len(log['msg']) <= 200


# Filters logs by allowing msges that contain text only
def filterByMsgTextOnly(log):
    # "\"[a-z:= A-Z]+\"$|\'[a-z:= A-Z]+\'$" allows for ' ' strings, but this seems to not be needed
    pattern = "\"[a-z:= A-Z]+\"$"
    return bool(re.match(pattern, log["msg"]))


# filter by log level methods follow

def filterByTrace(log):
    return log['severity'] == "trace"

def filterByDebug(log):
    return log['severity'] == "debug"


def filterByInfo(log):
    return log['severity'] == "info"

def filterByWarn(log):
    return log['severity'] == "warn"

def filterByError(log):
    return log['severity'] == "error"


def filterByFatal(log):
    return log['severity'] == "fatal"


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(
        description="Analyze a single JSON file extensively.")
    parser.add_argument("input_json", help="Location of json file. Please use full path",
                        type=str)

    args = parser.parse_args()
    fileLoc = Path(args.input_json)
    main()
