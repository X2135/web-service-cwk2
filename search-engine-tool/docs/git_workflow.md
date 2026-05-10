# Git 工作流指南

## 1. 分支策略

建议采用简化的功能分支流程：

- `main`：稳定、可提交版本
- `feat/<topic>`：新功能或较大改动
- `fix/<topic>`：缺陷修复
- `docs/<topic>`：文档改动
- `chore/<topic>`：构建、CI、依赖或杂项改动

示例：

```bash
git checkout -b feat/bm25-ranking
git checkout -b fix/perf-check-threshold
git checkout -b docs/architecture
```

## 2. 语义提交（Conventional Commits）

推荐使用以下格式：

```text
type(scope): short summary
```

常见类型：
- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档
- `test`: 测试
- `refactor`: 重构
- `chore`: 构建/依赖/杂项

示例：

```text
feat(search): add BM25 scoring and cache key support
test(search): add BM25 vs TF-IDF ranking regression test
docs(readme): update architecture and benchmark instructions
chore(ci): add perf regression check to GitHub Actions
```

## 3. Tag 规范

建议在可提交阶段打语义化 tag：

- `v1.0.0`：首次稳定提交
- `v1.1.0`：新增检索质量或工程增强
- `v1.1.1`：小修复或文档更新

示例：

```bash
git tag -a v1.1.0 -m "Add BM25, CI, and benchmark reporting"
git push origin v1.1.0
```

## 4. 建议流程

1. 从 `main` 拉出功能分支。
2. 完成一个可运行的小增量。
3. 运行测试与基准检查。
4. 使用语义提交记录变更。
5. 合并前更新文档与 tag。

## 5. 这份项目中推荐的提交拆分

- `feat(crawler): improve session retries and politeness logging`
- `feat(search): add TF-IDF and BM25 ranking`
- `test(search): add ranking and cache regression tests`
- `docs: add benchmark, architecture, and grading mapping`
- `chore(ci): add GitHub Actions and perf regression check`
