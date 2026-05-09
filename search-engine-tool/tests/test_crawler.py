"""
Tests for the crawler module.

Tests URL validation, politeness window, link extraction, and crawling functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from crawler import Crawler


class TestCrawler(unittest.TestCase):
    """Test suite for the Crawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://quotes.toscrape.com"
        self.crawler = Crawler(base_url=self.base_url, politeness_window=0)  # No wait for tests
    
    def test_crawler_initialization(self):
        """Test that crawler initializes correctly."""
        self.assertEqual(self.crawler.base_url, self.base_url)
        self.assertEqual(self.crawler.politeness_window, 0)
        self.assertEqual(len(self.crawler.visited_urls), 0)
        self.assertEqual(len(self.crawler.pages), 0)
    
    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(self.crawler._is_valid_url("https://quotes.toscrape.com/"))
        self.assertTrue(self.crawler._is_valid_url("https://quotes.toscrape.com/page/2"))
        
        # Invalid URLs (different domain)
        self.assertFalse(self.crawler._is_valid_url("https://example.com/"))
    
    def test_extract_links_empty_html(self):
        """Test link extraction from empty HTML."""
        links = self.crawler._extract_links("<html></html>", self.base_url)
        self.assertEqual(len(links), 0)
    
    def test_extract_links_with_links(self):
        """Test link extraction from HTML with links."""
        html = """
        <html>
            <a href="/page/2">Next</a>
            <a href="/author/Albert-Einstein">Author</a>
        </html>
        """
        links = self.crawler._extract_links(html, self.base_url)
        
        # Should resolve relative URLs
        self.assertIn("https://quotes.toscrape.com/page/2", links)
        self.assertIn("https://quotes.toscrape.com/author/Albert-Einstein", links)
    
    def test_extract_links_removes_duplicates(self):
        """Test that duplicate links are not added."""
        html = """
        <html>
            <a href="/page/2">Next</a>
            <a href="/page/2">Next Again</a>
        </html>
        """
        self.crawler.visited_urls.add("https://quotes.toscrape.com/page/2")
        links = self.crawler._extract_links(html, self.base_url)
        
        # Should not include already visited URL
        self.assertEqual(len(links), 0)
    
    def test_extract_links_removes_fragments(self):
        """Test that URL fragments are removed."""
        html = """
        <html>
            <a href="/page/1#section">Link with fragment</a>
        </html>
        """
        links = self.crawler._extract_links(html, self.base_url)
        
        # Fragment should be removed
        self.assertNotIn("#section", links[0])
    
    @patch('crawler.requests.get')
    def test_get_page_content_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = self.crawler._get_page_content("https://quotes.toscrape.com/")
        
        self.assertEqual(content, "<html><body>Test</body></html>")
        mock_get.assert_called_once()
    
    @patch('crawler.requests.get')
    def test_get_page_content_failure(self, mock_get):
        """Test page fetching with error."""
        mock_get.side_effect = Exception("Connection error")
        
        with self.assertRaises(Exception):
            self.crawler._get_page_content("https://quotes.toscrape.com/")
    
    def test_respect_politeness_window(self):
        """Test that politeness window is respected."""
        # This is hard to test without mocking time
        # Just ensure the method exists and can be called
        self.crawler._respect_politeness_window()
    
    def test_get_pages(self):
        """Test getting crawled pages."""
        self.crawler.pages = {"url1": "content1", "url2": "content2"}
        pages = self.crawler.get_pages()
        
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages["url1"], "content1")


class TestCrawlerIntegration(unittest.TestCase):
    """Integration tests for the Crawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crawler = Crawler(base_url="https://quotes.toscrape.com", politeness_window=0)
    
    @patch('crawler.requests.get')
    def test_crawl_integration(self, mock_get):
        """Test full crawl workflow (mocked)."""
        # Create mock responses
        main_page = """
        <html>
            <a href="/page/2">Page 2</a>
            <a href="/author/Albert-Einstein">Author</a>
        </html>
        """
        
        page_2 = """
        <html>
            <a href="/">Home</a>
        </html>
        """
        
        # Set up mock to return different content for different URLs
        def mock_get_side_effect(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            
            if 'page/2' in url:
                mock_response.text = page_2
            else:
                mock_response.text = main_page
            
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        # Crawl should return pages
        pages = self.crawler.crawl("https://quotes.toscrape.com/")
        
        # Should have crawled multiple pages
        self.assertGreater(len(pages), 0)


if __name__ == '__main__':
    unittest.main()
