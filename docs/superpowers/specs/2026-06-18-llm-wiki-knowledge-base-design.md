---
title: 【设计】LLM-Wiki 个人知识库改造方案
tags: [AI, 工作流, 知识库, 设计]
created: 2026-06-18
description: 按 Karpathy LLM-Wiki 模式把现有 276 篇知识库改造成"LLM 维护 + 混合所有权 + 全套护栏"的可复利系统
status: draft
---

# 【设计】LLM-Wiki 个人知识库改造方案

> 来源：Karpathy 的 [llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 及其评论区高质量讨论。
> 决策记录：本稿经 brainstorming 多轮确认——所有权 = **混合**；目标痛点 = **全部 4 项**；规模 = **方案 C（全套带护栏）**，但按价值分阶段落地。

## 1. 背景与问题

### 1.1 当前仓库状态（已核实）

- 两个知识库：`UnityKnowledge/`（16 个子域）、`AIKnowledge/`（7 个子域），共 **276 个 .md**。
- 已具备的"地基"：git + Markdown + Obsidian + `[[wikilinks]]` + YAML frontmatter + 标签体系；有 schema 层 [CLAUDE.md](../../../CLAUDE.md)；有真在跑的 pre-commit [.claude/hooks/pre-commit.py](../../../.claude/hooks/pre-commit.py)；有链接校验 [UnityKnowledge/scripts/check_links.py](../../../UnityKnowledge/scripts/check_links.py)。
- **关键事实（用户确认）**：现有文档**主要由 AI 撰写**；后续会持续积累**外部文章**。
- **三个硬缺口**：
  1. 全库 **没有 `index.md` / `log.md`**（Karpathy 强调的两个特殊文件）——276 篇无目录，导航与 agent 定位都靠静态 README。
  2. [README.md](../../../README.md) 的"每周维护清单"全是**人工**账本活（补 frontmatter/标签/链接、查过期结论）——正是 Karpathy 诊断"人类因此放弃 wiki"的负担。
  3. [CLAUDE.md](../../../CLAUDE.md) **已与现状脱节**：大篇幅描述 `tools/knowledge_base/`、`unity-rules-checker/`、`tools/check_docs_compliance.py`，但这些在近期提交（`删除多余的`、`全库文档规则迁移（211文档）`）中已被删除，全库已搜不到对应文件。

### 1.2 要解决的四个痛点（用户确认为"全部"）

| 痛点 | 主要由哪个机制解决 |
|------|------|
| 找不到 / 不知道有什么 | `index.md` + `log.md` + 紧凑 schema |
| 维护负担太重 | `lint` 自动化（扩展现有 check_links.py） |
| 知识不复利 | 综述页 + query 好答案回填 |
| AI 进来抓不住全貌 | 紧凑 schema + 域 index 让 agent 一进来就能下钻 |

四者由**一组连贯机制**同时覆盖，不是四个独立项目。

## 2. 参考模式与偷来的关键洞察

Karpathy 核心：别把 LLM 当搜索引擎，让它像程序员维护代码库一样**持续编译并维护一个会滚雪球的 Markdown wiki**。三个层次（raw sources / wiki / schema）、三个操作（ingest / query / lint）、两个特殊文件（index.md / log.md）。

评论区值得落地的洞察：

- **Provenance / 引用即契约**（@vvvvvivekkk、@yazanabuashour、@Clod）：每条结论可追溯到源；markdown 是唯一真相源，索引/检索产物全部一次性可重建。
- **幻觉累积**（@Archimondstat，"苏格拉底-柏拉图-贝叶斯"）：笔记越多，库中至少含一条幻觉的概率 → 1。wiki 应存"用户验证过的"，不是"AI 替你想好的"。对本库（AI 写为主）尤其致命。
- **类型化边**（@pursultani）：`relates_to` 带受控词表（extends/supersedes/contradicts/supports/refines）。客观认识论领域（技术）把矛盾当缺陷处理。
- **置信度分级 + review 队列**（@watsonrm、@LARIkoz）：高置信自动应用，推翻既有结论的进 review 队列，绝不静默改；矛盾按"声明身份"（sources 引用）判，不按文本邻近。
- **Token 效率**（@Motya-cobol）：成本主要来自反复加载上下文；确定性活交脚本，LLM 只做综合/判断；schema 保持紧凑。

## 3. 设计决策（已确认）

- **所有权：混合**——外部文章与少量人写笔记当真相源，LLM 维护 index、生成综述/概念页、补链接、查矛盾。
- **规模：方案 C（全套带护栏）**，但**按价值分阶段**，P1 即完整可用，P2/P3 按真实痛点增量。
- **存量认知**：现有 276 篇大多 AI 写、大多无 sources → 默认 `author: llm` + `status: draft`，作为"待回溯债务"暴露。

## 4. 架构

### 4.1 三层模型（按"AI 写为主 + 外部源"重建）

| 层 | 是什么 | 谁能改 |
|----|--------|--------|
| **原始层 (raw)** | 外部文章/论文/剪藏——**唯一不可变的真相源** | 不可变。捕获进 `01_Inbox/`，确认后提升到 `_sources/` |
| **笔记层 (wiki)** | 现有 276 篇 + 未来综述/概念页，**主要由 AI 写** | LLM 维护；每条结论要么 `sources:` 指回 raw，要么显式 `status: draft` |
| **schema 层** | CLAUDE.md（修订） | 人 + LLM 共同演进 |

目录约定（最终命名可在实现时微调）：
- `01_Inbox/`：捕获区（外部剪藏 + 零散想法），两个 KB 都已存在。
- `_sources/`：提升后的不可变外部原文，每域一个。
- 其余按现有编号域结构不变。

### 4.2 Frontmatter 约定

`sources` 是**负载字段**（决定结论可否追溯），`author` 是次要信号：

```yaml
---
title: 【综述】xxx
tags: [AI, 综述]
created: 2026-06-18
author: human | llm        # 现状多数 llm；人写（复盘/决策/捕获）是少数高信任锚点
sources: [外部文章A, 笔记B]  # 综合页必填；空 = 无据可查（lint 标黄）
status: draft | verified | stale   # draft=刚写未验 / verified=有源或人工背书 / stale=过期
relates_to:                # 可选，类型化边
  - page: "【笔记】对象池"
    rel: extends
---
```

**状态机**：`draft` →（外部源背书 或 人工确认 或 苏格拉底挑战通过）→ `verified` →（新源推翻）→ `stale`。

**幻觉防御（三层闸门）**：
1. **Provenance 强制**：综述/综合页 `sources:` 必填、指回 raw 或已 `verified` 笔记；无源 → lint 标黄（P2 升 block）。
2. **苏格拉底闸门**：纯推断（非外部源、未经人确认）默认 `status: draft`，挑战通过才升 `verified`。
3. **存量迁移**：现有 276 篇一次性回填 `author: llm` + `status: draft`，lint 暴露为"待回溯债务"，随外部文章积累逐步补 sources 升级。

### 4.3 index.md / log.md（两个特殊文件）

- **按域 index，不做单一根 index**：[UnityKnowledge/index.md](../../../UnityKnowledge/index.md) + [AIKnowledge/index.md](../../../AIKnowledge/index.md)。每行 `| 链接 | 一句话摘要 | author | status | 更新日 |`，按子目录分组，机器可读、LLM 先读它下钻。
  - 与 README 分工：**README = 给人看的叙事入口（不动）；index.md = 给 LLM/检索用的目录（LLM 维护）**。职责分开，不双写漂移。
- **log.md**：每域一个，append-only，固定前缀 `## [2026-06-18] ingest|query|lint | 标题`，`grep "^## \[" log.md | tail` 即时间线。
- 根目录 `_index.md`（<10 行）只做两个域 index 的指针，不重复内容。

### 4.4 操作契约：ingest / query / lint

- **ingest**：读源 → 讨论 → 写综述/更新页 → 每个被碰的真相层页加 `updated` → 更新域 index → 追加 log。一次平均碰 5–10 页。综述页强制 `sources:` + `author: llm`。
- **query**：读域 index 定位 → 读相关页 → **带引用作答** → **好答案回填为新页**（复利引擎，同样标 `author: llm` + `sources:`）。
- **lint**：把 [check_links.py](../../../UnityKnowledge/scripts/check_links.py) 扩成统一入口，查 7 项：
  1. 断链（broken wikilinks）
  2. 孤儿页（无入链）
  3. 缺 frontmatter（必填字段）
  4. `status: stale` 标记
  5. 综合页缺 `sources`
  6. 真相层与综合层矛盾（按 sources 声明身份判，不按文本邻近）
  7. 声明无据（非 draft 但 `sources` 为空）
  - 高置信修正（修断链、补 frontmatter、更新 index）自动应用；**推翻既有结论 / 解决矛盾 / 改写 `verified` → 进 `_review.md` 队列**，绝不静默改。

### 4.5 护栏（C 专属，叠在核心之上）

**4.5a 类型化边**：`relates_to` 受控词表 = `extends | supersedes | contradicts | supports | refines`（5 个动词）。lint 校验 `rel` 在枚举内（防词表漂移）。技术领域把 `contradicts` 当缺陷 → 推进 review，不当内容保留。Dataview 出图。Unity 版本（2021→2022→6）的 API 弃用/替换是 `supersedes` 的典型场景。

**4.5b review 队列**：`_review.md`，列 pending 改动的 diff + 理由，人工清空。

**4.5c 触发模型（手动为主，自动化只报告不决定）**：
- 手动 skill（主力）：`/ingest`、`/query`、`/lint`，Claude Code 会话内触发。
- pre-commit（最廉价的确定性检查）：仅断链 / 缺 frontmatter / `relates_to` 非法枚举，挂到 [pre-commit.py](../../../.claude/hooks/pre-commit.py)，秒级。
- 可选 cron lint：定时跑，**只往 `_review.md` 报告，不自动改**。
- 确定性活（index 重建、intake 解析、routing）交脚本；LLM 只做综合/判断。

**4.5d 检索层（不重建被删的 ChromaDB）**：
- 276 篇量级，`index.md` + ripgrep 足够；markdown 是唯一真相源，索引/检索产物全部可重建。
- **明确不把删掉的向量 RAG 当主力**（那是 Karpathy 批的"每次重新发现知识"）。真要搜索引擎，后期上 `qmd` 式本地 BM25+重排作为 markdown 之上的派生层。
- agent query 流程：读域 index → ripgrep 关键词 → 读 2–5 页 → 带引用作答；不全量读 CLAUDE.md。

### 4.6 CLAUDE.md 修订（具体改动）

- **删**：`tools/knowledge_base/`、`tools/check_docs_compliance.py`、`unity-rules-checker/` 及 Quick Reference 表对应条目（已核实全不存在）。
- **加**：三层模型 + 目录约定（`_sources/` / `01_Inbox/`）；`## Ingest/Query/Lint` 三段操作契约；页面约定（`【综述】` 类型 + `author/sources/status/relates_to` 语义 + 状态机）。
- **瘦身**：现状 ~12KB 每会话全量进上下文 = 烧 token。把细节（完整 lint 规则表、Dataview 查询示例）挪到 `docs/` 参考文件按需读，CLAUDE.md 本身压成 ~6–8KB 的路由文件。

## 5. 存量迁移

一次性脚本，对每个现有 .md：
- 无 `author` → 设 `author: llm`（多数情况）；人写明显的（`【复盘】`、决策类）手动改 `author: human`。
- 无 `status` → 设 `status: draft`。
- 无 `sources` → 留空（lint 标黄为待回溯债务）。
- **不覆盖**已有 frontmatter 值。

迁移后，lint 第 7 项（声明无据）会产出"待回溯清单"，作为后续 ingest 外部文章时逐步补 sources 的输入。

## 6. 分阶段落地

| 阶段 | 内容 | 痛点覆盖 | 触发 |
|------|------|---------|------|
| **P1 地基**（B 核心，最高价值） | §4.1 层模型 + §5 存量迁移 + §4.3 按域 index/log + §4.4 lint 核心 7 项 + `【综述】`+query 回填 + §4.6 清 CLAUDE.md | **全部 4 痛点** | 手动 |
| **P2 护栏** | §4.5a 类型化边 + §4.5b review 队列 + provenance 强制（综述页 `sources` 从 warn 升 block） | 防幻觉、防静默改 | 手动 |
| **P3 自动化**（最 YAGNI，按需） | pre-commit 廉价 lint + 可选 cron report-only | 维护负担自动化 | hook/cron |

**眼睛睁开的对冲**：P3 的 cron、甚至 P2 的类型化本体是一人维护 KB 最易"建了不用"的件。**P1 跑完即有完整可用系统**，P2/P3 按真实痛点增量加，不强制做完。

## 7. 明确的非目标（Non-goals）

- 不重建向量 RAG 作为主力检索层。
- 不做人文学科式的"保留矛盾作为内容"（本库是客观认识论，矛盾当缺陷）。
- 不做团队级多 writer 并发协调（单 writer，per-file，append-only 已足够）。
- 不做 NotebookLM 式一次性总结堆（wiki 是持续编译、保持当前的产物）。
- 不强制把 P2/P3 一次性做完。

## 8. 待确认 / 后续再定

- `_sources/` 目录命名（实现时可换）。
- cron 是否最终启用（P3 按需）。
- `relates_to` 词表是否够用（P2 跑过后按真实关系再扩）。

## 9. 参考

- Karpathy llm-wiki Gist：<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- 知乎解读：<https://zhuanlan.zhihu.com/p/2024849279961821906>
- 关键评论洞察：@pursultani（类型化边）、@Archimondstat（幻觉累积）、@watsonrm（置信度/幂等写）、@Motya-cobol（token 效率）、@vvvvvivekkk（provenance/可重建）、@yazanabuashour（写权限边界）、@LARIkoz（drift 检测）。
