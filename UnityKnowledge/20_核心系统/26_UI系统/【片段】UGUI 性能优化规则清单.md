---
title: 【片段】UGUI 性能优化规则清单
tags: ["Unity", "UI", "UI系统", "UGUI", "性能优化", "规则清单", "片段", "合批", "Checklist"]
category: 核心系统/UI系统
created: "2026-06-25 10:00"
updated: "2026-06-25 10:00"
description: 可直接作为团队 Code Review 标准的 UGUI 性能优化规则集（R1-R6），覆盖 Layout、Graphic、合批、Canvas、列表、资源六个维度，附 ROI 优先级与运行时监控阈值。
unity_version: 2021.3+
status: 待验证
validation: 未经测试
related: ["[[【踩坑记录】UGUI常见性能陷阱与根因分析]]", "[[【设计原理】UGUI合批机制深度解析]]", "[[【实战案例】UI卡顿优化全流程]]", "[[【性能数据】UGUI DrawCall影响因素全面测试]]", "[[【最佳实践】TextMeshPro性能优化实战]]", "[[UI系统专题索引]]"]
author: llm
sources:
  - "[[【踩坑记录】UGUI常见性能陷阱与根因分析]]"
  - "[[【实战案例】UI卡顿优化全流程]]"
  - "[[【设计原理】UGUI合批机制深度解析]]"
  - "[[UGUI/第4章 UI 更新与重建系统]]"
  - "[[UGUI/第7章 CanvasRenderer 机制]]"
---

# 【片段】UGUI 性能优化规则清单

> UGUI 性能优化的团队规范与 Code Review 清单 `#片段` `#规则清单` `#性能优化` `#UGUI`

## 文档定位

本文档将 UGUI 性能优化经验提炼为一套**可执行规则（R1–R6）**，按 Layout、Graphic、合批、Canvas、列表、资源六个维度组织，每条规则标注根因与代价。可作为：

- **Code Review 检查项**：逐条对照，违反即打回
- **新成员上手清单**：理解「为什么」而不只是「怎么做」
- **问题排查索引**：按瓶颈类型反查规则

**核心方法论**：先测量后优化，按瓶颈类型（CPU-布局 / CPU-重建 / GPU-DrawCall / 内存-GC）对症下药，一次只改一个变量。

**相关文档**：[[【踩坑记录】UGUI常见性能陷阱与根因分析]]、[[【实战案例】UI卡顿优化全流程]]、[[【设计原理】UGUI合批机制深度解析]]、[[【性能数据】UGUI DrawCall影响因素全面测试]]、[[【最佳实践】TextMeshPro性能优化实战]]

---

## 一、瓶颈分类与定位（先诊断，再开方）

| 瓶颈类型 | 典型现象 | 定位工具 | 根因 |
|---------|---------|---------|------|
| **CPU - 布局** | `LayoutRebuilder.Rebuild` 占比高 | CPU Profiler | LayoutGroup 嵌套 / 频发 |
| **CPU - 重建** | `Graphic.Rebuild` / `OnPopulateMesh` 高 | CPU Profiler | 每帧改 Image/Text |
| **GPU - DrawCall** | DrawCall 高、GPU 耗时高 | Frame Debugger | 合批被打断 |
| **内存 - GC** | `GC.Alloc` 抖动、卡顿尖峰 | Memory Profiler | 滚动期 Instantiate/拼接 |

---

## 二、规则集（R1–R6）

### R1 — Layout 规则（收益最高）

> 根因：修改 `anchoredPosition` 或嵌套 LayoutGroup 会触发 `MarkParentForRebuild`，沿父级重算整棵布局子树；嵌套层级带来指数级放大。

- **R1.1** 列表项排列**禁止使用 LayoutGroup**，必须手动计算 `anchoredPosition = new Vector2(0, -i * (itemHeight + spacing))`。
- **R1.2** LayoutGroup 嵌套**不得超过 1 层**；Content 下直接挂 Horizontal/Vertical，子项内部禁止再套 LayoutGroup。
- **R1.3** 滚动列表**禁用 `ContentSizeFitter`**；Content 高度由代码 `sizeDelta` 计算。
- **R1.4** 批量增删子项后，调用**一次** `LayoutRebuilder.ForceRebuildLayoutImmediate(content)`，禁止依赖每帧自动 Rebuild。
- **R1.5** **禁止在 `Update` 中修改** `anchoredPosition` / `sizeDelta`；动画用 DOTween 或手动脏标记驱动。

> 量化参考（来自实战）：手动布局 + 去 ContentSizeFitter 后，Layout 耗时 **45ms → 0.5ms**。

### R2 — Graphic 规则

> 根因：`color` / `fillAmount` / `sprite` / `text` 任一变化都触发 `OnPopulateMesh` 全量重建，每个 Graphic 0.5–2ms。

- **R2.1** 所有逐帧 UI 赋值（血条、进度、计时）**必须有「值变化守卫」**：`if (Mathf.Abs(newVal - lastVal) > 0.001f)`。
- **R2.2** 非实时数据（分数、时间）**更新频率限制 ≤ 10Hz**。
- **R2.3** 新建 UI 文本**统一使用 `TextMeshProUGUI`**，禁用旧 `Text`。
- **R2.4** TMP 赋值用 `SetText("Score: {0}", score)`，**禁止字符串拼接**（`$"{a}"` / `+`）。

### R3 — 合批 / DrawCall 规则

> 根因：合批成立需同时满足「同 Canvas、同 Material、同 Texture、同 Shader Pass、同 Stencil、渲染顺序连续」，任一断裂即新增 DrawCall。

- **R3.1** 代码中**禁止访问 `.material`**（会触发 Material 实例化打断合批），必须用 `.sharedMaterial`；需运行时改属性时用 `MaterialPropertyBlock` 或独立材质实例。
- **R3.2** 同一界面的 UI 图**必须打到同一图集**；文字 atlas 与图形 atlas 分开。
- **R3.3** Image 与 Text 在层级中**分组排列**（同类相邻），禁止交错导致材质反复切换。
- **R3.4** 优先 `RectMask2D`；仅在需任意形状镂空时用 `Mask`；**禁止 Mask 嵌套**（改变 Stencil → 隐式拆批）。
- **R3.5** 每个界面 DrawCall 目标 **≤ 30**（移动端基准），超出需在 Frame Debugger 定位断批点。

### R4 — Canvas 规则

> 根因：Canvas 既是渲染单元也是重建单元——子树任一元素变脏，整个 Canvas 都要重新 BuildBatch。

- **R4.1** 按「变化频率」**拆 Canvas**：静态背景 / 常驻动态 / 弹窗至少三层，隔离 BuildBatch 影响范围。
- **R4.2** **禁止为每个 UI 元素单独挂 Canvas**（100 元素 100 Canvas = 100 DrawCall）；弹窗用 Canvas 对象池复用。
- **R4.3** 频繁变化元素（血条、倒计时、滚动 Content）**必须独立到子 Canvas**。

### R5 — 列表 / 滚动规则

- **R5.1** 数据项 **> 20 的列表必须使用虚拟列表**（只渲染可见项 + 缓冲：`visibleCount = CeilToInt(viewportHeight / itemHeight) + 2`）。
- **R5.2** 列表项**必须走对象池**，禁止滚动时 `Instantiate / Destroy`。
- **R5.3** 滚动回调**零 GC**：预分配复用对象，禁止闭包 / lambda 捕获分配。

### R6 — 资源 / 内存规则

- **R6.1** UI 预制体、常用图标在启动 / 场景加载时**异步预加载**（`Resources.LoadAsync`），禁止运行时同步 `Resources.Load` 阻塞主线程。
- **R6.2** 界面关闭后**释放其专属大纹理**；图集共享纹理不释放。
- **R6.3** **非交互 Graphic 一律关闭 `Raycast Target` 与 `Maskable`**，降低射线检测与重建开销。

---

## 三、优先级 / ROI 排序

> 经验值：**Layout 优化 + 对象池**两项通常吃掉 60%+ 的 UI 性能问题，先做这两项再谈其他。

| 优先级 | 措施 | 实施难度 | 收益 | 适用场景 |
|--------|------|---------|------|---------|
| **P0** | 列表手动布局 + 去 ContentSizeFitter | 中 | 极高 | 任何含列表的项目 |
| **P0** | UI 对象池 + 虚拟列表 | 中 | 极高 | 滚动列表 |
| **P1** | `sharedMaterial` 规范 + 图集合并 | 低 | 高 | 全项目 |
| **P1** | TMP 替换 + `SetText` | 低 | 高 | 全项目 |
| **P2** | 按频率拆 Canvas | 中 | 中 | 复杂界面 |
| **P2** | 关闭非交互元素 Raycast Target | 低 | 中 | 全项目 |
| **P3** | 资源异步预加载 | 低 | 中 | 启动期卡顿 |

---

## 四、运行时监控阈值（开发构建常驻）

> 参考 `UIPerformanceMonitor` 思路，超阈值即 `LogWarning`，把规则变成会主动报警的红线。

| 指标 | 阈值 | 触发后的排查方向 |
|------|------|----------------|
| `UnityStats.drawCalls` | **> 30** | R3：合批被打断（图集 / 材质实例化 / 层级穿插 / Mask） |
| Layout Rebuild 次数/帧 | **> 10** | R1：LayoutGroup 滥用 / Update 改 anchoredPosition |
| Graphic Rebuild 次数/帧 | **> 100** | R2：逐帧赋值 / 缺值变化守卫 |
| `GC.Alloc` / 帧 | **> 1 KB** | R5：滚动期 Instantiate / 字符串拼接 |
| Frame Time | **> 16.67 ms** | 综合定位，按上述四类逐项排查 |

---

## 五、Code Review 速查清单

```markdown
## UI 性能 Code Review 清单

### Layout（R1）
- [ ] 列表项无 LayoutGroup，手动算 anchoredPosition（R1.1）
- [ ] LayoutGroup 嵌套 ≤ 1 层（R1.2）
- [ ] 滚动列表无 ContentSizeFitter（R1.3）
- [ ] 批量增删用 ForceRebuildLayoutImmediate 一次性触发（R1.4）
- [ ] Update 内无 anchoredPosition / sizeDelta 修改（R1.5）

### Graphic（R2）
- [ ] 逐帧赋值有值变化守卫（R2.1）
- [ ] 非实时数据更新 ≤ 10Hz（R2.2）
- [ ] 新文本用 TextMeshProUGUI（R2.3）
- [ ] TMP 用 SetText，无字符串拼接（R2.4）

### 合批（R3）
- [ ] 代码未访问 .material，用 sharedMaterial（R3.1）
- [ ] 同界面 UI 在同一图集（R3.2）
- [ ] Image/Text 分组排列，无交错（R3.3）
- [ ] 无 Mask 嵌套，优先 RectMask2D（R3.4）
- [ ] DrawCall ≤ 30（R3.5）

### Canvas（R4）
- [ ] 按变化频率拆分静态/动态/弹窗 Canvas（R4.1）
- [ ] 无逐元素独立 Canvas（R4.2）
- [ ] 频繁变化元素独立子 Canvas（R4.3）

### 列表（R5）
- [ ] >20 项使用虚拟列表（R5.1）
- [ ] 列表项走对象池（R5.2）
- [ ] 滚动回调零 GC（R5.3）

### 资源（R6）
- [ ] 常用资源异步预加载，无同步 Load（R6.1）
- [ ] 界面关闭释放专属大纹理（R6.2）
- [ ] 非交互 Graphic 关闭 Raycast Target / Maskable（R6.3）
```

---

## 六、配套代码片段

### 值变化守卫（R2.1）

```csharp
public void UpdateHealth(float newHealth)
{
    // ✅ 仅在值实际变化时才触发 Graphic Rebuild
    if (Mathf.Abs(newHealth - lastHealth) > 0.001f)
    {
        healthBar.fillAmount = Mathf.Clamp01(newHealth / maxHealth);
        lastHealth = newHealth;
    }
}
```

### 手动布局列表（R1.1 / R1.3）

```csharp
public void SetData(IList<ItemData> dataList)
{
    // ✅ 直接设置 Content 高度，不用 ContentSizeFitter
    float totalHeight = dataList.Count * (itemHeight + spacing);
    contentRect.sizeDelta = new Vector2(contentRect.sizeDelta.x, totalHeight);

    // ✅ 固定位置布局，无需 LayoutGroup
    for (int i = 0; i < dataList.Count; i++)
    {
        var rect = itemPool.Get().GetComponent<RectTransform>();
        float yPos = -i * (itemHeight + spacing);
        rect.anchoredPosition = new Vector2(0, yPos);
        rect.sizeDelta = new Vector2(contentRect.rect.width, itemHeight);
        rect.GetComponent<ItemSlot>().SetData(dataList[i]);
    }
}
```

### 零 GC TMP 赋值（R2.4）

```csharp
// ✅ SetText 内部复用缓冲，无字符串分配
scoreText.SetText("Score: {0}  Time: {1:F2}", score, Time.time);
```

---

## 相关链接

- [[【踩坑记录】UGUI常见性能陷阱与根因分析]] — 各规则的根因与反例代码
- [[【实战案例】UI卡顿优化全流程]] — 完整案例：650ms→35ms、28fps→60fps、127→18 DrawCall
- [[【设计原理】UGUI合批机制深度解析]] — R3 合批条件的底层依据
- [[【性能数据】UGUI DrawCall影响因素全面测试]] — DrawCall 影响因素量化数据
- [[【最佳实践】TextMeshPro性能优化实战]] — R2.3/R2.4 的深入实践
- [[UI系统专题索引]]

---

*创建日期: 2026-06-25*
*Unity版本: 2021.3 LTS*
