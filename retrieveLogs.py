import os
import sys
import glob
import json
from tqdm import tqdm

from graph_pb2 import Graph
from graph_pb2 import FeatureNode
#Display lots of info
verbose = False

class Log:
    def __init__(self, severity, msg, lineLoc, fileLoc):
        self.severity = severity
        self.msg = msg
        self.lineLoc = lineLoc
        self.fileLoc = fileLoc

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
# Convert java.util.logging.Level to the rest of the levels (loose a log level, but its fine anyways)
def standardiselogLevels(logLevel):
    if logLevel == "severe":
        return "fatal"
    elif logLevel == "warning":
        return "error"
    elif logLevel == "config":
        return "debug"
    elif logLevel == "fine":
        return "info"
    elif logLevel == "finer" or logLevel == "finest":
        return "trace"
    else:
        return logLevel

# Detects LogBack (Spring) and Juli (Tomcat) and JBOSS (Hibernate)
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
            severity = standardiselogLevels(severity)
            # address jboss on this level instead of further down (makes life easier)
            severity = addressjBoss(severity)
            # verify the log level
            if verifyLogLevel(severity):
                # isolate the message
                msg = isolateMsg(nodes,i + 4)
                # Avoid false positives. If they occur, then the ENTIRE file (10k+ nodes) gets written.
                if len(msg) <= 1500:
                    fileLoc = graph.sourceFile
                    # remove false location data (and make it relative to the corpus)
                    fileLoc = fileLoc.replace('/local/data/Desktop/java-corpus-utils/java_projects-waiting/', '')
                    fileLoc = fileLoc.replace('/local/data/Desktop/java-corpus-utils/java_projects/', '')
                    lineLoc = node.startLineNumber
                    log = Log(severity, msg, lineLoc, fileLoc)
                    results.append(log)
    return results


#Converts the graph content markets into their respective string
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
        if node.contents =="SEMI":
            # go back an element from the semicolon
            endLocation = i - 1
            break
    # grab the nodes that contain the statement
    statementNodes = startNodes[0 : endLocation]
    msg = ""
    #Extract the msg and return it
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


    #(0)Tester path
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\TEST\\"



    #(2)All of cassandra
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\cassandra\\"

    #(3)All of clojure
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\clojure\\"

    #(4)All of dubbo
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\dubbo\\"

    #(5)All of errorProne
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\errorprone\\"

    #(6)All of grails
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\grails-core\\"

    #(7) all of guice
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\guice\\"

    #(9) jsoup
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\jsoup\\"

    #(10) junit4
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\junit4\\"

    #(11) kafka
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\kafka\\"

    #(14) oktttp
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\okhttp\\"

    #(16)Tomcat
    #path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\tomcat\\"

    # All of the corpus
    path = "C:\\Users\\GN\\Desktop\\work\\Uni\\Masters\\Dissertation\\corpus\\extracted\\"

    # https://mkyong.com/python/python-how-to-list-all-files-in-a-directory/
    # Get all files within the directory of the path
    files = [f for f in glob.glob(path + "**/*.java.proto", recursive=True)]
    results = []

    # if we are using verbose, don't display the bar (everything will print)
    if verbose:
        for f in files:
            results = results + runAnalysis(f)
    else:
        # Use tqdm to dispay a nice progress bar, requires manual for loop instead of for f in files
        for i in tqdm(range(len(files)), unit="files"):
            results = results + runAnalysis(files[i])

    for result in results:
        print(result)
    print("Execution finished, number of logs found: " + str(len(results)))
    # Write to JSON
    with open('result.json', 'w') as outfile:
        json.dump([ob.__dict__ for ob in results],outfile)
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
    # main(sys.argv[1])
    main()
