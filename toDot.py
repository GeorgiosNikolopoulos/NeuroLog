import re
import argparse
from graph_pb2 import Graph
from pathlib import Path


# Writes out a .dot file from the inputed graph file
def main():
    with open(str(graphLocation), "rb") as graphFile:
        g = Graph()
        g.ParseFromString(graphFile.read())
        logIds = []
        with open(graphLocation.name + ".dot", "w") as f:
            # write the first line of the dot
            f.write("digraph G {\n")
            # for each node, write out the node with the contents as its label
            for node in g.node:
                # the first line writes the node type as the label, the second the node contents. Second is better.
                # f.write(str(node.id) + ' [ label="' + toNodeText(node) + '" ];\n')
                f.write(str(node.id) + ' [ label="' + re.escape(node.contents) + '" ];\n')
                if (toNodeText(node) == "LOG"):
                    logIds.append(node.id)
            # for each edge, write out the edge as a link between the source and the destination
            for edge in g.edge:
                f.write((str(edge.sourceId) + " -> " + str(edge.destinationId) + "\n"))
            # Pretify any special LOG nodes by making them distinct (Square with diamond inside)
            for logId in logIds:
                f.write(str(logId) + " [shape=Msquare];")
            f.write("}\n")
            f.close()


# there is a way to do this by using google's protobuff tools, but it'll take more time to find it
def toNodeText(node):
    elements = ["TOKEN", "AST_ELEMENT", "COMMENT_LINE", "COMMENT_BLOCK", "COMMENT_JAVADOC", "", "IDENTIFIER_TOKEN"
        , "FAKE_AST", "SYMBOL", "SYMBOL_TYP", "SYMBOL_VAR", "SYMBOL_MTH", "TYPE", "METHOD_SIGNATURE",
                "AST_LEAF", "", "LOG"]
    return (elements[node.type - 1])


if __name__ == "__main__":
    # use argparser to set up all argument parsing
    parser = argparse.ArgumentParser(
        description="Generates a dot file for graph visualization. NOTE: this is not bug-free,"
                    "it has been written as a quick and easy visualization tool, do not be surpised if the output is broken")
    parser.add_argument("graph_file", help="Location of graph file to convert.",
                        type=str)
    args = parser.parse_args()
    graphLocation = Path(args.graph_file)
    main()
