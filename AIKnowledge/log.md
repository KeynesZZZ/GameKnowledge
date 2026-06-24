# AIKnowledge 维护日志（log.md）

> append-only。每行前缀 `## [YYYY-MM-DD] ingest|query|lint | 标题`，可 `grep "^## \[" log.md | tail`。

## [2026-06-24] lint | P1 地基初始化
- 生成首版 index.md
- 全库回填 author 字段
- 统一 lint 基线跑通
