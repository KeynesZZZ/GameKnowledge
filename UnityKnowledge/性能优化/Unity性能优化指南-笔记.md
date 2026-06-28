---
title: "Unity性能优化指南-笔记"
source: "https://zhuanlan.zhihu.com/p/1947807025321993799"
author:
  - "[[洛桑]]"
published:
created: 2026-06-27
description: "指南版本：Unity PC、主机优化指南-2022LTS 原网址： 更新后的 2022 LTS 游戏优化最佳实践指南 | Unity 博客Profiling尽早地、经常地、在目标机器上做性能分析在项目开发早期就开始Profile（分析性能），而不是快…"
tags:
  - "clippings"
---
[收录于 · Unity](https://www.zhihu.com/column/c_1947806959756645517)

70 人赞同了该文章

目录

收起

Profiling

尽早地、经常地、在目标机器上做性能分析

优化的功夫要下在正确的地方

理解Unity Profiler的工作原理

使用Profile Analyzer

为每一帧设定一个特定的时间预算

确定瓶颈在CPU还是GPU

使用平台原生性能分析工具和调试工具

Project Auditor

构建结果检查器

内存

使用内存分析器

减少GC的影响

尽可能定时垃圾收集

使用增量垃圾收集器来分割GC工作负载

堆查看器

编程与代码架构

理解Unity PlayerLoop

尽量减少每帧运行的代码

缓存昂贵函数返回的结果

避免使用空的Unity事件函数

自定义一个UpdateManager

移除Debug语句

禁用堆栈跟踪日志

使用哈希值代替字符串参数

选择正确的数据结构

避免运行时附加组件

使用对象池

坐标变换一次，而不是两次

使用ScriptableObjects

避免使用Lambda语句

C# Job System

Burst Compiler

项目配置

关闭不必要的玩家或质量设置

切换到IL2CPP

避免大层次结构

资产

压缩纹理

纹理导入设置

对纹理使用图集

检查多边形的数量

网格导入设置

其他网格优化方式

对资产进行审计

异步纹理缓冲区

流式加载Mipmaps和纹理

使用Addressables资产系统

图形

提交到渲染管线

选择一条渲染路径

优化Shader Graph

移除内置着色器设置

去除着色器变体

粒子模拟：粒子系统或VFX Graph

用抗锯齿平滑画面

常见的光照优化

GPU优化

对GPU进行基准测试

监视渲染统计数据

使用draw call合批

检查帧调试器

优化填充率和减少过度绘制

绘制顺序和渲染队列

优化主机平台的图形效果

剔除

动态分辨率

多相机视图

URP中的RenderObjects

HDRP中的CustomPassVolumes

使用LOD

分析后处理效果

UI

分离画布Canvas

隐藏不可见UI元素

限制GraphicRaycaster和关闭射线目标选项

避免大型列表或网格视图

避免大量互相堆叠的元素

使用全屏UI时隐藏所有其他东西

UI Toolkit性能优化技巧

音频

使用无损文件作为源文件

减少AudioClips数量

优化混音器

物理

简化碰撞体

优化设置选项

调整模拟频率

修改网格碰撞器的CookingOptions

使用Physics.BakeMesh

对于大型场景使用箱形修剪

修改求解器迭代次数

禁用自动Transform同步

复用碰撞回调

移动静态碰撞器

使用不会产生分配的查询

将光线投射查询进行合批

用物理调试器可视化物理

动画

为简易动画使用替代方案

避免缩放曲线

只在可见时更新

优化工作流

工作流与协作

使用版本控制

Unity版本控制

拆分大型场景

Accelerate Solutions用行业领先的专业知识助力到达下一阶段

用Unity Integrated Success移除障碍

Next steps

更多资源

Unity创作者的专业培训

指南版本：Unity PC、主机优化指南-2022LTS

原网址： [更新后的 2022 LTS 游戏优化最佳实践指南 | Unity 博客](https://link.zhihu.com/?target=https%3A//unity.com/cn/blog/engine-platform/updated-2022-lts-best-practice-guides)

## Profiling

### 尽早地、经常地、在目标机器上做性能分析

在项目开发早期就开始Profile（分析性能），而不是快要到shipping的时候才开始。在小毛病和性能尖刺出现时就进行调查。

只要有可能就应该构建在目标机器上并进行性能分析，记住要分析和优化你打算支持的最高端和最低端机器。

### 优化的功夫要下在正确的地方

对于拖慢游戏性能的问题，不要猜或假设。使用Unity Profiler或者平台特有的工具去定位延迟的精确来源。而且，不要等到严重的性能问题开始出现的时候才去工具箱里找办法

不是所有的优化手段都适用于你的项目，应当根据实际情况而有所调整。找出真正的瓶颈且集中精力在能真正使你工作事半功倍的方法上。

### 理解Unity Profiler的工作原理

自带的性能分析工具能帮助你在运行时定位任何造成瓶颈或卡顿的原因，且能更好地认识到在一个特定的帧或特定时间点发生了什么。

Profiler是基于插桩获取数据进行分析的，比如侦测游戏或引擎中被自动标记的代码（Mono的Start、Update方法或者特定的API调用），以及通过ProfileMarker API显式包装后的代码。

刚开始时可以只开启CPU和内存的检测作为默认手段，还可以用补充的分析器去监测渲染器、音频、物理，具体取决于项目的实际情况。

注意：只启用你所需要的分析器，以免其他分析器影响性能进而扰乱你的分析结果。

使用下面的流程图可以更有效地分析你的Unity项目：

![](https://pic4.zhimg.com/v2-e152e07c521efbe02d9a4d19c798a645_1440w.jpg)

为了在真机平台上抓取性能分析数据，在构建点击Build And Run之前需要确认勾选上了 Development Build

还可以选择性勾选 Autoconnect Profiler ，后者在有些时候比如想抓取应用开始的那几帧时可能有用，但要注意这个选项会增加5~10s的启动时间，所以应当只在必要时使用它（实际上大型项目的打包时间都是以小时计的，远大于这几秒的启动时间，所以勾选的关键其实是会不会影响打包管线和时间，启动时间这点耗时可以忽略不计，毕竟没勾上就得重打一个包几个小时就过去了）。

![](https://pic2.zhimg.com/v2-096ae4036294cfb2647033586cc56e0f_1440w.jpg)

选择目标平台进行性能分析，Record按钮将追踪应用在几秒内的情况（默认是300帧），可以通过 Preference>Analysis>Profiler>Frame Count进行更改，最高2000帧，当然了提高这个设置会消耗更多的CPU和内存。

当使用 [Deep Profiling](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/ProfilerWindow.html%23deep-profiling) 时，Unity会分析你脚本代码中的每个函数调用的开始与结束，以告诉你应用程序的哪个部分正在被执行且很可能是造成卡顿的原因。然而，深度性能分析会对每个方法调用都增加额外开销，这可能会导致分析结果出现偏差。

在窗口中点击以分析特定的一帧，接下来使用时间轴视图或层次视图进行分析：

- **时间轴** 将一帧中的时间拆开来做可视化展示。这允许您可视化活动之间以及不同线程之间的关系。使用该选项可以决定是CPU瓶颈还是GPU瓶颈。
![](https://pic4.zhimg.com/v2-e99cf84c8a7de3ce5e72870bbf348c2d_1440w.jpg)

- **层次视图** 展示 ProfileMarkers 的层级，将同组的东西放在一起。这允许你基于耗时对采样的事件进行排序，你还可以统计函数调用的次数以及托管堆内存（GC Alloc）的情况
![](https://pic2.zhimg.com/v2-ed3593d71b501a7aadc52890c3baa1c1_1440w.jpg)

可以在 [这里](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/ultimate-guide-to-profiling-unity-games%3Fungated%3Dtrue) 找到关于Unity Profiler的完整概况。如果你是性能分析新手，可以看 [这个视频](https://link.zhihu.com/?target=https%3A//youtu.be/uXRURWwabF4) 。

**深层性能分析**

可以在构建设置中启用 Deep Profiling Support，此时当构建完的包体启动时，深层分析器将分析所有代码部分，而不只是被ProfilerMarkers显式标记的代码部分。

如前所述其会产生很大的资源消耗和内存消耗。每个ProfilerMarker会产生一点开销（10ns，具体取决于目标平台）。如果函数调用非常多就得注意了，需要谨慎使用。

如果想看到诸如 [GC.Alloc](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/profiler-markers.html%23backend%3F) 或 [JobHandle.Complete](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/profiler-markers.html%23multithreading%3F) 这些被标记过的采样样本的细节，可以在Profiler窗口工具栏中启用Call Stacks设置，这将提供样本的完整调用栈，而不用引入深层分析的开销。

![](https://pic3.zhimg.com/v2-6b35771252000980bcf8d486cff045ec_1440w.jpg)

总之，只在必要时使用深层分析，毕竟开启后你的项目会运行得非常慢。

### 使用Profile Analyzer

分析结果解析器聚合了多帧的分析器数据，然后定位到出问题的那些帧。想知道你对项目做的改动对Profiler造成了什么影响的话，就去Compare视图里面加载两套数据以找出区别，以此来测试改动并改善结果。

Profile Analyzer可通过Unity包管理器获取。

![](https://pic2.zhimg.com/v2-1b703730256df1eae6f69ed73a8214e7_1440w.jpg)

### 为每一帧设定一个特定的时间预算

比如目标是30帧，则帧时间预算为33.33ms，60帧则为16.66ms。

**帧数其实是一种带有欺骗性的度量方法**

更推荐的方式是使用以毫秒计的帧时间而不是FPS（frames per second，帧数），想知道为什么的话看看下面这个对比图：

![](https://pica.zhimg.com/v2-e200ba2b738a108dfd27d7ee37e7c9de_1440w.jpg)

有如下的计算数据：

```
1000 ms/sec / 900 fps = 1.111 ms per frame
1000 ms/sec / 450 fps = 2.222 ms per frame
1000 ms/sec / 60 fps = 16.666 ms per frame
1000 ms/sec / 56.25 fps = 17.777 ms per frame
```

900fps对应1.111ms帧时间，450fps对应2.222ms，只差1.111ms帧数却减半了。但是在60fps和56.25fps的时候，同样只差1.111ms，但是帧数下降的比例却远比前面少。

这就是为什么开发者使用平均帧时间作为游戏运行快慢的测试基准，而不是用fps。

除非fps掉到了目标fps之下，否则就不需要担心fps而应该集中精力在如何测量游戏运行得多快上，即帧时间预算之中。

这篇原始文章 [Robert Dunlop's FPS versus Frame Time](https://link.zhihu.com/?target=http%3A//www.mvps.org/directx/articles/fps_versus_frame_time.htm) 或许能提供更多的信息。

### 确定瓶颈在CPU还是GPU

CPU负责决定哪些东西要被绘制，GPU负责实际绘制它们。当渲染性能问题是一帧中CPU花费太多时间时，就是CPU瓶颈。当渲染性能问题是GPU在一帧中花费太多时间时，就是GPU瓶颈。

Profiler能告诉你到底是GPU还是CPU花费了你帧预算中的大部分时间，这是通过使用Gfx前缀的性能标记实现的：

- `Gfx.WaitForCommands` 标记，说明渲染线程已在待命，但可能在等待主线程
- 如果 `Gfx.WaitForPresentOnGfxThread` 频繁出现，说明主线程在等待渲染线程，这说明程序可能出现了GPU瓶颈。检查CPU Profiler模块的时间轴视图去检查渲染线程上的任务。

若渲染线程在 `Camera.Render` 上耗时过多，则程序出现CPU瓶颈，这可能是因为花费了太多时间去传输draw call和纹理到GPU上。

若渲染线程在 `Gfx.PresentFrame` 上耗时过多，则程序出现GPU瓶颈，可能是因为在 [等待GPU上的垂直同步](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/profiler-markers.html%23rendering) 。

参考 [Common Profiler markers](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/profiler-markers.html%3F) 以获取关于标记符的完整列表。同时也可以看看我们的博客 [Fixing Time.deltaTime in Unity 2020.2 for smoother gameplay](https://link.zhihu.com/?target=https%3A//blog.unity.com/technology/fixing-time-deltatime-in-unity-2020-2-for-smoother-gameplay-what-did-it-take%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 以获取有关帧pipeline的更多信息。

### 使用平台原生性能分析工具和调试工具

如果需要更多的细节，就要去找一找平台可用的原生性能分析与调试工具。

原生分析工具：

**Intel：**

- [英特尔VTune](https://link.zhihu.com/?target=https%3A//www.intel.com/content/www/us/en/developer/tools/oneapi/vtune-profiler.html):使用仅适用于英特尔处理器的工具套件，快速找到并修复英特尔平台上的性能瓶颈。
- [Intel GPA套件](https://link.zhihu.com/?target=https%3A//software.intel.com/content/www/us/en/develop/tools/graphics-performance-analyzers.html):这套以图像为中心的工具可以通过快速识别问题区域来帮助您提高游戏的性能。

**Xbox和Windows PC：**

- PIX: PIX是使用DirectX 12的Windows和Xbox游戏开发者的性能调优和调试工具。它包括用于理解和分析CPU和GPU性能的工具，以及监控各种实时性能计数器。对于Windows开发人员， [从这里开始](https://link.zhihu.com/?target=https%3A//devblogs.microsoft.com/pix/download/) 。要了解更多关于Xbox的PIX的详细信息，您需要成为注册的Xbox开发人员:[从这里开始](https://link.zhihu.com/?target=https%3A//www.xbox.com/en-US/developers/id) 。

**PC平台通用：**

- [AMD μProf](https://link.zhihu.com/?target=https%3A//developer.amd.com/amd-uprof/): AMD uProf是一个性能分析工具，用于理解和分析在AMD硬件上运行的应用程序的性能。
- [NVIDIA NSight](https://link.zhihu.com/?target=https%3A//developer.nvidia.com/tools-overview):该工具使开发人员能够使用NVIDIA最新的视觉计算硬件构建、调试、配置文件和开发一流的尖端软件。
- [Superluminal](https://link.zhihu.com/?target=https%3A//superluminal.eu/): Superluminal是一个高性能、高频的分析器，支持用c++、Rust和。net编写的Windows、Xbox One和PlayStation®上的分析应用程序。不过，这是一款付费产品，必须获得使用许可。

**PlayStation：**

- CPU分析器工具可用于PlayStation硬件。要了解更多细节，您需要成为注册的PlayStation开发人员:[从这里开始](https://link.zhihu.com/?target=https%3A//partners.playstation.net/) 。

**WebGL：**

- [Firefox Profiler](https://link.zhihu.com/?target=https%3A//profiler.firefox.com/):挖掘调用栈并查看Unity的火焰图，WebGL与Firefox Profiler一起构建(以及其他东西)。它还提供了一个比较工具，可以并排查看分析捕获。
- [Chrome DevTools Performance](https://link.zhihu.com/?target=https%3A//developer.chrome.com/docs/devtools/evaluate-performance/):这个web浏览器工具可以用来分析Unity WebGL构建。

**GPU调试与性能分析工具：**

Unity帧调试工具能捕捉并展示CPU发出的绘制调用，而下面的工具能帮助你知道GPU收到这些命令后做了些什么，其中的一些工具是平台特有的且提供了平台相关的集成：

- [RenderDoc](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/RenderDocIntegration.html%3F):桌面和移动平台的GPU调试器
- [Intel GPA](https://link.zhihu.com/?target=https%3A//software.intel.com/content/www/us/en/develop/tools/graphics-performance-analyzers.html):基于Intel平台的图形分析
- [Apple Frame Capture Debugging Tools](https://link.zhihu.com/?target=https%3A//developer.apple.com/documentation/metal/frame_capture_debugging_tools/):针对Apple平台的GPU调试
- [Visual Studio Graphics Diagnostics](https://link.zhihu.com/?target=https%3A//docs.microsoft.com/en-gb/visualstudio/debugger/graphics/visual-studio-graphics-diagnostics%3Fview%3Dvs-2019%26redirectedfrom%3DMSDN%26viewFallbackFrom%3Dvs-2015):针对基于directx的平台(如Windows或Xbox)选择此和/或PIX
- [NVIDIA Nsight Frame debugger](https://link.zhihu.com/?target=https%3A//docs.nvidia.com/gameworks/content/developertools/desktop/frame_debugger_ogl.htm):针对NVIDIA GPU的基于opengl的帧调试器
- [AMD Radeon Developer Tool Suite](https://link.zhihu.com/?target=https%3A//gpuopen.com/tools/):针对AMD GPU的GPU分析器
- [Xcode帧调试器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/2020.1/Documentation/Manual/XcodeFrameDebuggerIntegration.html):针对iOS和macOS

### Project Auditor

[Project Auditor](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/ProjectAuditor) 是一个试验性的工具，用来做项目脚本和设置的静态分析，其提供了追踪造成托管堆内存分配、低效项目配置及可能导致性能瓶颈的原因。

此工具是免费的，目前仅用于编辑器模式，且不是官方发布的包。详情请查阅其 [文档](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/ProjectAuditor/blob/master/Documentation~/index.md) 。

### 构建结果检查器

[Build Report Inspector](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.build-report-inspector%400.1/manual/index.html) (in Preview) 是一个编辑器脚本，它允许您访问有关上次构建的信息，以便您可以分析构建项目所花费的时间和构建的磁盘大小占用。

该脚本允许您在Editor UI中以图形方式检查这些信息，这可比访问具体的脚本API方便多了。

生成报告显示包含的资源和生成的代码大小的统计信息。

观看Unite Now关于 [优化二进制部署大小](https://link.zhihu.com/?target=https%3A//www.youtube.com/watch%3Fv%3D4JLpJHIdx7E) 的演示，了解如何优化构建大小。您还可以阅读 [Build Report Inspector文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.build-report-inspector%400.1/manual/%23%3A~%3Atext%3DBuild%2520Report%2520Inspector%2520is%2520an%2Cthe%2520builds%2520disk%2520size%2520footprint.%3F) 以获取更多信息。

## 内存

Unity为用户生成的代码和脚本使用自动内存管理。像值类型的局部变量这样的小块数据被分配给堆栈。较大的数据块和长期存储被分配给托管堆或本机堆。

垃圾回收器周期性地识别和释放未被使用的托管堆内存。资产垃圾收集在需要时运行，或者当你加载一个新场景时，它会释放本地对象和资源。虽然这是自动运行的，但检查堆中所有对象的过程可能会导致游戏断断续续或运行缓慢。

优化内存使用意味着要注意何时分配和释放托管堆内存，以及如何最大限度地减少垃圾收集的影响。

在 [Understanding the managed heap](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/performance-memory-overview.html) 可以获取更多信息。

![](https://pic2.zhimg.com/v2-8c9c95c854e58a937d7059ec2f25bdb3_1440w.jpg)

### 使用内存分析器

内存分析器插件获取托管堆内存的快照，以帮助您识别碎片和内存泄漏等问题。

使用Unity Objects选项卡来识别可以消除重复内存条目的区域或查找使用最多内存的对象。All of Memory选项卡显示Unity跟踪的快照中所有内存的分解。

通过 [Memory Profiler in Unity](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.memoryprofiler%40latest) 这个资料可以最大程度利用内存分析器来最大化内存利用率。

### 减少GC的影响

Unity使用 [Boehm-Demers-Weiser](https://link.zhihu.com/?target=https%3A//www.hboehm.info/gc/) 垃圾回收器算法，其会暂停程序代码且只在其回收工作结束后恢复业务代码运行。

注意某些不必要的堆分配，这可能会导致GC峰值：

- 字符串：C#的字符串是引用类型，这意味着每个新字符串会在托管堆上分配空间，即使该字符串只是临时使用。应当减少不必要的字符串创建及操作。避免解析基于字符串的数据文件，如JSON和XML，并以 ScriptableObjects 或MessagePack或Protobuf等格式存储数据。如果需要在运行时构建字符串，可以使用StringBuilder类。
- Unity函数调用：一些Unity API函数创建堆分配，特别是那些返回托管对象数组的函数。缓存对数组的引用，而不是在循环中间分配它们。另外，利用某些避免生成垃圾的函数。例如，使用GameObject.CompareTag而不是手动比较字符串与GameObject.tag（因为返回一个新字符串会产生垃圾）。
- 装箱：避免传递值类型变量代替引用类型变量。这会创建一个临时对象，随之而来的潜在垃圾会将值类型隐式地转换为类型对象(例如，int i = 123; object o = i)。相反，尝试使用您想要传入的值的具体类型。泛型也可以用于这些覆盖。
- 协程：虽然yield不产生垃圾，但是创建一个新的WaitForSeconds对象会产生。缓存和重用WaitForSeconds对象，而不是在生成行中创建它
- LINQ和正则表达：这两种方法都会在幕后产生垃圾。如果性能有问题，请避免使用LINQ和正则表达式。编写for循环并使用列表作为创建新数组的替代方法。
- 泛型集合和其他托管类型：不要在更新的每一帧中声明和填充一个列表或集合(例如，玩家特定半径内的敌人列表)。相反，让List成为MonoBehaviour的成员，并在Start中初始化它。在使用它之前，只需清空每一帧的集合。

更多信息，请参考 [垃圾回收最佳实践](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/performance-garbage-collection-best-practices.html) 的教程页。

### 尽可能定时垃圾收集

如果你确定垃圾收集冻结不会影响游戏中的特定点，你可以使用System.GC.Collect触发垃圾收集。

请参阅 [了解自动内存管理](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/performance-garbage-collector.html) ，以获得如何使用它的示例。

> 请注意，使用GC可以为一些C#调用添加读写障碍，这带来的开销很少，每帧脚本调用开销最多可增加1毫秒。为了获得最佳性能，理想的做法是在主要游戏循环中没有GC分配，并隐藏GC。收集用户不会注意到的地方。

### 使用增量垃圾收集器来分割GC工作负载

增量垃圾收集不是在程序执行期间创建一个长时间的中断，而是使用多个短得多的中断，将工作负载分配到许多帧上。如果垃圾收集正在影响性能，请尝试启用此选项，看看它是否可以减少GC峰值。使用Profile Analyzer来验证它对应用程序的好处。

注意：增量GC可以暂时帮助缓解垃圾收集问题，但是最好的长期做法是定位并停止触发垃圾收集的频繁分配。

![](https://pic4.zhimg.com/v2-19f45297ee2f4d95a57a66bc20a80a09_1440w.jpg)

### 堆查看器

![](https://pic3.zhimg.com/v2-db3c8ae3d0b1468fde0253cd30f8be26_1440w.jpg)

Heap Explorer是用于Unity的第三方的内存探查器、调试器、分析器。该包可用于获取给定框架的内存快照，并显示本机、托管和静态内存的清晰表格。堆资源管理器可以帮助你识别重复的资源，比如在多个assetbundle之间复制的纹理。

虽然它在功能上与Unity的内存分析器重叠，但仍有些人因为易于理解的UI/UX喜欢它。

## 编程与代码架构

Unity PlayerLoop包含与游戏引擎核心交互的功能。这个结构包括许多处理初始化和逐帧更新的系统。您的所有脚本都将依赖于此PlayerLoop创建游戏玩法。

在分析时，您将在PlayerLoop下看到项目的用户代码（EditorLoop下的编辑器组件）。

![](https://pic1.zhimg.com/v2-5a9f8d007a3694d588e30f7e11f8cfd0_1440w.jpg)

### 理解Unity PlayerLoop

确保你理解Unity框架循环的 [执行顺序](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/ExecutionOrder.html) 。每一个Unity脚本以预定的顺序运行几个事件函数。您应该了解Awake、Start、Update和其他创建脚本生命周期的函数之间的区别。你可以利用低级API为玩家的更新循环添加自定义逻辑。

请参考 [脚本生命周期流程图](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/ExecutionOrder.html%3F) 了解事件函数的具体执行顺序。

![](https://pic1.zhimg.com/v2-aad1f0af5c4e9de37437d6dc3dba3c1a_1440w.jpg)

### 尽量减少每帧运行的代码

考虑代码是否必须每一帧都运行。去掉不必要的逻辑Update, LateUpdate和FixedUpdate。这些事件函数被设计成方便地在每一帧中特定时候更新，我们需要找出那些不需要每帧更新的逻辑。尽可能只在事情发生变化时执行逻辑。

如果您确实需要使用Update，请考虑每n帧运行一次代码。这是应用时间切片的一种方法，时间切片是一种将繁重的工作负载分配到多个帧的常用技术。在本例中，我们运行 `ExampleExpensiveFunction` 每三帧一次：

```
private int interval = 3;
void Update()
{
    if (Time.frameCount % interval == 0)
        ExampleExpensiveFunction();
}
```

更好的是，如果 `ExampleExpensiveFunction` 在一组数据上执行一些操作，可以考虑使用时间切片每帧对该数据的不同子集进行操作。通过每帧执行1/n的工作，而不是每n帧执行所有的工作，最终会获得更稳定和可预测的整体性能，而不是看到周期性的CPU峰值。

诀窍是将它与其他帧上运行的其他工作交织在一起。在本例中，您可以在以下情况下“调度”其他昂贵的函数 `Time.frameCount % interval == 1` 或 `Time.frameCount % interval == 2` 。

或者，使用自定义的 `UpdateManager` 类(下文会提到)，每n帧更新一次订阅对象。

### 缓存昂贵函数返回的结果

`GameObject.Find` ， `GameObject.GetComponent` 和 `Camera.main` (在2020.2之前的版本中)可能非常昂贵，因此最好避免在 `Update` 方法中调用它们。此外，避免将昂贵的方法放在 `OnEnable` 和 `OnDisable` 中，如果它们经常被调用的话。

频繁调用这些方法可能会导致CPU峰值。只要有可能，在初始化阶段运行开销较大的函数(即 `Awake` 和 `Start` 事件函数中)。缓存所需的引用并在以后重用它们。

下面的例子展示的低效重复调用 `GetComponent` 方法：

```
void Update()
{
    Renderer myRenderer = GetComponent<Renderer>();
    ExampleFunction(MyRenderer);
}
```

事实上， `GetComponent` 调用只需要一次，之后就作为引用被缓存下来。被缓存的引用可以在 `Update` 中被重复使用而不再需要调用 `GetComponent`

```
private Renderer myRenderer;
void Start()
{
    myRenderer = GetComponent<Renderer>();
}
void Update()
{
    ExampleFunction(myRenderer);
}
```

### 避免使用空的Unity事件函数

即使是空的MonoBehaviour也需要资源，所以你应该删除空白的 `Update` 或 `LateUpdate` 方法。如果要使用这些方法进行测试，请使用预处理器指令如 `#if UNITY_EDITOR` 。这样你就可以随便地在编辑器下使用Update方法进行测试，而不用担心shipping版本的开销。这篇 [10000次Update调用](https://link.zhihu.com/?target=https%3A//blog.unity.com/technology/1k-update-calls%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 的博客能帮助你理解Unity如何执行 `MonoBehaviour.Update` 。

### 自定义一个UpdateManager

Update或LateUpdate的常见使用模式是仅在满足某些条件时运行逻辑。这可能导致大量的逐帧回调，除了检查此条件外，这些回调实际上不运行任何代码。

每次Unity调用Update或LateUpdate等Message方法时，它都会进行一次跨语言(interop)调用，即从C/C++端到托管C#端的调用。对于少数对象，这不是问题。当您有数千个对象时，这种开销开始变得显著。

如果您有一个大型项目，请考虑创建一个自定义的 `UpdateManager` 以这种方式 `Update` 或 `LateUpdate` (例如，开放世界游戏)。让活动对象在需要回调时订阅这个 `UpdateManager` ，不需要时退订。这种模式可以减少对 `MonoBehaviour` 对象的许多跨语言调用。

![](https://picx.zhimg.com/v2-272f3f4eee5ad90ee37545d88e8886e5_1440w.jpg)

![](https://pic4.zhimg.com/v2-d0dd70a3a187cb53c17a14792870630f_1440w.jpg)

参考 [Game engine-specific optimization techniques for Unity](https://link.zhihu.com/?target=https%3A//github.com/Menyus777/Game-engine-specific-optimization-techniques-for-Unity) ，可以看到其中的例子给出了具体实现，以及可能的性能提升。

### 移除Debug语句

日志语句(尤其是在Update、LateUpdate或fixeduupdate中的时候)会降低性能。在构建之前禁用Log语句。

为了更容易地做到这一点，可以考虑创建一个 [条件属性](https://link.zhihu.com/?target=https%3A//docs.microsoft.com/en-us/dotnet/api/system.diagnostics.conditionalattribute%3Fview%3Dnet-5.0) 和一个预处理指令。例如，像这样创建一个自定义类：

```
public static class Logging
{
    [System.Diagnostics.Conditional("ENABLE_LOG")]
    static public void Log(object message)
    {
        UnityEngine.Debug.Log(message);
    }
}
```
![](https://pica.zhimg.com/v2-b6fcce2efcb43b9c28355f1d4fda528c_1440w.jpg)

使用自定义类生成日志消息。如果在Player Settings>Scripting Define Symbols中禁用 `ENABLE_LOG` 预处理器，你所有的Log语句就一下子消失了。

同样的事情也适用于Debug类的其他用例，比如Debug、DrawLine和Debug.DrawRay。这些也仅供在开发期间使用，并且会对性能产生重大影响。

在Unity项目中处理字符串和文本是一个常见的导致性能问题的原因。移除Log语句以及他们昂贵的字符串格式化会有很大的帮助。

### 禁用堆栈跟踪日志

使用Player Settings中的堆栈跟踪选项来控制出现的日志消息类型。如果您的应用程序在发布版本中记录错误或警告消息(例如，在野外生成崩溃报告)，请禁用堆栈跟踪以提高性能。

![](https://pica.zhimg.com/v2-0151fca6a52b7676b3f66c8373e020aa_1440w.jpg)

### 使用哈希值代替字符串参数

Unity内部不使用字符串名称来命名动画器、材质和着色器属性。为了提高速度，所有属性名称都被散列到property中id，这些id实际上是用来定位属性的。

当对Animator、材质或着色器使用Set或Get方法时，使用整数值方法而不是字符串值方法。字符串方法只是执行字符串散列，然后将散列后的ID转发给整数值方法。

使用 `Animator.StringToHash` 用于Animator属性名和 `Shader.PropertyToID` 用于材质和着色器属性名称的。在初始化期间获取这些哈希值，并将它们缓存到变量中，以便在需要传递给Get或Set方法时使用。

### 选择正确的数据结构

数据结构的选择会影响每帧迭代数千次时的效率。不确定是为集合使用列表、数组还是字典？遵循C#数据结构的 [MSDN指南](https://link.zhihu.com/?target=https%3A//msdn.microsoft.com/en-us/library/7y3x785f) ，作为选择正确结构的一般指南。

### 避免运行时附加组件

在运行时调用 `AddComponent` 会带来一些成本。每当在运行时添加组件时，Unity必须检查是否有重复或其他所需组件。

用已经设置好的所需组件 [实例化Prefab](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Prefabs.html) 通常会更高效。

### 使用对象池

实例化和销毁会导致垃圾和GC峰值，这通常来说是个比较慢的过程。

![](https://pic3.zhimg.com/v2-5c7c2e49bdf230314120aaecc8774fae_1440w.jpg)

对象池是一种设计模式，它可以通过减少CPU运行重复的创建和销毁调用所需的处理能力来提供性能优化。相反，通过对象池，现有的GameObjects可以被反复使用。

对象池的关键功能是提前创建对象并将其存储在池中，而不是根据需要创建和销毁对象。当需要一个对象时，它从池中取出并使用。当它不再需要时，它会被送回池中，而不是被销毁。

与其定期实例化和销毁GameObjects(例如，枪射出的子弹)，不如使用可重复使用和回收的预分配对象池。

![](https://pic4.zhimg.com/v2-8979548afeb8f30ec780bb90fe273af7_1440w.jpg)

这减少了项目中托管内存分配的数量，并可以防止垃圾收集问题。

学习如何在Unity中 [使用pooling API（2021LTS）](https://link.zhihu.com/?target=https%3A//unity.com/how-to/use-object-pooling-boost-performance-c-scripts-unity%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 创建一个简单的对象池系统。

### 坐标变换一次，而不是两次

当移动变换时，使用 `Transfrom.SetPositionAndRotation` 同时更新位置和旋转。这避免了两次修改Transform组件的开销。

如果你需要在运行时实例化一个GO，一个简单的优化是在实例化期间设定parent和新定位：

```
GameObject.Instantiate(prefab, parent);
GameObject.Instantiate(prefab, parent, position, rotation);
```

有关脚本API的更多信息请参考 [文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Object.Instantiate.html%3F) 。

### 使用ScriptableObjects

将不变的值或设置存储在ScriptableObject中，而不是MonoBehaviour。ScriptableObject是一个位于项目内部的资产，您只需要设置一次。它不能直接连接到GameObject。

monobehaviour会带来额外的开销，因为它们需要GameObject(默认情况下是Transform)来充当宿主。这意味着您需要在存储单个值之前创建大量未使用的数据。ScriptableObject通过删除GameObject和Transform来减少内存占用。它还在项目级别存储数据，如果需要从多个场景访问相同的数据，这将非常有用。

一个常见的用例是拥有许多依赖于相同重复数据的游戏对象，这些数据并不需要在运行时进行更改。你可以将其汇集到一个ScriptableObject，而不是在每个GameObject上都有重复的本地数据。然后，每个对象存储对共享数据资产的引用，而不是复制数据本身。这是一个好处，可以为具有数千个对象的项目提供显著的性能改进。

在ScriptableObject中创建字段来存储您的值或设置，然后在monobehaviour中引用ScriptableObject。

![](https://picx.zhimg.com/v2-70a1376dc629b9d2c883d377bec7429d_1440w.jpg)

每次使用MonoBehaviour实例化对象时，使用ScriptableObject中的字段可以防止不必要的数据重复。

在软件设计中，这是一种被称为flyweight模式的优化。使用 `ScriptableObjects` 以这种方式重构代码可以避免复制大量值并减少内存占用。

观看这篇 [关于ScriptableObjects的介绍](https://link.zhihu.com/?target=https%3A//youtu.be/WLDgtRNK2VE) ，了解 `ScriptableObjects` 如何使您的项目受益。您还可以查看 [相关文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-ScriptableObject.html%3F) 。

要了解更多关于在Unity中使用设计模式的知识，请参阅电子书 [《用游戏编程模式升级你的代码》](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/level-up-your-code-with-game-programming-patterns) ，以了解更多关于使用设计模式的知识。

要了解有关在项目中使用ScriptableObjects的更多信息，请参阅电子书

[使用ScriptableObjects在Unity中创建模块化架构](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/create-modular-game-architecture-with-scriptable-objects-ebook%3Fungated%3Dtrue%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 。

### 避免使用Lambda语句

lambda表达式可以简化代码，但这种简化是有代价的。调用lambda也会创建一个委托。通过上下文(例如，this，一个实例成员，或一个局部变量)使委托的任何旧缓存失效。发生这种情况时，频繁调用它会产生大量内存流量。

在使用lambda表达式时重构任何包含闭包的方法。在这里查看如何做到这一点的 [示例](https://link.zhihu.com/?target=https%3A//blog.jetbrains.com/dotnet/2014/07/24/unusual-ways-of-boosting-up-app-performance-lambdas-and-linqs/) 。

### C# Job System

现代cpu有多个内核，但是应用程序需要多线程代码来利用它们。Unity的作业系统允许你将大型任务分成更小的块，并在那些额外的CPU内核上并行运行，这可以显著提高性能。

通常在多线程编程中，一个CPU执行线程，即主线程，创建其他线程来处理任务。一旦工作完成，这些额外的工作线程就会与主线程同步。

![](https://picx.zhimg.com/v2-47977a5717f9b457dbe6fe4a33ca6eef_1440w.jpg)

如果您有一些需要长时间运行的任务，那么这种多线程方法效果很好。然而，对于游戏应用程序来说，它的效率较低，因为它通常必须以每秒30-60帧的速度处理许多短任务。

这就是为什么Unity使用了一种稍微不同的多线程方法，称为 [C#作业(任务)系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystem.html%3F) 。它不是生成具有短生命周期的许多线程，而是将您的工作分解为称为作业的更小单元。

![](https://pica.zhimg.com/v2-2ad6851a218890e4692b34f16519d252_1440w.jpg)

这些作业进入一个队列，该队列安排它们在 [工作线程](https://link.zhihu.com/?target=https%3A//docs.microsoft.com/en-us/cpp/parallel/multithreading-creating-worker-threads%3Fview%3Dmsvc-160) 的共享池中运行。 [JobHandles](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemJobDependencies.html%3F) 帮助您创建依赖项，确保作业以正确的顺序运行。

多线程的一个潜在问题是竞争，当两个线程同时访问一个共享变量时，就会出现争用条件。为了防止这种情况，Unity多线程使用安全系统来隔离作业需要执行的数据。C#作业系统使用作业结构的 *副本* 启动每个作业，从而消除了竞争条件。

为了使用Unity的c#作业系统，需要遵循以下指导方针：

- 将类更改为结构。作业是实现 [IJob](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemCreatingJobs.html%3F) 接口的任何结构体。如果要在大量对象上执行相同的任务，还可以使用 [IJobParallelFor](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Unity.Jobs.IJobParallelFor.html%3F) 跨多个核心运行。
- 传递到作业中的数据必须是 [Blittable类型](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Blittable_types) 。删除引用类型，并仅将blittable的数据作为副本传递给作业。
- 因为为了安全起见，每个作业中的工作是隔离的，所以使用一个 [NativeContainer](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemNativeContainer.html%3F) 将结果发送回主线程。 [Unity Collections包](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.collections%400.17/manual/index.html%23data-structures%3F) 中的一个native container为本机内存提供了一个C#包装器。它的子类型(例如，NativeArray, NativeList, NativeHashMap，NativeQueue等)的工作方式与它们等效的C#数据结构类似。

参考 [文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystem.html) ，了解如何使用 [C#作业系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemOverview.html%3F) 在您自己的项目中优化CPU性能。

### Burst Compiler

[Burst Compiler](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.burst%401.5/manual/index.html%3F) 是对作业系统的补充。Burst翻译为IL/.NET字节码为 [LLVM](https://link.zhihu.com/?target=https%3A//llvm.org/) 优化后的本机代码。要访问它，只需从包管理器中添加 **com.unit.burst** 包。

Burst允许Unity开发人员在提高性能的同时继续使用C#的子集。

为脚本启用Burst编译器，需要如下步骤：

- 删除静态变量。如果你需要写一个列表，考虑使用 [NativeDisableContainerSafetyRestriction属性](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Unity.Collections.LowLevel.Unsafe.NativeDisableContainerSafetyRestrictionAttribute.html%3F) 修饰的NativeArray。这允许作业并行写入NativeArray。
- 使用 `Unity.Mathematics` 而不是 `Mathf.functions` 。
- 使用 [BurstCompiler属性](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.burst%401.1/api/Unity.Burst.BurstCompileAttribute.html%3F) 修饰作业的定义。
```
[BurstCompiler]
public struct MyFirstJob : IJob
{
    public NativeArray<float3> ToNormalize;
    public void Execute()
    {
        for (int i = 0; i < ToNormalize.Length; i++)
        {
            ToNormalize[i] = math.normalize(ToNormalize[i]);
        }
    }
}
```

这是一个有关Burst作业的示例，它在float3数组上运行并规范化向量。它使用前面提到过的的Unity数学包。

C#作业系统和Burst编译器都是Unity的一部分 [面向数据技术栈(DOTS)](https://link.zhihu.com/?target=https%3A//unity.com/dots%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 。然而，你也可以将它们与“经典”Unity GameObjects或 [实体组件系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.entities%400.17/manual/index.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 一起使用。

参考 [最新的文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/2022.2/Documentation/Manual/com.unity.burst.html) ，看看Burst如何与C#作业系统结合起来加速你的工作流程。

> 译者注：Unity的DOTS一直饱受诟病，知道Unite 2024上海站，Unity中国将部分团结引擎新写的DOTS迁到新的Unity DOTS里面才稍微好一点，但目前来说，单从学习目的来讲，直接去学团结引擎的DOTS更好，而且团结的DOTS有更好的性能更快的官方本土团队支持。

## 项目配置

这里有几个项目设置会影响您的性能。

### 关闭不必要的玩家或质量设置

在Player设置中，关闭自动图形API选项并且移除你不打算支持的图形API。这可以避免生成过多的着色器变体。同时还可以禁用老旧CPU的架构，除非你的应用程序打算支持他们。

在“Quality设置”中，禁用不必要的质量级别。

### 切换到IL2CPP

我们建议将脚本后端从Mono到IL2CPP(中间语言到c++)。这样做将提供更好的运行时性能。

请注意，这确实会增加构建时间。有些开发人员更喜欢在本地使用Mono来加快迭代，然后在构建机器和/或候选版本上切换到IL2CPP。参考 [优化IL2CPP构建时间文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/IL2CPP-OptimizingBuildTimes.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 来减少构建时间。

![](https://pic1.zhimg.com/v2-005b6f49c670b4ca6f9c0d2fe47ffff6_1440w.jpg)

使用此选项，Unity在为目标平台创建本机二进制文件(例如，.exe，.apk，.xap)之前会将脚本和程序集的IL代码转换为C++。

您还可以阅读 [介绍IL2CPP内部](https://link.zhihu.com/?target=https%3A//blog.unity.com/technology/an-introduction-to-ilcpp-internals%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 的博客文章了解更多细节，或者查阅 [编译器选项手册页面](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/IL2CPP-CompilerOptions.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) ，了解各种编译器选项如何影响运行时性能。

### 避免大层次结构

分解你的层次结构。如果你的GameObjects不需要嵌套在层次结构中，那就简化父类。较小的层次结构受益于多线程来刷新场景中的变换。复杂的层次结构会导致不必要的转换计算并增加垃圾收集的成本。

关于Transform的最佳实践，请参阅 [优化层次结构](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/2017/06/29/best-practices-from-the-spotlight-team-optimizing-the-hierarchy/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 和 [本Unite](https://link.zhihu.com/?target=https%3A//youtu.be/W45-fsnPhJY%3Ft%3D794) 演讲。

## 资产

资产流水线可以极大地影响应用程序的性能。经验丰富的技术美术可以帮助您的团队定义和执行资产格式、规范和导入设置，以实现顺利的流程。

不要依赖默认设置，使用特定于平台的覆盖选项卡来优化诸如纹理和网格几何等资产。不正确的设置可能导致更大的构建大小、更长的构建时间、较差的GPU性能和较差的内存使用。考虑使用 [Presets](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Presets.html) 功能来帮助自定义基线设置，以增强特定项目。

请参阅 [这本指南](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/HOWTO-ArtAssetBestPracticeGuide.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) ，了解导入美术资产的最佳实践。对于移动端特定的指南(当然也包含许多通用建议)，请查看Unity学习课程 [移动应用的3D美术优化](https://link.zhihu.com/?target=https%3A//learn.unity.com/course/3d-art-optimization-for-mobile-gaming-5474%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 。观看GDC 2023会议“ [游戏创作的每个阶段的技术tips](https://link.zhihu.com/?target=https%3A//youtu.be/o_QBMz0WZjI%3Flist%3DPLX2vGYjWbI0TkxPwhWgsBhvj-EwxJDt5x%26t%3D656) ”，以了解更多关于如何利用预设。

### 压缩纹理

考虑这两个使用相同模型和纹理的例子。与底部的设置相比，顶部的设置消耗的内存是底部设置的五倍多，在视觉质量上没有多大好处。

![](https://pic1.zhimg.com/v2-4e8e8575c51af9d224882faec0ab1a50_1440w.jpg)

[纹理压缩](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-TextureImporter.html%3F) 会在你正确应用时提供巨大的性能提升。

这可以加快加载时间，减少内存占用，并显著提高渲染性能。压缩纹理只使用未压缩的32位RGBA纹理所需内存带宽的一小部分。

参考这个 [不同平台纹理压缩格式的推荐列表](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-TextureImporterOverride.html%3F) ，根据你目标平台选择压缩格式：

- iOS / Android / Switch: 使用 **ASTC**.
- PC/XBox One/PS4: **BC7** (high quality) or **DXT1** (low/normal quality)

### 纹理导入设置

纹理可能会使用大量的资源。这里的导入设置非常关键。一般来说，试着遵循以下准则：

- **降低最大尺寸** ：使用能产生视觉上可接受的效果的最小设置。这是非破坏性的，可以迅速减少你的纹理内存。
- **使用2的幂(POT)** ：Unity需要POT尺寸的纹理来进行纹理压缩，如果尺寸不符合会填充到2的幂，进而造成内存占用/浪费。
- **关闭Read/Write Enabled选项** ：当启用时，此选项在CPU和gpu可寻址内存中创建一个副本，使纹理的内存占用增加一倍。在大多数情况下，保持禁用(仅在运行时生成纹理并需要覆盖它时，才启用此功能)。你也可以通过 `Texture2D.Apply` 来执行这个选项。应用，将makeNoLongerReadable设置为true。
- **禁用不必要的mipmaps** ：对于在屏幕上保持一致大小的纹理，例如2D精灵和UI图形，不需要mipmaps(对于距离相机不同的3D模型，保留mipmaps功能)。
![](https://picx.zhimg.com/v2-a41850152edb29ba4b222da8e61f4361_1440w.jpg)

### 对纹理使用图集

图集化是将几个较小的纹理组合成一个统一大小的较大纹理的过程。这可以减少绘制内容所需的GPU工作量(使用更少的绘制调用)并减少内存占用。

> 原理就跟读取单个大文件和多个小文件哪个更快一个道理

对于2D项目，你可以使用 [Sprite Atlas](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-SpriteAtlas.html) (Asset > Create > 2D > Sprite Atlas)，而不是渲染单独的精灵和纹理。

对于3D项目，您可以使用您选择的数字内容创建(DCC)包。一些第三方工具，如 [MA\_TextureAtlasser](https://link.zhihu.com/?target=https%3A//maxkruf.com/ma_textureatlas/) 或 [TexturePacker](https://link.zhihu.com/?target=https%3A//www.codeandweb.com/texturepacker) 也可以构建纹理地图集。

![](https://picx.zhimg.com/v2-e5f9a065594227979bd4c7777e2c90bf_1440w.jpg)

为任何不需要高分辨率地图的3D几何图形组合纹理和重新映射uv。可视化编辑器让你能够设置纹理图集或精灵表中的大小和位置并确定其优先级。

纹理包装器将单个地图整合成一个大纹理。然后，Unity可以发出单个绘制调用，以较小的性能开销访问打包的纹理。

### 检查多边形的数量

更高分辨率的模型意味着更多的内存使用和可能更长的GPU时间。你的背景几何真的需要一百万个多边形吗？

将场景中游戏对象的几何复杂性保持在最低限度，否则Unity必须将大量顶点数据推送到显卡上。

考虑在您选择的DCC包中减少模型。从摄像机的视角中删除不可见的多边形。例如，如果你从来没有看到橱柜的背面靠在墙上，那么这个模型在这方面就不应该有任何面。

![](https://picx.zhimg.com/v2-a3a2ae7b9cd16d5c601e764992e084bf_1440w.jpg)

请注意，瓶颈通常不是现代gpu上的多边形计数，而是多边形密度。我们建议在所有资产上执行美术传递，以减少远处物体的多边形数量。 [微三角形](https://link.zhihu.com/?target=https%3A//www.g-truc.net/post-0662.html) 可能是导致GPU性能低下的重要原因。

根据目标平台，研究通过高分辨率添加细节纹理来补偿低多边形几何。使用纹理和法线贴图代替增加网格的密度。

通过将尽可能多的细节放入纹理中来降低像素计算的复杂度。例如，将高光捕获到纹理中，以避免在片段着色器中计算高光。

要注意并记住定期进行配置，因为这些技术可能会影响性能，并且可能不适合您的目标平台。

### 网格导入设置

就像纹理一样，如果导入不正确，网格也会消耗多余的内存。为了最小化网格的内存消耗，有如下方法：

- 使用网格压缩：积极的网格压缩可以减少磁盘空间(然而，运行时的内存不受影响)。请注意，网格量化可能导致不准确，所以尝试压缩级别，看看什么对你的模型有效。
- 禁用读/写：启用此选项将在内存中复制网格，这将在系统内存中保留网格的一个副本，而在系统内存中保留另一个副本GPU内存。在大多数情况下，您应该禁用它(在Unity 2019.2及更早版本中，默认勾选此选项)。
- 禁用rig和混合形状：如果你的网格不需要骨骼或混合形状动画，尽可能禁用这些选项。
- 禁用法线和切线：如果你绝对确定网格的材料不需要法线或切线，取消这些选项以节省额外的费用。
![](https://pic4.zhimg.com/v2-2a6508929cbdead76bb2af6b16ea74c3_1440w.jpg)

### 其他网格优化方式

在玩家设置中，你也可以对你的网格进行一些其他的优化：

**顶点压缩：** 设置每个通道的顶点压缩。例如，除了位置和光图uv之外，您可以启用所有内容的压缩。这可以减少网格的运行时内存使用。

注意，每个网格的导入设置中的网格压缩 *覆盖* 顶点压缩设置。在这种情况下，网格的运行时副本是未压缩的，可能会使用更多的内存。

**优化网格数据：** 从网格中删除其材质不需要的那些数据(例如切线，法线，颜色和uv)。

### 对资产进行审计

通过自动化资产审计流程，您可以避免意外更改资产设置。有几个工具可以帮助标准化导入设置或分析现有资产。

**资产后处理器**

[AssetPostprocessor](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/AssetPostprocessor.html%3F) 允许你hook导入管线，并在导入资产之前或导入资产时运行脚本。这提示您在导入模型、纹理、音频等之前和/或之后自定义设置，其方式类似于预置，只不过是通过代码的方式实现。在GDC 2023的演讲“ [游戏创造的每个阶段的技术技巧](https://link.zhihu.com/?target=https%3A//youtu.be/o_QBMz0WZjI%3Flist%3DPLX2vGYjWbI0TkxPwhWgsBhvj-EwxJDt5x%26t%3D816) ”中了解更多关于这一过程的内容。

**Unity DataTools**

[Unity DataTools](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/UnityDataTools) 是一个由Unity提供的开源工具集合，旨在增强Unity项目中的数据管理和序列化能力。它包括用于分析和优化项目数据的特性，例如识别未使用的资产、检测资产依赖关系以及减少构建大小。

在官方仓库了解更多关于这些工具的信息，并在最佳实践指南中的 [理解Unity优化](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity.html%3F) 部分了解更多有关 [资产审计](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity4.html%3F) 的信息。

### 异步纹理缓冲区

Unity使用环形缓冲区将纹理推送到GPU。你可以通过 `QualitySettings.asyncUploadBufferSize` 手动调整这个异步纹理缓冲区。

如果上传速度太慢或者主线线程在一次加载多个纹理时停滞不前，请调整 [纹理缓冲](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/QualitySettings-asyncUploadBufferSize.html%3F) 。通常你可以将值(以MB为单位)设置为场景中需要加载的最大纹理的大小。

请注意，更改默认值可能会导致内存压力很大。同样，你不能在Unity分配完循环缓冲区后将其内存返回给系统。如果GPU内存过载，GPU卸载最近最少使用的纹理，并迫使CPU在下一次进入相机视锥体时重新加载它。

在 [Unity的内存管理指南](https://link.zhihu.com/?target=https%3A//unity3d.com/learn/tutorials/topics/best-practices/guide-optimizing-memory%3Fplaylist%3D30089%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 中阅读更多有关使用时间片唤醒时纹理缓冲区的内存限制。另外，请参阅帖子 [优化加载性能](https://link.zhihu.com/?target=https%3A//blog.unity.com/technology/optimizing-loading-performance-understanding-the-async-upload-pipeline%3F) ，研究如何使用异步上传管道提高加载时间。

### 流式加载Mipmaps和纹理

Mipmap流系统使您可以控制加载到内存中的Mipmap级别。要启用它，请转到Unity的质量设置(Edit > Project Settings> Quality)，并检查Texture Streaming。要启用Mipmaps的流式加载，在纹理导入设置的高级选项下面启用。

![](https://pic1.zhimg.com/v2-18eddde5cd8ca89ced392f4833a3838e_1440w.jpg)

![](https://pic3.zhimg.com/v2-c233c68a01ec73b7dc729c2c449832ee_1440w.jpg)

这个系统减少了纹理所需的内存总量，因为它只加载渲染当前摄像机位置所需的mipmaps。否则，Unity默认加载所有纹理。纹理流以少量的CPU资源，来节省潜在的大量GPU内存。

您可以使用 [Mipmap Streaming API](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/TextureStreaming-API.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 进行额外的控制。纹理流自动减少mipmap级别，以保持在用户定义的内存预算内。

### 使用Addressables资产系统

[可寻址资产系统](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/2019/07/15/addressable-asset-system/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 简化了你管理构成游戏的资产的方式。任何资产，包括场景、预制件、文本资产等等，都可以被标记为“可寻址”并赋予一个唯一的名称。然后，您可以从任何地方调用这个别名。

在游戏及其资产之间添加这种额外的抽象层次可以简化某些任务，例如创建一个单独的可下载内容包。Addressables也使得引用这些资源包更容易，无论资产包是本地的还是远程的。

![](https://pic4.zhimg.com/v2-2250feb67af0d7c61057f7f192a7c311_1440w.jpg)

从包管理器安装 [Addressables包](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.addressables%401.21/manual/index.html) 。因此，项目中的每个资产或预制件都具有“可寻址”的能力。在检查器中检查资源名称下的选项，为其分配一个默认的唯一地址。

![](https://pic1.zhimg.com/v2-fae704d527177da3fe5effcfb5fbfc40_1440w.jpg)

标记后，相应的资产将出现在“Window > Asset Management > Addressables > Groups”窗口。

![](https://pica.zhimg.com/v2-e630a8777c920e31d8d4232610ee6b2a_1440w.jpg)

无论资产是托管在其他地方还是存储在本地，系统都将使用Addressable Name字符串对其进行定位。可寻址的Prefab直到需要时才加载到内存中，并在不再使用时自动卸载其相关资产。

“ [来自优化战壕的故事：用可寻址地址节省内存](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/2021/03/31/tales-from-the-optimization-trenches-saving-memory-with-addressables/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) ”博客文章演示了一个如何组织Addressable Groups的例子以便更有效地使用内存。也可以查看 [Addressables概念介绍](https://link.zhihu.com/?target=https%3A//learn.unity.com/tutorial/addressables-introduction-to-concepts%235fade876edbc2a00225e815a%3F%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 这个学习模组来快速了解可寻址资产系统如何在您的项目中工作。

## 图形

Unity的图像工具可以让你在各种平台(从手机到高端主机和桌面)上创建漂亮的、优化的图像。由于照明和效果相当复杂，我们建议您在尝试优化之前彻底查看 [渲染管线文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/render-pipelines.html) 。

### 提交到渲染管线

优化场景照明并不是一门精确的科学。你的过程通常取决于你的艺术方向和渲染管道。

在你开始点亮场景之前，你需要选择一个可用的渲染管道。渲染管道执行一系列操作，将场景的内容显示在屏幕上。

Unity提供了三种预构建的渲染管道，具有不同的功能和性能特征，或者您可以自己创建新的渲染管线。

- [Bulit-in渲染管道](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/built-in-render-pipeline.html%3F) 是一种通用的渲染管线，只有有限的自定义功能。
- [通用渲染管道(URP)](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.universal%4011.0/manual/%3F) 是一个预先构建的 [可脚本化渲染管道](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/ScriptableRenderPipeline.html%3F) 。URP提供了艺术家友好的工作流程，可以在从移动到高端控制台和pc的一系列平台上创建优化的图形。URP最终将成为Unity的默认渲染管道，然而，具体日期尚未确定。内置渲染管道至少在2023年的下一个发布周期中仍然是一个可用的选项。

URP添加了内置渲染无法使用的图形和渲染功能管线。为了保持性能，它做出权衡，以减少照明和阴影的计算成本。如果你想接触到最多的目标平台，包括手机和VR，那么就选择URP。

在电子书中获得URP功能的完整概述 - [为高级Unity创作者介绍通用渲染管道](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/introduction-universal-render-pipeline-for-advanced-unity-creators%3FUNGATED%3DTRUE) 。

- [高清晰度渲染管道(High Definition Render Pipeline, HDRP)](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4011.0/manual/index.html%3F) 是另一个预构建的脚本渲染管道，专为尖端，高保真的图形。

HDRP的目标是高端硬件，如PC、Xbox和PlayStation。使用它来创建逼真的游戏，汽车演示或建筑应用程序。HDRP使用基于物理的照明和材料，并支持改进的调试工具。

在电子书中获得HDRP功能的完整概述 - [在高清渲染管道中照明的最终指南](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/the-definitive-guide-to-lighting-in-the-high-definition-render-pipeline-unity-2021-lts-edition%3Fungated%3Dtrue) 。

URP和HDRP工作在可脚本渲染管道(SRP)之上。这是一个瘦API层，允许您使用C#脚本。这种灵活性允许您自定义管道的几乎每个部分。您还可以基于SRP创建自己的 [定制渲染管线](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/srp-custom.html%3F) 。

请参阅 [Unity中的渲染管道](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/render-pipelines.html%3F) ，以获得可用管道的更详细比较。

![](https://pic4.zhimg.com/v2-3ae6886004f35847b30e1c795abdc269_1440w.jpg)

**主机平台的渲染管线**

要构建目标平台为PS4、PS5、Game Core Xbox的项目，这些平台每个都需要额外安装一个包，分别是：

- PS4：com.unity.render-pipelines.ps4
- PS5：com.unity.render-pipelines.ps5
- Xbox：com.unity.render-pipelines.gamecore

### 选择一条渲染路径

在选择渲染管线时，还应该考虑渲染路径。渲染路径表示与照明和阴影相关的一系列特定操作。渲染路径的选择取决于您的应用程序需求和目标硬件。

![](https://pic4.zhimg.com/v2-cc000c64ce7542fedad419e06e4098fd_1440w.jpg)

**前向渲染路径**

在前向渲染中，显卡投射几何体并将其分割成顶点。这些顶点被进一步分解成碎片或像素，渲染到屏幕上以创建最终图像。

管道将每个对象一次一个地传递给图形API。正向渲染带来了每个光的成本。场景中的灯光越多，渲染时间就越长。

![](https://pic4.zhimg.com/v2-d7ac2a22b0b4622ab5443d821db2079f_1440w.jpg)

内置渲染管道的前向渲染器在每个对象的单独通道中绘制每个光。如果你有多个灯光照射同一个GameObject，这可能会造成严重的过度绘制，因为重叠区域需要多次绘制相同的像素。尽量减少实时灯光的数量，以减少overdraw。

URP不是为每个光源渲染一次，而是为每个物体筛选光源。这允许在一个通道中计算照明，与内置渲染管道的前向渲染器相比，产生更少的绘制调用。

**延迟着色路径**

延迟着色中，光照并不是逐物体计算的。

![](https://pic1.zhimg.com/v2-84ae3fb7390132f8fa3130a32376b094_1440w.jpg)

![](https://picx.zhimg.com/v2-607c382ddea71271eda34ca068c6c191_1440w.jpg)

延迟着色推迟重度渲染工作，比如照明，到管线的后期阶段。延迟着色使用两次着色。

第一趟，也被称为G-Buffer几何渲染pass，Unity渲染GameObjects。这一趟渲染检索几种类型的几何属性并将它们存储在一组纹理中。G-buffer纹理可能包括：

- 慢发射和高光颜色
- 表面平滑度
- 遮挡
- 世界空间法线
- 发光+环境光+反射+光照贴图

第二趟，也被称为光照pass，Unity基于G-buffer中的信息去渲染场景的光照。想象一下，基于缓冲区而不是单个对象迭代每个像素并计算照明信息。因此，在延迟着色中添加更多的非阴影投射灯不会像前向渲染那样产生相同的性能影响。

虽然选择渲染路径本身不是优化，但它会影响您优化项目的方式。本节中的其他技术和工作流可能会根据您选择的渲染管线和渲染路径而有所不同。

### 优化Shader Graph

HDRP和URP都支持 [Shader Graph](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.shadergraph%406.9/manual/Getting-Started.html) ，这是一个创建着色器的可视化界面。这允许一些用户创建复杂的阴影效果，这可能是以前无法实现的。使用可视图形系统中的150多个节点来创建更多的着色器。您还可以使用该API创建自己的自定义节点。

![](https://pic1.zhimg.com/v2-72fe7042aa0d7bf83cf22b5c8fd31b00_1440w.jpg)

每个Shader Graph都由一个兼容的主节点开始，这决定了图形的输出。在可视化界面添加节点和操作符，并构建着色器逻辑。

这个ShaderGraph然后传递到渲染管道的后端。最终的结果是一个ShaderLab着色器，功能类似于用hsl或Cg编写的着色器。

优化一个ShaderGraph遵循许多适用于传统HLSL/Cg着色器的相同规则。你的Shader Graph处理得越多，它对应用程序性能的影响就越大。

如果你有CPU瓶颈，优化着色器不会提高帧率，但可能会提高手机平台的电池寿命。

如果是GPU瓶颈，可遵循以下准则来提升ShaderGraph的性能

- 大大削减你的节点：移除未使用的节点。除非有必要，否则不要更改任何默认值或连接节点。Shader Graph自动编译剔除掉任何未使用的特性。

尽可能将值烘焙成贴图。例如，不是使用节点来照亮纹理，而是将额外的亮度应用到纹理资源本身。

- 使用更小的数据格式：尽可能切换到更小的数据结构。如果不影响你的项目，考虑使用Vector2而不是Vector3。如果情况允许，你也可以降低精度(例如，half而不是float)。
![](https://picx.zhimg.com/v2-977dd18fdf6b13d79069f9b7208747d7_1440w.jpg)

- 减少数学操作：着色器操作每秒运行多次，所以尽可能优化任何数学运算符。尝试混合结果，而不是创建逻辑分支。使用常量，并在应用向量之前组合标量值。最后，将不需要出现在检查器中的任何属性转换为内联节点。所有这些增量加速都将对你的帧预算有所帮助。
- 创建一个预览分支：当graph变大时，编译速度可能会变慢。用一个单独的、更小的分支来简化你的工作流程，这个分支只包含你想要预览的操作，然后在这个更小的分支上更快地迭代，直到你达到你想要的结果。

如果分支没有连接到主节点，则可以安全地将预览分支留在图中。Unity在编译过程中删除不影响最终输出的节点。

- 手动优化：即使你是一个经验丰富的图形程序员，你仍然可以使用Shader Graph为基于脚本的着色器编写一些样板代码。选择Shader Graph资产，然后从上下文菜单中选择 复制着色器。

创建一个新的HLSL/Cg着色器，然后粘贴到复制着色器图中。这是一个单向操作，但它允许您通过手动优化获得额外的性能。

### 移除内置着色器设置

从图形设置(Edit > ProjectSettings > Graphics)中的始终包含的着色器列表中删除您不使用的每个着色器。在这里添加应用程序生命周期所需的着色器。

![](https://pic1.zhimg.com/v2-abd69d1036afb639df1db25bf2965250_1440w.jpg)

### 去除着色器变体

你可以使用 [Shader编译pragma指令](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SL-PragmaDirectives.html%3F) 为目标平台编译不同的Shader。然后，使用shader关键字(或 [Shader Graph关键字](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.shadergraph%4010.5/manual/Keywords.html) 节点)启用或禁用某些功能来创建 [shader变体](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SL-MultipleProgramVariants.html%3F) 。

着色器变体可以用于平台特定的功能，但会增加构建时间和文件大小。如果你知道它们不是必需的，你可以阻止着色器变体被包含在你的构建中。

解析 [Editor.log](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/LogFiles.html) 中的着色器时间和大小。定位以“Compiled shader”和“Compressed Shader”开头的行。

在示例日志中，TEST着色器可能会向你展示：

```
Compiled shader ‘TEST Standard (Specular setup)’ in 31.23s
    d3d9 (total internal programs: 482, unique: 474)
    d3d11 (total internal programs: 482, unique: 466)
    metal (total internal programs: 482, unique: 480)
    glcore (total internal programs: 482, unique: 454)
Compressed shader ‘TEST Standard (Specular setup)’ on d3d9 from 1.04MB to 0.14MB
Compressed shader ‘TEST Standard (Specular setup)’ on d3d11 from 1.39MB to 0.12MB
Compressed shader ‘TEST Standard (Specular setup)’ on metal from 2.56MB to 0.20MB
Compressed shader ‘TEST Standard (Specular setup)’ on glcore from 2.04MB to 0.15MB
```

上述日志中可以看出关于这个Shader的几个信息：

- 由于 `#pragma multi_compile` 和 `shader_feature` ，着色器扩展为482个变体。
- Unity将包含在游戏数据中的着色器压缩为压缩大小的总和： 0.14+0.12+0.20+0.15 = 0.61MB。
- 在运行时，Unity将压缩数据保存在内存中(0.61MB)，而当前使用的图形API的数据是未压缩的。例如，如果您当前的API是Metal，那么这将占2.56MB。

在构建之后， [Project Auditor](https://link.zhihu.com/?target=https%3A//github.com/Unity-Technologies/ProjectAuditor) 可以解析Editor.log来显示编译到项目中的所有着色器、着色器关键字和着色器变体的列表。它还可以在游戏运行后分析 [Player.log](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/LogFiles.html%3F) 。这将向您显示应用程序在运行时实际编译和使用的变体。

利用这些信息来构建一个可脚本编程的着色器剥离系统，并减少变量的数量。这可以改善构建时间、构建大小和运行时内存使用情况。

阅读 [剥离脚本着色器变体](https://link.zhihu.com/?target=https%3A//blog.unity.com/technology/stripping-scriptable-shader-variants%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 的博客文章，详细了解这个过程。

### 粒子模拟：粒子系统或VFX Graph

Unity包括烟雾，液体，火焰或其他效果的两个粒子模拟解决方案：

- [内置粒子系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Built-inParticleSystem.html%3F) 可在CPU上模拟数以千计的粒子。可以通过C#脚本去定义一个系统和它每个粒子。

粒子系统可以与Unity的底层物理系统和场景中的任何collider进行交互。粒子系统提供了最大的兼容性，并与任何Unity支持的构建平台工作。

![](https://picx.zhimg.com/v2-54f20ac052a4d9fa2f1e808806f57845_1440w.jpg)

- [VFX Graph](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/VFXGraph.html%3F) 使用计算着色器将计算移到了GPU上。这可以模拟数百万粒子的大规模视觉效果。工作流包括一个高度可定制的图形视图。粒子也可以与颜色和深度缓冲进行交互。
![](https://pic4.zhimg.com/v2-54f25d49c2d8ce0decb459ef6f0d11c3_1440w.jpg)

虽然它不能访问底层物理系统，但VFX图形可以与复杂的资产交互，如点缓存，矢量字段和有向距离场。VFX Graph只在 [支持HDRP和URP计算着色器的平台](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-ComputeShader.html%3F) 上工作。

在选择两种系统之一时，请考虑设备兼容性。大多数pc和主机支持 [计算着色器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-ComputeShader.html%3F) ，但许多移动设备不支持。如果你的目标平台不支持计算着色器，Unity允许你在你的项目中使用两种类型的粒子模拟。

了解更多关于创建高端视觉效果与电子书的最终指南 - [在Unity中创建高级视觉效果](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/definitive-guide-to-creating-visual-effects%3Fungated%3Dtrue) 。

### 用抗锯齿平滑画面

抗锯齿是非常可取的，因为它有助于平滑图像，减少锯齿边缘，并最大限度地减少镜面混叠。

如果你使用前向渲染与内置渲染管道， [Multisample抗锯齿(MSAA)](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Multisample_anti-aliasing) 在 [质量设置](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-QualitySettings.html%3F) 中可用。MSAA产生高质量的抗混叠，但它可能很昂贵。下拉菜单中的MSAA Sample Count (None, 2X, 4X, 8X)定义了渲染器使用多少采样来计算单个像素。

如果你正在使用URP或HDRP的前向渲染，你可以在渲染管道资产上启用MSAA。

![](https://pica.zhimg.com/v2-a09a18622d4d1ab3786cd594895dc3de_1440w.jpg)

或者，您可以选择添加抗锯齿作为后处理效果。这出现在Camera组件的“抗锯齿”下：

- 快速近似抗锯齿(FXAA)平滑每像素水平的边缘。这使用最少的资源密度去抗锯并得到轻微模糊最终图像。
- 亚像素形态抗锯齿(SMAA)基于图像的边界混合像素。这比FXAA有更清晰的结果，适合平面，卡通或干净的艺术风格

在HDRP中，你也可以使用FXAA和SMAA后抗锯齿相机。HDRP还提供了一个额外的选项：

- 时域抗锯齿(TAA)使用历史缓存中的帧来平滑边缘。这比FXAA更有效，但需要 [运动矢量](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4011.0/manual/Motion-Vectors.html) 才能工作。TAA还可以改善环境遮挡和体积。它通常比FXAA质量更高，但它需要更多的资源，并且偶尔会产生重影。
![](https://pic4.zhimg.com/v2-e83f21ebb28f04600e0681b377b215af_1440w.jpg)

### 常见的光照优化

虽然照明是一个巨大的主题，这些一般的技巧可以帮助你优化你的资源。

**烘焙光照贴图**

创建灯光的最快选择是不需要逐帧计算的。要做到这一点，使用 [Lightmapping](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Lightmappers.html) 来“烘焙”静态照明一次，而不是实时计算。

使用全局照明(GI)为静态几何体添加细致入微的照明。用Contribute GI标记对象，这样你就可以以Lightmaps的形式存储高质量的照明。

![](https://pic2.zhimg.com/v2-7b9c7178fba2ee2f78c7c49fd88a7a49_1440w.jpg)

生成光照贴图环境的过程比在Unity中在场景中放置光源要花更长的时间，但是：

- 运行速度更快，2–3 times faster for two-per-pixel lights（这个two-per-pixel是什么玩意）
- 看起来更好 - 全局光照可以计算逼真的直接和间接照明。lightmapper能使最终的贴图平滑并降噪。

烘焙的阴影和照明可以在不影响实时照明和阴影的情况下渲染。

复杂的场景可能需要很长的烘焙时间。如果您的硬件支持 **渐进式GPU Lightmapper** ，这个选项可以大大加快你的光图生成，在某些情况下高达十倍。

![](https://pic2.zhimg.com/v2-7e8774c7b6946f719e6f812af23ba16f_1440w.jpg)

遵循 [手册指南](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Lightmapping.html%3F) 和 [这篇关于优化照明的文章](https://link.zhihu.com/?target=https%3A//unity.com/how-to/advanced/optimize-lighting-mobile-games%3F) ，由此开始在Unity中使用灯光映射。

**减少反射探针的使用**

[反射探针](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-ReflectionProbe.html%3F) 可以创建真实的反射，但就合批而言，这可能非常昂贵。使用低分辨率立方体贴图、剔除蒙版和纹理压缩来提高运行时性能。使用 **Type: Baked** 来避免每帧更新。

如果在URP中必须使用 **Type: Realtime** ，请尽可能避免使用 **Every Frame** 。调整 [刷新模式](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rendering.ReflectionProbeRefreshMode.html%3F) 和 [时间切片](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rendering.ReflectionProbeTimeSlicingMode.html) 设置以降低更新速率。您还可以使用Via Scripting选项控制刷新，并从自定义脚本 [渲染探针](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/ReflectionProbe.RenderProbe.html) 。

如果在HDRP中需要使用 **Type: Realtime** ，请使用 **On Demand** 模式。您也可以在“项目设置> HDRP默认设置”中修改帧设置，降低实时反射下的质量和特性以提高性能。

**关闭阴影**

阴影投射可以被MeshRenderer和light禁用。尽可能禁用阴影，减少绘制调用。

你也可以使用一个模糊的纹理创建假阴影以应用到一个简单的网格或在你的角色下面的四边形。否则，您可以使用自定义着色器创建一团阴影。

![](https://pic3.zhimg.com/v2-022ac4f9d6bc1abc4b81066351ece44a_1440w.jpg)

特别要避免对点光源启用阴影。每个带阴影的点光源需要6个阴影贴图pass——与聚光灯的单个阴影贴图通道相比的话。考虑在动态阴影绝对必要的地方用聚光灯代替点灯。如果你可以避免动态阴影，使用立方体贴图作为 [Light.cookie](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Light-cookie.html) 代替点光源。

**替换一个着色器效果**

在某些情况下，你可以应用简单的技巧，而不是添加多个额外的灯光。例如，不是创建一个直接照进相机的光来给边缘照明效果，而是使用一个模拟边缘照明的着色器(参见 [表面着色器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SL-SurfaceShaderExamples.html) 的例子，在HLSL中实现这个)。

**使用光照层**

对于具有多个灯光的复杂场景，使用图层将对象分开，然后将每个灯光的影响限制在特定的剔除蒙版上。

![](https://pic2.zhimg.com/v2-748ceae11019875532702f7ff78a2c85_1440w.jpg)

**对运动对象或背景对象使用光探针**

Light Probes存储关于场景中空白空间的烘焙照明信息，同时提供高质量的照明(直接和间接)。他们使用 [球谐函数](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Spherical_harmonics) ，与动态光相比其计算速度非常快。这对移动的物体特别有用，因为它们通常不能接收烘焙的光照映射。

![](https://pic3.zhimg.com/v2-77ca88e4af1c4acc441ae9eb48e06fce_1440w.jpg)

光探针也可以应用于静态网格。在MeshRenderer组件中，找到Receive Global Illumination下拉菜单，并将其从 光映射 调整为 光探针。

继续对重要的关卡几何图形使用光照贴图，但将较小的细节切换到探针照明。光探头不需要适当的照明uv，这节省了你展开网格的额外步骤。探针也减少磁盘空间，因为它们不生成光图纹理。

![](https://pic2.zhimg.com/v2-dbdbb59cf3b6c0901d44fe663c18cec3_1440w.jpg)

![](https://pic3.zhimg.com/v2-aa02cc4db6829acdb28989dd41a58088_1440w.jpg)

请参阅 [使用光探针进行静态照明](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/2019/08/28/static-lighting-with-light-probes/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 博客文章，了解使用 [光探针](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/LightProbes.html%3F) 选择性地照亮场景对象的信息。

有关Unity中照明工作流程的更多信息，请阅读 [在Unity中制作可信的视觉效果](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/2020.1/Documentation/Manual/BestPracticeMakingBelievableVisuals.html) 。

## GPU优化

为了优化图形渲染，您需要了解目标硬件的限制以及如何分析GPU。分析可以帮助您检查和验证您正在进行的优化是否有效。

使用这些最佳实践来减少GPU上的渲染工作量。

### 对GPU进行基准测试

在进行分析时，从基准开始是很有用的。基准测试告诉您应该期望从特定gpu得到什么样的分析结果。

参见 [GFXBench](https://link.zhihu.com/?target=https%3A//gfxbench.com/result.jsp) 获取不同行业标准基准测试的GPU列表。该网站提供了当前的可用的gpu以及它们互相对比的一个很好的概述。

### 监视渲染统计数据

点击游戏视图右上角的Stats按钮。此窗口显示在Play模式下有关应用程序的实时渲染信息。使用这些数据来帮助优化性能：

- FPS：每秒帧数
- CPU Main：处理一帧的总时间（包括更新编辑器上的所有窗口）
- CPU Render：游戏视图窗口渲染一帧的总时间
- Batches：绘制调用命令被成组一起绘制的数量
- Tris (triangles) and Verts (vertices)：网格几何体
- SetPass calls：Unity必须切换着色器通道以在屏幕上渲染GameObjects的次数，每一个pass都可能引入额外的CPU开销。

注意：在编辑器中的fps不一定转化为构建性能。我们建议您配置您的构建以获得最准确的结果。在基准测试中，以毫秒为单位的帧时间是比每秒帧数更准确的度量，正如“帧数其实是一种带有欺骗性的度量方法”一节所述。

### 使用draw call合批

为了绘制一个GameObject, Unity向图形API发出一个绘制调用(例如，OpenGL, Vulkan或Direct3D)。每个绘制调用都是资源密集型的。绘制调用之间的状态变化(例如切换材料)可能会导致CPU端的性能开销。

PC和主机硬件可以承担许多绘制调用，但每个调用的开销仍然很高，因此需要尝试减少它们。在移动设备上，绘制调用优化至关重要。您可以使用 [draw call合批](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/DrawCallBatching.html%3F) 来实现这一点。

绘制调用合批将这些状态变化最小化，并降低渲染对象的CPU成本。Unity可以使用几种技术将多个对象组合成更少的批次：

- SRP Batching：如果您正在使用HDRP或URP，请在管线资产中的高级选项中启用 [SRP批处理](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/2019/02/28/srp-batcher-speed-up-your-rendering/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 程序。当使用兼容的着色器时，SRP批处理器减少了绘制调用之间的GPU设置，并使材料数据持久保存在GPU内存中。这可以显著加快CPU渲染时间。使用更少的着色器变体和最少量的关键字来改善SRP批处理。请参阅此 [SRP文档](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SRPBatcher.html%3F) ，了解您的项目如何利用此呈现工作流。
- GPU实例化：如果你有大量相同的对象(例如，建筑物，树木，草等具有相同的网格和材料)，此时就适合使用 [GPU实例化](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/GPUInstancing.html%3F) 。这种技术使用图形硬件对它们进行批处理。要启用GPU实例化，在项目窗口中选择你的材质，然后在检查器中勾选启用实例化。
- 静态合批：对于非移动几何体，Unity可以减少对共享相同材质的任何网格的绘制调用。它比动态批处理更有效，但它使用更多内存。

在Inspector中将所有从不移动的网格标记为静态合批。Unity在构建时将所有静态网格合并为一个大网格。 [StaticBatchingUtility](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/StaticBatchingUtility.html) 还允许您在运行时自己创建这些静态批处理(例如，在程序化生成一个非移动物件的关卡)。

![](https://picx.zhimg.com/v2-5ededb9f63911236c0c5a85c24594805_1440w.jpg)

- 动态合批：对于小网格，Unity可以在CPU上对顶点进行分组和变换，然后一次性绘制它们。注意：除非你有足够的低多边形网格(每个顶点不超过300个，顶点属性总数不超过900个)，否则不要使用这个功能，不然的话启用它将浪费时间CPU时间寻找小网格以进行合批。

你可以通过一些简单的规则来最大化合批的作用：

- 在场景中使用尽可能少的纹理。更少的纹理需要更少的独特材料，使它们更容易批量制作。此外，尽可能使用纹理地图集。
- 总是以最大的地图集尺寸烘烤光图。更少的光映射需要的材质状态变化更少，但要注意内存占用。
- 小心不要无意中实例化材质。访问 [Renderer.material](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Renderer-material.html%3F) 时，脚本中的材质会复制材质并返回对新副本的引用。这将破坏任何已经包含该材料的现有批处理。如果你想访问批处理对象的材质，使用 [Renderer.sharedMaterial](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Renderer-sharedMaterial.html%3F) 代替。
- 通过使用Profiler或优化期间的渲染数据，密切关注静态和动态批处理计数与总draw call的数量。

参考 [绘制调用合批](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/DrawCallBatching.html%3F) 文档以获取更多资讯。

### 检查帧调试器

Frame Debugger允许你在单个帧上冻结播放，并观察Unity如何构建场景来识别优化机会。寻找那些非必需渲染的游戏对象，并禁用它们以减少每帧的绘制调用。

![](https://pic3.zhimg.com/v2-216b430945af53deff29040668d0736a_1440w.jpg)

注意：帧调试器不显示单独的绘制调用或状态更改。只有Native GPU分析器给你详细的绘制调用和计时信息。但是，Frame Debugger在调试管线问题或批处理问题时仍然非常有用。

Unity Frame Debugger的一个优势是，你可以将绘制调用与场景中的特定游戏对象联系起来。这使得调查外部帧调试器可能无法解决的某些问题变得更加容易。

有关更多信息，请阅读 [Frame Debugger](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/FrameDebugger.html) 文档，并参阅前面的“使用平台原生性能分析工具和调试工具”一节，以获得特定于平台的调试工具列表。

### 优化填充率和减少过度绘制

填充率是指GPU每秒可以渲染到屏幕的像素数。

如果你的游戏受到填充率的限制，这意味着它试图在每帧中绘制比GPU所能处理的更多的像素。

在同一像素上多次绘制称为过度绘制（overdraw）。过度绘制会降低填充率并消耗额外的内存带宽。最常见的透支原因是：

- 重叠的不透明或透明的几何体
- 复杂的着色器，通常有多个渲染pass
- 未优化粒子
- 重叠的UI元素

虽然您希望将其影响降到最低，但解决overdraw没有放之四海而皆准的方法。从试验上述因素开始，逐渐减少它们的影响。

### 绘制顺序和渲染队列

为了防止overdraw，你应该了解Unity在渲染对象之前是如何对它们进行排序的。

内置渲染管道根据GO的 [渲染模式](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/StandardShaderMaterialParameterRenderingMode.html) 和 [renderQueue](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rendering.RenderQueue.html) 排序GO。每个对象的着色器将其放置在渲染队列中，而渲染队列通常决定了其绘制顺序。

在Unity实际将对象绘制到屏幕上之前，每个渲染队列可能遵循不同的排序规则。例如，Unity对不透明几何队列是从前往后排列的，而透明队列是从后往前排列的。

对象渲染在另一个对象之上就导致了overdraw。如果你使用内置渲染管道，你可以在 [场景视图控制栏](https://link.zhihu.com/?target=http%3A//docs.unity3d.com/Manual/ViewModes.html) 中可视化过度绘制，并切换到查看过度绘制模式。

![](https://pic2.zhimg.com/v2-bed15effdf16955df476c69960208905_1440w.jpg)

较亮的像素表示物体彼此重叠；暗像素意味着更少的overdraw。

![](https://pic1.zhimg.com/v2-1405e537e4b085bdc554e4f32ec133fe_1440w.jpg)

![](https://pic3.zhimg.com/v2-d67af667f44144b80f9c980cacc3fb96_1440w.jpg)

HDRP对渲染队列的控制略有不同。为了计算渲染队列的顺序，HDRP：

- 按共享材质分组网格
- 根据 [材质优先级](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4011.0/manual/Renderer-And-Material-Priority.html%3F) 计算这些组的渲染顺序
- 根据每个Mesh Renderer的Priority属性对每个组进行排序。

最终的队列是一个游戏对象列表，首先根据它们的材质优先级排序，然后根据它们各自的网格渲染器优先级排序。关于 [渲染器和材质优先级](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%406.7/manual/Renderer-And-Material-Priority.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 的这个网页更详细地说明了这一点。

为了可视化透明透支与HDRP，使用渲染管线调试窗口(Window > Render

Pipeline > Render Pipeline Debug)选择TransparencyOverdraw。

这个调试选项将每个像素显示为热图，从黑色(表示没有透明像素)到蓝色到红色(有透明像素的最大成本数)。

![](https://pic2.zhimg.com/v2-723616563b2c39cab1c1e9a3d650cc13_1440w.jpg)

在纠正Overdraw时，这些诊断工具可以提供可视化的优化晴雨表。

### 优化主机平台的图形效果

虽然面向Xbox和PlayStation开发游戏确实类似于PC平台，但这些主机平台也有自己平台的一些挑战。实现平滑的帧率通常意味着专注于GPU优化。

![](https://pic4.zhimg.com/v2-e361c285ebea8bfaa3f0e4a7541a5b0d_1440w.jpg)

**识别性能瓶颈**

首先，找到一个具有高GPU负载的帧。微软和索尼提供了很好的工具来分析你的项目在CPU和GPU上的性能。当涉及到这些平台的优化时，让Xbox的PIX和PlayStation的分析器工具成为你工具箱的一部分。

使用各自的本机分析器将帧成本分解为其特定部分。这将是您提高图形性能的起点。

![](https://pica.zhimg.com/v2-2a3c881f476d32b689f4115c28266e38_1440w.jpg)

**降低合批的总量**

与其他平台一样，主机上的优化通常意味着减少绘制调用批次。有一些技巧可能会有所帮助。

- 使用 [遮挡剔除](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/OcclusionCulling.html%3F) 去除隐藏在前景物体后面的物体，减少过度绘制。请注意，这需要额外的CPU处理，因此使用Profiler确保将工作从GPU转移到CPU是有益的。
- 如果你有许多对象共享相同的网格和材质，GPU实例化也可以减少批处理。限制场景中的模型数量可以提高性能。如果做得巧妙，你可以构建一个复杂的场景，而不会让它看起来重复。
- SRP Batcher可以通过批处理减少在DrawCalls之间的GPU设置 [绑定和绘制GPU命令](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SRPBatcher.html) 。为了从这个SRP批处理中受益，使用尽可能多的材料，但将它们限制为少量兼容的着色器(例如，URP和HDRP中的Lit和Unlit着色器)。

**启用图形作业**

在Player Settings > Other Settings中启用此选项以利用PlayStation或Xbox的多核处理器。Graphics Jobs (Experimental)允许Unity将渲染工作分散到多个CPU核心，消除渲染线程的压力。请参阅 [多线程渲染和图形作业教程](https://link.zhihu.com/?target=https%3A//learn.unity.com/tutorial/optimizing-graphics-in-unity%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 的详细信息。

**对后处理做分析**

确保使用针对主机优化的后期处理资产。来自Asset Store的最初为PC编写的工具可能会消耗比Xbox或PlayStation所需的更多资源，使用本机分析器无疑效果最好。

**避免曲面细分着色器**

曲面细分将形状细分为该形状的较小版本。这可以通过增加几何形状来增强细节。虽然有一些例子表明曲面细分是有意义的(如 [Book of the Dead](https://link.zhihu.com/?target=https%3A//assetstore.unity.com/packages/essentials/tutorial-projects/book-of-the-dead-environment-hdrp-121175%3F) 中的极其真实的树皮)，但一般情况下，我们还是要避免在主机上使用曲面细分，它们在GPU上可能很昂贵。

**用计算着色器替换几何着色器**

像曲面细分着色器一样，几何和顶点着色器可以在GPU上每帧运行两次——一次是在pre-z pass期间，另一次是在shadow pass期间。

如果你想在GPU上生成或修改顶点数据， [计算着色器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-ComputeShader.html%3F) 通常是比几何着色器更好的选择。在计算着色器中完成工作意味着实际渲染几何图形的顶点着色器可以相对快速和简单。

**将更高的wavefront占用率设为目标**

当你向GPU发送draw调用时，这项工作将分成许多wavefront，Unity将这些wavefront分配到GPU内的可用simd中。

每个SIMD都有一次可以运行的最大wavefront数。wavefront占用率是指相对于最大值，目前有多少wavefront在使用，这是衡量你如何利用GPU的潜力。PIX和Razor非常详细地显示了波前占用。

![](https://pic3.zhimg.com/v2-c0744fe102a5e3fe37c871342f43a2e0_1440w.jpg)

在 *Book of the Dead* 的这个例子中，顶点着色器wavefront显示为绿色。像素着色器波前显示为蓝色。在下图中，许多顶点着色器波前出现，但没有太多的像素着色器活动。这表明GPU的潜力没有得到充分利用。

如果你做了很多顶点着色器的工作，但没有产生像素，这可能表明效率低下。虽然低wavefront占用率并不一定是坏事，但这是一个开始优化着色器并检查其他瓶颈的指标。例如，如果由于内存或计算操作而出现stall，那么增加占用率可能有助于提高性能。另一方面，过多的wavefront可能会导致缓存抖动并降低性能。

**使用HDRP内置和自定义的pass**

如果您的项目使用HDRP，请利用其内置和自定义pass，这些有助于渲染场景。内置的pass可以帮助你优化着色器。HDRP包括几个注入点，您可以在其中添加自定义pass到着色器。

![](https://pic3.zhimg.com/v2-678fdc8b8a06fdad1fab4a1a2eb0c41c_1440w.jpg)

要优化透明材料的性能，请参阅页面渲染器和材质优先级。

**降低阴影贴图渲染目标的大小**

HDRP的高质量设置默认使用4K阴影贴图。降低阴影贴图分辨率并测量对帧成本的影响。但要注意你可能需要对光的设置造成任何变化的视觉质量做额外的补偿工作。

**充分利用异步计算**

如果你有一段时间GPU利用率不足，异步计算允许你将有用的工作移动到计算着色器中，跟图形队列并行工作。这样可以更好地利用这些GPU资源。

例如，在阴影贴图生成过程中，GPU执行深度渲染。在这一点上，很少有像素着色器工作发生，并且许多wavefront仍然未被占用。

![](https://pic3.zhimg.com/v2-682f84eca0beaca00a8eef2c044511ac_1440w.jpg)

如果你可以同步一些计算着色器工作与深度仅渲染，这能提高GPU的整体使用率。未使用的wavefront可以帮助屏幕空间环境遮挡或任何补充当前工作的任务。

![](https://pica.zhimg.com/v2-2a4f0b6c806d1bef17f3d7466eb32ad6_1440w.jpg)

在这个来自 *Book of the Dead* 的例子中，一些优化将阴影映射、光照传递和大气氛围的耗时减少了几毫秒。由此产生的帧成本允许应用程序在PlayStation®4 Pro上以30 fps运行。

观看 [优化高端主机的性能](https://link.zhihu.com/?target=https%3A//www.youtube.com/watch%3Fv%3DI5lzlGiJW0k) 中的性能案例研究，Unity图像开发者Rob Thompson讨论了如何移植Book of the Dead到PlayStation 4。你也可以阅读这张优化主机游戏图像的 [技巧列表](https://link.zhihu.com/?target=https%3A//unity.com/how-to/performance-optimization-high-end-graphics%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 以了解更多信息。

### 剔除

遮挡剔除会禁用被其他游戏对象完全隐藏(遮挡)的游戏对象。这可以防止CPU和GPU浪费时间来渲染永远不会被相机看到的对象。

每台摄像机都会进行 [剔除](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Hidden-surface_determination) 。它会对性能产生很大的影响，尤其是在同时启用多个摄像头的情况下。Unity使用两种类型的剔除，截锥体剔除和遮挡剔除。

- 在每个相机上自动执行 **截锥体剔除** 。它可以防止在 [视界平截头体](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/UnderstandingFrustum.html%3F) 之外的游戏对象被渲染，有助于优化性能。

你可以通过 [Camera.layerCullDistances](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Camera-layerCullDistances.html%3F) 手动设置 [每层剔除距离](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Documentation/ScriptReference/Camera-layerCullDistances.html%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 。这允许你在比默认的 [farClipPlane](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Camera-farClipPlane.html%3F) 更短的距离上剔除小的GameObjects。

将游戏对象组织到图层中。使用layerCullDistances数组为32层中的每一层分配一个小于farClipPlane的值(或者使用0作为farClipPlane的默认值)。

Unity首先按层进行筛选，只在相机使用的层上保留GameObjects。之后，截锥体剔除会移除摄像机截锥体外的所有GameObjects。截锥体筛选作为一系列作业执行，以利用可用的工作线程。

每个层剔除测试非常快(本质上只是一个位掩码操作)。然而，这一成本仍然会增加很多GameObjects。如果这对你的项目来说是一个问题，你可能需要执行一些系统来将你的世界划分为“扇区”，并禁用相机视锥外的扇区，以减轻Unity层/视锥剔除系统的一些压力。

- 遮挡剔除从游戏视图中移除任何游戏对象相机看不到他们。使用此功能可以防止渲染隐藏在其他对象后面的对象，因为这些对象仍然可被渲染并消耗资源。例如，如果门是关闭的，那渲染另一个房间是不必要的，因为相机无法看到房间内部。

启用遮挡剔除可以显著提高性能，但也需要更多的磁盘空间、CPU时间和RAM。Unity在构建过程中烘烤遮挡数据，然后需要在加载场景时将其从磁盘加载到RAM。

虽然相机视图外的截锥体剔除是自动的，但遮挡剔除是一个烘烤的过程。简单地将对象标记为Static.Occluders或Occludees，然后通过Window > Rendering > Occlusion Culling对话框进行烘焙操作。

查看 [遮挡剔除教程](https://link.zhihu.com/?target=https%3A//learn.unity.com/tutorial/working-with-occlusion-culling%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dasset-links-gmg-choose-unity-for-multiplatform%26utm_content%3Doptimize-game-performance-2020-lts-ebook) 了解更多信息。

![](https://pic3.zhimg.com/v2-e24936cc86115a25c9bc824192393650_1440w.jpg)

### 动态分辨率

**允许动态分辨率** 是一个相机设置，允许您动态缩放单个render target，以减少GPU上的工作量。在应用程序的帧率降低的情况下，您可以逐渐降低分辨率以保持一致的帧率。

如果性能数据显示由于gpu性能瓶颈将要导致帧率下降，Unity就会触发这种缩放。您也可以使用脚本手动先发制人地触发此缩放。这在接近应用程序中gpu密集的部分时很有用。如果采用渐进式的缩放，动态分辨率几乎让人看不出区别。

参考 [动态分辨率](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/DynamicResolution.html%3F) 教程页以获取额外的信息和支持该功能的平台列表。

### 多相机视图

有时候你可能需要在游戏过程中从多个角度进行渲染。例如，在FPS游戏中，通过不同的视野(FOV)分别绘制玩家的武器和环境是很常见的。

这可以在用广角FOV显示背景场景时，防止前景对象感觉太扭曲。

![](https://pic1.zhimg.com/v2-1f8d57fb358d6617e600706f1c1a2d20_1440w.jpg)

你可以在URP中使用 [相机堆叠](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.universal%4010.5/manual/camera-stacking.html) 来渲染多个相机视图。然而，仍然有重要的剔除和渲染为每个相机完成。无论它是否在做有意义的工作，每个摄像头都会产生一些开销，所以应当只使用渲染所需的Camera组件。在移动平台上，即使没有渲染，每个活动摄像头可以使用高达1毫秒的CPU时间。

![](https://pic3.zhimg.com/v2-6e1029bdbb99ecbdf49655b033b20cc6_1440w.jpg)

![](https://pic1.zhimg.com/v2-2d8a88488d96d385ef7ebb9fedf345fc_1440w.jpg)

### URP中的RenderObjects

在URP中，尝试自定义RenderObject，而不是使用多个摄像头。在Renderer Data资产中选择 **Add Renderer Feature** 。选择 **RenderObject (Experimental)** 。

![](https://pic1.zhimg.com/v2-5a8efbcff1c296efa087675c104d7310_1440w.jpg)

当覆盖每个RenderObject时，能够实现如下目的：

- 将其与Event关联，并将其注入呈现循环的特定时间
- 通过渲染队列过滤(透明或不透明)和LayerMask
- 影响“深度”和“模板”设置
- 修改相机设置(视野和位置偏移)
![](https://pic4.zhimg.com/v2-1f89685aa9fc1cafab5f196fced1ef2d_1440w.jpg)

### HDRP中的CustomPassVolumes

在HDRP中，您可以使用 [自定义Pass](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4010.5/manual/Custom-Pass.html%3F) 达到类似的效果。配置一个使用CustomPassVolumes的自定义Pass，这类似于使用 [HDRP Volume](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4010.0/manual/Volumes.html%3F) 。

一个自定义Pass能使你实现这些效果：

- 改变你场景中材质的外观
- 改变Unity渲染GO的顺序
- 将相机的Buffer读入Shader中

在 [HDRP中使用自定义通道](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4010.5/manual/Custom-Pass-Volume-Workflow.html%3F) 可以帮助您避免使用额外的相机和与之相关的额外开销。自定义通道在如何与着色器交互方面具有额外的灵活性。你也可以用 [c#扩展Custom Pass类](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition%4010.5/manual/Custom-Pass-Scripting.html%3F) 。

![](https://picx.zhimg.com/v2-e717f2d11da7395d1b5fca74bac49b47_1440w.jpg)

### 使用LOD

当物体向远处移动时， [细节级别](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/LevelOfDetail.html) 可以调整或切换它们，使用更简单的材质和着色器的低分辨率网格，以帮助GPU性能。

请参阅Unity Learn [LOD课程](https://link.zhihu.com/?target=https%3A//learn.unity.com/tutorial/working-with-lods-2019-3%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 了解更多细节。

![](https://pic2.zhimg.com/v2-4f9c1be57ff697ea7149a11ade73f3f1_1440w.jpg)

![](https://picx.zhimg.com/v2-e80eb3dd79948af5b7e81202070c61eb_1440w.jpg)

### 分析后处理效果

分析你的后处理效果，看看他们在GPU上的成本。有些全屏效果(如Bloom和景深)可能会很昂贵，但你可以不断尝试，直到找到视觉质量和性能之间的平衡点。

在运行时，后处理往往波动不大。一旦你确定了你的Volume覆写，从你的总帧预算取一个静态部分来分配你的后期效果。

![](https://pic2.zhimg.com/v2-1ee6934ac33fa73b5fdfaffa363bf57b_1440w.jpg)

## UI

Unity提供了两种UI系统：旧的Unity UI和新的UI Toolkit。 [UI Toolkit](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/UIElements.html) 旨在成为推荐的UI系统。它是为最大的性能和可重用性量身定制的，工作流程和创作工具受到标准web技术的启发，这意味着如果UI设计师和艺术家已经有设计网页的经验，他们会发现它很熟悉。

然而知道2022LTS，UI工具集都没能支持完 [Unity UI](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/com.unity.ugui.html) 和 [IMGUI](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/GUIScriptingGuide.html) 的一些特性。Unity UI和IMGUI更适合某些用例，并且需要支持遗留项目。有关更多信息，请参阅 [Unity中UI系统的比较](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/UI-system-compare.html%3F) 。

### 分离画布Canvas

如果你有一个大画布与成千上万的元素，更新一个UI元素力量整个画布来更新，这可能会生成一个CPU峰值。

利用UGUI支持多个画布的能力。将UI元素基于他们需要刷新的频率。保持静态的UI元素单独的画布上，同时更新在更小的画布上的动态元素。

确保每个Canvas中的所有UI元素具有相同的Z值、材质和纹理。

### 隐藏不可见UI元素

你的UI元素可能只是偶尔出现在游戏中(例如，当角色受到伤害时出现的生命条)。如果隐形的元素是激活的，它可能仍在使用绘制调用。显式禁用任何不可见的UI组件，并根据需要重新启用它们。

如果你只需要关闭Canvas的可见性，禁用Canvas组件而不是整个GameObject。当你重新启用它时，这可以防止你的游戏不得不重建网格和顶点。

### 限制GraphicRaycaster和关闭射线目标选项

像屏幕上的触摸或点击这样的输入事件需要GraphicRaycaster组件。这只是循环遍历屏幕上的每个输入点，并检查它是否在UI的RectTransform。在每个需要输入的画布(包括子画布)上都需要一个GraphicRaycaster。

虽然这不是一个真正的光线投射器(名字让人以为跟光线追踪有关)，但每个交叉检查都有一些费用。尽量减少图形光线投射器的数量，不要将它们添加到不需要交互的UI画布中。

![](https://pic1.zhimg.com/v2-e797962953a5d327af1f77199814d59e_1440w.jpg)

此外，在所有不需要它的UI文本和图像上禁用光线投射目标。如果UI包含许多元素，那么所有这些小的更改都可以减少不必要的计算。

![](https://pica.zhimg.com/v2-f831c935f6541ec9fb57f8c31d11d602_1440w.jpg)

避免使用布局组

布局组更新效率不高，所以要谨慎使用。如果你的内容不是动态的，就完全避免使用Pivot，而应该在比例布局中使用Pivot。否则，创建自定义代码以在 [Layout Group组件](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.ugui%401.0/manual/UIAutoLayout.html%3F) 设置UI后禁用它们。

如果您确实需要为动态元素使用布局组(水平、垂直、网格)，请避免嵌套它们以提高性能。

![](https://pic1.zhimg.com/v2-9b16ea78fda48c259f76eb1d2574f67a_1440w.jpg)

### 避免大型列表或网格视图

大型列表和网格视图的开销很大。如果您需要创建一个大的列表或网格视图(例如，屏幕上包含数百个物品的库存)，考虑重用较小的UI元素池，而不是为每个项目创建一个UI元素。查看这个示例 [GitHub项目](https://link.zhihu.com/?target=https%3A//github.com/boonyifei/ScrollList) ，看看它是如何工作的。

### 避免大量互相堆叠的元素

大量UI元素的分层(例如，在卡片战斗游戏中堆叠卡片)会造成Overdraw。自定义代码，以便在运行时将分层元素合并为更少的元素和批次。

### 使用全屏UI时隐藏所有其他东西

如果暂停或开始屏幕覆盖了场景中的其他所有内容，请禁用渲染3D场景的相机。同样，禁用任何背景隐藏在顶部画布后面的画布元素。

考虑在全屏UI中降低应用程序目标帧率（ `Application.targetFrameRate` ），因为你不需要以60fps更新。

### UI Toolkit性能优化技巧

UI Toolkit提供了优于Unity UI的性能，为最大性能和可重用性量身定制，并提供了受标准web技术启发的工作流和创作工具。它的主要优点之一是，它使用了专门为UI元素设计的高度优化的渲染管线。

以下是一些使用UI Toolkit优化UI性能的通用建议：

- **使用高效布局** ：高效布局指的是使用UI Toolkit提供的 [布局组](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/2022.3/Documentation/Manual/UIE-LayoutEngine.html) (如Flexbox)，而不是手动定位和调整UI元素的大小。布局组自动处理布局计算，这可以显著提高性能。它们确保UI元素根据指定的布局规则正确排列和调整大小。通过使用高效的布局，您可以避免手动布局计算的开销，并实现一致和优化的UI呈现。
- **避免Update中昂贵的操作** ：尽量减少Update方法中执行的工作量，特别是像UI元素创建、操作或计算这样的繁重操作。因为更新方法每帧调用一次，故应尽可能少地执行这些操作，或者在初始化期间执行这些操作。
- **优化事件处理** ：注意事件订阅，并在不再需要时取消订阅。过多的事件处理会影响性能，因此请确保只订阅必要的事件。
- **优化样式表** ：注意样式表中使用的样式类和选择器的数量。带有大量规则的大型样式表可能会影响性能。保持样式表精简，避免不必要的复杂性。
- **分析和优化** ：使用Unity的分析工具来识别UI中的性能瓶颈，并找出可以进一步优化的区域，例如低效的布局计算或过度的重绘。
- **在目标平台上测试** ：在目标平台上测试你的UI性能，以确保在不同设备上的最佳性能。性能可能因硬件功能而异，因此在优化UI时要考虑目标平台。

记住，性能优化是一个迭代过程。持续地分析、测量和优化UI代码，以确保它平稳高效地运行。

## 音频

虽然音频通常不是性能瓶颈，但您仍然可以优化以节省内存、磁盘空间或CPU使用率。

### 使用无损文件作为源文件

从WAV或AIFF等无损文件格式的声音资源开始。

如果你使用任何压缩格式(如MP3或Vorbis)，那么Unity将在构建时解压缩并重新压缩它。这将导致两次有损传递，降低最终质量。

![](https://pic2.zhimg.com/v2-bfe61d1217bdc4a18faea145e88356d1_1440w.jpg)

### 减少AudioClips数量

音频剪辑的导入设置可以节省运行时内存和CPU性能：

- 如果立体声音频文件不需要立体声上，启用 **强制单声道** 选项，节省运行时内存和磁盘空间。

空间音源应该使用AudioClips要么在单声道中创作，要么在其导入设置中启用强制单声道。如果你在空间中使用立体声音频源，音频数据会占用两倍的磁盘空间和内存；Unity必须在音频混合过程中将声音转换为单声道，这也需要额外的CPU处理时间。

![](https://picx.zhimg.com/v2-cc6b05b10d2883d7c6730435b4f864bf_1440w.jpg)

- **预加载音频数据** 确保Unity在初始化场景之前加载任何引用的AudioClips。然而，这可能会增加场景加载时间。
- 如果您的声音片段不是立即需要的，请异步加载它。检查 **后台加载** 。这将在一个单独的线程上延迟加载声音，而不会阻塞主线程。
- 设置采样率设置为优化采样率或覆盖采样率。对于移动平台，22050 Hz应该足够了。谨慎使用44100赫兹(即CD质量)。48000Hz过高。对于PC/主机平台，44100Hz是理想的。48000Hz通常是不必要的。
- 压缩AudioClip并降低压缩比特率。

对于手机平台，使用Vorbis来处理大多数声音(或者使用MP3来录制不打算循环播放的声音)。使用ADPCM处理短且经常使用的声音(例如，脚步声，枪声)。

对于PC和Xbox，请使用Microsoft XMA编解码器而不是Vorbis或MP3。微软推荐的压缩比在8:1到15:1之间。

对于Playstation，使用ATRAC9格式。它的CPU开销比Vorbis或MP3更少

- 正确的加载类型取决于音频片段的长度。

| 片段大小 | 使用示例 | 加载类型设置 |
| --- | --- | --- |
| 小(<200KB) | 嘈杂的音效(脚步声，枪声)，UI声音 | 使用加载时解压。这将声音解压缩为原始的16位PCM音频数据会产生很小的CPU成本，但在运行时将是最高效的。或设置为压缩在内存中和设置压缩格式为ADPCM。这提供了一个固定的3.5:1的压缩比，并且实时解压缩的成本很低。 |
| 中(>=200KB) | 对话，短音乐，中等/无噪音的声音效果 | 最优负载类型取决于项目的优先级。如果降低内存使用是优先级，请选择在内存中压缩。如果需要考虑CPU使用率，片段应该设置为加载时解压。 |
| 大(>350-400KB) | 背景音乐，环境背景噪音，长对话 | 设置为流式加载。流式传输有200 KB的开销，所以它只适合足够大的AudioClips。 |

### 优化混音器

除了AudioClip设置之外，还要注意AudioMixer的这些问题。

- [SFX混响效果](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-AudioReverbEffect.html%3F) 是AudioMixer最昂贵的音频效果之一。添加一个混音组与SFX混音(以及一个发送到它的混音组)将增加CPU成本。

即使没有AudioSource实际向组发送信号，也会发生这种情况。Unity的 [数字信号处理图(DSPGraph)](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Packages/com.unity.audio.dspgraph%400.1/manual/index.html%3F) 不区分它是否得到空信号。

![](https://pica.zhimg.com/v2-1f35e2e39c627a1ae2d50321d2c4f52e_1440w.jpg)

- 减少混音器组的数量以提高AudioMixer的性能。在单个父组下添加大量的子组会显著增加音频CPU成本。即使AudioSource直接输出到Master这种情况仍会发生，因为Unity的DSP不区分空信号。
![](https://pic1.zhimg.com/v2-36b557dbad3c986d61c1e37fa8a47a18_1440w.jpg)

- 避免只有单个子组的组。尽可能将2个混音组合成1个。
![](https://pic4.zhimg.com/v2-f40e3ce123e383d4612fb86dfe729031_1440w.jpg)

## 物理

物理可以创造复杂的游戏玩法，但这需要性能成本。当您知道这些成本时，您可以调整模拟以适当地管理它们。这些技巧可以帮助你保持在你的目标帧率的同时用Unity的内置物理(NVIDIA PhysX)。创造丝滑的物理反馈

### 简化碰撞体

网格碰撞器很昂贵。用基础碰撞体或简化的网格碰撞器代替更复杂的网格碰撞器来近似原始形状。

![](https://pic2.zhimg.com/v2-031713718ca50ee5b147d5ac074936d9_1440w.jpg)

### 优化设置选项

在Player Settings中，如有可能就该勾选预烘焙碰撞体网格。

![](https://pic1.zhimg.com/v2-4b94731b6818f987efe6881769c63144_1440w.jpg)

确保你编辑了你的物理设置(Project Settings > Physics)。尽可能简化你的图层碰撞矩阵。

![](https://pic4.zhimg.com/v2-7ef2d49a59a7ae09051e56ea4befd0bf_1440w.jpg)

### 调整模拟频率

物理引擎通过在固定的时间步长上运行来工作。要查看项目运行的固定速率，请转到Edit > Project Settings > Time。

![](https://pic4.zhimg.com/v2-bf070226471f0c3be10e0ff18c577c61_1440w.jpg)

Fixed Timestep字段定义了物理引擎每一步的时间步长。例如，默认值0.02秒(20毫秒)相当于50fps或50hz。

因为Unity中的每一帧都需要不同的时间，所以它并不能与物理模拟完美同步。引擎至多计算到下一个物理时间步。如果一帧运行得稍慢或稍快，Unity将使用经过的时间来知道何时在适当的时间步运行物理模拟。

如果一个帧需要很长时间来准备，这可能会导致性能问题。例如，如果你的游戏经历了一个高峰(例如，实例化许多游戏对象或从磁盘加载文件)，帧可能需要40毫秒或更长时间才能运行。对于默认的20毫秒固定时间步长，这将导致两个物理模拟在下一帧上运行，以“赶上”可变时间步长。

额外的物理模拟反过来又增加了处理帧的时间。在低端平台上，这可能会导致性能螺旋式下降。

后续的帧需要更长的时间来准备，使得物理模拟的积压也更长。这将导致更慢的帧和更多的模拟每帧运行。结果是表现越来越差。

最终，物理更新之间的时间间隔可能会超过最大允许时间步长。在此中断后，Unity开始放弃物理更新，游戏便会出现口吃。

为了避免物理的性能问题，有如下方法：

- 降低仿真频率。对于低端平台，增加固定时间步长略高于你的目标帧速率。例如，在移动设备上使用0.035秒换取30ps。这可能有助于防止性能螺旋式下降。
- 减小最大允许时间步长。使用较小的值(如0.1秒)会牺牲一些物理模拟的准确性，但也会限制在一帧内发生的物理更新次数。尝试不同的值，找到适合项目需求的值。
- 如果需要，手动模拟物理步骤。你可以在物理设置中禁用自动模拟，而直接调用 [Physics.Simulate](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.Simulate.html) 以在帧的更新阶段进行模拟。这允许你控制何时运行物理步骤。将Time.deltaTime传给Physics.Simulate以保持物理与模拟时间同步。

这种方法可能会导致复杂物理或高度可变帧时间场景的物理模拟不稳定，所以要谨慎使用。

![](https://pic2.zhimg.com/v2-49cfd4b47936ee5ccfbc6e1a402679c3_1440w.jpg)

### 修改网格碰撞器的CookingOptions

物理引擎使用的网格要经过一个叫做cook的过程，这个过程后准备好了网格，这样它就可以处理物理查询，比如光线投射、接触等等。

一个网格碰撞器有几个 [CookingOptions](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/MeshColliderCookingOptions.html%3Fhttp%3A//) 来帮助你验证物理网格。如果你确定你的网格不需要这些检查，你可以禁用它们来加快你的cook时间。

在每个网格碰撞器的CookingOptions中，取消选中EnableMeshCleaning,, WeldColocatedVertices和CookForFasterSimulation。这些选项对于运行时程序生成的网格很有价值，但如果你的网格已经有适当的三角形，则可以禁用这些选项。

此外，如果你的目标平台是PC，确保你保持启用Use Fast Midphase。在模拟的中期阶段，这将从PhysX 4.1切换到一个更快的算法(这有助于缩小物理查询的一小部分潜在相交三角形)。非桌面平台仍然必须使用较慢的生成r树算法。

![](https://pic2.zhimg.com/v2-95848385c77355f6d4705f2fad076afb_1440w.jpg)

### 使用Physics.BakeMesh

如果你在玩法中中程序化生成网格，你可以在运行时创建一个网格碰撞器。然而，将一个MeshCollider组件直接添加到网格中，会在主线程上烹饪/烘烤物理。这会消耗大量的CPU时间。

使用 [Physics.BakeMesh](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.BakeMesh.html) 为MeshCollider准备一个网格，并将烘烤的数据与网格本身一起保存。一个新的MeshCollider引用这个网格将重用这个预烘烤的数据(而不是再次烘烤网格)。这可以帮助减少场景加载时间或实例化时间。

为了优化性能，你可以用 [C#作业系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemOverview.html) 将网格烹饪卸载到另一个 [线程](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/JobSystemOverview.html) 。关于如何在多线程中烘烤网格的细节，请参考 [这个例子](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.BakeMesh.html) 。

![](https://pica.zhimg.com/v2-f4fa97b7e3e28aeafc07de6e4ed14e06_1440w.jpg)

### 对于大型场景使用箱形修剪

Unity物理引擎的运行分为两个步骤:

- 粗略阶段：它使用 [sweep and prune](https://link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Sweep_and_prune) 算法收集潜在的碰撞
- 精确阶段：引擎实际计算碰撞

粗略阶段有sweep and prune的默认设置(Edit > Project Settings > Physics > BroadPhase Type)可以产生false positive的世界，这种情况下的世界通常是平坦的，有许多碰撞器。

如果你的场景很大而且大部分是平的，为了避免这个问题，切换到 **Automatic Box Pruning** 或 **Multibox Pruning Broadphase** 。这些选项将世界划分为一个网格，其中每个网格单元执行清扫和修剪。

Multibox Pruning Broadphase允许您手动指定世界边界和网格单元的数量，而Automatic Box Pruning则是自动帮你计算这2个数量。

![](https://pic3.zhimg.com/v2-66a7fd2b85df476d7822a3d049e4ba16_1440w.jpg)

### 修改求解器迭代次数

如果您想更准确地模拟特定的物理物体，请增加其 `Rigidbody.solverIterations` 。

![](https://pic2.zhimg.com/v2-667cbdce7043bcb134a32b8a14555063_1440w.jpg)

这将覆盖Physics.defaultSolverIterations，它也可以在Edit > Project Settings > Physics > Default Solver Iterations修改。

为了优化你的物理模拟，在项目的defaultSolveIterations中设置一个相对较低的值。然后应用更高的自定义 `Rigidbody.solverIterations` 值到那些需要更多细节的单个实例。

### 禁用自动Transform同步

当你更新一个Transform时，Unity不会自动将其同步到物理引擎。Unity累积转换并等待物理更新执行或用户调用 [Physics.SyncTransforms](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.SyncTransforms.html) 。

如果你想更频繁地同步物理与Transform，你可以设置 `Physics.autoSyncTransform` 为true(也可以在Project Settings > Physics >

Auto Sync Transforms中找到)。在启用此属性时， [Transform](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Transform.html%3F) 上的任何 [刚体](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rigidbody.html%3F) 或 [碰撞体](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Collider.html%3F) 或它的子元素会自动更新Transform。

但是，除非绝对必要，否则应该禁用此功能。否则，一系列连续的物理查询(如光线投射)可能会导致性能损失。

![](https://picx.zhimg.com/v2-dda0ef5c970283e1533b569bb93d7fbd_1440w.jpg)

### 复用碰撞回调

`MonoBehaviour.OnCollisionEnter`, `MonoBehaviour.OnCollisionStay` 和 `MonoBehaviour.OnCollisionExit` 都需要传入一个碰撞实例作为参数，该碰撞实例会在托管堆上被分配然后必被垃圾回收。

为了减少产生的垃圾数量，启用 `Physics.reuseCollisionCallbacks`

(也可以在Projects Settings > Physics > Reuse Collision Callbacks)。启用了之后，Unity对每个回调只分配一个共用的碰撞实例。这减少了垃圾收集器的浪费并提高了性能。

注意：如果你在碰撞回调之外引用碰撞实例进行后处理，你必须禁用重用碰撞回调选项。

![](https://pic3.zhimg.com/v2-ea525b8801721344467043b8d6ea7f5a_1440w.jpg)

### 移动静态碰撞器

静态碰撞器是带有碰撞器组件但没有刚体的gameobject。

请注意，您可以移动静态碰撞器，这与术语“静态”相反。要做到这一点，只需修改物理体的位置。在物理更新之前累积位置变化并同步。你不需要为静态碰撞器 *添加刚体组件* 来移动它。

然而，如果你想让静态碰撞器以更复杂的方式与其他物理体交互，就需要给它一个 [运动学刚体](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rigidbody-isKinematic.html%3F) 。使用 [Rigidbody.position](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rigidbody-position.html%3F) 和 [Rigidbody.rotation](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Rigidbody-rotation.html%3F) 来移动它，而不是访问Transform组件。这保证了物理引擎更可预测的行为。

注意：在2D物理中，不要移动静态碰撞器，因为重建树非常耗时。

### 使用不会产生分配的查询

要在特定距离和特定方向检测和收集碰撞器，可以使用光线投射和其他物理查询，如 [BoxCast](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.BoxCast.html) 。

物理查询返回一个包含多个碰撞器的数组，如 [OverlapSphere](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.OverlapSphere.html) 或 [OverlapBox](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.OverlapBox.html) ，需要在托管堆上分配这些对象。这意味着垃圾收集器最终需要收集分配的对象，而如果在错误的时间发生分配，就可能会降低性能。

为了减少这种开销，可以使用这些查询的 **NonAlloc** 版本。例如，如果你使用OverlapSphere来收集一个点周围所有潜在的碰撞器，使用 [OverlapSphereNonAlloc](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.OverlapSphereNonAlloc.html) 代替。

这允许您传入一个碰撞器数组(是参数，也是结果返回值)来充当buffer。NonAlloc方法不会产生垃圾。否则，它的就跟产生分配的方法版本一样了。

注意：需要定义一个足够大的结果缓冲区NonAlloc方法。如果缓冲区的空间用完，它并不会增长。

### 将光线投射查询进行合批

你可以使用 [Physics.Raycast](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/Physics.Raycast.html%3F) 来运行光线投射查询。然而，如果你有大量的光线投射操作(例如，计算10,000个代理的视线)，这可能会占用大量的CPU时间。

使用C#作业系统和 [RaycastCommand](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/ScriptReference/RaycastCommand.html%3F) 来批处理查询。这从主线程中卸载了工作，这样光线投射就可以异步地并行进行。

### 用物理调试器可视化物理

使用物理调试窗口(Window > Analysis > Physics Debugger)来帮助解决任何碰撞器问题或差异，这显示了可以相互碰撞的游戏对象的颜色编码指示器。

![](https://pic3.zhimg.com/v2-b68e77b8a1ebd4b15814e87e3a8f61a6_1440w.jpg)

阅读 [物理调试](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/PhysicsDebugVisualization.html) 文档以获取更多信息。

## 动画

Unity的 [动画系统](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/AnimationOverview.html%3F) (有时称为Mecanim)相当复杂。它的工作流程包括几个关键组件：

![](https://picx.zhimg.com/v2-f766e207a2e10994444f44f77a8239cf_1440w.jpg)

- [动画片段](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/AnimationClips.html%3F) 包含关于特定对象应该如何随时间改变其位置、旋转或其他属性的信息。
- [动画控制器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-AnimatorController.html%3F) ，一个结构化的流程图系统，作为一个 [动画状态机](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/AnimationStateMachines.html) 。这将跟踪当前正在播放的片段，以及动画何时应该改变或混合在一起。
- 人形骨骼让您能够从任何来源(例如，动作捕捉，资产商店或其他第三方动画库) [重定位](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/Retargeting.html%3F) 双足动画到您自己的角色模型。Unity的 [Avatar](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/AvatarCreationandSetup.html%3F) 系统将人形角色映射到一个通用的内部格式，使上述过程成为可能。
- GameObject有一个 [Animator组件](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-Animator.html%3F) 将这些部分连接在一起。这个组件引用一个Animator Controller和一个Avatar(如果需要的话)。相应地，动画控制器引用它使用的动画剪辑。

下面的指导方针将帮助你在Unity中使用动画功能。

使用通用rig而不是人形rig

默认情况下，Unity使用通用rig导入动画模型，但开发人员在动画角色时经常切换到人形rig。需要注意rig的这些问题：

![](https://pic3.zhimg.com/v2-8e8ca18b68f07aa0d9942bea11bf03ce_1440w.jpg)

- 尽可能使用通用rig。即使在不使用时，每一帧人形rig也会计算逆运动学和动画重定位，因此，它们消耗的CPU时间比同等的通用Rig多30-50%。
- 当导入人形动画时，如果你不需要的话，可以使用Avatar Mask删除IK Goals或手指动画。
- 对于通用rig，使用根运动比不使用它更昂贵。如果你的动画不使用根运动，就不要指定根骨骼。

### 为简易动画使用替代方案

Animators主要用于人形角色。然而，它们经常被重新用于animate单个值(例如，UI元素的alpha通道)。应当避免过度使用动画器，特别是避免与UI元素结合使用，因为它们会带来额外的开销。

当前的动画系统针对动画混合和更复杂的设置进行了优化。它有用于混合的临时缓冲区，并且有采样曲线和其他数据的额外副本。

此外，如果可能的话，考虑根本不使用动画系统。创建 [曲线函数](https://link.zhihu.com/?target=https%3A//easings.net/) 或在可能的情况下使用第三方渐变库(例如 [DOTween](https://link.zhihu.com/?target=https%3A//assetstore.unity.com/packages/tools/animation/dotween-hotween-v2-27676%3F))。这些可以用数学表达式实现非常自然的插值。

### 避免缩放曲线

动画缩放曲线比动画平移和旋转曲线更昂贵。为了提高性能，应当避免缩放动画。

注意：这不适用于常量曲线(对于整个动画片段的长度具有相同值的曲线)。常数曲线是经过优化的，而且这些曲线比普通曲线更便宜。

### 只在可见时更新

将Animator的剔除模式设置为Based on Renderers，并当其不在屏幕上时禁用 [蒙皮网格渲染器](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/class-SkinnedMeshRenderer.html%3F) 的更新，这节省了Unity在角色不可见时更新动画的消耗。

### 优化工作流

场景级别的其他优化比如：

- 使用散列值而不是字符串来查询动画器。
- 实现一个小的AI层来控制动画器。你可以让它为OnStateChange, OnTransitionBegin和其他事件提供简单的回调。
- 使用State Tags来轻松匹配你的AI状态机和Unity状态机。
- 使用额外的曲线来模拟事件。
- 使用额外的曲线来标记你的动画，例如 [与目标匹配](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/TargetMatching.html%3F) 。

## 工作流与协作

在Unity中构建应用程序是需要大量的通力协作，通常涉及许多开发人员。确保为您的团队将项目设置了最优状态。

### 使用版本控制

作为团队的一部分，版本控制是必不可少的。它可以帮助你追踪bug和糟糕的版本。遵循良好的实践，比如使用分支和标签来管理里程碑和版本。

为了帮助进行版本控制合并，请确保您的编辑器设置将Asset Serialization Mode设置为Force Text。这空间效率较低，但使Unity以基于文本的格式存储场景文件。

![](https://pic4.zhimg.com/v2-dd9192729b846ecafd48f65b161f53fd_1440w.jpg)

如果您使用的是外部版本控制系统(如Git)，则可以在版本控制设置中，确认“模式”设置为“可见元文件”。

Unity还有一个内置的YAML(一种人类可读的数据序列化语言)工具，专门用于合并场景和预制件。有关更多信息，请参见Unity文档中的 [智能合并](https://link.zhihu.com/?target=https%3A//docs.unity3d.com/Manual/SmartMerge.html) 。

### Unity版本控制

除了脚本代码，大多数Unity项目都包含相当数量的美术资产。如果你想用版本控制来管理这些资产，可以考虑切换到 [Unity版本控制](https://link.zhihu.com/?target=https%3A//unity.com/solutions/version-control%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) (以前称为Plastic SCM)。即使有Git LFS, Git在处理大型二进制文件(>500 MB)时，不如使用较大存储库的Plastic SCM运行得好。

![](https://pic2.zhimg.com/v2-17c7b59ee31c207e2c1dc2074c9250c9_1440w.jpg)

Unity版本控制使你能够：

- 知道你的美术资产是安全备份的
- 跟踪每项资产的所有权
- 回滚到以前的资产迭代
- 在单个中央存储库上驱动自动化流程
- 在多个平台上快速安全地创建分支

此外，Unity版本控制可以帮助您使用出色的可视化工具集中开发。艺术家尤其喜欢用户友好的工作流程，因为它鼓励开发团队和美术团队更紧密地整合在一起。

![](https://pic1.zhimg.com/v2-da6998611bf70fcef704454d3b42f478_1440w.jpg)

要开始使用Unity版本控制，请查看我们的 [入门指南](https://link.zhihu.com/?target=https%3A//learn.unity.com/project/getting-started-with-plastic-scm) 。

### 拆分大型场景

大型、单一的Unity场景并不适合合作。将关卡分解成许多较小的场景，这样美工和设计师就可以在一个关卡上有效合作，同时将冲突的风险降至最低。

注意，在运行时，使用 `SceneManager.LoadSceneAsync` 并传递 `LoadSceneMode.Additive` 参数，你的项目可以额外加载场景。

### Accelerate Solutions用行业领先的专业知识助力到达下一阶段

Accelerate Solutions专注于帮助游戏工作室在多个用例中实现他们最雄心勃勃的目标，包括改进性能和优化、游戏规划和技术设计、项目加速、提高玩家kpi和盈利，以及交付具有挑战性的移植和迁移。我们的全球团队由Unity最资深的软件开发人员和技术美工组成，他们精通Unity引擎、多人游戏、云计算、开发、AI/ML和游戏设计。

团队的专长在于帮助你在游戏开发的任何阶段将游戏带到下一个阶段。优化主要集中于识别一般和特定的性能问题，如帧率、内存和二进制大小，以改善玩家体验和/或迭代时间。服务范围从咨询到完整的游戏开发。

**咨询**

在这项服务中，顾问将分析您的项目或工作流程，并就如何实现预期结果向您的团队提供指导和建议。

**协同开发**

与你的团队一起工作：Unity开发人员和/或团队将深入研究你的项目并实现预期的结果。

**定制化开发和完整游戏开发**

对于这些合作，加速解决方案团队将指派并与Unity内部团队或经验丰富的Unity游戏工作室团队合作，代表你领导和执行一个项目，从开始到完成拥有它。

要了解更多关于加速解决方案，请 [联系我们](https://link.zhihu.com/?target=https%3A//create.unity.com/contact-unity-expert) 。

### 用Unity Integrated Success移除障碍

[Integrated Success](https://link.zhihu.com/?target=https%3A//unity.com/success-plans/integrated-success) 是我们最完整的成功计划 - 适合您最复杂的项目，并帮助您的游戏充分发挥其潜力。从战略规划到不可预见的情况，我们都有。在这里获得洞察力，实际指导和优质技术支持，以确保您的项目成功。该计划提供了高级功能的访问权限，包括我们最快的响应时间，合作伙伴关系经理的专门战略支持，优先bug处理和LTS支持，以及年度深入项目审查。

Integrated Success也允许你选择性地添加读取和修改访问Unity源代码。对于想要深入研究Unity源代码以适应和重用其他应用程序的开发团队来说是不可多得的机会。

**通过项目评审优化你的游戏**

项目评审是Integrated Success包的重要组成部分。在年度回顾中学习如何优化你的项目。高级工程师对您的工作进行分析，并针对您的目标提供见解和可行的建议。

团队首先熟悉您的项目，然后使用各种分析工具来检测性能瓶颈，考虑现有的需求和设计决策。他们还试图确定性能可以优化的点，以获得更高的速度、稳定性和效率。

对于架构良好、构建时间较短的项目(模块化场景、大量使用AssetBundles等)，他们会进行调整和重新分析以发现新问题。

在团队无法立即解决问题的情况下，他们将尽可能多地获取信息，并在内部进行进一步调查，必要时咨询研发部门的专业开发人员。

虽然可交付成果可能会根据您的需求而有所不同，但研究结果将在书面报告中总结并提供建议。团队的目标是通过帮助识别潜在的障碍、评估风险、验证解决方案并确保遵循最佳实践来始终为您提供最大的价值。

**伙伴关系经理(PRM)**

除了项目审查，Unity Integrated Success还附带了一个合作伙伴关系经理(PRM) - 一位战略Unity顾问，作为您的内部倡导者和团队的延伸，帮助您最大限度地利用Unity。他们保持清晰的沟通方式，这样你就能随时了解情况，朝着你的目标努力。您的PRM为您提供所需的专业技术和运营专业知识，以先发制人地解决问题，并保持您的项目在启动之前和之后顺利运行。

要了解更多关于我们的Integrated Success package,、项目评审和项目管理机制，请 [联系](https://link.zhihu.com/?target=https%3A//create.unity.com/contact-unity-expert) 我们。

## Next steps

您可以在 [Unity博客](https://link.zhihu.com/?target=https%3A//blogs.unity3d.com/%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 和 [Unity社区论坛](https://link.zhihu.com/?target=https%3A//forum.unity.com/) 网站上找到其他优化技巧、最佳实践和新闻，以及通过 [Unity Learn](https://link.zhihu.com/?target=https%3A//learn.unity.com/) 和#unitytips标签。

性能优化是一个广泛的主题，需要仔细关注。了解目标硬件的运行方式及其局限性是至关重要的。为了找到满足设计需求的有效解决方案，你需要掌握Unity的类和组件、算法和数据结构，以及平台的分析工具。

Unity的团队总是在这里帮助你找到合适的工具和服务来支持你的游戏开发过程，从概念到商业化。如果您已经准备好开始，您可以 [现在访问Unity Pro](https://link.zhihu.com/?target=https%3A//unity.com/pages/choose-unity-pro-game-development%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 或与 [我们的专家之一交谈](https://link.zhihu.com/?target=https%3A//create.unity.com/contact-unity-expert) ，了解我们准备帮助您实现愿景的所有方式。

### 更多资源

《 [创建c#风格指南：编写整洁的可伸缩代码](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/create-code-style-guide-e-book%3Fungated%3Dtrue) 》可以帮助您开发一个风格指南，以帮助您统一创建更具内聚性的代码库的方法。

《 [用游戏编程模式升级你的代码](https://link.zhihu.com/?target=https%3A//resources.unity.com/games/level-up-your-code-with-game-programming-patterns%3Fungated%3Dtrue) 》重点介绍了在Unity项目中使用SOLID原则和通用编程模式创建可扩展游戏代码架构的最佳实践。

《在Unity中用ScriptableObjects创建模块化游戏架构》是我们从中级编程高级Unity程序员系列中的第三个指南。每个指南都是由经验丰富的程序员撰写的，为开发团队重要的主题提供了最佳实践。

### Unity创作者的专业培训

Unity专业培训为您提供在Unity中更高效地工作和高效协作的技能和知识。提供一个为在任何行业，在任何技能水平专业人士设计的广泛的培训目录，该目录能以多种格式获取。

所有材料都是由经验丰富的教学设计师与我们的工程师和产品团队合作创建的。这意味着你总是接受最新的Unity技术的最新培训。

[了解更多](https://link.zhihu.com/?target=https%3A//unity.com/learn/professionals%3Futm_source%3Ddemand-gen%26utm_medium%3Dpdf%26utm_campaign%3Dclean-code%26utm_content%3Dconsole-pc-performance-optimization-ebook) 关于Unity专业培训如何支持您和您的团队。

编辑于 2025-09-07 00:01・广东[程序员0基础入门大模型的学习路线！](https://zhuanlan.zhihu.com/p/31864213680)

[

0基础入门大模型，transformer、bert这些是要学的，但是 你的第一口不一定从这里咬下去。真的没有必要一上来就把时间精力全部投入到复杂的理论、各种晦涩的数学公式还有编程语言上，这...

](https://zhuanlan.zhihu.com/p/31864213680)

赞同 70