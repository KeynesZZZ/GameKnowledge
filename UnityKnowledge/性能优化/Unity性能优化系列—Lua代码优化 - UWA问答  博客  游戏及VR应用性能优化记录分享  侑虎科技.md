---
title: "Unity性能优化系列—Lua代码优化 - UWA问答 | 博客 | 游戏及VR应用性能优化记录分享 | 侑虎科技"
source: "https://blog.uwa4d.com/archives/UWA_ReportModule4.html"
author:
published:
created: 2026-06-28
description: "我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为&..."
tags:
  - "clippings"
---
## Unity性能优化系列—Lua代码优化

我们曾在四年前对于Unity的主流模块的性能优化知识点逐一做过讲解，俗称“小白版”。随着这几年引擎本身、硬件设备、制作标准等等的升级，UWA也不断更新优化规则和方法并持续输出给广大开发者。作为"升级版"的性能优化手册， 【Unity性能优化系列】 将力图以浅显易懂的表达，让更多开发者可以受用。本期我们来分享Lua相关的知识点。

Lua可以说是现在商业游戏中的标配，随着大家Lua用得越来越重度，一些性能问题也开始浮出水面。无论是GPM、GOT Online还是真人真机测试报告中，我们经常会在一些逻辑代码的Top20的开销列表中看到Lua开销的相关函数，这就是要引起我们重视的。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/1.png)

有什么办法可以快速抓到Lua的瓶颈呢？让我们打开GOT Online的Lua报告看看它有什么很棒的feature吧：

这里小编先分别解释下报告页面中的几个标签，如下所示，我们依次来看下：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/2.png)

### 1、代码效率>>解决Lua CPU耗时较高的问题

在代码效率-CPU时间占用页面，可以看到Lua端的耗时。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/3.png)

点开这些函数，我们就可以查看这些函数的总体耗时堆栈、指定场景堆栈以及在任意一帧的具体耗时堆栈，迅速定位瓶颈函数。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/4.png)

**说明：** 可以通过这里提供的Lua文件名/行号/函数名来定位CPU耗时的瓶颈函数和CPU耗时峰值的具体原因。

Lua函数的命名格式为X@Y:Z，其中X是其函数名，在无法获取时，X会变为默认的unknown；Y是该函数定义的文件位置；Z则是该函数被定义的行号。需要注意的是，当Lua脚本以字节码运行时，该值将始终为0，因此建议在测试时尽可能使用Lua源码来运行。

**特别地，堆栈的分析支持倒序查看，很多时候我们需要展开堆栈点个几十层，看得头晕眼花，但如果我们切换成倒序分析，即将原始的CPU耗时堆栈进行倒序排列，从而将真正开销最大的深层子函数直接突显，研发团队就能很快定位开销的瓶颈。**

以某个项目为例，下图为正序排序的高耗时函数列表：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/5.png)

点开几层堆栈后我们发现这里有个大头子函数“Update@logic/factory/player\_builder/hall\_player:209”，但如果我们直接用倒序查看的话会怎么样呢？

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/6.png)

这个大头函数直接被排上了首位，那我们就直接拿这个函数开刀就可以啦~

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/7.png)

---

### 2、堆内存分配>>解决Lua堆内存分配较多的问题

Lua的堆内存分配同样是需要我们关注的，用来降低Lua GC的触发频率和触发时的开销。在报告中我们也是通过堆内存累计分配曲线+函数堆栈来定位造成堆内存分配的函数。

分析的思路如下：

**1、关注堆内存分配的峰值**

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/8.png)

**2、关注持续性的分配**  
如果每帧都有持续的开销，那一定需要特别关注，持续性的分配容易触发GC。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/9.png)

**3、堆内存分配倒序分析**  
在总体堆栈信息中关注倒序堆栈分配占比较高的父节点进行针对性优化：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/10.png)

如上图，在Lua的堆内存中我们同样可以这样切换成“倒序”：只需要切换查看方式，我们就可以直观地定位到底哪一个Lua脚本中的哪一行代码在分配大量堆内存。这样，研发团队就能直接打开对应的Lua脚本，找到那一行和函数直接修改。

---

### 3、Mono对象引用>> 解决让你秃头的泄露问题

**在任意一种Lua插件中，都存在类似的机制：在C#层维护一个Cache来引用那些被Lua访问过的C#层对象，防止出现以下的问题：当Lua中再次访问该C#对象时，该对象可能已经被C#层的GC回收掉了，从而导致逻辑错误。所以，在Lua中始终保留某个C#层对象的引用，将会导致其无法被释放，当这样的引用越来越多，就会导致C#层的内存泄漏。**

为了便于用户排查这种情况，我们在Mono对象引用的报告页面中对上述的Cache中C#层对象进行了汇总，统计了Cache中出现的对象类型和各个类型的对象总数。当该对象继承自UnityEngine.Object时，还将统计该类型中已经被Destroy的对象数量，如下图所示：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/11.png)

**所以，对于判断Lua引用导致Mono泄露的一个简单的方法就是查看Destroyed总数是否为零。因为它表示的是Mono端已经被Destroy但Lua端却依然被索引的变量总数，理论上应该是趋向于0的。如果它持续很高，甚至还有不断走高的趋势，那么很大概率是泄露了，如下图所示：**

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/12.png)

对于某些数量持续上涨的对象类型，还可以在图表下通过对比两个不同采样点的对象引用，从而进一步定位Lua中不合理的引用。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/13.png)

补充说明：但凡是排查泄露的需求，建议长时间测试，毕竟泄露问题一旦发生，聚沙成塔就很快了。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/14.png)

以上就是在优化Lua性能时需要关注的一些问题和对应的方法，如何操作还需要大家结合项目实际情况。当然我们UWA已经开发的 [GOT Online](https://blog.uwa4d.com/archives/Lua_Cpu.html) 和 [本地资源检测](https://blog.uwa4d.com/archives/UWA_Pipeline15.html) 都已经提供了很丰富的检测功能，希望能成为大家优化Lua的神助攻。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_ReportModule4/15.png)

【Unity性能优化系列】

[《Unity性能优化系列—渲染模块》](https://blog.uwa4d.com/archives/UWA_ReportModule1.html)  
[《Unity性能优化系列—加载与资源管理》](https://blog.uwa4d.com/archives/UWA_ReportModule2.html)  
[《粒子系统优化——如何优化你的技能特效》](https://blog.uwa4d.com/archives/UWA_ReportModule3.html)  
[《Unity性能优化系列 — 资源内存泄漏》](https://blog.uwa4d.com/archives/UWA_ReportModule5.html)  
[《Unity性能优化 — 动画模块》](https://blog.uwa4d.com/archives/UWA_ReportModule6.html)  
[《Unity性能优化 — 物理模块》](https://blog.uwa4d.com/archives/UWA_ReportModule7.html)  
[《Unity性能优化 — UI模块》](https://blog.uwa4d.com/archives/UWA_ReportModule8.html)