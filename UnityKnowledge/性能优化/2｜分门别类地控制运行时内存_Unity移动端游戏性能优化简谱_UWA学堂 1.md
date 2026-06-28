---
title: "2｜分门别类地控制运行时内存_Unity移动端游戏性能优化简谱_UWA学堂"
source: "https://edu.uwa4d.com/lesson-detail/430/2110/0?isPreview=0"
author:
published:
created: 2026-06-28
description: "2.1 总览2.1.1 运行时内存占用首先，在讨论内存相关的各项参数和制定标准之前，我们需要先理清在各种性能工具的统计数据中常出现的各种内存参数的实际含义。在包括UWA在内的多种性能工具中，我们最常见到和关心的PSS（Proportional Set Size）Total内存，其含义为一个进程在RAM中实际使用的空间地址大小，即实际使用的物理内存（比例分配共享库占用的内存，按照进程数等比例划分），"
tags:
  - "clippings"
---
## 3｜以模块思维划分的CPU耗时调优

### 3.1 总览

**3.1.1 模块划分**

UWA将CPU中工作内容明确、耗时占比一般较高的函数整理划分为：渲染、UI、物理、动画、粒子、加载、逻辑等模块。但这并不意味着模块之间的工作互相独立毫无关联。举例而言，渲染模块的性能压力势必受到复杂的UI和粒子影响，而加载模块的很多操作实际上都是在逻辑中调用并完成的。

划分模块有利于我们确认问题、找到重点。与此同时，也要建立起模块之间的关联，有助于更高效地解决问题。

**3.1.2 耗时瓶颈**

当一个项目由于CPU端性能瓶颈而产生帧率偏低、卡顿明显的现象时，如何提炼出哪个模块的哪个问题是造成性能瓶颈的主要问题就成了关键。尽管我们已经对引擎中主要模块做了整理，各个模块间会出现的问题还是会千奇百怪不可一以概之，而且它们对CPU性能压力的贡献也不尽相同。那么我们就需要对什么样的耗时可以认为是潜在的性能瓶颈有准确的认知。

在移动端项目中，我们CPU端性能优化的目标是能够在中低端机型上大部分时间跑满30帧的流畅游戏过程。为了达成这一目标，简单做一下除法就得到我们的CPU耗时均值应控制在33ms以下。当然，这并不意味着CPU均值已经在33ms以下的项目就已经把CPU耗时控制的很好了。游戏运行过程中性能压力点是不同的，可能一系列UI界面中压力很小、但反过来游戏中最重要的战斗场景中帧率很低、又或者是存在大量几百毫秒甚至几秒的卡顿，而最终平均下来仍然低于33ms。

为此，UWA认为，在一次测试中，当33ms及以上耗时的帧数占总帧数的10%以下时，可以认为项目CPU性能整体控制在正常范围内。而这个占比越高，说明当前项目的CPU性能瓶颈越严重。

以上的讨论内容主要是围绕着我们对CPU性能的宏观的优化目标，和内存一样，我们仍要结合具体模块的具体数据来排查和解决项目中实际存在的问题。

---

### 3.2 渲染模块

围绕渲染模块相关优化更全面的内容可以参考 [《Unity性能优化系列—渲染模块》](https://blog.uwa4d.com/archives/UWA_ReportModule1.html) 。

**3.2.1 多线程渲染**

一般情况下，在单线程渲染的流程中，在游戏每一帧运行过程中，主线程（CPU1）先执行Update，在这里做大量的逻辑更新，例如游戏AI、碰撞检测和动画更新等；然后执行Render，在这里做渲染相关的指令调用。在渲染时，主线程需要调用图形API更新渲染状态，例如设置Shader、纹理、矩阵和Alpha融合等，然后再执行DrawCall，所有的这些图形API调用都是与驱动层交互的，而驱动层维护着所有的渲染状态，这些API的调用有可能会触发驱动层的渲染状态地改变，从而发生卡顿。由于驱动层的状态对于上层调用是透明的，因此卡顿是否会发生以及卡顿发生的时间长短对于API的调用者（CPU1）来说都是未知的。而此时其它CPU有可能处于空闲等待的状态，从而造成浪费。因此可以将渲染部分抽离出来，放到其它的CPU中，形成单独的渲染线程，与逻辑线程同时进行，以减少主线程卡顿。

其大致的实现流程是，在主线程中调用的图形API被封装成命令，提交到渲染队列，这样就可以节省在主线程中调用图形API的开销，从而提高帧率；渲染线程从渲染队列获取渲染指令并执行调用图形API与驱动层交互，这部分交互耗时从主线程转到渲染线程。

而Unity在Project Settings中支持且默认开启了Multithreaded Rendering，一般建议保持开启。在UWA的大量测试数据中，还是发现有部分项目关闭了多线程渲染。开启多线程渲染时，CPU等待GPU完成工作的耗时会被统计到Gfx.WaitForPresent函数中，而关闭多线程渲染时这一部分耗时则被主要统计到Graphics.PresentAndSync中。所以，项目中是否统计到Gfx.WaitForPresent函数耗时是判断是否开启了多线程渲染的一个依据。特别地，在项目开发和测试阶段可以考虑暂时性地关闭多线程渲染并打包测试，从而更直观地反映出渲染模块存在的性能瓶颈。

对于正常开启了多线程渲染的项目，Gfx.WaitForPresent的耗时走向也有相当的参考意义。测试中局部的GPU压力越大，CPU等待GPU完成工作的时间也就越长，Gfx.WaitForPresent的耗时也就越高。所以，当Gfx.WaitForPresent存在数十甚至上百毫秒地持续耗时时，说明对应场景的GPU压力较大。

![loading](https://videos2.uwa4d.com/image069.1654596781648.png "UWA")

另外，根据UWA的大量项目和测试经验，GPU压力过大也会使得渲染模块CPU端的主函数耗时（Camera.Render和RenderPipelineManager.DoRenderLoop\_Internal）整体相应上升。我们会在最后专门讨论GPU部分的优化。

**3.2.2 同屏渲染面片数**

影响渲染效率的两个最基本的参数无疑就是Triangle和DrawCall。

通常情况下，Triangle面片数和GPU渲染耗时是成正比的，而对于大部分项目来说，不透明Triangle数量又往往远比半透明Triangle要多，尤其需要关注。UWA一般建议在低端机型（4G内存的）上将同屏渲染面片数控制在25万面以内，即便是高端机也不建议超过60万面。当使用工具发现局部同屏渲染面片数过高后，可以结合Frame Debugger对重点帧的渲染物体进行排查。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image071.1654596938598.png "UWA")

常见的优化方案是，在制作上需要严格控制网格资源的面片数，尤其是一些角色和地形的模型，应严格警惕数万面及以上的网格；另外，一个很好的方法是一通过LOD工具减少场景中的面片数——比如在低端机上使用低模、减少场景中相对不重要的小物件的展示——进而降低渲染的开销。

需要指出的是，UWA工具所关注和统计的面片数量并不是当前帧场景模型的面片数，而是当前帧所渲染的面片数，其数值不仅与模型面片数有关，也和渲染次数相关，更加直观地反映出同屏渲染面片数造成的渲染压力。例如：场景中的网格模型面片数为1万，而其使用的Shader拥有2个渲染Pass，或者有2个相机对其同时渲染；又或者使用了SSAO、Reflection等后处理效果中的一个，那么此处所显示的Triangle数值将为2万。所以，在低端机上应严格警惕这些一下就会使同屏渲染面片数加倍的操作，即便对于高端机也应做好权衡，三思而后用。

**3.2.3 Batch（DrawCall）**

在Unity中，我们需要区分DrawCall和Batch。在一个Batch中会存在有多个DrawCall，出现这种情况时我们往往更关心Batch的数量，因为它才是把渲染数据提交给GPU的单位，也是我们需要优化和控制数量的真正对象。

降低Batch的方式通常有动态合批、静态合批、SRP Batcher和GPU Instancing这四种，围绕Batch优化的讨论较为复杂，再写一篇文章也不为过，所以本文不再展开来讨论，但在UWA DAY 2020中我们详细讨论和分享了DrawCall与Batch的关系以及这4种Batching的使用详解，供大家参考： [《Unity移动游戏项目优化案例分析（上）》](https://edu.uwa4d.com/course-intro/1/197) 。

下面简单总结静态合批、SRP Batcher和GPU Instancing的合批条件和优缺点。

**1\. 静态合批**

条件：不同Mesh，只要使用相同的材质球即可。

优点：节省顶点信息地绑定；节省几何信息地传递；相邻材质相同时, ，节省材质地传递。

缺点：离线合并时，若合并的Mesh中存在重复资源，则容易使得合并后包体变大；运行时合并，则生成Combine Mesh的过程会造成CPU短时间峰值；同样的，若合并的Mesh中存在重复资源，则会使得合并后内存占用变大。

**2\. SRP Batcher**

条件：不同Mesh，只要使用相同的Shader且变体一样即可。

优点：节省Uniform Buffer的写入操作；按Shader分Batch，预先生成Uniform Buffer，Batch内部无CPU Write。

缺点：Constant Buffer（CBuffer）的显存固定开销；不支持MaterialPropertyBlock。

**3\. GPU Instancing**

条件：相同的Mesh，且使用相同的材质球。

优点：适用于渲染同种大量怪物的需求，合批的同时能够降低动画模块的耗时。

缺点：可能存在负优化，反而使DrawCall上升；Instancing有时候被打乱，可以自己分组用API渲染。

**3.2.4 粒子系统渲染开销**

一般来说，在渲染模块的堆栈中出现的ParticleSystem.Draw，其调用次数代表了测试过程中粒子系统DrawCall的变化情况。粒子系统DrawCall高，会造成较高的半透明渲染耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image105.1712720445395.png "UWA")

针对粒子系统DrawCall的常见优化手段如下：

1\. 从策略上分级减少粒子在中低端机型上的播放量本身就是一种思路。就像MMO游戏作最大同屏人数上限一样，也可以为粒子系统设置不同机型上的最大播放上限。比如多人游戏中，场景中的粒子用缓存池管理，非玩家主视角的技能产生的粒子系统到达一定数量后就不允许实例化和入池、同种粒子也设置缓存池数量上限，从而控制整体数量；

2\. 使用TextureSheetAnimation来降低粒子系统的DrawCall，从TextureSheetAnimation设置中Mode下拉选单中选择Sprites选项，可以定义要为每个粒子显示的精灵列表，而不是使用纹理上的一组常规帧。使用此模式可以利用精灵的许多功能，例如精灵打包器（Sprite Packer）、自定义轴心和每个精灵帧的不同大小。Sprite Packer可帮助在不同粒子系统之间共享材质，方法是将纹理整理成图集，从而通过动态批处理（Dynamic Batching）提高性能。

3\. 还有一种非常常见的粒子DrawCall过高的原因是穿插，比如某个预制体下有1-5，5个不同的粒子构成一整个特效，场景中有100个这个预制体。默认情况下总计500个粒子渲染顺序是相同的，此时在Frame Debugger中很有可能会发现此时有500个DrawCall，且呈现为123451234512345......但显然，理想状况下只需要5个DrawCall就够了。可以考虑通过控制Render Queue、Sorting Layer、Order in Layer和Sorting Fudge来重新排布它们的渲染顺序，从而增加粒子系统的DrawCall合批，从而降低粒子系统的渲染Batch数量（具体需要结合项目中粒子的具体制作情况）。

**3.2.5 UGUI UI 渲染开销**

通常战斗场景中其他模块耗时压力大，此时UI模块更要仔细控制性能开销。其中，不仅是UI更新的开销，还有渲染层面的开销。一般而言，战斗场景中的UI DrawCall控制到40-50左右为最佳。

在不减少UI元素的前提下，控制DrawCall的问题，其实也就是如何使得UI元素尽量合批的问题。一般的合批要求材质相同，而在UI中却常常会发生明明是使用同一材质、同一图集制作的UI元素却无法合批的现象。这其实和UGUI DrawCall的计算原理有关。详细的原理介绍可以在UWA学堂中学习有关课程 [《详解UGUI DrawCall计算和Rebuild操作优化》](https://edu.uwa4d.com/course-intro/0/126) 。

在UGUI的制作过程中，建议关注以下几点：

1\. 同一Canvas下的UI元素才能合批。不同Canvas即使Order in Layer相同也不合批，所以UI的合理规划和制作非常重要；

2\. 尽量整合并制作图集，从而使得不同UI元素的材质图集一致。图集中的按钮、图标等需要使用图片的比较小的UI元素，完全可以整合并制作图集。当它们密集地同时出现时，就有效降低了DrawCall；

3\. 在同一Canvas下、且材质和图集一致的前提下，避免层级穿插。笼统地说，应使得符合合批条件的UI元素的“层级深度”相同；

4\. 将相关UI的Pos Z尽量统一设置为0。Z值不为0的UI元素只能与Hierarchy中相邻元素尝试合批，所以容易打断合批；

5\. 对于Alpha为0的Image，需要勾选其CanvasRender组件上的Cull Transparent Mesh选项，否则依然会产生DrawCall且容易打断合批。

还有一部分的渲染开销是UI可能对GPU层面Overdraw产生的压力，这里见最后的GPU章节中相关讨论。

**3.2.6 Shader.CreateGPUProgram**

该API常常在渲染模块主函数的堆栈中出现，并造成渲染模块中的大多数函数峰值。它是Shader第一次渲染时产生的耗时，其耗时与渲染Shader的复杂程度相关。当它在游戏过程中被调用并且造成较高的耗时峰值时应引起注意。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image073.1654596938661.png "UWA")

对此，我们可以将Shader通过ShaderVariantCollection收集要用到的变体并进行AssetBundle打包。在将该ShaderVariantCollection资源加载进内存后，通过在游戏前期场景调用ShaderVariantCollection.WarmUp来触发Shader.CreateGPUProgram，并将此SVC进行缓存，从而避免在游戏运行时触发此API的调用、避免局部的CPU高耗时。

然而即便是已经做过以上操作的项目也常会检测到运行时偶尔的该API耗时峰值，说明存在一些“漏网之鱼”。开发者可以结合Profiler的Timeline模式，选中触发调用Shader.CreateGPUProgram的帧来查看具体是哪些Shader触发了该API，可以参考 [《一种Shader变体收集和打包编译优化的思路》](https://blog.uwa4d.com/archives/USparkle_Shadervariant.html) 。

**3.2.7 Culling**

绝大多数情况下，Culling本身耗时并不显眼，它的意义在于反映一些与渲染相关的问题。

**1\. 相机数量多**

当渲染模块主函数的堆栈中Culling耗时的占比比较高（一般项目中在10%-20%左右）。

**2\. 场景中小物件多**

Culling耗时与场景中的GameObject小物件数量的相关性比较大。这种情况建议研发团队优化场景制作方式 ，关注场景中是否存在过多小物件，导致Culling耗时增高。可以考虑采用动态加载、分块显示，或者Culling Group、Culling Distance等方法优化Culling的耗时。

**3\. Occlusion Culling**

如果项目使用了多线程渲染且开启了Occlusion Culling，通常会导致子线程的压力过大而使整体Culling过高。

由于Occlusion Culling需要根据场景中的物体计算遮挡关系，因此开启Occlusion Culling虽然降低了渲染消耗，其本身的性能开销却也是值得注意的，往往不适用于绝大部分移动端游戏场景。这种情况建议开发者选择性地关闭一部分Occlusion Culling去测试一下渲染数据的整体消耗进行对比，再决定是否需要开启这个功能。

**4\. 包围盒更新**

Culling的堆栈中有时出现的FinalizeUpdateRendererBoundingVolumes为包围盒更新耗时。一般常见于Skinned Mesh和粒子系统的包围盒更新上。如果该API出现很频繁，则要通过截图去排查此时是否有较大量的Skinned Mesh更新，或者较为复杂的粒子系统更新。

**5\. PostProcessingLayer.OnPreCull/WaterReflection.OnWillRenderObject**

PostProcessLayer.OnPreCull这一方法和项目中使用的PostProcessing Stack相关。可以在PostProcessManager.cs中添加静态变量GlobalNeedUpdateSettings，在切场景的时候通过设置PostProcessManager.GlobalNeedUpdateSettings为true来UpdateSettings。这样就可以避免每帧都做UpdateSettings操作，从而减少一部分耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image075.1654596938724.png "UWA")

**3.2.8 阴影**

阴影是提升游戏画面层次感与真实感的核心渲染效果，但移动端硬件算力有限，不合理的阴影设置会导致同屏渲染面片数翻倍、GPU带宽占用激增，同时增加CPU、GPU端的计算开销，成为性能瓶颈。因此，移动端项目需围绕“分级策略+精准控制”制定阴影优化方案，在表现与性能间找到平衡。

首先，阴影的性能损耗贯穿CPU与GPU两端，主要集中在三个环节：

1\. CPU端开销。阴影投射物的边界计算（用于生成Shadowmap）、视锥体裁剪、多光源阴影的叠加计算，以及Shadowmap的内存分配与管理；

2\. GPU端开销。Shadowmap的渲染（本质是额外的全屏绘制）、阴影采样（增加纹理带宽占用）、阴影过滤（如PCF软阴影的多采样计算）；

3\. 资源开销。Shadowmap作为Render Texture，其分辨率直接决定内存占用，例如1024\*1024分辨率的Shadowmap，在RGBA32格式下内存占用约4MB，若开启级联阴影（Cascade），内存开销会按级叠加。

基于此，常见问题或关键优化策略如下：

1\. 分级策略

阴影是分级优化的核心场景之一，需根据目标机型的GPU算力、内存大小，制定差异化方案：

低端机型上，考虑直接关闭所有动态阴影或仅保留主角等核心对象的简单阴影，或者使用烘焙、平面阴影等低开销策略。优先保证帧率流畅，牺牲非必要的表现细节；

中端机型上，启用较为基础的阴影设置，限制Shadowmap分辨率，关闭软阴影，仅保留主光源的阴影，且Shadow Distance（阴影绘制距离）控制在20-30米；

高端机型上，仍然需要警惕使用软阴影与级联阴影，即便要用也要严格限制相关设置，并可适当提升Shadowmap、阴影距离等设置的规格。

2\. 控制阴影投射与接收范围

并非所有对象都需要投射或接收阴影，精准筛选能大幅降低开销：

关闭非关键对象的阴影，场景中的小物件（如道具、装饰植物）、远距离对象、半透明物体（如粒子特效），可在Inspector面板中取消Cast Shadows和Receive Shadows；

分层控制阴影交互，通过Project Settings→Graphics→Layer Collision Matrix，配置不同层级对象间的阴影投射规则，减少无效计算；

动态调整阴影距离，结合场景相机的视野范围，在战斗、跑图等不同场景动态修改Shadow Distance。例如，近战场景将阴影距离缩短至15米，大世界跑图时延长至30米，避免远距离对象的阴影浪费性能。

3\. 优化Shadowmap设置

Shadowmap的参数直接决定阴影的性能开销，需重点把控以下几点：

分辨率控制，移动端Shadowmap分辨率建议控制在1024\*1024，最高不超过2048\*2048；

减少阴影级联数，Unity的级联阴影会将视锥体分为多个层级，每个层级生成独立的Shadowmap，级联数越多开销越大。移动端建议级联数≤2，低端机直接使用1级；

关闭不必要的阴影过滤，软阴影（如PCF4x4过滤）的采样计算量是硬阴影的4至8倍，中端以下机型建议使用硬阴影；

限制阴影投射光源数量，单场景中开启阴影的光源数量建议≤1，优先保留主光源的阴影，点光源、聚光灯等辅助光源直接关闭阴影，或用烘焙阴影替代。

4\. 烘焙阴影，这里可以说是又一处用内存换性能的范例

对于静态场景（如地形、建筑、静态装饰），烘焙阴影是移动端的最优选择——将阴影信息预先烘焙到光照贴图中，运行时无需实时计算，大幅降低阴影的CPU/GPU开销，其中还可关注：

静态对象标记。将场景中不移动的对象标记为Contribute GI和Receive GI，确保烘焙时包含阴影信息；

光照贴图优化。降低光照贴图的分辨率，启用压缩格式，减少内存占用；

混合烘焙策略。静态场景用烘焙阴影，动态对象（如角色、怪物）用实时阴影，通过光照探针让动态对象与烘焙阴影自然融合，避免画面割裂。

5\. 技术替代方案

若部分场景必须保留动态阴影，但硬件性能不足，可采用轻量化替代方案，降低开销。

比如平面阴影（Planar Shadows），仅在地面等平面上绘制阴影，通过简单的矩阵计算模拟阴影投射，无需生成Shadowmap，CPU/GPU开销极低，适合风格上偏2.5D的游戏或角色阴影；

又比如投射阴影简化，为动态对象创建低模（LOD 0的1/5面片数），仅用低模投射阴影，不影响视觉效果但减少阴影渲染的面片数；

阴影距离衰减：通过Shader控制阴影的透明度，距离越远阴影越淡，最终在Shadow Distance边界处完全消失，避免远距离阴影的无效渲染。

综上，移动端阴影优化的核心很多时候是“取舍”——通过分级策略放弃低端机的非必要阴影效果，用烘焙阴影等低开销方案替代高开销的实时阴影和精良的阴影效果（结合实际项目需要，可能的方案远不止上文讨论的内容，可参考 [UWA社区](https://community.uwa4d.com/) 中更多文章），在保证画面可接受的前提下，将性能开销降至最低。

---

### 3.3 UI模块

在Unity引擎中，主流的UI框架有UGUI、NGUI以及使用越来越多的FairyGUI。本文主要从使用最多的UGUI来进行说明。围绕UGUI相关优化更全面的内容可以参考 [《Unity性能优化 — UI模块》](https://blog.uwa4d.com/archives/UWA_ReportModule8.html) 。

**3.3.1 UGUI EventSystem.Update**

EventSystem.Update函数为UGUI的事件系统耗时，其耗时偏高时主要关注以下两个因素：

**1\. 触发调用耗时高**

作为UGUI事件系统的主函数，该函数主要是在触摸释放时触发，当本身有较高的CPU开销时，通常都是因为调用了其它较为耗时的函数引起。因此需要通过添加Profiler.BeginSample/EndSample打点或者GOT Online服务+UWA API打点来对所触发的逻辑进行进一步地检测，从而排查出具体是哪一个子函数或者代码段造成的高耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image073.1654652582128.png "UWA")

**2\. 轮询耗时高**

所有UGUI组件在创建时都默认开启了Raycast Target这一选项，实际上是为接受事件响应做好了准备。事实上，大部分比如Image、Text类型的UI组件是不会参与事件响应的，但仍然会在鼠标/手指划过或悬停时参与轮询，所以通过模拟射线检测判断UI组件是否被划过或悬停，造成不必要的耗时。尤其在项目中UI组件比较多时，关闭不参与事件响应的组件的Raycast Target设置，可以有效降低EventSystem.Update()耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image075.1654652606570.png "UWA")

**3.3.2 UGUI Canvas.SendWillRenderCanvases**

Canvas.SendWillRenderCanvases函数的耗时代表的是UI元素自身变化带来的更新耗时，这是需要和Canvas.BuildBatch（见下文）的网格重建的耗时所区分的。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image077.1654652667449.png "UWA")

持续的高耗时往往是由于UI元素过于复杂且更新过于频繁造成。UI元素的自身更新包括：替换图片、文本或颜色发生变化等等。UI元素发生位移、旋转或者缩放并不会引起该函数有开销。该函数的耗时取决于UI元素发生更新的数量以及UI元素的复杂度，因此要优化此函数的开销通常可以从如下几点着手：

**1\. 降低频繁更新的UI元素的频率**

比如小地图的怪物标记、角色或者怪物的血条等，可以控制逻辑在变动超过某个阈值时才更新UI的显示，再比如技能CD效果，伤害飘字等控制隔帧更新。

那么，如何定位哪些UI元素在进行频繁更新？这里推荐在Canvas.SendWillRenderCanvases源码中插桩的方式，就可以在运行时输出再进行更新的UI元素有哪些。可以参考雨松大佬的博客的做法： [《UGUI研究院之找到具体某个引起了网格重建的UI元素（三十二）》](https://www.xuanyusong.com/archives/4573) 。

**2\. 尽量让复杂的UI不要发生变动**

如某些字符串特别多且又使用了Rich Text、Outline或者Shadow效果的Text，Image Type为Tiled的Image等。这些UI元素因为顶点数量非常多，一旦更新便会有较高的耗时。如果某些效果需要使用Outline或者Shadow，但是却又频繁的变动，如飘动的伤害数字，可以考虑将其做成固定的美术字，这样顶点数量就不会翻N倍。

判断UI元素是否复杂，其实就是看它的UI Vertex数量。使用Unity Profiler自带的UI模块，可以看到相应帧中相应Canvas路径下各个UI Batch绘制的UI元素数量和Vertex数量，快速定位到复杂元素。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image123.1712722363982.png "UWA")

**3\. 关注Font.CacheFontForText**

该函数往往会造成一些耗时峰值。该API主要是生成动态字体Font Texture的开销，在运行时突发高耗时，很有可能是一次性写入很多新的字符，导致Font Texture纹理扩容。可以从减少字体种类、减少字体字号、提前显示常用字以扩充动态字体FontTexture等方式去优化这一项的耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image079.1654652911755.png "UWA")

**4\. 使用TMP的情况**

使用TMP的项目在出现如过场剧情、聊天框等存在大量文本的功能时都可能出现Canvas.SendWillRenderCanvases的持续高耗时或卡顿耗时。此时在堆栈中往往会出现TMP.Generate等相关节点。这是因为TMP在高频接受大量新的字符并填入动态字体图集时会产生较高的耗时。经UWA实验发现，在调换为静态字体后，相关UI耗时可能会有近一半的大幅度耗时下降。因此前文在内存中讨论的TMP静态图集方案对于耗时也有一定优化效果。

**5\. 使用UI Particle的情况**

在UWA遇到的多数大面积使用UI Particle的项目中，其性能表现都比较糟糕。这是因为UI Particle是继承于UGUI的MaskableGraphic类写的，因此除了会有本身的粒子更新开销外，还会作为UGUI的元素进行更新，而往往其UI Vertex复杂且更新非常频繁，因此容易造成很高的耗时。因此一般建议尽量少用、简化或改为其他方案来呈现类似的效果。

**3.3.3 UGUI Canvas.BuildBatch**

Canvas.BuildBatch为UI元素合并的Mesh需要改变时所产生的调用。通常之前所提到的Canvas.SendWillRenderCanvases()的调用都会引起Canvas.BuildBatch的调用。另外，Canvas中的UI元素发生移动也会引起Canvas.BuildBatch的调用。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image081.1654652950074.png "UWA")

Canvas.BuildBatch是在主线程发起UI网格合并，具体的合并过程是在子线程中处理的，当子线程压力过大，或者合并的UI网格过于复杂的时候，会在主线程产生等待，等待的耗时会被统计到EmitWorldScreenspaceCameraGeometry中。

这两个函数产生高耗时，说明发生重建的Canvas非常复杂，此时需要将Canvas进行细分处理，通常是将静态的元素放在一个Canvas中，将发生更新的UI元素放入一个Canvas中，这样静态的Canvas由于缓存不会发生网格更新，从而降低网格更新的复杂度，减少网格重建的耗时。

**3.3.4 UGUI CanvasRenderer.SyncTransform**

我们常注意到有些项目的部分帧中CanvasRenderer.SyncTransform调用频繁。如下图，CanvasRenderer.SyncTransform调用次数多达1017次。当Canvas.SyncTransform触发次数非常频繁时，会导致它的父节点UGUI.Rendering.UpdateBatches产生非常高的耗时。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image083.1654653076366.png "UWA")

而该节点调用次数过高时，应考虑以下四种可能，并采取相应的策略控制调用次数、降低开销：

1\. 任何UI元素Transform信息变化（如位移、旋转、拉伸，例如飘字这类UI动画）都会导致自身触发一次CanvasRenderer.SyncTransform，若同时发生Transform信息变化的UI元素多，则显然会导致调用次数高（如多人游戏中频繁移动的其他玩家的HUD、战斗场景中频繁弹跳而得出的伤害数字位移动画等）。此时，可以考虑适当限制降低相关变化的更新频率。

2\. 调用SetActive(True)激活UI元素时，会使当前Canvas下和其父Canvas下所有UI元素都触发CanvasRenderer.SyncTransform，特别地，调用SetActive(False)隐藏UI元素时，不会触发。因此，应考虑将需要频繁激活隐藏的UI元素与其他静态元素进行动静分离。

3\. Instantiate实例化UI元素时，会使当前Canvas下和其父Canvas下所有UI元素都触发CanvasRenderer.SyncTransform。

4\. Destroy销毁UI元素时，会仅使当前Canvas下所有UI元素都触发CanvasRenderer.SyncTransform，综合第3、4点，应考虑将需要频繁实例化和销毁的UI元素与其他静态元素进行动静分离。

PS：以上API未实际生效时（如对一个已经被激活的对象调用SetActive(True)），则不会触发CanvasRenderer.SyncTransform。

**3.3.5 UI界面切换卡顿**

UI界面切换耗时过长也是很多开发者都头疼的问题之一。其实从玩家视角来看UI切换时画面变化幅度大，因此体感上200ms以下的耗时往往并不会造成明显的卡顿感。但尽管如此，实际项目中，如通行证、背包、角色展示界面等较为复杂的UI界面的切换时间超过200ms甚至超过1s的情况并不少见，这就会使得玩家的体验出现明显的打断和不适。

当然，实际上UI界面切换的耗时大多来源于UI元素的实例化和显隐开销，以及一些相应的逻辑耗时。这些本身并不归类到UI模块的函数耗时中，但一些策略就可以很大程度解决这方面的问题。

一种思路是对UI的归类和缓存。一些游戏过程中最常用的UI界面是可以考虑予以缓存的，具体哪些UI值得缓存则需要根据游戏类型或者热点统计数据判断。比如一个养成游戏的角色展示页面、一个Moba游戏的商店页面等等。

还有则是UI的分帧加载。很多项目的通行证页面或者背包页面打开速度很慢，因为其中的图标非常之多。但实际上，可以对其中的UI元素进行重要性梳理后作分帧加载，比如优先加载按钮、重要数值、物品名称等元素，而装饰、图标、分页中的内容都可以放到之后的帧再加载。这样呈现出的效果是，玩家点击时，界面立刻产生了相应，并且重要的交互和信息都可以直接操作，体验将大幅上升。

---

### 3.4 物理模块

围绕物理模块相关优化更全面的内容可以参考 [《Unity性能优化 — 物理模块》](https://blog.uwa4d.com/archives/UWA_ReportModule7.html) 。

**3.4.1 Auto Simulation**

在Unity 2017.4版本之后，物理模拟的设置选项Auto Simulation被开放并且默认开启，即项目过程中总是默认进行着物理模拟。但在一些情况下，这部分的耗时是浪费的。

判断物理模拟耗时是否被浪费的一个标准就是Contacts数量，即游戏运行时碰撞对数量。一般来说，碰撞对的数量越多，则物理系统的CPU耗时越大。但在很多移动端项目中，我们都检测到在整个游戏过程中Contacts数量始终为0。

在这种情况下，开发者可以关闭物理的自动模拟来进行测试。如果关闭Auto Simulation并不会对游戏逻辑产生任何影响，在游戏过程中依然可以进行很好地对话、战斗等，则说明可以节省这方面的耗时。同时也需要说明的是，如果项目需要使用射线检测，那么在关闭Auto Simulation后需要开启Auto Sync Transforms，来保证射线检测可以正常作用。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image085.1654653606099.png "UWA")

**3.4.2 Contacts**

就像上面提到的，若Contacts始终为0，一定程度上说明项目大概率用不到物理模拟，可以考虑关闭。

而如果我们确实用到物理模拟，则一般碰撞对的数量越多，物理系统的CPU耗时也就越大。所以，严格控制碰撞对数量对于降低物理模块耗时非常重要。

在GOT Online Overview的物理模块中，统计了测试过程中Overlap事件的数量，本质上就是Contacts碰撞次数。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image133.1712730276896.png "UWA")

很多项目中可能存在一些不必要的Rigidbody组件，在开发者不知情的地方造成了不必要的碰撞，从而产生了耗时浪费；另外，可以检查修改Project Settings的Physics设置中的Layer Collision Matrix，取消不必要的层之间的碰撞检测，将Contacts数量尽可能降低。

报告中也会有Rigidbody、静态碰撞体数量曲线，以辅助开发者判断物理模块的制作导致的性能问题。

**3.4.3 OnTrigger替换**

还一种需要物理模拟的情况，即需要触发的回调逻辑（如OnTrigger，OnCollision等）。但多数情况下，如用来判断角色和场景坐标、人物的交互等，是可以考虑通过其它方式实现的，如Bounds.Contain、Physics.OverlapSphere等API。它们本质也是计算某一点是否在某包围盒范围内，属于较为简单的几何运算，不需要走物理模拟，因此完全替换后最终也可以考虑关闭物理的自动模拟。以下是将OnTriggerEnter的逻辑改为C#脚本逻辑实现的一种参考方式。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image135.1712730471821.png "UWA")

**3.4.4 Collider碰撞体**

除了碰撞体的数量外，碰撞体的复杂度也会影响物理模块的耗时。默认为模型生成碰撞体，会是接近于模型本体的MeshCollider。但精细度非常高的MeshCollider，即便是在竞技射击类这种对受击判定有着极高要求的项目也可能是完全没有必要的。

多数项目中利用Collider进行相关逻辑判定时，使用复杂MeshCollider并不会有什么实际区别，还会造成非常高的额外开销。

因此一般要尽量少使用MeshCollider，可以用简单Collider代替，即使用多个简单Collider组合代替也要比复杂的MeshCollider来的高效。

MeshCollider是基于三角形面的碰撞，三角形面数越多，运算成本越高；而球体、箱体、胶囊这类简单碰撞体本身形状单一，Unity内部会用更快捷的几何算法进行碰撞运算。

MeshCollider生成的碰撞体网格占用内存也较高；而简单碰撞体重复度高，因而内存中只有几个很小的元碰撞体。

**3.4.5 物理更新次数**

Unity物理模拟过程的主要耗时函数是在FixedUpdate中的，也就是说，当每帧该函数调用次数越高、物理更新次数也就越频繁，每帧的耗时也就相应地高。

物理更新次数，或者说FixedUpdate的每帧调用次数，是和Unity Project Settings的Time设置中最小更新间隔（Fixed Timestep）以及最大允许时间（Maximum Allowed Timestep）相关的。这里我们需要先知道物理系统本身的特性，即当游戏上一帧卡顿时，Unity会在当前帧非常靠前的阶段连续调用N次FixedUpdate.PhysicsFixedUpdate，Maximum Allowed Timestep的意义就在于限制物理更新的次数。它决定了单帧物理最大调用次数，该值越小，单帧物理最大调用次数越少。现在设置这两个值分别为20ms和100ms，那么当某一帧耗时30ms时，物理更新只会执行1次；耗时200ms时也只会执行5次。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image087.1654653721430.png "UWA")

所以一个行之有效的方法是调整这两个参数的设置，尤其是控制更新次数的上限（默认为17次，最好控制到5次以下），物理模块的耗时就不会过高；另一方面则是先优化其它模块的CPU耗时，当项目运行过程中耗时过高的帧很少，则FixedUpdate也不会总是达到每帧更新次数的上限。这对于其它FixedUpdate中的函数是同理的，也是基于这种原因，我们一般不建议在FixedUpdate中写过多游戏逻辑。

---

### 3.5 动画模块

围绕动画模块相关优化更全面的内容可以参考 [《Unity性能优化 — 动画模块》](https://blog.uwa4d.com/archives/UWA_ReportModule6.html) 。

**3.5.1 Mecanim动画系统**

Mechanic动画系统是Unity公司从Unity 4.0之后开始引入的新版动画系统（使用Animator控制动画），相比于Legacy的Animation控制系统，在功能上，Mecanim动画系统主要有以下几点优势：

1\. 针对人形角色提供了一套特殊的工作流，包括Avatar的创建以及Muscles肌肉的调节；

2\. 动画重定向（Retarting）的能力，可以非常方便地把一个动画从一个角色模型应用到其他角色模型上；

3\. 提供了可视化的Animator编辑器，可以快捷预览和创建动画片段；

4\. 更加方便地创建状态机以及状态之间Transition的转换；

5\. 便于操作的混合树功能。

在性能上，对于骨骼动画且曲线较多的动画，使用Animator的性能是要比Animation要好的，因为Animator是支持多线程计算的，而且Animator可以通过开启Optimized GameObjects进行优化，具体细节可以参考UWA学堂的课程 [《Unity移动游戏中动画系统的性能优化》](https://edu.uwa4d.com/course-intro/1/111) 。相反，对于比较简单的类似于移动旋转这样的动画，使用Animation控制则比Animator要高效一些。

**3.5.2 BakeMesh**

对于一两千面这样面数较少且动画时长较短的对象，如MOBA、SLG中的小兵等，可考虑用SkinnedMeshRenderer.BakeMesh的方案，用内存换CPU耗时。其原理是将一个蒙皮动画的某个时间点上的动作，Bake成一个不带蒙皮的Mesh，从而可以通过自定义的采样间隔，将一段动画转成一组Mesh序列帧。而后在播放动画时只需选择最近的采样点（即一个Mesh）进行赋值即可，从而省去了骨骼更新与蒙皮计算的时间（几乎没有动画，只是赋值的动作）。整个操作比较适合于面片数小的人物，因为此举省去了蒙皮计算。其作用在于：用内存换取计算时间，在场景中大量出现同一个带动画的模型时，效果会非常明显。该方法的缺点是内存的占用极大地受到模型顶点数、动画总时长及采样间隔的限制。因此，该方法只适用于顶点数较少，且动画总时长较短的模型。同时，Bake的时间较长，需要在加载场景时完成。

**3.5.3 Active Animator数量**

Active状态的Animator个数会极大地影响动画模块的耗时，而且是一个可量化的重要标准，控制其数量到一个相对合理的值是我们优化动画模块的重要手段。需要开发者结合画面排查对应的数量是否合理。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image091.1654654749271.png "UWA")

**1\. Animator Culling Mode**

控制Active Animator的一个方法是针对每个动画组件调整合理的Animator.CullingMode设置。该项设置一共有三个选项：AlwaysAnimate、CullUpdateTransforms和CullComplete。

默认的AlwaysAnimate使得当前物体不管是不是在视域体内，或者在视域体被LOD Culling掉了，Animator的所有东西都仍然更新；其中，UI动画一定要选AlwaysAnimate，不然会出现异常表现。

而设置为CullUpdateTransforms时，当物体不在视域体内，或者被LOD Culling掉后，逻辑继续更新，就表示状态机是更新的，动画资源中连线的条件等等也都是会更新和判断的；但是Retarget、IK和从C++回传Transform这些显示层的更新就不做了。所以，在不影响表现的前提下把部分动画组件尝试设置成CullUpdateTransforms可以节省物体不可见时动画模块的显示层耗时。

最后，CullComplete就是完全不更新了，适用于场景中相对不重要的动画效果，在低端机上需要保留显示但可以考虑让其静止的物体，分级地选用该设置。

**2\. DOTween插件**

很多时候，UI动画也会贡献大量的Active Animator。针对一些简单的UI动画，如改变颜色、缩放、移动等效果，UWA建议改用DOTween制作。经测试，性能比原生的UI动画要好得多。

**3.5.4 开启Apply Root Motion的Animator数量**

在Animators.Update的堆栈中，有时会看到Animator.ApplyBuiltinRootMotion占比过高，这一项通常和项目中开启了Apply Root Motion的模型动画相关。如果其动画不需要产生位移，则不必开启此选项。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image093.1654655378834.png "UWA")

**3.5.5 Animator.Initialize**

Animator.Initialize API会在含有Animator组件的GameObject被Active和Instantiate时触发，耗时较高。因此尤其是在战斗场景中不建议过于频繁地对含有Animator的GameObject进行Deactive/Active GameObject操作。对于频繁实例化的角色，可尝试通过缓冲池的方式进行处理，在需要隐藏角色时，不直接Deactive角色的GameObject，而是Disable Animator组件，并把GameObject移到屏幕外。

**3.5.6 Meshskinning.Update和Animators.WriteJob**

网格资源对于动画模块耗时的影响是十分显著的。

一方面，Meshskinning.Update耗时较高时。主要因素为蒙皮网格的骨骼数和面片数偏高，所以可以针对网格资源进行减面和LOD分级。

另一方面，默认设置下，我们经常发现很多项目中角色的骨骼节点的Transform一直都是在场景中存在的，这样在Native层计算完它们的Transform后，会回传给C#层，从而产生一定的耗时。

在场景中角色数量较多，骨骼节点的回传会产生一定的开销，体现在动画模块的主函数之一PreLateUpdate.DirectorUpdateAnimationEnd的Animators.WriteJob子函数上。

对此开发者可以考虑勾选FBX资源中Rig页签下的Optimize Game Objects设置项，将骨骼节点“隐藏”，从而减少这部分的耗时。

**3.5.7 GPU Skinning/Compute Skinning**

特别地，对于Unity引擎原生的GPU Skinning设置项（新版Unity中为Compute Skinning），理论上会在一定程度上改变网格和动画的更新方法以优化对骨骼动画的处理，但从针对移动平台的多项测试结果来看，无论是在iOS还是安卓平台上，多个Unity版本提供的GPU Skinning对性能的提升效果都不明显，甚至存在负优化的现象。在Unity的迭代中已对其逐步优化，将相关操作放到渲染线程中进行，但其实用性还需要进一步考察。

对于大量同种怪物的需求，可以考虑使用自己实现的 [《GPU Skinning 加速骨骼动画》](https://blog.uwa4d.com/archives/Sparkle_GPUSkinning.html) ，和UWA开源库中的GPU Instancing来进行渲染，这样既可以降低Animator.Update耗时，又能达到合批的效果。

**3.5.8 Spine**

Spine作为一种动画方案，在移动游戏中使用率也相当高。但它本身的性能表现比较一般，在实际使用过程中可能会造成意想不到的极高开销。

在运行时，Spine的耗时主要体现在SkeletonAnimation.Update和SkeletonAnimation.LateUpdate、或SkeletonGraphic.Update和SkeletonGraphic.LateUpdate这几个函数中。差别是用一般的组件则是前者，用UI上的Spine组件则是后者。Spine作为频繁更新的复杂动画方案，在UI上可能造成额外的更新耗时，因此一般能用一般组件制作的效果尽量不要用UI组件。Spine的耗时高，一般是上述函数单次耗时高的同时调用次数还高导致的，而这两个因素受到本身美术资源制作的复杂度、和运行时同时播放更新的Spine组件数量影响。此外，Spine还可能对渲染压力、堆内存占用等性能问题也有影响。

以下讨论几个常见的Spine性能问题和优化方法：

1\. Spine的美术制作。Spine作为一种动画方案，同样会因为本身Timeline复杂、骨骼节点多而导致在Runtime时更新耗时高。因此，在编辑器阶段，应请美术同学清理用不到的Timeline信息，移除没有用的骨骼、插槽，对每个动作尝试用Spine引擎自带的Clear进行清理，尽量少用Clipping等等。当然，一定要使用二进制方式导出Spine资源，其耗时和堆内存表现要远比Json好的多。

2\. Spine组件数量。也需要监控和控制处于更新状态的Spine数量，关注高压场景的Spine数量是否符合设计预期。一些简单的动画不应用Spine制作，应尽量考虑其他方案。

3\. Update When Invisible设置。SkeletonAnimation组件上存在和Animator的Culling Mode类似的设置Advanced-Update When Invisible。设置为Nothing后，视域体外的Spine动画都停止更新，耗时将得到大幅降低。SkeletonGraphic组件上也有该设置，但需要配合父结点上的RectMask2D才能生效。

4\. Freezing设置。SkeletonGraphic组件上还有Freeze属性，勾选后相关更新会直接Return，不造成任何开销的同时Spine动画也静止了。这个属性适用于某些Spine动画需要条件才触发，其他时候是静止的。则可以在代码中设计为平时是Freeze的，条件出发后才更新，能够节省平时的耗时。该设置在SkeletonAnimation中没有，但完全可以自己调整Spine的Runtime源码实现类似效果。

5\. Spine通过SRP Batcher合批。只要在官网下载替换支持SRP Batcher的Shader，Spine在URP项目中也能通过SRP Batcher合批，降低渲染开销。具体可参考： [https://answer.uwa4d.com/question/6100d3094f8c177460171597](https://answer.uwa4d.com/question/6100d3094f8c177460171597) 。

6\. Overdraw。Spine一般作为一种半透明渲染物体，当制作较为复杂时，也可能使得叠层过多，对GPU渲染也造成压力，同样需要在美术层面就予以关注。

7\. 通过按需加载降低Spine堆内存占用。一些游戏中，随着不断迭代，部分角色的Spine资源可能包含了大量的皮肤、动作等信息，若这些信息进入游戏则一次性全部加载，则会对堆内存产生严重负担，相关的加载耗时也会很高。做拆分确实可以一定程度上解决该问题，但是需要重新导出资源、调整相关代码，且增加了管理维护这些资源的成本。其实也可以考虑一种按需加载的方式，即游戏过程中需要哪些信息则自动加载相应部分进内存，具体做法可参考： [《Spine动画加载优化思路》](https://edu.uwa4d.com/course-intro/0/440) 。

---

### 3.6 粒子系统

围绕粒子系统相关优化更全面的内容可以参考 [《粒子系统优化——如何优化你的技能特效》](https://blog.uwa4d.com/archives/UWA_ReportModule3.html) 。

**3.6.1 Playing粒子系统数量**

UWA统计了粒子系统数量和Playing状态的粒子系统数量。前者是指内存中所有的ParticleSystem的总数量，包含正在播放的和处于缓存池中的；后者指的是正在播放的ParticleSystem组件的数量，这个包含了屏幕内和屏幕外的，我们建议在一帧中出现的数量峰值不超过50（1GB机型）。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image099.1654682189285.png "UWA")

针对这两个数值，我们一方面关注粒子系统数量峰值是否偏高，可选中某一峰值帧查看到底是哪些粒子系统缓存着、是否都合理、是否有过度缓存的现象；另一方面关注Playing数量峰值是否偏高，可选中某一峰值帧查看到底是哪些粒子系统在播放、是否都合理。

前文提到的控制同种粒子数量上限也是常见方案。

分级策略也是粒子系统优化过程中必不可少的手段。比如对于一个有12345，五种子粒子的火焰特效Prefab，其中345可能是美术同学用来做火焰燃烧时飞溅的火星、飘散的烟尘、空气的波动的，只有12是火焰本体。则低端机上应该考虑只保留12。

虽然我们在讨论粒子系统对耗时的影响时，多数时候还是在讨论粒子系统的渲染开销，无论是CPU端还是GPU端的。但对于粒子系统使用非常重度、数量非常多的项目来说，Playing的粒子过多也会对其本身在CPU端进行更新计算的ParticleSystem.Update()耗时有所影响。

**3.6.2 Culling Mode**

为粒子系统设置合理的Culling Mode也是一种有效降低粒子系统CPU端更新耗时的方式。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image151.1773909136768.png "UWA")

相关的关键设置为如上图的Simulation Space和Culling Mode。

其中，Simulation Space可选项有Local，World，Custom；CullingMode可选项为Automatic，Pause And Catch-up，Pause，Always Simulate。通常创建的粒子系统的默认选项是Local和Automatic。

我们显然希望当粒子在屏幕外看不到时停止相关运算、减少其耗时开销。因此我们测试在不同设置组合下粒子系统在屏幕外时的ParticleSystem.Update()函数耗时，结果如下：

1\. 在Local模式下，只有Culling Mode为Always Simulate有例子更新耗时（没有开启额外的Module）。

2\. 在Local模式下，如果粒子系统开启了Collision等Module，那么Culling Mode为Automatic时也会产生耗时。

3\. 在Local模式下，如果是Culling Mode为Pause或者Pause and Catch-up，就算有Collision Module也没有耗时。

4\. 在World模式下，Culling Mode为Automatic也会有耗时（没有开启额外的Module）。

5\. 在World模式下，Culling Mode为Pause，就算有Collision，也没有耗时。

综上，我们可以看到Culling Mode的设置对不同设置的粒子系统开销的限制能力是合理递进的，这说明我们在设置粒子系统时应尽量至少设为Automatic；应慎用Simulation Space为World的粒子；应慎用Collision、Trigger、Noise、Trails这些颇为常见的Module；对于确实要使用Module的粒子，也应考虑进一步调整设置为Pause等以节省耗时。

**3.6.3 Prewarm**

ParticleSystem.Prewarm作为粒子系统的核心初始化选项，其设计初衷是为了让粒子系统在实例化或从Deactive状态激活时，立即完成一次完整的生命周期模拟，使粒子效果从激活瞬间就呈现出“已运行一段时间”的成熟状态（例如持续燃烧的火焰、循环播放的光晕等），避免出现“从无到有”的突兀感。但该机制在带来表现优势的同时，也隐藏着显著的性能风险——尤其在粒子系统数量较多、效果复杂的场景中，Prewarm触发的瞬时计算开销可能成为CPU耗时峰值的主要诱因，甚至引发卡顿。

主要优化手段如下：

1\. 优化粒子系统本身的复杂度，通过降低Prewarm触发时的计算量，从源头减少耗时：

2\. 规避集中触发Prewarm的场景，当多个带Prewarm的粒子系统需要激活时，通过分帧激活、延迟激活、或缓存复用的方式分散计算压力。

---

### 3.7 加载模块

围绕加载模块相关优化更全面的内容可以参考 [《Unity性能优化系列—加载与资源管理》](https://blog.uwa4d.com/archives/UWA_ReportModule2.html) 。

**3.7.1 Shader加载**

**1\. Shader.Parse**

Shader.Parse是指Shader加载进行解析的操作，如果此操作较为频繁，通常是由于Shader的重复加载导致的，这里的重复可以理解为2层意思。

第一层是由于Shader的冗余导致的，通常是因为打包AssetBundle的时候，Shader被被动打进了多个不同的AssetBundle中而没有进行依赖打包，这样当这些AssetBundle中的资源进行加载的时候，会被动加载这些Shader，就进行了多次“重复的”Shader.Parse，所以同一种Shader就在内存中有多份了，这就是冗余了。

要去除这种冗余的方法也很简单，就是把这些会冗余的Shader依赖打包进一个公共的AssetBundle包。这样就会主动打包了，而不是被动进入某些使用了这个Shader的包体中。如果对这个Shader进行了主动打包，那么其它使用了这个Shader的AssetBundle中就只会对这个Shader打出来的公共AssetBundle进行引用，这样在内存中就只有一份Shader，其它用到这个Shader的时候就直接引用它，而不需要多次进行Shader.Parse了。

第二层意思是同一个Shader多次地加载卸载，没有缓存住导致的。假设AssetBundle进行了主动打包，生成了公共的AssetBundle，这样在内存中只有这一份Shader，但是因为这个Shader加载完后（也就是Shader.Parse）没有进行缓存，用完马上被卸载了。下次再用到这个Shader的时候，内存里没有这个Shader了，那就必须再重新加载进来，这样同样的一个Shader加载解析了多次，就造成了多次的Shader.Parse。一般而言，经过变体优化以后的开发者自己写的Shader内存占用都不高，可以统一在游戏开始时加载并缓存。

特别地，对于Unity内置的Shader，只要是变体数量不多的，可以放进Project Settings中的Always Included中去，从而避免这一类Shader的冗余和重复解析。

**2\. Shader.CreateGPUProgram**

该API也会在加载模块主函数甚至UI模块、逻辑代码的堆栈中出现。相关的讨论上文已经涉及，优化方法相同，不再赘述。

**3.7.2 Resources.UnloadUnusedAssets**

该API会在场景切换时被Unity自动调用，一般单次调用耗时较高，通常情况下不建议手动调用。

但在部分不进行场景切换或用Additive加载场景的项目中，不会调用该API，从而使得项目整体资源数量和内存有上升趋势。对于这种情况则可以考虑每5-10min手动调用一次。

Resources.UnloadUnusedAssets的底层运作机理是，对于每个资源，遍历所有Hierarchy Tree中的GameObject结点，以及堆内存中的对象，检测该资源是否被某个GameObject或对象（组件）所使用，如果全部都没有使用，则引擎才会认定其为Unused资源，进而进行卸载操作。简单来讲，Resources.UnloadUnusedAssets的单次耗时大致随着（（GameObject数量+Mono对象数量）\*Asset数量）的乘积变大而变大。

因此，该过程极为耗时，并且场景中GameObject/Asset数量越高，堆内存中的对象数越高，其开销也就越大。对此，我们的建议如下：

**1\. Resources.UnloadAsset/AssetBundle.Unload(True)**

研发团队可尝试在游戏运行时，通过Resources.UnloadAsset/AssetBundle.Unload(True)来去除已经确定不再使用的某一资源，这两个API的效率很高，同时也可以降低Resources.UnloadUnusedAssets统一处理时的压力，进而减少切换场景时该API的耗时。

**2\. 严格控制场景中材质资源和粒子系统的使用数量**

专门提到这两种资源，因为在大多数项目中，虽然它们的内存占用一般不是大头，但往往资源数量远高于其他类型的资源，很容易达到数千的数量级，从而对单次Resources.UnloadUnusedAssets耗时有较大贡献。

**3\. 降低驻留的堆内存**

堆内存中的对象数量同样会显著影响Resources.UnloadUnusedAssets的耗时，这在上文也已经讨论过。

**3.7.3 加载AssetBundle**

使用AssetBundle加载资源是目前移动端项目中比较普遍的做法。

而其中，应尽量用LZ4压缩格式打包AssetBundle，并用LoadFromFile的方式加载。经测试，这种组合下即便是较大的AssetBundle包（包含10张1024\*1024的纹理），其加载耗时也仅零点几毫秒。而使用其他加载方式，如LoadFromMemory，加载耗时则上升到了数十毫秒；而使用WebRequest加载则会造成AssetBundle包的驻留内存显著上升。

这是因为，LoadFromFile是一种高效的API，用于从本地存储（如硬盘或SD卡）加载未压缩或LZ4压缩格式的AssetBundle。

在桌面独立平台、控制台和移动平台上，API将只加载AssetBundle的头部，并将剩余的数据留在磁盘上。AssetBundle的Objects会按需加载，比如：加载方法（例如：AssetBundle.Load）被调用或其InstanceID被间接引用的时候。在这种情况下，不会消耗过多的内存。

但在Editor环境下，API还是会把整个AssetBundle加载到内存中，就像读取磁盘上的字节和使用AssetBundle.LoadFromMemoryAsync一样。如果在Editor中对项目进行了分析，此API可能会导致在AssetBundle加载期间出现内存尖峰。但这不应影响设备上的性能，在做优化之前，这些尖峰应该在设备上重新再测试一遍。

要注意，这个API只针对未压缩或LZ4压缩格式，因为如果使用LZMA压缩，它是针对整个生成后的数据包进行压缩的，所以在未解压之前是无法拿到AssetBundle的头信息的。

由于LoadFromMemory的加载效率相较其他的接口而言，耗时明显增大，因此我们不建议大规模使用，而且堆内存会变大。如果确实有对AssetBundle文件加密的需求，可以考虑仅对重要的配置文件、代码等进行加密，对纹理、网格等资源文件则无需进行加密。因为目前市面上已经存在一些工具可以从更底层的方式来获取和导出渲染相关的资源，如纹理、网格等，因此，对于这部分的资源加密并不是十分的必要性。

在UWA GOT Online Resource模式下的资源管理页面中可以排查加载耗时较高的AssetBundle，从而排查和优化加载方式、压缩格式、包体过大等问题，或者对反复加载的AssetBundle考虑予以缓存。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image097.1654656957261.png "UWA")

**3.7.4 加载资源**

有关加载资源所造成的耗时，若加载策略比较合理，则一般发生在游戏一开始和场景切换时，往往不会造成严重的性能瓶颈。但不排除一些情况需要予以关注，那么可以把资源加载耗时的排序作为依据进行排查。

对于单次加载耗时过高的资源，比如达到数百毫秒甚至几秒时，就应考察这类资源是否过于复杂，从制作上考虑予以精简。

对于反复频繁加载且耗时不低的资源，则应该在第一次加载后予以缓存，避免重复加载造成的开销。

值得一提的是，在Unity的异步加载中有时会出现每帧进行加载所能占用的最高耗时被限制，但主线程中却在空转的现象。尤其是在切场景的时候集中进行异步加载，有时会耗费几十甚至数十秒的时间，但其中大部分时间是被空转浪费的。这是因为控制异步加载每帧最高耗时的API Application.backgroundLoadingPriority默认值为BelowNormal，每帧最多只加载4ms。此时一般建议把该值调为High，即最多50ms每帧。

在UWA GOT Online Resource模式下的资源管理页面中可以排查加载耗时较高的资源，从而排查和优化加载方式、资源过于复杂等问题，或者对反复加载的资源考虑予以缓存。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image099.1654657136618.png "UWA")

**3.7.5 实例化和销毁**

实例化同样主要存在单个资源实例化耗时过高或某个资源反复频繁实例化的现象。根据耗时多少排列后，针对疑似有问题的资源，前者考虑简化，或者可以考虑分帧操作，比如对于一个较为复杂的UI Prefab，可以考虑改为先实例化显眼的、重要的界面和按钮，而翻页后的内容、装饰图标等再进行实例化；后者则建立缓存池，使用显隐操作来代替频繁的实例化。

在UWA GOT Online Resource模式下的资源管理页面中可以排查实例化耗时较高的资源，从而排查和优化资源过于复杂的问题，或者对反复实例化的资源考虑予以缓存。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image101.1654657244846.png "UWA")

**3.7.6 激活和隐藏**

激活和隐藏的耗时本身不高，但如果单帧的操作次数过多就需要予以关注。可能出于游戏逻辑中的一些判断和条件不够合理，很多项目中往往会出现某一种资源的显隐操作次数过多，且其中SetActive(True)远比SetActive(False)次数多得多、或者反之的现象，亦即存在大量不必要的SetActive调用。由于SetActive API会产生C#和Native的跨层调用，所以一旦数量一多，其耗时仍然是很可观的。针对这种情况，除了应该检查逻辑上是否可以优化外，还可以考虑在逻辑中建立状态缓存，在调用该API之前先判断资源当前的激活状态。相当于使用逻辑的开销代替该API的开销，相对耗时更低一些。

在UWA GOT Online Resource模式下的资源管理页面中可以排查激活隐藏操作较频繁的资源，从而排查和优化相关逻辑和调用。

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image103.1654657356084.png "UWA")

---

### 3.8 逻辑代码

逻辑代码的CPU耗时优化更多是结合项目实际需求、考验程序员本人的过程，很难定量定性进行讨论。不过UWA SDK中提供了方便开发者在逻辑代码中进行打点的 [API&UWA GOT Online](https://blog.uwa4d.com/archives/UWAGOT0L_API.html) ，从而将复杂的函数拆解开，在报告中排查堆栈耗时、更快速地验证优化效果。

我们发现有越来越的团队在使用JobSystem将主线程中的部分逻辑代码放入子线程中来进行处理，对于可以并行运算的逻辑，非常推荐将其放入到子线程中来处理，这样可以有效降低主线程CPU处理逻辑运算的压力。

---

### 3.9 Lua

GOT Online Lua模式提供的分析Lua造成的CPU耗时工具可视化程度高，堆栈清晰明了，还提供了实用且特色的倒序调用分析功能。以下结合一个Lua报告Demo简单介绍使用该工具分析Lua耗时的方法。

重申：Lua报告中出现的函数名称格式为：函数名称@文件名：行号。

可以通过报告提供的Lua文件名/行号/函数名来定位CPU耗时的瓶颈函数和CPU耗时峰值的具体原因。Lua函数的命名格式为X@Y:Z，其中X是其函数名，在无法获取时，X会变为默认的unknown；Y是该函数定义的文件位置；Z则是该函数被定义的行号。需要注意的是，当Lua脚本以字节码运行时，该值将始终为0，因此建议在测试时尽可能使用Lua源码来运行。

**1\. 正序调用分析——总表（曲线图+列表）**

曲线图：

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image105.1654657548316.png "UWA")

曲线选取了选取总体Lua代码耗时和按照耗时均值正向排序的前五个函数耗时组成耗时曲线图，每一个数据点代表了该函数在当前帧（横坐标）的耗时（纵坐标），有助于定位耗时瓶颈函数。

列表：

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image107.1654657609938.png "UWA")

列表默认按照耗时均值从高到低对Lua函数进行了排序，粗略展示了函数名、总CPU耗时、场景CPU耗时、耗时均值等数据。通过点击函数，可以进入对应的单个函数分析页面。

**2\. 正序调用分析——单个函数页（截图+曲线图+堆栈信息）**

截图：

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image109.1654657673613.png "UWA")

项目运行时截图与使用者选中的帧大致对应，有助于定位问题。

曲线图：

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image111.1654657699776.png "UWA")

曲线图包括了CPU耗时曲线图和调用次数曲线图；也可以使用下方条缩放曲线观察局部耗时情况。

从曲线图中可以观察到：函数是否存在持续性高耗时；函数是否存在短暂的大量耗时，导致卡顿；某些函数单次耗时并不高，但因为被大量的调用，导致函数总耗时较高。

函数XXXX堆栈信息 （列表）：

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image113.1654657750693.png "UWA")

其中，可以在右上角选定列表数据的时间范围：总体堆栈信息时，时间范围为全部测试时间；指定场景堆栈信息时，时间范围为指定场景的开启时间；指定帧堆栈信息时，时间范围为当前在曲线图中选中的指定帧。

列表中各项指标含义是：总体占比，以根节点函数的总耗时为100%，当前节点函数总耗时相对根节点函数的总耗时占比；自身占比，以根节点函数的总耗时为100%，当前节点函数自身耗时相对根节点函数的总耗时占比；总耗时，时间范围内执行该函数的耗时；自身耗时，时间范围内去除子节点函数（该函数调用的函数）耗时剩余的耗时；调用次数，时间范围内该函数被调用的次数；单次耗时，总耗时/调用次数，表示每次执行该函数的平均耗时；显著调用帧数，该函数自身耗时大于3ms的帧数。

**3\. 倒序调用分析——总表（曲线图+列表）**

曲线图：与正序调用分析不同的是，选取了自身耗时正向排序的前五个函数，每一个数据点代表了该函数在当前帧（横坐标）的自身耗时（纵坐标）。

列表：与上同理。

**4\. 倒序调用分析——单个函数页（截图+曲线图+堆栈信息）**

![loading](https://uwa-edu.oss-cn-beijing.aliyuncs.com/image115.1654657896460.png "UWA")

函数XXXX堆栈信息 （列表）：

各项指标含义（与正序相比有所不同）变为了：自身占比，以选定函数的自身耗时总和为100%，这条调用路径下选定函数的自身耗时相对选定节点函数总自身耗时的占比；自身耗时，时间范围内，这条调用路径下，选定函数自身耗时的总和；调用次数，这条调用路径的调用次数；单次耗时，代表这条路调用路径下，选定函数的平均耗时。

在通过以上界面定位到自身耗时较高的函数后，常见的优化手段有：优化该函数的函数体，减少该函数自身的耗时；定位调用次数较多的调用路径，减少调用次数。

**5\. 优化建议**

（1）优化单次调用耗时过高的函数的函数体，减少该函数自身的耗时；

（2）定位调用次数较多的调用路径，减少调用次数；

（3）在高调用次数的函数中，尤其关注其中是否同时存在大量Lua和C#之间的穿梭调用，效率较低的同时可能对CPU端的能耗和发热产生大幅度贡献；

（4）UWA报告中的Lua函数耗时相当于在进出函数时打点，统计耗时。所以如果Lua脚本运行时调用了C#函数，这部分C#函数是会被统计进去的。

因此，需要关注和C#穿插调用的情况。对于一些反复调用同一个C#函数，或者调用多个C#函数但流程比较固定的情况，应考虑将相关逻辑移入C#层，把需要改动的参数开放。即可能需要多传几个参数，但跨语言穿梭调用的次数能够大幅降低，从而节省开销。

---

### 3.10 ILRuntime

ILRuntime的使用率相对低一些，但有些团队延续着之前项目的开发习惯，仍在移动端项目中大规模使用ILRuntime。但根据UWA经验，使用ILRuntime的项目无论是逻辑耗时还是堆内存相关的性能表现都较为糟糕，因此建议尽量不用或少用。在热更方案的选择上，更多项目团队都在使用的Lua，或最近使用率飙升的HybridCLR（huatuo），仅从性能层面来看也都是更好的替代方案。

以下针对已经遇到ILRuntime导致的性能问题，但短时间内无法调换方案的情况，提出一些相对有效的优化手段。

CPU层面：

1\. 尤其是战斗部分的逻辑尽量少用，考虑写成固定的C#代码。在ILRuntime代码中如果有大量的密集型的计算或者循环，会导致性能急速的下降。所以在ILRuntime的使用上，可以用来做一些UI的更新，在核心战斗逻辑中避免使用，需要控制力度；

2\. 打DLL的时候选择Release的方式；

3\. 对于Android平台，可以选择使用Mono的模式打包，然后使用反射的方式进行加载，这样可以做到和原生C#效率相当。

堆内存层面：

1\. 尽量少用，尤其是核心战斗模块，因为其对于数值类型的变量也存在装箱的问题；

2\. 关闭Debug的宏，可以降低堆内存的分配，在PlayerSettings中定义DISABLE\_ILRUNTIME\_DEBUG宏。

官方文档提供的一些优化建议可以作为进一步节省ILRuntime开销的思路： [https://ourpalm.github.io/ILRuntime/public/v1/guide/FastQA.html](https://ourpalm.github.io/ILRuntime/public/v1/guide/FastQA.html)

2｜分门别类地控制运行时内存

4｜达到GPU压力与画面表现间的平衡

源代码及PDF课件地址：

暂无课件

共1条评论发表评论

![](https://uwa-hdimg.oss-cn-beijing.aliyuncs.com/user_head_default.png)

色星星2024-10-13 09:53:59

有一个问题没有理解，SSAO为什么会使得渲染面数增加一倍呀？

![](https://public1.uwa4d.com/uwa-edu/app-qrcode/WebEdu3Channel.png)