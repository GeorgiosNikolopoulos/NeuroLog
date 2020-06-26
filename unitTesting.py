import json
import unittest
from collections import Counter
from pathlib import Path

from graph_pb2 import Graph

corpusLocation = "/home/gn/Desktop/work/Uni/Masters/Dissertation/detecting-log-statements/modified_corpus"
jsonLocation = "/home/gn/Desktop/work/Uni/Masters/Dissertation/detecting-log-statements/results/all_projects.json"


class TestGraphGeneration(unittest.TestCase):
    # Read the logs at the start
    def setUp(self):
        with open(jsonLocation, "rb") as jsonf:
            self.logs = json.load(jsonf)

    # Verify that no logs get Lost when the new corpus is generated via nodeParsing.py. So, if two logs were
    # detected in retrieveLogs.py script (and were written in the JSON), then 2 special nodes of LOG should be
    # detected in the output location. Tests the entire corpus, as it is isn't terribly expensive to do so (~20 secs)
    def test_multiple_logs_get_written(self):
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


if __name__ == '__main__':
    unittest.main()
