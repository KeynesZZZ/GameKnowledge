---
title: 【教程】AI行为树实现
tags: [Unity, AI, AI导航系统, 行为树, 教程]
category: 核心系统/AI导航系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: AI行为树系统实现教程
unity_version: 2021.3+
---
# AI 行为树实现

> Unity 行为树（Behavior Tree）系统完整实现指南 `#AI与导航系统` `#行为树` `#AI`

## 文档定位

本文档从**使用角度**讲解AI行为树实现。

**相关文档**：

---

## 概述

行为树是一种用于 AI 决策的分层结构，比状态机更灵活、更易于扩展。Unity 提供了 Behavior Tree System 插件。

## 行为树基础

### 节点类型

| 类型 | 描述 | 使用场景 |
|------|------|----------|
| **Composite** | 组合子节点 | 控制子节点执行流程 |
| **Decorator** | 装饰子节点 | 修改子节点结果 |
| **Leaf** | 叶子节点 | 实际行为（移动、攻击等） |

### Composite 节点

```csharp
// Sequence（顺序执行）
public class SequenceNode : Node
{
    public Node[] children;

    public override Status OnUpdate()
    {
        foreach (Node child in children)
        {
            if (child.OnUpdate() != Status.Success)
            {
                return child.Status;
            }
        }
        return Status.Success;
    }
}

// Selector（选择第一个成功的）
public class SelectorNode : Node
{
    public Node[] children;

    public override Status OnUpdate()
    {
        foreach (Node child in children)
        {
            Status status = child.OnUpdate();
            if (status != Status.Failure)
            {
                return status;
            }
        }
        return Status.Failure;
    }
}
```

---

## Unity 行为树节点

### 1. 条件节点

```csharp
using UnityEngine;
using UnityEngine.AI;

public class Condition : BehaviorTreeNode
{
    [Header("Condition")]
    public string key;
    public CompareMethod compare;
    public float value;

    public override Status OnUpdate()
    {
        float currentValue = Blackboard.GetFloat(key);
        bool result = Compare(currentValue, compare, value);
        
        return result ? Status.Success : Status.Failure;
    }

    bool Compare(float a, CompareMethod method, float b)
    {
        switch (method)
        {
            case CompareMethod.Equal: return Mathf.Abs(a - b) < 0.001f;
            case CompareMethod.Greater: return a > b;
            case CompareMethod.Less: return a < b;
            default: return false;
        }
    }
}

public enum CompareMethod
{
    Equal, Greater, Less, GreaterOrEqual, LessOrEqual
}
```

### 2. 动作节点

```csharp
using UnityEngine;
using UnityEngine.AI;

public class MoveToTarget : BehaviorTreeNode
{
    [Header("Target")]
    public string targetKey = "Target";

    private NavMeshAgent agent;

    void Start()
    {
        agent = GetComponent<NavMeshAgent>();
    }

    public override Status OnUpdate()
    {
        Vector3 target = Blackboard.GetVector3(targetKey);
        
        if (!agent.SetDestination(target))
        {
            return Status.Failure;
        }

        if (agent.remainingDistance < 0.5f)
        {
            return Status.Success;
        }

        return Status.Running;
    }
}
```

### 3. 装饰器节点

```csharp
// Repeater（重复执行）
public class Repeater : DecoratorNode
{
    public Node child;
    public int repeatCount;

    private int currentCount;

    public override Status OnUpdate()
    {
        Status status = child.OnUpdate();
        currentCount++;

        if (currentCount >= repeatCount || status == Status.Failure)
        {
            currentCount = 0;
            return status;
        }

        return Status.Running;
    }
}

// Inverter（反转结果）
public class Inverter : DecoratorNode
{
    public Node child;

    public override Status OnUpdate()
    {
        Status status = child.OnUpdate();
        
        if (status == Status.Success)
        {
            return Status.Failure;
        }
        else if (status == Status.Failure)
        {
            return Status.Success;
        }
        
        return status;
    }
}
```

---

## 黑板（Blackboard）

```csharp
using UnityEngine;
using System.Collections.Generic;

public class Blackboard : MonoBehaviour
{
    public static Blackboard Instance { get; private set; }
    
    private Dictionary<string, object> data = new Dictionary<string, object>();

    void Awake()
    {
        Instance = this;
    }

    // Set/Get 方法
    public void SetFloat(string key, float value) => data[key] = value;
    public void SetVector3(string key, Vector3 value) => data[key] = value;
    public void SetBool(string key, bool value) => data[key] = value;
    
    public float GetFloat(string key) => data.ContainsKey(key) ? (float)data[key] : 0f;
    public Vector3 GetVector3(string key) => data.ContainsKey(key) ? (Vector3)data[key] : Vector3.zero;
    public bool GetBool(string key) => data.ContainsKey(key) && (bool)data[key];
}
```

---

## 实战示例

### 1. 追逐行为树

```
Root
├── Sequence
│   ├── Selector
│   │   ├── Condition (IsPlayerVisible)
│   │   │   ├── Chase
│   │   │   └── Patrol
│   └── Attack
```

### 2. 资源收集行为树

```
Root
├── Selector
│   ├── Sequence (收集食物)
│   │   ├── Condition (HasFood)
│   │   ├── MoveToFood
│   │   └── Collect
│   ├── Sequence (收集水)
│   │   ├── Condition (HasWater)
│   │   ├── MoveToWater
│   │   └── Drink
│   └── Idle
```

---

## 性能优化

### 1. 行为树缓存

```csharp
public class BehaviorTreeCache : MonoBehaviour
{
    public BehaviorTree tree;
    private Status cachedStatus;

    void Update()
    {
        if (tree.status != cachedStatus)
        {
            tree.Update();
            cachedStatus = tree.status;
        }
    }
}
```

### 2. 条件缓存

```csharp
public class CachedCondition : Condition
{
    private float lastValue;
    private bool lastResult;
    private float cacheDuration = 0.5f;
    private float lastCheckTime;

    public override Status OnUpdate()
    {
        float currentTime = Time.time;
        
        if (currentTime - lastCheckTime < cacheDuration)
        {
            return lastResult ? Status.Success : Status.Failure;
        }

        float currentValue = Blackboard.GetFloat(key);
        lastResult = Compare(currentValue, compare, value);
        lastCheckTime = currentTime;
        
        return lastResult ? Status.Success : Status.Failure;
    }
}
```

---

## 最佳实践

### DO ✅

- 使用行为树处理复杂 AI 决策
- 使用黑板共享数据
- 使用 Decorator 控制节点执行
- 避免深层嵌套（性能问题）
- 合理设计节点复用

### DON'T ❌

- 不要创建过多的条件节点
- 不要忽视行为树的调试难度
- 不要忘记重置状态
- 不要混淆行为树和状态机
- 不要在 Update 中频繁重建行为树

---

## 常见问题

### Q: 行为树 vs 状态机？

**A**: 
- 行为树：更适合复杂决策，更灵活
- 状态机：更适合状态转换，更直观

**推荐**: 两者结合使用

### Q: 如何调试行为树？

**A**: 
1. 使用行为树调试器
2. 添加日志输出
3. 可视化节点状态
4. 逐步测试每个节点

### Q: 行为树性能差？

**A**: 
1. 减少条件检查
2. 使用缓存
3. 避免深层嵌套
4. 合理设计节点

---

## 相关链接

- [状态机 AI 设计](./状态机AI设计.md)
- [NavMesh 基础配置](./【教程】NavMesh基础配置.md)
- [寻路算法对比](./寻路算法对比.md)

---

**适用版本**: Unity 2020.1+
**最后更新**: 2026-03-04
