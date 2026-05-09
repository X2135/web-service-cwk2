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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Crawler:
    """
    A web crawler that respectfully scrapes pages from a target website.
    
    Attributes:
        base_url: The starting URL to crawl from
        politeness_window: Minimum seconds to wait between requests
        visited_urls: Set of URLs already visited
        pages: Dictionary storing page content
    """
    
    def __init__(self, base_url: str = "https://quotes.toscrape.com", 
                 politeness_window: int = 6):
        """
        Initialize the crawler.
        
        Args:
            base_url: Starting URL to crawl from
            politeness_window: Minimum seconds between requests (default: 6)
        """
        self.base_url = base_url
        self.politeness_window = politeness_window
        self.visited_urls: Set[str] = set()
        self.pages: Dict[str, str] = {}  # url -> html content
        self.last_request_time = 0
    
    def _respect_politeness_window(self) -> None:
        """Wait to respect the politeness window before making a request."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.politeness_window:
            wait_time = self.politeness_window - elapsed
            logger.info(f"Waiting {wait_time:.2f} seconds for politeness window...")
            time.sleep(wait_time)
    
    def _get_page_content(self, url: str) -> str:
        """
        Fetch and return the HTML content of a page.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            requests.RequestException: If the request fails
        """
        self._respect_politeness_window()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            self.last_request_time = time.time()
            logger.info(f"Successfully fetched: {url}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL belongs to the target domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid and belongs to base domain
        """
        parsed_url = urlparse(url)
        parsed_base = urlparse(self.base_url)
        return parsed_url.netloc == parsed_base.netloc
    
    def _extract_links(self, html: str, current_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html: HTML content to parse
            current_url: Current page URL (for resolving relative links)
            
        Returns:
            List of absolute URLs found in the page
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            url = urljoin(current_url, link['href'])
            # Remove fragments
            url = url.split('#')[0]
            
            if self._is_valid_url(url) and url not in self.visited_urls:
                links.append(url)
        
        return links
    
    def crawl(self, start_url: str = None) -> Dict[str, str]:
        """
        Crawl the website starting from the base URL.
        
        Uses breadth-first search to explore all reachable pages.
        
        Args:
            start_url: Optional starting URL (defaults to base_url)
            
        Returns:
            Dictionary mapping URLs to HTML content
        """
        if start_url is None:
            start_url = self.base_url
        
        to_visit = [start_url]
        logger.info(f"Starting crawl from {start_url}")
        
        while to_visit:
            current_url = to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            
            try:
                html_content = self._get_page_content(current_url)
                self.pages[current_url] = html_content
                
                # Extract and queue new links
                new_links = self._extract_links(html_content, current_url)
                to_visit.extend(new_links)
                
                logger.info(f"Crawled {len(self.visited_urls)} pages so far...")
                
            except requests.RequestException:
                logger.warning(f"Skipping {current_url} due to fetch error")
                continue
        
        logger.info(f"Crawling complete. Total pages: {len(self.pages)}")
        return self.pages
    
    def get_pages(self) -> Dict[str, str]:
        """
        Get all crawled pages.
        
        Returns:
            Dictionary mapping URLs to HTML content
        """
        return self.pages
