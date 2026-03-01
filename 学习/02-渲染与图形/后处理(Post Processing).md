# 后处理（Post Processing）

> 第5课 | 渲染与图形模块

## 1. URP Volume系统

**Volume系统**是URP的后处理框架，允许通过Volume组件配置各种后处理效果。

```
┌─────────────────────────────────────────────────────────────┐
│                     URP Volume 系统                          │
│                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│   │   Volume    │────→│    Profile    │────→│   Override  │   │
│   │  (全局配置) │     │   (效果配置)   │     │  (覆盖效果)   │   │
│   └─────────────┘     └─────────────┘     └─────────────┘   │
│         │                  │                    │                │
│         ↓                  ↓                    ↓                │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Volume Stack (效果栈)                        │   │
│   │  Bloom → Tonemapping → Vignette → ColorGrading          │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Volume组件

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Volume组件 - 挂载到相机上配置后处理效果
/// </summary>
public class PostProcessVolume : MonoBehaviour
{
    [Header("Volume Settings")]
    [SerializeField] private bool isGlobal = true;
    [SerializeField] private int priority = 0;

    private Volume volume;

    private void Awake()
    {
        volume = GetComponent<Volume>();
        if (volume == null)
        {
            volume = gameObject.AddComponent<Volume>();
        }

        volume.isGlobal = isGlobal;
        volume.priority = priority;
    }

    private void OnEnable()
    {
        if (isGlobal)
        {
            VolumeManager.instance.Register(volume, priority);
        }
    }

    private void OnDisable()
    {
        if (isGlobal)
        {
            VolumeManager.instance.Unregister(volume);
        }
    }
}
```

---

## 2. 内置后处理效果

URP提供的内置后处理效果：

| 效果 | 用途 |
|------|------|
| **Bloom** | 辉光效果 |
| **Tonemapping** | 色调映射 |
| **Vignette** | 暗角效果 |
| **ColorAdjustment** | 颜色调整 |
| **ChromaticAberration** | 色差 |
| **DepthOfField** | 景深效果 |
| **MotionBlur** | 运动模糊 |
| **ScreenSpaceAmbientOcclusion** | 环境光遮蔽 |

### 通过代码配置后处理

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class PostProcessManager : MonoBehaviour
{
    [Header("Post Processing")]
    [SerializeField] private VolumeProfile volumeProfile;

    private Bloom bloom;
    private ColorAdjustments colorAdjustments;
    private Vignette vignette;

    private void Start()
    {
        if (volumeProfile == null)
        {
            volumeProfile = ScriptableObject.CreateInstance<VolumeProfile>();
        }

        CreateBloom();
        CreateColorAdjustments();
        CreateVignette();
    }

    private void CreateBloom()
    {
        bloom = volumeProfile.Add<Bloom>();
        bloom.intensity.Override(0.5f);
        bloom.threshold.Override(1.0f);
        bloom.scatter.Override(0.5f);
    }

    private void CreateColorAdjustments()
    {
        colorAdjustments = volumeProfile.Add<ColorAdjustments>();
        colorAdjustments.postExposure.Override(1.0f);
        colorAdjustments.contrast.Override(1.0f);
        colorAdjustments.saturation.Override(1.0f);
    }

    private void CreateVignette()
    {
        vignette = volumeProfile.Add<Vignette>();
        vignette.intensity.Override(0.3f);
        vignette.roundness.Override(1.0f);
    }

    // 动态更新效果
    public void SetBloomIntensity(float intensity)
    {
        bloom?.intensity.Override(intensity);
    }

    public void SetVignetteIntensity(float intensity)
    {
        vignette?.intensity.Override(intensity);
    }
}
```

---

## 3. 自定义后处理（Renderer Feature）

通过`ScriptableRendererFeature`实现自定义后处理效果。

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// 自定义后处理效果
/// </summary>
public class CustomPostProcessFeature : ScriptableRendererFeature
{
    [System.Serializable]
    public class CustomSettings
    {
        public Material material;
        public float intensity = 1.0f;
        public Color tintColor = Color.white;
    }

    [SerializeField] private CustomSettings settings = new CustomSettings();

    private CustomPostProcessPass pass;

    public override void Create()
    {
        pass = new CustomPostProcessPass(settings);
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        renderer.EnqueuePass(pass);
    }

    private class CustomPostProcessPass : ScriptableRenderPass
    {
        private CustomSettings settings;
        private RenderTargetIdentifier source;
        private RenderTargetHandle tempTexture;

        public CustomPostProcessPass(CustomSettings settings)
        {
            this.settings = settings;
            renderPassEvent = RenderPassEvent.AfterRenderingTransparents;
        }

        public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
        {
            source = renderingData.cameraData.renderer.cameraColorTarget;

            var descriptor = renderingData.cameraData.cameraTargetDescriptor;
            descriptor.depthBufferBits = 0;
            cmd.GetTemporaryRT(tempTexture.id, descriptor);
        }

        public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
        {
            if (settings.material == null) return;

            CommandBuffer cmd = CommandBufferPool.Get("Custom Post Process");

            cmd.SetGlobalTexture("_MainTex", source);
            cmd.SetGlobalFloat("_Intensity", settings.intensity);
            cmd.SetGlobalColor("_TintColor", settings.tintColor);

            cmd.Blit(source, tempTexture.Identifier(), settings.material, 0);
            cmd.Blit(tempTexture.Identifier(), source);

            context.ExecuteCommandBuffer(cmd);
            CommandBufferPool.Release(cmd);
        }

        public override void OnCameraCleanup(CommandBuffer cmd)
        {
            cmd.ReleaseTemporaryRT(tempTexture.id);
        }
    }
}
```

---

## 4. 三消游戏后处理应用

```csharp
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// 三消游戏后处理控制器
/// </summary>
public class Match3PostProcessController : MonoBehaviour
{
    [Header("Post Processing")]
    [SerializeField] private VolumeProfile volumeProfile;

    private ColorAdjustments colorAdjustments;
    private Bloom bloom;
    private Vignette vignette;

    [Header("Game State Effects")]
    [SerializeField] private float normalSaturation = 1.0f;
    [SerializeField] private float comboSaturation = 1.5f;
    [SerializeField] private float gameOverVignette = 0.5f;
    [SerializeField] private float victoryBloom = 1.0f;

    private void Start()
    {
        InitializeEffects();
    }

    private void InitializeEffects()
    {
        if (volumeProfile == null) return;

        colorAdjustments = volumeProfile.Add<ColorAdjustments>();
        bloom = volumeProfile.Add<Bloom>();
        vignette = volumeProfile.Add<Vignette>();

        SetNormalState();
    }

    public void SetNormalState()
    {
        colorAdjustments?.saturation.Override(normalSaturation);
        bloom?.intensity.Override(0.3f);
        vignette?.intensity.Override(0.2f);
    }

    public void OnCombo(int comboCount)
    {
        float saturationBoost = normalSaturation + comboCount * 0.1f;
        colorAdjustments?.saturation.Override(Mathf.Clamp01(saturationBoost, 0, 2));
        bloom?.intensity.Override(0.5f + comboCount * 0.1f);
    }

    public void OnGameOver()
    {
        colorAdjustments?.saturation.Override(0);
        vignette?.intensity.Override(gameOverVignette);
        bloom?.intensity.Override(0);
    }

    public void OnVictory()
    {
        colorAdjustments?.saturation.Override(1.5f);
        bloom?.intensity.Override(victoryBloom);
        vignette?.intensity.Override(0.1f);
    }

    public void TransitionTo(float targetSaturation, float targetVignette, float duration)
    {
        StartCoroutine(TransitionCoroutine(targetSaturation, targetVignette, duration));
    }

    private IEnumerator TransitionCoroutine(float targetSaturation, float targetVignette, float duration)
    {
        float startSaturation = colorAdjustments.saturation.value;
        float startVignette = vignette.intensity.value;

        float elapsed = 0;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / duration;

            colorAdjustments?.saturation.Override(Mathf.Lerp(startSaturation, targetSaturation, t));
            vignette?.intensity.Override(Mathf.Lerp(startVignette, targetVignette, t));

            yield return null;
        }

        colorAdjustments?.saturation.Override(targetSaturation);
        vignette?.intensity.Override(targetVignette);
    }
}
```

---

## 5. 后处理最佳实践

```
┌─────────────────────────────────────────────────────────────┐
│                    后处理最佳实践                              │
│                                                             │
│  性能优化：                                                │
│  ├── 移动端减少效果数量（2-3个）                            │
│  ├── 避免每帧更新Volume参数                              │
│  ├── 使用On/Off控制效果启用                              │
│  └── 使用低分辨率LUT（256或512）                            │
│                                                             │
│  效果选择：                                                │
│  ├── 三消游戏：Bloom + ColorAdjustment + Vignette           │
│  ├── 竞技游戏：同上 + MotionBlur（可选）                        │
│  └── 恐怖游戏：ChromaticAberration + Vignette + ColorGrading │
│                                                             │
│  时机控制：                                                │
│  ├── UI显示时：暂时禁用后处理                              │
│  ├── 过场动画：平滑过渡效果                                │
│  └── 游戏暂停：保存当前效果状态                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| Volume系统 | URP的后处理配置框架 |
| Volume组件 | 挂载到相机，配置效果 |
| VolumeProfile | 效果容器，管理多个效果 |
| 内置效果 | Bloom, Tonemapping, Vignette等 |
| 自定义后处理 | ScriptableRendererFeature + ScriptableRenderPass |
| 动态控制 | 通过代码.Override()修改效果参数 |

### 常用后处理效果

| 效果 | 参数 | 用途 |
|------|------|------|
| Bloom | intensity, threshold, scatter | 辉光效果 |
| ColorAdjustments | postExposure, contrast, saturation | 颜色调整 |
| Vignette | intensity, roundness | 暗角效果 |
| Tonemapping | mode, toeLength | 色调映射 |
| ChromaticAberration | intensity | 色差（镜头效果） |

---

## 延伸阅读

- [URP Post Processing](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/post-processing.html)
- [Volume Framework](https://docs.unity3d.com/Packages/com.unity.render-pipelines.core@latest/manual/Volumes.html)
- [Custom Renderer Features](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/custom-renderer-features.html)
