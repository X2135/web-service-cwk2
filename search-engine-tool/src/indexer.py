"""
Indexer module for building inverted indices from crawled web pages.

This module processes HTML content and creates an inverted index that maps
words to their occurrences across pages, storing statistics like frequency and position.
"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List, Tuple, Set
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvertedIndex:
    """
    An inverted index data structure for efficient search.
    
    Maps words to documents and stores statistics about their occurrences.
    
    Attributes:
        index: Dictionary mapping words to posting lists
        documents: Dictionary mapping document IDs to URLs
        word_stats: Statistics for each word
    """
    
    def __init__(self):
        """Initialize an empty inverted index."""
        # word -> [(doc_id, frequency, positions), ...]
        self.index: Dict[str, List[Tuple[int, int, List[int]]]] = {}
        # doc_id -> url
        self.documents: Dict[int, str] = {}
        # word -> Document Frequency (DF)
        self.word_stats: Dict[str, Dict] = {}
    
    def add_document(self, doc_id: int, url: str, words_with_positions: Dict[str, List[int]]) -> None:
        """
        Add a document to the index.
        
        Args:
            doc_id: Unique document identifier
            url: Source URL of the document
            words_with_positions: Dict mapping words to lists of positions they appear at
        """
        self.documents[doc_id] = url
        
        for word, positions in words_with_positions.items():
            word_lower = word.lower()
            frequency = len(positions)
            
            if word_lower not in self.index:
                self.index[word_lower] = []
                self.word_stats[word_lower] = {'df': 0, 'cf': 0}  # df: document freq., cf: collection freq.
            
            self.index[word_lower].append((doc_id, frequency, positions))
            self.word_stats[word_lower]['df'] += 1
            self.word_stats[word_lower]['cf'] += frequency
    
    def get_postings(self, word: str) -> List[Tuple[int, int, List[int]]]:
        """
        Get posting list for a word.
        
        Args:
            word: Word to search for (case-insensitive)
            
        Returns:
            List of (doc_id, frequency, positions) tuples, or empty list if word not found
        """
        word_lower = word.lower()
        return self.index.get(word_lower, [])
    
    def contains_word(self, word: str) -> bool:
        """
        Check if a word exists in the index.
        
        Args:
            word: Word to check
            
        Returns:
            True if word is in the index
        """
        return word.lower() in self.index
    
    def get_documents_for_word(self, word: str) -> List[int]:
        """
        Get list of document IDs containing a word.
        
        Args:
            word: Word to search for
            
        Returns:
            List of document IDs containing the word
        """
        postings = self.get_postings(word)
        return [doc_id for doc_id, _, _ in postings]
    
    def to_dict(self) -> Dict:
        """
        Serialize index to dictionary for storage.
        
        Returns:
            Dictionary representation of the index
        """
        return {
            'index': {word: [(doc_id, freq, pos) for doc_id, freq, pos in postings]
                      for word, postings in self.index.items()},
            'documents': self.documents,
            'word_stats': self.word_stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InvertedIndex':
        """
        Deserialize index from dictionary.
        
        Args:
            data: Dictionary representation of the index
            
        Returns:
            Reconstructed InvertedIndex object
        """
        inv_index = cls()
        inv_index.index = {word: [(doc_id, freq, pos) for doc_id, freq, pos in postings]
                           for word, postings in data['index'].items()}
        inv_index.documents = {int(doc_id): url for doc_id, url in data['documents'].items()}
        inv_index.word_stats = data['word_stats']
        return inv_index


class Indexer:
    """
    Builds an inverted index from crawled HTML pages.
    
    Attributes:
        inv_index: The InvertedIndex object
    """
    
    def __init__(self):
        """Initialize the indexer with an empty index."""
        self.inv_index = InvertedIndex()
    
    def _extract_text(self, html: str) -> str:
        """
        Extract plain text from HTML content.
        
        Args:
            html: HTML content to process
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of words
        """
        # Convert to lowercase
        text = text.lower()
        # Split on whitespace and punctuation
        words = re.findall(r'\b[a-z]+\b', text)
        return words
    
    def _extract_words_with_positions(self, text: str) -> Dict[str, List[int]]:
        """
        Extract words from text and record their positions.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary mapping words to lists of positions
        """
        text = text.lower()
        words = re.findall(r'\b[a-z]+\b', text)
        
        words_with_positions: Dict[str, List[int]] = {}
        for position, word in enumerate(words):
            if word not in words_with_positions:
                words_with_positions[word] = []
            words_with_positions[word].append(position)
        
        return words_with_positions
    
    def index_pages(self, pages: Dict[str, str]) -> InvertedIndex:
        """
        Build inverted index from a collection of HTML pages.
        
        Args:
            pages: Dictionary mapping URLs to HTML content
            
        Returns:
            The constructed InvertedIndex object
        """
        logger.info(f"Indexing {len(pages)} pages...")
        
        for doc_id, (url, html) in enumerate(pages.items()):
            try:
                # Extract text from HTML
                text = self._extract_text(html)
                
                # Extract words with positions
                words_with_positions = self._extract_words_with_positions(text)
                
                # Add to index
                self.inv_index.add_document(doc_id, url, words_with_positions)
                
                if (doc_id + 1) % 10 == 0:
                    logger.info(f"Indexed {doc_id + 1} pages...")
                    
            except Exception as e:
                logger.error(f"Error indexing page {url}: {e}")
                continue
        
        logger.info(f"Indexing complete. Index size: {len(self.inv_index.index)} unique words")
        return self.inv_index
    
    def get_index(self) -> InvertedIndex:
        """
        Get the constructed index.
        
        Returns:
            The InvertedIndex object
        """
        return self.inv_index
