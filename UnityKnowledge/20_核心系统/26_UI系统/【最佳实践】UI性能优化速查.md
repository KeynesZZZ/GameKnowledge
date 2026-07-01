---
title: 【最佳实践】UI性能优化
tags: ["Unity", "性能优化", "渲染优化", "最佳实践", "UI", "渲染"]
category: 性能优化
created: "2026-03-05 08:44"
updated: "2026-07-01 00:00"
description: UGUI性能优化最佳实践速查——按ROI排序的可落地操作清单
unity_version: 2021.3+
status: 待验证
validation: 部分结论引用26_UI系统系列量化数据
related: ["[[【综述】UGUI性能优化实战总览]]", "[[【片段】UGUI 性能优化规则清单]]", "[[【踩坑记录】UGUI常见性能陷阱与根因分析]]", "[[【设计原理】UGUI合批机制深度解析]]", "[[【性能数据】UGUI DrawCall影响因素全面测试]]", "[[../../32_内存管理/【最佳实践】GC优化清单]]"]
author: llm
sources:
  - "[[【综述】UGUI性能优化实战总览]]"
  - "[[【片段】UGUI 性能优化规则清单]]"
  - "[[【踩坑记录】UGUI常见性能陷阱与根因分析]]"
  - "[[【设计原理】UGUI合批机制深度解析]]"
---

# 【最佳实践】UI性能优化

> UGUI 性能优化速查指南，按 ROI 排序，每条附根因与落地代码。`#性能优化` `#UI` `#最佳实践`

## 文档定位

本文是 UGUI 性能优化的**可落地速查页**，按收益从高到低排列。深度机制与量化数据不在本页展开，而是指向 `20_核心系统/26_UI系统/` 下的专题文档：

| 深度需求 | 目标文档 |
|----------|----------|
| 合批底层机制 | [[【设计原理】UGUI合批机制深度解析]] |
| DrawCall 影响因子量化 | [[【性能数据】UGUI DrawCall影响因素全面测试]] |
| 各陷阱根因与反例代码 | [[【踩坑记录】UGUI常见性能陷阱与根因分析]] |
| 全景综述（图集打包/Mask/适配/特效混合等） | [[【综述】UGUI性能优化实战总览]] |
| 团队 Code Review 规则集 | [[【片段】UGUI 性能优化规则清单]] |

---

## 核心原则

```
UGUI 优化四象限：
├─ CPU — 布局：LayoutGroup 嵌套 / ContentSizeFitter → R1（收益最高）
├─ CPU — 重建：Graphic 每帧赋值 → R2
├─ GPU — DrawCall：合批断裂 → R3
└─ 内存 — GC：滚动期 Instantiate / 字符串拼接 → R5
```

> 经验值：**Layout 优化 + 对象池**两项通常吃掉 60%+ 的 UI 性能问题。

---

## 一、Layout 优化（P0 — 收益最高）

> **根因**：修改 `anchoredPosition` 或嵌套 LayoutGroup 会触发 `MarkParentForRebuild`，沿父级重算整棵布局子树；嵌套层级带来指数级放大。Profiler 中表现为 `LayoutRebuilder.Rebuild` 占比高。

### 1.1 禁止列表项使用 LayoutGroup

列表项排列**必须手动计算**，禁用 LayoutGroup：

```csharp
// ❌ 错误：Content 挂 VerticalLayoutGroup，100 项嵌套 LayoutGroup
// Layout Rebuild 可达 15-30ms

// ✅ 正确：手动布局
public void SetData<T>(IList<T> dataList)
{
    float totalHeight = dataList.Count * (itemHeight + spacing);
    contentRect.sizeDelta = new Vector2(contentRect.sizeDelta.x, totalHeight);

    for (int i = 0; i < dataList.Count; i++)
    {
        var rect = itemPool.Get().GetComponent<RectTransform>();
        rect.anchoredPosition = new Vector2(0, -i * (itemHeight + spacing));
        rect.GetComponent<ItemSlot>().SetData(dataList[i]);
    }
}
```

> 量化参考：手动布局 + 去 ContentSizeFitter 后，Layout 耗时 **45ms → 0.5ms**。

### 1.2 LayoutGroup 嵌套不超过 1 层

```csharp
// ❌ Content → VerticalLayoutGroup → Item → HorizontalLayoutGroup → Inner → VerticalLayoutGroup
// 3 层嵌套，50 个 Item = 150 次 Rebuild，耗时 15ms+

// ✅ Content → VerticalLayoutGroup → Item（子项内部禁用 LayoutGroup）
```

### 1.3 滚动列表禁用 ContentSizeFitter

Content 高度由代码计算，不依赖 ContentSizeFitter 自动撑开：

```csharp
// ❌ Content 上挂 ContentSizeFitter → 每次子项变动触发额外 Rebuild
// ✅ 代码直接设置 sizeDelta
contentRect.sizeDelta = new Vector2(contentRect.sizeDelta.x, totalCount * (itemHeight + spacing));
```

### 1.4 批量增删后一次性触发 Rebuild

```csharp
// ✅ 批量操作后调用一次，而非依赖每帧自动 Rebuild
LayoutRebuilder.ForceRebuildLayoutImmediate(content);
```

### 1.5 禁止在 Update 中修改布局属性

`anchoredPosition` / `sizeDelta` 的修改应通过事件驱动或脏标记，**禁止在 `Update` 中逐帧修改**。动画用 DOTween 或手动插值。

> 深度分析见 [[【踩坑记录】UGUI常见性能陷阱与根因分析]] 坑1。

---

## 二、对象池 + 虚拟列表（P0）

> **根因**：`Instantiate` / `Destroy` 每次分配 5-10KB 内存，滚动列表中每秒可产生数百 KB GC。

### 2.1 数据项 > 20 的列表必须使用虚拟列表

只渲染可见项 + 少量缓冲：

```csharp
public class VirtualScrollList : MonoBehaviour
{
    [SerializeField] private ScrollRect scrollRect;
    [SerializeField] private RectTransform content;
    [SerializeField] private GameObject itemPrefab;

    private readonly List<ItemData> dataList = new();
    private readonly List<RectTransform> activeItems = new();
    private readonly Stack<RectTransform> itemPool = new();

    private float itemHeight = 100f;
    private float spacing = 10f;
    private int lastStartIndex = -1;

    private void Start()
    {
        scrollRect.onValueChanged.AddListener(OnScroll);
        RefreshVisibleItems();
    }

    private void OnScroll(Vector2 _)
    {
        RefreshVisibleItems();
    }

    private void RefreshVisibleItems()
    {
        float step = itemHeight + spacing;
        int visibleCount = Mathf.CeilToInt(scrollRect.viewport.rect.height / step) + 2;
        int startIndex = Mathf.Max(0, Mathf.FloorToInt(-content.anchoredPosition.y / step));

        if (startIndex == lastStartIndex) return;
        lastStartIndex = startIndex;

        // 回收所有活跃项
        foreach (var item in activeItems)
        {
            item.gameObject.SetActive(false);
            itemPool.Push(item);
        }
        activeItems.Clear();

        // 重新创建可见项
        for (int i = 0; i < visibleCount; i++)
        {
            int dataIndex = startIndex + i;
            if (dataIndex < 0 || dataIndex >= dataList.Count) continue;

            var item = GetItemFromPool();
            item.anchoredPosition = new Vector2(0, -dataIndex * step);
            item.GetComponent<ItemSlot>().SetData(dataList[dataIndex]);
            activeItems.Add(item);
        }
    }

    private RectTransform GetItemFromPool()
    {
        if (itemPool.Count > 0)
        {
            var pooled = itemPool.Pop();
            pooled.gameObject.SetActive(true);
            return pooled;
        }

        var go = Instantiate(itemPrefab, content);
        return go.GetComponent<RectTransform>();
    }
}
```

### 2.2 滚动回调零 GC

- 预分配复用对象，禁止在 `onValueChanged` 回调中使用闭包 / lambda 捕获
- 列表项走对象池，禁止滚动时 `Instantiate / Destroy`

> 规则 R5 详见 [[【片段】UGUI 性能优化规则清单]]。

---

## 三、Graphic 优化（P1）

> **根因**：`color` / `fillAmount` / `sprite` / `text` 任一变化都触发 `OnPopulateMesh` 全量重建，每个 Graphic 0.5-2ms。

### 3.1 值变化守卫

所有逐帧 UI 赋值（血条、进度、计时）**必须有值变化守卫**：

```csharp
// ❌ 每帧无条件赋值
void Update()
{
    healthBar.fillAmount = health / maxHealth;
}

// ✅ 仅在值实际变化时触发 Graphic Rebuild
private float lastHealth = -1;

public void UpdateHealth(float newHealth)
{
    if (Mathf.Abs(newHealth - lastHealth) > 0.001f)
    {
        healthBar.fillAmount = Mathf.Clamp01(newHealth / maxHealth);
        lastHealth = newHealth;
    }
}
```

### 3.2 非实时数据限制更新频率

```csharp
// 分数、时间等非实时数据更新频率限制 ≤ 10Hz
private float lastUpdateTime;

void Update()
{
    if (Time.time - lastUpdateTime > 0.1f)
    {
        scoreText.SetText("Score: {0}", score);
        lastUpdateTime = Time.time;
    }
}
```

### 3.3 Outline / Shadow 组件开销

`Outline` 组件会将顶点数扩大 **5 倍**（原顶点 + 上下左右各偏移一份），`Shadow` 扩大 **2 倍**。在列表项中批量使用时是性能杀手。

```csharp
// ❌ 100 个 Item 各挂 Outline → 顶点数从 400 涨到 2000
// ✅ 替代方案：
// 1. 美术直接在图片中绘制描边效果
// 2. 使用 TextMeshPro 的描边功能（SDF 着色器，不增加顶点数）
// 3. 必须用 Outline 时，控制在静态 UI 上，避免出现在列表项中
```

### 3.4 TMP 零 GC 赋值

```csharp
// ❌ 字符串拼接产生 GC
scoreText.text = $"Score: {score}  Time: {Time.time:F2}";

// ✅ SetText 内部复用缓冲，零分配
scoreText.SetText("Score: {0}  Time: {1:F2}", score, Time.time);
```

> 新建 UI 文本统一使用 `TextMeshProUGUI`，禁用旧 `Text`。

---

## 四、DrawCall 合批优化（P1）

> **根因**：合批成立需同时满足「同 Canvas、同 Material、同 Texture、同 Shader Pass、同 Stencil、渲染顺序连续」，任一断裂即新增 DrawCall。

### 4.1 合批条件速查

| 条件 | 说明 |
|------|------|
| **相同材质** | 使用相同 Shader 和纹理（同一图集） |
| **相同层级** | Canvas 下的渲染顺序连续，无穿插 |
| **无遮挡打断** | 中间不能穿插不同材质的元素 |
| **同 Stencil 状态** | Mask 会改变 Stencil，Mask 内外不能合批 |

### 4.2 关键规则：sharedMaterial vs material

```csharp
// ❌ 访问 .material 会触发材质实例化，永久打断合批
Image1.material.SetColor("_Color", Color.red);

// ✅ 使用 .sharedMaterial 或 MaterialPropertyBlock
Image1.SetPropertyBlock(materialPropertyBlock);
// 或在需要独立材质时，显式创建实例并管理生命周期
```

### 4.3 合批打断常见因素

```csharp
// ❌ 以下操作会打断合批：

// 1. 不同图集的图片穿插排列
Image1 → Text1 → Image2(from另一图集)  // Image1 和 Image2 无法合批

// 2. 访问 .material 导致材质实例化
GetComponent<Image>().material.color = Color.red;  // 永久打断！

// 3. 不同字体（旧 Text 组件）
Text1.font = fontA;
Text2.font = fontB;

// 4. Mask 嵌套（改变 Stencil 层级）
Mask → Mask → Image  // 双重 Stencil，隐式拆批
```

### 4.4 优化措施

- 同一界面的 UI 图**打到同一图集**；文字 atlas 与图形 atlas 分开
- Image 与 Text 在层级中**分组排列**（同类相邻），禁止交错
- 每个界面 DrawCall 目标 **≤ 30**（移动端基准）

> 合批底层机制详见 [[【设计原理】UGUI合批机制深度解析]]，量化数据见 [[【性能数据】UGUI DrawCall影响因素全面测试]]。

---

## 五、Canvas 动静分离（P2）

> **根因**：Canvas 既是渲染单元也是重建单元——子树任一元素变脏，整个 Canvas 都要重新 BuildBatch。"动静分离"主要优化 `Canvas.BuildBatch`，**优化不了 `Canvas.SendWillRenderCanvases`**。

### 5.1 按更新频率拆分

```
Canvas (主Canvas)
├── StaticCanvas      // 静态元素，不重建（背景、装饰、固定文字）
├── DynamicCanvas     // 动态元素，频繁重建（血条、分数、计时器）
└── PopupCanvas       // 弹窗，按需启用
```

```csharp
// 原则：静态 / 常驻动态 / 弹窗至少三层
// ⚠️ 禁止为每个 UI 元素单独挂 Canvas（100 元素 100 Canvas = 100 DrawCall）
// ⚠️ 频繁变化元素（血条、倒计时、滚动 Content）必须独立到子 Canvas
```

### 5.2 Rebuild 与 Rebatch 双阶段

| 阶段 | 单位 | 触发 | Profiler 标记 |
|------|------|------|---------------|
| **Rebuild** | UI 元素 | 顶点属性变化（Color、Size 等） | `Canvas.SendWillRenderCanvases` |
| **Rebatch** | Canvas | Canvas 内任意元素变化（含位置） | `Canvas.BuildBatch` + 子线程 `Canvas.SortJob` |

定位技巧：Profiler 选中 `Canvas.BuildBatch`，右侧对象列表即当前帧发生 Rebatch 的 Canvas 名。

### 5.3 Canvas 重建的脏标记模式

```csharp
// ❌ 每帧更新文字
void Update()
{
    scoreText.text = score.ToString();  // 每帧重建！
}

// ✅ 脏标记
private int lastScore = int.MinValue;

void Update()
{
    if (score != lastScore)
    {
        scoreText.SetText("Score: {0}", score);
        lastScore = score;
    }
}
```

---

## 六、Mask 选型（P2）

> 多数资料只说"RectMask2D 省 DrawCall"，但**到底用哪个取决于界面里 Mask 的数量**。

| 界面 Mask 数量 | 推荐 | 原因 |
|----------------|------|------|
| **1 个** | RectMask2D | 不增加额外 DrawCall，CPU 每帧算裁剪区域 |
| **2 个** | 差不多 | — |
| **> 2 个** | Mask | Mask 间首尾 DrawCall 可合批，RectMask2D 之间不可合批 |

补充说明：
- **RectMask2D**：不依赖 Image 组件，多个 RectMask2D 之间不能合批，子节点多时持续开销较高
- **Mask**：依赖 Image 组件，首尾各多 2 个 DrawCall，但多个 Mask 间可合批
- **禁止 Mask 嵌套**（改变 Stencil → 隐式拆批）
- 减少 Mask 的真正原因是 GPU Overdraw 与额外 DrawCall，需与 RectMask2D 的 CPU 持续裁剪计算权衡

> 详细合批性质分析见 [[【综述】UGUI性能优化实战总览]] §七。

---

## 七、隐藏 UI 的正确方式（P2）

| 手法 | 优点 | 注意 |
|------|------|------|
| `SetActive(false)` | 彻底停渲染与逻辑 | 切换有 GC（`OnEnable/OnDisable` 回调），Instantiate/Destroy 开销大 |
| 改 Canvas Layer + CullingMask | 切换零开销、无多余 DrawCall | Mesh 常驻内存、需屏蔽事件 |
| `transform.localScale = 0` | 降 CPU 消耗 | 仍参与 Rebuild 排序判断，非完全剔除 |
| `CanvasRenderer` Alpha=0 | DrawCall 与顶点更少 | 配合 `Cull Transparent Mesh` 使用 |

```csharp
// 推荐的界面软隐藏方案（零开销、无多余 DrawCall）
public void HideUICanvas(Canvas canvas)
{
    // 将 Canvas 的 Layer 改为相机 Culling Mask 未选中的 Layer
    canvas.gameObject.layer = LayerMask.NameToLayer("HiddenUI");
}

public void ShowUICanvas(Canvas canvas)
{
    canvas.gameObject.layer = LayerMask.NameToLayer("UI");
}
```

> ⚠️ **禁忌：不要在 `OnEnable` / `OnDisable` 里写重要逻辑**，否则 SetActive 切换产生大量 GC 与逻辑消耗。

---

## 八、滚动列表专项（P2）

### 滚动列表卡顿排查

| Profiler 瓶颈 | 原因 | 处理 |
|---------------|------|------|
| `OnTransformChanged` → `OnDimensionChanged` 高 | 开了 Pixel Perfect | **拖动时暂时关闭 Pixel Perfect** |
| `Canvas.BuildBatch` 高 | 元素数量大 | 滚动部分**独立成 Canvas**，缩小 BuildBatch 范围 |
| `SendWillRenderCanvases` 高 | 每帧改 Image.color 等 | 改属性本质是改顶点色，引起网格 Rebuild |

### Pixel Perfect

- 滚动列表**不要开 Pixel Perfect**，避免 `SendWillRenderCanvases()` 与 `BuildBatch` 频繁触发
- 静态 UI 可以开，但要测量开销

---

## 九、事件系统优化（P2）

### Raycast Target

```csharp
// ✅ 非交互 Graphic 一律关闭 Raycast Target 和 Maskable
// 在 Prefab 编辑器中取消勾选，或批量处理：
public class RaycastTargetOptimizer : MonoBehaviour
{
    [ContextMenu("禁用所有非交互 Graphic 的 Raycast Target")]
    public void DisableNonInteractiveRaycastTargets()
    {
        var graphics = GetComponentsInChildren<Graphic>(true);
        foreach (var graphic in graphics)
        {
            if (!graphic.TryGetComponent<IPointerClickHandler>(out _) &&
                !graphic.TryGetComponent<IDragHandler>(out _))
            {
                graphic.raycastTarget = false;
            }
        }
    }
}
```

### 弹窗交互隔离

```csharp
// 弹窗显示时，禁用背景 UI 的 GraphicRaycaster
public class UIManager : MonoBehaviour
{
    [SerializeField] private GraphicRaycaster backgroundRaycaster;

    public void ShowPopup(GameObject popup)
    {
        backgroundRaycaster.enabled = false;
        popup.SetActive(true);
    }

    public void HidePopup(GameObject popup)
    {
        backgroundRaycaster.enabled = true;
        popup.SetActive(false);
    }
}
```

---

## 十、图集优化（P2）

### Sprite Atlas 配置建议

```
// 移动端推荐配置：
- Max Size: 1024（功能内）/ 2048（通用常驻）
- Format: ASTC 6x6（移动端首选，平衡质量与大小）
- Read/Write: false（除非需要运行时修改）
- Allow Rotation: false（UI 不建议旋转）
- Include in Build: 根据打包策略决定
```

### 图集尺寸策略

| 图集用途 | 建议尺寸 | 说明 |
|----------|----------|------|
| 常驻通用资源 | 2048 甚至 4096 | 一张，减少加载次数 |
| 单个功能独有图集 | ≤ 1024 | 达到 3 张 1024 时可升 2048 |

> 权衡逻辑：分配合理时，多一张贴图只多 1 个 DrawCall；强行合并到 2048 可能空白多、内存反而浪费。

### 注意事项

- **RawImage 不要引用图集中的 Sprite**——会导致该图额外打包一份，包体增大
- 大图（背景等）使用单独加载，**避免打包到 UI 图集中**
- 使用九宫格（Sliced）减少图片尺寸

> SpriteAtlas 与 AssetBundle 打包的冗余规则详见 [[【综述】UGUI性能优化实战总览]] §一。

---

## 十一、内存优化（P3）

### UI 对象池

```csharp
public class UIPool : MonoBehaviour
{
    [SerializeField] private GameObject prefab;
    private readonly Queue<GameObject> pool = new();

    public GameObject Get(Transform parent)
    {
        if (pool.TryDequeue(out var go))
        {
            go.transform.SetParent(parent, false);
            go.SetActive(true);
            return go;
        }
        return Instantiate(prefab, parent);
    }

    public void Release(GameObject go)
    {
        go.SetActive(false);
        go.transform.SetParent(transform);
        pool.Enqueue(go);
    }

    public void Clear()
    {
        while (pool.Count > 0)
            Destroy(pool.Dequeue());
    }
}
```

### 资源管理要点

- UI 预制体、常用图标在启动 / 场景加载时**异步预加载**，禁止运行时同步 `Resources.Load`
- 界面关闭后**释放其专属大纹理**；图集共享纹理不释放

> GC 优化详见 [[../../32_内存管理/【最佳实践】GC优化清单]]。

---

## 十二、性能检测

### Profiler 关键指标

```
Window > Analysis > Profiler > UI 模块

重点关注：
├─ Canvas.BuildBatch          — Rebatch 耗时（高 → 拆分 Canvas）
├─ Canvas.SendWillRenderCanvases — Rebuild 耗时（高 → 减少逐帧赋值）
└─ Canvas.RenderOverlays      — 渲染提交耗时
```

### Frame Debugger

```
Window > Analysis > Frame Debugger

观察：
├─ UI DrawCall 数量（目标 ≤ 30 移动端）
├─ 每个 Canvas 的渲染情况
└─ 合批断点位置（定位材质/纹理切换点）
```

### 运行时监控阈值（开发构建常驻）

| 指标 | 阈值 | 触发后的排查方向 |
|------|------|----------------|
| DrawCalls | > 30 | 合批被打断（图集 / 材质实例化 / 层级穿插 / Mask） |
| Layout Rebuild 次数/帧 | > 10 | LayoutGroup 滥用 / Update 改 anchoredPosition |
| Graphic Rebuild 次数/帧 | > 100 | 逐帧赋值 / 缺值变化守卫 |
| GC.Alloc / 帧 | > 1 KB | 滚动期 Instantiate / 字符串拼接 |
| Frame Time | > 16.67 ms | 综合定位，按上述四类逐项排查 |

---

## 优化检查清单

### P0 — Layout（收益最高）

- [ ] 列表项无 LayoutGroup，手动算 anchoredPosition
- [ ] LayoutGroup 嵌套 ≤ 1 层
- [ ] 滚动列表无 ContentSizeFitter
- [ ] 批量增删用 `ForceRebuildLayoutImmediate` 一次性触发
- [ ] Update 内无 `anchoredPosition` / `sizeDelta` 修改

### P0 — 列表 / 滚动

- [ ] > 20 项使用虚拟列表
- [ ] 列表项走对象池，禁止滚动时 Instantiate / Destroy
- [ ] 滚动回调零 GC

### P1 — Graphic

- [ ] 逐帧赋值有值变化守卫
- [ ] 非实时数据更新 ≤ 10Hz
- [ ] 新文本用 TextMeshProUGUI，TMP 用 `SetText`
- [ ] 列表项中无 Outline / Shadow（或用 TMP 描边替代）

### P1 — 合批

- [ ] 代码未访问 `.material`，用 `sharedMaterial`
- [ ] 同界面 UI 在同一图集
- [ ] Image / Text 分组排列，无交错
- [ ] 无 Mask 嵌套，Mask 数量决策正确（1→RectMask2D，>2→Mask）
- [ ] DrawCall ≤ 30

### P2 — Canvas

- [ ] 按变化频率拆分静态 / 动态 / 弹窗 Canvas
- [ ] 无逐元素独立 Canvas
- [ ] 频繁变化元素独立子 Canvas
- [ ] 滚动列表关闭 Pixel Perfect

### P2 — 隐藏与交互

- [ ] 软隐藏用 CullingMask，避免 SetActive 抖动
- [ ] `OnEnable` / `OnDisable` 内无重要逻辑
- [ ] 非交互 Graphic 关闭 Raycast Target / Maskable
- [ ] 弹窗显示时禁用背景 GraphicRaycaster

### P3 — 资源

- [ ] 常用资源异步预加载，无同步 Load
- [ ] 界面关闭释放专属大纹理
- [ ] RawImage 不引用图集中的 Sprite
- [ ] UI 预制体走对象池复用

---

## 相关链接

### 深度文档（20_核心系统/26_UI系统/）

- [[【综述】UGUI性能优化实战总览]] — 全景速查（图集打包/Mask/适配/特效混合等）
- [[【片段】UGUI 性能优化规则清单]] — 团队 Code Review 规则集（R1-R6 + ROI + 监控阈值）
- [[【踩坑记录】UGUI常见性能陷阱与根因分析]] — 各陷阱根因与反例代码
- [[【设计原理】UGUI合批机制深度解析]] — Rebuild/Rebatch、合批底层机制
- [[【性能数据】UGUI DrawCall影响因素全面测试]] — DrawCall 影响因子量化数据
- [[UI系统专题索引]]

### 关联优化

- [[../../32_内存管理/【最佳实践】GC优化清单]] — GC 优化清单
