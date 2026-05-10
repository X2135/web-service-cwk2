"""
Indexer module for building inverted indices from crawled web pages.

This module processes HTML content and creates an inverted index that maps
words to their occurrences across pages, storing statistics like frequency and position.
Features include stopword filtering, TF-IDF calculation, and performance monitoring.
"""

from bs4 import BeautifulSoup
import re
import math
from typing import Dict, List, Tuple, Set
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common English stopwords to filter out
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
    'the', 'to', 'was', 'will', 'with', 'this', 'but', 'have', 'had',
    'what', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'some', 'such', 'no', 'nor', 'not', 'only',
    'same', 'so', 'than', 'too', 'very', 'just', 'can', 'should', 'would',
    'could', 'if', 'then', 'do', 'does', 'did', 'i', 'you', 'he', 'she',
    'we', 'they', 'them', 'who', 'which', 'whom', 'am', 'being', 'been',
}


class InvertedIndex:
    """
    An inverted index data structure for efficient search.
    
    Maps words to documents and stores statistics about their occurrences.
    Supports TF-IDF calculations for better ranking.
    
    Attributes:
        index: Dictionary mapping words to posting lists
        documents: Dictionary mapping document IDs to URLs
        word_stats: Statistics for each word (DF, CF, IDF)
        doc_count: Total number of documents in the index
    """
    
    def __init__(self):
        """Initialize an empty inverted index."""
        # word -> [(doc_id, frequency, positions), ...]
        self.index: Dict[str, List[Tuple[int, int, List[int]]]] = {}
        # doc_id -> url
        self.documents: Dict[int, str] = {}
        # word -> Document Frequency (DF), Collection Frequency (CF), IDF
        self.word_stats: Dict[str, Dict] = {}
        # Total number of documents
        self.doc_count: int = 0
        # doc_id -> document length (number of terms)
        self.doc_lengths: Dict[int, int] = {}
        # Average document length (computed after indexing)
        self.avg_doc_len: float = 0.0
    
    def add_document(self, doc_id: int, url: str, words_with_positions: Dict[str, List[int]]) -> None:
        """
        Add a document to the index.
        
        Args:
            doc_id: Unique document identifier
            url: Source URL of the document
            words_with_positions: Dict mapping words to lists of positions they appear at
        """
        self.documents[doc_id] = url
        self.doc_count = max(self.doc_count, doc_id + 1)
        # Document length = total term occurrences in document
        doc_len = sum(len(pos) for pos in words_with_positions.values())
        self.doc_lengths[doc_id] = doc_len
        
        for word, positions in words_with_positions.items():
            word_lower = word.lower()
            frequency = len(positions)
            
            if word_lower not in self.index:
                self.index[word_lower] = []
                self.word_stats[word_lower] = {
                    'df': 0,        # Document Frequency
                    'cf': 0,        # Collection Frequency
                    'idf': 0        # Inverse Document Frequency (calculated later)
                }
            
            self.index[word_lower].append((doc_id, frequency, positions))
            self.word_stats[word_lower]['df'] += 1
            self.word_stats[word_lower]['cf'] += frequency
    
    def calculate_idf(self) -> None:
        """
        Calculate IDF (Inverse Document Frequency) for all words.
        
        IDF = log(total_docs / document_frequency)
        Should be called after all documents are added.
        """
        if self.doc_count == 0:
            return
        
        for word, stats in self.word_stats.items():
            df = stats['df']
            # Add 1 to avoid division by zero
            idf = math.log(self.doc_count / (df + 1)) + 1
            stats['idf'] = idf
        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_len = sum(self.doc_lengths.values()) / len(self.doc_lengths)
        else:
            self.avg_doc_len = 0.0
    
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
    
    def get_word_frequency(self, word: str, doc_id: int) -> int:
        """
        Get frequency of a word in a specific document.
        
        Args:
            word: Word to search for
            doc_id: Document ID
            
        Returns:
            Frequency of the word in the document, or 0 if not found
        """
        postings = self.get_postings(word)
        for posting_doc_id, freq, _ in postings:
            if posting_doc_id == doc_id:
                return freq
        return 0
    
    def get_idf(self, word: str) -> float:
        """
        Get IDF score for a word.
        
        Args:
            word: Word to get IDF for
            
        Returns:
            IDF score, or 0 if word not found
        """
        word_lower = word.lower()
        return self.word_stats.get(word_lower, {}).get('idf', 0)
    
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
            'word_stats': self.word_stats,
            'doc_count': self.doc_count,
            'doc_lengths': self.doc_lengths,
            'avg_doc_len': self.avg_doc_len
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
        inv_index.doc_count = data.get('doc_count', len(inv_index.documents))
        inv_index.doc_lengths = {int(k): int(v) for k, v in data.get('doc_lengths', {}).items()}
        inv_index.avg_doc_len = float(data.get('avg_doc_len', 0.0))
        return inv_index



class Indexer:
    """
    Builds an inverted index from crawled HTML pages.
    
    Features:
    - Stopword filtering for cleaner index
    - Performance monitoring
    - IDF calculation for better ranking
    - Progress tracking
    
    Attributes:
        inv_index: The InvertedIndex object
        index_stats: Indexing statistics
    """
    
    def __init__(self, remove_stopwords: bool = True):
        """
        Initialize the indexer.
        
        Args:
            remove_stopwords: Whether to filter out common stopwords (default: True)
        """
        self.inv_index = InvertedIndex()
        self.remove_stopwords = remove_stopwords
        self.index_stats = {
            'total_words': 0,
            'unique_words': 0,
            'indexing_time': 0,
            'pages_indexed': 0,
            'pages_failed': 0
        }
    
    def _extract_text(self, html: str) -> str:
        """
        Extract plain text from HTML content.
        
        Removes script, style, and other non-visible elements.
        Preserves heading and paragraph structure for better text flow.
        
        Args:
            html: HTML content to process
            
        Returns:
            Cleaned text content
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up multiple whitespace
            text = re.sub(r'\s+', ' ', text)
            
            return text
        except Exception as e:
            logger.warning(f"Error extracting text from HTML: {e}")
            return ""
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words with optional stopword filtering.
        
        Converts to lowercase and extracts only alphabetic words.
        Filters out stopwords if enabled.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of words
        """
        # Convert to lowercase
        text = text.lower()
        # Extract words (only alphabetic characters)
        words = re.findall(r'\b[a-z]+\b', text)
        
        # Filter stopwords if enabled
        if self.remove_stopwords:
            words = [w for w in words if w not in STOPWORDS and len(w) > 1]
        
        return words
    
    def _extract_words_with_positions(self, text: str) -> Dict[str, List[int]]:
        """
        Extract words from text and record their positions.
        
        Tracks positions of each word for phrase queries and highlighting.
        Applies stopword filtering if enabled.
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary mapping words to lists of positions
        """
        text = text.lower()
        words = re.findall(r'\b[a-z]+\b', text)
        
        words_with_positions: Dict[str, List[int]] = {}
        position = 0
        
        for word in words:
            # Skip stopwords if filtering enabled
            if self.remove_stopwords and (word in STOPWORDS or len(word) <= 1):
                position += 1
                continue
            
            if word not in words_with_positions:
                words_with_positions[word] = []
            words_with_positions[word].append(position)
            position += 1
        
        return words_with_positions
    
    def index_pages(self, pages: Dict[str, str]) -> InvertedIndex:
        """
        Build inverted index from a collection of HTML pages.
        
        Processes each page, extracts words, and builds the index.
        Calculates IDF scores after indexing all documents.
        Tracks performance metrics throughout.
        
        Args:
            pages: Dictionary mapping URLs to HTML content
            
        Returns:
            The constructed InvertedIndex object
        """
        logger.info("=" * 60)
        logger.info(f"Starting indexing of {len(pages)} pages...")
        logger.info(f"Stopword filtering: {'Enabled' if self.remove_stopwords else 'Disabled'}")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        for doc_id, (url, html) in enumerate(pages.items()):
            try:
                # Extract text from HTML
                text = self._extract_text(html)
                
                if not text:
                    logger.warning(f"✗ No text extracted from {url}")
                    self.index_stats['pages_failed'] += 1
                    continue
                
                # Extract words with positions
                words_with_positions = self._extract_words_with_positions(text)
                
                if not words_with_positions:
                    logger.warning(f"✗ No words extracted from {url}")
                    self.index_stats['pages_failed'] += 1
                    continue
                
                # Add to index
                self.inv_index.add_document(doc_id, url, words_with_positions)
                
                # Update statistics
                self.index_stats['pages_indexed'] += 1
                self.index_stats['total_words'] += sum(len(pos) for pos in words_with_positions.values())
                
                # Progress report every 10 pages
                if (doc_id + 1) % 10 == 0:
                    logger.info(f"✓ Progress: Indexed {doc_id + 1} pages...")
                    
            except Exception as e:
                logger.error(f"✗ Error indexing page {url}: {e}")
                self.index_stats['pages_failed'] += 1
                continue
        
        # Calculate IDF for all words
        self.inv_index.calculate_idf()
        self.index_stats['unique_words'] = len(self.inv_index.index)
        self.index_stats['indexing_time'] = time.time() - start_time
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("Indexing Complete:")
        logger.info(f"  ✓ Pages indexed: {self.index_stats['pages_indexed']}")
        logger.info(f"  ✗ Pages failed: {self.index_stats['pages_failed']}")
        logger.info(f"  📝 Total words processed: {self.index_stats['total_words']}")
        logger.info(f"  🔑 Unique words in index: {self.index_stats['unique_words']}")
        logger.info(f"  ⏱ Indexing time: {self.index_stats['indexing_time']:.2f} seconds")
        logger.info("=" * 60)
        
        return self.inv_index
    
    def get_index(self) -> InvertedIndex:
        """
        Get the constructed index.
        
        Returns:
            The InvertedIndex object
        """
        return self.inv_index
    
    def get_stats(self) -> Dict:
        """
        Get indexing statistics.
        
        Returns:
            Dictionary with indexing statistics
        """
        return self.index_stats.copy()
