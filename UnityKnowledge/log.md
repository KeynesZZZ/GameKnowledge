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

## [2026-06-26] ingest | 补全热更新方案对比（机制+选型总览）
- 扩写 [[40_工具链/【设计原理】热更新方案对比]]（author:llm，status:待验证）：60 → ~217 行，定位为热更专题的「机制+选型总览页」
- 核心修正：拆分「资源热更(AssetBundle/Addressables) vs 代码热更」两条正交轴（旧版混在同一张表）；新增根因（iOS W^X 禁 JIT → 只能解释器/AOT）、三类方案执行机制剖析（Lua 系 / ILRuntime / HybridCLR + puerts）、多维对比表、选型决策矩阵、共性工程问题、DO/DON'T
- 纠偏：HybridCLR 由「侵入性强」改为「低侵入，代价在构建管线 + 泛型补充 AOT 元数据」；指明 LuaJIT iOS 无 JIT、基准以 iOS 解释器模式为准；区分 xLua Hotfix（可注入式热修已上线 C#）与 toLua#（不可热修 C# 接口）
- 「怎么做」交给周边教程（Addressables / 打包与热更新），本文仅 wikilink 不重复
- 内容为 LLM 基于训练知识编译（非外部源），未编造 sources；官方链接（HybridCLR/xLua/ILRuntime/puerts/Addressables）放正文「相关链接」作参考
- 重生成 UnityKnowledge/index.md（261 篇，仅本文 description 同步）；lint：本文档零 issue，工具链目录 64 链接全有效（既有 44 ERROR 均为模板/Clippings 作者标签断链，与本次无关）

## [2026-06-27] ingest | 热更新方案对比迁入 35_高级主题
- [[35_高级主题/【设计原理】热更新方案对比]] 由 40_工具链 迁入 35_高级主题（与 tolua 专题/打包与热更聚合，图谱更连通）
- 同步本文：category 工具链→高级主题、updated→2026-06-27；文件内相对 wikilink 改同目录 basename（tolua 系列 / 打包与热更），Addressables 链接补 ../40_工具链/ 跨目录前缀
- 入链同步：tolua专题索引（推荐顺序/分类标签/按目录段重组，覆盖目录数 2→1）、tolua入门 related 去旧路径前缀、Addressables教程 markdown 链接改 ../35_高级主题/
- 重生成 UnityKnowledge/index.md（262 篇，本文归入 35_高级主题 段）；lint ERROR=44 不变（零新断链），35_高级主题(133)/40_工具链(43) 目录链接全有效
- 附注：lint 新增 1 WARN 孤儿页 [[35_高级主题/【实战案例】tolua热更新系统完整落地]] 为外部新建未跟踪文件，与本次无关

## [2026-06-27] ingest | 新增 Lua 面向对象深入笔记
- 新增 [[35_高级主题/【笔记】Lua面向对象深入]]（author:llm，status:待验证）：把 Lua OOP 从语法糖讲到底层机制
- 覆盖：`__index` 读路径查找算法、self 本质（类方法 vs 实例方法）、生产级 `class()` 逐行剖析、继承链两条委托方向、super 正确写法（`.` + 手动 self）、`__index` vs `__newindex` 读写不对称、原型委托 vs 闭包范式权衡、访问控制/接口的 duck typing、`.` vs `:` 深坑、metatable 链查找的性能代价（呼应 iOS 解释器模式）、tolua 热更语境三点、C# vs Lua OOP 速查表
- 定位为 [[35_高级主题/【笔记】Lua语法速查]] 第七节（基础）的机制深入篇，不重复基础语法
- 更新 tolua专题索引（收录数 6→7、笔记分布 3→4、推荐阅读顺序第 3 位、笔记分类/按目录/相关链接）；互链避免孤儿
- 内容为 LLM 基于训练知识编译（非外部源），未编造 sources
- 重生成 UnityKnowledge/index.md（263 篇）；lint：新文档零 issue，35_高级主题 157 链接全有效（ERROR=44 不变）

## [2026-06-27] ingest | Lua OOP 笔记补充云风 class/单例/重载（首次引入 sources）
- 读源：博客园《Lua 面向对象》（Fflyqaq, 2020）→ https://www.cnblogs.com/Fflyqaq/p/13292388.html
- 增量补充 [[35_高级主题/【笔记】Lua面向对象深入]]：云风 class.lua 虚表实现（类表代理独立虚表 + 继承查找缓存 `vtb[k]=ret`，呼应第十节性能）、构造链基类优先递归（对比第五节手动 super）、单例模式（Instance+m_instance）、重载模拟（可变参+nil 判断）
- 该源基础部分（类/封装/继承/多态）与既有笔记重叠且笔记更深入机制（如读写不对称），仅取增量；文章 1.3「boy.name 不影响 person」正印证第六节读委托/写实例
- 首次为该笔记加 sources（引用即契约）；基础机制部分仍为 LLM 基于训练知识编译，非整篇 ingest
- 重生成 UnityKnowledge/index.md；lint：本文档零 issue

## [2026-06-27] ingest | 新增 tolua 完整实战案例
- 新增 [[35_高级主题/【实战案例】tolua热更新系统完整落地]]（author:llm，status:待验证）：以休闲游戏为例的 toLua# 热更新系统端到端参考实现
- 覆盖：C# 宿主层（LuaEnv/HotUpdateManager/稳定接口契约）、Lua 业务层（main + 模块）、版本比对→下载→校验→Reload 时序、对接踩坑文档的问题处置表、效果权衡与换方案建议
- 明确标注为参考实现（非某次真实项目复盘），未编造实测性能数据
- 更新 tolua专题索引（收录数→8、推荐阅读顺序 #8、新增「实战案例」分类/目录/相关链接）与 35_高级主题/README
- 注：用户同期新增 [[35_高级主题/【笔记】Lua面向对象深入]] 并将 [[【设计原理】热更新方案对比]] 由 40_工具链 移入本目录，索引已同步
- 重生成 UnityKnowledge/index.md（264 篇）

## [2026-06-27] ingest | 新增 Unity 客户端面试题综述（按域补全答案）
- 读源：知乎《Unity客户端面试题记录》（Ray小铭）→ https://zhuanlan.zhihu.com/p/449331086
- 新增 [[35_高级主题/【综述】Unity客户端面试题]]（author:llm，status:待验证，sources 含原文 URL + 6 篇互链笔记）：跨域面试速查 + 复习清单
- 覆盖 29 道题，按域分 7 章：C#/.NET（GC/闭包/unsafe/值引用类型/il2cpp vs Mono）、渲染（渲染管线/UGUI渲染流程/合批/UGUI优化/粒子层级/实时阴影）、算法（A*/DFS-BFS/快排/三消）、Lua（数据类型/字符串拼接/sort/OOP/GC与泄漏）、3D数学（叉乘判左右/2D射线相交/AABB Slab法）、网络（GET vs POST/TCP握手挥手）、Unity工程（AB打包/Animator优化/骨骼动画/背包虚拟化）
- 原文已给答案的题目整理自原文（如渲染管线、合批、AB策略、叉乘、TCP）；原文只列题目无答案的由 LLM 补充并明确标注「（LLM 补充）」（如 A*、il2cpp/Mono、实时阴影、AABB Slab、骨骼动画、Lua sort/OOP/GC 等），未编造数据
- 强调作者经验：中级主考算法/Lua/3D数学，3D数学公式原理为高频失分点
- 交叉互链既有真相层笔记（Lua面向对象深入/UGUI性能优化综述/打包与热更新/Unity内存管理/tolua GC/三消架构），避免孤儿且可下钻
- 更新 35_高级主题/README 入口；重生成 UnityKnowledge/index.md（264→266 篇）
- lint：新文档与 35_高级主题 目录零 issue；总计 ERROR=48/WARN=25 均为既有 UGUI/、Clippings/、性能优化/ 书籍摘录的作者署名 token（黑客不黑/洛桑/MrLiu 等），非本次引入

## [2026-06-27] query | 回填 AB 压缩格式选型（LZMA vs LZ4）
- 用户追问综述第 26 题 AB 打包的压缩选择，对话答案回填 [[35_高级主题/【综述】Unity客户端面试题]] 第 26 题新增「压缩格式选型」子节
- 内容：LZMA/LZ4/不压缩 三方对比表（压缩率/解压速度/随机访问）+ 原理（LZMA 流式全局字典 vs LZ4 块压缩可 seek）+ 选型决策（热更用 LZ4、首包用 LZMA、CDN 传 LZMA+本地缓存转可随机访问）
- 未改 frontmatter（updated 仍 2026-06-27）；无新增断链

## [2026-06-28] ingest | 新增 Unity 资源依赖与打包陷阱综述（原文反爬截断，据片段+官方文档撰写）
- 读源：知乎《为什么你的包体总是莫名增大？深度解析 Unity 资源依赖关系与打包陷阱》（【Unity 底层与原理向】03）→ https://zhuanlan.zhihu.com/p/1962283012189292152
  - ⚠️ 反爬限制：web reader / curl / Googlebot / 知乎 API / Wayback / RSSHub 全部受阻，仅获取到原文**开头约 1/3**（标题、开篇四问、图书馆引用链类比、Resources 模式开头），正文后半未获取
  - 用户决策：基于「已获取片段 + Unity 官方 AssetBundle 依赖文档 + 工程经验」撰写综述，文内严格区分标注
- 新增 [[35_高级主题/【综述】Unity资源依赖与打包陷阱]]（author:llm，status:待验证，sources 含知乎原文 + Unity 官方文档 ×3 + 互链笔记 ×6）
- 内容：问题四问（原文）→ 图书馆类比（原文，截断处标注）→ 依赖系统底层机制（LLM 补充，据 Unity 官方）→ 打包冗余成因（LLM 补充，含官方 383KB+377KB→359KB+2×20KB 算账）→ 灵异事件归因 → 依赖分析工具（Browser/Analyzer/Analyze/GetDependencies/BuildReport）→ 优化策略（公共依赖单独成包/加载顺序/Shader 图集字体/分包粒度/Resources 清理）→ 避坑清单
- 来源分离：`（原文）` 标注整理自原文已获取片段；`（LLM 补充，据 Unity 官方文档）` 标注 LLM 编译部分，并在文首声明"可能与原文后半不一致，引用前对照原文"，未编造 sources
- 聚焦增量：通用 AB 依赖树/构建期冗余/分析工具/打包策略；不重述 UI 图集冗余（→UGUI性能优化综述）、Addressables 用法（→资源管线-Addressables）、热更选型（→热更新方案对比）
- 交叉互链既有笔记（打包与热更新/Unity客户端面试题/资源管线-Addressables/资源卸载指南/内存分析工具使用指南/Unity内存管理/资源预加载策略/UGUI性能优化实战总览），避免孤儿且可下钻
- 更新 35_高级主题/README 入口；重生成 UnityKnowledge/index.md（273 篇）
- lint：新文档与 35_高级主题 目录零 issue；总计 ERROR=50/WARN=32 均为既有 UGUI/、Clippings/、性能优化/ 书籍摘录的作者署名 token 断链及其在 index.md 的镜像，非本次引入
