---
title: 【最佳实践】UI性能优化
tags: [Unity, 性能优化, 渲染优化, 最佳实践]
category: 性能优化
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: Unity UI性能优化最佳实践
unity_version: 2021.3+
---
# 最佳实践 - UI性能优化

> UGUI性能优化完整指南 `#性能优化` `#渲染` `#UI` `#最佳实践`

## 快速参考

```csharp
// UI优化核心原则
1. 减少DrawCall（合批）
2. 避免UI重建（脏标记）
3. 优化事件系统
4. 合理使用图集
```

---

## DrawCall优化

### 合批条件

UGUI合批需要满足以下条件：

| 条件 | 说明 |
|------|------|
| **相同材质** | 使用相同Shader和纹理 |
| **相同图集** | 图片来自同一Sprite Atlas |
| **相同层级** | Canvas下的渲染顺序连续 |
| **无遮挡** | 中间不能穿插不同材质的元素 |

### 合批打断因素

```csharp
// ❌ 这些会打断合批：

// 1. 不同图集的图片
Image1.sprite = spriteFromAtlasA;
Image2.sprite = spriteFromAtlasB;  // 打断！

// 2. 使用了不同材质
Image1.material = null;  // 默认
Image2.material = customMaterial;  // 打断！

// 3. 文字（使用不同字体）
Text1.font = fontA;
Text2.font = fontB;  // 打断！

// 4. 遮罩组件
Mask mask;  // 会增加DrawCall

// 5. RectMask2D
RectMask2D rectMask;  // 裁剪区域不同会打断
```

### 优化方案

```csharp
// ✅ 优化：使用图集
// 1. 创建Sprite Atlas
// 2. 将UI元素打包到同一图集
// 3. 确保连续排列

// ✅ 优化：TextMeshPro共享材质
// 使用同一个字体图集

// ✅ 优化：减少层级穿插
// 将相同类型元素放在一起
```

---

## Canvas优化

### Canvas拆分策略

```csharp
// 原则：按更新频率拆分Canvas

// 1. 静态UI - 很少更新
//    - 背景图片
//    - 装饰元素
//    - 固定文字

// 2. 动态UI - 频繁更新
//    - 血条
//    - 分数
//    - 计时器

// 3. 弹窗UI - 按需启用/禁用
//    - 对话框
//    - 菜单

// 示例结构
Canvas (主Canvas)
├── StaticCanvas      // 静态元素，不重建
│   ├── Background
│   └── Decorations
├── DynamicCanvas     // 动态元素，频繁重建
│   ├── HealthBars
│   └── ScoreText
└── PopupCanvas       // 弹窗，按需启用
    └── Dialogs
```

### Canvas重建优化

```csharp
// UI重建触发条件：
// 1. 改变Text内容
// 2. 改变Image的Sprite
// 3. 改变RectTransform大小
// 4. 启用/禁用UI元素

// ❌ 错误：每帧更新
void Update()
{
    scoreText.text = score.ToString();  // 每帧重建！
}

// ✅ 正确：脏标记
private int lastScore = -1;
private int currentScore;

void Update()
{
    if (currentScore != lastScore)
    {
        scoreText.text = currentScore.ToString();
        lastScore = currentScore;
    }
}

// ✅ 更好：使用TextMeshPro
// TMP的重建开销更小
```

---

## 事件系统优化

### GraphicRaycaster优化

```csharp
// ❌ 问题：大量可点击元素
// 每次点击都要遍历所有Raycast Target

// ✅ 优化1：禁用不必要的Raycast Target
// 对于不需要交互的UI元素，取消勾选Raycast Target

// ✅ 优化2：使用Raycast Target层级
public class UIRaycastOptimizer : MonoBehaviour
{
    [SerializeField] private GraphicRaycaster raycaster;

    // 在不需要交互时禁用
    public void DisableInteraction()
    {
        raycaster.enabled = false;
    }

    public void EnableInteraction()
    {
        raycaster.enabled = true;
    }
}

// ✅ 优化3：减少EventSystem的检测频率
// 对于不需要即时响应的UI
```

### 避免不必要的EventSystem更新

```csharp
// 在弹窗显示时，禁用背景UI的交互
public class UIManager : MonoBehaviour
{
    [SerializeField] private GraphicRaycaster backgroundRaycaster;
    [SerializeField] private GraphicRaycaster popupRaycaster;

    public void ShowPopup()
    {
        backgroundRaycaster.enabled = false;
        popupRaycaster.enabled = true;
    }

    public void HidePopup()
    {
        backgroundRaycaster.enabled = true;
        popupRaycaster.enabled = false;
    }
}
```

---

## 图集优化

### Sprite Atlas配置

```csharp
// 1. 创建Sprite Atlas
// Assets > Create > Sprite Atlas

// 2. 配置建议
// - Max Size: 2048 (移动端)
// - Format: RGBA 32 bit 或 ASTC 6x6
// - Include in Build: true
// - Allow Rotation: false (UI不建议旋转)

// 3. 运行时加载
public class AtlasLoader : MonoBehaviour
{
    [SerializeField] private SpriteAtlas uiAtlas;

    public Sprite GetSprite(string name)
    {
        return uiAtlas.GetSprite(name);
    }
}
```

### 动态图集

```csharp
// 对于动态加载的图片，使用动态图集
// 或手动管理图集

public class DynamicAtlas : MonoBehaviour
{
    private Dictionary<string, Sprite> spriteCache = new();

    public async UniTask<Sprite> LoadSpriteAsync(string path)
    {
        if (spriteCache.TryGetValue(path, out var cached))
        {
            return cached;
        }

        var sprite = await LoadFromAddressables(path);
        spriteCache[path] = sprite;
        return sprite;
    }

    public void ClearCache()
    {
        spriteCache.Clear();
    }
}
```

---

## 内存优化

### UI资源管理

```csharp
public class UIResourceManager : MonoBehaviour
{
    // 缓存常用UI组件
    private Dictionary<string, GameObject> uiPrefabs = new();

    // 对象池
    private Dictionary<string, Queue<GameObject>> uiPools = new();

    public GameObject GetUI(string name)
    {
        // 先从池中获取
        if (uiPools.TryGetValue(name, out var pool) && pool.Count > 0)
        {
            var go = pool.Dequeue();
            go.SetActive(true);
            return go;
        }

        // 池中没有则实例化
        if (uiPrefabs.TryGetValue(name, out var prefab))
        {
            return Instantiate(prefab);
        }

        return null;
    }

    public void ReturnUI(string name, GameObject go)
    {
        go.SetActive(false);
        go.transform.SetParent(transform);

        if (!uiPools.ContainsKey(name))
        {
            uiPools[name] = new Queue<GameObject>();
        }
        uiPools[name].Enqueue(go);
    }
}
```

### 大图优化

```csharp
// 对于大图（背景等），使用单独图集或直接加载
// 避免打包到UI图集中

// 使用九宫格减少图片大小
// 设置 Border 属性

// 对于装饰性大图，考虑使用：
// 1. 压缩格式 (ASTC)
// 2. 降低分辨率
// 3. 使用Mesh + Material替代
```

---

## 文字优化

### TextMeshPro vs Text

| 特性 | Text (UGUI) | TextMeshPro |
|------|-------------|-------------|
| 渲染质量 | 一般 | **优秀** |
| 内存占用 | 高 | **低** |
| 合批支持 | 有 | **更好** |
| 功能 | 基础 | **丰富** |
| 性能 | 一般 | **更好** |

### 文字优化建议

```csharp
// ✅ 使用TextMeshPro
// 1. 更好的渲染质量
// 2. 更少的DrawCall
// 3. 支持更多样式

// ✅ 缓存文字组件
private TextMeshProUGUI cachedText;

// ✅ 避免频繁更新
private string lastText;
private StringBuilder sb = new();

void UpdateText(int score)
{
    sb.Clear();
    sb.Append("Score: ");
    sb.Append(score);
    string newText = sb.ToString();

    if (newText != lastText)
    {
        cachedText.text = newText;
        lastText = newText;
    }
}
```

---

## 滚动视图优化

### 虚拟列表

```csharp
// 对于长列表，只渲染可见项
public class VirtualList : MonoBehaviour
{
    [SerializeField] private ScrollRect scrollRect;
    [SerializeField] private RectTransform content;
    [SerializeField] private GameObject itemPrefab;

    private List<object> dataList = new();
    private List<GameObject> visibleItems = new();

    private float itemHeight = 100f;
    private int visibleCount;

    private void Start()
    {
        visibleCount = Mathf.CeilToInt(scrollRect.viewport.rect.height / itemHeight) + 2;

        // 预创建Item
        for (int i = 0; i < visibleCount; i++)
        {
            var item = Instantiate(itemPrefab, content);
            visibleItems.Add(item);
        }

        scrollRect.onValueChanged.AddListener(OnScroll);
    }

    private void OnScroll(Vector2 position)
    {
        int startIndex = Mathf.FloorToInt(content.anchoredPosition.y / itemHeight);

        for (int i = 0; i < visibleCount; i++)
        {
            int dataIndex = startIndex + i;
            if (dataIndex >= 0 && dataIndex < dataList.Count)
            {
                visibleItems[i].SetActive(true);
                UpdateItem(visibleItems[i], dataList[dataIndex]);
                visibleItems[i].GetComponent<RectTransform>().anchoredPosition =
                    new Vector2(0, -dataIndex * itemHeight);
            }
            else
            {
                visibleItems[i].SetActive(false);
            }
        }
    }

    private void UpdateItem(GameObject item, object data)
    {
        // 更新Item显示
    }
}
```

---

## 性能检测

### UI Profiler

```
1. Window > Analysis > Profiler
2. 选择 UI 模块
3. 观察:
   - Canvas.BuildBatch 时间
   - Canvas.SendWillRenderCanvases 时间
   - Canvas.RenderOverlays 时间
```

### Frame Debugger

```
1. Window > Analysis > Frame Debugger
2. 启用后观察:
   - UI DrawCall 数量
   - 每个Canvas的渲染情况
```

---

## 优化检查清单

### Canvas设置

- [ ] 按更新频率拆分Canvas
- [ ] 静态UI使用独立Canvas
- [ ] 弹窗使用独立Canvas
- [ ] 合理设置Pixel Perfect

### 图集

- [ ] UI元素打包到图集
- [ ] 图集大小合理（2048以内）
- [ ] 禁用不必要的Read/Write

### 交互

- [ ] 禁用不必要的Raycast Target
- [ ] 减少GraphicRaycaster检测范围
- [ ] 使用对象池复用UI

### 文字

- [ ] 使用TextMeshPro
- [ ] 避免频繁更新文字
- [ ] 共享字体资源

---

## 相关链接

- 深入学习: [UGUI深度解析](../../20_核心系统/32_游戏系统/【源码解析】UGUI深度解析.md)
- 最佳实践: [GC优化清单](../内存管理/最佳实践-GC优化清单.md)
- 性能工具: [性能分析工具](../../30_性能优化/教程-性能分析工具.md)
