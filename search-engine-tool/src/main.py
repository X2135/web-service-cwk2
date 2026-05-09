"""
Main module providing the command-line interface for the search tool.

Implements commands: build, load, print, find
"""

import sys
import json
import os
from pathlib import Path
from typing import Optional
import logging

from crawler import Crawler
from indexer import Indexer, InvertedIndex
from search import SearchEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_INDEX_PATH = 'data/index.json'
DEFAULT_DOCUMENTS_PATH = 'data/documents.json'


class SearchToolCLI:
    """
    Command-line interface for the search tool.
    
    Handles user input and executes search, indexing, and loading operations.
    """
    
    def __init__(self, index_path: str = DEFAULT_INDEX_PATH, 
                 documents_path: str = DEFAULT_DOCUMENTS_PATH):
        """
        Initialize the CLI.
        
        Args:
            index_path: Path to save/load the index file
            documents_path: Path to save/load the documents mapping
        """
        self.index_path = index_path
        self.documents_path = documents_path
        self.inv_index: Optional[InvertedIndex] = None
        self.search_engine: Optional[SearchEngine] = None
        
        # Ensure data directory exists
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    
    def cmd_build(self, url: str = "https://quotes.toscrape.com") -> None:
        """
        Build the index by crawling the website.
        
        Usage: build [url]
        
        Args:
            url: Website URL to crawl (default: quotes.toscrape.com)
        """
        logger.info(f"Starting crawl of {url}...")
        
        try:
            # Step 1: Crawl the website
            crawler = Crawler(base_url=url)
            pages = crawler.crawl(url)
            logger.info(f"Crawled {len(pages)} pages")
            
            # Step 2: Index the pages
            logger.info("Building index...")
            indexer = Indexer()
            self.inv_index = indexer.index_pages(pages)
            self.search_engine = SearchEngine(self.inv_index)
            
            # Step 3: Save index to file
            self._save_index()
            
            logger.info(f"✓ Index built successfully with {len(self.inv_index.index)} unique words")
            print(f"\nIndex built successfully!")
            print(f"  - Pages crawled: {len(pages)}")
            print(f"  - Unique words: {len(self.inv_index.index)}")
            print(f"  - Index saved to: {self.index_path}")
            
        except Exception as e:
            logger.error(f"Error during build: {e}")
            print(f"Error: Failed to build index - {e}")
    
    def cmd_load(self) -> None:
        """
        Load the index from file.
        
        Usage: load
        """
        try:
            if not os.path.exists(self.index_path):
                print(f"Error: Index file not found at {self.index_path}")
                print("Please run 'build' command first.")
                return
            
            self._load_index()
            logger.info("Index loaded successfully")
            print(f"✓ Index loaded successfully from {self.index_path}")
            print(f"  - Unique words: {len(self.inv_index.index)}")
            print(f"  - Indexed pages: {len(self.inv_index.documents)}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            print(f"Error: Failed to load index - {e}")
    
    def cmd_print(self, word: str) -> None:
        """
        Print the inverted index for a word.
        
        Usage: print <word>
        
        Args:
            word: Word to look up in the index
        """
        if not self.search_engine:
            print("Error: Index not loaded. Please run 'load' command first.")
            return
        
        if not word:
            print("Error: Please provide a word to print.")
            return
        
        result = self.search_engine.print_index(word)
        
        if not result:
            print(f"Word '{word}' not found in index")
            return
        
        print(f"\n=== Index Entry for '{word}' ===")
        print(f"Document Frequency: {result['document_frequency']}")
        print(f"\nPostings:")
        print("-" * 80)
        
        for posting in result['postings']:
            print(f"  Doc ID: {posting['doc_id']}")
            print(f"  URL: {posting['url']}")
            print(f"  Frequency: {posting['frequency']}")
            print(f"  Positions: {posting['positions']}")
            print()
    
    def cmd_find(self, query: str) -> None:
        """
        Find pages containing search terms.
        
        Usage: find <query>
        Supports single or multiple words (AND logic).
        
        Args:
            query: Search query (one or more words)
        """
        if not self.search_engine:
            print("Error: Index not loaded. Please run 'load' command first.")
            return
        
        if not query or not query.strip():
            print("Error: Please provide a search query.")
            return
        
        results = self.search_engine.find(query)
        
        print(f"\n=== Search Results for '{query}' ===")
        print(f"Found {len(results)} page(s):")
        print("-" * 80)
        
        if results:
            for i, url in enumerate(results, 1):
                print(f"{i}. {url}")
        else:
            print("No results found.")
        print()
    
    def _save_index(self) -> None:
        """Save the index to a JSON file."""
        if not self.inv_index:
            raise ValueError("No index to save")
        
        # Convert index to serializable format
        index_data = self.inv_index.to_dict()
        
        # Convert string keys in documents dict to int keys for JSON
        index_data['documents'] = {str(k): v for k, v in index_data['documents'].items()}
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Index saved to {self.index_path}")
    
    def _load_index(self) -> None:
        """Load the index from a JSON file."""
        with open(self.index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # Convert string keys back to int for documents
        index_data['documents'] = {int(k): v for k, v in index_data['documents'].items()}
        
        self.inv_index = InvertedIndex.from_dict(index_data)
        self.search_engine = SearchEngine(self.inv_index)
        
        logger.info(f"Index loaded from {self.index_path}")
    
    def run_interactive(self) -> None:
        """Run the interactive command-line interface."""
        print("=" * 80)
        print("Search Engine Tool - Interactive CLI")
        print("=" * 80)
        print("\nAvailable commands:")
        print("  build          - Crawl website and build index")
        print("  load           - Load index from file")
        print("  print <word>   - Print index entry for a word")
        print("  find <query>   - Find pages containing search terms")
        print("  help           - Show this help message")
        print("  exit/quit      - Exit the program")
        print("-" * 80)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(None, 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == "exit" or command == "quit":
                    print("Goodbye!")
                    break
                elif command == "help":
                    self._print_help()
                elif command == "build":
                    url = args if args else "https://quotes.toscrape.com"
                    self.cmd_build(url)
                elif command == "load":
                    self.cmd_load()
                elif command == "print":
                    if not args:
                        print("Usage: print <word>")
                    else:
                        self.cmd_print(args)
                elif command == "find":
                    if not args:
                        print("Usage: find <query>")
                    else:
                        self.cmd_find(args)
                else:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                print(f"Error: {e}")
    
    @staticmethod
    def _print_help() -> None:
        """Print help information."""
        print("""
Commands:
  build              - Crawl the target website and build the inverted index
  load               - Load a previously built index from file
  print <word>       - Print the inverted index entry for a specific word
  find <query>       - Find all pages containing the search query
                       Supports multi-word queries (uses AND logic)
  help               - Show this help message
  exit/quit          - Exit the program

Examples:
  > build
  > load
  > print good
  > find good friends
        """)


def main():
    """Main entry point for the search tool."""
    cli = SearchToolCLI()
    
    if len(sys.argv) > 1:
        # Command-line arguments provided
        command = sys.argv[1].lower()
        
        if command == "build":
            url = sys.argv[2] if len(sys.argv) > 2 else "https://quotes.toscrape.com"
            cli.cmd_build(url)
        elif command == "load":
            cli.cmd_load()
        elif command == "print":
            if len(sys.argv) > 2:
                cli.cmd_print(sys.argv[2])
            else:
                print("Usage: python main.py print <word>")
        elif command == "find":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                cli.cmd_find(query)
            else:
                print("Usage: python main.py find <query>")
        else:
            print(f"Unknown command: {command}")
            print("Available commands: build, load, print, find")
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == "__main__":
    main()
