#!/usr/bin/env python3
"""
Simple benchmark harness for indexing and query performance.

Generates synthetic documents, builds an index with `Indexer`, and
measures average query time for `SearchEngine` using TF-IDF and BM25.
"""
from __future__ import annotations

import time
import random
import argparse
import statistics
import csv
import json
from pathlib import Path
from argparse import Namespace
from typing import Dict

from indexer import Indexer
from search import SearchEngine


def generate_documents(num_docs: int, avg_terms: int, vocab_size: int) -> Dict[str, str]:
    """Generate synthetic HTML pages for benchmarking.

    The vocabulary is alphabetic-only so it survives the indexer's token
    extraction regex. Each generated page contains a single paragraph.

    Args:
        num_docs: Number of documents to generate.
        avg_terms: Average number of terms per document.
        vocab_size: Size of the synthetic vocabulary.

    Returns:
        Mapping of URL to HTML content.
    """
    random.seed(42)
    # create alphabetic-only vocabulary (avoid digits so Indexer regex matches)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    vocab = [''.join(random.choice(letters) for _ in range(6)) for _ in range(vocab_size)]

    pages: Dict[str, str] = {}
    for i in range(num_docs):
        doc_len = max(1, int(random.gauss(avg_terms, avg_terms * 0.1)))
        terms = [random.choice(vocab) for _ in range(doc_len)]
        text = " ".join(terms)
        # simple HTML wrapper (indexer extracts text via BeautifulSoup)
        html = f"<html><body><p>{text}</p></body></html>"
        pages[f"http://example.local/doc/{i}"] = html
    return pages


def benchmark(args: Namespace) -> None:
    """Run the benchmark and print summary statistics.

    Args:
        args: Parsed CLI arguments.
    """
    print(f"Generating {args.docs} documents (avg {args.avg_terms} terms)...")
    pages = generate_documents(args.docs, args.avg_terms, args.vocab)

    indexer = Indexer(remove_stopwords=False)
    t0 = time.perf_counter()
    inv_index = indexer.index_pages(pages)
    t_index = time.perf_counter() - t0

    print(f"Indexing complete: {args.docs} docs, unique words: {len(inv_index.index)}")
    print(f"Indexing time: {t_index:.3f}s")

    engine = SearchEngine(inv_index)

    # generate queries
    random.seed(123)
    vocab = list(inv_index.index.keys())
    queries: list[str] = []
    for _ in range(args.queries):
        if args.query_terms == 1:
            q = random.choice(vocab)
        else:
            q = " ".join(random.choice(vocab) for _ in range(args.query_terms))
        queries.append(q)

    def run_queries(scoring: str) -> list[float]:
        """Execute the prepared query set using a specific scoring method."""
        engine.scoring = scoring
        engine.clear_cache()
        times: list[float] = []
        for q in queries:
            t0 = time.perf_counter()
            _ = engine.find_ranked(q, top_n=args.top)
            times.append(time.perf_counter() - t0)
        return times

    for scoring in ("tfidf", "bm25"):
        times = run_queries(scoring)
        avg_ms = statistics.mean(times) * 1000
        p50_ms = statistics.median(times) * 1000
        print(f"Scoring: {scoring} — queries: {len(times)}; avg: {avg_ms:.3f} ms; p50: {p50_ms:.3f} ms")

        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            summary = {
                "docs": args.docs,
                "avg_terms": args.avg_terms,
                "vocab": args.vocab,
                "queries": args.queries,
                "query_terms": args.query_terms,
                "top_n": args.top,
                "scoring": scoring,
                "index_time_s": round(t_index, 6),
                "query_time_ms_avg": round(avg_ms, 6),
                "query_time_ms_p50": round(p50_ms, 6),
            }

            json_path = output_dir / f"benchmark_{scoring}.json"
            csv_path = output_dir / f"benchmark_{scoring}.csv"

            with json_path.open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
                writer.writeheader()
                writer.writerow(summary)

            print(f"Saved results: {json_path} and {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark indexing and query latency")
    parser.add_argument("--docs", type=int, default=500, help="Number of synthetic documents to generate")
    parser.add_argument("--avg-terms", dest="avg_terms", type=int, default=200, help="Average number of terms per document")
    parser.add_argument("--vocab", type=int, default=2000, help="Vocabulary size")
    parser.add_argument("--queries", type=int, default=100, help="Number of queries to run")
    parser.add_argument("--query-terms", dest="query_terms", type=int, default=2, help="Terms per query")
    parser.add_argument("--top", type=int, default=10, help="Top-N results to request")
    parser.add_argument("--output-dir", type=str, default="results", help="Directory to write benchmark JSON/CSV summaries (set to empty to disable)")
    args = parser.parse_args()

    benchmark(args)
