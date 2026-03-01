# 常用Shader技术

> 第3课 | 渲染与图形模块

## 1. UV动画

UV动画是通过修改UV坐标实现流动效果的技术。

### 1.1 流动效果

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    // 基于时间的UV偏移
    float2 flowUV = input.uv + _Time.y * _FlowSpeed.xy * _FlowIntensity;

    half4 color = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, flowUV);
    return color;
}
```

### 1.2 双向流动（水流效果）

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    // 两层UV，不同速度和方向
    float2 uv1 = input.uv + _Time.y * float2(0.1, 0.05);
    float2 uv2 = input.uv + _Time.y * float2(-0.05, 0.1);

    half4 layer1 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv1);
    half4 layer2 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv2);

    // 混合两层
    half4 color = lerp(layer1, layer2, 0.5);
    return color;
}
```

### 1.3 UV旋转

```hlsl
// UV旋转函数
float2 RotateUV(float2 uv, float angle, float2 pivot)
{
    float2 delta = uv - pivot;

    float c = cos(angle);
    float s = sin(angle);

    float2 rotated = float2(
        delta.x * c - delta.y * s,
        delta.x * s + delta.y * c
    );

    return rotated + pivot;
}

half4 Fragment(Varyings input) : SV_Target
{
    // 围绕中心点旋转
    float2 rotatedUV = RotateUV(input.uv, _Time.y * 0.5, float2(0.5, 0.5));

    half4 color = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, rotatedUV);
    return color;
}
```

### 1.4 缩放动画

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    // 以中心为基准缩放
    float2 center = float2(0.5, 0.5);
    float scale = 1.0 + sin(_Time.y * 2.0) * 0.1;  // 0.9 ~ 1.1

    float2 scaledUV = center + (input.uv - center) * scale;

    half4 color = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, scaledUV);
    return color;
}
```

---

## 2. 溶解效果

溶解效果常用于物体消失、燃烧等效果。

### 2.1 基础溶解

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;
    half dissolveMask = SAMPLE_TEXTURE2D(_DissolveMap, sampler_DissolveMap, input.uv).r;

    // 溶解阈值
    half threshold = _DissolveAmount;

    // 计算边缘
    half edgeFactor = smoothstep(threshold, threshold + _DissolveEdge, dissolveMask);

    // 边缘颜色发光
    half3 edgeGlow = _EdgeColor.rgb * (1 - edgeFactor) * 2;
    baseColor.rgb = lerp(edgeGlow, baseColor.rgb, edgeFactor);

    // Alpha裁剪
    half alpha = step(threshold, dissolveMask);
    baseColor.a *= alpha;

    return baseColor;
}
```

### 2.2 带动画的溶解

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);

    // 使用时间偏移UV，让溶解图案流动
    float2 dissolveUV = input.uv + _Time.y * 0.1;
    half dissolveMask = SAMPLE_TEXTURE2D(_DissolveMap, sampler_DissolveMap, dissolveUV).r;

    half threshold = _DissolveAmount;
    half edgeFactor = smoothstep(threshold, threshold + _DissolveEdge, dissolveMask);

    // 边缘颜色渐变
    half3 edgeColor = lerp(_EdgeColor.rgb, _EdgeColor2.rgb, 1 - edgeFactor);
    half3 finalColor = lerp(edgeColor * 2, baseColor.rgb, edgeFactor);

    half alpha = step(threshold, dissolveMask);

    return half4(finalColor, baseColor.a * alpha);
}
```

### 2.3 三消游戏中的消除效果

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;

    // 使用纹理亮度作为溶解遮罩
    half luminance = dot(baseColor.rgb, half3(0.299, 0.587, 0.114));

    // 从外向内溶解（使用到中心的距离）
    float dist = distance(input.uv, float2(0.5, 0.5)) * 2;
    half mask = (1 - dist) * luminance;

    // 溶解进度
    half threshold = _DissolveProgress;
    half edgeWidth = 0.1;

    // 平滑边缘
    half edgeFactor = smoothstep(threshold - edgeWidth, threshold, mask);

    // 边缘颜色渐变
    half3 edgeColor = lerp(_EndColor.rgb, _StartColor.rgb, edgeFactor);
    baseColor.rgb = lerp(edgeColor * 3, baseColor.rgb, edgeFactor);

    // Alpha
    half alpha = step(threshold - edgeWidth * 0.5, mask);
    baseColor.a *= alpha * (1 - _DissolveProgress);

    return baseColor;
}
```

---

## 3. 边缘光与菲涅尔效果

### 3.1 菲涅尔效果

**菲涅尔效应**：物体边缘比中心更亮，观察角度越斜越亮。

```hlsl
// 菲涅尔公式
half Fresnel(half3 normal, half3 viewDir, half power)
{
    // NdotV: 法线与视线的点积
    half NdotV = saturate(dot(normal, viewDir));

    // Schlick菲涅尔近似
    half fresnel = pow(1 - NdotV, power);
    return fresnel;
}

// 使用示例
half4 Fragment(Varyings input) : SV_Target
{
    half3 normal = normalize(input.normalWS);
    half3 viewDir = normalize(_WorldSpaceCameraPos - input.positionWS);

    half fresnel = Fresnel(normal, viewDir, _FresnelPower);

    half3 finalColor = baseColor.rgb + _FresnelColor.rgb * fresnel * _FresnelIntensity;

    return half4(finalColor, baseColor.a);
}
```

### 3.2 2D边缘光（三消棋子）

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);

    // 计算到边缘的距离
    float2 center = float2(0.5, 0.5);
    float distFromCenter = distance(input.uv, center);
    float distFromEdge = 0.5 - distFromCenter;  // 越靠近边缘值越小

    // 边缘光
    half edgeFactor = 1 - smoothstep(0, _OutlineThickness, distFromEdge);
    half3 outline = _OutlineColor.rgb * edgeFactor * _OutlineIntensity;

    // 高亮效果
    half3 highlight = half3(1, 1, 1) * _Highlight * 0.3;

    // 组合
    half3 finalColor = baseColor.rgb * _BaseColor.rgb + outline + highlight;

    return half4(finalColor, baseColor.a * _BaseColor.a);
}
```

---

## 4. 纹理混合

### 4.1 基础混合

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 base = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);
    half4 overlay = SAMPLE_TEXTURE2D(_OverlayMap, sampler_OverlayMap, input.uv);
    half mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, input.uv).r;

    // 使用遮罩混合
    half blendFactor = mask * _BlendAmount;
    half4 color = lerp(base, overlay, blendFactor);

    return color * _BaseColor;
}
```

### 4.2 高度混合

```hlsl
// 根据高度图混合两种纹理
half4 HeightBlend(half4 layer1, half4 layer2, half height1, half height2, half blendFactor)
{
    half h1 = height1 * (1 - blendFactor);
    half h2 = height2 * blendFactor;

    half weight1 = max(h1 - h2, 0);
    half weight2 = max(h2 - h1, 0);
    half total = weight1 + weight2;

    if (total > 0.001)
    {
        weight1 /= total;
        weight2 /= total;
    }

    return layer1 * weight1 + layer2 * weight2;
}
```

---

## 5. 闪烁与脉冲效果

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;

    if (_EnablePulse > 0.5)
    {
        // 正弦波脉冲 (0~1)
        half pulse = sin(_Time.y * _PulseSpeed * 6.28) * 0.5 + 0.5;

        // 应用脉冲到颜色
        half3 pulseEffect = _PulseColor.rgb * pulse * _PulseIntensity;
        baseColor.rgb += pulseEffect;

        // 可选：同时调整亮度
        baseColor.rgb *= 1 + pulse * _PulseIntensity * 0.5;
    }

    return baseColor;
}
```

---

## 6. 技巧总结

### UV动画

| 效果 | 公式 |
|------|------|
| 流动 | `uv + _Time.y * speed` |
| 旋转 | `RotateUV(uv, angle, pivot)` |
| 缩放 | `center + (uv - center) * scale` |

### 溶解效果

| 函数 | 用途 |
|------|------|
| `smoothstep(a, b, x)` | 平滑边缘 |
| `step(a, x)` | 硬边缘 |
| `lerp(edge, base, factor)` | 边缘颜色混合 |

### 边缘光

| 场景 | 方法 |
|------|------|
| 3D物体 | `pow(1 - NdotV, power)` |
| 2D精灵 | `distance(uv, center)` |

### 脉冲效果

```hlsl
// 标准脉冲 (0~1)
half pulse = sin(_Time.y * speed * 6.28) * 0.5 + 0.5;

// 双向脉冲 (-1~1)
half pulse2 = sin(_Time.y * speed * 6.28);
```

---

## 本课小结

| 技术 | 核心公式 | 用途 |
|------|----------|------|
| UV流动 | `uv + _Time.y * speed` | 流动效果 |
| UV旋转 | `RotateUV(uv, angle, pivot)` | 旋转效果 |
| 溶解 | `smoothstep(threshold, threshold+edge, mask)` | 消除效果 |
| 菲涅尔 | `pow(1 - NdotV, power)` | 边缘发光 |
| 脉冲 | `sin(_Time.y * speed) * 0.5 + 0.5` | 闪烁效果 |

---

## 延伸阅读

- [Unity Shader Lab](https://docs.unity3d.com/Manual/SL-Reference.html)
- [Shader Graph Examples](https://unity.com/features/shader-graph)
- [Book of Shaders](https://thebookofshaders.com/)
