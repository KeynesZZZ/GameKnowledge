---
title: 【综述】UGUI性能优化实战总览
tags: ["Unity", "UI", "UI系统", "UGUI", "性能优化", "综述", "图集", "适配"]
category: 核心系统/UI系统
created: "2026-06-25 11:30"
updated: "2026-06-25 11:30"
description: 综合外部原文与既有笔记，覆盖图集、合批、Mask、动静分离、适配等 UGUI 性能优化全景
unity_version: 2021.3+
status: 待验证
validation: 部分结论含原文量化数据，未独立复测
related: ["【设计原理】UGUI合批机制深度解析", "【性能数据】UGUI DrawCall影响因素全面测试", "【踩坑记录】UGUI常见性能陷阱与根因分析", "【最佳实践】TextMeshPro性能优化实战"]
author: llm
sources:
  - https://zhuanlan.zhihu.com/p/1941865546690827415
  - "[[【设计原理】UGUI合批机制深度解析]]"
  - "[[【性能数据】UGUI DrawCall影响因素全面测试]]"
  - "[[【踩坑记录】UGUI常见性能陷阱与根因分析]]"
  - "[[【最佳实践】TextMeshPro性能优化实战]]"
---

# 【综述】UGUI性能优化实战总览

> 本页由 LLM 跨外部原文与既有笔记综合生成。`sources` 是引用契约，每条结论可追溯。`#综述` `#性能优化` `#UI`

## 文档定位

本综述从**实战优化全景**角度，把一篇 UGUI 性能优化长文（[知乎原文](https://zhuanlan.zhihu.com/p/1941865546690827415)）与本地既有深度笔记合并成一张可执行的总图。

它的价值在于**广度 + 速查**：图集打包、合批、Mask 取舍、动静分离、界面切换、字体、特效混合、刘海屏/横竖屏适配——一条线串起来。深度机制不在本页展开，而是指向真相层笔记：

- **合批底层机制** → [[【设计原理】UGUI合批机制深度解析]]
- **DrawCall 影响因子量化** → [[【性能数据】UGUI DrawCall影响因素全面测试]]
- **常见陷阱与根因** → [[【踩坑记录】UGUI常见性能陷阱与根因分析]]
- **TextMeshPro 专项** → [[【最佳实践】TextMeshPro性能优化实战]]

> 注：原文为个人总结，部分量化数据（界面切换耗时等）为单机测量，迁移到自身项目前请按"[[文档生命周期]]"以 `待验证` 对待，关键结论建议自测复核。

---

## 全景速查表

| 症状 / 目标 | 关键手段 | 深度文档 |
|---|---|---|
| DrawCall 高 | 合批、图集、减少 Mask、Cull Transparent | [[【性能数据】UGUI DrawCall影响因素全面测试]] |
| `Canvas.BuildBatch` 卡 | 动静分离、拆分 Canvas、减少元素变动 | [[【设计原理】UGUI合批机制深度解析]] |
| `SendWillRenderCanvases` 高 | 减少顶点属性变动、动静分离、关注 `Font.CacheFontForText` | [[【踩坑记录】UGUI常见性能陷阱与根因分析]] |
| 界面打开/关闭卡顿 | CullingMask 隐藏替代 SetActive、预实例化 | 本文 §界面切换开销 |
| 包体/内存里图集冗余 | SpriteAtlas + AssetBundle 打包策略 | 本文 §图集 |
| 滑动列表卡 | 独立 Canvas、关 Pixel Perfect、Mask→RectMask2D | 本文 §ScrollRect |
| 字体纹理过大 / TMP 耗时 | 减少字号、静态字体、单独 Canvas | [[【最佳实践】TextMeshPro性能优化实战]] |

---

## 一、图集（Sprite Atlas）

### 1.1 打包工具

- 第三方 **Texture Packer**
- Unity 自带 **Sprite Packer / Sprite Atlas**

### 1.2 `Include in Build` 与 AssetBundle 冗余规则

这是最容易踩的冗余点，原文给出明确规则：

- 若某个 Sprite 加入了 SpriteAtlas，**真正使用该 Sprite 的资源引用的是 `sactx` 图集纹理**，而非小 Texture2D。
- **SpriteAtlas 不打进 AssetBundle 时**：必须勾选 `Include in Build`，否则 `sactx` 纹理"消失"；且 SpriteAtlas 中所有小 Sprite **必须打进同一个 AssetBundle**，否则 `sactx` 冗余。
- **SpriteAtlas 本身打进 AssetBundle 时**：`sactx` 永不冗余（指打包造成的冗余）。此时小 Sprite 也最好打进 AssetBundle，否则小 Sprite 会冗余。
- 勾不勾 `Include in Build` **不影响依赖关系**，唯一区别是是否"主动显示图片"：勾选主动显示，不勾需脚本控制显示。

### 1.3 包体出现重复资源（RawImage 陷阱）

> 用 Sprite Packer 打图集时，**图集中的图片不能被 `RawImage` 引用**。

被引用则会另外打包一份，同一张图存在两处，包体增大。结论：

- `RawImage` 不要引用 Sprite 格式图片；
- 若一定要引用，**不要把该图打入图集**。

### 1.4 取 Sprite 在图集中的 UV

```csharp
// 获取 Sprite 在所在图集中的 Outer UV（用于自定义 mesh / RawImage 等）
Vector4 uv = Sprites.DataUtility.GetOuterUV(activeSprite);
```

---

## 二、图集尺寸策略：8 张 1024 vs 2 张 2048

原文给出的分配原则（内存与 DrawCall 权衡）：

- **常驻内存的通用资源**：可放宽上限，允许 2048 甚至 4096 一张。
- **单个游戏功能内部的独有图集**：建议控制在 **1024 以内**；当用量达到 **3 张 1024** 级别，才允许升到 2048。
- 权衡逻辑：分配合理时，多一张贴图理论上只多 1 个 DrawCall；而把 2 张 1024 强行并成 1 张 2048，要么空白多、要么合并不合理，内存反而浪费。
- Shader 绑定贴图消耗是 ns 级，**主要消耗在渲染面积（填充率）和 DrawCall**，而非贴图绑定本身。

---

## 三、DrawCall 与合批（速查，深度见专题）

深度机制见 [[【设计原理】UGUI合批机制深度解析]]、量化数据见 [[【性能数据】UGUI DrawCall影响因素全面测试]]。本节只补原文两条易被忽视的实战结论。

### 3.1 挪到屏幕外不会减少 DrawCall

UGUI 合并网格以 **Canvas 为单位**，把 UI 元素移出屏幕并不能降 DrawCall。

- Unity 5.2 之前：需 `Screen Space – Camera` + 把移出元素放独立 Canvas 再整体移出；
- 5.2 之后上述方法失效；
- **可行做法**：把移出的 UI 元素放在**独立 Canvas**，再把该 Canvas 的 Layer 改为相机 Culling Mask 未选中的 Layer，从而剔除这部分 Draw Call。相比直接 `Enabled = false`，能省一定 CPU 开销。

### 3.2 `SetActive(true)` 产生 GC

切换 `SetActive` 会产生 `GC.Alloc`。若要同时降 Batches 和 GC，原文方案：

- 新增一个 Layer（如 `OutUI`），在相机 Culling Mask 中取消勾选（不渲染该 Layer）；
- 界面切换时**直接改 Canvas 的 Layer** 来实现"隐藏"；
- 注意：**屏蔽事件**（禁用可交互元素）、禁用动态 UI 元素。

优缺点：切换几乎零开销、无多余 DrawCall；缺点是"隐藏"状态仍有持续开销（通常不大）、对应 Mesh 仍常驻内存（通常不大）。

> 禁忌：**不要在 `OnEnable` / `OnDisable` 里写重要逻辑**，否则产生大量 GC 与逻辑消耗。

---

## 四、Rebuild 与 Rebatch 双阶段开销

Canvas 在 CPU 侧的主要消耗来自这两个阶段（深度见 [[【设计原理】UGUI合批机制深度解析]]）：

| 阶段 | 单位 | 触发 | 开销归属（Profiler） |
|---|---|---|---|
| **Rebuild** | UI 元素 | 顶点属性变化（Color、Size 等） | `Canvas.SendWillRenderCanvases` |
| **Rebatch** | Canvas | Canvas 内任意元素变化（含位置） | `Canvas.BuildBatch` + 子线程 `Canvas.SortJob` / `Canvas.GeometryJob` |

定位技巧：

- **哪个 Canvas 在 Rebatch**：Profiler 选中 `Canvas.BuildBatch`，右侧对象列表即当前帧发生 Rebatch 的 Canvas 名。
- **哪个元素在 Rebuild**：Profiler 看不出具体元素（这是排查难点）。

重建 vs 更新频率：

- 元素变了 → 引发网格**重建（BuildBatch）**；
- 只有**顶点属性**变了 → 才出现网格**更新（SendWillRenderCanvases）**；
- 重建频率高于更新，因为更新总是伴随重建。

---

## 五、隐藏 UI 的正确姿势（汇总）

| 手法 | 优点 | 注意 |
|---|---|---|
| `SetActive(false)` | 彻底停渲染与逻辑 | 切换有 GC、Instantiate/Destroy 开销大 |
| 改 Canvas Layer + CullingMask | 切换零开销、无多余 DrawCall | Mesh 常驻内存、需屏蔽事件 |
| `transform.localScale = 0` | 降 CPU 消耗 | 仍参与 Rebuild 排序判断，非完全剔除 |
| `CanvasRenderer` Alpha=0 | DrawCall 与顶点更少（做了不绘制特殊处理） | 与 `Cull Transparent Mesh` 配合 |

---

## 六、动静分离

> "动静分离"主要用来优化 **`Canvas.BuildBatch`**，**优化不了 `Canvas.SendWillRenderCanvases`**。

原理：UGUI 网格更新/重建以 **Canvas 为单位**，且只在其内 UI 元素变动时进行。把动态元素与静态元素分到不同 Canvas 后：

- 动态元素的变化只在小范围 Canvas 内引发网格更新/重建；
- 静态元素所在的 Canvas 不再出现网格更新/重建开销。

> 这是 UGUI 优化的第一性原则之一，详见 [[【设计原理】UGUI合批机制深度解析]]。

---

## 七、Mask vs RectMask2D（详细合批性质）

这是原文最有价值的一段——多数资料只说"RectMask2D 省 DrawCall"，但**到底用哪个取决于界面里 Mask 的数量**。

### 7.1 RectMask2D 性质

- **不依赖** Image 组件，裁剪区域 = 自身 `RectTransform` 的 rect。
- 性质1：RectMask2D 节点下**所有孩子不能与外界 UI 合批**，且**多个 RectMask2D 之间不能合批**。
- 性质2：计算 Depth 时按一般 UI 节点看待，但没有 CanvasRenderer，不能作为任何 UI 控件的 bottomUI。
- **持续开销**：每帧计算子节点裁剪区域，子节点多时耗时较高。

### 7.2 Mask 性质

- **依赖**一个 Image 组件，裁剪区域 = Image 大小。
- 性质1：首尾各多 **2 个 Draw Call**（首=Mask 节点，尾=其孩子遍历完）；多个 Mask 间若符合合批条件，这两个 Draw Call 可对应合批（Mask1 首 与 Mask2 首 合；尾同理；**首尾不能合**）。
- 性质2：遍历到 Mask 的首时，当作不可合批节点，但**可作为其孩子 UI 节点的 bottomUI**。
- 性质3：Mask 内 UI 节点 与 Mask 外 UI 节点**不能合批**；但多个 Mask 内的 UI 节点间若符合条件**可以合批**。

### 7.3 数量决策结论

| 界面 Mask 数量 | 推荐 |
|---|---|
| 1 个 | **RectMask2D** 优于 Mask |
| 2 个 | 两者差不多 |
| > 2 个 | **Mask** 优于 RectMask2D（因为 Mask 间可合批） |

> 一句话：**不是 Mask 越多越差**——Mask 间可以合批。减少 Mask 的真正原因是 GPU Overdraw 与额外 DrawCall，需与 RectMask2D 的 CPU 持续裁剪计算权衡（一个省 GPU、一个省 CPU）。

---

## 八、ScrollRect 优化

原文列出的滚动列表卡顿排查与处理：

1. **看子函数占比**：若 `OnTransformChanged` 触发了 `OnDimensionChanged`（耗时明显升高），通常是开了 **Pixel Perfect** → 拖动时**暂时关闭 Pixel Perfect**。
2. **自身开销高**：多半是移动的 UI 元素数量过大 → 策略上减少元素数（如做成**拖动翻页**，一次只移动两页元素）。
3. **Mask 组件**：尝试把 Mask 换成 **RectMask2D**（注意结合 §7 的数量决策）。

背包/滚动界面拖动开销补充：

- 把**滚动部分独立成 Canvas**，缩小 `Canvas.BuildBatch` 范围；
- 尽可能**不用 PixelPerfect**，避免 `SendWillRenderCanvases()` 与 `BuildBatch`；
- 改 `Image.color` **本质是改顶点色**，会引起网格 Rebuild（同时触发 BuildBatch 与 SendWill）。

---

## 九、界面切换开销数据（原文单机测量）

原文给了一组界面切换耗时（仅供参考，未独立复测）：

| 方式 | 隐藏 | 显示 |
|---|---|---|
| `Instantiate` / `Destroy` | 60.71 ms | 229.00 ms |
| `GameObject.Activate` / `Deactivate` | 40.56 ms | 124.57 ms |

切换耗时主要来自：`Instantiate/Destroy`、`Activate/Deactivate`、`CanvasRenderer.OnRectTransformChange`。

减耗要点：

- **不修改 parent**，避免 `XXXParentChanged` 回调；
- **尽量避免 Pixel Perfect**；
- 用 **CullingMask** 做软隐藏（见 §五）。

---

## 十、字体（Font）优化

深度 TMP 优化见 [[【最佳实践】TextMeshPro性能优化实战]]，本节补原文几条通用要点。

### 10.1 加粗需要"粗体字面文件"

用 `msyh`（微软雅黑）想用粗体，资源里要**同时放 `msyh` 和 `msyhbd`**，否则 UGUI 拿到的只是 Unity 自己加粗（伪粗）的 `msyh`。

### 10.2 动态字体 Font Texture 过大

Font Texture 尺寸受**字体种类、字号、文本量**影响。避免过大的手段：

- **减少多种字号的使用**（字号种类越多，纹理越大）。

### 10.3 TextMeshPro Fallback 遍历序列

TMP 的 Fallback（后备字体）在出现当前字体不支持的字符时，按以下序列遍历，直到找到支持字体：

> 主字体 → 主字体的后备 → 后备的后备 → 通用后备 → 通用后备的后备 → 通用默认 → 通用默认的后备 …

TMP 耗时高的常见原因与解法：

- 动态字体导致耗时高、`SendWillRenderCanvases` 耗时高；
- 解法：**单独给这块开 Canvas**；**静态字体方案**在耗时层面更优。

---

## 十一、UI 中夹 Particle 与 Mesh

UI 与特效混合层级管理的常见方案：

- **UIEffect** 插件
- **Particle Effect For UGUI** 插件
- **UI Particle** 组件（让 UI 中间显示粒子）
  - ⚠️ 该插件按 `ParticleSystem.MaxParticles` 数量初始化数组，**要特别注意 MaxParticles 数量**。
- **Render Texture**
- **World Space Canvas**
- **Screen Space – Camera**
- **多相机**

---

## 十二、适配

### 12.1 刘海屏适配

三种技术方案：

1. 改相机 **ViewPort**；
2. **缩放**；
3. 改**锚点**。

### 12.2 横屏 / 竖屏切换

横屏游戏中个别玩法切到竖屏的实践方案：

- 修改 `Screen.orientation`；
- 同时修改 UI 全局根节点 `CanvasScaler`：
  - **竖屏**：`referenceResolution = (1080, 1920)`，`matchWidthOrHeight = 0`；
  - **横屏**：`referenceResolution = (1920, 1080)`，`matchWidthOrHeight = 1`；
  - `matchWidthOrHeight` 与项目适配策略相关；
- 切换时加一个**全屏遮罩 fade**，避免切换瞬间显示错误。

### 12.3 自适应背景

- **CPU 角度**：分两种——拉伸（图片变形）与不拉伸（图片被裁切）。
- **GPU 角度**：通过**修改采样矩阵**实现背景填充。

---

## 十三、其它战术要点

- **`CanvasRenderer.setColor` / Alpha=0**：Alpha 设为 0 时 DrawCall 和顶点数更少（做了不绘制的特殊处理）。
- **Cull Transparent Mesh**：勾选后，Image 的 Alpha 为 0 时不渲染。
- **Scale = 0 / 1 替代 DeActive/Active**：降低 CPU 消耗。
- **非静态 Canvas**：严格控制其中 UI 元素数量——Canvas 所有元素合并到一个 Mesh，任一元素变化都会引发整个 Mesh 变化。
- **Mesh 多线程合并**：`RuntimeMeshUtility` 性能优于 `ProceduralMeshLibrary`。
- **事件检测优化**：过滤不需检测的 Canvas / Graphic；一个 Item 只需一个 Target 检测。
- **灵活滑动列表动画**：可用 **FancyScrollView** 通用组件。
- **`SendWillRenderCanvases` 高的排查**：画布会重算 UV、重并图集；RectMask2D 持续每帧算子节点裁剪区域。优化思路：降频繁更新 UI 频率、让复杂 UI 不变动、关注 `Font.CacheFontForText`。

---

## 综合优化检查清单

> 需要可直接落地的团队 Code Review 规则集（R1–R6 + ROI 优先级 + 运行时监控阈值），见 [[【片段】UGUI 性能优化规则清单]]。本清单偏全景速查，二者互补。

- [ ] 图集：SpriteAtlas 与 AssetBundle 打包策略一致，无 `sactx` / 小 Sprite 冗余
- [ ] `RawImage` 不引用图集中的 Sprite
- [ ] 高频变动 UI 与静态 UI 分离 Canvas（动静分离）
- [ ] 单个非静态 Canvas 内元素数量受控
- [ ] Mask 数量决策正确（1→RectMask2D，>2→Mask）
- [ ] 滚动列表独立 Canvas、拖动时关 Pixel Perfect
- [ ] 界面软隐藏用 CullingMask，避免 SetActive 抖动
- [ ] `OnEnable/OnDisable` 内无重要逻辑
- [ ] 字体字号种类收敛，粗体提供 `bd` 字面
- [ ] 特效混合时注意 `MaxParticles` 数组初始化
- [ ] 横竖屏切换改 `CanvasScaler` + fade 遮罩

---

## 证据来源

- 外部原文：[Unity性能优化总结-UI（知乎 / DragonL, 2025-08）](https://zhuanlan.zhihu.com/p/1941865546690827415)
- [[【设计原理】UGUI合批机制深度解析]] — Rebuild/Rebatch、合批底层机制
- [[【性能数据】UGUI DrawCall影响因素全面测试]] — DrawCall 影响因子量化
- [[【踩坑记录】UGUI常见性能陷阱与根因分析]] — SendWill / Layout 风暴根因
- [[【最佳实践】TextMeshPro性能优化实战]] — TMP 字体专项

## 相关链接

- [[【片段】UGUI 性能优化规则清单]]
- [[【设计原理】UGUI合批机制深度解析]]
- [[【性能数据】UGUI DrawCall影响因素全面测试]]
- [[【踩坑记录】UGUI常见性能陷阱与根因分析]]
- [[【最佳实践】TextMeshPro性能优化实战]]
- [[【源码解析】Unity事件系统实现机制]]
- [[UI系统专题索引]]
