---
title: "【Unity】Playable使用细则"
source: "https://zhuanlan.zhihu.com/p/632890306"
author:
  - "[[Solarian]]"
published:
created: 2026-06-26
description: "本文基于Unity 2021.3 API。本文介绍官方文档中没提及的Playable使用限制、注意事项、Bug及规避方案，不是Playable的入门教程！ 如果你还不熟悉Playable的基础用法，请先学习以下官方文档和示例： PlayableGraph介…"
tags:
  - "clippings"
---
167 人赞同了该文章

> 本文基于Unity 2021.3 API。

本文介绍官方文档中没提及的Playable使用限制、注意事项、Bug及规避方案，不是Playable的入门教程！ 如果你还不熟悉Playable的基础用法，请先学习以下官方文档和示例：

- [PlayableGraph介绍](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Playables-Graph.html)
- [Playable介绍](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Playables.html)
- [Playable API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Playables.Playable.html)
- [ScriptPlayable API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Playables.ScriptPlayable_1.html)
- [PlayableBehaviour API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Playables.PlayableBehaviour.html)
- [AnimationScriptPlayable API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.AnimationScriptPlayable.html)
- [IAnimationJob API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.IAnimationJob.html)
- [AnimationStream API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.AnimationStream.html)
- [PropertyStreamHandle API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.PropertyStreamHandle.html)
- [PropertySceneHandle API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.PropertySceneHandle.html)
- [TransformStreamHandle API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.TransformStreamHandle.html)
- [TransformSceneHandle API文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Animations.TransformSceneHandle.html)
- [Notification](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Playables.Notification.html)
- [Unity-Technologies/SimpleAnimation示例项目](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/SimpleAnimation)
- [Unity-Technologies/animation-jobs-samples示例项目](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/animation-jobs-samples)

### PlayableGraph Monitor

一个PlayableGraph监控工具，功能比Unity官方的Graph Visualizer更强更完善。

- 支持大型PlayableGraph
- 可显示PlayableGraph和Playable节点的详细数据
- 支持缩放视图
- 支持拖拽视图和Playable节点
- 支持为Playable节点添加额外文本标签
- 支持带有 [循环引用](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E5%BE%AA%E7%8E%AF%E5%BC%95%E7%94%A8&zhida_source=entity) 的PlayableGraph（需要手动调整 [节点布局](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E8%8A%82%E7%82%B9%E5%B8%83%E5%B1%80&zhida_source=entity) ）

工具地址： [github.com/SolarianZ/Un](https://link.zhihu.com/?target=https%3A//github.com/SolarianZ/UnityPlayableGraphMonitorTool)

![](https://pica.zhimg.com/v2-2b0d3e9d4275e570e940917f7fd8ad5a_1440w.jpg)

PlayableGraph Monitor

### PlayableGraph

连接Playable和Playable Output时不需要严格的匹配Playable类型，一个Playable可以同时作为多个 `ScriptPlayableOutput` 的输入。动画Playable可以连接到脚本Playable，也可以作为 `ScriptPlayableOutput` 的输入，反之亦然。但需要注意，如果Playable最终没有输入到对应类型的 `ScriptPlayableOutput` ，其中的某些功能可能不会生效，下文有具体案例。

在Editor中逐帧运行游戏时， `PlayableGraph.IsPlaying()` 方法总是返回 `false` ，无论是否调用过 `PlayableGraph.Stop()` 方法。我认为这是个Bug，但是Unity表示这是故意设计的。这个设计显然非常糟糕，因为Runtime应该对Editor无感知， [逐帧播放](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E9%80%90%E5%B8%A7%E6%92%AD%E6%94%BE&zhida_source=entity) 是存粹的Editor功能，但它却改变了Runtime接口的行为。如果游戏中根据PlayableGraph的播放状态决定代码执行逻辑，那在逐帧调试时很可能出现异常。要规避此问题，可以额外维护一个字段来标识PlayableGraph是否被人为停止播放。

PlayableGraph开始播放后，将其更新模式设为 `DirectorUpdateMode.Manual` ，PlayableGraph的播放状态会自动变为停止（ `PlayableGraph.IsPlaying()` 方法返回 `false` ）。此时再调用 `PlayableGraph.Play()` 方法，PlayableGraph的播放状态会变为播放中（ `PlayableGraph.IsPlaying()` 方法返回 `true` ），但PlayableGraph仍不会自动更新，需要主动调用 `PlayableGraph.Evaluate()` 方法驱动其更新，至此都是符合预期的。此时，如果将PlayableGraph的更新模式设为任意 **非** `DirectorUpdateMode.Manual` 模式，PlayableGraph将不会按预期恢复自动更新。这是 [Unity的Bug](https://link.zhihu.com/?target=https%3A//issuetracker.unity3d.com/product/unity/issues/guid/UUM-32824) ，要使PlayableGraph恢复自动更新，可以先调用 `PlayableGraph.Stop()` 方法，再调用 `PlayableGraph.Play()` 方法，强制刷新一下状态。参考下文的Bug规避方案。

### ScriptPlayable\<T>和PlayableBehaviour

`PlayableBehaviour` 的生命周期如下图所示：

![](https://pic3.zhimg.com/v2-428f14d8924592ad70878929e88eac68_1440w.jpg)

PlayableBehaviour生命周期

PlayableGraph在每一帧中总是先前序遍历调用每个节点的 `PrepareFrame()` 方法，再 [后序遍历](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E5%90%8E%E5%BA%8F%E9%81%8D%E5%8E%86&zhida_source=entity) 调用每个节点的 `ProcessFrame()` 方法。如果 `ScriptPlayable<T>` 最终没有输出到 `ScriptPlayableOutput` ，其 `PlayableBehaviour.ProcessFrame()` 方法 **不会** 被调用，但其 `PlayableBehaviour.PrepareFrame()` 方法 **会** 被调用。

`Initialize()` 方法不是 `PlayableBehaviour` 内置的生命周期方法。为了实现自定游戏逻辑，一般需要给Playable传递一些数据来对其进行初始化，因此通常会额外定义一个 `Initialize()` 方法，在创建Playable后立即调用此方法来进行初始化。参考示例代码。

```csharp
// PlayableBehaviour初始化示例
public class MyBehaviour : PlayableBehaviour
{
    private object _data;

    public void Initialize(object data)
    {
        _data = data;

        // TODO: 其他初始化操作……
    }

    // TODO: 其他生命周期方法……
}

// 示例方法：创建ScriptPlayable并初始化Behaviour
public ScriptPlayable<MyBehaviour> CreateMyScriptPlayable(PlayableGraph graph, object data)
{
    var playable = ScriptPlayable<MyBehaviour>.Create(graph);
    var behaviour = playable.GetBehaviour();
    behaviour.Initialize(data);
    return playable;
}
```

### 动画Playable的评估（Evaluate）顺序

PlayableGraph在每帧中总是按照后续遍历的顺序评估每个动画Playable。在 `AnimationScripPlayable` 的Job中，如果手动触发对子Playable树的评估时没有按输入索引顺序升序进行，这个规则将在这一节点中被破坏。

### AnimationClipPlayable

使用 `AnimationClipPlayable` 播放 **非循环** 动画时：

- 将时间设置到大于AnimationClip长度的位置
- 若播放速度大于 `0` ，动画不会继续播放
	- 若播放速度小于 `0` ，动画会反向播放直到时间为 `0`
- 将时间设置到小于 `0` 的位置
- 若播放速度小于 `0` ，动画不会继续播放
	- 若播放速度大于 `0` ，动画会正向播放直到时间为AnimationClip长度

### AnimationScriptPlayable

`AnimationScriptPlayable` 用于在 [多线程](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E5%A4%9A%E7%BA%BF%E7%A8%8B&zhida_source=entity) 环境中执行自定义动画Job。在自定义动画Job中，可以通过 `AnimationStream` 来读写动画和组件数据，实现程序性动画。

定义动画Job时，需要实现一个实现了 `IAnimationJob` 接口的纯值类型结构体，该结构体中不能直接或间接含有任何引用类型的非静态字段或非静态属性。Unity提供了一些 [非托管](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E9%9D%9E%E6%89%98%E7%AE%A1&zhida_source=entity) 的集合和引用，可在一定程度上减少不能使用引用类型所带来的限制。参考上文提及的NativeArray和Unity Collections包。

若 `Animator.cullingMode` 不是 `AnimatorCullingMode.AlwaysAnimate` ，当角色不在相机视锥体内时， `IAnimationJob.ProcessAnimation()` 方法 **不会** 被调用。设计如此，符合预期。

若 `AnimationScriptPlayable` 没有最终没有输入到 `AnimationPlayableOutput` ，或者所输入到的 `AnimationPlayableOutput` 没有绑定到有效的 `Animator` 组件， `IAnimationJob.ProcessRootMotion()` 方法和 `IAnimationJob.ProcessAnimation()` 方法都 **不会** 被调用。设计如此，符合预期。

在某些Playable连接关系下， `IAnimationJob.ProcessRootMotion()` 和 `IAnimationJob.ProcessAnimation()` 不会被调用，是 [Unity的Bug](https://link.zhihu.com/?target=https%3A//issuetracker.unity3d.com/product/unity/issues/guid/UUM-34442) ，参考下文的Bug规避方案。

设置 `AnimationScriptPlayable` 的输入权重不会实际影响输入Playable的数据，需要在Job代码中手动处理 [权重](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=2&q=%E6%9D%83%E9%87%8D&zhida_source=entity) 。在手动处理输入权重的情况下，一般会使用 `AnimationScriptPlayable.SetProcessInputs(false)` 方法来禁止其自动评估子Playable树，然后在Job代码中调用 `AnimationStream.GetInputStream()` 方法来手动触发评估子Playable树。因为 `AnimationScriptPlayable` 自动评估所得到的输入数据会被直接写入到自己的 `AnimationStream` 中，没有施加权重影响，属于无用的数据，浪费计算性能。另外 `AnimationStream.GetInputStream()` 方法没有内部 [缓存机制](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E7%BC%93%E5%AD%98%E6%9C%BA%E5%88%B6&zhida_source=entity) ，每次调用都会重新评估整棵子Playable树，应该尽量减少调用次数。参考示例代码。

```csharp
// 自定义动画混合器示例
public struct MyCustomMixerJob : IAnimationJob
{
    public NativeArray<TransformStreamHandle>.ReadOnly boneHandles;

    public void ProcessRootMotion(AnimationStream stream) { }

    public void ProcessAnimation(AnimationStream stream)
    {
        // 每次GetInputStream，都会触发对输入子树的评估，开销很高，
        // 所以这里先缓存输入流，不在每个骨骼循环中反复调用GetInputStream
        Span<AnimationStream> inputStreams = stackalloc AnimationStream[stream.inputStreamCount];
        for (int i = 0; i < stream.inputStreamCount; i++)
        {
            inputStreams[i] = stream.GetInputStream(i);
        }

        for (int i = 0; i < boneHandles.Length; i++)
        {
            var boneHandle = boneHandles[i];
            for (int j = 0; j < inputStreams.Length; j++)
            {
                var inputStream = inputStreams[j];
                // TODO: 在这里完成自定义混合逻辑，例如惯性混合……
            }
        }
    }
}

// 示例方法：创建自定义动画混合器Playable（示例中没有连接输入的子Playable树）
public AnimationScriptPlayable CreateMyCustomMixerPlayable(PlayableGraph graph,
    NativeArray<TransformStreamHandle>.ReadOnly boneHandles)
{
    var jobData = new MyCustomMixerJob
    {
        boneHandles = boneHandles,
    };
    var playable = AnimationScriptPlayable.Create(graph, jobData);
    // 禁止自动评估输入的Playable子树，这样在Job中手动调用GetInputStream之前，整棵子树都不会被评估
    playable.SetProcessInputs(false);

    return playable;
}
```

### AnimationStream

`AnimationStream` 作为动画数据的载体在动画Playable之间传递。在 `IAnimationJob` 中，可以修改 `AnimationStream` 中的动画数据，实现程序性动画。

![](https://pica.zhimg.com/v2-6a634ba788b9ba111a523ddbfdf50bea_1440w.jpg)

AnimationStream

修改 `AnimationStream.velocity` 属性可以改变角色移动速度。修改 `AnimationStream.angularVelocity` 属性可以改变角色的 [转向速度](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E8%BD%AC%E5%90%91%E9%80%9F%E5%BA%A6&zhida_source=entity) （单位是弧度/秒）。这两个速度都是模型空间下的速度，使用时可能需要进行坐标 [空间转换](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E7%A9%BA%E9%97%B4%E8%BD%AC%E6%8D%A2&zhida_source=entity) 。

`AnimationStream` 配合 `PropertyStreamHandle` / `PropertySceneHandle` 或 `TransformStreamHandle` / `TransformSceneHandle` 可以实现读写动画曲线、组件属性和 `Transform` 数据，下文会介绍。

### PropertyStreamHandle和PropertySceneHandle

`PropertyStreamHandle` 可以绑定到 [动画曲线](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/animeditor-AnimationCurves.html) 、组件属性和自定义属性，然后借助 `AnimationStream` 读写所绑定的属性值。目前支持 `float` 、 `int` 和 `bool` 类型的属性。需要注意， `PropertyStreamHandle` 所绑定的目标 `Component` 对象必须是 `AnimationPlayableOutput` 所绑定的 `Animator` 组件所在的GameObject的直接或间接子节点。

组件属性被绑定到 `PropertyStreamHandle` 后，将无法在动画Job外部修改其数值，是 [Unity的Bug](https://link.zhihu.com/?target=https%3A//issuetracker.unity3d.com/product/unity/issues/guid/UUM-36913) ，已在Unity 2022.2.17f1中修复。

通过 `PropertyStreamHandle` 修改 "GravityWeight" 曲线的值，无法实际影响到角色所承受的重力（作用于 `CharacterController` 组件）（怀疑是Bug，待确认）。

在某些Playable连接关系下，通过 `PropertyStreamHandle` 修改属性不会生效（或数值不匹配），是 [Unity的Bug](https://link.zhihu.com/?target=https%3A//issuetracker.unity3d.com/product/unity/issues/guid/UUM-33944) ，参考下文的Bug规避方案。

`AnimatorJobExtensions.BindStreamProperty()` 方法同时支持绑定动画曲线、组件属性和自定义属性：

- 绑定组件属性时，目标组件不能是 `Transform` ，否则会报错（ `Transform` 需要使用 `TransformStreamHandle` 绑定）
- 绑定组件属性时，目标属性名必须在目标组件中存在，否则会报错
- 绑定AnimationClip中的动画曲线或自定义属性时， `transform` 参数是 `Animator.transform` ， `type` 参数是 `typeof(Animator)`
- 如果属性名参数 `property` 与AnimationClip中的动画曲线名称相同，则绑定动画曲线，否则绑定为自定义属性
	- AnimationClip中的动画曲线中可能有 [BlendShape](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/BlendShapes.html) 数据，但是BlendShape是 `SkinnedMeshRenderer` 组件的属性，绑定时需要指定组件类型为 `typeof(SkinnedMeshRenderer)` ，不是 `typeof(Animator)`
- 绑定AnimationClip中的动画曲线时，需要删除曲线名称中的空格
- 绑定在 [动画导入设置](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/AnimationCurvesOnImportedClips.html) 中手动添加的曲线，需要保留曲线名称中的空格
- 某些自定义动画曲线需要在模型导入设置中启用 [Animated Custom Properties](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-AnimationClip.html%23%3A~%3Atext%3DAnimated%2520Custom%2520Properties) 选项后才能绑定
- 并非所有的动画曲线都能绑定（例如，AnimationClip中的肌肉曲线和带路径的曲线无法绑定），参考下方的获取可绑定的动画曲线的名称的代码

`AnimatorJobExtensions.BindCustomStreamProperty()` 方法只能用于绑定自定义属性，不能绑定动画曲线和组件属性：

- 该方法总是在动画内存中开辟新空间存储目标属性，即使AnimationClip中有同名曲线，也不会绑定到该曲线
```csharp
// 获取可绑定的动画曲线的名称
public static List<string> GetBindableCurveNames(AnimationClip clip)
{
    List<string> exclusion = new List<string>() {
        "RootT.x", "RootT.y", "RootT.z",
        "RootQ.x", "RootQ.y", "RootQ.z", "RootQ.w",
        "LeftFootT.x", "LeftFootT.y", "LeftFootT.z",
        "LeftFootQ.x", "LeftFootQ.y", "LeftFootQ.z", "LeftFootQ.w",
        "RightFootT.x", "RightFootT.y", "RightFootT.z",
        "RightFootQ.x", "RightFootQ.y", "RightFootQ.z", "RightFootQ.w",
        "LeftHandT.x", "LeftHandT.y", "LeftHandT.z",
        "LeftHandQ.x", "LeftHandQ.y", "LeftHandQ.z", "LeftHandQ.w",
        "RightHandT.x", "RightHandT.y", "RightHandT.z",
        "RightHandQ.x", "RightHandQ.y", "RightHandQ.z", "RightHandQ.w",
    };

    var curveNames = new List<string>();
    var muscleNames = new List<string>(HumanTrait.MuscleName);
    var curveBindings = UnityEditor.AnimationUtility.GetCurveBindings(clip);
    foreach (var binding in curveBindings)
    {
        if (!string.IsNullOrEmpty(binding.path))
        {
            continue;
        }

        if (muscleNames.Contains(binding.propertyName))
        {
            continue;
        }

        if (exclusion.Contains(binding.propertyName))
        {
            continue;
        }

        const string LeftHandPrefix = "LeftHand.";
        if (binding.propertyName.StartsWith(LeftHandPrefix))
        {
            var propName = "Left " + binding.propertyName.Substring(LeftHandPrefix.Length).Replace('.', ' ');
            if (muscleNames.Contains(propName))
            {
                continue;
            }
        }

        const string RightHandPrefix = "RightHand.";
        if (binding.propertyName.StartsWith(RightHandPrefix))
        {
            var propName = "Right " + binding.propertyName.Substring(RightHandPrefix.Length).Replace('.', ' ');
            if (muscleNames.Contains(propName))
            {
                continue;
            }
        }

        curveNames.Add(binding.propertyName);
    }

    return curveNames;
}
```

`PropertySceneHandle` 的功能与 `PropertyStreamHandle` 类似，但只提供数据读取功能，不支持数据写入，并且可以绑定到场景中的任意 `Component` 对象，不受与 `Animator` 组件的层级关系限制。

### TransformStreamHandle和TransformSceneHandle

`TransformStreamHandle` 可以绑定到一个 `Transform` 组件，然后借助 `AnimationStream` 读写 `Transform` 数据。需要注意， `TransformStreamHandle` 所绑定的目标 `Transform` 组件必须是 `AnimationPlayableOutput` 所绑定的 `Animator` 组件所在的GameObject的直接或间接子节点（包含自身，但绑定自身时可能遇到无法修改角色位置或角色跳回初始位置的问题，是 [Unity的Bug](https://link.zhihu.com/?target=https%3A//issuetracker.unity3d.com/product/unity/issues/guid/UUM-31822) ，参考下文的Bug规避方案）。

`TransformSceneHandle` 的功能与 `TransformStreamHandle` 类似，但只提供数据读取功能，不支持数据写入，并且可以绑定到场景中的任意 `Transform` 组件，不受与 `Animator` 组件层级关系限制。

### 执行时序变化

动画Job方法的调用时机、动画消息的触发时机，会受到 `Animator.updateMode` 属性和 `PlayableGraph` 的更新模式（ `DirectorUpdateMode` ）影响。

当 `Animator.updateMode` 为 `AnimatorUpdateMode.Normal` 、 `PlayableGraph` 的更新模式为 `DirectorUpdateMode.GameTime` 时， `ScriptPlayable<T>` 先于动画Job进行准备和评估。利用这一点，可以将动画Playable输入到Script Playble，在评估动画之前，在ScriptPlayable的 `PrepareFrame()` 方法中完成动画的逻辑状态更新（修改权重、接枝、剪枝等）。

Playable Notification在推送后进入队列，而不是立即发送给监听者，当Playable Graph评估完成后，才会发送给监听者。

### Playable Bug及规避方案汇总

Playable系统中有很多离谱的Bug。有些Playable在简单 [连接结构](https://zhida.zhihu.com/search?content_id=228773861&content_type=Article&match_order=1&q=%E8%BF%9E%E6%8E%A5%E7%BB%93%E6%9E%84&zhida_source=entity) 下做测试的时候，表现正常，但连接结构变得复杂后，就出Bug了。这个时候，你很可能已经基于原本预期表现正常的Playable做了很多上层封装，为了解决这个突然出现的Bug，不得不去改架构，非常恶心。这里的每一项注意事项和Bug记录，都是我踩过的一个坑！

- [Bug及规避方案汇总](https://zhuanlan.zhihu.com/p/631392835)
- [Bug及规避方案的最小化复现工程汇总](https://link.zhihu.com/?target=https%3A//github.com/zdirtywork%3Ftab%3Drepositories)

编辑于 2023-11-14 18:09・上海[游戏搬砖月入7-8k，真有这么赚钱吗？](https://zhuanlan.zhihu.com/p/1920800837787181968)

[

别人赚不赚不知道， 但我自己玩游戏搬砖是真的赚！我一哥们儿做 游戏搬砖工作室，赚的比这还多，而且全是自动挂机，解放双手！就下面这种， 单窗几百钻石，加一起也有两万了吧，卖掉之...

](https://zhuanlan.zhihu.com/p/1920800837787181968)

赞同 167