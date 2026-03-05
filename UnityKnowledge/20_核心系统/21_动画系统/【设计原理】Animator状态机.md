---
title: 【设计原理】Animator状态机
tags: [Unity, 动画, 动画系统, 状态机, 设计原理]
category: 核心系统/动画系统
created: 2026-03-05 08:30
updated: 2026-03-05 08:30
description: 状态机模型在动画系统中的应用
unity_version: 2021.3+
---
# Animator 状态机

> 第1课 | 动画系统模块

## 文档定位

本文档从**底层机制角度**深入讲解Animator状态机的本质原理。

**相关文档**：、、

---

## 1. Animator 组件

### 1.1 基础配置

```csharp
using UnityEngine;

public class AnimationController : MonoBehaviour
{
    private Animator animator;

    private void Awake()
    {
        animator = GetComponent<Animator>();
    }

    private void Update()
    {
        // 设置参数
        animator.SetFloat("Speed", Input.GetAxis("Vertical"));
        animator.SetBool("IsGrounded", IsGrounded());

        // 触发触发器
        if (Input.GetButtonDown("Jump"))
        {
            animator.SetTrigger("Jump");
        }
    }

    private bool IsGrounded()
    {
        return Physics.Raycast(transform.position, Vector3.down, 0.1f);
    }
}
```

### 1.2 参数类型

```csharp
public class AnimatorParameters : MonoBehaviour
{
    private Animator animator;

    private void Start()
    {
        animator = GetComponent<Animator>();

        // Float - 用于混合树
        animator.SetFloat("Speed", 5.0f);

        // Int - 用于状态选择
        animator.SetInteger("WeaponType", 1);

        // Bool - 用于状态切换
        animator.SetBool("IsAttacking", true);

        // Trigger - 一次性触发
        animator.SetTrigger("Attack");

        // 获取参数
        float speed = animator.GetFloat("Speed");
        bool isAttacking = animator.GetBool("IsAttacking");
    }
}
```

---

## 2. 状态机控制

### 2.1 状态信息

```csharp
public class StateInfo : MonoBehaviour
{
    private Animator animator;

    private void Update()
    {
        // 当前状态信息
        AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(0);

        // 状态名称
        Debug.Log($"当前状态: {stateInfo.shortNameHash}");

        // 是否是特定状态
        if (stateInfo.IsName("Idle"))
        {
            Debug.Log("正在待机");
        }

        // 动画进度 (0-1)
        float normalizedTime = stateInfo.normalizedTime;

        // 动画长度
        float length = stateInfo.length;

        // 循环次数
        int loopCount = (int)stateInfo.normalizedTime;

        // 动画是否即将结束
        if (stateInfo.normalizedTime > 0.9f)
        {
            Debug.Log("动画即将结束");
        }
    }
}
```

### 2.2 状态切换

```csharp
public class StateSwitcher : MonoBehaviour
{
    private Animator animator;

    public void PlayAnimation(string stateName)
    {
        // 直接播放状态（无过渡）
        animator.Play(stateName);

        // 带过渡播放
        animator.CrossFade(stateName, 0.25f);

        // 指定层播放
        animator.CrossFade(stateName, 0.25f, 1);  // 层索引 1

        // 从指定时间开始播放
        animator.Play(stateName, 0, 0.5f);  // 从 50% 处开始
    }

    public void PlayInFixedTime()
    {
        // 使用固定时间（秒）
        animator.CrossFadeInFixedTime("Attack", 0.5f);
    }
}
```

---

## 3. 动画层

### 3.1 层操作

```csharp
public class LayerControl : MonoBehaviour
{
    private Animator animator;

    private void Start()
    {
        // 获取层数量
        int layerCount = animator.layerCount;

        // 获取层名称
        string layerName = animator.GetLayerName(0);

        // 获取层权重
        float weight = animator.GetLayerWeight(1);

        // 设置层权重（用于混合）
        animator.SetLayerWeight(1, 0.5f);  // 上半身动画层
    }

    private void Update()
    {
        // 根据战斗状态调整上半身动画权重
        bool inCombat = IsInCombat();
        float targetWeight = inCombat ? 1f : 0f;

        // 平滑过渡层权重
        float currentWeight = animator.GetLayerWeight(1);
        animator.SetLayerWeight(1, Mathf.Lerp(currentWeight, targetWeight, Time.deltaTime * 5f));
    }

    private bool IsInCombat() => true;
}
```

---

## 4. 动画事件

### 4.1 定义事件

```csharp
public class AnimationEvents : MonoBehaviour
{
    private Animator animator;

    // 动画事件回调
    public void OnAnimationStart()
    {
        Debug.Log("动画开始");
    }

    public void OnAnimationEnd()
    {
        Debug.Log("动画结束");
    }

    public void OnAttackHit()
    {
        // 在攻击动画的关键帧检测伤害
        DealDamage();
    }

    public void OnFootstep()
    {
        // 播放脚步声
        PlayFootstepSound();
    }

    private void DealDamage()
    {
        // 伤害逻辑
    }

    private void PlayFootstepSound()
    {
        // 音效逻辑
    }
}
```

### 4.2 脚本添加事件

```csharp
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.Animations;

public class AnimationEventSetter
{
    [MenuItem("Tools/Add Animation Events")]
    public static void AddEventsToClip()
    {
        AnimationClip clip = Selection.activeObject as AnimationClip;
        if (clip == null) return;

        // 创建事件
        AnimationEvent attackEvent = new AnimationEvent
        {
            time = 0.5f,  // 动画 50% 处
            functionName = "OnAttackHit",
            intParameter = 10  // 伤害值
        };

        // 添加事件
        AnimationUtility.SetAnimationEvents(clip, new[] { attackEvent });

        EditorUtility.SetDirty(clip);
        AssetDatabase.SaveAssets();
    }
}
#endif
```

---

## 5. 根运动（Root Motion）

### 5.1 应用根运动

```csharp
public class RootMotionController : MonoBehaviour
{
    private Animator animator;

    private void Awake()
    {
        animator = GetComponent<Animator>();
        animator.applyRootMotion = true;
    }

    // 自定义根运动处理
    private void OnAnimatorMove()
    {
        // 获取根运动位移
        Vector3 deltaPosition = animator.deltaPosition;
        Quaternion deltaRotation = animator.deltaRotation;

        // 应用到角色
        transform.position += deltaPosition;
        transform.rotation = deltaRotation * transform.rotation;

        // 或者使用 Rigidbody
        // rigidbody.MovePosition(rigidbody.position + deltaPosition);
        // rigidbody.MoveRotation(deltaRotation * rigidbody.rotation);
    }
}
```

---

## 6. 状态机行为（StateMachineBehaviour）

### 6.1 自定义状态行为

```csharp
using UnityEngine;

public class AttackStateBehaviour : StateMachineBehaviour
{
    // 进入状态
    override public void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        Debug.Log("进入攻击状态");

        // 获取角色组件
        var player = animator.GetComponent<Player>();
        player?.OnAttackStart();
    }

    // 更新状态（每帧）
    override public void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        // 检测攻击帧
        if (stateInfo.normalizedTime >= 0.5f && stateInfo.normalizedTime < 0.6f)
        {
            Debug.Log("攻击判定帧");
        }
    }

    // 退出状态
    override public void OnStateExit(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        Debug.Log("退出攻击状态");

        var player = animator.GetComponent<Player>();
        player?.OnAttackEnd();
    }

    // 状态机移动（Root Motion）
    override public void OnStateMove(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        Vector3 delta = animator.deltaPosition;
        // 处理移动
    }

    // 状态机 IK
    override public void OnStateIK(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        // 处理 IK
    }
}
```

---

## 7. 动画覆盖控制器

### 7.1 运行时切换

```csharp
public class AvatarSwitcher : MonoBehaviour
{
    public AnimatorOverrideController[] overrideControllers;
    private Animator animator;

    public void SwitchAvatar(int index)
    {
        animator.runtimeAnimatorController = overrideControllers[index];
    }

    // 运行时创建覆盖控制器
    public void CreateOverrideController(AnimationClip idleClip, AnimationClip walkClip)
    {
        var baseController = animator.runtimeAnimatorController;
        var overrideController = new AnimatorOverrideController(baseController);

        // 替换动画片段
        overrideController["Idle"] = idleClip;
        overrideController["Walk"] = walkClip;

        animator.runtimeAnimatorController = overrideController;
    }
}
```

---

## 本课小结

### Animator 参数类型

| 类型 | 方法 | 用途 |
|------|------|------|
| Float | SetFloat/GetFloat | 混合树、连续值 |
| Int | SetInteger/GetInteger | 状态选择 |
| Bool | SetBool/GetBool | 状态开关 |
| Trigger | SetTrigger | 一次性触发 |

### StateMachineBehaviour 回调

| 方法 | 调用时机 |
|------|----------|
| OnStateEnter | 进入状态 |
| OnStateUpdate | 每帧更新 |
| OnStateExit | 退出状态 |
| OnStateMove | Root Motion |
| OnStateIK | IK 计算 |

### 最佳实践

1. **使用 Hash 优化** - Animator.StringToHash()
2. **避免频繁 SetTrigger** - 可能丢失触发
3. **使用 StateMachineBehaviour** - 分离动画逻辑
4. **合理使用层** - 分离身体部位动画

---

## 相关链接

- [Animator 官方文档](https://docs.unity3d.com/ScriptReference/Animator.html)
- [Animation System Overview](https://docs.unity3d.com/Manual/AnimationOverview.html)
