# Search Engine Tool

A Python-based web crawler and search engine that indexes and searches pages from [quotes.toscrape.com](https://quotes.toscrape.com).

## Project Overview

This tool implements a complete search engine pipeline:

1. **Web Crawler**: Respectfully crawls web pages while observing a politeness window
2. **Indexer**: Builds an inverted index from crawled content
3. **Search Engine**: Retrieves pages matching search queries
4. **CLI Interface**: Command-line interface for all operations

### Features

- ✅ Web crawling with politeness window (6-second minimum delay)
- ✅ Inverted index with word statistics (frequency, positions)
- ✅ Case-insensitive search
- ✅ Single and multi-word queries (AND logic)
- ✅ Index persistence (save/load from JSON)
- ✅ Ranked retrieval with TF-IDF and BM25
- ✅ Query caching and ranking toggle support
- ✅ Comprehensive test suite + performance regression check
- ✅ GitHub Actions CI for automated verification
- ✅ Error handling and logging
- ✅ Interactive command-line interface

## Architecture

```
src/
  ├── crawler.py      # Web crawler with politeness window
  ├── indexer.py      # Inverted index and indexing logic
  ├── search.py       # Search engine, TF-IDF/BM25 ranking, cache
  └── main.py         # Command-line interface

tests/
  ├── test_crawler.py    # Crawler tests
  ├── test_indexer.py    # Indexer and index tests
  ├── test_search.py     # Search engine tests
  ├── test_search_tfidf.py
  └── test_bm25_ranking.py

data/
  └── index.json      # Generated index file

scripts/
  ├── benchmark.py    # Synthetic benchmark harness
  └── perf_check.py   # CI performance regression check

docs/
  ├── benchmark.md     # Benchmark results and complexity notes
  └── grading_mapping.md

requirements.txt     # Project dependencies
README.md           # This file
```

## Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd search-engine-tool
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode

Run the tool in interactive mode:

```bash
python src/main.py
```

This opens an interactive shell with the following commands:

#### Commands

**`build [url]`** - Crawl the website and build the index
```bash
> build
> build https://quotes.toscrape.com/
```

**`load`** - Load a previously built index
```bash
> load
```

**`print <word>`** - Display the index entry for a word
```bash
> print good
```

Shows:
- Document frequency (how many pages contain the word)
- Posting list with:
  - Document ID
  - Source URL
  - Frequency (times word appears)
  - Positions (where word appears)

**`find <query>`** - Search for pages containing search terms
```bash
> find good
> find good friends
```

Returns a list of URLs containing all search terms (AND logic).

### Command-Line Mode

Execute single commands from the terminal:

```bash
# Build index
python src/main.py build

# Load index
python src/main.py load

# Print index entry
python src/main.py print good

# Find pages
python src/main.py find good friends
```

## Testing

### Run All Tests

```bash
PYTHONPATH=./src python3 -m unittest discover -v
```

or

```bash
cd tests
python -m pytest
```

### Run Specific Test Suite

```bash
# Test crawler
python -m unittest tests.test_crawler

# Test indexer
python -m unittest tests.test_indexer

# Test search engine
python -m unittest tests.test_search
```

### Test Coverage

Generate coverage report:

```bash
pip install coverage
coverage run -m unittest discover tests
coverage report
coverage html  # Generate HTML report
```

### Performance Check

Run the small CI-style performance regression check:

```bash
PYTHONPATH=./src python3 scripts/perf_check.py --docs 50 --avg-terms 100 --vocab 500 --queries 20 --query-terms 2 --threshold-ms 5.0
```

Run the larger benchmark used for comparison:

```bash
PYTHONPATH=./src python3 scripts/benchmark.py --docs 500 --avg-terms 200 --vocab 2000 --queries 100 --query-terms 2
```

## How It Works

### 1. Web Crawler (`crawler.py`)

- **Politeness**: Respects 6-second minimum delay between requests
- **BFS Traversal**: Uses breadth-first search to explore pages
- **URL Validation**: Only crawls pages on the target domain
- **Error Handling**: Gracefully handles network errors
- **Link Extraction**: Finds and follows links within the same domain

### 2. Indexer (`indexer.py`)

- **Text Extraction**: Parses HTML and removes scripts/styles
- **Tokenization**: Splits text into words
- **Position Tracking**: Records word positions within documents
- **Case Normalization**: Converts all words to lowercase
- **Statistics**: Tracks document frequency and collection frequency

**Inverted Index Structure:**
```python
{
    "word": [
        (doc_id, frequency, [positions])
    ]
}
```

### 3. Search Engine (`search.py`)

- **Single-Word Search**: Direct lookup in inverted index
- **Multi-Word Search**: Set intersection (AND logic)
- **Case-Insensitive**: Treats "Good", "good", "GOOD" identically
- **Fuzzy Matching**: Handles typos with edit distance
- **Ranked Retrieval**: TF-IDF and BM25 scoring
- **Query Cache**: Reuses recent ranked results
- **Result Formatting**: Returns URLs with statistics

### 4. Data Persistence

- **Index Storage**: JSON format for easy inspection
- **Save Format**: Preserves all statistics and document mappings
- **Load/Restore**: Reconstruct exact index from saved file

## Example Workflow

```bash
# 1. Start the tool
python src/main.py

# 2. Build the index (takes a few minutes)
> build
[INFO] Starting crawl from https://quotes.toscrape.com
[INFO] Successfully fetched: https://quotes.toscrape.com/
...
Index built successfully!
  - Pages crawled: 100
  - Unique words: 5234
  - Index saved to: data/index.json

# 3. Examine specific words
> print good
=== Index Entry for 'good' ===
Document Frequency: 45
Postings:
  Doc ID: 2
  URL: https://quotes.toscrape.com/page/2
  Frequency: 3
  Positions: [12, 45, 67]
  ...

# 4. Search for pages
> find good friends
=== Search Results for 'good friends' ===
Found 8 page(s):
1. https://quotes.toscrape.com/page/1
2. https://quotes.toscrape.com/page/3
...

# 5. Exit
> exit
```

## Performance Considerations

### Crawling
- Politeness window: 6 seconds per request
- Estimated crawl time: ~10 minutes for full site (~100 pages)
- Network dependent

### Indexing
- Text extraction: BeautifulSoup parsing
- Tokenization: Regex-based word splitting
- Index building: O(n) where n = total words

### Searching
- Single word: O(1) lookup
- Multi-word: O(k * m) where k = words, m = avg. documents per word
- Ranked search: O(k * m) with extra scoring cost; BM25 adds length normalization
- Results: Typically instant for queries on small/medium corpora

### Memory
- Index size: ~10-50 MB (depending on corpus size)
- JSON serialization: Readable human-friendly format

## Data Structures

### Inverted Index
- **Primary structure**: Dictionary of word → postings
- **Posting list**: List of (doc_id, frequency, positions)
- **Statistics**: Document frequency and collection frequency

### Document Mapping
- URL storage: Maps document IDs to original URLs
- Reconstruction: Used to display results

## Error Handling

The tool gracefully handles:
- Network timeouts and connection errors
- Malformed HTML
- Missing or unreachable pages
- Empty queries
- Non-existent words
- Invalid commands

All errors are logged with context for debugging.

## Code Quality

- **PEP 8 Compliance**: Follows Python style guidelines
- **Documentation**: Docstrings for core functions and scripts
- **Type Hints**: Present in the core pipeline and benchmark/perf scripts
- **Testing**: Unit, integration, and performance regression checks
- **Logging**: DEBUG/INFO/WARNING/ERROR levels

## Development Notes

### Key Implementation Decisions

1. **Lowercase normalization**: Simplifies case-insensitive search
2. **Position tracking**: Enables advanced ranking algorithms
3. **JSON serialization**: Human-readable, portable format
4. **BFS crawling**: Ensures breadth-first exploration
5. **Set intersection**: Efficient multi-word AND queries
6. **BM25 ranking**: Better long-document normalization than raw TF-IDF
7. **CI perf gate**: Catch regressions on a small synthetic corpus

### Future Enhancements

- Phrase queries ("exact match")
- OR queries
- Query suggestions/autocomplete
- Performance optimization (indexing speed)
- Distributed crawling
- Caching layer
- Coverage reporting upload (e.g. Codecov)

## Dependencies

- **requests**: HTTP client for web requests
- **beautifulsoup4**: HTML parsing and text extraction

See `requirements.txt` for specific versions.

## Troubleshooting

### Issue: "Index file not found"
**Solution**: Run `build` command first to create the index

### Issue: Crawling is very slow
**Solution**: This is normal - the 6-second politeness window is intentional
- Estimated time: ~10 minutes for full crawl
- You can interrupt with Ctrl+C and load the partial index

### Issue: Import errors
**Solution**: Ensure PYTHONPATH includes src directory
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Issue: Tests failing
**Solution**: Install test dependencies and run from project root
```bash
PYTHONPATH=./src python3 -m unittest discover -v
```

## Notes on GenAI Usage

This project was developed with guidance from AI tools for:
- Code structure and design patterns
- Error handling best practices
- Documentation generation
- Test case coverage

### Supporting Documents

- `docs/grading_mapping.md` — grading criteria to implementation mapping
- `docs/architecture.md` — system architecture and complexity overview
- `docs/benchmark.md` — benchmark results and analysis
- `docs/genai_evaluation.md` — critical GenAI evaluation
- `docs/git_workflow.md` — suggested branch/commit/tag workflow

See `docs/grading_mapping.md` for the rubric-to-implementation mapping and next steps.

The implementation demonstrates understanding of:
- Web crawling algorithms
- Inverted index data structures
- Search query processing
- Python best practices

All code has been reviewed and understood by the developer.

## License

This project is part of coursework for XJCO3011: Web Services and Web Data.

## Author

Created for University of Leeds, School of Computer Science
Assignment: Coursework 2 - Search Engine Tool
Module: XJCO3011 - Web Services and Web Data

## Version History

- **v1.0.0** (2026-05-09): Initial release
  - Core crawler, indexer, and search functionality
  - Command-line interface
  - Comprehensive test suite
  - Full documentation

---

**Last Updated**: 2026-05-10
**Status**: Ready for submission
