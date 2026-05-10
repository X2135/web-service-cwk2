#!/usr/bin/env python3
"""
Evaluate ranked retrieval using MAP and NDCG.

This script loads a saved index (`data/index.json`) and evaluates TF-IDF vs BM25
using a set of queries. Relevance judgments are defined as documents that
contain ALL query terms (exact match) — a practical ground truth for these
queries in the coursework context.

Outputs results to `results/relevance_results.json` and `docs/relevance_results.md`.
"""
from __future__ import annotations

import json
import argparse
from typing import List, Dict, Tuple
from indexer import InvertedIndex
from search import SearchEngine
from pathlib import Path
import math


def load_index(path: str = "data/index.json") -> InvertedIndex:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["documents"] = {int(k): v for k, v in data["documents"].items()}
    return InvertedIndex.from_dict(data)


def precision_at_k(ranked: List[int], relevant_set: set, k: int) -> float:
    if k <= 0:
        return 0.0
    ranked_k = ranked[:k]
    if not ranked_k:
        return 0.0
    rel_count = sum(1 for d in ranked_k if d in relevant_set)
    return rel_count / k


def average_precision(ranked: List[int], relevant_set: set) -> float:
    if not relevant_set:
        return 0.0
    score = 0.0
    num_rel = 0
    for i, doc_id in enumerate(ranked, start=1):
        if doc_id in relevant_set:
            num_rel += 1
            score += num_rel / i
    return score / len(relevant_set) if len(relevant_set) > 0 else 0.0


def dcg_at_k(relevances: List[int], k: int) -> float:
    relevances = relevances[:k]
    dcg = 0.0
    for i, rel in enumerate(relevances, start=1):
        denom = math.log2(i + 1)
        dcg += (2 ** rel - 1) / denom
    return dcg


def ndcg_at_k(ranked: List[int], relevant_set: set, k: int) -> float:
    # binary relevance (1 if in relevant_set else 0)
    relevances = [1 if d in relevant_set else 0 for d in ranked]
    dcg = dcg_at_k(relevances, k)
    ideal = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate(engine: SearchEngine, queries: List[str], top_n: int = 100) -> Dict[str, float]:
    map_score = 0.0
    ndcg_score = 0.0
    for q in queries:
        words = [w for w in q.strip().lower().split() if w]
        # ground truth: documents that contain all words
        doc_sets = [set(engine.inv_index.get_documents_for_word(w)) for w in words if engine.inv_index.contains_word(w)]
        relevant_set = set.intersection(*doc_sets) if doc_sets else set()

        # get ranked doc ids
        ranked_urls = engine.find_ranked(q, top_n=top_n)
        # convert urls back to doc_ids
        ranked_doc_ids = []
        url_to_doc = {v: k for k, v in engine.inv_index.documents.items()}
        for url in ranked_urls:
            if url in url_to_doc:
                ranked_doc_ids.append(url_to_doc[url])

        ap = average_precision(ranked_doc_ids, relevant_set)
        ndcg = ndcg_at_k(ranked_doc_ids, relevant_set, k=10)
        map_score += ap
        ndcg_score += ndcg

    n = len(queries)
    return {"MAP": map_score / n if n else 0.0, "NDCG@10": ndcg_score / n if n else 0.0}


DEFAULT_QUERIES = [
    "life",
    "love",
    "friendship",
    "truth",
    "inspirational",
    "reading",
    "happiness",
    "success",
    "courage",
    "knowledge",
    "dreams",
    "writing",
    "books",
    "humor",
    "faith",
    "hope",
    "music",
    "poetry",
    "wisdom",
    "education",
]


def main():
    parser = argparse.ArgumentParser(description="Evaluate TF-IDF vs BM25 using MAP/NDCG with simple exact-match relevance")
    parser.add_argument("--index", type=str, default="data/index.json")
    parser.add_argument("--output", type=str, default="results/relevance_results.json")
    parser.add_argument("--top", type=int, default=100)
    args = parser.parse_args()

    inv_index = load_index(args.index)

    # evaluate TF-IDF
    engine_tfidf = SearchEngine(inv_index)
    engine_tfidf.scoring = "tfidf"
    res_tfidf = evaluate(engine_tfidf, DEFAULT_QUERIES, top_n=args.top)

    # evaluate BM25
    engine_bm25 = SearchEngine(inv_index)
    engine_bm25.scoring = "bm25"
    res_bm25 = evaluate(engine_bm25, DEFAULT_QUERIES, top_n=args.top)

    out = {"queries": DEFAULT_QUERIES, "tfidf": res_tfidf, "bm25": res_bm25}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # also write a markdown summary
    md_path = Path("docs/relevance_results.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Relevance Evaluation Results\n\n")
        f.write(f"**Queries**: {len(DEFAULT_QUERIES)}\n\n")
        f.write("## TF-IDF\n\n")
        f.write(f"- MAP: {res_tfidf['MAP']:.4f}\n")
        f.write(f"- NDCG@10: {res_tfidf['NDCG@10']:.4f}\n\n")
        f.write("## BM25\n\n")
        f.write(f"- MAP: {res_bm25['MAP']:.4f}\n")
        f.write(f"- NDCG@10: {res_bm25['NDCG@10']:.4f}\n\n")

    print(f"Saved evaluation: {args.output} and {md_path}")


if __name__ == "__main__":
    main()
