# DOTS 技术栈学习路径

> 目标：掌握 Unity 的数据导向技术栈，实现高性能游戏逻辑

## 什么是 DOTS？

**Data-Oriented Technology Stack** - Unity 的高性能技术栈：

```
DOTS = ECS + Job System + Burst Compiler
```

---

## 前置知识

- C# 基础
- Unity 基础
- 数据结构基础

---

## 学习路线

```
Week 1-2: Job System
    ├── IJob 接口
    ├── IJobParallelFor
    ├── JobHandle 与依赖
    └── NativeContainer

Week 3-4: Burst Compiler
    ├── Burst 属性标注
    ├── Burst 编译原理
    ├── SIMD 优化
    └── Burst 调试

Week 5-8: ECS 架构
    ├── Entity/Component/System
    ├── Archetype 与 Chunk
    ├── SystemGroup 与更新顺序
    └── 查询与遍历

Week 9-10: 实战项目
    ├── DOTS 版三消算法
    └── DOTS 版战斗系统
```

---

## 核心概念

### 1. Job System

| 概念 | 说明 |
|------|------|
| IJob | 单线程任务 |
| IJobParallelFor | 并行任务 |
| NativeArray | 非托管数组 |
| NativeList | 非托管列表 |
| NativeHashMap | 非托管字典 |
| JobHandle | 任务句柄与依赖 |

### 2. Burst Compiler

```csharp
[BurstCompile]
struct MyJob : IJob
{
    public NativeArray<float> input;
    public NativeArray<float> output;

    public void Execute()
    {
        // Burst 编译为高效原生代码
    }
}
```

### 3. ECS 架构

| 概念 | 说明 |
|------|------|
| Entity | 实体（仅 ID） |
| Component | 纯数据组件 |
| System | 行为逻辑 |
| World | 实体世界 |
| EntityManager | 实体管理器 |
| EntityQuery | 实体查询 |

---

## 性能对比

| 场景 | OOP | DOTS |
|------|-----|------|
| 10000 实体更新 | ~5ms | ~0.5ms |
| 碰撞检测 | ~10ms | ~1ms |
| 路径寻路 | ~20ms | ~2ms |

---

## 注意事项

⚠️ **DOTS 仍在快速迭代中**
- API 可能变化
- 部分功能实验性
- 学习曲线陡峭

---

## 推荐资源

- Unity DOTS 官方文档
- Unity DOTS 示例项目
- Catlike Coding - DOTS 教程
