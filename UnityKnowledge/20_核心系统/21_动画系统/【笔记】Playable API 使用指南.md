---
title: 【笔记】Playable API 使用指南
tags: ["Unity", "动画", "动画系统", "Playable", "Playables API", "程序化动画", "IAnimationJob", "笔记"]
category: 核心系统/动画系统
created: "2026-06-26 10:00"
updated: "2026-06-26 10:00"
description: Playable API 的概念、数据流、三大类节点、最小示例与程序化动画，附高频坑速查。综合剪藏细则与官方文档。
unity_version: 2021.3+
status: 待验证
validation: 代码示例未经实机验证，结论与坑点引用自剪藏细则与官方文档
related: ["[[【设计原理】Animator深度解析]]", "[[【设计原理】Animator状态机]]", "[[【设计原理】混合树与动画混合]]", "[[【Unity】Playable使用细则]]", "[[动画系统专题索引]]"]
author: llm
sources:
  - "[[【Unity】Playable使用细则]]"
  - https://zhuanlan.zhihu.com/p/632890306
  - https://docs.unity3d.com/Manual/Playables.html
  - https://docs.unity3d.com/Manual/Playables-Graph.html
  - "[[【设计原理】Animator深度解析]]"
---

# 【笔记】Playable API 使用指南

> Unity Playables API 的概念模型、数据流、三大类节点、最小可运行示例与程序化动画，并汇总官方文档未写明的限制与坑点。`#Playable` `#动画系统` `#程序化动画`

## 文档定位

本文是 Playables API 的**入门到进阶桥梁**：补齐官方文档偏概念、社区文章偏踩坑之间的「理解 + 用法」中间层。所有「坑/Bug/规避」细节均引用 [[【Unity】Playable使用细则]]（基于 Unity 2021.3），本文只做速查索引，不重复展开。

**相关文档**：[[【设计原理】Animator深度解析]]、[[【设计原理】Animator状态机]]、[[【设计原理】混合树与动画混合]]、[[【Unity】Playable使用细则]]

---

## 一、Playable 是什么？解决什么问题？

`Playables` 是 Unity 提供的一套**通用的、基于有向图（DAG）的数据驱动框架**。它最初为动画设计，但实际上可以驱动任何"随时间变化"的数据：动画、音频、材质属性、Light 强度、自定义脚本逻辑……

**与 Animator/Mecanim 的关系：**

- **Animator 状态机**：擅长"状态切换"（跑→跳→攻击），是高层编排工具。状态一多就臃肿，混合逻辑被固定在 BlendTree 内，不够灵活。
- **Playable**：擅长"数据混合 / 程序化控制"，可理解为**比 Animator 更底层、更可编程的动画管线**。事实上 Animator 内部就是用 PlayableGraph 实现的——用 Playable API 等于绕开状态机，直接搭这条管线。

> **一句话定位**：当需要"运行时动态决定怎么混合动画、做程序化动画、或用动画曲线驱动任意属性"，且 Animator 状态机力不从心时，就该上 Playable。

---

## 二、核心概念与数据流

理解 Playable 只需抓住 4 个概念：

| 概念 | 作用 | 类比 |
|------|------|------|
| **PlayableGraph** | 容器，持有所有节点，驱动每帧求值 | 一个"播放引擎实例" |
| **Playable** | 图中的**输入节点**，产出数据（动画帧、属性值） | 流水线工位 |
| **PlayableOutput** | 图中的**输出节点**，把数据消费到具体组件（Animator / Audio / 脚本） | 流水线终点装车 |
| **Input Weight（输入权重）** | 父节点混合多个子输入时的占比 | 混音器推子 |

**数据流方向**：输入节点 →（层层混合）→ 输出节点 → 组件。一个 Playable 可同时连到多个 Output；一个图里可有多棵树、多个 Output。类型不必严格匹配——动画 Playable 也能接到 `ScriptPlayableOutput`，但某些功能可能不生效（详见 [[【Unity】Playable使用细则]] 的具体案例）。

**每帧求值顺序（剪藏反复强调的坑点）：**

```
1. PrepareFrame()  —— 前序遍历：自顶向下，决定"本帧怎么播"
                     （改权重、改速度、接枝/剪枝、逻辑状态更新）
2. ProcessFrame()  —— 后序遍历：自底向上，"实际计算并写出数据"
                     （读子节点结果、混合、写回组件）
```

> ⚠️ `ScriptPlayable<T>` 若最终没接到 `ScriptPlayableOutput`，**`ProcessFrame()` 不会被调用，但 `PrepareFrame()` 仍会调**。设计逻辑状态更新时务必记住这点。

---

## 三、三大类 API

### 1. PlayableGraph —— 容器与驱动

```csharp
// 创建图
PlayableGraph graph = PlayableGraph.Create("MyGraph");

// 关键：更新模式
graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime); // 跟随游戏时间自动推进

// 创建节点 + 连接拓扑 + 挂输出后：
graph.Play();
// Manual 模式下需手动驱动：
// graph.Evaluate(deltaTime);
```

> ⚠️ **生命周期必做**：图用完必须 `graph.Destroy()`，否则泄漏 native 内存且绑定的 Animator 会卡住。通常在 `OnDestroy()` / `OnDisable()` 中销毁。

### 2. ScriptPlayable\<T> + PlayableBehaviour —— 自定义逻辑节点

在图里插一段自己的 C# 逻辑。`PlayableBehaviour` 主要生命周期：

- `OnGraphStart()` / `OnGraphStop()`
- `OnPlayableCreate()` / `OnPlayableDestroy()`
- `PrepareFrame()` —— **每帧、前序**，改权重/速度/状态
- `ProcessFrame()` —— **每帧、后序**，读输入、算结果、写数据
- `OnBehaviourPlay()` / `OnBehaviourPause()` —— 当前段播放/暂停

> ⚠️ `Initialize()` **不是内置方法**。约定俗成的做法是自定义一个 `Initialize(data)`，在 `ScriptPlayable<T>.Create()` 之后立刻调用：

```csharp
using UnityEngine.Playables;

/// <summary>自定义脚本 Playable 行为示例</summary>
public class MyBehaviour : PlayableBehaviour
{
    private float _param;

    /// <summary>自定义初始化（非内置生命周期方法）</summary>
    public void Initialize(float param) => _param = param;

    public override void PrepareFrame(Playable playable, FrameData info)
    {
        // 前序阶段：根据 _param 决定本帧权重 / 速度等
    }
}

public static ScriptPlayable<MyBehaviour> Create(PlayableGraph graph, float param)
{
    var playable = ScriptPlayable<MyBehaviour>.Create(graph);
    playable.GetBehaviour().Initialize(param); // 创建后立即喂数据
    return playable;
}
```

### 3. 动画类 Playable —— 最常用场景

| 节点 | 作用 |
|------|------|
| `AnimationClipPlayable` | 播放一段 AnimationClip |
| `AnimationMixerPlayable` | 按输入权重混合多个动画 |
| `AnimationLayerMixerPlayable` | 分层混合（上下半身分层） |
| `AnimationScriptPlayable` | 跑自定义 **IAnimationJob**（多线程程序化动画） |
| `AnimationPlayableOutput` | 输出到 `Animator` |

输出节点需绑定到 `Animator`：

```csharp
var output = AnimationPlayableOutput.Create(graph, "AnimOutput", animatorComponent);
```

---

## 四、最小可运行示例：播放单段动画

挂到带 `Animator` 的 GameObject 上即可运行（等价于 Animator 里只有一个 Clip）：

```csharp
using UnityEngine;
using UnityEngine.Playables;
using UnityEngine.Animations;

/// <summary>用 Playable API 播放单个动画剪辑的最小示例</summary>
[RequireComponent(typeof(Animator))]
public class SimplePlayableAnim : MonoBehaviour
{
    [SerializeField] private AnimationClip _clip;

    private PlayableGraph _graph;
    private AnimationClipPlayable _clipPlayable;

    private void Start()
    {
        _graph = PlayableGraph.Create("SimpleAnimGraph");
        _graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);

        // 1. 输入节点：动画剪辑
        _clipPlayable = AnimationClipPlayable.Create(_graph, _clip);

        // 2. 输出节点：绑定到本物体的 Animator
        var output = AnimationPlayableOutput.Create(_graph, "Output", GetComponent<Animator>());
        output.SetSourcePlayable(_clipPlayable); // 连接：剪辑 → 输出

        _graph.Play();
    }

    private void OnDestroy()
    {
        // 必须销毁，否则泄漏 native 内存
        if (_graph.IsValid()) _graph.Destroy();
    }
}
```

**进阶——混合两段动画（淡入淡出）**：把上面的 `_clipPlayable` 换成 Mixer，在 `Update` 里把权重从 `(1, 0)` 渐变到 `(0, 1)`：

```csharp
var mixer = AnimationMixerPlayable.Create(_graph, inputCount: 2);
var clipA = AnimationClipPlayable.Create(_graph, clipA);
var clipB = AnimationClipPlayable.Create(_graph, clipB);

_graph.Connect(clipA, 0, mixer, 0);
_graph.Connect(clipB, 0, mixer, 1);
mixer.SetInputWeight(0, 1f); // A 权重 1
mixer.SetInputWeight(1, 0f); // B 权重 0

output.SetSourcePlayable(mixer);
```

---

## 五、程序化动画：AnimationScriptPlayable + IAnimationJob

Playable 的**杀手锏**——在多线程 Job 里写自定义动画逻辑（IK、惯性混合、布娃娃辅助、骨骼修正……）。详见 [[【笔记】IK系统实现]]。

```csharp
using UnityEngine;
using UnityEngine.Animations;
using Unity.Collections;
using UnityEngine.Playables;

/// <summary>示例：程序化地把某根骨骼抬高一定高度</summary>
public struct LiftBoneJob : IAnimationJob
{
    public TransformStreamHandle bone;        // 目标骨骼
    public NativeArray<float> liftHeight;     // 抬升量（unmanaged 容器传参）

    public void ProcessRootMotion(AnimationStream stream) { }

    public void ProcessAnimation(AnimationStream stream)
    {
        Vector3 pos = bone.GetLocalPosition(stream);
        pos.y += liftHeight[0];
        bone.SetLocalPosition(stream, pos);
    }
}
```

> ⚠️ **Job 两条铁律（剪藏最值得记住）：**
> 1. Job 是**纯值类型 struct**，不能含引用类型字段。需要"引用"时用 `NativeArray` / Unity Collections。
> 2. `AnimationScriptPlayable.SetInputWeight()` **不会真正施加权重到输入数据**，必须在 Job 里手动 `stream.GetInputStream(i)` 处理混合；且 `GetInputStream()` 无缓存、每次全量评估子树，要先用 `stackalloc` 批量取出再循环（性能关键）。

自定义混合器典型写法（节选，完整版见 [[【Unity】Playable使用细则]]）：

```csharp
public void ProcessAnimation(AnimationStream stream)
{
    // GetInputStream 每次都重新评估整棵子树，开销很高，
    // 先用 stackalloc 批量缓存输入流，避免在骨骼循环里反复调用
    Span<AnimationStream> inputStreams = stackalloc AnimationStream[stream.inputStreamCount];
    for (int i = 0; i < stream.inputStreamCount; i++)
        inputStreams[i] = stream.GetInputStream(i);

    // TODO: 在此完成自定义混合逻辑（如惯性混合）……
}
```

---

## 六、典型用法与选型

| 场景 | 用什么 | 何时选 |
|------|--------|--------|
| 替代简单状态机播动画 | `AnimationClipPlayable` + `AnimationMixerPlayable` | 不想要 Animator 状态图，运行时动态拼 |
| 动画淡入淡出 / 跨(fade)混合 | `AnimationMixerPlayable` 权重插值 | 动作衔接、惯性混合 |
| 上下半身分层 | `AnimationLayerMixerPlayable` | 下半身跑、上半身开枪 |
| 程序化/物理动画 | `AnimationScriptPlayable` + `IAnimationJob` | IK、风摆、随动物体、骨骼修正 |
| 用动画曲线驱动**非动画属性** | `ScriptPlayable` + `PropertyStreamHandle` / `PropertySceneHandle` | 用一条曲线驱动 Light 强度、材质参数、BlendShape |
| Timeline 自定义轨道 | `TrackAsset` + `PlayableAsset` + `PlayableBehaviour` | 过场动画嵌入自定义逻辑 |

**该用：** 需要运行时**动态**组合/混合动画；**程序化**动画（Job 级性能）；用动画曲线驱动**任意属性**；做 Timeline 自定义轨道。

**别为用而用：** 纯线性状态切换（Animator 状态机更直观、可视化更好）；不需跨(fade)混合、不需程序化控制的简单角色。

---

## 七、高频坑速查（详见 [[【Unity】Playable使用细则]]）

| 坑 | 规避 |
|----|------|
| 逐帧调试时 `IsPlaying()` 永远返回 `false` | 自己维护一个 `_isPlaying` 字段 |
| Manual → 非 Manual 切换后图不自动更新 | 先 `Stop()` 再 `Play()` 强刷状态 |
| `ProcessFrame()` 不调（脚本节点没接到对应 Output） | 确保最终输出到匹配类型的 Output + 有效 Animator |
| `SetInputWeight()` 对 Job 无效 | Job 内手动 `GetInputStream` 混合 |
| `GetInputStream()` 无缓存、全量评估 | `stackalloc` 批量取一次再循环 |
| 复杂连接结构下属性写入 / Job 调用失效 | 见剪藏末尾 Bug 复现工程汇总 |
| `Animator.cullingMode ≠ AlwaysAnimate` 时角色出视野 Job 不跑 | 设计如此，按需设 cullingMode |

> 调试建议配合作者工具 **PlayableGraph Monitor**（比官方 Graph Visualizer 强，支持大型图 / 缩放 / 拖拽 / 循环引用）。

---

## 相关链接

- [[【Unity】Playable使用细则]] —— 进阶限制 / Bug / 规避方案（本文引用源）
- [[【设计原理】Animator深度解析]] —— Animator 内部机制（Playable 的上层封装）
- [[【设计原理】Animator状态机]] —— 状态机模型与 Playable 的取舍
- [[【设计原理】混合树与动画混合]] —— BlendTree 混合原理，对照 Playable 手动混合
- [[【笔记】IK系统实现]] —— IAnimationJob 的典型应用场景
- [[动画系统专题索引]]
