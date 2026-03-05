---
title: 【源码解析】IK系统实现
tags: [Unity, 动画系统, IK, 源码解析]
category: 核心系统/动画系统
created: 2026-03-05 08:30
updated: 2026-03-05 08:30
description: Unity反向动力学系统实现原理
unity_version: 2021.3+
---
# IK 系统实现

> Unity IK（反向运动学）系统完整实现指南 `#动画系统` `#IK` `#反向运动学`

## 概述

IK（Inverse Kinematics，反向运动学）允许通过指定目标位置来控制肢体末端，与 FK（Forward Kinematics，正向运动学）相反。IK 广泛应用于角色手部、脚部位置控制。

## FK vs IK 对比

### 正向运动学（FK）

```csharp
// 从根关节驱动到末端
public void RotateJoint(float angle)
{
    // 旋转肩关节
    shoulderJoint.rotation = Quaternion.Euler(angle, 0, 0);
    // 肘关节自然跟随
}
```

### 反向运动学（IK）

```csharp
// 从末端反推到根关节
public void MoveHandToTarget(Vector3 targetPosition)
{
    // IK Solver 自动计算关节角度
    animator.SetIKPosition(AvatarIKGoal.RightHand, targetPosition);
    animator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1.0f);
}
```

| 特性 | FK（正向） | IK（反向） |
|------|------------|------------|
| **控制方式** | 关节角度 | 末端位置 |
| **计算方向** | 根 → 末端 | 末端 → 根 |
| **用途** | 动画播放 | 交互控制 |
| **性能** | 快 | 较慢 |

---

## Unity IK 系统

### 1. 2D IK

**适用于 2D 游戏，简单且快速**

```csharp
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class TwoBoneIKController : MonoBehaviour
{
    public Transform target;
    public Transform mixTarget;
    public float mixWeight = 0.5f;

    private Animator animator;
    private Vector3 ikPosition;
    private Quaternion ikRotation;

    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void OnAnimatorIK(int layerIndex)
    {
        // 计算目标位置
        ikPosition = target.position;
        ikRotation = target.rotation;

        if (mixTarget != null)
        {
            // 混合 IK 位置
            ikPosition = Vector3.Lerp(
                ikPosition,
                mixTarget.position,
                mixWeight
            );
        }

        // 设置 IK 位置和旋转
        animator.SetIKPosition(AvatarIKGoal.RightHand, ikPosition);
        animator.SetIKRotation(AvatarIKGoal.RightHand, ikRotation);
        animator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1.0f);
        animator.SetIKRotationWeight(AvatarIKGoal.RightHand, 1.0f);
    }
}
```

### 2. CCD IK（Cyclic Coordinate Descent）

**适用于快速移动物体，精确性高**

```csharp
public class CCDSolver : MonoBehaviour
{
    public Transform[] joints;      // 关节链
    public Transform target;        // 目标位置
    public int iterations = 10;    // 迭代次数

    void LateUpdate()
    {
        for (int i = 0; i < iterations; i++)
        {
            SolveCCD();
        }
    }

    void SolveCCD()
    {
        for (int i = joints.Length - 1; i >= 0; i--)
        {
            Transform joint = joints[i];
            Vector3 toTarget = target.position - joints[joints.Length - 1].position;

            // 旋转关节指向目标
            Quaternion rotation = Quaternion.FromToRotation(
                joints[joints.Length - 1].position - joint.position,
                toTarget
            );

            joint.rotation = rotation * joint.rotation;
        }
    }
}
```

### 3. FABRIK（Forward And Backward Reaching Inverse Kinematics）

**Unity 内置，适用于角色手臂/腿部**

```csharp
[RequireComponent(typeof(Animator))]
public class FABRIKController : MonoBehaviour
{
    public Transform handTarget;
    public Transform elbowTarget;
    public float lookAtWeight = 1.0f;
    public float bodyWeight = 1.0f;

    private Animator animator;

    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void OnAnimatorIK(int layerIndex)
    {
        // 设置 FABRIK 位置
        animator.SetIKPosition(AvatarIKGoal.RightHand, handTarget.position);
        animator.SetIKRotation(AvatarIKGoal.RightHand, handTarget.rotation);

        // 设置 IK 权重
        animator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1.0f);
        animator.SetIKRotationWeight(AvatarIKGoal.RightHand, 1.0f);

        // 身体 IK
        animator.SetLookAtPosition(handTarget.position);
        animator.SetLookAtWeight(lookAtWeight);

        // 手肘目标
        if (elbowTarget != null)
        {
            animator.SetIKHintPosition(
                AvatarIKHint.RightElbow,
                elbowTarget.position
            );
            animator.SetIKHintPositionWeight(
                AvatarIKHint.RightElbow,
                1.0f
            );
        }
    }
}
```

---

## 实战示例

### 1. 角色手部 IK

```csharp
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class HandIK : MonoBehaviour
{
    public Transform handTarget;
    public float weight = 1.0f;
    public float transitionSpeed = 5.0f;

    private Animator animator;
    private float currentWeight;

    void Start()
    {
        animator = GetComponent<Animator>();
        currentWeight = 0f;
    }

    void Update()
    {
        // 平滑过渡 IK 权重
        currentWeight = Mathf.Lerp(
            currentWeight,
            weight,
            Time.deltaTime * transitionSpeed
        );
    }

    void OnAnimatorIK(int layerIndex)
    {
        if (currentWeight > 0.01f)
        {
            // 设置手部 IK
            animator.SetIKPosition(
                AvatarIKGoal.RightHand,
                handTarget.position
            );
            animator.SetIKRotation(
                AvatarIKGoal.RightHand,
                handTarget.rotation
            );
            animator.SetIKPositionWeight(
                AvatarIKGoal.RightHand,
                currentWeight
            );
            animator.SetIKRotationWeight(
                AvatarIKGoal.RightHand,
                currentWeight
            );
        }
    }
}
```

### 2. 角色脚部 IK（自适应地形）

```csharp
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class FootIK : MonoBehaviour
{
    public float groundDistance = 0.2f;
    public float footOffset = 0.1f;
    public LayerMask groundLayer;

    private Animator animator;

    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void OnAnimatorIK(int layerIndex)
    {
        // 脚部 IK 目标
        Vector3 leftFootTarget = GetFootTarget(
            AvatarIKGoal.LeftFoot
        );
        Vector3 rightFootTarget = GetFootTarget(
            AvatarIKGoal.RightFoot
        );

        // 设置脚部 IK
        animator.SetIKPosition(AvatarIKGoal.LeftFoot, leftFootTarget);
        animator.SetIKPosition(AvatarIKGoal.RightFoot, rightFootTarget);
        animator.SetIKPositionWeight(AvatarIKGoal.LeftFoot, 1.0f);
        animator.SetIKPositionWeight(AvatarIKGoal.RightFoot, 1.0f);
    }

    Vector3 GetFootTarget(AvatarIKGoal foot)
    {
        Vector3 footPosition = animator.GetIKPosition(foot);
        Vector3 origin = footPosition + Vector3.up * 0.1f;

        // 检测地面
        RaycastHit hit;
        if (Physics.Raycast(origin, Vector3.down, out hit, groundDistance, groundLayer))
        {
            // 调整脚部位置到地面
            return hit.point + Vector3.up * footOffset;
        }

        return footPosition;
    }
}
```

### 3. 抓取系统 IK

```csharp
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class GrabIK : MonoBehaviour
{
    public Transform grabTarget;
    public float grabDistance = 1.5f;
    public LayerMask grabLayer;

    private Animator animator;
    private bool isGrabbing;

    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void Update()
    {
        if (Input.GetButtonDown("Grab"))
        {
            if (!isGrabbing)
            {
                TryGrab();
            }
            else
            {
                Release();
            }
        }
    }

    void TryGrab()
    {
        Collider[] hits = Physics.OverlapSphere(
            transform.position,
            grabDistance,
            grabLayer
        );

        if (hits.Length > 0)
        {
            grabTarget = hits[0].transform;
            isGrabbing = true;
        }
    }

    void Release()
    {
        grabTarget = null;
        isGrabbing = false;
    }

    void OnAnimatorIK(int layerIndex)
    {
        if (isGrabbing && grabTarget != null)
        {
            // 手部 IK 到目标
            animator.SetIKPosition(
                AvatarIKGoal.RightHand,
                grabTarget.position
            );
            animator.SetIKRotation(
                AvatarIKGoal.RightHand,
                grabTarget.rotation
            );
            animator.SetIKPositionWeight(
                AvatarIKGoal.RightHand,
                1.0f
            );
            animator.SetIKRotationWeight(
                AvatarIKGoal.RightHand,
                1.0f
            );
        }
        else
        {
            // 重置 IK
            animator.SetIKPositionWeight(
                AvatarIKGoal.RightHand,
                0.0f
            );
            animator.SetIKRotationWeight(
                AvatarIKGoal.RightHand,
                0.0f
            );
        }
    }
}
```

### 4. 多重 IK（手 + 身体）

```csharp
[RequireComponent(typeof(Animator))]
public class MultiIK : MonoBehaviour
{
    public Transform handTarget;
    public Transform bodyTarget;
    public float handWeight = 1.0f;
    public float bodyWeight = 0.5f;

    private Animator animator;

    void Start()
    {
        animator = GetComponent<Animator>();
    }

    void OnAnimatorIK(int layerIndex)
    {
        // 手部 IK
        animator.SetIKPosition(
            AvatarIKGoal.RightHand,
            handTarget.position
        );
        animator.SetIKRotation(
            AvatarIKGoal.RightHand,
            handTarget.rotation
        );
        animator.SetIKPositionWeight(
            AvatarIKGoal.RightHand,
            handWeight
        );
        animator.SetIKRotationWeight(
            AvatarIKGoal.RightHand,
            handWeight
        );

        // 身体 IK（朝向目标）
        animator.SetLookAtPosition(bodyTarget.position);
        animator.SetLookAtWeight(bodyWeight);
    }
}
```

---

## 性能优化

### 1. 减少 IK 计算频率

```csharp
public class OptimizedIK : MonoBehaviour
{
    public Transform target;
    public float ikUpdateInterval = 0.05f;

    private Animator animator;
    private float nextUpdateTime;

    void Start()
    {
        animator = GetComponent<Animator>();
        nextUpdateTime = Time.time + ikUpdateInterval;
    }

    void Update()
    {
        if (Time.time >= nextUpdateTime)
        {
            // 更新 IK
            UpdateIK();
            nextUpdateTime = Time.time + ikUpdateInterval;
        }
    }

    void UpdateIK()
    {
        // IK 计算
        animator.SetIKPosition(AvatarIKGoal.RightHand, target.position);
        animator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1.0f);
    }
}
```

### 2. 使用 IK 权重过渡

```csharp
public class SmoothIKWeight : MonoBehaviour
{
    public float targetWeight = 1.0f;
    public float weightSpeed = 2.0f;

    private Animator animator;
    private float currentWeight;

    void Update()
    {
        currentWeight = Mathf.Lerp(
            currentWeight,
            targetWeight,
            Time.deltaTime * weightSpeed
        );
    }

    void OnAnimatorIK(int layerIndex)
    {
        animator.SetIKPositionWeight(
            AvatarIKGoal.RightHand,
            currentWeight
        );
    }
}
```

---

## 最佳实践

### DO ✅

- 根据场景选择合适的 IK Solver
- 使用 FABRIK 处理角色手臂/腿部
- 使用 CCD 处理快速移动物体
- 使用 IK 权重平滑过渡
- 为脚部 IK 添加自适应地形
- 减少 IK 计算频率优化性能

### DON'T ❌

- 不要在不合适的地方使用 IK（简单动画用 FK）
- 不要忽视 IK 的性能开销
- 不要忘记设置 IK 权重（默认为 0）
- 不要混合使用多种 IK Solvers（会导致冲突）
- 不要在 Update 中频繁修改 IK 目标

---

## 常见问题

### Q: IK 不工作？
**A**: 
1. 检查 Animator 是否启用了 IK Pass
2. 检查 IK 权重是否设置为 > 0
3. 检查 Avatar 是否正确配置
4. 检查 OnAnimatorIK 是否在正确的图层调用

### Q: IK 抖动严重？
**A**: 
1. 增加 IK 计算频率
2. 平滑 IK 权重过渡
3. 调整 IK 目标位置
4. 使用 FABRIK 而不是 CCD

### Q: 如何优化 IK 性能？
**A**: 
1. 减少 IK 计算频率
2. 使用简单的 IK Solver
3. 限制 IK 的影响范围
4. 使用对象池减少物体数量

---

## 相关链接

- [动画混合与过渡](./动画混合与过渡.md)
- [动画事件与回调](./动画事件与回调.md)
- [性能优化指南](../../30_性能优化/README.md)

---

**适用版本**: Unity 2019.4+
**最后更新**: 2026-03-04
