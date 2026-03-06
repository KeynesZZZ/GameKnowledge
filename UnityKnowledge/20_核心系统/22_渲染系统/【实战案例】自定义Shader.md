---
title: 【实战案例】自定义Shader
tags: [Unity, 渲染, 渲染系统, Shader, 实战案例]
category: 核心系统/渲染系统
created: 2026-03-05 08:31
updated: 2026-03-05 08:31
description: 自定义Shader开发实战案例
unity_version: 2021.3+
---
# 自定义 Shader 实战

> Unity 自定义 Shader 基础语法和实战案例 `#渲染与Shader` `#自定义Shader` `#Shader编程`

## 概述

自定义 Shader 允许创建独特的视觉效果。Unity 使用 HLSL 语言编写 Shader，支持 Surface Shader 和 Vertex/Fragment Shader 两种方式。

## Surface Shader 基础

### 1. Surface Shader 模板

```hlsl
Shader "Custom/SurfaceShader"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Color", Color) = (1,1,1,1)
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _Color;

        struct Input
        {
            float2 uv_MainTex;
        };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb;
            o.Metallic = 0.0;
            o.Smoothness = 0.5;
            o.Alpha = c.a;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
```

### 2. 属性（Properties）

| 类型 | 声明 | Inspector 显示 |
|------|-------|---------------|
| **Color** | `_Color ("Color", Color)` | 颜色选择器 |
| **Range** | `_Range ("Range", Range(0,1)) = 0.5` | 滑块 |
| **Vector** | `_Vector ("Vector", Vector) = (0,0,0,0)` | 四维向量 |
| **Float** | `_Float ("Float", Float) = 0.0` | 浮点数 |
| **Int** | `_Int ("Int", Int) = 0` | 整数 |
| **Texture2D** | `_Tex ("Texture", 2D) = "white" {}` | 2D 纹理 |
| **Cube** | `_Cube ("Cubemap", Cube) = "" {}` | 立方体贴图 |

---

## 实战案例

### 1. 简单光照 Shader

```hlsl
Shader "Custom/SimpleLighting"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Color", Color) = (1,1,1,1)
        _Glossiness ("Glossiness", Range(0,1)) = 0.5
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _Color;
        float _Glossiness;

        struct Input
        {
            float2 uv_MainTex;
        };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb;
            o.Metallic = 0.0;
            o.Smoothness = _Glossiness;
            o.Alpha = c.a;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
```

### 2. 边缘发光 Shader

```hlsl
Shader "Custom/RimLighting"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _RimColor ("Rim Color", Color) = (0,1,0,1)
        _RimPower ("Rim Power", Range(0.1,10.0)) = 3.0
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _RimColor;
        float _RimPower;

        struct Input
        {
            float2 uv_MainTex;
            float3 viewDir;
        };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex);
            
            // 边缘发光计算
            half rim = 1.0 - saturate(dot(IN.viewDir, o.Normal));
            fixed3 rimColor = _RimColor.rgb * pow(rim, _RimPower);
            
            o.Albedo = c.rgb + rimColor;
            o.Alpha = c.a;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
```

### 3. 扫描线 Shader

```hlsl
Shader "Custom/Scanline"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _ScanlineColor ("Scanline Color", Color) = (0,0,0,1)
        _ScanlineSize ("Scanline Size", Range(1,20)) = 10.0
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Lambert

        sampler2D _MainTex;
        fixed4 _ScanlineColor;
        float _ScanlineSize;

        struct Input
        {
            float2 uv_MainTex;
            float4 screenPos;
        };

        void surf (Input IN, inout SurfaceOutput o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex);
            
            // 扫描线效果
            float scanline = step(fmod(IN.screenPos.y, _ScanlineSize), 1.0);
            c.rgb = lerp(c.rgb, _ScanlineColor.rgb * 0.2, scanline);
            
            o.Albedo = c.rgb;
            o.Alpha = c.a;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
```

### 4. 热变形 Shader

```hlsl
Shader "Custom/HeatDistortion"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _DistortionTex ("Distortion Texture", 2D) = "white" {}
        _DistortionStrength ("Distortion Strength", Range(0,0.5)) = 0.1
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Lambert

        sampler2D _MainTex;
        sampler2D _DistortionTex;
        float _DistortionStrength;

        struct Input
        {
            float2 uv_MainTex;
        };

        void surf (Input IN, inout SurfaceOutput o)
        {
            // 获取变形偏移
            fixed2 distortion = tex2D(_DistortionTex, IN.uv_MainTex).rg * 2.0 - 1.0;
            
            // 应用变形
            float2 distortedUV = IN.uv_MainTex + distortion * _DistortionStrength;
            
            fixed4 c = tex2D(_MainTex, distortedUV);
            o.Albedo = c.rgb;
            o.Alpha = c.a;
        }
        ENDCG
    }
    Fallback "Diffuse"
}
```

---

## 性能优化

### 1. 减少 Shader 复杂度

```hlsl
// ❌ 错误：复杂的计算
void surf (Input IN, inout SurfaceOutputStandard o)
{
    for (int i = 0; i < 100; i++)
    {
        // 复杂循环
    }
}

// ✅ 正确：预计算或简化
void surf (Input IN, inout SurfaceOutputStandard o)
{
    // 简化计算
    fixed rim = saturate(dot(IN.viewDir, o.Normal));
}
```

### 2. 使用 LOD

```hlsl
SubShader
{
    Tags { "RenderType"="Opaque" }
    LOD 200  // LOD 200

    CGPROGRAM
    #pragma surface surf Standard fullforwardshadows
    // ...
    ENDCG
}

SubShader
{
    Tags { "RenderType"="Opaque" }
    LOD 100  // LOD 100（简化版）

    CGPROGRAM
    #pragma surface surf Standard
    // 简化版本
    ENDCG
}
```

---

## 最佳实践

### DO ✅

- 根据效果选择合适的 Shader 类型
- 使用 Surface Shader 简化光照计算
- 使用 LOD 优化不同距离的 Shader
- 在 Inspector 中设置合理的默认值
- 为属性添加清晰的名称和描述
- 使用 fallback Shader 处理不支持的情况

### DON'T ❌

- 不要在不必要的地方使用复杂 Shader
- 不要忘记设置正确的 Tags
- 不要忽略移动平台优化
- 不要在 Shader 中使用不必要的循环
- 不要忘记设置 fallback

---

## 常见问题

### Q: Shader 不显示？
**A**: 
1. 检查 Shader 是否正确导入
2. 检查材质是否正确分配
3. 检查 SubShader 是否正确配置
4. 检查是否设置了 fallback

### Q: Shader 性能太差？
**A**: 
1. 简化计算逻辑
2. 使用 LOD
3. 减少纹理采样
4. 使用移动平台优化指令

---

## 相关链接

- [Shader基础语法](./【教程】HLSL与Shader基础.md)
- [URP管线配置](./【最佳实践】URP常用配置.md)

---

**适用版本**: Unity 2019.4+
**最后更新**: 2026-03-04
