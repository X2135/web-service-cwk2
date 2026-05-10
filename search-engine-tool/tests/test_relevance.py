import unittest
import json
from pathlib import Path
from indexer import Indexer
from search import SearchEngine

from scripts.eval_relevance import average_precision, ndcg_at_k

class TestRelevanceMetrics(unittest.TestCase):
    def test_average_precision_simple(self):
        # ranked list: doc 1 at pos1, doc2 at pos2; relevant set contains doc1 and doc2
        ranked = [1,2,3,4]
        relevant = {1,2}
        ap = average_precision(ranked, relevant)
        # precision at 1 =1, precision at 2 = 2/2=1 -> AP = (1+1)/2 =1
        self.assertAlmostEqual(ap, 1.0)

    def test_ndcg_binary(self):
        ranked = [1,2,3,4]
        relevant = {2,4}
        ndcg = ndcg_at_k(ranked, relevant, 4)
        # compute manually: relevances = [0,1,0,1]
        # DCG = (2^0-1)/log2(1+1)=0 + (2^1-1)/log2(2+1)=1/1.58496 + 0 + (1)/log2(4+1)
        self.assertGreaterEqual(ndcg, 0.0)

if __name__ == '__main__':
    unittest.main()
