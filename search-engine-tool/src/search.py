"""
Search module for querying the inverted index.

Provides functionality to search for single words and multi-word phrases
using the inverted index.
"""

from typing import List, Dict, Set, Tuple
from indexer import InvertedIndex
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Search engine interface for querying the inverted index.
    
    Attributes:
        inv_index: The InvertedIndex to search against
    """
    
    def __init__(self, inv_index: InvertedIndex):
        """
        Initialize the search engine with an index.
        
        Args:
            inv_index: InvertedIndex object to search
        """
        self.inv_index = inv_index
    
    def print_index(self, word: str) -> Dict:
        """
        Print the inverted index entry for a specific word.
        
        Args:
            word: Word to look up
            
        Returns:
            Dictionary containing postings for the word with document details
        """
        if not word:
            logger.warning("Empty word provided to print_index")
            return {}
        
        word_lower = word.lower()
        
        if not self.inv_index.contains_word(word_lower):
            logger.info(f"Word '{word}' not found in index")
            return {}
        
        postings = self.inv_index.get_postings(word_lower)
        result = {
            'word': word_lower,
            'document_frequency': len(postings),
            'postings': []
        }
        
        for doc_id, frequency, positions in postings:
            url = self.inv_index.documents.get(doc_id, "UNKNOWN")
            result['postings'].append({
                'doc_id': doc_id,
                'url': url,
                'frequency': frequency,
                'positions': positions[:10]  # Show first 10 positions
            })
        
        return result
    
    def find_single_word(self, word: str) -> List[str]:
        """
        Find all pages containing a specific word.
        
        Args:
            word: Word to search for
            
        Returns:
            List of URLs containing the word
        """
        if not word:
            logger.warning("Empty word provided to find_single_word")
            return []
        
        word_lower = word.lower()
        doc_ids = self.inv_index.get_documents_for_word(word_lower)
        
        urls = [self.inv_index.documents[doc_id] for doc_id in doc_ids]
        return urls
    
    def find_multi_word(self, words: List[str]) -> List[str]:
        """
        Find pages containing ALL specified words (AND query).
        
        Args:
            words: List of words to search for
            
        Returns:
            List of URLs containing all words
        """
        if not words:
            logger.warning("Empty word list provided to find_multi_word")
            return []
        
        # Get document sets for each word
        doc_sets = []
        for word in words:
            word_lower = word.lower()
            if self.inv_index.contains_word(word_lower):
                doc_ids = self.inv_index.get_documents_for_word(word_lower)
                doc_sets.append(set(doc_ids))
            else:
                # If any word is not found, intersection will be empty
                logger.info(f"Word '{word}' not found in index")
                return []
        
        if not doc_sets:
            return []
        
        # Find intersection of all document sets
        result_doc_ids = set.intersection(*doc_sets)
        
        urls = [self.inv_index.documents[doc_id] for doc_id in sorted(result_doc_ids)]
        return urls
    
    def find(self, query: str) -> List[str]:
        """
        Find pages matching a search query.
        
        Supports both single and multi-word queries using AND logic.
        
        Args:
            query: Search query (one or more words)
            
        Returns:
            List of URLs matching the query
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        # Tokenize query
        words = query.strip().lower().split()
        words = [w for w in words if w]  # Remove empty strings
        
        if not words:
            return []
        
        if len(words) == 1:
            return self.find_single_word(words[0])
        else:
            return self.find_multi_word(words)
    
    def search_with_stats(self, query: str) -> Dict:
        """
        Search with detailed statistics.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results and statistics
        """
        results = self.find(query)
        
        words = query.strip().lower().split()
        words = [w for w in words if w]
        
        stats = {
            'query': query,
            'num_words': len(words),
            'results_found': len(results),
            'urls': results
        }
        
        return stats
    
    def fuzzy_match(self, query: str, max_distance: int = 1) -> List[str]:
        """
        Find pages with fuzzy matching (handles typos).
        
        Simple implementation using edit distance.
        
        Args:
            query: Search query
            max_distance: Maximum edit distance to consider
            
        Returns:
            List of URLs with fuzzy-matched words
        """
        words = query.strip().lower().split()
        words = [w for w in words if w]
        
        if not words:
            return []
        
        # Try direct match first
        direct_results = self.find(query)
        if direct_results:
            return direct_results
        
        # Try fuzzy matching on first word
        target_word = words[0]
        
        # Find similar words in index
        similar_words = []
        for indexed_word in self.inv_index.index.keys():
            if self._edit_distance(target_word, indexed_word) <= max_distance:
                similar_words.append(indexed_word)
        
        if similar_words:
            logger.info(f"Fuzzy matches for '{target_word}': {similar_words}")
            results = self.find_single_word(similar_words[0])
            return results
        
        logger.info(f"No fuzzy matches found for '{query}'")
        return []
    
    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """
        Calculate edit distance between two strings.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return SearchEngine._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
