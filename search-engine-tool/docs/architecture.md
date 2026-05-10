# 架构设计说明

## 1. 总体结构

本项目采用“爬虫 → 索引 → 检索 → CLI/报告”的分层设计：

1. `crawler.py` 负责抓取 HTML 页面，并遵守域名过滤、礼貌抓取窗口与重试机制。
2. `indexer.py` 负责抽取文本、分词、位置记录和倒排索引构建，并计算文档长度、平均文档长度与词项统计。
3. `search.py` 负责查询解析、布尔查找、TF‑IDF/BM25 排序、查询缓存与模糊匹配。
4. `main.py` 提供交互式 CLI，支持 build/load/print/find，以及缓存和排序开关。

## 2. 数据流

```mermaid
flowchart LR
    A[网页 HTML] --> B[爬虫]
    B --> C[页面集合]
    C --> D[Indexer]
    D --> E[InvertedIndex]
    E --> F[SearchEngine]
    F --> G[CLI / 报告]
```

## 3. 核心数据结构

### InvertedIndex
- `index`: 词项 → posting list
- `documents`: doc_id → URL
- `word_stats`: DF / CF / IDF
- `doc_lengths`: doc_id → 文档长度
- `avg_doc_len`: 全局平均文档长度（BM25 使用）

### SearchEngine
- `scoring`: 当前排序方法（`tfidf` 或 `bm25`）
- `_cache`: 查询结果缓存，减少重复计算

## 4. 排序策略

### TF‑IDF
适合展示词项稀有度，但会偏向词频高的长文档。

### BM25
加入长度归一化，能缓解长文档“天然占优”的问题，更适合一般信息检索场景。

## 5. 复杂度概览

- 索引构建：$O(N \times L)$，其中 $N$ 为文档数，$L$ 为单文档平均词数。
- 单词查询：近似 $O(m)$，$m$ 为该词 posting list 长度。
- 多词查询：近似 $O(k \times m)$，$k$ 为查询词数。
- BM25 与 TF‑IDF 相比增加常数级长度归一化成本，但查询规模较小时影响很小。

## 6. 工程实践

- 单元/集成测试：验证关键功能和边界条件。
- 性能回归检查：`scripts/perf_check.py` 用于 CI 小规模阈值检测。
- 基准脚本：`scripts/benchmark.py` 记录 TF‑IDF 与 BM25 的对比结果。

## 7. 可扩展方向

- Phrase query（精确短语检索）
- OR 查询与布尔表达式
- 更完善的相关性评测（MAP / NDCG）
- 覆盖率上传与更严格的静态分析
