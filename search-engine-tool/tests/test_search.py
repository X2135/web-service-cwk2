"""
Tests for the search module.

Tests search functionality, query processing, and result retrieval.
"""

import unittest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indexer import InvertedIndex
from search import SearchEngine


class TestSearchEngine(unittest.TestCase):
    """Test suite for the SearchEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
        
        # Add some test data
        self.index.add_document(0, "http://example.com/1", 
                               {"hello": [0], "world": [1], "python": [2]})
        self.index.add_document(1, "http://example.com/2", 
                               {"hello": [0], "programming": [1]})
        self.index.add_document(2, "http://example.com/3", 
                               {"world": [0], "java": [1]})
        
        self.search_engine = SearchEngine(self.index)
    
    def test_search_engine_initialization(self):
        """Test that search engine initializes correctly."""
        self.assertIsNotNone(self.search_engine.inv_index)
        self.assertEqual(self.search_engine.inv_index, self.index)
    
    def test_print_index(self):
        """Test printing index entry for a word."""
        result = self.search_engine.print_index("hello")
        
        self.assertEqual(result['word'], "hello")
        self.assertEqual(result['document_frequency'], 2)
        self.assertEqual(len(result['postings']), 2)
    
    def test_print_index_nonexistent_word(self):
        """Test printing index for nonexistent word."""
        result = self.search_engine.print_index("nonexistent")
        
        self.assertEqual(result, {})
    
    def test_print_index_case_insensitive(self):
        """Test that print_index is case-insensitive."""
        result1 = self.search_engine.print_index("HELLO")
        result2 = self.search_engine.print_index("hello")
        
        self.assertEqual(result1['word'], result2['word'])
    
    def test_print_index_empty_word(self):
        """Test printing index with empty word."""
        result = self.search_engine.print_index("")
        
        self.assertEqual(result, {})
    
    def test_find_single_word(self):
        """Test finding pages with a single word."""
        results = self.search_engine.find_single_word("hello")
        
        self.assertEqual(len(results), 2)
        self.assertIn("http://example.com/1", results)
        self.assertIn("http://example.com/2", results)
    
    def test_find_single_word_case_insensitive(self):
        """Test that single word search is case-insensitive."""
        results1 = self.search_engine.find_single_word("HELLO")
        results2 = self.search_engine.find_single_word("hello")
        
        self.assertEqual(results1, results2)
    
    def test_find_single_word_not_found(self):
        """Test searching for a word not in index."""
        results = self.search_engine.find_single_word("nonexistent")
        
        self.assertEqual(results, [])
    
    def test_find_multi_word_and_logic(self):
        """Test multi-word search with AND logic."""
        # Both words must be present
        results = self.search_engine.find_multi_word(["hello", "world"])
        
        # Only doc 0 has both 'hello' and 'world'
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "http://example.com/1")
    
    def test_find_multi_word_no_match(self):
        """Test multi-word search with no matching documents."""
        results = self.search_engine.find_multi_word(["hello", "java"])
        
        # No document has both words
        self.assertEqual(results, [])
    
    def test_find_multi_word_word_not_found(self):
        """Test multi-word search when one word doesn't exist."""
        results = self.search_engine.find_multi_word(["hello", "nonexistent"])
        
        self.assertEqual(results, [])
    
    def test_find_query_single_word(self):
        """Test find method with single word query."""
        results = self.search_engine.find("hello")
        
        self.assertEqual(len(results), 2)
    
    def test_find_query_multiple_words(self):
        """Test find method with multiple word query."""
        results = self.search_engine.find("hello world")
        
        self.assertEqual(len(results), 1)
    
    def test_find_empty_query(self):
        """Test find method with empty query."""
        results = self.search_engine.find("")
        
        self.assertEqual(results, [])
    
    def test_find_whitespace_only_query(self):
        """Test find method with whitespace-only query."""
        results = self.search_engine.find("   ")
        
        self.assertEqual(results, [])
    
    def test_search_with_stats(self):
        """Test search with statistics."""
        stats = self.search_engine.search_with_stats("hello world")
        
        self.assertEqual(stats['query'], "hello world")
        self.assertEqual(stats['num_words'], 2)
        self.assertEqual(stats['results_found'], 1)
        self.assertGreater(len(stats['urls']), 0)
    
    def test_edit_distance(self):
        """Test edit distance calculation."""
        # Identical strings
        dist = SearchEngine._edit_distance("hello", "hello")
        self.assertEqual(dist, 0)
        
        # One character different
        dist = SearchEngine._edit_distance("hello", "hallo")
        self.assertEqual(dist, 1)
        
        # Completely different
        dist = SearchEngine._edit_distance("cat", "dog")
        self.assertEqual(dist, 3)
    
    def test_fuzzy_match(self):
        """Test fuzzy matching for typo tolerance."""
        # Add a word to the index for testing
        self.index.add_document(3, "http://example.com/4", 
                               {"programming": [0]})
        
        # Search for a similar word (with typo)
        results = self.search_engine.fuzzy_match("programing", max_distance=1)
        
        # Should find 'programming' despite the typo
        self.assertGreater(len(results), 0)


class TestSearchEngineEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
        self.search_engine = SearchEngine(self.index)
    
    def test_search_on_empty_index(self):
        """Test searching on an empty index."""
        results = self.search_engine.find("hello")
        
        self.assertEqual(results, [])
    
    def test_print_index_on_empty_index(self):
        """Test printing index entry on empty index."""
        result = self.search_engine.print_index("hello")
        
        self.assertEqual(result, {})
    
    def test_special_characters_in_query(self):
        """Test handling special characters in query."""
        result = self.search_engine.find("hello!@#$%")
        
        # Should handle gracefully (invalid characters stripped)
        self.assertIsInstance(result, list)
    
    def test_very_long_query(self):
        """Test handling very long query."""
        long_query = " ".join(["word"] * 100)
        result = self.search_engine.find(long_query)
        
        self.assertEqual(result, [])


class TestSearchEngineIntegration(unittest.TestCase):
    """Integration tests for search functionality."""
    
    def test_complete_search_workflow(self):
        """Test complete search workflow."""
        # Create index with sample data
        index = InvertedIndex()
        
        # Add documents
        index.add_document(0, "http://example.com/quotes/1", 
                          {"good": [0], "friends": [1], "hard": [2]})
        index.add_document(1, "http://example.com/quotes/2", 
                          {"good": [0], "people": [1]})
        index.add_document(2, "http://example.com/quotes/3", 
                          {"friendship": [0], "is": [1], "good": [2]})
        
        search_engine = SearchEngine(index)
        
        # Test single word search
        results = search_engine.find("good")
        self.assertEqual(len(results), 3)
        
        # Test multi-word search
        results = search_engine.find("good friends")
        self.assertEqual(len(results), 1)
        
        # Test print
        index_entry = search_engine.print_index("good")
        self.assertEqual(index_entry['document_frequency'], 3)


if __name__ == '__main__':
    unittest.main()
