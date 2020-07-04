import json
import unittest
from collections import Counter
from pathlib import Path
import random

from graph_pb2 import Graph

corpusLocation = Path().absolute() / "modified_corpus"
jsonLocation = Path().absolute() / "results/all_projects.json"

class TestGraphGeneration(unittest.TestCase):
    # Read the logs at the start
    def setUp(self):
        with open(jsonLocation, "rb") as jsonf:
            self.logs = json.load(jsonf)

    # Verify that no logs get Lost when the new corpus is generated via nodeParsing.py. So, if two logs were
    # detected in retrieveLogs.py script (and were written in the JSON), then 2 special nodes of LOG should be
    # detected in the output location. Tests the entire corpus, as it is isn't terribly expensive to do so (~20 secs)
    def test_correct_log_numbers_get_written(self):
        # Get all the graph locations
        graphLocs = map(lambda log: str(corpusLocation / Path(log["fileLoc"] + ".proto")), self.logs)
        # Convert them into a nice dictionary containing the number of occurrences
        logsCounter = Counter(graphLocs)
        for location, logNumberActual in logsCounter.items():
            # open the graph location
            with open(location, "rb") as graphFile:
                LOGNumber = 0
                g = Graph()
                g.ParseFromString(graphFile.read())
                # Loop through the nodes, counting the special LOG nodes
                for node in g.node:
                    if node.type == 17:
                        LOGNumber += 1
                # verify that the correct number of special nodes exist
                self.assertEqual(LOGNumber, logNumberActual)

    # Test 10 graph files to see that the special logs are in the correct place.
    def test_graph_structure(self):
        for x in range(10):
            log = random.choice(self.logs)
            logLocation = corpusLocation / Path(log["fileLoc"] + ".proto")
            with open(logLocation,"rb") as graphFile:
                g = Graph()
                g.ParseFromString(graphFile.read())
                for key, node in enumerate(g.node):
                    # got the correct node
                    if node.id == log["rootId"]:
                        # Make sure its the special LOG and that the roots match
                        self.assertEqual(node.type, 17)
                        self.assertEqual(node.id, log["rootId"])

    # Tests a few graphs to verify that no edges either originate or point to the nodes that were removed
    # during the nodeParsing procedure
    def test_graph_edge_structure(self):
        for x in range(10):
            # get a random log
            log = random.choice(self.logs)
            # form its location
            logLocation = corpusLocation / Path(log["fileLoc"] + ".proto")
            with open(logLocation, "rb") as graphFile:
                g = Graph()
                g.ParseFromString(graphFile.read())
                for key, node in enumerate(g.node):
                    # if the LOG node is found
                    if node.id == log["rootId"]:
                        # get the following node
                        nextNode = g.node[key + 1]
                        # calculate how many nodes are "missing"
                        idDiff = nextNode.id - node.id
                        # get the missing node id's as an array
                        missingNodes = getMissingIds(node.id,idDiff)
                        # see if any edges either point to or originate from the missing nodes
                        edgesFromAndToMissingNodes = list(filter(lambda edge: edge.sourceId in missingNodes
                                                                 or edge.destinationId in missingNodes, g.edge))
                        # make sure that value is 0
                        self.assertEqual(len(edgesFromAndToMissingNodes), 0)

# Return an array of ids that are missing from the graph
def getMissingIds(startId, idDiff):
    ids = []
    for x in range(idDiff):
        if x != 0:
            ids.append(startId + x)
    return ids

if __name__ == '__main__':
    unittest.main()
