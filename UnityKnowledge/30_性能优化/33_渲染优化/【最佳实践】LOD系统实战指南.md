---
title: 【最佳实践】LOD系统实战指南
tags: [Unity, 性能优化, 渲染, LOD, 最佳实践]
category: 性能优化/渲染优化
created: 2026-03-07 10:00
updated: 2026-03-07 10:00
description: Unity LOD(Level of Detail)系统完整实战指南，包含配置方法、过渡优化和性能收益分析
unity_version: 2021.3+
---

# 最佳实践 - LOD系统实战指南

> 使用LOD系统降低远处物体的渲染成本 `#性能优化` `#渲染` `#LOD` `#最佳实践`

## 文档定位

本文档从**实战角度**讲解 LOD 系统的配置和优化。

**相关文档**：[[【最佳实践】3D渲染优化指南]]、[[【教程】渲染性能优化]]

---

## 1. LOD 系统概述

### 1.1 什么是 LOD

**LOD (Level of Detail)**：根据物体与摄像机的距离，使用不同精度的模型进行渲染。

```
┌─────────────────────────────────────────────────────────────┐
│                    LOD 工作原理                              │
│                                                             │
│   摄像机                                                    │
│     👁️                                                      │
│      │                                                      │
│      ├──── LOD0 (0-20m)  ── 高精度模型 (10000 三角形)       │
│      │                                                      │
│      ├──── LOD1 (20-50m) ── 中精度模型 (2500 三角形)        │
│      │                                                      │
│      ├──── LOD2 (50-100m)── 低精度模型 (500 三角形)         │
│      │                                                      │
│      └──── LOD3 (100m+)  ── 最低精度/隐藏 (<100 三角形)     │
│                                                             │
│   性能收益：                                                │
│   ├── 顶点处理减少 50-90%                                  │
│   ├── GPU 负载降低                                         │
│   └── 内存带宽节省                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 LOD 组件

```csharp
using UnityEngine;

/// <summary>
/// LOD 组配置示例
/// </summary>
public class LODSetupExample : MonoBehaviour
{
    [System.Serializable]
    public class LODLevel
    {
        public Mesh mesh;
        public Material[] materials;
        public float screenRelativeTransitionHeight; // 屏幕占比阈值
        public float fadeTransitionWidth;            // 过渡宽度
    }

    [Header("LOD Levels")]
    [SerializeField] private LODLevel[] lodLevels;

    // Unity LODGroup 组件使用：
    // 1. 添加 LODGroup 组件
    // 2. 配置各 LOD 级别的屏幕占比
    // 3. 为每个级别指定 MeshRenderer
}
```

---

## 2. LOD 配置实战

### 2.1 基础配置步骤

```
┌─────────────────────────────────────────────────────────────┐
│                    LOD 配置步骤                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 准备模型                                                │
│     ├── LOD0: 原始高模 (100%)                               │
│     ├── LOD1: 简化 50%                                      │
│     ├── LOD2: 简化 25%                                      │
│     └── LOD3: 简化 10% 或 Billboard                         │
│                                                             │
│  2. 创建 LODGroup                                           │
│     ├── 选中根物体                                          │
│     ├── Add Component → LOD Group                           │
│     └── 配置 LOD 级别                                       │
│                                                             │
│  3. 配置各级别                                               │
│     ├── 点击 LOD 节点                                       │
│     ├── 拖入对应的 MeshRenderer                             │
│     └── 调整屏幕占比阈值                                    │
│                                                             │
│  4. 测试效果                                                │
│     ├── Scene 视图查看 LOD 切换                             │
│     └── Game 视图验证视觉效果                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 LOD 级别配置

```csharp
/// <summary>
/// LOD 配置管理器
/// </summary>
public class LODConfigurator : MonoBehaviour
{
    [Header("LOD Settings")]
    [SerializeField] private bool autoConfigure = true;
    [SerializeField] private float lod0Distance = 20f;
    [SerializeField] private float lod1Distance = 50f;
    [SerializeField] private float lod2Distance = 100f;
    [SerializeField] private float cullDistance = 200f;

    private LODGroup lodGroup;
    private Camera mainCamera;

    private void Start()
    {
        mainCamera = Camera.main;

        if (autoConfigure)
        {
            ConfigureLOD();
        }
    }

    /// <summary>
    /// 自动配置 LOD
    /// </summary>
    [ContextMenu("Configure LOD")]
    public void ConfigureLOD()
    {
        lodGroup = GetComponent<LODGroup>();
        if (lodGroup == null)
        {
            lodGroup = gameObject.AddComponent<LODGroup>();
        }

        // 获取所有子物体的 MeshRenderer
        var renderers = GetComponentsInChildren<MeshRenderer>(true);

        if (renderers.Length == 0)
        {
            Debug.LogWarning("No MeshRenderers found");
            return;
        }

        // 计算屏幕占比阈值
        float screenSize = CalculateScreenSize();

        // 配置 LOD 级别
        var lods = new LOD[]
        {
            // LOD0: 高精度 (50% - 100% 屏幕占比)
            new LOD(0.5f, new Renderer[] { renderers[0] }),

            // LOD1: 中精度 (25% - 50%)
            new LOD(0.25f, new Renderer[] { renderers.Length > 1 ? renderers[1] : renderers[0] }),

            // LOD2: 低精度 (10% - 25%)
            new LOD(0.1f, new Renderer[] { renderers.Length > 2 ? renderers[2] : renderers[0] }),

            // LOD3: 最低精度/隐藏 (0% - 10%)
            new LOD(0.01f, new Renderer[] { renderers.Length > 3 ? renderers[3] : renderers[0] })
        };

        lodGroup.SetLODs(lods);
        lodGroup.RecalculateBounds();

        // 设置剔除距离
        lodGroup.fadeMode = LODFadeMode.CrossFade;
    }

    private float CalculateScreenSize()
    {
        // 估算物体在屏幕上的大小
        var bounds = CalculateBounds();
        float maxExtent = bounds.extents.magnitude;
        float distance = Vector3.Distance(transform.position, mainCamera.transform.position);

        // 屏幕占比 ≈ 物体大小 / 距离
        return (maxExtent / distance) * 0.5f;
    }

    private Bounds CalculateBounds()
    {
        var renderers = GetComponentsInChildren<Renderer>();
        if (renderers.Length == 0) return new Bounds();

        Bounds bounds = renderers[0].bounds;
        foreach (var renderer in renderers)
        {
            bounds.Encapsulate(renderer.bounds);
        }
        return bounds;
    }
}
```

### 2.3 运行时 LOD 控制

```csharp
/// <summary>
/// 运行时 LOD 控制器
/// </summary>
public class RuntimeLODController : MonoBehaviour
{
    [Header("LOD Control")]
    [SerializeField] private bool enableDynamicLOD = true;
    [SerializeField] private float lodBias = 1.0f;
    [SerializeField] private float maxLODLevel = 3;

    [Header("Quality Settings")]
    [SerializeField] private QualityPreset lowQuality;
    [SerializeField] private QualityPreset mediumQuality;
    [SerializeField] private QualityPreset highQuality;

    [System.Serializable]
    public class QualityPreset
    {
        public float lodBias;
        public int maximumLODLevel;
        public float lodCrossFadeDuration;
    }

    private LODGroup[] allLODGroups;

    private void Start()
    {
        allLODGroups = FindObjectsOfType<LODGroup>();
        ApplyQualitySettings(QualitySettings.GetQualityLevel());
    }

    /// <summary>
    /// 根据画质设置调整 LOD
    /// </summary>
    public void ApplyQualitySettings(int qualityLevel)
    {
        QualityPreset preset;

        switch (qualityLevel)
        {
            case 0:
                preset = lowQuality;
                break;
            case 1:
            case 2:
                preset = mediumQuality;
                break;
            default:
                preset = highQuality;
                break;
        }

        // 应用 LOD Bias
        QualitySettings.lodBias = preset.lodBias;

        // 应用最大 LOD 级别
        QualitySettings.maximumLODLevel = preset.maximumLODLevel;

        Debug.Log($"Applied LOD settings: Bias={preset.lodBias}, MaxLOD={preset.maximumLODLevel}");
    }

    /// <summary>
    /// 动态调整 LOD（基于帧率）
    /// </summary>
    public void AdjustLODForPerformance(float currentFPS, float targetFPS)
    {
        if (!enableDynamicLOD) return;

        if (currentFPS < targetFPS - 5f)
        {
            // 帧率过低，降低 LOD 质量
            QualitySettings.lodBias = Mathf.Max(0.5f, QualitySettings.lodBias - 0.1f);
        }
        else if (currentFPS > targetFPS + 10f)
        {
            // 帧率充足，提高 LOD 质量
            QualitySettings.lodBias = Mathf.Min(2.0f, QualitySettings.lodBias + 0.1f);
        }
    }
}
```

---

## 3. LOD 过渡优化

### 3.1 过渡模式

```
┌─────────────────────────────────────────────────────────────┐
│                    LOD 过渡模式对比                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 无过渡 (None)                                           │
│     ├── 直接切换，可能闪烁                                  │
│     ├── 性能最优                                            │
│     └── 适合快速移动的物体                                  │
│                                                             │
│  2. 淡入淡出 (CrossFade)                                    │
│     ├── 平滑过渡                                            │
│     ├── 短暂同时渲染两个LOD                                │
│     └── 适合静态场景                                        │
│                                                             │
│  3. SpeedTree (植被专用)                                    │
│     ├── 专为植被优化                                        │
│     ├── Billboard过渡                                       │
│     └── 适合大量树木                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 CrossFade 配置

```csharp
/// <summary>
/// LOD 过渡优化配置
/// </summary>
public class LODTransitionOptimizer : MonoBehaviour
{
    [Header("Transition Settings")]
    [SerializeField] private LODFadeMode fadeMode = LODFadeMode.CrossFade;
    [SerializeField] private float crossFadeDuration = 0.3f;
    [SerializeField] private AnimationCurve crossFadeCurve = AnimationCurve.EaseInOut(0, 0, 1, 1);

    private LODGroup lodGroup;

    private void Awake()
    {
        lodGroup = GetComponent<LODGroup>();
        if (lodGroup != null)
        {
            ConfigureTransitions();
        }
    }

    private void ConfigureTransitions()
    {
        // 设置过渡模式
        lodGroup.fadeMode = fadeMode;

        // 配置动画过渡宽度
        var lods = lodGroup.GetLODs();
        for (int i = 0; i < lods.Length; i++)
        {
            // fadeTransitionWidth: 过渡区域占LOD范围的比例
            lods[i].fadeTransitionWidth = 0.1f; // 10% 过渡区域
        }

        lodGroup.SetLODs(lods);
    }

    /// <summary>
    /// 自定义 LOD 过渡着色器
    /// </summary>
    public void SetupCustomLODShader()
    {
        // 对于 URP，需要在 Shader 中添加 LOD CrossFade 支持
        // HLSL 代码示例：
        /*
        #pragma multi_compile _ LOD_FADE_CROSSFADE

        // 在片元着色器中
        #ifdef LOD_FADE_CROSSFADE
            float2 fadeXY = unity_LODFade.xy;
            float fade = fadeXY.x + fadeXY.y;
            clip(fade - 0.5);
        #endif
        */
    }
}
```

### 3.3 消除 LOD Pop 效果

```csharp
/// <summary>
/// LOD 切换平滑化
/// </summary>
public class LODPopReducer : MonoBehaviour
{
    [Header("Pop Reduction")]
    [SerializeField] private float transitionHysteresis = 0.1f; // 滞后值
    [SerializeField] private float minTransitionInterval = 0.5f; // 最小切换间隔

    private LODGroup lodGroup;
    private int currentLODLevel = 0;
    private float lastTransitionTime;

    private void Start()
    {
        lodGroup = GetComponent<LODGroup>();
    }

    private void Update()
    {
        if (lodGroup == null) return;

        // 获取当前应该的 LOD 级别
        int desiredLevel = CalculateDesiredLODLevel();

        // 检查是否需要切换
        if (desiredLevel != currentLODLevel)
        {
            // 检查切换间隔
            if (Time.time - lastTransitionTime < minTransitionInterval)
            {
                return; // 太快，跳过
            }

            // 应用滞后
            float hysteresis = transitionHysteresis * (desiredLevel > currentLODLevel ? 1f : -1f);

            if (Mathf.Abs(desiredLevel - currentLODLevel) > hysteresis)
            {
                currentLODLevel = desiredLevel;
                lastTransitionTime = Time.time;
            }
        }
    }

    private int CalculateDesiredLODLevel()
    {
        // 基于距离计算 LOD 级别
        float distance = Vector3.Distance(transform.position, Camera.main.transform.position);

        // 这里简化处理，实际应使用 LODGroup 的计算
        if (distance < 20f) return 0;
        if (distance < 50f) return 1;
        if (distance < 100f) return 2;
        return 3;
    }
}
```

---

## 4. Billboard LOD

### 4.1 何时使用 Billboard

```
┌─────────────────────────────────────────────────────────────┐
│                    Billboard 使用场景                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 适合：                                                  │
│  ├── 远处的树木、植被                                       │
│  ├── 远处的建筑                                             │
│  ├── 大量重复物体（草地、石头）                             │
│  └── 背景装饰物                                             │
│                                                             │
│  ❌ 不适合：                                                │
│  ├── 近处物体                                               │
│  ├── 玩家可交互的物体                                       │
│  ├── 需要正确阴影的物体                                     │
│  └── 高度不对称的物体                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Billboard 配置

```csharp
/// <summary>
/// Billboard LOD 配置
/// </summary>
public class BillboardLODSetup : MonoBehaviour
{
    [Header("Billboard Settings")]
    [SerializeField] private Texture2D billboardTexture;
    [SerializeField] private float billboardDistance = 100f;
    [SerializeField] private bool faceCamera = true;

    private LODGroup lodGroup;
    private GameObject billboardObject;

    /// <summary>
    /// 设置 Billboard LOD
    /// </summary>
    [ContextMenu("Setup Billboard LOD")]
    public void SetupBillboardLOD()
    {
        lodGroup = GetComponent<LODGroup>();
        if (lodGroup == null)
        {
            lodGroup = gameObject.AddComponent<LODGroup>();
        }

        // 创建 Billboard 对象
        CreateBillboard();

        // 配置 LOD
        var renderers = GetComponentsInChildren<MeshRenderer>(true);
        var billboardRenderer = billboardObject.GetComponent<MeshRenderer>();

        var lods = new LOD[]
        {
            // LOD0-2: 使用原模型
            new LOD(0.5f, new Renderer[] { renderers[0] }),
            new LOD(0.25f, new Renderer[] { renderers[0] }),
            new LOD(0.1f, new Renderer[] { renderers[0] }),

            // LOD3: 使用 Billboard
            new LOD(0.02f, new Renderer[] { billboardRenderer })
        };

        lodGroup.SetLODs(lods);
        lodGroup.RecalculateBounds();
    }

    private void CreateBillboard()
    {
        // 创建 Billboard 四边形
        billboardObject = new GameObject("Billboard");
        billboardObject.transform.SetParent(transform);
        billboardObject.transform.localPosition = Vector3.zero;

        // 添加 MeshFilter 和 MeshRenderer
        var meshFilter = billboardObject.AddComponent<MeshFilter>();
        var meshRenderer = billboardObject.AddComponent<MeshRenderer>();

        // 创建四边形网格
        meshFilter.mesh = CreateQuadMesh();

        // 设置材质
        var material = new Material(Shader.Find("Unlit/Transparent Cutout"));
        material.mainTexture = billboardTexture;
        meshRenderer.material = material;

        // 如果需要面向摄像机
        if (faceCamera)
        {
            billboardObject.AddComponent<BillboardFaceCamera>();
        }
    }

    private Mesh CreateQuadMesh()
    {
        Mesh mesh = new Mesh();

        Vector3[] vertices = new Vector3[]
        {
            new Vector3(-0.5f, 0, 0),
            new Vector3(0.5f, 0, 0),
            new Vector3(0.5f, 2, 0),
            new Vector3(-0.5f, 2, 0)
        };

        int[] triangles = new int[] { 0, 2, 1, 0, 3, 2 };

        Vector2[] uv = new Vector2[]
        {
            new Vector2(0, 0),
            new Vector2(1, 0),
            new Vector2(1, 1),
            new Vector2(0, 1)
        };

        mesh.vertices = vertices;
        mesh.triangles = triangles;
        mesh.uv = uv;
        mesh.RecalculateNormals();

        return mesh;
    }
}

/// <summary>
/// Billboard 面向摄像机
/// </summary>
public class BillboardFaceCamera : MonoBehaviour
{
    private Camera mainCamera;

    private void Start()
    {
        mainCamera = Camera.main;
    }

    private void LateUpdate()
    {
        if (mainCamera == null) return;

        // 只绕 Y 轴旋转
        Vector3 direction = mainCamera.transform.position - transform.position;
        direction.y = 0;

        if (direction.sqrMagnitude > 0.001f)
        {
            transform.rotation = Quaternion.LookRotation(direction);
        }
    }
}
```

---

## 5. LOD 性能收益分析

### 5.1 性能数据对比

**场景**：100棵树的森林场景

| 配置 | 三角形数 | DrawCall | GPU时间 | FPS |
|------|---------|----------|---------|-----|
| 无LOD | 500,000 | 100 | 12ms | 45 |
| LOD0-2 | 150,000 | 100 | 5ms | 80 |
| LOD0-3+Billboard | 50,000 | 100 | 2ms | 120 |
| LOD + 批处理 | 50,000 | 10 | 1.5ms | 150 |

### 5.2 LOD 配置建议

```
┌─────────────────────────────────────────────────────────────┐
│                    LOD 配置建议                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  移动端 (性能优先)：                                        │
│  ├── LOD0: 0-15m, 原模型                                   │
│  ├── LOD1: 15-40m, 简化50%                                 │
│  ├── LOD2: 40-80m, 简化80%                                 │
│  └── LOD3: 80m+, Billboard或隐藏                           │
│                                                             │
│  PC端 (画质优先)：                                          │
│  ├── LOD0: 0-30m, 原模型                                   │
│  ├── LOD1: 30-80m, 简化50%                                 │
│  ├── LOD2: 80-150m, 简化75%                                │
│  └── LOD3: 150m+, 简化90%                                  │
│                                                             │
│  过渡设置：                                                  │
│  ├── fadeTransitionWidth: 0.1-0.2                          │
│  ├── CrossFade时长: 0.2-0.5秒                              │
│  └── 最小切换间隔: 0.3-0.5秒                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 LOD 检查清单

```markdown
## LOD 优化检查清单

### 模型准备
- [ ] 为每个重要物体准备3-4个LOD级别
- [ ] LOD1 简化约50%
- [ ] LOD2 简化约75%
- [ ] LOD3 简化约90%或Billboard

### 配置
- [ ] 正确设置屏幕占比阈值
- [ ] 启用CrossFade过渡
- [ ] 设置合理的过渡宽度
- [ ] 配置剔除距离

### 性能验证
- [ ] 使用Frame Debugger验证LOD切换
- [ ] 测试各距离的三角形数量
- [ ] 确认无明显的Pop效果
- [ ] 验证帧率提升

### 特殊情况
- [ ] 植被使用SpeedTree LOD
- [ ] 大量重复物体考虑GPU Instancing
- [ ] 背景物体考虑Billboard
```

---

## 相关链接

- [[【最佳实践】3D渲染优化指南]] - 3D渲染优化完整指南
- [[【最佳实践】遮挡剔除实战]] - 遮挡剔除优化
- [[【教程】渲染性能优化]] - 渲染优化基础

---

*创建日期: 2026-03-07*
*相关标签: #性能优化 #渲染 #LOD #最佳实践*
