import glob
import json
import os

def main():
    #Path of results
    path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\detecting-log-statements\\results\\individual_results"
    # Grab all the files
    files = [f for f in glob.glob(path + "**/*.json", recursive=True)]
    for fileLocation in files:
        with open(fileLocation, "rb") as f:
            # Get the file name (removing the rest of the directory)
            head, fileName = os.path.split(fileLocation)
            logs = json.load(f)
            #Calculate and print stats
            traceLogs = list(filter(filterByTrace, logs))
            debugLogs = list(filter(filterByDebug, logs))
            infoLogs = list(filter(filterByInfo, logs))
            warnLogs = list(filter(filterByWarn, logs))
            errorLogs = list(filter(filterByError, logs))
            fatalLogs = list(filter(filterByFatal, logs))
            print("For : " + fileName + " :")
            print("Trace logs: " + str(len(traceLogs)))
            print("Debug logs: " + str(len(debugLogs)))
            print("Info logs: " + str(len(infoLogs)))
            print("Warn logs: " + str(len(warnLogs)))
            print("Error logs: " + str(len(errorLogs)))
            print("Fatal logs: " + str(len(fatalLogs)))
            print("Total logs: " + str(len(logs)))

# Copy pasted filter methods from gatherStats.py

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
