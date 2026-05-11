import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import SearchToolCLI


class TestSmokeE2E(unittest.TestCase):
    """End-to-end smoke tests for the CLI workflow."""

    def test_build_load_print_find_smoke(self):
        """Run a tiny build/load/print/find flow without network access."""
        fake_pages = {
            "https://quotes.toscrape.com/": """
                <html><body>
                    <p>Hello world and good friends.</p>
                    <a href="/page/2/">Next</a>
                </body></html>
            """,
            "https://quotes.toscrape.com/page/2/": """
                <html><body>
                    <p>Good friends say hello again.</p>
                </body></html>
            """,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "index.json"
            cli = SearchToolCLI(index_path=str(index_path))

            with patch("main.Crawler") as mock_crawler_cls:
                mock_crawler = mock_crawler_cls.return_value
                mock_crawler.crawl.return_value = fake_pages

                build_out = StringIO()
                with patch("sys.stdout", build_out):
                    cli.cmd_build()

            self.assertTrue(index_path.exists(), "build should create an index file")
            self.assertIn("Index built successfully", build_out.getvalue())

            load_out = StringIO()
            with patch("sys.stdout", load_out):
                cli.cmd_load()
            self.assertIn("Index loaded successfully", load_out.getvalue())

            print_out = StringIO()
            with patch("sys.stdout", print_out):
                cli.cmd_print("good")
            print_text = print_out.getvalue().lower()
            self.assertIn("index entry for 'good'", print_text)
            self.assertIn("positions", print_text)

            find_out = StringIO()
            with patch("sys.stdout", find_out):
                cli.ranking_enabled = False
                cli.cmd_find("hello, world!")
            find_text = find_out.getvalue().lower()
            self.assertIn("search results for 'hello, world!'", find_text)
            self.assertIn("page(s)", find_text)
            self.assertIn("quotes.toscrape.com", find_text)

            # Ensure the saved index is not empty
            with index_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertGreater(len(data.get('documents', {})), 0)
            self.assertGreater(len(data.get('index', {})), 0)


if __name__ == '__main__':
    unittest.main()
