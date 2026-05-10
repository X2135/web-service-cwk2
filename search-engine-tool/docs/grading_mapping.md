**评分对照表（逐项映射）**

目标：把课程评分标准逐项映射到项目实现、证据与下一步建议，便于证明满足高分要求。

1) 功能完整性（必需）
- 要求：爬虫、索引、查询、持久化/加载、演示/CLI。
- 已实现：`src/crawler.py`, `src/indexer.py`, `src/search.py`, `src/main.py`。
- 证据：单元测试覆盖与 `QUICKSTART.md` 演示命令。
- 建议：在 README 中列出复现步骤与示例输入/输出截图。

2) 检索质量（加分）
- 要求：合理排序（TF‑IDF / BM25）与评价。
- 已实现：TF‑IDF 与可切换的 BM25（`SearchEngine.scoring`）；`scripts/benchmark.py` 提供延迟对比。
- 证据：`docs/benchmark.md`、`scripts/benchmark_results.json`。
- 建议：添加小规模相关性评估（人工标注 10–20 个 query 的 MAP/NDCG 对比）。

3) 鲁棒性与测试（必需/高分）
- 要求：单元 + 集成测试、异常处理、复现性。
- 已实现：59 个单元/集成测试，网络调用已 mock，错误处理存在于各模块。
- 建议：增加性能测试（小规模）并将其纳入 CI；补充边界条件测试（超长文档、二进制输入）。

4) 性能与复杂度分析（高分）
- 要求：基准、时间/空间复杂度分析、可重复结果。
- 已实现：`scripts/benchmark.py` 与 `docs/benchmark.md`（索引与查询延迟示例）。
- 建议：将基准结果输出为 CSV/JSON（已添加），并在 docs 中加入图表与多次实验统计。

5) 代码质量（推荐/加分）
- 要求：类型注解、清晰 API、文档字符串、代码风格。
- 当前：大部分核心模块已有类型注解与 docstrings，但可补充完整性与静态检查（mypy）。
- 建议：运行 `mypy`、`flake8`，并修复提示；补充函数/类 docstrings。

6) 工程实践（推荐）
- 要求：CI、测试覆盖报告、语义提交、分支策略。
- 当前：尚未配置 CI（将添加 GitHub Actions），已实现单元测试。
- 建议：添加 `.github/workflows/ci.yml`（单元测试 + 小规模基准），并生成覆盖率报告上传到 Codecov（或 similar）。

7) 反思/评估（卓越档）
- 要求：批判性讨论局限、未来工作与伦理影响（如使用爬虫的合法性、数据偏差）。
- 建议：撰写 `docs/genai_evaluation.md` 或 `REPORT.md` 包含方法比较、局限与改进计划。

实施优先级（建议）
- 立即：生成评分对照文档（本文件），添加 CI（运行所有单元测试），把基准输出持久化。
- 优先：扩展测试（集成 + 性能回归）；添加类型检查与文档完善。
- 后续：相关性评测、CI 中的性能检查、撰写深度评估报告与提交历史优化。

证据位置快速索引：
- 核心代码：`src/` 目录
- 测试：`tests/` 目录
- 基准：`scripts/benchmark.py`, `scripts/benchmark_results.json`, `docs/benchmark.md`
- CLI 快速说明：`QUICKSTART.md`

下一步：我将添加 GitHub Actions CI 配置来自动运行测试（并生成简要日志）。
