---
title: 【教程】NavMesh基础配置
tags: [Unity, AI导航系统, NavMesh, 教程]
category: 核心系统/AI导航系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: NavMesh导航系统基础配置教程
unity_version: 2021.3+
---
# NavMesh 基础配置

> Unity NavMesh 导航系统完整配置指南 `#AI与导航系统` `#NavMesh` `#寻路`

## 概述

NavMesh（Navigation Mesh）是 Unity 的内置寻路系统，允许 AI 角色在复杂环境中自动寻路。正确配置 NavMesh 对 AI 行为至关重要。

## NavMesh 基础

### 1. 创建 NavMesh

```
Window > AI > Navigation
```

### 2. 烘焙（Baking）NavMesh

```csharp
using UnityEngine;
using UnityEngine.AI;

public class NavMeshBaker : MonoBehaviour
{
    public NavMeshSurface surface;

    void Start()
    {
        // 自动烘焙
        surface.BuildNavMesh();
    }

    void Update()
    {
        // 动态更新（用于移动平台）
        surface.UpdateNavMesh(surface.navMeshData);
    }
}
```

---

## NavMeshAgent 配置

### 1. 基础参数

```csharp
using UnityEngine;
using UnityEngine.AI;

public class NavAgentSetup : MonoBehaviour
{
    public NavMeshAgent agent;
    public float speed = 3.5f;

    void Start()
    {
        // 配置 Agent
        agent.speed = speed;
        agent.angularSpeed = 120f;
        agent.acceleration = 8f;
        agent.stoppingDistance = 0.5f;
        agent.autoBraking = true;
    }
}
```

### 2. Agent 类型

| 类型 | 自动寻路 | 碰撞避让 | 使用场景 |
|------|---------|---------|----------|
| **Humanoid** | ✅ | ✅ | 角色 |
| **Car** | ✅ | ✅ | 车辆 |

---

## 实战示例

### 1. 基础寻路

```csharp
using UnityEngine;
using UnityEngine.AI;

public class BasicPathfinding : MonoBehaviour
{
    public NavMeshAgent agent;
    public Transform target;

    void Start()
    {
        agent = GetComponent<NavMeshAgent>();
    }

    void Update()
    {
        // 设置目标
        agent.SetDestination(target.position);
    }
}
```

### 2. 状态机寻路

```csharp
public class FSMPathfinding : MonoBehaviour
{
    public enum AIState { Idle, Chasing, Patroling }
    
    public NavMeshAgent agent;
    public Transform player;
    public Transform[] patrolPoints;
    
    private AIState currentState;

    void Start()
    {
        currentState = AIState.Patrolling;
        agent = GetComponent<NavMeshAgent>();
    }

    void Update()
    {
        switch (currentState)
        {
            case AIState.Idle:
                IdleBehavior();
                break;
            case AIState.Chasing:
                ChaseBehavior();
                break;
            case AIState.Patrolling:
                PatrolBehavior();
                break;
        }
    }

    void ChaseBehavior()
    {
        // 追逐玩家
        if (Vector3.Distance(transform.position, player.position) < 20f)
        {
            currentState = AIState.Chasing;
            agent.SetDestination(player.position);
        }
    }
}
```

---

## 性能优化

### 1. 减少寻路频率

```csharp
public class OptimizedPathfinding : MonoBehaviour
{
    public NavMeshAgent agent;
    public float updateInterval = 0.5f;
    
    private float nextUpdateTime;

    void Update()
    {
        if (Time.time >= nextUpdateTime)
        {
            UpdatePath();
            nextUpdateTime = Time.time + updateInterval;
        }
    }

    void UpdatePath()
    {
        agent.SetDestination(target.position);
    }
}
```

---

## 最佳实践

### DO ✅

- 为 AI 使用 NavMeshAgent
- 合理设置 Agent 参数
- 使用状态机管理 AI 行为
- 减少寻路频率优化性能
- 使用 Off-Mesh Links 连接分离区域

### DON'T ❌

- 不要每帧更新寻路目标
- 不要忽略 Agent 的 stoppingDistance
- 不要使用过大的 Agent 数量
- 不要忘记烘焙 NavMesh
- 不要混淆不同类型的 Agent

---

## 常见问题

### Q: AI 不移动？
**A**: 
1. 检查 NavMesh 是否正确烘焙
2. 检查 Agent 是否正确配置
3. 检查目标是否在 NavMesh 上
4. 检查是否启用了避让

### Q: 寻路性能差？
**A**: 
1. 减少 Agent 数量
2. 减少寻路频率
3. 使用简化的 NavMesh
4. 使用层级分离不同类型的 AI

---

## 相关链接

- [AI行为树实现](./AI行为树实现.md)
- [状态机AI设计](./状态机AI设计.md)
- [寻路算法对比](./寻路算法对比.md)

---

**适用版本**: Unity 2019.4+
**最后更新**: 2026-03-04
