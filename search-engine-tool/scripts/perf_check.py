#!/usr/bin/env python3
"""
Small performance regression check for CI.

Runs a compact benchmark and fails (non-zero exit) if average query
latency exceeds a specified threshold (in milliseconds).
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from argparse import Namespace
from typing import Dict

from indexer import Indexer
from search import SearchEngine


def generate_documents(num_docs: int, avg_terms: int, vocab_size: int) -> Dict[str, str]:
    """Generate a small synthetic corpus for performance checks.

    Args:
        num_docs: Number of documents to generate.
        avg_terms: Average number of terms per document.
        vocab_size: Vocabulary size.

    Returns:
        Mapping of URLs to HTML snippets.
    """
    random.seed(1)
    letters = 'abcdefghijklmnopqrstuvwxyz'
    vocab = [''.join(random.choice(letters) for _ in range(6)) for _ in range(vocab_size)]

    pages: Dict[str, str] = {}
    for i in range(num_docs):
        doc_len = max(1, int(random.gauss(avg_terms, avg_terms * 0.1)))
        terms = [random.choice(vocab) for _ in range(doc_len)]
        text = " ".join(terms)
        html = f"<html><body><p>{text}</p></body></html>"
        pages[f"http://ci.local/doc/{i}"] = html
    return pages


def run_check(args: Namespace) -> None:
    """Run the regression check and terminate with an exit code."""
    pages = generate_documents(args.docs, args.avg_terms, args.vocab)
    indexer = Indexer(remove_stopwords=False)
    inv_index = indexer.index_pages(pages)

    engine = SearchEngine(inv_index)
    engine.scoring = args.scoring

    # prepare queries
    vocab = list(inv_index.index.keys())
    if not vocab:
        print("No vocabulary in generated index; failing.")
        sys.exit(2)

    queries: list[str] = []
    random.seed(2)
    for _ in range(args.queries):
        q = " ".join(random.choice(vocab) for _ in range(args.query_terms))
        queries.append(q)

    times: list[float] = []
    for q in queries:
        t0 = time.perf_counter()
        _ = engine.find_ranked(q, top_n=args.top)
        times.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = statistics.mean(times) if times else float('inf')
    p50 = statistics.median(times) if times else float('inf')

    print(f"Perf check: scoring={args.scoring} docs={args.docs} queries={args.queries} avg_ms={avg_ms:.3f} p50={p50:.3f}")

    if avg_ms > args.threshold_ms:
        print(f"FAIL: average query time {avg_ms:.3f} ms exceeds threshold {args.threshold_ms} ms")
        sys.exit(1)
    else:
        print("OK: performance within threshold")
        sys.exit(0)


def main() -> None:
    """CLI entry point for the performance regression check."""
    parser = argparse.ArgumentParser(description='CI performance regression check')
    parser.add_argument('--docs', type=int, default=50)
    parser.add_argument('--avg-terms', type=int, dest='avg_terms', default=100)
    parser.add_argument('--vocab', type=int, default=500)
    parser.add_argument('--queries', type=int, default=20)
    parser.add_argument('--query-terms', type=int, dest='query_terms', default=2)
    parser.add_argument('--top', type=int, default=10)
    parser.add_argument('--scoring', type=str, default='bm25')
    parser.add_argument('--threshold-ms', dest='threshold_ms', type=float, default=5.0,
                        help='Average query time threshold in milliseconds')
    args = parser.parse_args()
    run_check(args)


if __name__ == '__main__':
    main()
