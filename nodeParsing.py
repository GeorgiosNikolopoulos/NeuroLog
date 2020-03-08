from graph_pb2 import Graph
from pathlib import Path
import json

jsonPath = str(
    Path("C:/Users/GN/Desktop/work/Uni/Masters/Dissertation/detecting-log-statements/results/all_projects.json"))
corpusPath = str(Path("C:/Users/GN/Desktop/work/Uni/Masters/Dissertation/corpus/extracted/"))


def main():
    with open(jsonPath, "rb") as jsonf:
        singleLog = json.load(jsonf)[0]
        modifiedGraph = modifyGraphFile(singleLog)
        #out = open("test.java.proto", "wb")
        #out.write(modifiedGraph.SerializeToString())
        #out.close()
        print(modifiedGraph.node)
        jsonf.close()


def modifyGraphFile(log):
    rootId = log["rootId"]
    graphLocation = Path(corpusPath + "/" + log["fileLoc"] + ".proto")
    with open(str(graphLocation), "rb") as graphFile:
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

        nodes = modifyNodes(nodes, baseNodeIndex, lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition)
        # edgeswithSourceLink = list(filter(lambda edge: edge.sourceId in allLogNodesIds, edges))
        # edgeswithDestinationLink = list(filter(lambda edge: edge.destinationId in allLogNodesIds, edges))
        # print(allLogNodesIds)
        # print(edgeswithSourceLink)
        # print(edgeswithDestinationLink)
        graphFile.close()
        return g


# Modify the nodes to remove the log statment and replace it with our special LOG type. Makes sure end position and
# end line number match the last node
def modifyNodes(nodes, baseNodeIndex, lastLogNodeIndex, lastNodeEndLineNumber, lastNodeEndPosition):
    del nodes[baseNodeIndex + 1: lastLogNodeIndex]
    nodes[baseNodeIndex].type = 17
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


if __name__ == "__main__":
    # main(sys.argv[1])
    main()
