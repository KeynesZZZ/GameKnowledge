---
title: "Unity性能优化 — UI模块 - UWA问答 | 博客 | 游戏及VR应用性能优化记录分享 | 侑虎科技"
source: "https://blog.uwa4d.com/archives/UWA_ReportModule8.html"
author:
published:
created: 2026-06-28
description: "我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为&..."
tags:
  - "clippings"
---
## Unity性能优化 — UI模块

我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为"升级版"的性能优化手册， **【Unity性能优化系列】** 将力图以浅显易懂的表达，让更多开发者可以受用。本期我们来继续分享UI模块相关的知识点。

在Unity引擎中，主流的UI框架有UGUI，NGUI以及使用越来越多的FairyGUI。本篇文章主要从使用最多的UGUI来进行说明。本文从CPU耗时部分和对内存分配的影响，以及对GPU的影响来讨论UI的优化。

### 一、CPU耗时

下图是使用GOT Online测试的某一项目中的UGUI的耗时分布堆栈，也是较为典型的案例。Unity 2019版本之前，Canvas.SendWillRenderCanvases中所有的耗时都统计到Layout中。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/1.png)

在Unity 2019版本中会稍有不同，耗时分为了Layout和Render两部分，如下图所示。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/2.png)

接下来我们要讨论的是这些堆栈中的Canvas.SendWillRendererCanvses，Canvas.BuildBatch以及SyncTransform。

**1.Canvas.SendWillRenderCanvases**  
该函数的耗时代表的是UI元素自身的变化带来的更新耗时，可以理解为UI更新的耗时，这是需要和Canvas.BuildBatch（见下文）的网格重建的耗时所区分的。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/3.png)

UI元素的自身更新包括：替换图片，文本或颜色发生变化等等。UI元素发生位移、旋转或者缩放并不会引起该函数有开销。该函数的耗时取决于UI元素发生更新的数量以及UI元素的复杂度，因此要优化此函数的开销通常可以从如下几点着手：

**1）降低频繁更新的UI元素的频率**  
比如小地图的怪物标记、角色或者怪物的血条等，可以控制逻辑在变动超过某个阈值时才更新UI的显示，再比如技能CD效果，伤害飘字等控制隔帧更新。

**2）尽量让复杂的UI不要发生变动**  
如某些字符串特别多且又使用了Rich Text、Outline或者Shadow效果的Text，Image Type为Tiled的Image等。这些UI元素因为顶点数量非常多，一旦更新便会有较高的耗时。如果某些效果需要使用Outline或者Shadowmap，但是却又频繁的变动，如飘动的伤害数字，可以考虑将其做成固定的美术字，这样顶点数量就不会翻N倍。

**3）关注Font.CacheFontForText**  
该函数往往会造成一些耗时峰值。该API主要是生成动态字体Font Texture的开销，在运行时突发的高耗时，很有可能是一次性写入很多新的字符，导致Font Texture纹理扩容。可以从减少字体种类、减少字体字号、提前显示常用字以扩充动态字体FontTexture等方式去优化这一项的耗时。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/4.png)

**2.BuildBatch & EmitWorldScreenspaceCameraGeometry**  
Canvas.BuildBatch为UI元素合并的Mesh需要改变时所产生的调用。通常之前所提到的Canvas.SendWillRenderCanvases()的调用都会引起Canvas.BuildBatch的调用。另外，Canvas中的UI元素发生移动也会引起Canvas.BuildBatch的调用。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/5.png)

Canvas.BuildBatch是在主线程发起UI网格合并，具体的合并过程是在子线程中处理的，当子线程压力过大，或者合并的UI网格过于复杂的时候，会在主线程产生等待，等待的耗时会被统计到EmitWorldScreenspaceCameraGeometry中。

这两个函数产生高耗时，说明发生重建的Canvas非常复杂，此时需要将Canvas进行细分处理，通常是将静态的元素放在一个Canvas中，将发生更新的UI元素放入一个Canvas中，这样静态的Canvas由于缓存不会发生网格更新，从而降低网格更新的复杂度，减少网格重建的耗时。

**3.SyncTransform**  
注意到有些项目的部分帧中CanvasRenderer.SyncTransform调用频繁。如图例中，CanvasRenderer.SyncTransform调用次数多达1017次。当Canvas.SyncTransform触发次数非常频繁时，会导致它的父节点UGUI.Rendering.UpdateBathes产生非常高的耗时。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/6.png)

而该节点调用次数过高时，应考虑以下四种可能，并采取相应的策略控制调用次数、降低开销：

1. 任何UI元素Transform信息变化（如位移、旋转、拉伸，例如飘字这类UI动画）都会导致自身触发一次CanvasRenderer.SyncTransform，若同时发生Transform信息变化的UI元素多，则显然会导致调用次数高（如多人游戏中频繁移动的其他玩家的HUD、战斗场景中频繁弹跳而得出的伤害数字位移动画等）。此时，可以考虑适当限制降低相关变化的更新频率。
2. 调用SetActive(True)激活UI元素时，会使当前Canvas下和其父Canvas下所有UI元素都触发CanvasRenderer.SyncTransform，特别地，调用SetActive(False)隐藏UI元素时，不会触发。因此，应考虑将需要频繁激活隐藏的UI元素与其他静态元素进行动静分离。
3. Instantiate实例化UI元素时，会使当前Canvas下和其父Canvas下所有UI元素都触发CanvasRenderer.SyncTransform。
4. Destroy销毁UI元素时，会仅使当前Canvas下所有UI元素都触发CanvasRenderer.SyncTransform，综合第3、4点，应考虑将需要频繁实例化和销毁的UI元素与其他静态元素进行动静分离。

PS：以上API未实际生效时（如对一个已经被激活的对象调用SetActive(True)），则不会触发CanvasRenderer.SyncTransform。

**4.EventSystem.Update**  
1）触发调用耗时高  
该函数为触摸释放时触发，该函数本身有较高的CPU开销时，通常都是因为调用了其他的较为耗时的函数引起。因此需要通过添加 Profiler.BeginSample/EndSample 打点或者GOT Online服务+UWA API打点来对所触发的逻辑来进行进一步的检测。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/7.png)

  

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/8.png)

2）轮询耗时高  
所有UGUI组件在创建时都默认开启了Raycast Target这一选项，实际上是为接受事件响应做好了准备。而事实上，大部分比如Image、Text类型的UI组件是不会参与事件响应的，但仍然会在鼠标/手指划过或悬停时参与轮询，通过模拟射线检测判断UI组件是否被划过或悬停，造成不必要的耗时。尤其在项目中UI组件比较多时，关闭不参与事件响应的组件的Raycast Target设置，可以有效降低EventSystem.Update()耗时。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/9.png)

**5.UI DrawCall**  
通常战斗场景中其他模块耗时压力大，此时UI模块更要仔细控制性能开销。一般而言，战斗场景中的UI DrawCall控制到40-50左右为最佳。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/10.png)

在不减少UI元素的前提下，控制DrawCall的问题，其实也就是如何使得UI元素尽量合批的问题。一般的合批要求材质相同，而在UI中却常常会发生明明是使用同一材质、同一图集制作的UI元素却无法合批的现象。这其实和UGUI DrawCall的计算原理有关。详细的原理介绍欢迎在 **UWA学堂中学习有关课程** 。

[《详解UGUI DrawCall计算和Rebuild操作优化》](https://edu.uwa4d.com/course-intro/0/126)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/11.png)

在制作过程中，建议关注以下几点：  
（1）同一Canvas下的UI元素才能合批。不同Canvas即使Order in Layer相同也不合批，所以UI的合理规划和制作非常重要；  
（2）尽量整合并制作图集，从而使得不同UI元素的材质图集一致。图集中的按钮、图标等需要使用图片的比较小的UI元素，完全可以整合并制作图集。当它们密集地同时出现时，就有效降低了DrawCall；  
（3）在同一Canvas下、且材质和图集一致的前提下，避免层级穿插。笼统地说，应使得符合合批条件的UI元素的“层级深度”相同；  
（4）将相关UI的Pos Z尽量统一设置为0。Z值不为0的UI元素只能与Hierarchy中相邻元素尝试合批，所以容易打断合批。  
（5）对于Alpha为0的Image，需要勾选其CanvasRender组件上的Cull Transparent Mesh选项，否则依然会产生DrawCall且容易打断合批。

### 二、内存

1）通常UGUI本身分配的堆内存是非常少的，所以我们需要关注第三方插件或者自己写的UI组件，比如比较流行的UIParticles，该插件是让UI和特效非常方便地进行层级管理，但是该插件是以ParticleSystem的MaxParticles数量进行数组初始化，因此要特别注意ParticleSystem的MaxParticles数量。

从下图中可以看到，开发者自己写的MeshImage这个UI组件产生了非常多的堆内存，需要对其进行针对性的优化。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/12.png)

2）合并图集，尽量使同一个图集最多不要超过2个Atlas，否则这个图集中的任何Sprite子图被加载进内存中会导致此图集的所有的Atlas被加载进内存。

3）UGUI的GC优化  
这里可以参考UWA学堂 [《Unity的GC优化原理与实践》](https://edu.uwa4d.com/course-intro/0/165) 课程中的这一点：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/13.png)

UGUI的GC优化其他文章说的比较详细了，这里说一个比较容易忽视的一点，就是当Prefab中有大量空的Text，初始化的时候就会有很严重的GC Alloc。这是因为在初始化时，会先初始化TextGenerator，如果Text为空，则会先按50个字来初始化，即50个字的UI Vertex和50个字的UICharInfo，这种可以不让它为空，或者填一个空格进去来组织。

### 三、GPU

1）当某个全屏UI打开时，建议将被背景遮挡住的其他UI进行关闭。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/14.png)

2）对于Alpha为0的UI，建议将其Canvas Renderer组件上的CullTransparent Mesh进行勾选，这样既能保证UI事件的响应，又不需要对其进行渲染。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule8/15.png)

3）尽可能减少Mask组件的使用，不仅提高绘制的开销，同时会造成DrawCall上升。在Overdraw较高的情况下，可以考虑使用RectMask2D代替。

4）在URP下需要额外关心是否有没必要的Copy Color或者Copy Depth存在。尤其是在UI和战斗场景中的相机使用同一个RendererPipelineAsset的情况下，容易出现不必要的渲染耗时和带宽浪费，这样会对GPU造成不必要的开销。通常建议UI相机和场景相机使用不同的RendererData。

以上就是优化UI模块性能时需要注意的一些问题和相对应的解决方法，需要大家根据自己项目的实际情况进行操作，同时还可以结合UWA性能优化服务譬如真人真机测评或GOT Online，快速定位性能瓶颈，为项目保驾护航。

【Unity性能优化系列】

[《Unity性能优化系列—渲染模块》](https://blog.uwa4d.com/archives/UWA_ReportModule1.html)  
[《Unity性能优化系列—加载与资源管理》](https://blog.uwa4d.com/archives/UWA_ReportModule2.html)  
[《粒子系统优化——如何优化你的技能特效》](https://blog.uwa4d.com/archives/UWA_ReportModule3.html)  
[《Unity性能优化系列—Lua代码优化》](https://blog.uwa4d.com/archives/UWA_ReportModule4.html)  
[《Unity性能优化系列 — 资源内存泄漏》](https://blog.uwa4d.com/archives/UWA_ReportModule5.html)  
[《Unity性能优化 — 动画模块》](https://blog.uwa4d.com/archives/UWA_ReportModule6.html)  
[《Unity性能优化 — 物理模块》](https://blog.uwa4d.com/archives/UWA_ReportModule7.html)