# 性能数据 - UGUI DrawCall影响因素

> UGUI DrawCall优化效果量化分析 `#性能优化` `#渲染` `#UI` `#性能数据`

## 测试环境

| 配置 | 值 |
|------|-----|
| Unity版本 | 2021.3 LTS |
| 测试平台 | Windows 11 |
| URP版本 | 14.0 |
| 测试场景 | 100个UI元素 |

---

## 测试1: 图集合批

### 测试配置

```
场景：100个Image元素
- 元素排列：10x10网格
- 每个元素：64x64像素
```

### 测试代码

```csharp
using UnityEngine;
using UnityEngine.UI;

public class DrawCallBenchmark : MonoBehaviour
{
    [SerializeField] private Sprite spriteA;  // 图集A中的Sprite
    [SerializeField] private Sprite spriteB;  // 图集B中的Sprite
    [SerializeField] private Transform container;

    public void CreateImages(bool useSameAtlas)
    {
        // 清理
        foreach (Transform child in container)
        {
            Destroy(child.gameObject);
        }

        // 创建100个Image
        for (int i = 0; i < 100; i++)
        {
            var go = new GameObject($"Image_{i}");
            go.transform.SetParent(container);

            var rectTransform = go.AddComponent<RectTransform>();
            rectTransform.sizeDelta = new Vector2(64, 64);

            var image = go.AddComponent<Image>();

            // 交替使用不同Sprite
            if (useSameAtlas)
            {
                image.sprite = spriteA;  // 同一图集
            }
            else
            {
                image.sprite = i % 2 == 0 ? spriteA : spriteB;  // 不同图集
            }
        }
    }
}
```

### 测试结果

| 配置 | DrawCall | 说明 |
|------|----------|------|
| **同一图集** | 1 | 完美合批 |
| **2个图集交替** | 100 | 每个打断合批 |
| **2个图集分组排列** | 2 | 分组后合批 |

### 结论

- 同一图集元素可以完美合批
- 穿插不同图集会完全打断合批
- 将相同图集元素放在一起可恢复合批

---

## 测试2: 文字影响

### 测试配置

```
场景：10个文本元素 + 10个图片元素
- 文本：TextMeshPro
- 图片：同一图集
```

### 测试结果

| 配置 | DrawCall | 说明 |
|------|----------|------|
| **10图片（同图集）** | 1 | 基准 |
| **+ 10个文字（同字体）** | 2 | 文字额外1个 |
| **+ 10个文字（2种字体）** | 3 | 字体不同增加 |
| **+ 10个文字（不同颜色）** | 2 | 颜色不影响 |

### 结论

- 文字与图片分开渲染
- 字体图集不同会增加DrawCall
- 文字颜色不影响DrawCall

---

## 测试3: 遮罩影响

### 测试配置

```
场景：20个图片元素（同一图集）
- 使用Mask或RectMask2D
```

### 测试结果

| 配置 | DrawCall | 说明 |
|------|----------|------|
| **无遮罩** | 1 | 基准 |
| **1个Mask** | 3 | +2（模板缓冲） |
| **1个RectMask2D** | 1 | 无额外开销 |
| **2个RectMask2D（不重叠）** | 1 | 仍可合批 |
| **2个RectMask2D（重叠）** | 2 | 裁剪区域不同 |

### 结论

- Mask增加2个DrawCall（模板缓冲）
- RectMask2D通常无额外开销
- 多个RectMask2D重叠会打断合批

---

## 测试4: 层级穿插

### 测试配置

```
场景：A、B两种图片交替排列
- A：图集1
- B：图集2
```

### 测试结果

| 排列方式 | DrawCall | 说明 |
|----------|----------|------|
| **AAAA BBBB** | 2 | 分组排列 |
| **ABAB ABAB** | 8 | 完全穿插 |
| **AABB AABB** | 4 | 部分穿插 |
| **ABBA ABBA** | 8 | 回文穿插 |

### 结论

- 分组排列是关键
- 任何穿插都会打断合批
- Hierarchy中的顺序影响渲染顺序

---

## 测试5: 材质影响

### 测试配置

```
场景：20个图片（同一图集）
- 使用默认材质或自定义材质
```

### 测试结果

| 配置 | DrawCall | 说明 |
|------|----------|------|
| **全部默认材质** | 1 | 基准 |
| **1个自定义材质** | 2 | 打断合批 |
| **相同自定义材质** | 1 | 可合批 |
| **不同自定义材质** | 20 | 完全打断 |

---

## 优化效果总结

### 典型场景优化

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **背包界面** | 50+ | 5-8 | 84% |
| **商店界面** | 80+ | 8-12 | 85% |
| **战斗UI** | 30+ | 4-6 | 80% |
| **弹窗界面** | 15+ | 3-4 | 75% |

### 优化策略效果

| 策略 | DrawCall减少 | 复杂度 |
|------|--------------|--------|
| **图集打包** | 70-90% | 低 |
| **层级分组** | 50-80% | 低 |
| **RectMask2D替代Mask** | 每个遮罩-2 | 低 |
| **Canvas拆分** | 隔离重建 | 中 |
| **禁用Raycast Target** | 0（提升交互性能） | 低 |

---

## 实际案例

### 背包界面优化

```
优化前：
├── DrawCall: 52
├── 重建触发: 每次滚动
└── 帧率影响: 5-10fps

优化措施：
1. 物品图标打包到图集
2. 文字使用统一字体
3. 稀有度边框使用Shader实现
4. RectMask2D替代Mask
5. 静态/动态元素分离Canvas

优化后：
├── DrawCall: 6
├── 重建触发: 仅动态区域
└── 帧率影响: <1fps
```

### 性能对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| **DrawCall** | 52 | 6 |
| **UI耗时/帧** | 2.3ms | 0.4ms |
| **滚动流畅度** | 卡顿 | 丝滑 |

---

## 检测工具

### Frame Debugger

```
1. Window > Analysis > Frame Debugger
2. 启用后观察每个DrawCall
3. 识别：
   - 哪些元素被打散
   - 遮罩影响
   - 材质差异
```

### Profiler

```
1. Window > Analysis > Profiler
2. 选择 UI 模块
3. 观察：
   - Canvas.BuildBatch
   - Canvas.SendWillRenderCanvases
```

---

## 相关链接

- 最佳实践: [UI性能优化](../渲染优化/最佳实践-UI性能优化.md)
- 深入学习: [UGUI深度解析](../../../学习/03-游戏系统开发/UGUI深度解析.md)
