# 文档规则迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 UnityKnowledge 下 227 个 .md 文档迁移到最新元数据、结构、生命周期和健康检查规则。

**Architecture:** 两阶段执行——先脚本批量确定性修改（frontmatter 标准化），再 Claude 逐目录智能修复（断链、结构、质量）。所有修改在 main 分支进行，不提交，最后统一确认。

**Tech Stack:** Python 3 (迁移/校验/链接检查脚本), Claude Code (智能修复), git (基线记录)

---

## File Structure

### 修改的文件

| 文件 | 修改类型 | 职责 |
|------|----------|------|
| `UnityKnowledge/00_元数据与模板/【模板】Bug记录.md` | 编辑 | 统一 frontmatter，修占位链接 |
| `UnityKnowledge/00_元数据与模板/【模板】代码审查清单.md` | 编辑 | 同上 |
| `UnityKnowledge/00_元数据与模板/【模板】代码片段.md` | 编辑 | 同上 |
| `UnityKnowledge/00_元数据与模板/【模板】性能分析.md` | 编辑 | 同上 |
| `UnityKnowledge/00_元数据与模板/【模板】技术文章.md` | 编辑 | 同上 |
| `UnityKnowledge/00_元数据与模板/【模板】架构决策记录.md` | 编辑 | 同上 + 更新旧状态值为新生命周期 |
| `UnityKnowledge/00_元数据与模板/【模板】系统设计说明书.md` | 编辑 | 统一 frontmatter，修占位链接 |
| `UnityKnowledge/00_元数据与模板/【模板】通用编程笔记.md` | 编辑 | 同上 |
| `.claude/skills/create-doc.md` | 编辑 | 对齐最新规则，更新时间戳 |
| `UnityKnowledge/00_元数据与模板/元数据规范.md` | 编辑 | 补全 category 合法值 |
| `UnityKnowledge/scripts/migrate_docs_to_latest_rules.py` | 可能编辑 | 审查逻辑是否与规则一致，不一致则修 |
| `UnityKnowledge/**/*.md`（227个） | 脚本批量修改 | frontmatter 标准化 |

### 使用的脚本（不修改，只运行）

| 脚本 | 用途 |
|------|------|
| `UnityKnowledge/scripts/migrate_docs_to_latest_rules.py` | 批量迁移 |
| `UnityKnowledge/scripts/validate_metadata.py` | 元数据校验 |
| `UnityKnowledge/scripts/check_links.py` | 链接检查 |

---

## Task 1: 冻结基线

**Files:**
- 无文件修改

- [ ] **Step 1: 检查当前工作区状态**

Run:
```bash
cd /Users/keynes/git/Doc && git status --short
```

Expected: 列出所有未提交变更（已有未提交文件是正常的）。

- [ ] **Step 2: 记录基线 commit hash**

Run:
```bash
git log --oneline -1
```

Expected: 输出当前 HEAD commit，例如 `c7186f0 删除多余的`。记录此 hash 作为回滚点。

- [ ] **Step 3: 确认脚本就绪**

Run:
```bash
ls -la UnityKnowledge/scripts/migrate_docs_to_latest_rules.py UnityKnowledge/scripts/validate_metadata.py UnityKnowledge/scripts/check_links.py
```

Expected: 三个文件都存在。

---

## Task 2: 修复模板文件 frontmatter（8 个模板）

**Files:**
- Modify: `UnityKnowledge/00_元数据与模板/【模板】Bug记录.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】代码审查清单.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】代码片段.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】性能分析.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】技术文章.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】架构决策记录.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】系统设计说明书.md`
- Modify: `UnityKnowledge/00_元数据与模板/【模板】通用编程笔记.md`

**修改规则（适用于所有 8 个模板）：**

1. **frontmatter 字段确认**：已有 9 个必填字段（title, tags, category, created, updated, description, status, validation, related）——不需要改动
2. **`related` 字段**：当前全部为 `related: []`，应填入至少 1 个指向规则文档的链接，例如 `["文档结构规范"]` 或 `["元数据规范"]`
3. **占位链接修复**：模板中的 `[[]]` 空链接（如代码审查清单中的 `需要修改的项` 表格里的 `[[]]`）应改为纯文本占位 `（待填写）`，避免 link checker 报断链
4. **机械「文档定位」修复**：底部的机械模板文字应改为有意义的模板使用说明
5. **相关链接**：底部的 `[[../00_元数据与模板/文档结构规范]]` 保留，但应确保路径正确（模板本身就在 `00_元数据与模板/` 内，相对路径 `../00_元数据与模板/` 可能不正确）

- [ ] **Step 1: 逐个读取 8 个模板，确认每个模板的具体问题**

读取每个模板文件，记录：
- 哪些有 `[[]]` 空链接
- 哪些的 `文档定位` 是机械模板文字
- `相关链接` 的路径是否正确
- `related` 字段应填什么

- [ ] **Step 2: 修复【模板】Bug记录.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 底部 `相关链接` 中 `[[../00_元数据与模板/文档结构规范]]` → 应改为 `[[文档结构规范]]`（同目录下不需要相对路径）
- 底部 `文档定位` 是机械文字 → 改为有意义的模板说明

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑底部「文档定位」段落，将：
```
## 文档定位

本文档用于沉淀 `【模板】Bug记录` 相关知识，说明其适用场景、核心内容和实践注意事项。
```
改为：
```
## 文档定位

Bug 记录模板，用于规范化记录 Bug 的发现、复现、根因分析和解决方案。适用于任何需要追踪和复盘的 Bug 场景。
```

编辑底部「相关链接」段落，将 `[[../00_元数据与模板/文档结构规范]]` 改为 `[[文档结构规范]]`。

- [ ] **Step 3: 修复【模板】代码审查清单.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 第 96 行 `| 1 | | | | 🔴必须修改 / 🟡建议修改 | [[]] |` 中的 `[[]]` → 改为 `（待填写）`
- 第 97 行 `| 2 | | | | | [[]] |` 中的 `[[]]` → 改为 `（待填写）`
- 底部 `文档定位` 是机械文字 → 改为有意义的说明
- 底部 `相关链接` 路径修正

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑占位链接，将 `[[]]` 改为纯文本 `（待填写）`。

编辑底部「文档定位」：
```
## 文档定位

代码审查清单模板，从架构一致性、性能、内存安全、可维护性、平台兼容性五个维度进行系统性检查。适用于团队 Code Review 流程。
```

编辑底部「相关链接」，将 `[[../00_元数据与模板/文档结构规范]]` 改为 `[[文档结构规范]]`。

- [ ] **Step 4: 修复【模板】代码片段.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 底部 `文档定位` 是机械文字 → 改为有意义说明
- 模板内容中的 `相关链接` 部分有空行占位 `- ` → 保留（这是模板示例，不应被检查）

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑底部「文档定位」：
```
## 文档定位

代码片段模板，适合快速记录单个代码片段、工具类或 API 使用示例。结构精简，重点突出代码和使用说明。与通用编程笔记模板相比，省略了案例对比等章节，更聚焦于代码本身。
```

- [ ] **Step 5: 修复【模板】性能分析.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 底部 `文档定位` 是机械文字
- 模板内 `关联笔记` 部分有空行 `- ` → 改为 `- （待填写）`

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑底部「文档定位」：
```
## 文档定位

性能分析模板，用于记录性能问题的完整分析和优化过程。包含基准数据、瓶颈定位、多方案对比和验证清单。适用于任何需要量化优化的性能场景。
```

编辑「九、经验总结」中的「关联笔记」空行，将 `- ` 改为 `- （待填写）`。

- [ ] **Step 6: 修复【模板】技术文章.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 底部 `文档定位` 是机械文字
- 底部 `相关链接` 路径问题

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑底部「文档定位」：
```
## 文档定位

技术文章模板，包含验证方法、常见误解、适用场景等字段，提升文章的可信度和实用性。适用于需要严谨论证的深度技术内容。
```

编辑底部「相关链接」，将 `[[../00_元数据与模板/文档结构规范]]` 改为 `[[文档结构规范]]`。

- [ ] **Step 7: 修复【模板】架构决策记录.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 第 31 行状态值使用旧格式：`提议 / 讨论中 / 已采纳 / 已实施 / 已验证 / 已过时 / 已拒绝` → 映射为新生命周期：`草稿 / 待验证 / 已验证 / 已过时 / 已归档`
- 第 32 行验证程度字段名应改为 `validation`：`未经测试 / Demo验证 / 项目实战 / 多项目验证`（值本身正确）
- 底部 `文档定位` 是机械文字
- 底部 `相关链接` 路径问题

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑「一、决策概述」表格中的状态行，将：
```
| **状态** | 提议 / 讨论中 / 已采纳 / 已实施 / 已验证 / 已过时 / 已拒绝 |
```
改为：
```
| **状态** | 草稿 / 待验证 / 已验证 / 已过时 / 已归档 |
```

编辑验证程度行，将 `验证程度` 改为 `validation`：
```
| **validation** | 未经测试 / Demo验证 / 项目实战 / 多项目验证 |
```

编辑底部「文档定位」：
```
## 文档定位

架构决策记录（ADR）模板，包含决策矩阵、多维度评分、后果分析。将技术决策从"拍脑袋"变为"有据可查的权衡分析"。适用于任何影响架构走向的技术选型。
```

编辑底部「相关链接」，将 `[[../00_元数据与模板/文档结构规范]]` 改为 `[[文档结构规范]]`。

- [ ] **Step 8: 修复【模板】系统设计说明书.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 第 22 行状态值使用旧格式 → 映射为新生命周期
- 第 23 行验证程度字段名 → 改为 `validation`
- 底部 `文档定位` 是机械文字
- 底部 `相关链接` 路径问题

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑「一、系统概述」表格中的状态行，将：
```
| **状态** | 提议 / 讨论中 / 已采纳 / 已实施 / 已验证 |
```
改为：
```
| **状态** | 草稿 / 待验证 / 已验证 / 已过时 / 已归档 |
```

编辑验证程度行，将 `验证程度` 改为 `validation`：
```
| **validation** | 未经测试 / Demo验证 / 项目实战 / 多项目验证 |
```

编辑底部「文档定位」：
```
## 文档定位

系统设计说明书模板，强制要求思考数据流向和并发模型。包含架构图、数据流设计、接口契约定义。适用于中大型系统的架构设计阶段。
```

编辑底部「相关链接」，将 `[[../00_元数据与模板/文档结构规范]]` 改为 `[[文档结构规范]]`。

- [ ] **Step 9: 修复【模板】通用编程笔记.md**

当前问题：
- `related: []` → 改为 `["文档结构规范", "元数据规范"]`
- 底部 `文档定位` 是机械文字

编辑 frontmatter `related` 字段：
```yaml
related: ["文档结构规范", "元数据规范"]
```

编辑底部「文档定位」：
```
## 文档定位

通用编程笔记模板，适配架构设计、技术原理、工具使用等多种编程类笔记。包含标准化元数据和统一排版结构，兼顾 Obsidian 本地检索和知识图谱。
```

---

## Task 3: 修复 create-doc skill 和元数据规范

**Files:**
- Modify: `.claude/skills/create-doc.md`
- Modify: `UnityKnowledge/00_元数据与模板/元数据规范.md`

- [ ] **Step 1: 审查 create-doc.md 与最新规则的一致性**

读取 `.claude/skills/create-doc.md`，逐项比对：
- 13 种文档类型是否与 `文档定位指南.md` 一致
- YAML 字段是否与 `元数据规范.md` 一致
- 生命周期状态是否使用新格式（草稿/待验证/已验证/已过时/已归档）
- 模板引用是否与实际模板文件一致

- [ ] **Step 2: 修复 create-doc.md 中发现的不一致**

常见修复点：
- 如果 YAML 示例中使用旧状态值（如 `已采纳`），替换为新值（如 `待验证`）
- 如果字段列表缺少 `status` 或 `validation`，补齐
- 更新 `updated` 时间戳为当前日期

- [ ] **Step 3: 审查元数据规范.md 的 category 合法值**

读取 `元数据规范.md`，检查 category 一级分类列表是否完整。当前已知的 category 包括：
- `元数据与模板`, `架构设计`, `核心系统`, `性能优化`, `高级主题`, `高级编程`, `工具链`, `平台适配`, `第三方库`, `项目复盘`, `项目实战`

确认 `导航` 是否应作为合法二级分类（`学习路径导航.md` 使用了 `元数据与模板/导航`）。如果不应存在，需修改 `学习路径导航.md` 的 category。

- [ ] **Step 4: 修复元数据规范.md（如有需要）**

如果发现 category 列表不完整，补充缺失的分类值。

- [ ] **Step 5: 验证模板文件通过 link checker**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/check_links.py 2>&1 | head -50
```

Expected: 模板文件不应有新的断链（之前修复的 `[[]]` 和路径问题应已解决）。

---

## Task 4: 审查并修复迁移脚本

**Files:**
- Modify (if needed): `UnityKnowledge/scripts/migrate_docs_to_latest_rules.py`

- [ ] **Step 1: 审查迁移脚本逻辑**

读取 `UnityKnowledge/scripts/migrate_docs_to_latest_rules.py`，逐项检查：

1. **文档类型前缀列表** (`VALID_PREFIXES`)：是否包含所有 13 种类型？
   - 预期：`【教程】`, `【最佳实践】`, `【踩坑记录】`, `【性能数据】`, `【设计原理】`, `【架构决策】`, `【系统架构】`, `【实战案例】`, `【代码片段】`, `【反模式】`, `【验证报告】`, `【架构演进】`, `【源码解析】`

2. **状态映射** (`STATUS_MAP`)：是否覆盖所有旧状态？
   - 预期包含：`提议`→`草稿`, `讨论中`→`草稿`, `已采纳`→`待验证`, `已实施`→`待验证`, `已拒绝`→`已归档`

3. **category 推断** (`infer_category`)：是否能正确推断二级 category？
   - 例如 `30_性能优化/31_代码优化/` 下的文件应得到 `性能优化/代码优化`

4. **必填字段补齐**：是否补齐所有 9 个字段（title, tags, category, created, updated, description, status, validation, related）？

5. **结构补齐**：是否补「文档定位」和「相关链接」段落？

- [ ] **Step 2: 修复脚本中的问题（如有）**

如果审查发现脚本逻辑与规则不一致，编辑脚本修复。常见问题：
- 缺少文档类型前缀 → 添加到 `VALID_PREFIXES`
- 状态映射不完整 → 补充缺失映射
- category 推断不准确 → 修复推断逻辑

- [ ] **Step 3: 在小范围测试脚本**

Run:
```bash
cd /Users/keynes/git/Doc && python3 -c "
import sys
sys.path.insert(0, 'UnityKnowledge/scripts')
# 先只看脚本会处理哪些文件
import migrate_docs_to_latest_rules
# (dry run if supported, otherwise just verify import works)
"
```

Expected: 脚本无语法错误，可以正常 import。

---

## Task 5: 运行迁移脚本

**Files:**
- Modify (batch): `UnityKnowledge/**/*.md`（227 个文件）

- [ ] **Step 1: 运行迁移脚本**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/migrate_docs_to_latest_rules.py
```

Expected: 脚本处理所有目标文件，输出修改统计。

- [ ] **Step 2: 查看修改统计**

Run:
```bash
git diff --stat UnityKnowledge/ .claude/skills/create-doc.md
```

Expected: 大量文件被修改，统计信息显示变更行数。

- [ ] **Step 3: 抽查 2-3 个文件确认修改质量**

Run:
```bash
git diff UnityKnowledge/10_架构设计/【代码片段】事件总线.md | head -60
git diff UnityKnowledge/30_性能优化/31_代码优化/【性能数据】foreach\ vs\ for.md | head -60
```

Expected: frontmatter 已标准化（9 字段齐全、状态已映射、category 已推断、validation 已补齐）。

---

## Task 6: 运行元数据校验

**Files:**
- 无新文件修改（仅验证）

- [ ] **Step 1: 运行严格校验**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/validate_metadata.py --strict
```

Expected: 输出校验结果。目标：错误 0，警告 0。

- [ ] **Step 2: 如果有错误，分析并修复**

根据校验输出的具体错误，针对性地修复。常见问题：
- 缺失字段 → 手动补充或修复脚本的补齐逻辑后重跑
- 标题前缀不在合法列表 → 添加到脚本的 `VALID_PREFIXES` 或修正文件名
- 日期格式不正确 → 修正日期字符串

修复后重新运行校验，直到：
```
错误: 0
警告: 0
```

- [ ] **Step 3: 确认校验通过**

记录校验通过输出作为迁移里程碑。

---

## Task 7: Claude 智能补结构 — P0 目录（00_元数据与模板）

**Files:**
- Modify: `UnityKnowledge/00_元数据与模板/*.md`（19 个文件）

**说明：** 本 Task 和后续 Task 7-11 需要Claude 的判断力。每个目录的处理方式是：批量读取目录内所有文档，识别问题，智能修复。

- [ ] **Step 1: 读取 00_元数据与模板 目录所有文档**

批量读取目录内所有 .md 文件，为每个文档记录：
- `文档定位` 段落是否有意义（非机械模板文字）
- `相关链接` 段落是否指向真实文档
- `related` 字段是否为空

- [ ] **Step 2: 逐文件修复「文档定位」和「相关链接」**

对每个文档，根据其内容生成有意义的定位说明（3 句话以内，说清「是什么、给谁看、解决什么问题」），并填充 related 字段和「相关链接」段落。

质量标准：
- 文档定位：3 句话以内，有具体内容
- 相关链接：至少 2 个，指向同目录或相关目录的真实文档
- related 字段：至少 2 个文档名

- [ ] **Step 3: 确认本目录无机械模板文字**

快速扫一遍修改后的文件，确认没有「本文档用于沉淀 ... 相关知识，说明其适用场景、核心内容和实践注意事项」之类的机械文字。

---

## Task 8: Claude 智能补结构 — P1 目录（10_架构设计）

**Files:**
- Modify: `UnityKnowledge/10_架构设计/*.md`（~40 个文件）

- [ ] **Step 1: 批量读取 10_架构设计 目录所有文档**

读取目录内所有 .md 文件，记录每个文档的：
- 标题前缀是否合理
- `文档定位` 是否有意义
- `related` 是否为空
- H1 是否与 title 一致
- 是否有空 wiki-link

- [ ] **Step 2: 批量修复所有问题**

对每个文档：
- 补充有意义的「文档定位」（基于文档类型和内容推断）
- 填充 `related` 字段（基于目录内文档关系，2-3 个相关文档）
- 修复标题前缀不匹配
- 修复 H1 与 title 不一致
- 清理空 wiki-link
- 修复 `相关链接` 内容错误

- [ ] **Step 3: 抽查 3-5 个文档确认质量**

确认修改后的文档没有机械重复内容，文档定位有意义。

---

## Task 9: Claude 智能补结构 — P2 目录（20_核心系统）

**Files:**
- Modify: `UnityKnowledge/20_核心系统/**/*.md`（~65 个文件，含子目录 21-29）

- [ ] **Step 1: 批量读取 20_核心系统 所有子目录的文档**

子目录：21_动画系统, 22_渲染系统, 23_物理系统, 24_输入系统, 25_音频系统, 游戏系统, 等。

记录每个文档的问题（同 Task 8 的检查项）。

- [ ] **Step 2: 按子目录批量修复**

对每个子目录的所有文档进行统一修复（同 Task 8 Step 2 的修复项）。

- [ ] **Step 3: 抽查每个子目录至少 1 个文档确认质量**

---

## Task 10: Claude 智能补结构 — P3 目录（30_性能优化）

**Files:**
- Modify: `UnityKnowledge/30_性能优化/**/*.md`（~55 个文件，含子目录 31-34）

- [ ] **Step 1: 批量读取 30_性能优化 所有子目录的文档**

子目录：31_代码优化, 32_内存管理, 33_渲染优化, 34_启动时间优化。

- [ ] **Step 2: 按子目录批量修复**

同 Task 9 Step 2。

- [ ] **Step 3: 抽查确认质量**

---

## Task 11: Claude 智能补结构 — P4 目录（其余所有）

**Files:**
- Modify: `UnityKnowledge/25_DOTS技术栈/*.md`（5 个）
- Modify: `UnityKnowledge/35_高级主题/*.md`（4 个）
- Modify: `UnityKnowledge/36_高级编程/*.md`（4 个）
- Modify: `UnityKnowledge/40_工具链/**/*.md`（~10 个）
- Modify: `UnityKnowledge/50_平台适配/*.md`（6 个）
- Modify: `UnityKnowledge/60_第三方库/*.md`（6 个）
- Modify: `UnityKnowledge/90_项目复盘/*.md`（1 个）
- Modify: `UnityKnowledge/100_项目实战/**/*.md`（~16 个）

- [ ] **Step 1: 批量读取所有剩余目录的文档**

按目录分组读取。

- [ ] **Step 2: 批量修复**

同 Task 8 Step 2。这些目录文档较少，可以一次性处理。

- [ ] **Step 3: 抽查确认质量**

---

## Task 12: 修复断链

**Files:**
- 修改数量取决于断链数量和类型

- [ ] **Step 1: 运行链接检查获取断链列表**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/check_links.py 2>&1
```

Expected: 输出所有断链。记录总数。

- [ ] **Step 2: 对断链分类处理**

对每条断链，按以下规则处理：

| 断链类型 | 处理方式 |
|----------|----------|
| 模板占位链接 `[[]]` | 改为普通文本 `（待填写）` |
| URL 编码路径（如 `%E4%BB%A3%E7%A0%81`） | 改为真实文件名 |
| 文档已改名/移动 | 指向当前真实存在的文档 |
| 文档确实不存在 | 改为 `（待整理）` 文本，或创建 Inbox 草稿 |

- [ ] **Step 3: 重跑链接检查**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/check_links.py 2>&1
```

Expected: 如果仍有断链，继续修复。循环直到输出 0 断链。

- [ ] **Step 4: 确认 0 断链**

最终确认：
```
断链: 0
```

---

## Task 13: 质量修复

**Files:**
- Modify: 可能涉及多个文件的质量问题

**说明：** 本 Task 是对 Task 7-11 的补充扫尾。检查并修复之前步骤可能遗漏的质量问题。

- [ ] **Step 1: 全库扫描标题前缀一致性**

检查所有文档的：
- frontmatter `title` 字段的前缀
- H1 标题的前缀
- 文件名的前缀

三者应一致。如不一致，根据内容判断正确前缀并统一。

- [ ] **Step 2: 检查 status 和 validation 是否过于乐观**

扫描所有文档，如果发现：
- `status: 已验证` 但 `validation: 未经测试` → 降级 status 为 `待验证`
- `status: 已验证` 但没有实际验证内容 → 降级为 `待验证`

- [ ] **Step 3: 检查自引用链接**

扫描所有 `相关链接` 段落，确保没有文档链接到自身。

- [ ] **Step 4: 抽查重点目录**

重点抽查：`00_元数据与模板`, `10_架构设计`, `30_性能优化`, `20_核心系统`, `40_工具链`

确认：
- 无机械重复内容
- 标题前缀合理
- category 符合目录
- status/validation 合理

---

## Task 14: 最终校验

**Files:**
- 无新文件修改

- [ ] **Step 1: 运行元数据严格校验**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/validate_metadata.py --strict
```

Expected:
```
错误: 0
警告: 0
```

- [ ] **Step 2: 运行链接检查**

Run:
```bash
cd /Users/keynes/git/Doc && python3 UnityKnowledge/scripts/check_links.py 2>&1
```

Expected:
```
断链: 0
```

- [ ] **Step 3: 查看完整修改统计**

Run:
```bash
git diff --stat
```

Expected: 显示所有修改文件的统计摘要。

- [ ] **Step 4: 生成迁移报告**

汇总以下信息：
- 总修改文件数
- 元数据校验结果
- 链接检查结果
- 残留人工复核清单（如有任何无法自动修复的问题）
- 回滚指令：`git restore UnityKnowledge .claude/skills/create-doc.md`
