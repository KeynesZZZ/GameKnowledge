---
title: "Unity性能优化系列 — 资源内存泄漏 - UWA问答 | 博客 | 游戏及VR应用性能优化记录分享 | 侑虎科技"
source: "https://blog.uwa4d.com/archives/UWA_ReportModule5.html"
author:
published:
created: 2026-06-28
description: "我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为&..."
tags:
  - "clippings"
---
## Unity性能优化系列 — 资源内存泄漏

我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为"升级版"的性能优化手册， **【Unity性能优化系列】** 将力图以浅显易懂的表达，让更多开发者可以受用。本期我们来分享资源泄露相关的知识点。

内存泄露是我们平时最常遇见，且最怕遇见的。为什么？

因为在我们定位到泄露瓶颈之前，我们根本无法预知泄露的程度是怎样，是否会在线上的某一刻集中爆发。曾经有小伙伴反馈，我们玩家玩了半小时没问题，但3~4小时之后会越来越卡，这个是他们之前万万没有想到的。那该怎么解决？今天这篇小笔记回答你的疑问。

无论是UWA的真人真机测试报告还是GOT Online-Assets报告，都有资源的占用走势图，如果出现下图这种步步高升的趋势，就要特别留意。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/1.png)

或者是这样：一山更比一山高

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/2.png)

出现这种情况的具体原因 大概率是研发团队对加载后的资源进行了缓存（比如放到Container中），但在场景切换时并没有将其Remove或Clear，从而无论是引擎本身还是手动调用Resources.UnloadUnusedAssets等相关API均无法对其进行卸载，进而造成了资源泄露。

在这里就为大家介绍我们常用的排查资源内存泄漏的思路逻辑。

**1、关注资源的生命周期**

即了解每个资源在项目运行过程中的使用范围。在报告的【资源具体详情】页面中，我们可以看到运行过程中出现的资源信息。勾选指定的资源，即可在生命走势图中看到它被加载和卸载的场景。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/3.png)

这个功能，主要是帮助大家快速查看有哪些资源是“常驻”内存的，并且判断该资源是“预加载”资源还是“泄露”资源。常见的Loading图、Login图（如下图所示），往往占用较大的内存，我们建议没必要做常驻内存。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/4.png)

**2、查泄露具体方法>>场景/帧 资源对比**

通常情况下项目的资源数是成百上千的，我怎么排查泄露比较科学呢？我们推荐通过以下几种方式进行资源比较，以便更快地找到存在“泄露”问题的资源：

**1）同类型场景/同一场景比较：关注差异资源**

同类型/同一场景的资源使用一般情况下较为固定，我们可以对比不同时刻、同类/同一场景的“差异”资源，只需要判断这些“差异”资源的存在是否合理，就可以快速判定是否存在泄漏资源以及具体哪个资源泄露了。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/5.png)

**2）不同类型场景比较：关注相同资源**

除常驻资源外，不同类型的场景使用的资源是完全不同的，我们可以比较两种不同类型场景的相同资源，判断其是否为常驻资源，如果不是，则很可能就是泄漏资源了。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/6.png)

**3）不同帧之间的对比**

此外，我们还可以通过不同帧之间的相同资源和差异资源来排查共有项/差异项是否合理。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/7.png)

只要找对方法，定位精准，问题修复是非常快的。

同时，这里小编还要建议大家平时备有长时间的测试用例，以此来规避泄露的问题，很多研发团队为了图方便省事，仅仅跑个10~15分钟，其实这些测试样本还是远远不够的，我们要尽量还原玩家的真实场景，在优化阶段尽量多做充分的测试。

当然，更可取的方法是通过一些自动化脚本来进行回归测试， 譬如新手开始的30分钟、副本的长时间挂机等，这些多数都可以通过自动化脚本来替代 ；而 [UWA已推出的Pipeline服务，支持多终端自动化测试，也能很好地契合这种长时间测试的需求。](https://blog.uwa4d.com/archives/UWA_PipelineBuild2.html)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule5/8.gif)  
中重度卡牌游戏上的推图用例

以上就是在优化内存时需要关注的一些问题和对应的方法，如何操作还需要大家结合项目实际情况。当然我们UWA已经开发的线上服务（GOT Online和真人真机测试）已经提供了很丰富的检测功能，希望能成为大家的神助攻。

【Unity性能优化系列】

[《Unity性能优化系列—渲染模块》](https://blog.uwa4d.com/archives/UWA_ReportModule1.html)  
[《Unity性能优化系列—加载与资源管理》](https://blog.uwa4d.com/archives/UWA_ReportModule2.html)  
[《粒子系统优化——如何优化你的技能特效》](https://blog.uwa4d.com/archives/UWA_ReportModule3.html)  
[《Unity性能优化系列—Lua代码优化》](https://blog.uwa4d.com/archives/UWA_ReportModule4.html)  
[《Unity性能优化 — 动画模块》](https://blog.uwa4d.com/archives/UWA_ReportModule6.html)  
[《Unity性能优化 — 物理模块》](https://blog.uwa4d.com/archives/UWA_ReportModule7.html)  
[《Unity性能优化 — UI模块》](https://blog.uwa4d.com/archives/UWA_ReportModule8.html)