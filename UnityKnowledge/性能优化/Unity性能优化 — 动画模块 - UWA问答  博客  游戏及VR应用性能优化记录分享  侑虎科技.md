---
title: "Unity性能优化 — 动画模块 - UWA问答 | 博客 | 游戏及VR应用性能优化记录分享 | 侑虎科技"
source: "https://blog.uwa4d.com/archives/UWA_ReportModule6.html"
author:
published:
created: 2026-06-28
description: "我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为&..."
tags:
  - "clippings"
---
## Unity性能优化 — 动画模块

我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为"升级版"的性能优化手册， **【Unity性能优化系列】** 将力图以浅显易懂的表达，让更多开发者可以受用。本期我们来继续分享动画模块相关的知识点。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/1.gif)  
[https://lab.uwa4d.com/lab/5b442633d7f10a201faf59b4](https://lab.uwa4d.com/lab/5b442633d7f10a201faf59b4)

目前在大家的报告中，我们可以看到和动画相关的主函数包括：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/2.png)

Animator相关的函数有两个：一个是DirectorUpdateAnimationBegin，一个是DirectorUpdateAnimationEnd，一般来说，我们都要关注这两个函数的堆栈，通过堆栈函数的调用次数、耗时占比来进一步定位原因。常见的影响性能的因素和优化对策有这些：

**1）控制Active的Animator数量**

角色数目的增加会导致整体耗时都增加，各个函数CPU耗时随着角色数据的增加近似线性地增大。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/3.png)

上图为某个项目的真人真机测评报告，我们选择某一帧查看其堆栈信息，发现ApplyOnAnimatorMove的调用次数高达168个，说明在当前场景下Update状态的Animator有168个，这个值是非常高的，一般来说建议尽量控制在30个以内。

**造成该值较高的原因通常是大量屏幕外的Animator仍在更新计算导致的CPU耗时，可能是缓存角色身上的Animator组件仍处于Active状态引起的，也可能是UI上的Animator组件过多引起的。对于UI上的Animator，如果动画较为简单，则建议尝试改用Dotween来实现。**

**2）建议排查“开启ApplyRootMotion”的Animator数量**

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/4.png)

通过Animators.Update的堆栈分析，可以看到Animator.ApplyBuiltinRootMotion占比高达28%，这一项通常和项目中开启了Apply Root Motion的模型动画相关。如果其动画不需要产生位移，则不必开启此选项。

**3）开启Optimize Game Objects选项**

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/5.png)

在勾选的状态下，Unity在处理动画片段时，会移除Transform的层级信息，该设置对于Animators.Update的耗时提升都非常明显，可以极大程度上降低主线程的动画耗时，把宝贵的主线程时间腾出来给更复杂的计算逻辑。

**4）控制Animator.Initialize触发频率**

Animator.Initialize会在含有Animator组件的GameObject被Active或Instantiate时触发，耗时较高，因此在战斗中不建议过于频繁地对含有Animator的GameObject进行Deactive/ActiveGameObject操作，如下图所示。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/6.png)

我们建议对于频繁实例化的角色，可尝试通过缓冲池的方式进行处理，在需要隐藏角色时，不直接Deactive角色的GameObject，而是DisableAnimator组件，并把GameObject移到屏幕外，从而降低Animator.Initialize的调用频率。

**5）AlwaysAnimate模式的Animator Controller数量过多**

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/7.png)

AlwaysAnimate状态下，当角色在屏幕外时，仍会继续产生Update开销。建议将这个选项改为CullUpdateTransforms或CullCompletely。CullUpdateTransforms适用于动画会产生位移的Animator Controller，CullCompletely适用于动画不会产生位移的Animator Controller。

**6）Animators.FireAnimationEventsAndBehaviours**

它是动画事件的具体耗时，主要是项目逻辑代码的性能开销，这种情况下建议研发团队进一步排查动画事件。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/8.png)

**7）群体动画渲染建议使用GPU Skinning+GPU Instancing**

建议关闭Unity引擎原生的GPU Skinning操作，该操作会导致额外的开销，会导致主线程或渲染线程无效的等待。

同时，对于大量同种怪物的需求，我们非常建议通过开源库中的GPU Skinning和GPU Instancing来进行渲染，这样既可以降低Animators.Update耗时，又能达到合批的效果。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/9.gif)

相关的开源库链接：  
[https://lab.uwa4d.com/lab/5bc6f85504617c5805d4eb0a](https://lab.uwa4d.com/lab/5bc6f85504617c5805d4eb0a)  
[https://lab.uwa4d.com/lab/5bc5511204617c5805d4e9cf](https://lab.uwa4d.com/lab/5bc5511204617c5805d4e9cf)

以上是我们优化动画模块时遇到的常见问题，供大家参考。出于效率，小编还是先给大家提供一个很套路但确实很高效的做法【我们永远应该做 **制作印刷机** 而非 **手工打制铜钱** 的事情】，大家可以参阅性能简报，按下ctrl+f搜索”动画“，如果你的报告中动画模块不太健康，很快就能看到这些未过关的检测项：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/10.png)

同样的，在我们的本地资源检测服务中也针对动画资源提供了以下4条检测规则，帮助大家进一步全面排查动画资源的相关设置的合理性。

- Compression!= Optimal的动画资源
- 精度过高的动画片段
- 包含Scale曲线的动画片段
- AnimationState数量过高的AnimatorController  
	![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule6/11.png)

以上就是在优化动画模块性能时需要关注的一些问题和对应的方法，如何操作还需要大家结合项目实际情况。当然我们UWA已经开发的GOT Online和本地资源检测都已经提供了很丰富的检测功能，希望能成为大家优化动画模块的神助攻。

【Unity性能优化系列】

[《Unity性能优化系列—渲染模块》](https://blog.uwa4d.com/archives/UWA_ReportModule1.html)  
[《Unity性能优化系列—加载与资源管理》](https://blog.uwa4d.com/archives/UWA_ReportModule2.html)  
[《粒子系统优化——如何优化你的技能特效》](https://blog.uwa4d.com/archives/UWA_ReportModule3.html)  
[《Unity性能优化系列—Lua代码优化》](https://blog.uwa4d.com/archives/UWA_ReportModule4.html)  
[《Unity性能优化系列 — 资源内存泄漏》](https://blog.uwa4d.com/archives/UWA_ReportModule5.html)  
[《Unity性能优化 — 物理模块》](https://blog.uwa4d.com/archives/UWA_ReportModule7.html)  
[《Unity性能优化 — UI模块》](https://blog.uwa4d.com/archives/UWA_ReportModule8.html)