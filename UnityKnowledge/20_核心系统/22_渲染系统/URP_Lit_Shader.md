# URP Lit Shader

> 第4课 | 渲染与图形模块

## 1. 光照基础概念

### 光照模型组成

```
最终颜色 = 环境光 + 漫反射 + 高光反射 + 自发光

┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│Ambient  │ + │Diffuse  │ + │Specular │ + │Emission │
│ 环境光  │   │ 漫反射  │   │ 高光    │   │ 自发光  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘

环境光：模拟间接光照（天空、地面反射）
漫反射：Lambert模型，N·L
高光：Blinn-Phong或PBR，反射高光
自发光：物体自身发光
```

### 核心向量

```
                ┌─────────┐
                │   Light │
                │ Direction│
                └────┬────┘
                     │
                     ↓
┌─────────┐      ┌─────────┐
│  View   │ ←─── │ Surface │
│Direction│      │  Normal │
└─────────┘      └─────────┘

N = 法线 (Normal)
L = 光线方向 (Light Direction)
V = 视线方向 (View Direction)
H = 半角向量 (Half Vector) = normalize(L + V)
```

---

## 2. URP光照系统

### 获取光照信息

```hlsl
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

// 获取主光源
Light mainLight = GetMainLight();

// 主光源属性
half3 lightColor = mainLight.color;           // 光源颜色
half3 lightDir = mainLight.direction;         // 光源方向
half lightAttenuation = mainLight.distanceAttenuation;  // 距离衰减
half shadowAttenuation = mainLight.shadowAttenuation;   // 阴影衰减

// 获取额外光源（点光源、聚光灯）
uint additionalLightsCount = GetAdditionalLightsCount();
for (uint i = 0; i < additionalLightsCount; i++)
{
    Light light = GetAdditionalLight(i, positionWS);
    // 处理额外光源...
}
```

### URP光照函数

```hlsl
// 初始化输入数据
InputData inputData = (InputData)0;
inputData.positionWS = positionWS;
inputData.normalWS = normalWS;
inputData.viewDirectionWS = viewDir;
inputData.shadowCoord = TransformWorldToShadowCoord(positionWS);

// 初始化表面数据
SurfaceData surfaceData = (SurfaceData)0;
surfaceData.albedo = baseColor.rgb;
surfaceData.metallic = metallic;
surfaceData.smoothness = smoothness;
surfaceData.normalTS = normalMap;
surfaceData.emission = emission;
surfaceData.occlusion = occlusion;

// URP内置PBR光照
half4 color = UniversalFragmentPBR(inputData, surfaceData);
```

---

## 3. 简化的光照模型

### 3.1 Lambert漫反射

```hlsl
// Lambert漫反射
half3 LambertDiffuse(half3 lightColor, half3 lightDir, half3 normal)
{
    half NdotL = saturate(dot(normal, lightDir));
    return lightColor * NdotL;
}
```

### 3.2 Blinn-Phong高光

```hlsl
// Blinn-Phong高光
half3 BlinnPhongSpecular(half3 lightColor, half3 lightDir, half3 viewDir, half3 normal, half gloss)
{
    half3 halfDir = normalize(lightDir + viewDir);
    half NdotH = saturate(dot(normal, halfDir));

    // gloss越大，高光越集中
    half specularPower = exp2(gloss * 10);  // 1 ~ 1024
    half specular = pow(NdotH, specularPower);

    return lightColor * specular;
}
```

### 3.3 完整的Blinn-Phong光照

```hlsl
half3 BlinnPhongLighting(
    half3 albedo,
    half3 normal,
    half3 viewDir,
    half3 lightColor,
    half3 lightDir,
    half gloss,
    half specularIntensity)
{
    // 漫反射
    half3 diffuse = LambertDiffuse(lightColor, lightDir, normal);

    // 高光
    half3 specular = BlinnPhongSpecular(lightColor, lightDir, viewDir, normal, gloss);
    specular *= specularIntensity;

    // 环境光
    half3 ambient = half3(0.1, 0.1, 0.1);

    // 最终颜色
    half3 color = albedo * (diffuse + ambient) + specular;

    return color;
}
```

---

## 4. 三消游戏简化Shader

```hlsl
Shader "Match3/GemSimpleLit"
{
    Properties
    {
        _BaseMap ("Base Map", 2D) = "white" {}
        _BaseColor ("Base Color", Color) = (1, 1, 1, 1)

        // 简单光照参数
        _LightIntensity ("Light Intensity", Range(0, 2)) = 1
        _LightColor ("Light Color", Color) = (1, 1, 1, 1)
        _LightDirection ("Light Direction", Vector) = (0.5, 1, 0.5, 0)

        // 高光
        _SpecularColor ("Specular Color", Color) = (1, 1, 1, 1)
        _Gloss ("Gloss", Range(0, 1)) = 0.5
        _SpecularIntensity ("Specular Intensity", Range(0, 1)) = 0.5

        // 边缘光
        _RimColor ("Rim Color", Color) = (0.5, 0.8, 1, 1)
        _RimPower ("Rim Power", Range(1, 10)) = 3
        _RimIntensity ("Rim Intensity", Range(0, 1)) = 0.5
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            HLSLPROGRAM
            #pragma vertex Vertex
            #pragma fragment Fragment

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_BaseMap);
            SAMPLER(sampler_BaseMap);

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4 _BaseColor;
                half _LightIntensity;
                half4 _LightColor;
                half3 _LightDirection;
                half4 _SpecularColor;
                half _Gloss;
                half _SpecularIntensity;
                half4 _RimColor;
                half _RimPower;
                half _RimIntensity;
            CBUFFER_END

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
                half3 normalWS : TEXCOORD1;
                half3 viewDirWS : TEXCOORD2;
            };

            Varyings Vertex(Attributes input)
            {
                Varyings output;

                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS = TransformWorldToHClip(positionWS);
                output.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                output.normalWS = TransformObjectToWorldNormal(input.normalOS);
                output.viewDirWS = normalize(_WorldSpaceCameraPos - positionWS);

                return output;
            }

            half4 Fragment(Varyings input) : SV_Target
            {
                // 基础颜色
                half4 baseColor = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;

                // 归一化
                half3 normal = normalize(input.normalWS);
                half3 viewDir = normalize(input.viewDirWS);
                half3 lightDir = normalize(_LightDirection);

                // ===== 漫反射 =====
                half NdotL = saturate(dot(normal, lightDir));
                half3 diffuse = _LightColor.rgb * NdotL * _LightIntensity;

                // ===== 高光 (Blinn-Phong) =====
                half3 halfDir = normalize(lightDir + viewDir);
                half NdotH = saturate(dot(normal, halfDir));
                half specularPower = exp2(_Gloss * 8);
                half specular = pow(NdotH, specularPower) * _SpecularIntensity;
                half3 specularColor = _SpecularColor.rgb * specular;

                // ===== 边缘光 (菲涅尔) =====
                half NdotV = saturate(dot(normal, viewDir));
                half rim = pow(1 - NdotV, _RimPower) * _RimIntensity;
                half3 rimColor = _RimColor.rgb * rim;

                // ===== 最终颜色 =====
                half3 ambient = half3(0.2, 0.2, 0.2);
                half3 finalColor = baseColor.rgb * (diffuse + ambient) + specularColor + rimColor;

                return half4(finalColor, baseColor.a);
            }
            ENDHLSL
        }
    }
}
```

---

## 5. 光照技巧总结

### 光照计算流程

```
1. 准备数据
   ├── 采样纹理 (Albedo, Normal)
   ├── 计算法线 (World Space Normal)
   └── 计算视线方向 (View Direction)

2. 光照计算
   ├── 获取光源信息 (GetMainLight)
   ├── 漫反射: N·L
   ├── 高光: pow(N·H, gloss)
   └── 阴影: shadowAttenuation

3. 额外效果
   ├── 环境光遮蔽 (Occlusion)
   ├── 菲涅尔边缘光 (Rim)
   └── 自发光 (Emission)

4. 组合输出
   finalColor = albedo * (diffuse + ambient) + specular + emission + rim
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| 光照模型 | 环境光 + 漫反射 + 高光 + 自发光 |
| URP光照 | `GetMainLight()`, `UniversalFragmentPBR` |
| 漫反射 | `NdotL = saturate(dot(N, L))` |
| 高光 | Blinn-Phong: `pow(NdotH, gloss)` |
| 边缘光 | 菲涅尔: `pow(1 - NdotV, power)` |
| 多Pass | Forward + ShadowCaster + DepthOnly |

### 常用光照函数

| 函数 | 用途 |
|------|------|
| `GetMainLight()` | 获取主光源 |
| `GetAdditionalLight(i, pos)` | 获取额外光源 |
| `UniversalFragmentPBR` | URP PBR光照 |
| `TransformWorldToShadowCoord` | 阴影坐标转换 |
| `LambertDiffuse` | 漫反射计算 |
| `BlinnPhongSpecular` | 高光计算 |

---

## 延伸阅读

- [URP Lighting](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/lighting.html)
- [Unity PBR](https://docs.unity3d.com/Manual/StandardShaderPhysicallyBasedRendering.html)
- [Blinn-Phong Model](https://en.wikipedia.org/wiki/Blinn%E2%80%93Phong_reflection_model)
