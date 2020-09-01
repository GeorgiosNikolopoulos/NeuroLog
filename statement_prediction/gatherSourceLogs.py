import argparse
import glob
import json
import re
from tqdm import tqdm
from pathlib import Path

# Gather logging statements from multiple source-code projects. Kind of dirty in the way it does it, but it works
# and is actually very fast, so it's ok!
def main():
    logsWithProject = []
    root = path.name
    # get all the java files
    files = glob.glob(str(path) + "/**/*.java", recursive=True)
    for file in tqdm(files):
        with open(file) as javaFile:
            # do some regex to find the project name and any logs
            project = re.findall(root + "/\w+", file)[0].replace(root + "/", "")
            tempLogs = []
            contents = javaFile.read()
            tempLogs += re.findall('logger\.trace\(.+\);', contents)
            tempLogs += re.findall('logger\.debug\(.+\);', contents)
            tempLogs += re.findall('logger\.info\(.+\);', contents)
            tempLogs += re.findall('logger\.warn\(.+\);', contents)
            tempLogs += re.findall('logger\.error\(.+\);', contents)
            tempLogs += re.findall('logger\.fatal\(.+\);', contents)

            tempLogs += re.findall('LOGGER\.trace\(.+\);', contents)
            tempLogs += re.findall('LOGGER\.debug\(.+\);', contents)
            tempLogs += re.findall('LOGGER\.info\(.+\);', contents)
            tempLogs += re.findall('LOGGER\.warn\(.+\);', contents)
            tempLogs += re.findall('LOGGER\.error\(.+\);', contents)
            tempLogs += re.findall('LOGGER\.fatal\(.+\);', contents)
            # we found some logs, append them
            if len(tempLogs) > 0:
                for tempLog in tempLogs:
                    logsWithProject.append([project, tempLog])
    # extract pure logs so we can feed them into the map function
    tempLogs = []
    for loc, logMsg in logsWithProject:
        tempLogs.append(logMsg)

    logs = list(map(lambda x: x.replace("LOGGER.", "").replace("logger.", ""), tempLogs))
    logs = list(map(convertLog, logs))
    # write out the train data for the tokenizer
    with open("trainData.txt", "w") as output:
        with open(inputJSON) as jsonf:
            JSONlogs = json.load(jsonf)
            for log in JSONlogs:
                output.write(log["msg"] + "\n")
        print(f"Found {len(logs)} logs! Will also write {len(JSONlogs)} as well.")
        for log in logs:
            output.write(log["msg"] + "\n")
        print(f"Wrote {(len(logs)) + len(JSONlogs)} logs to tokenization training file!")
    # Write out the TSV file
    with open("logs.tsv", "w") as output:
        # Header
        output.write(f"project\tseverity\tmsg\n")
        # use the JSON to write the extra logs we discovered in the Graph files
        with open(inputJSON) as jsonf:
            JSONlogs = json.load(jsonf)
            for log in JSONlogs:
                projectName = log["fileLoc"].split("/")[0]
                msg = log["msg"].replace("\t", "")
                output.write(f"{projectName}\t{log['severity']}\t{msg}\n")
        # write out the logs we found in the source code
        for index,log in enumerate(logs):
            projectName = logsWithProject[index][0]
            output.write(f'{projectName}\t{log["severity"]}\t{log["msg"]}\n')


def convertLog(log):
    returnDict = {

    }
    if "trace" in log:
        returnDict["severity"] = "trace"
        returnDict["msg"] = log.replace("trace(", "").replace(");", "").replace("\t", "")
    elif "debug" in log:
        returnDict["severity"] = "debug"
        returnDict["msg"] = log.replace("debug(", "").replace(");", "").replace("\t", "")
    elif "info" in log:
        returnDict["severity"] = "info"
        returnDict["msg"] = log.replace("info(", "").replace(");", "").replace("\t", "")
    elif "warn" in log:
        returnDict["severity"] = "warn"
        returnDict["msg"] = log.replace("warn(", "").replace(");", "").replace("\t", "")
    elif "error" in log:
        returnDict["severity"] = "error"
        returnDict["msg"] = log.replace("error(", "").replace(");", "").replace("\t", "")
    elif "fatal" in log:
        returnDict["severity"] = "fatal"
        returnDict["msg"] = log.replace("fatal(", "").replace(");", "").replace("\t", "")
    return returnDict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This file does 2 things: First it checks all java files inside a"
                                                 "folder for logging statements. Then, it uses the JSON output of the"
                                                 "retrieve logs script to generate a final TSV file containing all the data")
    parser.add_argument("input_folder", help="Root folder that contains source code folders (each folder inside containing a"
                                          "project's source code)",
                        type=str)
    parser.add_argument("input_json",
                        help="JSON file location",
                        type=str)

    args = parser.parse_args()
    path = Path(args.input_folder)
    inputJSON = Path(args.input_json)
    main()
