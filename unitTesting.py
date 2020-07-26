import glob
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

    def test_number_of_logs(self):
        files = [f for f in glob.glob(str(corpusLocation) + "/**/*.java.proto", recursive=True)]
        self.assertEqual(len(files), len(self.logs))


if __name__ == '__main__':
    unittest.main()
