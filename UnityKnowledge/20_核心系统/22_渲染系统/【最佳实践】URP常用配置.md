---
title: 【最佳实践】URP常用配置
tags: [Unity, 渲染系统, URP, 最佳实践]
category: 核心系统/渲染系统
created: 2026-03-05 08:31
updated: 2026-03-05 08:31
description: URP渲染管线常用配置优化
unity_version: 2021.3+
---
# URP 常用配置

> Universal Render Pipeline 配置指南 `#渲染` `#URP` `#配置`

## 快速参考

```
URP Asset 结构：
├── Render Pipeline Asset (URP设置)
├── Renderer Data (渲染器设置)
└── Renderer Features (渲染特性)
```

---

## URP Asset 配置

### General 设置

| 设置 | 说明 | 推荐值 |
|------|------|--------|
| **Depth Texture** | 深度纹理 | 开启（后处理需要） |
| **Opaque Texture** | 不透明纹理 | 按需开启 |
| **Opaque Downsampling** | 降采样 | None（质量）/ 2x（性能） |
| **SRP Batcher** | SRP批处理 | 开启 |
| **Dynamic Batching** | 动态合批 | 小项目开启 |
| **Mixed Lighting** | 混合光照 | 按需 |
| **SRP Default Shader** | 默认Shader | URP/Lit |

### Quality 设置

| 设置 | 移动端 | PC |
|------|--------|-----|
| **HDR** | 关闭 | 开启 |
| **MSAA** | 4x | 8x |
| **Render Scale** | 1.0 | 1.0 |
| **Main Light** | Per Pixel | Per Pixel |
| **Additional Lights** | Per Vertex / Off | Per Pixel |
| **Additional Lights Per Object** | 4 | 8 |
| **Cascade Count** | 2 | 4 |
| **Shadow Distance** | 50 | 150 |
| **Shadow Resolution** | 1024 | 2048 |

### Lighting 设置

```csharp
// 代码配置
using UnityEngine.Rendering.Universal;

public class URPConfigurator
{
    public static void ConfigureForMobile(UniversalRenderPipelineAsset urpAsset)
    {
        // 质量设置
        urpAsset.supportsHDR = false;
        urpAsset.msaaSampleCount = 4;
        urpAsset.renderScale = 1.0f;

        // 光照设置
        urpAsset.mainLightRenderingMode = LightRenderingMode.PerPixel;
        urpAsset.additionalLightsRenderingMode = LightRenderingMode.PerVertex;
        urpAsset.maxAdditionalLightsCount = 4;

        // 阴影设置
        urpAsset.shadowDistance = 50f;
        urpAsset.shadowCascadeCount = 2;
        urpAsset.mainLightShadowmapResolution = 1024;
    }

    public static void ConfigureForPC(UniversalRenderPipelineAsset urpAsset)
    {
        urpAsset.supportsHDR = true;
        urpAsset.msaaSampleCount = 8;
        urpAsset.renderScale = 1.0f;

        urpAsset.mainLightRenderingMode = LightRenderingMode.PerPixel;
        urpAsset.additionalLightsRenderingMode = LightRenderingMode.PerPixel;
        urpAsset.maxAdditionalLightsCount = 8;

        urpAsset.shadowDistance = 150f;
        urpAsset.shadowCascadeCount = 4;
        urpAsset.mainLightShadowmapResolution = 2048;
    }
}
```

---

## Renderer Features

### 屏幕空间遮蔽 (SSAO)

```
添加: URP Asset > Renderer Data > Add Feature > Screen Space Ambient Occlusion

配置：
├── Downsample: 开启（性能优化）
├── After Opaque: 关闭
├── Source: Depth Normal
├── Intensity: 1.0
├── Radius: 0.25
├── Sample Count: Medium
└── Blur Quality: Medium
```

### 屏幕空间阴影 (SSR)

```
添加: URP Asset > Renderer Data > Add Feature > Screen Space Reflections

配置：
├── Downsample: 开启
├── After Opaque: 开启
├── Depth Buffer Resolution: Downsample 2x
├── Screen Fade Distance: 0.1
├── Surface Fade Distance: 0.1
└── Reflect Layers: Default
```

### 全屏模糊

```csharp
// 自定义Renderer Feature
public class BlurFeature : ScriptableRendererFeature
{
    [System.Serializable]
    public class BlurSettings
    {
        public RenderPassEvent renderPassEvent = RenderPassEvent.AfterRenderingTransparents;
        public Material blurMaterial;
        public float blurStrength = 1.0f;
        public int blurPasses = 2;
    }

    public BlurSettings settings = new BlurSettings();
    private BlurPass blurPass;

    public override void Create()
    {
        blurPass = new BlurPass(settings);
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        renderer.EnqueuePass(blurPass);
    }
}
```

---

## 后处理配置

### Volume Profile

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class PostProcessingSetup : MonoBehaviour
{
    [SerializeField] private Volume volume;

    public void SetupDefaultPostProcessing()
    {
        var profile = volume.profile;

        // Bloom
        if (!profile.TryGet(out Bloom bloom))
        {
            bloom = profile.Add<Bloom>();
        }
        bloom.intensity.value = 0.5f;
        bloom.threshold.value = 0.9f;
        bloom.scatter.value = 0.5f;

        // Color Adjustments
        if (!profile.TryGet(out ColorAdjustments colorAdjustments))
        {
            colorAdjustments = profile.Add<ColorAdjustments>();
        }
        colorAdjustments.saturation.value = 10f;
        colorAdjustments.contrast.value = 10f;

        // Vignette
        if (!profile.TryGet(out Vignette vignette))
        {
            vignette = profile.Add<Vignette>();
        }
        vignette.intensity.value = 0.3f;
        vignette.roundness.value = 0.8f;

        // Tonemapping
        if (!profile.TryGet(out Tonemapping tonemapping))
        {
            tonemapping = profile.Add<Tonemapping>();
        }
        tonemapping.mode.value = TonemappingMode.ACES;
    }
}
```

### 运行时调整

```csharp
public class PostProcessingController : MonoBehaviour
{
    [SerializeField] private Volume volume;

    private ColorAdjustments colorAdjustments;
    private Vignette vignette;
    private Bloom bloom;

    private void Awake()
    {
        volume.profile.TryGet(out colorAdjustments);
        volume.profile.TryGet(out vignette);
        volume.profile.TryGet(out bloom);
    }

    public void SetSaturation(float value)
    {
        if (colorAdjustments != null)
        {
            colorAdjustments.saturation.value = value;
        }
    }

    public void SetVignetteIntensity(float value)
    {
        if (vignette != null)
        {
            vignette.intensity.value = value;
        }
    }

    public void SetBloomIntensity(float value)
    {
        if (bloom != null)
        {
            bloom.intensity.value = value;
        }
    }

    // 受伤效果
    public async UniTaskVoid DamageEffect()
    {
        // 快速变红 + 暗角
        var originalSaturation = colorAdjustments.saturation.value;
        var originalVignette = vignette.intensity.value;

        colorAdjustments.saturation.value = -50f;
        vignette.intensity.value = 0.6f;

        await UniTask.Delay(200);

        // 恢复
        colorAdjustments.saturation.value = originalSaturation;
        vignette.intensity.value = originalVignette;
    }
}
```

---

## 性能优化配置

### 分档配置

```csharp
public enum QualityPreset
{
    Low,
    Medium,
    High,
    Ultra
}

public class URPQualityManager : MonoBehaviour
{
    [SerializeField] private UniversalRenderPipelineAsset[] qualityAssets;

    public void SetQuality(QualityPreset preset)
    {
        QualitySettings.SetQualityLevel((int)preset);
    }

    public static void ApplyDeviceOptimal()
    {
        // 根据设备自动选择
        int memoryMB = SystemInfo.systemMemorySize;
        int cpuCores = SystemInfo.processorCount;

        QualityPreset preset;

        if (memoryMB >= 8000 && cpuCores >= 8)
        {
            preset = QualityPreset.Ultra;
        }
        else if (memoryMB >= 4000 && cpuCores >= 4)
        {
            preset = QualityPreset.High;
        }
        else if (memoryMB >= 2000)
        {
            preset = QualityPreset.Medium;
        }
        else
        {
            preset = QualityPreset.Low;
        }

        QualitySettings.SetQualityLevel((int)preset);
    }
}
```

### 动态分辨率

```csharp
public class DynamicResolution : MonoBehaviour
{
    [SerializeField] private float minScale = 0.7f;
    [SerializeField] private float maxScale = 1.0f;
    [SerializeField] private float targetFrameTime = 16.67f; // 60fps

    private float currentScale = 1.0f;

    private void Update()
    {
        float frameTime = Time.unscaledDeltaTime * 1000f;

        // 动态调整
        if (frameTime > targetFrameTime * 1.2f)
        {
            // 帧率过低，降低分辨率
            currentScale = Mathf.Max(minScale, currentScale - 0.05f);
        }
        else if (frameTime < targetFrameTime * 0.8f)
        {
            // 帧率充足，提高分辨率
            currentScale = Mathf.Min(maxScale, currentScale + 0.02f);
        }

        // 应用到URP
        var urpAsset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
        if (urpAsset != null)
        {
            urpAsset.renderScale = currentScale;
        }
    }
}
```

---

## 常见问题

### Q: 为什么SRP Batcher不生效？

```
检查清单：
1. URP Asset > SRP Batcher > 开启
2. Shader 使用 URP 标准 Shader
3. 材质使用同一个 Shader 变体
4. 不使用 Material Property Block
```

### Q: 阴影有锯齿怎么办？

```
解决方案：
1. 增加 Shadow Resolution
2. 增加 Cascade Count
3. 使用 Soft Shadows
4. 调整 Shadow Distance
```

### Q: 后处理不生效？

```
检查清单：
1. 场景中有 Volume 组件
2. Volume Profile 已配置
3. Camera 启用 Post Processing
4. URP Asset 中启用后处理
```

---

## 相关链接

- 深入学习: [渲染管线基础](../../20_核心系统/渲染系统/教程-渲染管线基础.md)
- Shader: [Shader基础模板](Shader基础模板.md)
- 后处理: [后处理(Post Processing)](../../20_核心系统/渲染系统/教程-后处理(Post%20Processing).md)
