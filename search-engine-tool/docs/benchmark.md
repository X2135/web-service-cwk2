**基准与复杂度分析**

概述
- 环境：本地 macOS（参见项目 README 以获取环境细节）
- 脚本：`scripts/benchmark.py`（生成合成文档、构建索引并测量查询延迟）

运行方式（示例）：
```
PYTHONPATH=./src python3 scripts/benchmark.py --docs 500 --avg-terms 200 --vocab 2000 --queries 100 --query-terms 2
```

若要自动保存结果，可加上输出目录参数：
```
PYTHONPATH=./src python3 scripts/benchmark.py --output-dir results
```

实测结果（一次运行）
- 文档数：500；平均词数：200；词表大小：2000
- 索引时间：0.107 s
- 查询（100 次，每次 2 词）延迟：
  - TF‑IDF 平均：0.021 ms（p50 0.020 ms）
  - BM25 平均：0.028 ms（p50 0.028 ms）

结论与复杂度分析
- 索引：当前实现为单线程，时间复杂度主要为 O(N * L)（N = 文档数，L = 每文档词数）用于分词与倒排表构建；空间复杂度与倒排表大小（词表 + posting 列表总和）成正比。
- 查询：查找 posting 并对候选文档计分，最坏情况需要遍历所有 posting（总词出现数 M），常见查询候选集 << M，因此实际平均查询延迟很低。
- BM25 相较于简单 TF‑IDF 多了文档长度归一化计算，常数开销略高（见上面延迟差异），但在相关性上通常更鲁棒。

后续建议
- 将 `scripts/benchmark.py` 输出保存为 CSV/JSON 以便长期比较（已支持 `results/`）。
- 增加多线程/并发索引与并行查询以评估可扩展性。
- 在 CI 中加入轻量基准（小规模）以捕捉性能回归。
