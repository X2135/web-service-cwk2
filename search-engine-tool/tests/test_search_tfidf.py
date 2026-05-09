import unittest
import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indexer import InvertedIndex
from search import SearchEngine


class TestSearchTFIDFAndCache(unittest.TestCase):
    def test_tfidf_ranking_prioritizes_relevance(self):
        index = InvertedIndex()
        # doc0 has 'apple' twice, doc1 has 'apple' once
        index.add_document(0, "http://example.com/doc0", {"apple": [0, 1], "banana": [2]})
        index.add_document(1, "http://example.com/doc1", {"apple": [0], "cherry": [1]})
        index.add_document(2, "http://example.com/doc2", {"banana": [0]})
        # calculate idf so TF-IDF can be computed
        index.calculate_idf()

        se = SearchEngine(index)
        results = se.find_ranked("apple", top_n=10)
        # Expect doc0 (higher term frequency) before doc1
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0], "http://example.com/doc0")
        self.assertEqual(results[1], "http://example.com/doc1")

    def test_query_cache_prevents_immediate_index_changes(self):
        index = InvertedIndex()
        index.add_document(0, "http://example.com/a", {"x": [0]})
        index.add_document(1, "http://example.com/b", {"x": [0,1]})
        index.calculate_idf()

        se = SearchEngine(index)
        first = se.find_ranked("x", top_n=10)
        # Add a new high-frequency document that should outrank existing ones
        index.add_document(2, "http://example.com/c", {"x": [0,1,2,3,4]})
        index.calculate_idf()

        second_cached = se.find_ranked("x", top_n=10)
        # Since result was cached, it should remain equal to first
        self.assertEqual(first, second_cached)

        # After clearing cache, results should update to reflect new document
        se.clear_cache()
        updated = se.find_ranked("x", top_n=10)
        self.assertNotEqual(first, updated)
        self.assertEqual(updated[0], "http://example.com/c")


if __name__ == '__main__':
    unittest.main()
