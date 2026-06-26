# UnityKnowledge 维护日志（log.md）

> append-only。每行前缀 `## [YYYY-MM-DD] ingest|query|lint | 标题`，可 `grep "^## \[" log.md | tail`。

## [2026-06-24] lint | P1 地基初始化
- 生成首版 index.md
- 全库回填 author 字段
- 统一 lint 基线跑通

## [2026-06-25] query | 回填 UGUI 性能优化规则清单
- 新增 [[20_核心系统/26_UI系统/【片段】UGUI 性能优化规则清单]]（author:llm + sources）
- 将「UGUI 如何实现 / 如何优化」问答沉淀为 R1–R6 规则集 + ROI 表 + 监控阈值 + Code Review 清单
- 来源：踩坑记录、UI卡顿优化实战案例、合批机制深度解析、UGUI 第4/7章
- 更新 UI系统专题索引（新增「规则清单」分类 + 目录条目 + 相关链接），避免孤儿页

## [2026-06-26] ingest | UGUI性能优化实战总览
- 读源：知乎《Unity性能优化总结-UI》(DragonL, 2025-08) → https://zhuanlan.zhihu.com/p/1941865546690827415
- 新增综述页：20_核心系统/26_UI系统/【综述】UGUI性能优化实战总览.md（author:llm，sources 含原文 URL + 4 篇既有笔记）
- 新增主题：图集/SpriteAtlas 打包冗余规则、RawImage 陷阱、图集尺寸策略、Mask vs RectMask2D 数量决策、动静分离、界面切换开销数据、刘海屏/横竖屏适配、UI 混合粒子、字体加粗与 Font Texture
- 重叠主题（合批/DrawCall/SendWill/TMP）以链接指向既有深度笔记，未重复展开；并与 [[【片段】UGUI 性能优化规则清单]] 互链
- 更新 README.md、UI系统专题索引.md（综述分类 + 推荐阅读首位 + 目录条目）；重生成 UnityKnowledge/index.md（254 篇）
- lint：新文档零 issue，未引入新断链/孤儿

## [2026-06-26] query | 回填 Playable API 使用指南
- 新增 [[20_核心系统/21_动画系统/【笔记】Playable API 使用指南]]（author:llm + sources）
- 将「讲解 Playable 的使用」问答沉淀为：概念定位 / 数据流与求值顺序 / 三大类节点（PlayableGraph·ScriptPlayable·动画类）/ 最小示例 / 程序化动画（IAnimationJob）/ 选型表 / 高频坑速查
- 来源：[[Clippings/【Unity】Playable使用细则]]（知乎 p/632890306）、Unity 官方 Playables 文档、[[【设计原理】Animator深度解析]]
- 更新 21_动画系统 README（入口）+ 动画系统专题索引（新增「笔记」分类 + 目录条目）+ index.md，避免孤儿页

## [2026-06-26] ingest | 新增 tolua 专题
- 新增专题索引：35_高级主题/tolua专题索引.md（author:llm），聚合 toLua# 绑定机制/性能/踩坑 + 既有热更新选型文档
- 新增 3 篇笔记：[[35_高级主题/【笔记】tolua入门与调用机制]]（Wrap/LuaState/C#↔Lua 互调）、[[35_高级主题/【笔记】tolua性能与GC优化]]（边界开销/GC/LuaJIT 平台差异）、[[35_高级主题/【踩坑】tolua热更新常见坑]]（7 类坑速查表）
- 新增 35_高级主题/README.md（领域入口，避免孤儿页）
- 内容为 LLM 基于训练知识编译（非外部源），统一标 status:待验证，未编造 sources
- 重生成 UnityKnowledge/index.md（260 篇）

## [2026-06-26] ingest | 补充 Lua 语法速查
- 新增 [[35_高级主题/【笔记】Lua语法速查]]（author:llm，status:待验证）：以 Lua 5.1/LuaJIT（tolua 默认）为准
- 覆盖：8 种数据类型、运算符（~= / and or / ..）、控制流（含无 continue）、函数（多返回值/可变参/`:` 糖）、table（1-based 索引、pairs/ipairs）、metatable 面向对象、闭包/upvalue、require 模块、给 C# 开发者的易错点速查表
- 更新 tolua专题索引（收录数 5→6、阅读顺序新增第 2 位、笔记分类/目录/相关链接）与 35_高级主题/README 入口
- 重生成 UnityKnowledge/index.md（261 篇）
