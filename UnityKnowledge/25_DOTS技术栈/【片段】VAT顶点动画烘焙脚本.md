---
title: 【片段】VAT 顶点动画烘焙脚本
tags: ["Unity", "DOTS", "DOTS技术栈", "Entities Graphics", "动画", "VAT", "编辑器扩展", "代码片段", "片段"]
category: DOTS技术栈
created: "2026-06-30"
updated: "2026-06-30"
description: 可复用的 VAT 烘焙 Editor 脚本骨架——逐帧 BakeMesh 采样写 RGBAFloat 纹理 + LUT，配套 shader 采样端。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【笔记】大规模单位动画方案]]"
  - "[[【笔记】同屏大规模单位渲染方案]]"
  - "[[【笔记】Entities 1.4 与 Entities Graphics 1.4 官方文档]]"
related: ["[[【笔记】大规模单位动画方案]]", "[[【笔记】同屏大规模单位渲染方案]]", "[[【笔记】大规模单位AI决策与寻路]]", "[[【实战案例】10w单位渲染与动画最小Demo]]", "[[DOTS专题索引]]"]
---

# 【片段】VAT 顶点动画烘焙脚本

> 承 [[【笔记】大规模单位动画方案]]。给出一套**可直接改用**的 VAT 烘焙 Editor 脚本骨架：把 SkinnedMesh + 多 AnimationClip 烘焙成一张 RGBAFloat 纹理 + 一个 LUT，配套 shader 采样端。

## 烘焙思路（先理清数据布局）

```
VAT 纹理（RGBAFloat，精度 32bit/通道）
  宽 = 单个 mesh 的顶点数（vertexCount）
  高 = 所有动画总采样帧数（totalFrames）
  每像素 = 一个顶点的一帧位置 (x,y,z) + 占位/法线 (w)

LUT（ScriptableObject）
  每段动画一条记录：
    { name, meshId, startFrame, frameCount, fps, loop }

运行时：单位传 (meshId, animIndex, animTime)
  → shader 查 LUT 得 (startFrame, fps, loop)
  → frame = animTime * fps + startFrame
  → tex2Dlod(VAT, float2(vertexId/width, frame/height))
```

⚠️ **VAT 要求同纹理内 mesh 顶点数一致**。12 种怪物 mesh 不同时：①把不同 mesh 各烘一张 VAT（纹理数组按 meshId 索引），或②把所有 mesh 顶点数补齐到同一上界（浪费但单纹理）。

---

## 一、烘焙 Editor 脚本（C#）

> 放 `Editor/` 目录。MenuItem 触发，选中带 SkinnedMeshRenderer 的 GameObject，配置 clip 列表与采样参数。

```csharp
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

/// <summary>
/// VAT 烘焙器：把 SkinnedMeshRenderer + 多 AnimationClip 烘焙成顶点动画纹理 + LUT。
/// 骨架代码，按项目需求调整（多 mesh、法线、half 精度、归一化等）。
/// </summary>
public class VatBaker : EditorWindow
{
    [MenuItem("Tools/DOTS/VAT Baker")]
    static void Open() => GetWindow<VatBaker>("VAT Baker");

    private GameObject _target;           // 带 SkinnedMeshRenderer + Animator 的预制体
    private List<AnimationClip> _clips = new();
    private int _fps = 30;
    private string _outputDir = "Assets/VAT";

    private void OnGUI()
    {
        _target = (GameObject)EditorGUILayout.ObjectField("Target", _target, typeof(GameObject), true);
        _fps = EditorGUILayout.IntField("Sample FPS", _fps);
        _outputDir = EditorGUILayout.TextField("Output Dir", _outputDir);

        GUILayout.Label("Animation Clips (顺序即 animIndex)");
        for (int i = 0; i < _clips.Count; i++)
        {
            _clips[i] = (AnimationClip)EditorGUILayout.ObjectField(
                $"Clip {i}", _clips[i], typeof(AnimationClip), false);
        }
        if (GUILayout.Button("+ Clip")) _clips.Add(null);

        if (GUILayout.Button("Bake") && _target != null)
            BakeAll();
    }

    private void BakeAll()
    {
        var smr = _target.GetComponent<SkinnedMeshRenderer>();
        if (smr == null) { Debug.LogError("需要 SkinnedMeshRenderer"); return; }

        // 1) 预采样每段帧数，得总帧数
        var entries = new List<(AnimationClip clip, int frames)>();
        int totalFrames = 0, maxVerts = 0;
        foreach (var clip in _clips)
        {
            if (clip == null) continue;
            int frames = Mathf.CeilToInt(clip.length * _fps);
            entries.Add((clip, frames));
            totalFrames += frames;
        }
        Mesh probe = new Mesh();
        smr.BakeMesh(probe);
        maxVerts = probe.vertexCount;
        if (maxVerts == 0 || totalFrames == 0) { Debug.LogError("采样失败"); return; }

        // 2) 分配像素缓冲（每顶点每帧一像素）
        Color[] pixels = new Color[maxVerts * totalFrames];
        var lut = ScriptableObject.CreateInstance<VatLUT>();
        lut.entries = new List<VatLUT.Entry>();
        lut.vertexCount = maxVerts;
        lut.frameCount = totalFrames;
        lut.textureWidth = maxVerts;
        lut.textureHeight = totalFrames;

        // 3) 逐 clip → 逐帧采样 BakeMesh → 写像素
        int startFrame = 0, meshId = 0;
        Mesh baked = new Mesh();
        AnimationMode.BeginSampling();
        try
        {
            foreach (var (clip, frames) in entries)
            {
                for (int f = 0; f < frames; f++)
                {
                    float t = (frames <= 1 ? 0f : (clip.length * f / (frames - 1)));
                    // 关键：采样 clip 到指定时间，再 BakeMesh
                    AnimationMode.SampleAnimationClip(_target, clip, t);
                    smr.BakeMesh(baked);
                    Vector3[] v = baked.vertices;   // 顶点位置（按需另取 normals）

                    int frameIndex = startFrame + f;
                    for (int v_i = 0; v_i < maxVerts; v_i++)
                    {
                        // 约定：位置存到网格 bounds 归一化？这里直接存世界单位（float 纹理精度够）
                        Vector3 p = v_i < v.Length ? v[v_i] : Vector3.zero;
                        pixels[frameIndex * maxVerts + v_i] = new Color(p.x, p.y, p.z, 0f);
                    }
                }
                lut.entries.Add(new VatLUT.Entry
                {
                    name = clip.name,
                    meshId = meshId,
                    startFrame = startFrame,
                    frameCount = frames,
                    fps = _fps,
                    loop = !clip.isLooping ? true : clip.isLooping   // 按需：idle/move loop，attack/death 不 loop
                });
                startFrame += frames;
            }
        }
        finally { AnimationMode.EndSampling(); }

        // 4) 写纹理（RGBAFloat，运行时无纹理压缩损失）
        if (!AssetDatabase.IsValidFolder(_outputDir)) AssetDatabase.CreateFolder("Assets", "VAT");
        var tex = new Texture2D(maxVerts, totalFrames, TextureFormat.RGBAFloat, false, true);
        tex.SetPixels(pixels);
        tex.Apply();
        var bytes = tex.GetRawTextureData();
        System.IO.File.WriteAllBytes($"{_outputDir}/VatTex_{_target.name}.asset.raw", bytes); // 简化：实际存为 .asset
        AssetDatabase.CreateAsset(tex, $"{_outputDir}/VatTex_{_target.name}.asset");
        AssetDatabase.CreateAsset(lut, $"{_outputDir}/VatLUT_{_target.name}.asset");
        AssetDatabase.SaveAssets();
        Debug.Log($"VAT 烘焙完成：{maxVerts}顶点 × {totalFrames}帧 → {entries.Count}段动画");
    }
}

/// <summary>运行时给 shader 查表的 LUT。</summary>
public class VatLUT : ScriptableObject
{
    public int vertexCount;
    public int frameCount;
    public int textureWidth;
    public int textureHeight;
    public List<Entry> entries;
    [System.Serializable] public class Entry
    {
        public string name;
        public int meshId;
        public int startFrame;
        public int frameCount;
        public float fps;
        public bool loop;
    }
}
```

> ⚠️ 骨架代码，工程化要点：
> - `AnimationMode.SampleAnimationClip` 需在 Editor，且 target 上的 rig/骨骼要正确驱动 SkinnedMesh。
> - 多 mesh：外层再套 `foreach meshId`，每 mesh 一张 VAT（或纹理数组）。
> - 精度/内存：顶点多时 RGBAFloat 体积大，可降到 RGBAHalf 或分块；位置范围大时归一化到 bounds 再 shader 解码。
> - 法线/切线：如需正确光照，再加一张「法线 VAT」用同样布局存 `mesh.normals`。

---

## 二、shader 采样端（URP，伪代码 / 关键段）

> 配合 [[【笔记】大规模单位动画方案]] 的 per-instance 属性 `_AnimIndex`（= meshId×N + state）、`_AnimTime`。LUT 数据烘焙成 `StructuredBuffer` 或 shader 常量数组。

```hlsl
// === 顶点阶段 ===
// 传入：SV_VertexID + per-instance _AnimIndex / _AnimTime
#pragma multi_compile_instancing
#pragma multi_compile _ DOTS_INSTANCING_ON

#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

TEXTURE2D(_VatTex); SAMPLER(sampler_VatTex);
float _VertexCount;     // = VAT 纹理宽度
float _FrameCount;      // = VAT 纹理高度

// LUT：每段 (startFrame, frameCount, fps, loop)，按 _AnimIndex 索引
StructuredBuffer<float4> _AnimLUT; // x=startFrame, y=frameCount, z=fps, w=loop

struct Attributes { uint vertexID : SV_VertexID; float3 posOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID; };

struct Varyings { float4 posCS : SV_POSITION; /* ... */ };

Varyings Vert(Attributes IN)
{
    Varyings o = (Varyings)0;
    UNITY_SETUP_INSTANCE_ID(IN);

#if defined(DOTS_INSTANCING_ON)
    float animIndex = UNITY_ACCESS_DOTS_INSTANCED_PROP(float, _AnimIndex);
    float animTime  = UNITY_ACCESS_DOTS_INSTANCED_PROP(float, _AnimTime);
#else
    float animIndex = 0; float animTime = 0;
#endif

    // 1) 查 LUT
    float4 e = _AnimLUT[(uint)animIndex];
    float frame = animTime * e.z + e.x;          // animTime*fps + startFrame
    if (e.w > 0.5) frame = e.x + fmod(frame - e.x, e.y); // loop
    frame = clamp(frame, e.x, e.x + max(e.y - 1, 0));

    // 2) 采样 VAT
    float u = (IN.vertexID + 0.5) / _VertexCount;
    float v = (frame + 0.5) / _FrameCount;
    float3 animPos = tex2Dlod(sampler_VatTex, float4(u, v, 0, 0)).xyz;

    // 3) 用动画后位置替代原始顶点位置，走标准 URP 变换
    o.posCS = TransformObjectToHClip(animPos);
    return o;
}
```

> DOTS Instancing 的 per-instance 属性 `_AnimIndex`/`_AnimTime` 由 ECS 端 `MaterialPropertyOverride` 组件上传，详见 [[【笔记】大规模单位动画方案]] 第三节。

---

## 三、接入清单

1. 用 `VatBaker` 烘焙每段动画 → 得 `VatTex_*.asset` + `VatLUT_*.asset`；
2. LUT entries 填进 shader 的 `StructuredBuffer`（或写死常量数组）；
3. ECS 端 `UnitAnim` 系统计算 `(animIndex, animTime)` → 写 `MaterialPropertyOverride`；
4. 材质用支持 DOTS Instancing 的 VAT shader（URP 默认 shader 不行，需自定义）。

## 相关链接

- [[【笔记】大规模单位动画方案]] · [[【实战案例】10w单位渲染与动画最小Demo]] · [[【笔记】Entities 1.4 与 Entities Graphics 1.4 官方文档]]
