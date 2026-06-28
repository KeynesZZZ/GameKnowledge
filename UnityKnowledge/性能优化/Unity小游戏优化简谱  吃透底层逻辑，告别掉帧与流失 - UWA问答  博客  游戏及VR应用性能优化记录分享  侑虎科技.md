---
title: "Unity小游戏优化简谱 | 吃透底层逻辑，告别掉帧与流失 - UWA问答 | 博客 | 游戏及VR应用性能优化记录分享 | 侑虎科技"
source: "https://blog.uwa4d.com/archives/UWA_MiniGame.html"
author:
published:
created: 2026-06-28
description: "做Unity小游戏的开发者，大概都遇到过这样的困境：明明在编辑器里跑得好好的，打包成WebGL上线后，却出现掉帧、发热、启动慢、甚至闪退的问题。用户一卡就流失，好不容易拉来的流量也留不住。这篇文..."
tags:
  - "clippings"
---
## Unity小游戏优化简谱 | 吃透底层逻辑，告别掉帧与流失

做Unity小游戏的开发者，大概都遇到过这样的困境：明明在编辑器里跑得好好的，打包成WebGL上线后，却出现掉帧、发热、启动慢、甚至闪退的问题。用户一卡就流失，好不容易拉来的流量也留不住。这篇文章，就从小游戏的底层原理讲起，帮你一步步定位性能瓶颈，把这些“隐形杀手”逐个击破。

> ### 1\. 前言

本章从“什么是小游戏”出发，简要介绍小游戏的概念、适用范围与开发原理，并梳理Unity小游戏性能优化的必要性及问题定位的基本思路，为后续各章节的深入讨论提供背景框架。

#### 1.1 什么是小游戏

“小游戏”是一个较为宽泛的概念。广义上，它通常指轻量、上手快、适合碎片化时间游玩的游戏；而对开发者而言，它更多是指依托于特定平台运行的游戏应用。例如微信在2017年推出的爆款小游戏“跳一跳”，无需额外安装，直接在微信内即可游玩。如今，微信、抖音、快手、QQ、支付宝等多个平台都提供了小游戏入口，品类也日益丰富。

这类基于常用平台的小游戏往往无需下载、安装或卸载，即点即玩，体验更轻便。除即时体验外，小游戏还能借助平台的账号体系、好友关系等能力，具备较强的社交属性，例如排行榜与邀请等功能。相较于APP手游，小游戏在类型上更偏轻松休闲，但也不乏玩法更复杂的重度产品。近年来，不少APP游戏也移植了小游戏版本，借助平台流量实现快速获量与更高的用户留存。

#### 1.2 适用范围

本文主要针对Unity WebGL转微信小游戏（下文简称微小）的性能优化场景，文中的经验数据、工具链说明和优化建议大多基于此方案。部分结论（如性能差异倍数、内存阈值、WASM编译内存估算等）不一定适用于Cocos/Laya/Godot等其他引擎，也不一定适用于抖音、快手等非微信平台。读者在参考时请结合自身项目的引擎、宿主平台和运行环境具体分析。

#### 1.3 小游戏的开发原理

各类小游戏平台通常面向多样化的开发需求，支持开发者使用不同的游戏引擎或技术方案进行开发，常见包括Unity、Cocos、Godot、Laya等。小游戏平台并不直接绑定具体的游戏引擎，而是以引擎构建的产物作为接入与运行的基础。各引擎均有对小游戏的适配与支持，能输出合适的产物在小游戏环境中运行，具体适配原理可参考对应引擎的官方文档，此处不再展开。当前简谱主要针对使用Unity引擎开发并转换的小游戏项目。

以上常见的游戏引擎可分为两类：基于JavaScript/TypeScript的HTML5游戏引擎，以及原生目标的游戏引擎，Unity属于后者。两种类型的适配方式有所不同。对于Unity项目而言，适配方式基于WebAssembly技术，将游戏代码导出为WASM代码，通过胶水层代码运行在浏览器环境中。这种方式的优势在于保持原有引擎工具链和技术栈不变，开发者无需重写游戏核心逻辑，通过转换工具即可完成小游戏适配。

#### 1.4 为什么要关注Unity小游戏的性能

玩家遇到掉帧、卡顿、发热、闪退等性能问题时，无论游戏美术是否精良、玩法是否有趣，体验都会直接变差，黏性随之下降。小游戏易上手、节奏快，遭遇性能问题后玩家流失会更快。

此外，相比于APP，小游戏即开即用的特点使玩家对启动耗时更加敏感 —— 从点开到进入正式场景的时间过长，用户流失的可能性就会越大。

从技术角度来看，Unity小游戏以WebAssembly（WASM）+ WebGL为核心技术方案，运行性能会极大影响可承载的游戏内容玩法。开发者需要关注不同技术栈带来的性能差异，以及不同系统平台（Android、iOS、Windows PC）之间的性能差异。

**1.4.1 Unity WebGL与APP的运行性能差异**  
**CPU性能差异：**

- Unity WebGL以WASM虚拟机的形式运行在类浏览器环境中，CPU算力受限于虚拟机的执行效率。
- 在多数小游戏运行环境和Unity WebGL转小游戏方案中，常规C# 多线程/Job多线程能力受限，不能按原生APP的线程模型使用，导致AI、动画、渲染等模块无法获得多线程加速。新版Unity Web平台已提供WebAssembly threads支持入口，但标准C# 多线程仍有限制，且依赖浏览器/宿主对SharedArrayBuffer等能力的支持。

这是导致Unity WebGL与APP存在性能差距的最主要因素。 ***作为常见经验值/保守预算，Unity WebGL通常约为APP手游性能的1/3，开发者应特别关注CPU侧的性能瓶颈。但需明确，不同机型、Unity版本、是否开启iOS高性能模式、业务瓶颈在CPU还是GPU，都会显著影响这一比例。***

**GPU性能差异：**

- Unity以WebGL API进行渲染，其中WebGL 1.0相当于OpenGL ES 2.0，WebGL 2.0相当于OpenGL ES 3.0。
- WebGL在原生渲染API之上封装存在少量开销，但基本渲染能力与原生APP接近。
- GPU Instancing、SRP Batcher等渲染特性需要WebGL 2.0。当APP手游使用了这些特性而小游戏未开启WebGL 2.0时，性能差距会进一步拉大。

**1.4.2 WASM与JS的运行差异**

- WASM是静态类型的二进制指令格式（虚拟机字节码），其类型系统使JIT优化能更准确地预判运行期类型，因此能更快达到JIT指令优化后的峰值。在计算密集型、类型稳定的场景中，WASM通常更容易获得稳定性能，但具体差距依赖引擎、宿主、代码形态和平台，不能简单以固定倍数对比。
- Unity引擎目前未针对浏览器环境做充分优化（如WASM与宿主接口互调频次偏高、未做充分的代码路径裁剪），整体较为臃肿，部分应用场景反而逊于JS的轻量实现。

因此，两者在实际使用中不能简单以语言算力对比，需以实测游戏为准。

**1.4.3 系统平台之间的性能差异**

- **Android与Windows PC：** Android平台（以微信小游戏为例，通常基于XWeb/Chromium体系，WASM虚拟机内核大体可理解为V8）与Windows PC均使用V8作为WASM虚拟机内核，均支持JIT，在相同算力条件下两者性能接近。但需注意移动平台散热更差，对性能要求更苛刻。不同平台和宿主版本的实际内核可能存在差异，不宜一概而论。
- **iOS：** iOS默认为普通模式，不支持JIT，可用于超休闲游戏；中重度游戏建议开启 [iOS高性能模式](https://developers.weixin.qq.com/minigame/dev/guide/game-engine/unity-webgl-transform/Design/iOSOptimization.html) 以支持JIT，但该模式需要更多精力进行调优，尤其在启动发烫与内存方面。

#### 1.5 如何确定问题

**定位思路**  
发现性能问题后的第一步就是确定问题。如果阅读过UWA提供的 [《Unity移动端游戏性能优化简谱》](https://edu.uwa4d.com/course-intro/0/430) ，读者可能已对Unity常见性能问题有一定认知。在小游戏侧，移动端的知识体系大部分仍然适用，但也有不少小游戏独有的问题需要特别留意。总之，确定问题本身也是一项挑战。

**可用工具**  
工欲善其事必先利其器，直接精确的性能数据能更直观地反映性能瓶颈，事半功倍。从小游戏角度，可用工具主要分为三个层面：

- **平台层：** 各小游戏官方平台基本都提供自带的性能调试与监控工具（如微信/抖音开发者工具）。
- **引擎层：** Unity Profiler、Memory Profiler等，用于定位引擎内部的CPU与内存瓶颈。
- **系统层：** Android Studio Profiler、Xcode Instruments等，用于从进程视角分析整体资源消耗。

此外，UWA已对微信、抖音等小游戏平台提供支持。UWA GOT Online工具可通过SDK快速集成到测试项目中，真机测试完成后在极短时间内完成数据上传与解析，自动生成一系列可视化图表。同时，基于UWA丰富的优化经验和数据库进行评分，针对各性能模块提供分析建议和参数变化趋势。

> **通用原则 —— PC开发者工具 vs 真机测试：** 小游戏开发中，PC端开发者工具的便捷性很容易让人依赖其数据进行性能判定，但工具环境与真机环境在多方面存在显著差异，贯穿CPU、内存、GPU、启动耗时等所有性能维度。例如：纹理压缩格式（ASTC等）在PC上会回退为RGBA32导致内存虚高、WASM编译与JIT行为在iOS/Android真机上与PC模拟差异明显、PC的高性能CPU会掩盖真机上更易暴露的瓶颈。因此， **任何时候都应优先以真机测试数据为最终依据，PC开发者工具仅用于初步调试和功能验证** 。后续各章节中也会反复强调这一原则。

**问题定位检查清单**

- 确认问题现象：掉帧/卡顿/发热/闪退/启动慢，明确优化目标
- 使用平台调试工具（微信/抖音开发者工具）获取初步性能数据
- 使用Unity Profiler/Memory Profiler定位引擎层瓶颈
- 真机测试（Android + iOS），勿仅依赖PC开发者工具数据
- 借助UWA GOT Online等第三方工具获取深度分析报告与优化建议
- 对比APP版本与原生性能基线，区分通用问题与小游戏特有问题

> ### 2\. 启动耗时

启动耗时是玩家对小游戏最直接的性能第一印象。本章围绕启动流程中的三个核心环节 —— 首包资源下载、WASM代码下载与编译、引擎初始化及首帧逻辑 —— 逐一分析各阶段的优化方法，并汇总可落地的检查清单。

#### 2.1 启动流程概览

当玩家上手一款小游戏时，最先影响到体验的性能指标就是启动耗时。在小游戏快节奏的环境下，启动过长可能导致玩家尚未体验游戏内容就已流失。根据微信小游戏官方数据，普通小游戏启动时间为7~10s，不经优化的Unity WebGL游戏启动可达该时间的2~3倍以上。 **优化目标是将首屏启动耗时控制在5~10s甚至更短** 。

以微信小游戏（以下简称微小）为例，Unity WebGL转换的微信小游戏主要依靠Unity Loader进行初始化，其工作流程如下：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/1.png)

不同平台小游戏的启动细节可能略有差异，但总体可归纳为三个核心环节： **首包资源下载、WASM代码下载和编译、引擎初始化与开发者首帧逻辑** 。

此外，UWA GOT Online的小游戏报告中也提供了启动耗时的相关指标、推荐值和优化建议，可帮助快速定位耗时较高的阶段：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/2.png)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/3.png)

#### 2.2 首包资源下载

**首包是什么：** 一般名称为xxx.webgl.data.unityweb.bin.txt，存放在CDN服务器上。首次进入游戏时下载、解压后保持在内存，二次启动可直接走缓存。因此对启动耗时而言，主要关注首次下载或首包更新时的下载耗时。

**首包内容构成：** 首包文件大小直接影响下载耗时，可使用AssetStudio查看其中包含的资源，通常包括：

- Unity Default Resources — 引擎默认资源（Arial字体、默认Mesh、纹理等）
- IL2CPP Meta Data — C#代码经IL2CPP生成的类、方法等元信息
- unity\_builtin\_extra — Always Included的Shader
- BuildSettings中所有Active的场景
- Resources文件夹中的资源及其引用的其他资源
- 全局设置及引用到的资源（如Splash图片等）

**优化方法：**  
**1\. 排查与精简：** 结合AssetStudio查看首包内容，排查其中内存占用较高或不符合预期出现的资源，尽量只保留首场景中的必要资源。下图为AssetStudio中看到的部分首包内容。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/4.png)

举例来说，加载过程的提示文字可能会使用自定义字体，如果用全量字体其内存占用对于首包来说可能过大。然而实际在加载过程中用到的文字量有限，可考虑单独拆分出一个更小的字体专门用于首包。

**2\. 转化工具设置：** 勾选转换工具面板的“压缩首包资源”选项，可对首包进行进一步br压缩。微信还提供了首包资源优化功能，可清理首包中项目并未实际使用的资源，进一步瘦身。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/5.png)

**3\. 目标值：** 一般建议将首包资源大小控制在 **5MB以下** 。

#### 2.3 WASM代码下载与编译载

**代码包是什么：** 一般名称为xxx.webgl.wasm.code.unityweb.wasm.br，默认进行br压缩。在启动阶段，wasmcode与首包资源并行下载，共同占用下载带宽；下载完成后进行编译，编译过程本身也消耗CPU资源。综合来看，核心优化方向是降低WASM代码体积，一般建议将原始代码包控制在 **30MB以下** 。

**优化方法：**  
**1\. 代码分包（最常用）：** 在开发者工具中安装wasmCodeSplit插件，原理是将原WASM拆分为主包（启动加载）和子包（延迟加载）。小游戏先加载较小的主包进入主场景，再异步加载剩余分包，可大幅降低下载与编译耗时。具体操作可参考官方文档。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/6.png)

> **注意：** 如果直接从拓展商店中安装插件失败，出现如下报错，可以直接从 **设置-拓展设置-编辑器拓展** 中找到wasmCodeSplit插件进行安装。
> 
> ![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/7.png)
> 
> ![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/8.png)

**2\. 代码裁剪：** Unity未针对WebGL平台做特别裁剪，默认会将引擎、业务代码、第三方插件全部编译为WASM二进制。建议勾选“Strip Engine Code”并将“Managed Stripping Level”设为High，可有效缩减代码包体积。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/9.png)

**3\. IL2CPP Size选项：** 使用Unity 2021以上版本时，可在PlayerSettings中将IL2CPP选项设为更小尺寸（SIZE），减少函数量。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/10.png)

**4\. 删除多余插件：** 排查项目使用的第三方插件，手动移除不必要的Unity模块（如物理模块、Unity数据统计等），从源头减少代码量。

#### 2.4 引擎初始化与开发者首帧逻辑

**该阶段做什么：** 引擎自身模块与数据初始化、首个场景加载以及MonoBehaviour的Awake/Start流程。此阶段CPU处理密集，但网络处于空闲状态，可利用预下载功能提前缓存后续资源（详见第3章资源加载）。

**优化要点：**

- MonoBehaviour脚本在首帧的Start/Awake中应尽量少做逻辑，优先把画面呈现出来
- 初始场景不宜过大，通常只呈现Splash场景即可
- 初始场景中如需加载后续主场景或配置，建议采用分帧策略，切勿在Start/Awake中阻塞

**调试工具 —— Android CPU Profiler**  
微信提供了Android CPU Profiler功能，可用于排查此阶段的CPU逻辑开销。使用方法如下：

1. 从右上角“…”打开菜单 → 开发调试 → 选择Start CPU Profile开始采集
2. 采集一段时间后点击Stop CPU Profiler，生成.cpuprofile文件
3. 文件路径通常为：Android/data/com.tencent.mm/MicroMsg/appbrand/trace
4. 数据可通过Chrome、Edge，或开发者工具中的JavaScript探测器打开分析

> **注意：** 若希望在堆栈中看到可读函数名，需勾选Profiling-funcs或使用Development模式，但会带来一定性能开销。否则函数仅显示数字ID，需借助symbols文件进行映射（微信提供Python替换脚本可自动处理）。此外，若要排查启动阶段，可手动修改game.js，让游戏在启动时增加一段黑屏等待时间，便于在启动期间打开调试。

#### 2.5 启动耗时检查清单

- 首包资源<5MB，仅包含首场景必要资源
- WASM原始代码包<30MB
- 开启代码分包（wasmCodeSplit插件）
- 勾选“Strip Engine Code”，Managed Stripping Level设为High
- Unity 2021 + 设置IL2CPP选项为更小尺寸（SIZE）
- 首场景只保留Splash，Awake/Start不阻塞主线程
- 初始场景中后续加载采取分帧策略，不在首帧同步完成

> ### 3\. 资源加载

启动耗时章节提到首包内容应尽可能精简，其余资源需放在CDN中延迟加载，因此资源的按需加载是小游戏中至关重要的环节。本章从加载方案选择、缓存机制、AssetBundle适配三个维度展开，帮助开发者在加载效率与内存占用之间找到平衡。

#### 3.1 常规加载方案

**三种方案对比：** 目前常见的加载策略有三种 —— Addressable方案、AssetBundle方案、Unity Instant Game方案。无论哪种方案，微信小游戏环境均不支持本地Bundle加载，最终都采用上传CDN方式在游戏运行时异步按需下载。

- **Addressable（AA）：** Unity官方推荐的资源管理方案，支持远程加载与本地缓存，适合大多数项目。
- **AssetBundle（AB）：** 传统分包方案，在内存和加载效率方面优于AA，尤其适合相对重度的游戏。目前UWA接触的小游戏项目中使用AB方案的偏多。
- **Instant Game：** Unity官方提供的自动加载方案，仅适合原生APP未使用资源按需加载、总包体较小的轻度游戏，具体参考 [团结引擎文档](https://docs.unity.cn/cn/tuanjiemanual/Manual/Wechat.html) 。

对于AA和AB两种方案，一般可以沿用原APP游戏工程的管理方案，转化工作量相对较小。后续讨论以AssetBundle方案为主，其余方案可参考官方文档。

**AB打包参数建议：** 使用AssetBundle进行资源打包时，推荐以下设置：

- BuildAssetBundleOptions.AppendHashToAssetBundleName：开启后Bundle名会携带Hash，是小游戏中资源缓存及缓存淘汰机制的重要依据（详见3.2节）。
- BuildAssetBundleOptions.ChunkBasedCompression：LZ4压缩方式，加载速度与包体大小更均衡。
- DisableWriteTypeTree：如无新老Unity版本兼容需求，建议开启以提升加载速度并降低内存。

**加载接口：** 小游戏不支持AssetBundle本地加载，从服务器下载Bundle主要使用以下接口：

- UnityWebRequestAssetBundle.GetAssetBundle
- UnityWebRequest

不建议使用WWW.LoadFromCacheOrDownload或WWW等带Cache接口，WebGL模式下会通过JS模拟文件系统，带来额外内存消耗。

#### 3.2 资源缓存

**缓存机制：** Unity Loader插件已内置资源缓存与淘汰功能，无需开发者自行实现。UnityWebRequest和UnityWebRequestAssetBundle接口均会自动触发缓存，业务侧无需关心资源是否有缓存，正常调用API即可。可通过Loader插件返回的Log判断当前是走下载还是缓存。

**预下载：** Loader插件提供预下载功能，目的是充分利用网络带宽。启动流程中「引擎初始化与首场景准备」阶段CPU处理密集，但网络处于空闲，利用预下载可在此阶段提前下载并缓存资源，后续即可直接走本地缓存。预下载文件总体积建议控制在 **3~5MB** 以内，文件数量不超过 **10个** （此阶段最多10个并发，超出将排队）。

**缓存过滤：** 并非所有文件都适合缓存。可在导出面板中配置不自动缓存的文件类型（如默认不缓存.json文件），也可在minigame/unity-namespace.js中手动处理缓存逻辑。

**版本管理：** 若资源文件已缓存到本地但后续版本更新，不特殊处理会继续加载旧缓存。需要以Hash区分资源版本 —— 本地有旧缓存时先清理再写入新版本。只需将资源URL携带Hash作为版本依据即可，默认Hash长度为32；若游戏自行计算CRC，也可设为CRC长度。注意Hash必须以‘-’或‘\_’作为分隔符，其他符号无法正确处理版本信息。

**缓存上限与淘汰：** 缓存体积随游戏进程逐渐增大，默认上限为 **200MB** 。可通过 maxStorage调整上限，也可前往微信后台申请空间提升，最高可达 **1GB** 。达到上限后Loader按LRU规则清理早期缓存。为避免频繁触发，默认额外多清理30MB（可通过defaultReleaseSize修改）。清理时支持忽略指定文件使其不被自动清理，仅可主动删除，具体通过minigame/unity-namespace.js中isErasableFile函数控制。

**常用接口：**

- public string WX.PluginCachePath：获取自动缓存的文件存储路径，返回值：${wx.env.USER\_DATA\_PATH}/\_\_GAME\_FILE\_CACHE
- public string WX.GetCachePath(string url)：传入URL或文件相对路径，返回缓存路径（无缓存则返回空字符串）
- public void CleanAllFileCache(Action action)：清理所有自动缓存的文件
- public void CleanFileCache(int fileSize, Action action)：从缓存目录中释放指定大小的文件
- public void RemoveFile(string path, Action action)：从缓存目录中删除指定文件

#### 3.3 小游戏中的AssetBundle

**AB内存差异：** AssetBundle打包后的文件由文件头（属性数据、Asset信息、依赖关系等）和主数据（平台对应的Asset数据）两部分组成。在Standalone、Android、iOS等具有本地文件系统的平台上，只需加载文件头，运行时按需读取资产数据。而WebGL平台受浏览器权限限制不能直接访问本地IO，加载AB时需将两部分全部加载到内存中。因此，原生APP只需关注AB文件头内存，但小游戏还需额外关注AB文件本身的内存占用。

**WXAssetBundle方案：** 小游戏平台提供了专用AB接口来解决上述问题。以微信小游戏为例，使用WXAssetBundle将文件系统接口桥接到微信的文件系统，使AB可读写到小游戏缓存目录，从而避免AB文件整体进入内存。经测试，使用Unity原生AB接口时，AB文件本体内存会进入UnityHeap并被Reserve；更换为WXAssetBundle后，该内存不再出现在UnityHeap中，而是进入本地缓存（仍需关注默认200MB上限）。

在UWA GOT Online小游戏报告中，也专门统计了WXAssetBundle接口的内存数据。下图为同一AssetBundle、不同加载接口的对照测试 —— 前半段为WXAB接口加载/卸载，后半段为Unity原生AB接口。可见前者几乎不会使Reserved Total升高，后者则有明显变化。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/11.png)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/12.png)

**打包策略：** 无论使用哪种AB接口，打包策略都值得关注。分包粒度太大，单个AB下载易卡顿；粒度太小则文件数量过多，IO和下载效率下降。建议根据资源使用频率和生命周期采用混合策略 —— 常更新的资源（如UI元素）打包至较小Bundle便于热更新，不常更新的资源（如场景资源）可打包至较大Bundle。通常单个AB包建议控制在 **10MB** 以内，总体AB驻留数量在 **1000个** 以内。

**AB利用率：** UWA提出了AB利用率的概念 —— 在特定测试流程中，某AB文件被加载进内存但真正用到的资产（含主动加载与被动依赖）比例很低，则判定为低利用率。这类AB的打包策略可能存在浪费，定位到具体AB后可进一步排查，对包内资产进行更精细的划分。

#### 3.4 资源加载检查清单

- 打包参数：开启AppendHashToAssetBundleName，使用ChunkBasedCompression (LZ4)
- 非跨版本兼容需求时，开启DisableWriteTypeTree
- 使用UnityWebRequest/UnityWebRequestAssetBundle加载（不用WWW等带Cache接口）
- 预下载文件总体积控制在3~5MB，文件数≤10个
- 单个AB包<10MB，总体AB驻留数量<1000 个
- 检查AB利用率，避免大量未使用资产进入内存
- 关注缓存上限（默认200MB，可申请提升至1GB），必要时调整maxStorage

> ### 4\. 内存

内存是小游戏中与闪退直接挂钩的核心性能指标，其分布结构、扩容机制和平台限制均与原生APP存在显著差异。本章从小游戏进程视角出发，梳理内存的整体构成与各子模块的优化要点，并对比iOS不同运行模式下的内存分布差异。

#### 4.1 进程视角的内存限制

**Android：** 小游戏通常运行在独立进程中（如微信小游戏为 com.tencent.mm:appbrand0/1/2），内存相对宽松。一般建议低端机 **<1.2GB** ，中高端机 **<1.5GB** 。可通过ADB或UWA Gears工具查看进程内存，下图为Gears采集到小游戏运行时的PSS内存走势。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/13.png)

**iOS：** 整体限制更严格，建议低端机 **<1GB** ，中高端机 **<1.4GB** ，最终需结合Xcode Instruments实际数据具体分析，微小通常关注com.apple.WebKit.WebContent进程。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/14.png)

iOS根据运行模式的不同，内存限制也有所差异：

- **普通模式（默认）：** WASM运行无JIT，计算性能受限。小游戏进程与微信绑定，同在WeChat进程中。
- **高性能模式：** CPU算力明显提升，但内存限制更严格 —— 2GB内存设备上限约1GB，3GB及以上设备上限约1.5GB，工程上建议控制在 **1.2~1.3GB** 以内。此时小游戏运行在独立进程com.apple.WebKit.WebContent中。
- **高性能+模式：** 在高性能模式基础上进一步升级，保留游戏独立进程的同时将渲染重新挪回微信进程，渲染效果和渲染内存消耗均得到改善。推荐使用WebGL2、内存压力大的游戏开启该模式。

#### 4.2 小游戏内存结构

Unity WebGL以WebAssembly+WebGL技术为基础，游戏内存分配完全托管在浏览器环境中。适配到小游戏后，进程成为“容器”，内存组成结构基本一致。典型游戏的内存分布如下图所示：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/15.png)

各内存区域简要说明：

- **UnityHeap：** 托管堆、本机堆与原生插件底层内存，初始值为转化面板中的“UnityHeap预留内存”，运行时只增不减且存在内存碎片。这是大部分小游戏项目中最主要的内存来源，是排查与优化的重点。
- **WASM编译：** 代码编译与运行时指令优化产生的内存，占比相对较高。一般无工具直接检测该部分精确占用。常见经验上可按未压缩WASM代码包的约 **8~12倍** 进行数量级估算，但实际比例受平台内核（iOS/Android）、是否开启JIT、分包策略及编译优化等级影响较大， **以真机实测为准** 。
- **GPU内存：** 纹理或模型Upload GPU后的显存占用。压缩纹理格式支持受宿主、浏览器、设备GPU和转换方案影响，PC开发者工具中可能回退为RGBA32， **必须以真机实测为准** 。
- **音频：** Unity将音频传递给容器后，播放时占用的内存。
- **基础库+Canvas：** 小游戏公共库、Canvas画布等固定开销，基本无法针对性优化。
- **其它：** Emscripten文件系统模拟等相关占用。

**4.2.1 UnityHeap**  
**扩容机制：** UnityHeap是为实际使用的内存部分提前预留的上限，实际占用指标为DynamicMemory。当DynamicMemory接近预留上限时（如初始500MB，达到约490MB以上），会触发扩容 —— 在内存中新分配一个更大的堆空间（如550MB），将旧内容复制过来后再释放旧堆。短时间内产生内存块复制导致的内存尖峰，极易造成闪退，尤其在iOS上更为严重。

**初始值设定：** 不宜过小（频繁扩容导致尖峰），也不宜过高（≥1024MB直接导致启动失败）。官方参考值：轻度游戏（休闲类） **256MB** ，中度游戏（模拟经营、卡牌成长） **496MB** ，重度游戏（SLG、MMO） **768MB** 。

**DynamicMemory构成：** DynamicMemory=MonoHeap+NativeReserved+原生插件内存，需分别关注各部分走势，避免泄漏。

**Mono堆内存** 是C#脚本托管对象（string、List、自定义类实例、委托等）的核心内存区域。GC会正常回收对象，Mono使用量可以有增有降；但受WebAssembly内存沙箱机制影响，堆容量一旦被峰值撑高便难以回缩，表现为峰值保持。因此在小游戏上要特别关注Mono的分配，避免单帧内出现大量分配把峰值顶上去。

**NativeReserved** 由Unity Native产生，属于引擎内部对象。动画、字体、Shader等资源类内存均包含在此。纹理、网格等传给GPU的资源原本计入GPU内存，但若开启了Read/Write Enable选项，CPU端还会额外存储一份，计入NativeReserved。此外，使用Unity原生AssetBundle接口时AB文件本体内存也会进入NativeReserved，使用WXAssetBundle可将其转移至本地缓存。

从WXAB和原生AB的加载对比测试数据中可以看到：使用原生AB接口会使NativeReserved明显上升，连带推高DynamicMemory；即使卸载后NativeReserved回落，DynamicMemory也已被撑高，剩余空间相当于被预留住了。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/16.png)

针对Native部分的排查可使用Unity Memory Profiler工具，需开启Development Build及AutoConnect。

**第三方原生插件内存** （如Lua）通常没有单独数值展示，可观察DynamicMemory与Mono、Native部分的差值是否偏大。若对插件管理较明确，可通过对比测试（开关插件观察内存变化）进一步定位来源。

**4.2.2 WASM编译**  
小游戏启动时下载WASM代码包并进行编译，编译后占据的内存很大。常见经验上可按未压缩WASM代码包的约 **8~12倍** 进行数量级估算（如微信官方数据：iOS上30MB未压缩代码约需300MB运行时编译内存），但实际比例受平台内核、是否开启JIT、分包策略及编译优化等级影响较大， **以真机实测为准** 。

最常见有效的优化方案是代码分包 —— 将原WASM代码包拆分为主包和子包：

- **主包（wasmcode）：** 启动时首先加载，大小约为原包的1/3~1/2，建议控制在3~5MB，需尽量覆盖大多数游戏场景和流程。
- **子包（wasmcode1/wasmcode2）：** 分别对应Android和iOS平台，约7~15MB，在游戏运行一段时间后自动加载或缺失函数时再加载。

分包后总大小可能比原包更大（因多出复制文件），但只有主包一定加载，其余延迟或按需下载，对运行几乎无影响。

**4.2.3 常见资源类型内存**  
对于Unity开发者而言，更直观、更容易上手修改的是纹理、网格、动画、字体等常见资源类型。各类资源在小游戏内存中的归属如下：

- **GPU内存：** 纹理、网格、RenderTexture
- **NativeReserved（UnityHeap内）：** 动画、字体、Shader、开启了Read/Write的纹理/网格、使用原生AB接口的AB文件本体
- **独立内存：** 音频资源

[《Unity移动端游戏性能优化简谱》](https://edu.uwa4d.com/course-intro/0/430) 中对各类资源内存优化已有系统介绍，以下仅提炼各类型的核心优化要点：

**纹理：** 内存大户，重点关注三个方面 —— ①格式：避免RGBA32/ARGB32等未压缩格式，优先使用ASTC/ETC2等移动端压缩格式（注意小游戏中格式支持因宿主和真机而异，务必真机验证）；②分辨率：1024以上的纹理需评估是否必要，高分辨率在小屏幕上往往看不出差异却占4倍内存；③Read/Write Enabled：开启后CPU端额外存一份，计入NativeReserved，非必要一律关闭。此外，开启Mipmap会使纹理内存增至约1.33倍，需权衡带宽收益后决定。

**网格：** 关注顶点数和面片数是否超出实际表现需求，顶点属性（UV2、Color、Tangent等）在不必要时可剥离以减小数据量。网格同样存在Read/Write Enabled问题，开启后CPU端多存一份。

**动画：** 动画Clip本身占用内存，且播放时涉及骨骼Transform更新等CPU开销。关注Animation Clip数量与时长，适当压缩关键帧或降低采样率。大量Animator处于Active状态还会额外增加CPU负担。

**音频：** 小游戏中音频内存独立于UnityHeap，但也需关注。建议使用压缩格式（如MP3/Vorbis），并根据音频类型选择Loader（Decompress On Load会将完整数据常驻内存，Streaming则按需读取但CPU开销更高）。

**字体：** 使用TextMeshPro时，SDF Atlas以Alpha8格式存储，内存较低；但若使用动态字体（.ttf直接渲染），会产生较大内存占用。建议优先使用TMP静态字体方案。首包中使用的字体应尽可能精简字符集。

**粒子系统：** 粒子数量、发射器复杂度直接影响CPU端计算和内存分配，中低端机上应限制Max Particles并精简粒子层级。

以上资源内容可以在UWA GOT Online小游戏报告中进行详细排查，在Resource模式中可获取具体的资源列表。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/17.png)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/18.png)

> **注意：** 新上手小游戏平台的开发者常遇到纹理内存远超预期的现象 —— 明明做了纹理压缩，测试数据却显示很高。这通常是PC开发者工具中ASTC等压缩格式回退为RGBA32所致，纹理压缩格式务必以真机测试为准（详见1.5节关于PC工具与真机测试的原则说明）。

#### 4.3 iOS高性能与高性能+模式对比

iOS的高性能模式和高性能+模式中内存分布存在明显差异，UWA通过对比测试帮助读者形成更直观的认识。

**高性能模式：** 小游戏运行在独立进程com.apple.WebKit.WebContent中。几乎所有类型的内存都会进入WebContent进程（不会使WeChat进程内存上升），仅音频资源例外。真正导致闪退的进程是 **WebContent进程** 。内存分布大致如下：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/19.png)

**高性能+模式：** 官方描述为“开创性地在保留游戏独立进程的基础上将渲染重新挪回了微信进程”。测试结果显示，属于GPU的纹理、网格、RT不再进入WebContent进程，而是进入WeChat进程。但开启了Read/Write的纹理/网格在CPU端仍有一份内存位于NativeReserved中，属于WebContent进程。

再次验证，小游戏闪退只与 **WebContent进程** 有关，一般建议控制在 **1.3GB** 以内；WeChat进程即使大幅超过这个范围也不会闪退。内存分布如下：

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/20.png)

可见高性能+模式的内存占用相比高性能模式确有下降，若高性能模式下内存吃紧可考虑开启高性能+。但具体仍需自行评估客户端版本、是否存在新的画面或性能问题。

#### 4.4 内存检查清单

- UnityHeap初始值合理设置（参考：轻度256MB/中度496MB/重度768MB，避免<256MB或≥1024MB）
- 关注DynamicMemory走势，避免泄漏和频繁扩容引发的内存尖峰
- Mono堆避免单帧内大量分配
- 纹理避免开启Read/Write Enable（否则CPU端多存一份计入NativeReserved）
- 考虑使用WXAssetBundle代替原生AssetBundle接口，避免AB本体进入UnityHeap
- WASM代码包按约8~12倍体积数量级估算编译期内存，以真机为准，关注分包效果
- 纹理压缩格式以真机测试为准，勿依赖PC开发者工具数据
- 内存压力大的游戏考虑开启iOS高性能+模式

> ### 5\. CPU压力

受限于WASM虚拟机的执行效率以及常规C# 多线程/Job多线程能力受限，小游戏上CPU性能约为原生APP的1/3（实际比例因机型、Unity版本、iOS模式、瓶颈类型等因素而异），是小游戏平台上最易出现高压问题的维度。本章聚焦小游戏中独有或更容易放大的CPU瓶颈场景，通用排查思路可参考 [《Unity移动端游戏性能优化简谱》](https://edu.uwa4d.com/course-intro/0/430) 中的CPU相关章节。

#### 5.1 蒙皮动画

小游戏中较常见的CPU性能压力来自蒙皮动画（Skinned Mesh Renderer）。在原生APP上，蒙皮计算可在工作线程处理，对主线程影响较小；而在小游戏中常规多线程能力受限，MeshSkinning.Update的耗时直接影响主线程，不经处理可能成为瓶颈。下图为某款SLG项目在Mi 10上的运行数据，在小怪较少的战斗场景中也会有持续4ms的MeshSkinning.Update开销，相对偏高。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/21.png)

优化方向有两个：

- **GPU Skinning：** 将蒙皮计算从CPU移至GPU处理。团结引擎已内置该功能，也可使用第三方GPU Skinning方案。上述SLG场景中替换为GPU Skinning方案后，在小怪数量更多、更复杂的战斗场景开销也仅有1~2ms，且表现无明显差别。
- **控制蒙皮规模：** 进一步限制骨骼数量和顶点数量，适当牺牲表现精度以换取性能。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/22.png)

#### 5.2 逻辑代码

部分在APP上运行稳定的计算逻辑，直接移植到小游戏中效率可能明显偏低，需要适量精简。这一部分与项目业务逻辑强相关，难以给出统一方案，但可遵循以下排查与优化思路：

- 配合Profiler打点定位耗时的函数，优先处理耗时最高的热点
- 关注每帧都在执行的逻辑（Update/FixedUpdate），检查是否有不必要的重复计算
- WebGL中Lua不支持JIT，避免将Lua用于重度计算逻辑
- 回顾1.5节中关于PC工具与真机测试的原则：PC端CPU性能远超真机，务必以真机Profiler数据为准

#### 5.3 UI模块

UGUI是许多Unity项目中CPU开销的重要来源，在小游戏单线程环境下影响更为明显。主要关注以下几个高耗时函数：

**EventSystem.Update：** UGUI事件系统的每帧更新，耗时偏高时通常与两个因素有关 —— 一是输入回调中挂载了耗时过高的逻辑函数，可通过Profiler打点进一步定位；二是大量UI元素默认开启了Raycast Target选项，而实际上多数Image、Text并不需要响应点击事件，关闭该选项可直接降低事件遍历开销。

**Canvas.SendWillRenderCanvases：** Canvas的渲染重建入口，当UI元素的Transform、颜色、层级等发生变化时触发。该函数耗时与发生变化的UI元素数量成正比。优化方向包括：将动态UI和静态UI拆分到不同Canvas中，避免静态元素被频繁连带重建；减少不必要的Layout Group、Content Size Fitter等自动布局组件使用。

**Canvas.BuildBatch：** UI元素合批为Mesh的主要耗时点，通常紧随SendWillRenderCanvases之后。合并批次时若发生打断（如同一Canvas下使用了不同材质/图集），会显著增加重建耗时。规划好UI的图集和材质共用策略、保持合批连续性，可有效降低该开销。

**CanvasRenderer.SyncTransform：** 当UI元素的Transform发生变更时触发，频繁调用时会连带导致渲染更新开销增高。需注意某些动画或逻辑中对UI元素Transform的频繁修改。

**通用建议：** 动态/静态UI分离到不同Canvas、关闭不需要的Raycast Target、减少自动布局组件使用、谨慎使用UI Particle（会作为UI元素高频更新并重建Mesh）。

#### 5.4 实例化与销毁

在游戏运行过程中，频繁的Instantiate和Destroy操作在小游戏上开销明显，原因在于单线程环境下内存分配与对象初始化的耗时直接阻塞主线程。

**场景/模块切换：** 进入新场景或新界面时，建议采用分帧加载策略，避免在一帧内完成大量对象的Instantiate导致明显卡顿。可结合对象池（Object Pool）复用高频创建销毁的对象（如子弹、特效、UI列表项），减少频繁的内存分配与回收。

**Activate/Deactivate vs Instantiate/Destroy：** 对于需要频繁显隐的对象，使用SetActive的代价远低于Instantiate/Destroy，但大量同时处于Active状态的对象仍会增加Update等逻辑开销，需要在两者之间平衡。

**Resources.UnloadUnusedAssets：** 卸载未使用资源是一项耗时操作，建议在场景切换完成后的静默期执行，避免在游戏流程中频繁调用。

#### 5.5 CPU压力检查清单

- 关注SkinnedMeshRenderer数量和MeshSkinning.Update耗时
- 考虑使用GPU Skinning（团结引擎已支持）或第三方方案
- 控制蒙皮骨骼数和顶点数，适当牺牲精度换取性能
- 逻辑代码配合打点定位高耗时函数，针对性精简
- WebGL中避免用Lua处理重度逻辑（不支持JIT）
- UI：动态/静态分离到不同Canvas，关闭非必要的Raycast Target
- UI：减少自动布局组件使用，规划好图集合批策略
- 频繁创建销毁的对象使用对象池，场景切换采用分帧加载

> ### 6\. GPU压力

小游戏上GPU运行效率与APP接近，相对于CPU较不容易成为性能瓶颈，但GPU压力同样关系到帧率、发热与功耗。本章提炼 [《Unity移动端游戏性能优化简谱》](https://edu.uwa4d.com/course-intro/0/430) 中GPU章节的核心要点，并补充微信小游戏平台在iOS上经验证的几个GPU压力关键来源（HDR、RT使用、纹理精度等）。

> **注意：** 1.5节中关于PC开发者工具与真机测试的原则在GPU侧尤为重要 —— ASTC等压缩纹理格式在PC上可能回退为RGBA32，WebGL 2.0特性（GPU Instancing、SRP Batcher）在PC与真机上的表现也可能存在差异，GPU数据务必以真机实测为准。

#### 6.1 判断GPU压力

当整体帧耗时明显超出目标帧，但CPU侧各模块耗时之和与之存在较大差距时，通常倾向于判定存在GPU压力。在原生APP上可借助GPU Clocks或同步等待函数标记辅助判断，但小游戏环境下渲染线程模型存在差异，更建议结合实际表现综合评估 —— 例如CPU耗时已优化到位而帧率仍不达标、或降低渲染分辨率后帧率明显回升，均可作为GPU Bound的佐证。

#### 6.2 顶点阶段压力

顶点阶段压力取决于渲染面片数与顶点着色器复杂度。GPU Primitive参数中，若剔除图元占比高达70-80%，说明存在大量浪费，需排查模型制作是否合理、大模型是否未拆小导致整体提交GPU、网格是否过于精细而屏占比有限等。

优化方法包括：LOD分级控制远距离面片数、精简复杂模型、CPU端提前剔除不可见物体、在中低端机上关闭多光源/阴影/多Pass等使面片数翻倍的特性。

#### 6.3 片元阶段压力

片元阶段的计算量取决于每帧绘制的像素数，由渲染分辨率和Overdraw共同决定。

**渲染分辨率：** 分级控制分辨率是最实用的GPU优化手段。低端机降至0.7-0.8倍，像素数可减半，3D场景通常可接受轻微模糊。需注意实际渲染分辨率与设备DPR（Device Pixel Ratio）相关 —— 高DPR屏幕即使设置较低倍率仍可能产生高像素负担，建议按像素总数而非固定比例制定分档标准。URP项目中可利用Camera Stack将3D场景渲染到低分辨率RT中，避免UI同时变模糊。

**Overdraw：** 指像素被重复绘制的次数。不透明物体应通过Render Queue调整渲染顺序来控制；粒子系统和UI是半透明Overdraw的主要来源 —— 中低端机精简粒子层级、限制Max Particles、裁剪纯透明贴图面积、考虑动画帧烘焙替代；UI侧注意全屏遮挡时关闭底层、Mask替换为RectMask2D等。此外，后处理、Blit、Copy等操作同样会产生全屏级别的Overdraw。特别地，开启HDR会引入额外的全分辨率RT拷贝操作以及额外的显存开销，在小游戏环境下对GPU压力影响显著，建议谨慎评估是否必要。

#### 6.4 着色器与后处理

**着色器：** 优先关注屏占比较高、Shader相对复杂的渲染对象（地表、建筑、特效），而非屏占比低的角色。项目中“万能Shader”常导致GPU对大量未使用特性进行全额计算，应通过关键字开关或拆分Shader优化。

**后处理：** 是GPU压力的常见来源 —— Bloom中低端机可从1/4分辨率开始下采样；SMAA开销较高不建议在中低端使用；DOF移动端开销大需谨慎；尽量使用Local Volume按需开启而非全局常驻。

#### 6.5 GPU带宽

GPU带宽主要影响能耗发热而非帧率。Mali官方数据显示约1GB/s带宽造成80-100mW功率开销，在游戏总功率中占比可观。在小游戏中，渲染产生的GPU带宽开销在DRAM带宽中占绝大部分，主要来自：频繁的RT使用与切换、高精度纹理资源的采样、以及HDR或后处理引入的额外RT拷贝。

优化手段包括：尽量复用RT减少切换、使用合理压缩格式降低单像素传输量、3D场景务必开启Mipmap（改善效果远超纹理压缩）、避免全局强制各向异性过滤、减少不必要的Copy和后处理采样。

#### 6.6 GPU压力检查清单

- 关注渲染面片数，排查剔除图元占比过高的场景
- 按像素总数分档控制渲染分辨率，中低端机可降至0.7-0.8倍
- 排查Overdraw（粒子系统、UI、后处理），定位热点资源
- 关注屏占比高且Shader复杂的渲染对象，拆分“万能Shader”
- 后处理效果分级取舍，中低端机关闭开销较高的效果
- 关注GPU带宽 —— 纹理压缩、Mipmap、减少不必要的Copy和采样
- GPU数据（纹理格式、WebGL 2.0特性等）务必以真机测试为准

> ### 7\. 功耗优化

小游戏的功耗优化整体上可参考移动端的优化思路与经验，且由于移动设备散热条件有限，功耗问题在小游戏上同样不容忽视。功耗不仅关乎设备续航，更与发热直接挂钩 —— 当设备温度超过系统温控阈值后，会触发CPU/GPU降频，导致帧率骤降，形成“高功耗→发热→降频→卡顿”的恶性循环。因此功耗优化本质上也是性能稳定性优化，核心手段与CPU、GPU章节的优化思路一脉相承。

#### 7.1 帧率对功耗的影响

首先要明确一个基本规律：在其它条件不变的情况下，帧率与功耗近似成正比，60FPS的功耗约为30FPS的两倍。这意味着高端机型上若不加限制地跑满帧率，反而可能因为功耗过高导致发热更严重。建议根据项目类型制定合理的目标帧率（如休闲游戏30FPS，中度游戏30~60FPS），也可对不同场景动态调整 —— 例如主界面、挂机场景降低帧率，核心战斗场景再恢复到目标帧率，从而有效控制整局功耗。

#### 7.2 功耗的来源

小游戏运行时的功耗主要来自以下几个方面：

- CPU：逻辑计算、蒙皮、动画、物理、脚本等，是小游戏功耗最主要的来源。
- GPU：顶点处理、片元着色、纹理采样、带宽传输等。
- 屏幕显示：屏幕亮度与分辨率直接关联功耗，但开发者通常无法直接控制。
- 网络传输：持续的网络请求与数据收发也会产生额外功耗。

对于开发者而言，能够直接着手优化的主要是CPU与GPU两部分。

**7.2.1 CPU侧功耗优化**  
在原生APP上，通常需要分别排查CPU主线程与子线程中的压力来源。但小游戏环境下常规多线程能力受限，因此重点关注CPU主线程上各模块的耗时即可。排查思路与本文「CPU压力」章节一致：通过Profiler定位高耗时模块（渲染、UI、物理、动画、逻辑脚本等），找到项目中压力较大的模块并予以针对性优化。由于功耗与CPU占用正相关，降低主线程耗时本身就是在降低功耗。

**7.2.2 GPU侧功耗优化**  
GPU侧功耗主要从GPU计算压力与GPU带宽两个维度进行排查，与本文「GPU压力」章节的思路一致：控制同屏面片数、合理设置渲染分辨率、减少Overdraw、精简Shader复杂度，同时关注纹理采样次数与带宽占用。降低GPU负载同样直接降低功耗。

#### 7.3 功耗优化检查清单

- 根据项目类型制定合理的目标帧率，避免高端机无限制跑满
- 对不同场景动态调整帧率（主界面/挂机降帧，核心玩法恢复目标帧率）
- 通过CPU主线程Profiler定位高耗时模块并针对性优化
- 从GPU计算压力与GPU带宽两个维度排查GPU侧功耗
- 将高温环境（户外、充电时游玩）纳入测试覆盖范围
- iOS高性能模式下尤其关注启动阶段的发热，避免长时间连续高负载

> ### 8\. APP转小游戏经验分享：同步转异步功耗优化

本章分享一个实际项目中将APP迁移到小游戏时遇到的典型问题 —— AssetBundle同步加载的兼容性改造，以及我们在实战中摸索出的一套低成本解决方案。

#### 8.1 问题背景

在原生APP项目中，同步加载与异步加载在实际运行时的体验差异通常不大，开发团队在早期也不一定会严格区分两者的使用场景。但在小游戏环境中，AssetBundle文件本身不支持同步加载（从已加载的AssetBundle中加载具体资源仍可使用同步接口），这意味着原本在APP中大量使用的同步加载逻辑都需要逐一改造。如果项目在原生APP阶段没有提前做好这方面的规范和管理，后续转换时的工作量会相当可观。

#### 8.2 快速定位方法

在Unity编辑器中将小游戏工具面板的Play Mode切换为Web Play Mode，此时在Editor中运行游戏，一旦触发AssetBundle的同步加载就会直接抛出WebGL platform not support sync load method这类报错，帮助快速发现哪些加载链路存在问题。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/23.png)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/24.png)

进一步地，还可以在同步加载接口的报错位置额外增加一条报空日志，显式输出对应资源的路径信息，这样每次报错时就能直接看到是哪个AB文件在哪个时机被同步加载了，排查效率大幅提升，不必逐个翻看代码调用链。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/25.png)

#### 8.3 集中预加载方案

从已加载的AssetBundle中加载具体资源仍然可以使用同步接口。基于这一点，核心思路就清晰了：只要在使用同步接口加载资源之前，确保对应的AssetBundle已经通过异步方式加载到内存中且未被卸载，那么原来的同步资源加载逻辑就完全可以保持不变。

按照这个思路，我们的做法是在游戏流程中找到一个统一的、早于所有实际资源加载的时机点，把所有会被同步加载使用的AssetBundle提前用异步接口统一加载一遍。只要保证后续真正使用同步接口加载资源时这些AB仍在内存中且未被卸载，整个项目中原有的同步加载逻辑就不需要逐一修改，也不会在小游戏环境中触发报错。

例如原先在Initialize阶段使用了同步加载会导致报错，我们找到了一个更早的时机点，通过PreloadAsync先用异步接口集中加载了timeConfig在内的多个后续会用同步加载的资源，那么后续的逻辑无需修改也不会报错了。

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/26.png)

![](http://uwa-ducument-img.oss-cn-beijing.aliyuncs.com/Blog/UWA_MiniGame/27.png)

这种方式本质上是将“同步改异步”的改造工作从散落在各处的资源加载点集中收拢到了一个统一的预加载节点，既降低了修改工作量，也避免了逐处改造时容易遗漏或引入新问题的风险。

> ### 9\. 结束语

这篇文章之所以称为简谱，实在是因为这些笔墨远不能达到面面俱到，很多内容还未涉及到，或者限于篇幅和重点不能深入讨论。它更多的是立足于如何以用好一套完善完整的性能工具为基础，构建发现问题-解决问题-监控问题的优化思维和优化体系，使得性能优化的工作事半功倍。更多的优秀内容，欢迎在UWA社区中进行搜索。

本文内容就介绍到这里啦，更多内容可以前往 [UWA学堂](https://edu.uwa4d.com/course-intro/0/645) 进行阅读。