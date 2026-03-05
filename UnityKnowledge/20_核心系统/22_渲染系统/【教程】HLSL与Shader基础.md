---
title: 【教程】HLSL与Shader基础
tags: [Unity, 渲染系统, HLSL, 教程]
category: 核心系统/渲染系统
created: 2026-03-05 08:31
updated: 2026-03-05 08:31
description: HLSL语言与Shader编程基础
unity_version: 2021.3+
---
# HLSL与Shader基础

> 第2课 | 渲染与图形模块

## 1. 什么是Shader？

**Shader**是运行在GPU上的小程序，用于计算每个顶点和像素的最终颜色。

```
┌─────────────────────────────────────────────────────────────┐
│                    Shader 流水线                             │
│                                                             │
│   CPU                      GPU                              │
│   ┌─────────┐             ┌─────────────────────────────┐  │
│   │ 3D模型  │             │                             │  │
│   │ 纹理    │  ─────────→ │  ┌─────────────────────┐   │  │
│   │ 材质    │   数据传输   │  │   顶点着色器        │   │  │
│   │ 参数    │             │  │   (Vertex Shader)   │   │  │
│   └─────────┘             │  └──────────┬──────────┘   │  │
│                           │             │              │  │
│                           │             ↓              │  │
│                           │  ┌─────────────────────┐   │  │
│                           │  │   光栅化            │   │  │
│                           │  │   (Rasterization)   │   │  │
│                           │  └──────────┬──────────┘   │  │
│                           │             │              │  │
│                           │             ↓              │  │
│                           │  ┌─────────────────────┐   │  │
│                           │  │   片元着色器        │   │  │
│                           │  │   (Fragment Shader) │   │  │
│                           │  └──────────┬──────────┘   │  │
│                           │             │              │  │
│                           │             ↓              │  │
│                           │  ┌─────────────────────┐   │  │
│                           │  │   最终像素颜色      │   │  │
│                           │  └─────────────────────┘   │  │
│                           └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. HLSL基础语法

### 基本数据类型

```hlsl
// ============ 标量类型 ============
float   // 32位浮点数（最常用）
half    // 16位浮点数（移动端优化）
fixed   // 11位定点数（已过时）
int     // 整数
bool    // 布尔值

// ============ 向量类型 ============
float2  // 2D向量 {
    return float2(1.0, 0.5);
}

// UV坐标（float2）
float2 uv = input.uv;
```

### 常用内置函数

```hlsl
// ============ 数学函数 ============
abs(x)           // 绝对值
sqrt(x)          // 平方根
pow(x, y)        // x的y次幂
exp(x)           // e的x次幂
log(x)           // 自然对数

// ============ 三角函数 ============
sin(x), cos(x), tan(x)
asin(x), acos(x), atan(x)

// ============ 取整函数 ============
floor(x)         // 向下取整
ceil(x)          // 向上取整
round(x)         // 四舍五入
frac(x)          // 小数部分
trunc(x)         // 截断小数

// ============ 插值与平滑 ============
lerp(a, b, t)              // 线性插值：a + (b-a) * t
smoothstep(min, max, x)    // 平滑插值
step(a, x)                 // x >= a ? 1 : 0

// ============ 向量运算 ============
dot(a, b)        // 点积
cross(a, b)      // 叉积（仅float3）
length(v)        // 向量长度
normalize(v)     // 归一化
distance(a, b)   // 两点距离
reflect(i, n)    // 反射向量
refract(i, n, ratio)  // 折射向量

// ============ 限制函数 ============
saturate(x)      // 限制在0-1范围
clamp(x, min, max)  // 限制在指定范围
min(a, b)        // 最小值
max(a, b)        // 最大值
```

---

## 3. URP Shader结构

### 完整的URP Shader模板

```hlsl
Shader "Custom/URPBasic"
{
    Properties
    {
        _BaseMap ("Base Map", 2D) = "white" {}
        _BaseColor ("Base Color", Color) = (1, 1, 1, 1)
        _Gloss ("Gloss", Range(0, 1)) = 0.5
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Opaque"
            "RenderPipeline" = "UniversalPipeline"
        }

        LOD 100

        Pass
        {
            Name "UniversalForward"
            Tags { "LightMode" = "UniversalForward" }

            HLSLPROGRAM
            #pragma vertex Vertex
            #pragma fragment Fragment

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
                float3 normalOS : NORMAL;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float3 positionWS : TEXCOORD2;
            };

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half _Gloss;
            CBUFFER_END

            Varyings Vertex(Attributes input)
            {
                Varyings output;

                VertexPositionInputs vertexInput = GetVertexPositionInputs(input.positionOS.xyz);
                VertexNormalInputs normalInput = GetVertexNormalInputs(input.normalOS);

                output.positionCS = vertexInput.positionCS;
                output.positionWS = vertexInput.positionWS;
                output.normalWS = normalInput.normalWS;
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);

                return output;
            }

            half4 Fragment(Varyings input) : SV_Target
            {
                half4 texColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);
                half4 color = texColor * _BaseColor;
                return color;
            }

            ENDHLSL
        }
    }
}
```

### Shader结构解析

```
Shader "Name"
├── Properties          ← Inspector显示的属性
│   ├── _BaseMap        ← 纹理属性
│   ├── _BaseColor      ← 颜色属性
│   └── _Gloss          ← 数值属性
│
└── SubShader           ← 渲染方案
    ├── Tags            ← 渲染标签
    │   ├── RenderType
    │   └── RenderPipeline = "UniversalPipeline"
    │
    └── Pass            ← 渲染通道
        ├── Name        ← 通道名称
        ├── Tags        ← 通道标签（LightMode）
        │
        └── HLSLPROGRAM
            ├── Attributes   ← 顶点输入
            ├── Varyings     ← 传递数据
            ├── 属性声明
            ├── Vertex       ← 顶点着色器
            └── Fragment     ← 片元着色器
```

---

## 4. 顶点着色器详解

**作用**：将3D顶点转换到2D屏幕坐标

```hlsl
struct Attributes
{
    float4 positionOS : POSITION;     // 物体空间坐标
    float2 uv : TEXCOORD0;            // UV坐标
    float3 normalOS : NORMAL;         // 法线
    float4 tangentOS : TANGENT;       // 切线
    float4 color : COLOR;             // 顶点颜色
};

struct Varyings
{
    float4 positionCS : SV_POSITION;  // 裁剪空间坐标（必须）
    float2 uv : TEXCOORD0;            // UV坐标
    float3 normalWS : TEXCOORD1;      // 世界空间法线
    float3 positionWS : TEXCOORD2;    // 世界空间坐标
    float fogFactor : TEXCOORD3;      // 雾因子
};

Varyings Vertex(Attributes input)
{
    Varyings output = (Varyings)0;

    // ========== 坐标转换 ==========
    VertexPositionInputs vertexInput = GetVertexPositionInputs(input.positionOS.xyz);
    output.positionCS = vertexInput.positionCS;
    output.positionWS = vertexInput.positionWS;

    // ========== 法线转换 ==========
    VertexNormalInputs normalInput = GetVertexNormalInputs(input.normalOS);
    output.normalWS = normalInput.normalWS;

    // ========== UV变换 ==========
    output.uv = TRANSFORM_TEX(input.uv, _BaseMap);

    // ========== 雾计算 ==========
    output.fogFactor = ComputeFogFactor(output.positionCS.z);

    return output;
}
```

### URP坐标转换函数

```hlsl
struct VertexPositionInputs
{
    float3 positionWS;    // 世界空间
    float3 positionVS;    // 视图空间
    float4 positionCS;    // 裁剪空间
    float4 positionNDC;   // 归一化设备坐标
};

struct VertexNormalInputs
{
    float3 normalWS;      // 世界空间法线
    float3 tangentWS;     // 世界空间切线
    float3 bitangentWS;   // 世界空间副切线
};
```

---

## 5. 片元着色器详解

**作用**：计算每个像素的最终颜色

```hlsl
half4 Fragment(Varyings input) : SV_Target
{
    // ========== 纹理采样 ==========
    half4 texColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);

    // ========== 基础颜色 ==========
    half4 baseColor = texColor * _BaseColor;

    // ========== 光照计算 ==========
    Light mainLight = GetMainLight();

    // 计算漫反射
    half3 normal = normalize(input.normalWS);
    half NdotL = saturate(dot(normal, mainLight.direction));
    half3 diffuse = mainLight.color * NdotL;

    // 最终颜色
    half3 finalColor = baseColor.rgb * (diffuse + half3(0.1, 0.1, 0.1));

    // ========== 雾效果 ==========
    finalColor = MixFog(finalColor, input.fogFactor);

    return half4(finalColor, baseColor.a);
}
```

### 常用片元操作

```hlsl
// ========== 纹理采样 ==========
half4 color = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv);

// ========== 颜色混合 ==========
half3 result = lerp(colorA.rgb, colorB.rgb, t);  // 线性插值
half3 result = colorA.rgb * colorB.rgb;          // 正片叠底
half3 result = min(colorA.rgb + colorB.rgb, 1);  // 滤色

// ========== Alpha裁剪 ==========
half alpha = texColor.a * _BaseColor.a;
clip(alpha - _Cutoff);  // 低于Cutoff的像素被丢弃

// ========== 雾效果 ==========
finalColor = MixFog(finalColor, input.fogFactor);
```

---

## 6. Properties属性类型

```hlsl
Properties
{
    // ========== 数值类型 ==========
    _Float ("Float", Float) = 0.5
    _Range ("Range", Range(0, 1)) = 0.5
    _Int ("Int", Int) = 1

    // ========== 颜色类型 ==========
    _Color ("Color", Color) = (1, 0, 0, 1)

    // ========== 向量类型 ==========
    _Vector ("Vector", Vector) = (1, 0, 0, 0)

    // ========== 纹理类型 ==========
    _MainTex ("Texture", 2D) = "white" {}
    _NormalMap ("Normal Map", 2D) = "bump" {}
    _CubeMap ("Cube Map", Cube) = "" {}
    _3DTex ("3D Texture", 3D) = "" {}
}
```

### HLSL中声明属性

```hlsl
// 纹理声明（URP方式）
TEXTURE2D(_MainTex);
SAMPLER(sampler_MainTex);

// 常量缓冲区（SRP Batcher需要）
CBUFFER_START(UnityPerMaterial)
    float4 _MainTex_ST;      // 纹理缩放和偏移
    half4 _Color;
    half _Float;
    half _Range;
    int _Int;
    float4 _Vector;
CBUFFER_END

// 使用纹理
half4 color = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv);

// 使用_ST进行UV变换
float2 transformedUV = TRANSFORM_TEX(uv, _MainTex);
```

---

## 7. 三消游戏Shader实战：棋盘格子

```hlsl
Shader "Match3/GemShader"
{
    Properties
    {
        _BaseMap ("Base Map", 2D) = "white" {}
        _BaseColor ("Base Color", Color) = (1, 1, 1, 1)

        // 高亮效果
        _HighlightIntensity ("Highlight Intensity", Range(0, 1)) = 0.3
        _HighlightColor ("Highlight Color", Color) = (1, 1, 1, 1)

        // 选中效果
        _Selected ("Selected", Float) = 0
        _SelectedPulse ("Selected Pulse", Float) = 0

        // 消除效果
        _Dissolve ("Dissolve", Range(0, 1)) = 0
        _DissolveColor ("Dissolve Color", Color) = (1, 0.5, 0, 1)
        _DissolveEdge ("Dissolve Edge", Range(0, 0.5)) = 0.1
    }

    SubShader
    {
        Tags
        {
            "RenderType" = "Transparent"
            "Queue" = "Transparent"
            "RenderPipeline" = "UniversalPipeline"
        }

        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex Vertex
            #pragma fragment Fragment

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float2 uv : TEXCOORD0;
                float4 color : COLOR;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float4 vertexColor : TEXCOORD1;
            };

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half _HighlightIntensity;
                half4 _HighlightColor;
                half _Selected;
                half _SelectedPulse;
                half _Dissolve;
                half4 _DissolveColor;
                half _DissolveEdge;
            CBUFFER_END

            Varyings Vertex(Attributes input)
            {
                Varyings output;

                VertexPositionInputs vertexInput = GetVertexPositionInputs(input.positionOS.xyz);
                output.positionCS = vertexInput.positionCS;
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                output.vertexColor = input.color;

                // 选中时的缩放动画
                if (_Selected > 0.5)
                {
                    float scale = 1.0 + sin(_SelectedPulse * 6.28) * 0.1;
                    output.positionCS.xy *= scale;
                }

                return output;
            }

            half4 Fragment(Varyings input) : SV_Target
            {
                half4 texColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv);
                half4 baseColor = texColor * _BaseColor * input.vertexColor;

                // 高亮效果
                half3 highlight = _HighlightColor.rgb * _HighlightIntensity;
                baseColor.rgb += highlight;

                // 选中效果 - 边缘发光
                if (_Selected > 0.5)
                {
                    float2 center = float2(0.5, 0.5);
                    float dist = distance(input.uv, center);
                    float edge = smoothstep(0.3, 0.5, dist);
                    baseColor.rgb += _HighlightColor.rgb * edge * 0.5
                        * (sin(_SelectedPulse * 6.28) * 0.5 + 0.5);
                }

                // 溶解效果
                if (_Dissolve > 0.001)
                {
                    half dissolveMask = texColor.a;
                    half threshold = _Dissolve;

                    half edge = smoothstep(threshold - _DissolveEdge, threshold, dissolveMask);
                    baseColor.rgb = lerp(_DissolveColor.rgb * 2, baseColor.rgb, edge);

                    half alpha = step(threshold, dissolveMask);
                    baseColor.a *= alpha;
                }

                return baseColor;
            }

            ENDHLSL
        }
    }
}
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| Shader | 运行在GPU上的小程序 |
| HLSL | Unity URP使用的着色器语言 |
| 顶点着色器 | 转换3D坐标到2D屏幕 |
| 片元着色器 | 计算每个像素的最终颜色 |
| Properties | Inspector中显示的属性 |
| CBUFFER | SRP Batcher需要的常量缓冲区 |

### 常用函数速查

| 函数 | 用途 |
|------|------|
| `lerp(a,b,t)` | 线性插值 |
| `saturate(x)` | 限制在0-1范围 |
| `smoothstep(a,b,x)` | 平滑插值 |
| `dot(a,b)` | 点积 |
| `normalize(v)` | 归一化 |
| `SAMPLE_TEXTURE2D` | 纹理采样 |
| `TRANSFORM_TEX` | UV变换 |

---

## 延伸阅读

- [Unity Shader Reference](https://docs.unity3d.com/Manual/SL-Reference.html)
- [URP Shader Templates](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/shaders-in-universal.html)
- [HLSL Documentation](https://docs.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl)
