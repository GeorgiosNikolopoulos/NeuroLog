import json
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np
import re

# open all projects and run the three methods
def main():
    with open('all_projects.json') as json_file:
        logs = json.load(json_file)
        calculateGlobalStatistics(logs)
        calculateLevelStatistics(logs)
        calculateMsgStatistics(logs)

# is responsible for calculating all the Global level stats
def calculateGlobalStatistics(logs):
    listOfMsgLength = convertToListOfMsgLength(logs)
    # get all the logs that have less than 200 chars in them
    under200Length = list(filter(filterByMsgLengthUnder,logs))
    # plot them and save the graph
    plt.hist(convertToListOfMsgLength(under200Length))
    plt.ylabel("Number of logs")
    plt.xlabel("Msg length (chars)")
    plt.title("Distribution of Message length (< 200 chars)")
    plt.savefig("msgLength.png")
    #plt.show() # uncomment to show the interactive chart

    print("-----------------------------------------------")
    print("           GLOBAL   STATS FOLLOW               ")
    print("-----------------------------------------------")
    print("Total Number of Logs: " + str(len(logs)))
    print("Average Message Length: " + str(round(mean(listOfMsgLength),2)))
    print("Min Message Length: " + str(min(listOfMsgLength)))
    print("Max Message Length: " + str(max(listOfMsgLength)))
    print("Histogram saved! " + str(len(under200Length)) + "/" + str(len(logs)) + " logs are displayed within it.")
    print("Quantile Stats: Q1:" + str(np.quantile(listOfMsgLength,0.25)) + ", Q2: " + str(np.quantile(listOfMsgLength,0.5)) + ", Q3: "
          + str(np.quantile(listOfMsgLength,0.75)))

# Calculates stats based on log levels
def calculateLevelStatistics(logs):
    # use the filter functions to get subsections of the logs
    traceLogs = list(filter(filterByTrace,logs))
    debugLogs = list(filter(filterByDebug,logs))
    infoLogs = list(filter(filterByInfo,logs))
    warnLogs = list(filter(filterByWarn,logs))
    errorLogs = list(filter(filterByError,logs))
    fatalLogs = list(filter(filterByFatal,logs))

    print("-----------------------------------------------")
    print("              LEVEL STATS FOLLOW               ")
    print("-----------------------------------------------")
    print("Trace logs detected: " + str(len(traceLogs)) + ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(traceLogs)),2)))
    print("Debug logs detected: " + str(len(debugLogs)) + ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(debugLogs)),2)))
    print("Info logs detected:  " + str(len(infoLogs)) + ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(infoLogs)),2)))
    print("Warn logs detected:  " + str(len(warnLogs)) + ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(warnLogs)),2)))
    print("Error logs detected: " + str(len(errorLogs))+ ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(errorLogs)),2)))
    print("Fatal logs detected: " + str(len(fatalLogs))+ ". Average msg length for them: " + str(round(mean(convertToListOfMsgLength(fatalLogs)),2)))

def calculateMsgStatistics(logs):
    onlyTextLogs = list(filter(filterByMsgTextOnly,logs))
    onlyMethodLogs = list(filter(filterByContainsMethod,logs))
    print("-----------------------------------------------")
    print("                MSG STATS FOLLOW               ")
    print("-----------------------------------------------")
    print("Logs that have text only in their msg: " + str(len(onlyTextLogs)) + " (" + str(round((len(onlyTextLogs) / len(logs) * 100),2)) + "%) of the whole data")
    print("Logs that have a method in their msg:" + str(len(onlyMethodLogs)) + " (" + str(round((len(onlyMethodLogs) / len(logs) * 100),2)) + "%) of the whole data")

# returns a list containing ints, each int represents the length of a log msg
def convertToListOfMsgLength(logs):
    return list(map(lambda log : (len(log["msg"])),logs))

# Checks if the text contains a parenthesis (a method)
def filterByContainsMethod(log):
    pattern = "[\(\)]+"
    return bool(re.search(pattern,log["msg"]))


# Filters logs based on length (<200)
def filterByMsgLengthUnder(log):
    return len(log['msg']) <= 200

# Filters logs by allowing msges that contain text only
def filterByMsgTextOnly(log):
    # "\"[a-z:= A-Z]+\"$|\'[a-z:= A-Z]+\'$" allows for ' ' strings, but this seems to not be needed
    pattern = "\"[a-z:= A-Z]+\"$"
    return bool(re.match(pattern,log["msg"]))


# filter by log level methods follow

def filterByTrace(log):
    if log['severity'] == "trace":
        return True
    else:
        return False


def filterByDebug(log):
    if log['severity'] == "debug":
        return True
    else:
        return False

def filterByInfo(log):
    if log['severity'] == "info":
        return True
    else:
        return False


def filterByWarn(log):
    if log['severity'] == "warn":
        return True
    else:
        return False

def filterByError(log):
    if log['severity'] == "error":
        return True
    else:
        return False

def filterByFatal(log):
    if log['severity'] == "fatal":
        return True
    else:
        return False

if __name__ == "__main__":
    main()