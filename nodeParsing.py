import argparse
import shutil
from graph_pb2 import Graph
import graph_pb2
from pathlib import Path
import json
from tqdm import tqdm


def main():
    # open the json
    with open(jsonPath, "rb") as jsonf:
        modifiedCorpusPath = Path("modified_corpus", ignore_errors=True, onerror=None)
        # get the logs, make the file strucutre
        logs = json.load(jsonf)
        #debug execution to generate a single graph
        if args.debug:
            modifiedCorpusPath.mkdir(parents=True, exist_ok=True)
            print("Debug mode active, using log element at index", args.debug)
            singleLog = logs[args.debug]
            rootId = singleLog["rootId"]
            graphLocation = Path(corpusPath + "/" + singleLog["fileLoc"] + ".proto")
            print("Using graph at:", graphLocation)
            with open(graphLocation, "rb") as graphFile:
                modifiedGraph = modifyGraphFile(graphFile, rootId)
                output = modifiedCorpusPath / graphLocation.name
                print("Writing new graph at", output)
                with open(output, "wb") as out:
                    out.write(modifiedGraph.SerializeToString())
                print("Done!")
        # proper corpus generation
        else:
            generateCorpus(logs, modifiedCorpusPath)
            print("Starting graph modification")
            # For each log...
            for log in tqdm(logs, unit="logs"):
                # get the graph location, the root ID and the output path
                rootId = log["rootId"]
                graphLocation = Path(corpusPath + "/" + log["fileLoc"] + ".proto")
                outputPath = modifiedCorpusPath / Path(log["fileLoc"] + ".proto")
                # if the output file exists (so the original file was already used once, meaning that the original
                # has at least 2 logs).
                # Reuse the OUTPUT graph file, so it does not overwrite the previous logs
                if outputPath.is_file():
                    graphLocation = outputPath
                # open the input graph
                with open(graphLocation, "rb") as graphFile:
                    # Do the hard work modifying it
                    modifiedGraph = modifyGraphFile(graphFile, rootId)
                    # write it back out, overwriting the old file
                    with open(outputPath, "wb") as out:
                        out.write(modifiedGraph.SerializeToString())



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
    # STEP 2) Modify any edge that links to one of our log nodes ( either so they originate from the source node
    # or that they point it now.)
    edges = adjustOutsideEdges(edges, allLogNodesIds)
    # STEP 3) Modify all the log nodes. Modify root node to be special LOG node, delete rest.
    nodes = modifyNodes(nodes, baseNodeIndex, lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition)

    # create a new Graph file to return for writing, using all the modified nodes and edges
    returnGraph = Graph()
    for node in nodes:
        graphNode = graph_pb2.FeatureNode()
        graphNode.id = node.id
        graphNode.type = node.type
        graphNode.contents = node.contents
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
        modifiedCorpusPath.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("\nModified corpus already exists, please delete before executing")
        exit(1)
    for log in logs:
        logPath = Path(log["fileLoc"])
        corpusPath = modifiedCorpusPath / logPath.parents[0]
        corpusPath.mkdir(parents=True, exist_ok=True)
    print(" Done!")


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(
        description="Generates a new corpus of protobuff files containing modified graph structures. Does so by "
                    "removing all log instances and re-creating the graph structure to leave no trace of a log's "
                    "existence, except a unique LOG node.")
    parser.add_argument("input_json", help="Location of json file. Please use full path",
                        type=str)
    parser.add_argument("corpus_location", help="Root folder location of the corpus used to generate the JSON")
    parser.add_argument("-d", "--delete", help="If a modified corpus exists, delete it", action="store_true")
    parser.add_argument("--debug", help=" Generate a single graph file, to check the graph output. Takes an integer,"
                                        "pointing to an element of the input json array.",type=int)
    args = parser.parse_args()
    jsonPath = str(Path(args.input_json))
    corpusPath = str(Path(args.corpus_location))
    main()
