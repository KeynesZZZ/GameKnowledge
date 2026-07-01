---
title: 【教程】DOTS专题索引
tags: ["Unity", "DOTS", "ECS", "JobSystem", "Burst", "专题索引", "教程"]
category: DOTS技术栈/专题索引
created: "2026-03-05 20:05"
updated: "2026-06-30"
description: DOTS 专题的自动生成索引，汇总 ECS、Job System、Burst、迁移实践与 Entities 1.4 量产栈综述。
status: 待验证
validation: Demo验证
related: ["[[【教程】DOTS学习路径]]", "[[../00_元数据与模板/学习路径导航]]", "[[../00_元数据与模板/文档结构规范]]"]
author: llm
---

# DOTS专题索引

> DOTS 专题的自动生成索引，汇总 ECS、Job System、Burst 和迁移实践。

## 文档定位

自动生成的DOTS技术栈专题索引，汇总了ECS、Job System、Burst等18篇文档的导航入口和推荐阅读顺序，便于快速定位相关教程。

## 专题概览

- 收录文档数：20
- 覆盖目录数：2
- 文档类型分布：设计原理1篇，教程5篇，综述1篇，笔记8篇，片段4篇，实战案例1篇

## 推荐阅读顺序

1. [【设计原理】ECS为什么快](./【设计原理】ECS为什么快.md) - 理解数据导向设计的性能原理，深入分析ECS架构的性能优势来源：内存布局、缓存命中、SIMD优化。
2. [【教程】ECS 入门与迁移指南](../10_架构设计/【教程】ECS入门与迁移指南.md) - Unity DOTS 技术栈中 ECS 架构的入门指南，包含从 OOP 到 ECS 的迁移策略和最佳实践。
3. [【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档](./【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档.md) - 综合 Unity 官方手册，补全 Baking 烘焙管线、SubScene/内容管理、ECS 渲染与现代 1.4 编程模型（含 IAspect 废弃、TransformUsageFlags、MaterialMeshInfo）。
4. [【笔记】ECS 与 GameObject 通信](./【笔记】ECS与GameObject通信.md) - 混合开发中的六种通信模式：EntityManager 直操作、托管 Singleton、事件队列、Companion Components 与分层策略。
5. [【笔记】同屏大规模单位渲染方案](./【笔记】同屏大规模单位渲染方案.md) - 同屏 10w+ 单位渲染的 DOTS 落地方案：合批、Burst 并行更新、LOD/剔除、避坑与 GPU-driven 进阶。
6. [【笔记】大规模单位动画方案](./【笔记】大规模单位动画方案.md) - 10w 单位 × 多类型 × 多动画的落地方案：GPU 顶点动画(VAT) + ECS 状态机，附方案选型与 12 怪数据组织。
7. [【片段】VAT 顶点动画烘焙脚本](./【片段】VAT顶点动画烘焙脚本.md) - 可复用的 VAT 烘焙 Editor 脚本骨架：逐帧 BakeMesh 采样写 RGBAFloat 纹理 + LUT，配套 shader 采样端。
8. [【实战案例】10w 单位渲染与动画最小 Demo](./【实战案例】10w单位渲染与动画最小Demo.md) - 把渲染、VAT 动画、ECS 状态机串成可跑的最小工程骨架：工程结构、关键系统、Profiler 验证清单与已知坑。
9. [【笔记】大规模单位 AI 决策与寻路](./【笔记】大规模单位AI决策与寻路.md) - 10w 单位 AI/寻路：Flow Field 流场（同目标 O(1) 查询）、空间分区、局部避障、分帧决策。
10. [【片段】Flow Field 流场 Job 实现](./【片段】FlowField流场Job实现.md) - Flow Field 三场（Cost/Integration/Vector）完整 Burst Job：wavefront Dijkstra + 8 邻域梯度，含对角线代价与桶式扩展。
11. [【笔记】RVO 避障算法原理](./【笔记】RVO避障算法原理.md) - 从 VO 速度障碍到 RVO 互惠避让再到 ORCA 半平面——完整推演大规模局部避障的数学原理、几何构造与线性规划求解。
12. [【片段】RVO2 局部避障 ECS 移植](./【片段】RVO2局部避障ECS移植.md) - RVO2/ORCA 完整 Burst 移植：computeORCALines、linearProgram1/2/3 数学、UniformGrid 邻域查询与参数调优。
13. [【笔记】大规模单位战斗结算](./【笔记】大规模单位战斗结算.md) - 碰撞（Unity.Physics ITriggerEventsJob/UniformGrid）+ 伤害事件化（DynamicBuffer+ECB）+ 死亡 IEnableableComponent 回收 + AOE。
14. [【笔记】大规模技能特效方案](./【笔记】大规模技能特效方案.md) - VFX Graph GPU 事件驱动、ECS 事件桥接、分层 LOD 策略、刀光拖尾与 AOE 特效。
15. [【片段】UniformGrid 空间分区 Job 实现](./【片段】UniformGrid空间分区Job实现.md) - 10w 单位「最近敌人」查询：NativeMultiHashMap 并行构建、3×3 邻域扫描、多阵营、分帧优化（12500x 加速）。

## 按文档类型

### 综述

- [【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档](./【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档.md) - `DOTS技术栈` - 综合 Unity 官方手册，补全 Baking 烘焙管线、SubScene/内容管理、ECS 渲染与现代 1.4 编程模型。

### 笔记

- [【笔记】ECS 与 GameObject 通信](./【笔记】ECS与GameObject通信.md) - `DOTS技术栈` - 混合开发中的六种通信模式：EntityManager 直操作、托管 Singleton、事件队列、Companion Components 与分层策略。
- [【笔记】同屏大规模单位渲染方案](./【笔记】同屏大规模单位渲染方案.md) - `DOTS技术栈` - 同屏 10w+ 单位渲染的 DOTS 落地方案：合批、Burst 并行更新、LOD/剔除、避坑与 GPU-driven 进阶。
- [【笔记】大规模单位动画方案](./【笔记】大规模单位动画方案.md) - `DOTS技术栈` - 10w 单位 × 多类型 × 多动画的落地方案：GPU 顶点动画(VAT) + ECS 状态机，附方案选型与 12 怪数据组织。
- [【笔记】大规模单位 AI 决策与寻路](./【笔记】大规模单位AI决策与寻路.md) - `DOTS技术栈` - 10w 单位 AI/寻路：Flow Field 流场（同目标 O(1) 查询）、空间分区、局部避障、分帧决策。
- [【笔记】大规模单位战斗结算](./【笔记】大规模单位战斗结算.md) - `DOTS技术栈` - 碰撞（Unity.Physics/UniformGrid）+ 伤害事件化（DynamicBuffer+ECB）+ 死亡回收 + AOE。
- [【笔记】Burst SIMD 原理详解](./【笔记】Burst SIMD原理详解.md) - `DOTS技术栈` - 从 CPU 向量寄存器、LLVM 编译流水线到内存布局，深入理解 Burst SIMD 自动向量化的底层原理与实战要点。
- [【笔记】大规模技能特效方案](./【笔记】大规模技能特效方案.md) - `DOTS技术栈` - VFX Graph GPU 事件驱动、ECS 事件桥接、分层 LOD 策略、刀光拖尾与 AOE 特效。
- [【笔记】RVO 避障算法原理](./【笔记】RVO避障算法原理.md) - `DOTS技术栈` - 从 VO 速度障碍到 RVO 互惠避让再到 ORCA 半平面——完整推演局部避障的数学原理、几何构造与线性规划求解。

### 片段

- [【片段】VAT 顶点动画烘焙脚本](./【片段】VAT顶点动画烘焙脚本.md) - `DOTS技术栈` - 可复用 VAT 烘焙 Editor 脚本骨架：逐帧 BakeMesh 写 RGBAFloat 纹理 + LUT，配套 shader 采样端。
- [【片段】Flow Field 流场 Job 实现](./【片段】FlowField流场Job实现.md) - `DOTS技术栈` - Flow Field 三场完整 Burst Job：wavefront Dijkstra + 8 邻域梯度，含桶式扩展。
- [【片段】RVO2 局部避障 ECS 移植](./【片段】RVO2局部避障ECS移植.md) - `DOTS技术栈` - RVO2/ORCA 完整 Burst 移植：computeORCALines + linearProgram1/2/3 + 参数调优。
- [【片段】UniformGrid 空间分区 Job 实现](./【片段】UniformGrid空间分区Job实现.md) - `DOTS技术栈` - 10w 单位「最近敌人」查询：NativeMultiHashMap 并行构建、3×3 邻域扫描、多阵营、分帧优化。

### 实战案例

- [【实战案例】10w 单位渲染与动画最小 Demo](./【实战案例】10w单位渲染与动画最小Demo.md) - `DOTS技术栈` - 把渲染、VAT 动画、ECS 状态机串成可跑的最小工程骨架：工程结构、关键系统、Profiler 验证清单与已知坑。

### 设计原理

- [【设计原理】ECS为什么快](./【设计原理】ECS为什么快.md) - `DOTS技术栈` - 理解数据导向设计的性能原理，深入分析ECS架构的性能优势来源：内存布局、缓存命中、SIMD优化。

### 教程

- [【教程】ECS 入门与迁移指南](../10_架构设计/【教程】ECS入门与迁移指南.md) - `架构设计/教程` - Unity DOTS 技术栈中 ECS 架构的入门指南，包含从 OOP 到 ECS 的迁移策略和最佳实践。
- [【教程】ECS架构入门](./【教程】ECS架构入门.md) - `DOTS技术栈` - Unity ECS架构入门教程。
- [【教程】JobSystem详解](./【教程】JobSystem详解.md) - `DOTS技术栈` - Unity JobSystem详解教程。
- [【教程】Burst编译器](./【教程】Burst编译器.md) - `DOTS技术栈` - Unity Burst编译器优化教程。
- [【教程】DOTS学习路径](./【教程】DOTS学习路径.md) - `DOTS技术栈` - Unity DOTS技术栈学习路径。

## 按目录

### 10_架构设计

- [【教程】ECS 入门与迁移指南](../10_架构设计/【教程】ECS入门与迁移指南.md)

### 25_DOTS技术栈

- [【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档](./【综述】Entities 1.4 与 Entities Graphics 1.4 官方文档.md)
- [【设计原理】ECS为什么快](./【设计原理】ECS为什么快.md)
- [【笔记】ECS与GameObject通信](./【笔记】ECS与GameObject通信.md)
- [【笔记】同屏大规模单位渲染方案](./【笔记】同屏大规模单位渲染方案.md)
- [【笔记】大规模单位动画方案](./【笔记】大规模单位动画方案.md)
- [【笔记】大规模单位 AI 决策与寻路](./【笔记】大规模单位AI决策与寻路.md)
- [【笔记】大规模单位战斗结算](./【笔记】大规模单位战斗结算.md)
- [【笔记】Burst SIMD 原理详解](./【笔记】Burst SIMD原理详解.md)
- [【笔记】大规模技能特效方案](./【笔记】大规模技能特效方案.md)
- [【笔记】RVO避障算法原理](./【笔记】RVO避障算法原理.md)
- [【片段】VAT 顶点动画烘焙脚本](./【片段】VAT顶点动画烘焙脚本.md)
- [【片段】Flow Field 流场 Job 实现](./【片段】FlowField流场Job实现.md)
- [【片段】RVO2 局部避障 ECS 移植](./【片段】RVO2局部避障ECS移植.md)
- [【片段】UniformGrid 空间分区 Job 实现](./【片段】UniformGrid空间分区Job实现.md)
- [【实战案例】10w 单位渲染与动画最小 Demo](./【实战案例】10w单位渲染与动画最小Demo.md)
- [【教程】ECS架构入门](./【教程】ECS架构入门.md)
- [【教程】JobSystem详解](./【教程】JobSystem详解.md)
- [【教程】Burst编译器](./【教程】Burst编译器.md)
- [【教程】DOTS学习路径](./【教程】DOTS学习路径.md)

## 相关链接

- [[【教程】DOTS学习路径]]
- [[../00_元数据与模板/学习路径导航]]
- [[../00_元数据与模板/文档结构规范]]
