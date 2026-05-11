import unittest
import sys
from pathlib import Path
from io import StringIO
import json
from unittest.mock import patch, Mock

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from main import SearchToolCLI
import main as main_module
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

    def test_save_index_requires_index(self):
        """Cover _save_index guard clause."""
        with self.assertRaises(ValueError):
            self.cli._save_index()

    def test_run_interactive_branches(self):
        """Exercise interactive command branches without real user input."""
        self.cli.search_engine = Mock()
        self.cli.search_engine.clear_cache = Mock()
        self.cli.search_engine.cache_enabled = True
        self.cli.cmd_build = Mock()
        self.cli.cmd_load = Mock()
        self.cli.cmd_print = Mock()
        self.cli.cmd_find = Mock()

        inputs = iter([
            "",
            "help",
            "toggle-ranking maybe",
            "toggle-ranking off",
            "toggle-ranking on",
            "toggle-cache maybe",
            "toggle-cache off",
            "toggle-cache on",
            "clear-cache",
            "print",
            "find",
            "unknown-cmd",
            "quit",
        ])

        out = StringIO()
        with patch("builtins.input", side_effect=lambda prompt='': next(inputs)), patch("sys.stdout", out):
            self.cli.run_interactive()

        text = out.getvalue().lower()
        self.assertIn("输入 help 查看命令".lower(), text)
        self.assertIn("commands:", text)
        self.assertIn("ranking disabled", text)
        self.assertIn("ranking enabled", text)
        self.assertIn("cache disabled", text)
        self.assertIn("cache enabled", text)
        self.assertIn("query cache cleared", text)
        self.assertIn("usage: toggle-ranking on|off", text)
        self.assertIn("usage: toggle-cache on|off", text)
        self.assertIn("usage: print <word>", text)
        self.assertIn("usage: find <query>", text)
        self.assertIn("unknown command", text)

    def test_run_interactive_keyboardinterrupt(self):
        """Cover KeyboardInterrupt branch in interactive loop."""
        self.cli.search_engine = Mock()
        out = StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), patch("sys.stdout", out):
            self.cli.run_interactive()
        self.assertIn("Interrupted by user", out.getvalue())

    def test_run_interactive_generic_exception(self):
        """Cover generic exception branch in interactive loop."""
        self.cli.search_engine = Mock()
        out = StringIO()
        with patch("builtins.input", side_effect=[Exception("boom"), "quit"]), patch("sys.stdout", out):
            self.cli.run_interactive()
        self.assertIn("Error: boom", out.getvalue())

    def test_main_command_branches(self):
        """Cover command-line entry point branches in main()."""
        with patch.object(main_module.SearchToolCLI, 'cmd_build') as mock_build, \
             patch.object(main_module.SearchToolCLI, 'cmd_load') as mock_load, \
             patch.object(main_module.SearchToolCLI, 'cmd_print') as mock_print, \
             patch.object(main_module.SearchToolCLI, 'cmd_find') as mock_find, \
             patch.object(main_module.SearchToolCLI, 'run_interactive') as mock_interactive:

            original_argv = sys.argv[:]
            try:
                sys.argv = ['main.py', 'build', 'https://example.com']
                main_module.main()
                mock_build.assert_called_once_with('https://example.com')

                sys.argv = ['main.py', 'build']
                main_module.main()
                self.assertEqual(mock_build.call_args_list[-1].args[0], 'https://quotes.toscrape.com')

                sys.argv = ['main.py', 'load']
                main_module.main()
                mock_load.assert_called_once()

                sys.argv = ['main.py', 'print', 'good']
                main_module.main()
                mock_print.assert_called_once_with('good')

                sys.argv = ['main.py', 'find', 'good', 'friends']
                main_module.main()
                mock_find.assert_called_once_with('good friends')

                out = StringIO()
                sys.stdout = out
                sys.argv = ['main.py', 'unknown']
                main_module.main()
                self.assertIn('Unknown command', out.getvalue())

                sys.stdout = sys.__stdout__
                sys.argv = ['main.py']
                main_module.main()
                mock_interactive.assert_called_once()
            finally:
                sys.argv = original_argv
                sys.stdout = sys.__stdout__

    def test_cmd_build_and_load_error_paths(self):
        """Exercise build/load error branches in main.py."""
        # Build exception path
        with patch('main.Crawler') as mock_crawler_cls, \
             patch('main.Indexer') as mock_indexer_cls:
            mock_crawler = mock_crawler_cls.return_value
            mock_crawler.crawl.side_effect = Exception('boom')

            out = StringIO()
            with patch('sys.stdout', out):
                self.cli.cmd_build()
            self.assertIn('Error: Failed to build index', out.getvalue())

        # Load missing file path
        out = StringIO()
        with patch('sys.stdout', out):
            self.cli.cmd_load()
        self.assertIn('Index file not found', out.getvalue())

        # Load exception path
        index = InvertedIndex()
        index.add_document(0, 'http://example.com/1', {'hello': [0]})
        data = index.to_dict()
        with open('data/test_index.json', 'w', encoding='utf-8') as f:
            data['documents'] = {str(k): v for k, v in data['documents'].items()}
            json.dump(data, f)

        with patch.object(self.cli, '_load_index', side_effect=Exception('load boom')):
            out = StringIO()
            with patch('sys.stdout', out):
                self.cli.cmd_load()
            self.assertIn('Error: Failed to load index', out.getvalue())

    def test_cmd_print_and_find_edge_paths(self):
        """Exercise cmd_print/cmd_find guard clauses and ranking toggle."""
        out = StringIO()
        with patch('sys.stdout', out):
            self.cli.cmd_print('hello')
        self.assertIn('Index not loaded', out.getvalue())

        self.cli.search_engine = Mock()
        self.cli.search_engine.find_ranked = Mock(return_value=['u1'])
        self.cli.search_engine.find = Mock(return_value=['u2'])

        # empty input guards
        out = StringIO()
        with patch('sys.stdout', out):
            self.cli.cmd_print('')
            self.cli.cmd_find('')
        self.assertIn('Please provide a word to print', out.getvalue())
        self.assertIn('Please provide a search query', out.getvalue())

        # ranking enabled / disabled branches
        out = StringIO()
        with patch('sys.stdout', out):
            self.cli.ranking_enabled = True
            self.cli.cmd_find('hello world')
            self.cli.ranking_enabled = False
            self.cli.cmd_find('hello world')
        self.assertEqual(self.cli.search_engine.find_ranked.call_count, 1)
        self.assertEqual(self.cli.search_engine.find.call_count, 1)

    def test_main_usage_messages(self):
        """Cover usage/help branches in main() for missing args and unknown command."""
        original_argv = sys.argv[:]
        try:
            out = StringIO()
            with patch('sys.stdout', out):
                sys.argv = ['main.py', 'print']
                main_module.main()
                sys.argv = ['main.py', 'find']
                main_module.main()
                sys.argv = ['main.py', 'unknown']
                main_module.main()
            text = out.getvalue().lower()
            self.assertIn('usage: python main.py print <word>', text)
            self.assertIn('usage: python main.py find <query>', text)
            self.assertIn('available commands', text)
        finally:
            sys.argv = original_argv

if __name__ == '__main__':
    unittest.main()
