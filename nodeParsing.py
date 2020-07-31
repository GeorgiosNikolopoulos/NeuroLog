import argparse
import shutil
from graph_pb2 import Graph
import graph_pb2
from pathlib import Path
import json
from tqdm import tqdm
#import youtokentome as yttm
import sentencepiece as spm


def main():
    model_path = "statement_prediction/statementPrediction.model"
    #bpe = yttm.BPE(model=model_path)
    sp = spm.SentencePieceProcessor(model_file='statement_prediction/spmModel.model')
    # open the json
    with open(jsonPath, "rb") as jsonf:
        modifiedCorpusPath = Path("modified_corpus", ignore_errors=True, onerror=None)
        # get the logs, make the file structure
        logs = json.load(jsonf)
        # debug execution to generate a single graph
        if args.debug:
            # Generate output directory (its ok if it does not exist)
            modifiedCorpusPath.mkdir(parents=True, exist_ok=True)
            print("Debug mode active, using log element at index", args.debug)
            # get the single log to use from the args
            singleLog = logs[args.debug]
            rootId = singleLog["rootId"]
            # form the correct graph location
            graphLocation = Path(corpusPath + "/" + singleLog["fileLoc"] + ".proto")
            print("Using graph at:", graphLocation)
            with open(graphLocation, "rb") as graphFile:
                # modify the graph
                modifiedGraph = modifyGraphFile(graphFile, rootId)
                output = modifiedCorpusPath / graphLocation.name
                print("Writing new graph at", output)
                with open(output, "wb") as out:
                    out.write(modifiedGraph.SerializeToString())
                print("Done!")
        # proper corpus generation
        else:
            # generate the copy of the relevant corpus file structure
            generateCorpus(logs, modifiedCorpusPath)
            print("Starting graph modification")
            # new dictionary containing our filenames and how many times the file has been opened, used in file naming
            fileDict = {}
            # dictionary containing each file with its corresponding correct log level
            levelArray = []
            # For each log...
            for log in tqdm(logs, unit="logs"):
                # get the graph location, the root ID and the output path
                rootId = log["rootId"]
                graphLocation = Path(corpusPath + "/" + log["fileLoc"] + ".proto")
                outputPathStr = log["fileLoc"].replace(".java", "")
                if outputPathStr in fileDict:
                    fileDict[outputPathStr] += 1
                else:
                    fileDict[outputPathStr] = 1

                outputPath = modifiedCorpusPath / Path(outputPathStr + f"{str(fileDict[outputPathStr])}.java.proto")
                # tokenize the msg
                #tokenizedMsg = bpe.encode([log["msg"]], output_type=yttm.OutputType.SUBWORD)[0]
                tokenizedMsg = sp.encode([log["msg"]], out_type=str)[0]
                levelArray.append([str(outputPath), log["severity"],tokenizedMsg])
                #levelDict[str(outputPath)] = log["severity"]
                # open the input graph
                with open(graphLocation, "rb") as graphFile:
                    # Do the hard work modifying it
                    modifiedGraph = modifyGraphFile(graphFile, rootId)
                    # write it back out, overwriting the old file
                    with open(outputPath, "wb") as out:
                        out.write(modifiedGraph.SerializeToString())

            print("Finished writing graph files")
            with open(modifiedCorpusPath / "severities.json", "w") as outJSON:
                json.dump(levelArray, outJSON)
                print("Wrote severities.json. Contains each graph location, it's corresponding log level and msg.")


def modifyGraphFile(graphFile, rootId):
    g = Graph()
    g.ParseFromString(graphFile.read())
    nodes = g.node
    edges = g.edge

    # get all the relevant log nodes
    allLogNodes, baseNodeIndex, \
    lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition = retrieveAllLogsNodes(nodes, rootId)
    # get the releant node ids
    allLogNodesIds = list(map(lambda node: node.id, allLogNodes))

    # STEP 1) Remove any edge that both originates and targets nodes within our log statment
    edges = removeLogEdges(edges, allLogNodesIds)
    # STEP 2) Modify any edge that links to one of our log nodes within the statement. These edges will now point to the
    # root LOG node.
    edges = adjustOutsideEdges(edges, allLogNodesIds)
    # STEP 3) Modify all the log nodes. Modify root node to be special LOG node, delete rest.
    nodes = modifyNodes(nodes, baseNodeIndex, lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition)

    # create a new Graph file to return for writing, using all the modified nodes and edges
    returnGraph = Graph()
    for node in nodes:
        graphNode = graph_pb2.FeatureNode()
        graphNode.id = node.id
        graphNode.type = node.type
        graphNode.contents = removeImportLeaks(node.contents)
        graphNode.startPosition = node.startPosition
        graphNode.endPosition = node.endPosition
        graphNode.startLineNumber = node.startLineNumber
        graphNode.endLineNumber = node.endLineNumber
        # append our node to the new graph file
        returnGraph.node.append(graphNode)
    for edge in edges:
        graphEdge = graph_pb2.FeatureEdge()
        graphEdge.sourceId = edge.sourceId
        graphEdge.destinationId = edge.destinationId
        graphEdge.type = edge.type
        # append our edge to the graph file
        returnGraph.edge.append(graphEdge)

    graphFile.close()
    return returnGraph


# Removes any potential leaks of log levels at import statements.
def removeImportLeaks(content):
    if "." in content and "log" in content and " " not in content:
        if "trace" in content or "debug" in content or "info" in content or "error" in content or "fatal" in content:
            return " "

    return content


# Modify the nodes to remove the log statment and replace it with our special LOG type. Makes sure end position and
# end line number match the last node
def modifyNodes(nodes, baseNodeIndex, lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition):
    del nodes[baseNodeIndex + 1: lastLogNodeIndex]
    nodes[baseNodeIndex].type = 17  # LOG enum ID
    nodes[baseNodeIndex].contents = ""
    nodes[baseNodeIndex].endLineNumber = lastNodeEndLineNumber
    nodes[baseNodeIndex].endPosition = lastNodeEndPosition
    return nodes


# Adjusts any edges that point to a node outside our log nodes (either as source or destination)
def adjustOutsideEdges(edges, allLogIds):
    def mapEdges(edge):
        # if the edge originates from one of our nodes
        if edge.sourceId in allLogIds:
            # change the sourceId to point to the root node (future LOG)
            edge.sourceId = allLogIds[0]
        # if the edge points to one of our log nodes
        elif edge.destinationId in allLogIds:
            # make it point to the root node (future LOG node)
            edge.destinationId = allLogIds[0]
        return edge

    return list(map(mapEdges, edges))


# Removes all logs that have edges starting AND pointing to nodes within our log statement
def removeLogEdges(edges, nodeIds):
    def filterEdges(edge):
        if edge.sourceId in nodeIds:
            if edge.destinationId in nodeIds:
                return False
        return True

    edges = list(filter(filterEdges, edges))
    return edges


# analyzes all nodes of a graph, returning the nodes that contain the logging statement
def retrieveAllLogsNodes(nodes, rootId):
    baseNodeIndex = 0
    discoveredLogNode = False
    lastNodeIndex = 0
    lastNodeEndLineNumber = 0
    lastNodeEndPosition = 0
    # loop over our nodes
    for index, node in enumerate(nodes):
        # if we are not looking for the semi
        if not discoveredLogNode:
            # if we found our root
            if node.id == rootId:
                # set the base index, start looking for the semi
                baseNodeIndex = index
                discoveredLogNode = True
        else:  # looking for the semi
            if "SEMI" in node.contents:
                # found it! Break out of the loop
                lastNodeIndex = index + 1
                lastNodeEndLineNumber = node.endLineNumber
                lastNodeEndPosition = node.endPosition
                break

    # get the relevant nodes
    allLogNodes = nodes[baseNodeIndex:lastNodeIndex]

    return allLogNodes, baseNodeIndex, lastNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition


# Generate the entire new corpus file structure. Currently unused
def generateCorpus(logs, modifiedCorpusPath):
    if args.delete:
        try:
            print("Deleting old modified corpus")
            shutil.rmtree(modifiedCorpusPath)
        except FileNotFoundError:
            pass
    print("Generating new corpus file structure...", end="")
    try:
        # make the main output directory
        modifiedCorpusPath.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("\nModified corpus already exists, please delete before executing")
        exit(1)
    # For every log...
    for log in logs:
        # get the path
        logPath = Path(log["fileLoc"])
        # form the new output folder structure
        corpusPath = modifiedCorpusPath / logPath.parents[0]
        # write it, its ok if it exists (as we can have multiple logs per file)
        corpusPath.mkdir(parents=True, exist_ok=True)
    print(" Done!")


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(
        description="Generates a new corpus of protobuff files containing modified graph structures. Does so by "
                    "removing all log instances and re-creating the graph structure to leave no trace of a log's "
                    "existence, except a unique LOG node.")
    parser.add_argument("input_json", help="Location of json file.",
                        type=str)
    parser.add_argument("corpus_location", help="Root folder location of the corpus used to generate the JSON")
    parser.add_argument("-d", "--delete", help="If a modified corpus exists, delete it", action="store_true")
    parser.add_argument("--debug", help=" Generate a single graph file, to check the graph output. Takes an integer,"
                                        "pointing to an element of the input json array.", type=int)
    args = parser.parse_args()
    jsonPath = Path(args.input_json)
    corpusPath = str(Path(args.corpus_location))
    main()
