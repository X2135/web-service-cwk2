"""
Tests for the indexer module.

Tests inverted index construction, word extraction, and index operations.
"""

import unittest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from indexer import InvertedIndex, Indexer


class TestInvertedIndex(unittest.TestCase):
    """Test suite for the InvertedIndex class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.index = InvertedIndex()
    
    def test_index_initialization(self):
        """Test that index initializes correctly."""
        self.assertEqual(len(self.index.index), 0)
        self.assertEqual(len(self.index.documents), 0)
    
    def test_add_document(self):
        """Test adding a document to the index."""
        words = {"hello": [0, 5], "world": [1]}
        self.index.add_document(0, "http://example.com", words)
        
        self.assertEqual(len(self.index.index), 2)
        self.assertIn("hello", self.index.index)
        self.assertIn("world", self.index.index)
    
    def test_case_insensitivity(self):
        """Test that indexing is case-insensitive."""
        self.index.add_document(0, "http://example.com", {"Hello": [0]})
        self.index.add_document(1, "http://example.com/2", {"hello": [1]})
        
        # Both should map to lowercase 'hello'
        postings = self.index.get_postings("HELLO")
        self.assertEqual(len(postings), 2)
    
    def test_get_postings(self):
        """Test retrieving postings for a word."""
        words = {"hello": [0, 5], "world": [1]}
        self.index.add_document(0, "http://example.com", words)
        
        postings = self.index.get_postings("hello")
        
        self.assertEqual(len(postings), 1)
        doc_id, frequency, positions = postings[0]
        self.assertEqual(doc_id, 0)
        self.assertEqual(frequency, 2)
        self.assertEqual(positions, [0, 5])
    
    def test_get_postings_nonexistent_word(self):
        """Test retrieving postings for a word not in the index."""
        postings = self.index.get_postings("nonexistent")
        self.assertEqual(postings, [])
    
    def test_contains_word(self):
        """Test checking if word exists in index."""
        self.index.add_document(0, "http://example.com", {"hello": [0]})
        
        self.assertTrue(self.index.contains_word("hello"))
        self.assertTrue(self.index.contains_word("HELLO"))
        self.assertFalse(self.index.contains_word("world"))
    
    def test_get_documents_for_word(self):
        """Test getting document IDs for a word."""
        self.index.add_document(0, "http://example.com/1", {"hello": [0]})
        self.index.add_document(1, "http://example.com/2", {"hello": [1]})
        self.index.add_document(2, "http://example.com/3", {"world": [0]})
        
        doc_ids = self.index.get_documents_for_word("hello")
        
        self.assertEqual(len(doc_ids), 2)
        self.assertIn(0, doc_ids)
        self.assertIn(1, doc_ids)
    
    def test_word_statistics(self):
        """Test word statistics tracking."""
        self.index.add_document(0, "http://example.com/1", {"hello": [0, 1]})
        self.index.add_document(1, "http://example.com/2", {"hello": [2]})
        
        stats = self.index.word_stats["hello"]
        
        # Document frequency (how many documents contain the word)
        self.assertEqual(stats['df'], 2)
        # Collection frequency (total occurrences)
        self.assertEqual(stats['cf'], 3)
    
    def test_serialization(self):
        """Test index serialization to dictionary."""
        self.index.add_document(0, "http://example.com", {"hello": [0, 1]})
        
        data = self.index.to_dict()
        
        self.assertIn('index', data)
        self.assertIn('documents', data)
        self.assertIn('word_stats', data)
    
    def test_deserialization(self):
        """Test index deserialization from dictionary."""
        # Create and serialize an index
        original_index = InvertedIndex()
        original_index.add_document(0, "http://example.com", {"hello": [0, 1]})
        data = original_index.to_dict()
        
        # Deserialize
        restored_index = InvertedIndex.from_dict(data)
        
        # Verify
        self.assertTrue(restored_index.contains_word("hello"))
        doc_ids = restored_index.get_documents_for_word("hello")
        self.assertIn(0, doc_ids)


class TestIndexer(unittest.TestCase):
    """Test suite for the Indexer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.indexer = Indexer()
    
    def test_indexer_initialization(self):
        """Test that indexer initializes correctly."""
        self.assertIsNotNone(self.indexer.inv_index)
    
    def test_extract_text(self):
        """Test HTML to text extraction."""
        html = "<html><body><p>Hello World</p></body></html>"
        text = self.indexer._extract_text(html)
        
        self.assertIn("Hello", text)
        self.assertIn("World", text)
    
    def test_extract_text_removes_scripts(self):
        """Test that script tags are removed."""
        html = """
        <html>
            <body>
                <p>Hello</p>
                <script>alert('xss')</script>
                <p>World</p>
            </body>
        </html>
        """
        text = self.indexer._extract_text(html)
        
        self.assertIn("Hello", text)
        self.assertIn("World", text)
        self.assertNotIn("xss", text)
        self.assertNotIn("alert", text)
    
    def test_tokenize(self):
        """Test text tokenization."""
        text = "Hello, world! This is a test."
        tokens = self.indexer._tokenize(text)
        
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
        # Stopwords are filtered by default, so 'this' should not be present
        self.assertNotIn("this", tokens)
        self.assertIn("test", tokens)
    
    def test_tokenize_case_insensitive(self):
        """Test that tokenization converts to lowercase."""
        text = "HELLO World MiXeD"
        tokens = self.indexer._tokenize(text)
        
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)
        self.assertIn("mixed", tokens)
    
    def test_extract_words_with_positions(self):
        """Test word extraction with position tracking."""
        text = "hello world hello test"
        words_with_positions = self.indexer._extract_words_with_positions(text)
        
        self.assertIn("hello", words_with_positions)
        self.assertIn("world", words_with_positions)
        
        # 'hello' appears at positions 0 and 2
        self.assertEqual(words_with_positions["hello"], [0, 2])
        # 'world' appears at position 1
        self.assertEqual(words_with_positions["world"], [1])
    
    def test_index_pages_single_page(self):
        """Test indexing a single page."""
        pages = {
            "http://example.com/1": "<html><body>hello world</body></html>"
        }
        
        index = self.indexer.index_pages(pages)
        
        self.assertTrue(index.contains_word("hello"))
        self.assertTrue(index.contains_word("world"))
    
    def test_index_pages_multiple_pages(self):
        """Test indexing multiple pages."""
        pages = {
            "http://example.com/1": "<html><body>hello world</body></html>",
            "http://example.com/2": "<html><body>hello python</body></html>"
        }
        
        index = self.indexer.index_pages(pages)
        
        # Check that 'hello' is in both pages
        doc_ids = index.get_documents_for_word("hello")
        self.assertEqual(len(doc_ids), 2)
    
    def test_index_pages_empty_pages(self):
        """Test indexing with empty pages dictionary."""
        pages = {}
        index = self.indexer.index_pages(pages)
        
        self.assertEqual(len(index.index), 0)
    
    def test_get_index(self):
        """Test getting the constructed index."""
        pages = {
            "http://example.com": "<html><body>test</body></html>"
        }
        self.indexer.index_pages(pages)
        
        index = self.indexer.get_index()
        
        self.assertIsNotNone(index)
        self.assertTrue(index.contains_word("test"))


class TestIndexerIntegration(unittest.TestCase):
    """Integration tests for the Indexer."""
    
    def test_full_indexing_workflow(self):
        """Test complete indexing workflow."""
        pages = {
            "http://example.com/1": """
                <html>
                    <body>
                        <h1>Python Programming</h1>
                        <p>Python is great for programming</p>
                    </body>
                </html>
            """,
            "http://example.com/2": """
                <html>
                    <body>
                        <h1>Web Development</h1>
                        <p>Python is also good for web development</p>
                    </body>
                </html>
            """
        }
        
        indexer = Indexer()
        index = indexer.index_pages(pages)
        
        # Verify the index
        self.assertTrue(index.contains_word("python"))
        self.assertTrue(index.contains_word("programming"))
        
        # 'python' should be in both pages
        python_docs = index.get_documents_for_word("python")
        self.assertEqual(len(python_docs), 2)


if __name__ == '__main__':
    unittest.main()
