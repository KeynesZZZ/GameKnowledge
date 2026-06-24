# ingest（喂入新源）

> 把一个新源（外部文章 / 新笔记）整合进 wiki。

## 工作流程
1. 读源（`_sources/` 外部原文，或 `01_Inbox/` 捕获），与用户讨论要点
2. 写或更新综述/概念页：`author: llm`，`sources:` 指向真相层笔记/原文
3. 被碰到的真相层页（`author: human`）加 `updated`，不改正文结论
4. 运行 `python3 scripts/generate_llm_index.py` 更新 index
5. 追加 `log.md`：`## [YYYY-MM-DD] ingest | 标题`
6. 跑 `/lint` 确认无新断链

## 用户指令
```
/ingest _sources/某文章.md
/ingest "把这篇整理进 20_核心系统"
```
