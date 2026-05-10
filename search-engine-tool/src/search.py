"""
Search module for querying the inverted index.

Provides functionality to search for single words and multi-word phrases
using the inverted index.
"""

from typing import List, Dict, Set, Tuple
from indexer import InvertedIndex
import logging
import math

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
        # Scoring method: 'bm25' or 'tfidf'
        self.scoring: str = 'bm25'
        # Simple in-memory cache for query -> ranked results
        self._cache: Dict[tuple, List[Tuple[int, float]]] = {}
    
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

        # Use TF-IDF ranking for results
        ranked_urls = self.find_ranked(query, top_n=50)
        return ranked_urls

    def find_ranked(self, query: str, top_n: int = 10) -> List[str]:
        """
        Find pages matching a query and return URLs ranked by TF-IDF score.

        Args:
            query: Search query (one or more words)
            top_n: Maximum number of results to return

        Returns:
            List of URLs sorted by descending TF-IDF score
        """
        if not query or not query.strip():
            return []

        key = (query.strip().lower(), top_n, self.scoring)
        if key in self._cache:
            postings = self._cache[key]
        else:
            words = query.strip().lower().split()
            words = [w for w in words if w]

            # For multi-word queries, require AND semantics: only consider docs that contain all words
            if len(words) > 1:
                doc_sets = []
                for w in words:
                    if self.inv_index.contains_word(w):
                        doc_sets.append(set(self.inv_index.get_documents_for_word(w)))
                    else:
                        # one word missing -> no results
                        self._cache[key] = []
                        return []
                candidate_docs = set.intersection(*doc_sets) if doc_sets else set()
            else:
                # single-word: all documents containing the word are candidates
                candidate_docs = set(self.inv_index.get_documents_for_word(words[0])) if words else set()

            # Compute scores according to chosen scoring method
            if self.scoring == 'bm25':
                scores = self._bm25_scores(words)
            else:
                scores = self._compute_scores(words)
            # Filter scores to candidate docs only
            filtered = {doc_id: score for doc_id, score in scores.items() if doc_id in candidate_docs}
            # Convert to list of tuples and sort
            postings = sorted(filtered.items(), key=lambda kv: kv[1], reverse=True)
            # Cache top results (doc_id, score)
            self._cache[key] = postings[:top_n]

        urls = [self.inv_index.documents.get(doc_id, "UNKNOWN") for doc_id, _ in self._cache[key]]
        return urls

    def _compute_scores(self, words: List[str]) -> Dict[int, float]:
        """
        Compute TF-IDF style scores for documents given query words.

        Returns a mapping doc_id -> score.
        """
        scores: Dict[int, float] = {}

        for word in words:
            word_lower = word.lower()
            idf = self.inv_index.get_idf(word_lower) or 1.0
            postings = self.inv_index.get_postings(word_lower)
            for doc_id, freq, positions in postings:
                # TF as raw frequency; weight by IDF
                scores[doc_id] = scores.get(doc_id, 0.0) + (freq * idf)

        return scores

    def _bm25_scores(self, words: List[str], k1: float = 1.5, b: float = 0.75) -> Dict[int, float]:
        """
        Compute BM25 scores for documents given query words.

        Returns a mapping doc_id -> score.
        """
        scores: Dict[int, float] = {}
        N = max(1, self.inv_index.doc_count)
        avgdl = getattr(self.inv_index, 'avg_doc_len', 0.0) or 0.0

        for word in words:
            w = word.lower()
            postings = self.inv_index.get_postings(w)
            df = len(postings)
            # BM25 idf with smoothing
            idf = 0.0
            try:
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
            except Exception:
                idf = 0.0

            for doc_id, freq, positions in postings:
                dl = self.inv_index.doc_lengths.get(doc_id, 0)
                denom = freq + k1 * (1 - b + b * (dl / avgdl)) if avgdl > 0 else freq + k1
                score = idf * ((freq * (k1 + 1)) / denom) if denom > 0 else 0.0
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        return scores

    def clear_cache(self) -> None:
        """Clear the internal query cache."""
        self._cache.clear()
    
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
