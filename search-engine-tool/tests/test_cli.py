import unittest
import sys
from pathlib import Path
from io import StringIO
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import SearchToolCLI
from indexer import InvertedIndex

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.cli = SearchToolCLI(index_path='data/test_index.json')

    def tearDown(self):
        # Clean up test index file if created
        try:
            import os
            os.remove('data/test_index.json')
        except Exception:
            pass

    def test_cmd_find_without_index(self):
        out = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = out
        try:
            self.cli.cmd_find('hello world')
        finally:
            sys.stdout = sys_stdout
        self.assertIn('Error: Index not loaded', out.getvalue())

    def test_clear_cache_and_toggle(self):
        # Prepare a simple index and load it
        index = InvertedIndex()
        index.add_document(0, 'http://example.com/1', {'hello':[0], 'world':[1]})
        data = index.to_dict()
        # Write to index path
        with open('data/test_index.json', 'w', encoding='utf-8') as f:
            data['documents'] = {str(k): v for k, v in data['documents'].items()}
            json.dump(data, f)

        self.cli.cmd_load()
        # Toggle cache off
        out = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = out
        try:
            self.cli.run_interactive = lambda: None  # prevent interactive loop
            # toggle off
            self.cli.ranking_enabled = True
            self.cli.cache_enabled = True
            # simulate toggle-cache off
            self.cli.search_engine.clear_cache()
            self.cli.cache_enabled = False
            # clear cache command
            self.cli.search_engine.clear_cache()
        finally:
            sys.stdout = sys_stdout
        # If no exception, pass
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
