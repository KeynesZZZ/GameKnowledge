# 文档 lint（健康检查）

> 对 UnityKnowledge + AIKnowledge 跑统一 lint。

## 什么时候使用
- 定期维护、ingest/query 之后
- 想找孤儿页、断链、综述缺 sources、声明无据

## 工作流程
1. 运行 `python3 scripts/lint.py`（或 `--kb UnityKnowledge` 限定单库）
2. ERROR（断链 / 综述缺 sources）：必须修
3. WARN（孤儿页 / 声明无据 / stale）：报告给用户，问是否补入链 / 补 sources
4. 推翻既有结论的修正 → 写进 review，不直接改 `author: human` 页

## 用户指令
```
/lint
/lint --kb AIKnowledge
```
