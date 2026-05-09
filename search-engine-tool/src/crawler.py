"""
Web crawler module for scraping quotes.toscrape.com

This module handles downloading and parsing HTML pages from the target website
while respecting a politeness window between requests.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Crawler:
    """
    A web crawler that respectfully scrapes pages from a target website.
    
    Features:
        - Respects politeness window (6 seconds between requests)
        - Automatic retry on failure
        - Connection pooling and session management
        - Comprehensive error handling and logging
    
    Attributes:
        base_url: The starting URL to crawl from
        politeness_window: Minimum seconds to wait between requests
        visited_urls: Set of URLs already visited
        pages: Dictionary storing page content
        max_retries: Maximum number of retries for failed requests
        timeout: Request timeout in seconds
    """
    
    # Default headers to be respectful
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, base_url: str = "https://quotes.toscrape.com", 
                 politeness_window: int = 6, max_retries: int = 3, timeout: int = 10):
        """
        Initialize the crawler.
        
        Args:
            base_url: Starting URL to crawl from
            politeness_window: Minimum seconds between requests (default: 6)
            max_retries: Maximum retries for failed requests (default: 3)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url
        self.politeness_window = politeness_window
        self.visited_urls: Set[str] = set()
        self.pages: Dict[str, str] = {}  # url -> html content
        self.last_request_time = 0
        self.max_retries = max_retries
        self.timeout = timeout
        self._session = self._create_session()
        self.failed_urls: Dict[str, str] = {}  # url -> error message
        self.crawl_stats = {'pages_crawled': 0, 'pages_failed': 0, 'bytes_downloaded': 0}
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with automatic retry strategy.
        
        Returns:
            Configured requests.Session object with retry logic
        """
        session = requests.Session()
        
        # Configure retry strategy for transient errors
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        logger.info(f"Session created with {self.max_retries} retry attempts")
        return session
    
    def _respect_politeness_window(self) -> None:
        """
        Wait to respect the politeness window before making a request.
        
        Enforces minimum delay between requests to avoid overloading
        the target server. Logs waiting time for transparency.
        """
        if self.last_request_time is None:
            return  # First request, no waiting needed
        
        elapsed = time.time() - self.last_request_time
        
        if elapsed < self.politeness_window:
            wait_time = self.politeness_window - elapsed
            logger.debug(f"⏳ Respecting politeness window: waiting {wait_time:.2f}s...")
            time.sleep(wait_time)
            logger.debug(f"✓ Politeness window respected")
    
    def _get_page_content(self, url: str) -> str:
        """
        Fetch and return the HTML content of a page with automatic retries.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            requests.RequestException: If all retries are exhausted
        """
        self._respect_politeness_window()
        
        try:
            response = self._session.get(
                url, 
                headers=self.DEFAULT_HEADERS, 
                timeout=self.timeout
            )
            response.raise_for_status()
            self.last_request_time = time.time()
            
            # Update statistics
            self.crawl_stats['bytes_downloaded'] += len(response.content)
            
            logger.info(f"✓ Fetched: {url} ({len(response.content)} bytes)")
            return response.text
            
        except requests.Timeout:
            error_msg = f"Timeout after {self.timeout}s"
            logger.error(f"✗ {error_msg}: {url}")
            self.failed_urls[url] = error_msg
            raise
        except requests.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            logger.error(f"✗ {error_msg}: {url}")
            self.failed_urls[url] = error_msg
            raise
        except requests.RequestException as e:
            error_msg = str(e)
            logger.error(f"✗ Request failed: {url} - {error_msg}")
            self.failed_urls[url] = error_msg
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL belongs to the target domain.
        
        Validates:
        - URL uses HTTP or HTTPS protocol
        - URL belongs to same domain as base_url
        - URL is well-formed
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and belongs to base domain
        """
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(self.base_url)
            
            # Check protocol (only http/https)
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Check domain match
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Additional validation: must have at least a path
            if not parsed_url.netloc:
                return False
            
            return True
        except Exception as e:
            logger.debug(f"URL validation error for {url}: {e}")
            return False
    
    def _extract_links(self, html: str, current_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Filters out:
        - Non-HTTP(S) links
        - Fragment links (#anchor)
        - External links
        - Links already visited
        - Duplicate links
        - JavaScript and mailto links
        
        Args:
            html: HTML content to parse
            current_url: Current page URL (for resolving relative links)
            
        Returns:
            List of unique, valid, absolute URLs found in the page
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            
            if not href:
                continue
            
            # Skip special links
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Resolve relative URLs to absolute
            url = urljoin(current_url, href)
            
            # Remove fragments for cleaner URLs
            url = url.split('#')[0]
            
            # Only add if valid domain and not already visited
            if self._is_valid_url(url) and url not in self.visited_urls:
                links.add(url)
        
        return list(links)
    
    def crawl(self, start_url: str = None, max_pages: int = None) -> Dict[str, str]:
        """
        Crawl the website starting from the base URL.
        
        Uses breadth-first search to explore all reachable pages.
        Respects politeness window and handles errors gracefully.
        
        Args:
            start_url: Optional starting URL (defaults to base_url)
            max_pages: Optional maximum pages to crawl (None = no limit)
            
        Returns:
            Dictionary mapping URLs to HTML content
        """
        if start_url is None:
            start_url = self.base_url
        
        to_visit = [start_url]
        logger.info("=" * 60)
        logger.info(f"Starting crawl from {start_url}")
        logger.info(f"Politeness window: {self.politeness_window}s, Max retries: {self.max_retries}")
        logger.info("=" * 60)
        
        while to_visit and (max_pages is None or self.crawl_stats['pages_crawled'] < max_pages):
            current_url = to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            
            try:
                html_content = self._get_page_content(current_url)
                self.pages[current_url] = html_content
                self.crawl_stats['pages_crawled'] += 1
                
                # Extract and queue new links
                new_links = self._extract_links(html_content, current_url)
                to_visit.extend(new_links)
                
                # Progress report every 10 pages
                if self.crawl_stats['pages_crawled'] % 10 == 0:
                    logger.info(f"Progress: {self.crawl_stats['pages_crawled']} pages crawled, "
                              f"{len(to_visit)} pages queued")
                
            except requests.RequestException:
                self.crawl_stats['pages_failed'] += 1
                logger.warning(f"Skipping {current_url} (failed after retries)")
                continue
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("Crawl Summary:")
        logger.info(f"  ✓ Pages crawled: {self.crawl_stats['pages_crawled']}")
        logger.info(f"  ✗ Pages failed: {self.crawl_stats['pages_failed']}")
        logger.info(f"  ↓ Data downloaded: {self.crawl_stats['bytes_downloaded'] / 1024:.1f} KB")
        logger.info("=" * 60)
        
        return self.pages
    
    def get_crawl_stats(self) -> Dict:
        """
        Get crawling statistics.
        
        Returns:
            Dictionary with crawl statistics
        """
        return {
            **self.crawl_stats,
            'unique_urls': len(self.visited_urls),
            'failed_urls': len(self.failed_urls)
        }
    
    def get_pages(self) -> Dict[str, str]:
        """
        Get all crawled pages.
        
        Returns:
            Dictionary mapping URLs to HTML content
        """
        return self.pages
