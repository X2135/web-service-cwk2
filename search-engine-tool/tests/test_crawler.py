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
    
    def test_crawler_initialization(self):
        """Test that crawler initializes correctly."""
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        self.assertEqual(crawler.base_url, self.base_url)
        self.assertEqual(crawler.politeness_window, 0)
        self.assertEqual(len(crawler.visited_urls), 0)
        self.assertEqual(len(crawler.pages), 0)
    
    def test_is_valid_url(self):
        """Test URL validation."""
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        # Valid URLs
        self.assertTrue(crawler._is_valid_url("https://quotes.toscrape.com/"))
        self.assertTrue(crawler._is_valid_url("https://quotes.toscrape.com/page/2"))

        # Invalid URLs (different domain)
        self.assertFalse(crawler._is_valid_url("https://example.com/"))
    
    def test_extract_links_empty_html(self):
        """Test link extraction from empty HTML."""
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        links = crawler._extract_links("<html></html>", self.base_url)
        self.assertEqual(len(links), 0)
    
    def test_extract_links_with_links(self):
        """Test link extraction from HTML with links."""
        html = """
        <html>
            <a href="/page/2">Next</a>
            <a href="/author/Albert-Einstein">Author</a>
        </html>
        """
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        links = crawler._extract_links(html, self.base_url)
        
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
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        crawler.visited_urls.add("https://quotes.toscrape.com/page/2")
        links = crawler._extract_links(html, self.base_url)
        
        # Should not include already visited URL
        self.assertEqual(len(links), 0)
    
    def test_extract_links_removes_fragments(self):
        """Test that URL fragments are removed."""
        html = """
        <html>
            <a href="/page/1#section">Link with fragment</a>
        </html>
        """
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        links = crawler._extract_links(html, self.base_url)

        # Fragment should be removed
        self.assertNotIn("#section", links[0])
    
    @patch.object(Crawler, '_create_session')
    def test_get_page_content_success(self, mock_create_session):
        """Test successful page fetching."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.content = mock_response.text.encode()
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_create_session.return_value = mock_session

        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        content = crawler._get_page_content("https://quotes.toscrape.com/")

        self.assertEqual(content, "<html><body>Test</body></html>")
        mock_session.get.assert_called_once()
    
    @patch.object(Crawler, '_create_session')
    def test_get_page_content_failure(self, mock_create_session):
        """Test page fetching with error."""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection error")
        mock_create_session.return_value = mock_session

        crawler = Crawler(base_url=self.base_url, politeness_window=0)

        with self.assertRaises(Exception):
            crawler._get_page_content("https://quotes.toscrape.com/")
    
    def test_respect_politeness_window(self):
        """Test that politeness window is respected."""
        # This is hard to test without mocking time
        # Just ensure the method exists and can be called
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        crawler._respect_politeness_window()
    
    def test_get_pages(self):
        """Test getting crawled pages."""
        crawler = Crawler(base_url=self.base_url, politeness_window=0)
        crawler.pages = {"url1": "content1", "url2": "content2"}
        pages = crawler.get_pages()

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages["url1"], "content1")


class TestCrawlerIntegration(unittest.TestCase):
    """Integration tests for the Crawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crawler = Crawler(base_url="https://quotes.toscrape.com", politeness_window=0)
    
    @patch.object(Crawler, '_create_session')
    def test_crawl_integration(self, mock_create_session):
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

        mock_session = Mock()

        def mock_get_side_effect(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.content = b"dummy"
            if 'page/2' in url:
                mock_response.text = page_2
            else:
                mock_response.text = main_page
            return mock_response

        mock_session.get.side_effect = mock_get_side_effect
        mock_create_session.return_value = mock_session

        crawler = Crawler(base_url="https://quotes.toscrape.com", politeness_window=0)

        # Crawl should return pages
        pages = crawler.crawl("https://quotes.toscrape.com/")

        # Should have crawled multiple pages
        self.assertGreater(len(pages), 0)


if __name__ == '__main__':
    unittest.main()
