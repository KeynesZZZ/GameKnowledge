# query（提问，好答案回填）

> 基于知识库作答，把有价值的答案回填为新页（复利引擎）。

## 工作流程
1. 先读 `<KB>/index.md` 定位相关页（不要全量读 CLAUDE.md）
2. 读 2–5 篇相关页 + ripgrep 关键词补全
3. 带引用作答（每条结论指向 `sources`）
4. 若答案有复用价值 → 征得用户同意后回填为新页：综述用 `【综述】`，否则合适类型；`author: llm` + `sources:` + `status: 待验证`
5. 更新 index + 追加 `log.md`：`## [YYYY-MM-DD] query | 问题摘要`

## 用户指令
```
/query UGUI 怎么减少 DrawCall？
```
