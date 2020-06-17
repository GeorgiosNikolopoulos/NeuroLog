import re
import argparse
from graph_pb2 import Graph
from pathlib import Path


def main():
    with open(str(graphLocation), "rb") as graphFile:
        g = Graph()
        g.ParseFromString(graphFile.read())
        logIds = []
        with open(graphLocation.name + ".dot", "w") as f:
            f.write("digraph G {\n")
            for node in g.node:
                #f.write(str(node.id) + ' [ label="' + toNodeText(node) + '" ];\n')
                f.write(str(node.id) + ' [ label="' + re.escape(node.contents) + '" ];\n')
                if(toNodeText(node) == "LOG"):
                    logIds.append(node.id)
            for edge in g.edge:
                f.write((str(edge.sourceId) + " -> " + str(edge.destinationId) + "\n"))
            for logId in logIds:
                f.write(str(logId) + " [shape=Msquare];")
            f.write("}\n")
            f.close()


def getOutEdges(node, edges):
    return list(filter(lambda edge: node.id == edge.sourceId, edges))


# there is a way to do this by using google's protobuff tools, but it'll take more time to find it
def toNodeText(node):
    elements = ["TOKEN", "AST_ELEMENT", "COMMENT_LINE", "COMMENT_BLOCK", "COMMENT_JAVADOC","", "IDENTIFIER_TOKEN"
        , "FAKE_AST", "SYMBOL", "SYMBOL_TYP", "SYMBOL_VAR", "SYMBOL_MTH", "TYPE", "METHOD_SIGNATURE",
                "AST_LEAF", "", "LOG"]
    return (elements[node.type - 1])


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(
        description="Generates a dot file for graph visualization. NOTE: this is not bug-free,"
                    "it has been written as a quick and easy visualization tool, do not be surpised if the output is broken")
    parser.add_argument("graph_file", help="Location of graph file to convert. Please use full path",
                        type=str)
    args = parser.parse_args()
    graphLocation = Path(args.graph_file)
    main()
