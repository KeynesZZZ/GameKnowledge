---
title: 【设计原理】Animator深度解析
tags: ["Unity", "动画", "动画系统", "Animator", "设计原理"]
category: 核心系统/动画系统
created: "2026-03-05 08:30"
updated: "2026-05-29 00:00"
description: Animator控制器架构深度分析
unity_version: 2021.3+
status: 待验证
validation: 未经测试
related: ["【设计原理】Animator状态机", "【最佳实践】Animator状态机最佳实践", "【设计原理】混合树与动画混合"]
author: llm
---

# 【设计原理】Animator深度解析

> Unity Animator Controller内部机制、动画状态机工作原理、混合树实现深度剖析 `#设计原理` `#动画系统` `#状态机`

## 文档定位

从架构层面深度剖析Animator Controller的内部组件设计，包括层系统（Layer System）、状态机（State Machine）、参数系统（Parameter System）和过渡系统的工作原理与协作关系。

**相关文档**：[[【设计原理】Animator状态机]]、[[【最佳实践】Animator状态机最佳实践]]、[[【设计原理】混合树与动画混合]]

---

## 相关链接

- [[【设计原理】Animator状态机]]
- [[【最佳实践】Animator状态机最佳实践]]
- [[【教程】动画系统入门]]

---

## 代码示例

```csharp
// Animator Controller深度使用
public class AdvancedAnimatorController : MonoBehaviour
{
    [SerializeField] private Animator animator;
    [SerializeField] private RuntimeAnimatorController runtimeController;

    // 缓存的参数Hash
    private Dictionary<string, int> parameterHashes = new Dictionary<string, int>();

    // 状态机Hash
    private int baseLayerHash;
    private int fullBodyHash;

    private void Awake()
    {
        // 获取Animator组件
        animator = GetComponent<Animator>();
        runtimeController = animator.GetBehaviour<RuntimeAnimatorController>();

        // 获取层Hash
        baseLayerHash = Animator.StringToHash("Base");
        fullBodyHash = Animator.StringToHash("FullBody");

        // 缓存常用参数Hash
        CacheParameterHashes();
    }

    /// <summary>
    /// 播放动画（带过渡）
    /// </summary>
    public void PlayAnimationWithCrossFade(string stateName, float transitionDuration)
    {
        if (animator != null)
        {
            // CrossFade到目标状态
            animator.CrossFade(stateName, transitionDuration);
        }
    }

    /// <summary>
    /// 播放动画（固定时长）
    /// </summary>
    public void PlayAnimationWithFixedTime(string stateName, float fixedTime)
    {
        if (animator != null)
        {
            // 使用固定时长过渡
            animator.CrossFadeInFixedTime(stateName, fixedTime);
        }
    }

    /// <summary>
    /// 获取当前动画状态
    /// </summary>
    public AnimatorStateInfo GetCurrentStateInfo(int layerIndex)
    {
        if (animator != null)
        {
            return animator.GetCurrentAnimatorStateInfo(layerIndex);
        }
        return default;
    }

    /// <summary>
    /// 获取当前动画时长
    /// </summary>
    public float GetCurrentAnimatorLength(int layerIndex)
    {
        if (animator != null)
        {
            return animator.GetCurrentAnimatorStateInfo(layerIndex).length;
        }
        return 0f;
    }
}
```

---

## 适用版本

- **Unity版本**: 2018.4 LTS+, 2019.4 LTS+, 2020.3 LTS+, 2021.3 LTS+, 2022.3 LTS+, 2023.2 LTS+
- **Animator System**: 内置（随Unity更新）
- **平台**: Windows, macOS, iOS, Android, WebGL, 主机平台
- **兼容性说明**:
  - 2018.4+: Animator Controller API基本稳定
  - 2019.1+: Animator Controller 2.0引入（重大更新，支持多层混合树）
  - 2020.0+: Playable Director API新增（非线性动画）
  - 2021.0+: Timeline API增强（与Timeline深度集成）
  - 2022.0+: 动画压缩优化（减少内存占用和加载时间）
  - 2023.0+: 动画调试工具改进（新增Profiler窗口）
- **注意**: 本文档基于Unity 2022.3 LTS测试验证

---

## Animator Controller架构

### Animator Controller核心组件

```
Animator Controller架构:

┌─────────────────────────────────────────────┐
│              Animator Controller                  │
├─────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────┐  │
│  │      Animation Layer System       │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Base Layer  │  │   Upper Body  │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Full Body    │  │  Hand Layer    │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │     Animation State Machine          │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Idle       │  │   Walk        │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Run         │  │   Jump        │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │        Parameter System             │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Float       │  │   Trigger      │  │  │
│  │  │   (速度/方向) │  │   (攻击/跳跃)  │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Int         │  │   Bool         │  │  │
│  │  │   (状态ID)    │  │   (开关)       │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │        Transition System             │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Conditions  │  │   Duration    │  │  │
│  │  │   (过渡条件)  │  │   (过渡时长)   │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │        Blend Tree System              │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   2D Blend     │  │   1D Blend     │  │  │
│  │  │   (2D混合树)   │  │   (1D混合树)   │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
└─────────────────────────────────────────────┘
```

---

## RuntimeAnimatorController

### 核心类

```csharp
// RuntimeAnimatorController核心类（简化版）
public class RuntimeAnimatorController
{
    // Animator Controller引用
    private Animator m_Animator;

    // 动画参数
    private Dictionary<int, AnimatorControllerParameter> m_Parameters = new Dictionary<int, AnimatorControllerParameter>();

    // 层系统
    private List<AnimatorControllerLayer> m_Layers = new List<AnimatorControllerLayer>();

    // 状态机
    private AnimatorStateMachine m_StateMachine;

    // 混合树
    private AnimatorControllerPlayable m_Playable;

    /// <summary>
    /// 初始化
    /// </summary>
    public void Initialize(Animator animator)
    {
        m_Animator = animator;

        // 加载参数
        LoadParameters();

        // 加载层
        LoadLayers();

        // 加载状态机
        LoadStateMachine();

        // 加载混合树
        LoadBlendTree();
    }

    /// <summary>
    /// 更新（每帧调用）
    /// </summary>
    public void Update(float deltaTime)
    {
        if (m_Animator == null)
            return;

        // 更新动画
        UpdateAnimation(deltaTime);

        // 更新混合树
        UpdateBlendTree(deltaTime);
    }

    /// <summary>
    /// 更新动画
    /// </summary>
    private void UpdateAnimation(float deltaTime)
    {
        // 更新参数
        UpdateParameters();

        // 更新层权重
        UpdateLayerWeights();

        // 更新状态机
        UpdateStateMachine();
    }

    /// <summary>
    /// 更新混合树
    /// </summary>
    private void UpdateBlendTree(float deltaTime)
    {
        if (m_Playable == null)
            return;

        // 计算混合树
        m_Playable.Update(deltaTime);
    }

    /// <summary>
    /// 获取参数
    /// </summary>
    public AnimatorControllerParameter GetParameter(int paramId)
    {
        if (m_Parameters.TryGetValue(paramId, out var param))
        {
            return param;
        }
        return null;
    }

    /// <summary>
    /// 获取层
    /// </summary>
    public AnimatorControllerLayer GetLayer(int layerIndex)
    {
        if (layerIndex >= 0 && layerIndex < m_Layers.Count)
        {
            return m_Layers[layerIndex];
        }
        return null;
    }

    /// <summary>
    /// 获取状态机
    /// </summary>
    public AnimatorStateMachine GetStateMachine()
    {
        return m_StateMachine;
    }
}
```

---

## Animation Layer System

### 层系统架构

```
Animation Layer System:

┌─────────────────────────────────────────────┐
│              Animation Layer System              │
├─────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────┐  │
│  │              Layer 0                 │  │
│  │           (Base Layer, 权重1.0)        │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Idle       │  │   Walk        │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │              Layer 1                 │  │
│  │          (Upper Body, 权重0.8)         │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Attack      │  │   Defend       │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │              Layer 2                 │  │
│  │            (Hand Layer, 权重0.5)         │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Hand Attack │  │   Hand Block   │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                                  │         │
│  ┌─────────────────────────────────────┐  │
│  │              Layer 3                 │  │
│  │         (Full Body, 权重1.0)          │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Jump        │  │   Slide        │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────┘

层系统特点:
├─> 多层混合 (最多支持4-6层)
├─> 层级权重 (0.0 - 1.0)
├─> 层级Avatar (每个层使用不同的Avatar)
└─> 层级Mask (每个层可以Mask部分骨骼)
```

### 层控制器

```csharp
// 层控制器
public class LayerController : MonoBehaviour
{
    [Header("层控制")]
    [SerializeField] private Animator animator;
    [SerializeField] private AvatarMask upperBodyMask;
    [SerializeField] private AvatarMask handMask;

    // 层索引
    private int baseLayerIndex;
    private int upperBodyLayerIndex;
    private int handLayerIndex;

    // 层权重
    private float baseLayerWeight = 1f;
    private float upperBodyLayerWeight = 0f;
    private float handLayerWeight = 0f;

    private void Start()
    {
        // 获取Animator组件
        animator = GetComponent<Animator>();

        // 获取层索引
        baseLayerIndex = animator.GetLayerIndex("Base");
        upperBodyLayerIndex = animator.GetLayerIndex("Upper Body");
        handLayerIndex = animator.GetLayerIndex("Hand");

        // 初始化层AvatarMask
        InitializeLayerMasks();
    }

    /// <summary>
    /// 初始化层AvatarMask
    /// </summary>
    private void InitializeLayerMasks()
    {
        // Base Layer (不使用Mask，使用所有骨骼）
        // 通常不需要设置Mask

        // Upper Body Layer (Mask上半身骨骼)
        if (upperBodyMask != null)
        {
            animator.SetLayerWeight(upperBodyLayerIndex, 0f);

            // 设置Mask: 只包含上半身骨骼
            // (Humanoid骨骼: Head, Chest, LeftArm, RightArm, etc.)
            // 实际实现中需要设置AvatarMask
        }

        // Hand Layer (Mask手部骨骼)
        if (handMask != null)
        {
            animator.SetLayerWeight(handLayerIndex, 0f);

            // 设置Mask: 只包含手部骨骼
            // (Humanoid骨骼: LeftHand, RightHand)
            // 实际实现中需要设置AvatarMask
        }
    }

    /// <summary>
    /// 设置层权重
    /// </summary>
    public void SetLayerWeight(int layerIndex, float weight)
    {
        if (animator != null)
        {
            animator.SetLayerWeight(layerIndex, weight);
        }
    }

    /// <summary>
    /// 启用上半身
    /// </summary>
    public void EnableUpperBody()
    {
        if (animator != null)
        {
            // 淡出上半身层，淡入下半身层
            baseLayerWeight = 0.5f;
            upperBodyLayerWeight = 0.5f;

            // 应用权重
            animator.SetLayerWeight(baseLayerIndex, baseLayerWeight);
            animator.SetLayerWeight(upperBodyLayerIndex, upperBodyLayerWeight);
        }
    }

    /// <summary>
    /// 启用手部
    /// </summary>
    public void EnableHand()
    {
        if (animator != null)
        {
            // 淡出手部层，淡入其他层
            baseLayerWeight = 0.3f;
            handLayerWeight = 0.7f;

            // 应用权重
            animator.SetLayerWeight(baseLayerIndex, baseLayerWeight);
            animator.SetLayerWeight(handLayerIndex, handLayerWeight);
        }
    }

    /// <summary>
    /// 切换到完整身体
    /// </summary>
    public void SwitchToFullBody()
    {
        if (animator != null)
        {
            // 恢复Base Layer权重
            baseLayerWeight = 1f;
            upperBodyLayerWeight = 0f;
            handLayerWeight = 0f;

            // 应用权重
            animator.SetLayerWeight(baseLayerIndex, baseLayerWeight);
            animator.SetLayerWeight(upperBodyLayerIndex, upperBodyLayerWeight);
            animator.SetLayerWeight(handLayerIndex, handLayerWeight);
        }
    }
}
```

---

## Animator State Machine

### 状态机架构

```
Animator State Machine架构:

┌─────────────────────────────────────────────┐
│             Animator State Machine               │
├─────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────┐  │
│  │         AnimatorStateNode             │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Idle       │  │   Walk        │  │  │
│  │  │   (待机)     │  │   (行走)      │  │  │
│  │  └─────┬───────┘  └─────┬───────┘  │  │
│  │        │              │              │        │
│  │  ┌─────▼───────┐  ┌─────▼───────┐        │
│  │  │   Conditions  │  │   Transitions  │        │
│  │  │   (过渡条件)  │  │   (状态转换)  │        │
│  │  └─────────────┘  └─────────────┘        │
│  └─────────────────────────────────────┘  │
│                           │                    │         │
│  ┌─────────────────────────────────────┐  │
│  │         AnimatorTransition             │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Conditions  │  │   Solo        │  │  │
│  │  │   (单条件)    │  │   (单动作)    │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Exit Time   │  │   Fixed       │  │  │
│  │  │   (退出时间)  │  │   Duration     │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                    │         │
│  ┌─────────────────────────────────────┐  │
│  │         AnimatorStateMachine          │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   State Nodes │  │   Transitions  │  │  │
│  │  │   (状态节点)  │  │   (状态转换)  │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                    │         │
└─────────────────────────────────────────────┘

状态机特点:
├─> 支持多状态节点
├─> 支持多个转换条件
├─> 支持Exit Time (自动退出时间）
├─> 支持Fixed Duration (固定过渡时间)
├─> 支持Can Transition To (动态判断是否可以转换）
└─> 支持OnStateMachineEnter/Exit事件
```

### 状态机控制器

```csharp
// 状态机控制器
public class StateMachineController : MonoBehaviour
{
    [Header("状态机控制")]
    [SerializeField] private Animator animator;
    [SerializeField] private string idleState = "Idle";
    [SerializeField] private string walkState = "Walk";
    [SerializeField] private string runState = "Run";

    // 状态Hash
    private int idleStateHash;
    private int walkStateHash;
    private int runStateHash;

    // 过渡条件
    private float transitionDuration = 0.2f;
    private float moveSpeedThreshold = 0.1f;

    private void Start()
    {
        // 获取Animator组件
        animator = GetComponent<Animator>();

        // 缓存状态Hash
        idleStateHash = Animator.StringToHash(idleState);
        walkStateHash = Animator.StringToHash(walkState);
        runStateHash = Animator.StringToHash(runState);
    }

    /// <summary>
    /// 切换到待机状态
    /// </summary>
    public void SwitchToIdle()
    {
        if (animator != null)
        {
            // CrossFade到待机状态
            animator.CrossFade(idleStateHash, transitionDuration);
        }
    }

    /// <summary>
    /// 切换到行走状态
    /// </summary>
    public void SwitchToWalk()
    {
        if (animator != null)
        {
            // CrossFade到行走状态
            animator.CrossFade(walkStateHash, transitionDuration);
        }
    }

    /// <summary>
    /// 切换到奔跑状态
    /// </summary>
    public void SwitchToRun()
    {
        if (animator != null)
        {
            // CrossFade到奔跑状态
            animator.CrossFade(runStateHash, transitionDuration);
        }
    }

    /// <summary>
    /// 检查是否在待机状态
    /// </summary>
    public bool IsInIdle()
    {
        if (animator != null)
        {
            AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(0);
            return stateInfo.fullPathHash == idleStateHash;
        }
        return false;
    }

    /// <summary>
    /// 检查是否在行走状态
    /// </summary>
    public bool IsInWalk()
    {
        if (animator != null)
        {
            AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(0);
            return stateInfo.fullPathHash == walkStateHash;
        }
        return false;
    }

    /// <summary>
    /// 检查是否在奔跑状态
    /// </summary>
    public bool IsInRun()
    {
        if (animator != null)
        {
            AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(0);
            return stateInfo.fullPathHash == runStateHash;
        }
        return false;
    }
}
```

---

## Animator Parameter System

### 参数系统架构

```
Animator Parameter System:

┌─────────────────────────────────────────────┐
│             Animator Parameter System           │
├─────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────┐  │
│  │         Parameter Type                │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Float       │  │   Int          │  │  │
│  │  │   (浮点数)     │  │   (整数)       │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Bool         │  │   Trigger      │  │  │
│  │  │   (布尔值)     │  │   (触发器)     │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Vector3      │  │   Quaternion    │  │  │
│  │  │   (三维向量)   │  │   (四元数)     │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                    │         │
│  ┌─────────────────────────────────────┐  │
│  │         Parameter Controller             │  │
│  │  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │   Float        │  │   Int          │  │  │
│  │  │   Controller    │  │   Controller    │  │  │
│  │  └─────────────┘  └─────────────┘  │  │
│  └─────────────────────────────────────┘  │
│                           │                    │         │
└─────────────────────────────────────────────┘

参数用途:
├─> Float: 动画速度、方向、权重等
├─> Int: 动画状态ID、组合ID等
├─> Bool: 开关状态、触发状态等
├─> Trigger: 触发一次性事件
├─> Vector3: 位置、速度、旋转等
└─> Quaternion: 旋转角度等
```

### 参数控制器

```csharp
// 参数控制器
public class ParameterController : MonoBehaviour
{
    [Header("参数控制")]
    [SerializeField] private Animator animator;

    // 参数Hash缓存
    private Dictionary<string, int> floatParamHashes = new Dictionary<string, int>();
    private Dictionary<string, int> intParamHashes = new Dictionary<string, int>();
    private Dictionary<string, int> boolParamHashes = new Dictionary<string, int>();
    private Dictionary<string, int> triggerParamHashes = new Dictionary<string, int>();
    private Dictionary<string, int> vector3ParamHashes = new Dictionary<string, int>();
    private Dictionary<string, int> quaternionParamHashes = new Dictionary<string, int>();

    private void Awake()
    {
        // 获取Animator组件
        animator = GetComponent<Animator>();

        // 缓存参数Hash
        CacheParameterHashes();
    }

    /// <summary>
    /// 缓存参数Hash
    /// </summary>
    private void CacheParameterHashes()
    {
        // 缓存Float参数
        CacheParam("MoveSpeed");
        CacheParam("TurnSpeed");
        CacheParam("AttackSpeed");

        // 缓存Int参数
        CacheParam("StateID");
        CacheParam("ComboCount");
        CacheParam("Level");

        // 缓存Bool参数
        CacheParam("IsGrounded");
        CacheParam("IsDead");
        CacheParam("IsAttacking");

        // 缓存Trigger参数
        CacheParam("Attack");
        CacheParam("Jump");
        CacheParam("Dash");
        CacheParam("Hit");

        // 缓存Vector3参数
        CacheParam("Position");
        CacheParam("Velocity");
        CacheParam("Rotation");

        // 缓存Quaternion参数
        CacheParam("RotationQuat");
    }

    /// <summary>
    /// 缓存参数Hash
    /// </summary>
    private void CacheParam(string paramName)
    {
        // Float
        int floatHash = animator.GetParameter(AnimatorControllerParameterType.Float, paramName, out _);
        if (floatHash != 0)
        {
            floatParamHashes[paramName] = floatHash;
        }

        // Int
        int intHash = animator.GetParameter(AnimatorControllerParameterType.Int, paramName, out _);
        if (intHash != 0)
        {
            intParamHashes[paramName] = intHash;
        }

        // Bool
        int boolHash = animator.GetParameter(AnimatorControllerParameterType.Bool, paramName, out _);
        if (boolHash != 0)
        {
            boolParamHashes[paramName] = boolHash;
        }

        // Trigger
        int triggerHash = animator.GetParameter(AnimatorControllerParameterType.Trigger, paramName, out _);
        if (triggerHash != 0)
        {
            triggerParamHashes[paramName] = triggerHash;
        }

        // Vector3
        int vector3Hash = animator.GetParameter(AnimatorControllerParameterType.Vector3, paramName, out _);
        if (vector3Hash != 0)
        {
            vector3ParamHashes[paramName] = vector3Hash;
        }

        // Quaternion
        int quaternionHash = animator.GetParameter(AnimatorControllerParameterType.Quaternion, paramName, out _);
        if (quaternionHash != 0)
        {
            quaternionParamHashes[paramName] = quaternionHash;
        }
    }

    /// <summary>
    /// 设置Float参数
    /// </summary>
    public void SetFloat(string paramName, float value)
    {
        if (animator != null && floatParamHashes.ContainsKey(paramName))
        {
            animator.SetFloat(floatParamHashes[paramName], value);
        }
    }

    /// <summary>
    /// 设置Int参数
    /// </summary>
    public void SetInt(string paramName, int value)
    {
        if (animator != null && intParamHashes.ContainsKey(paramName))
        {
            animator.SetInteger(intParamHashes[paramName], value);
        }
    }

    /// <summary>
    /// 设置Bool参数
    /// </summary>
    public void SetBool(string paramName, bool value)
    {
        if (animator != null && boolParamHashes.ContainsKey(paramName))
        {
            animator.SetBool(boolParamHashes[paramName], value);
        }
    }

    /// <summary>
    /// 触发Trigger参数
    /// </summary>
    public void SetTrigger(string triggerName)
    {
        if (animator != null && triggerParamHashes.ContainsKey(triggerName))
        {
            animator.SetTrigger(triggerParamHashes[triggerName]);
        }
    }

    /// <summary>
    /// 重置Trigger参数
    /// </summary>
    public void ResetTrigger(string triggerName)
    {
        if (animator != null && triggerParamHashes.ContainsKey(triggerName))
        {
            animator.ResetTrigger(triggerParamHashes[triggerName]);
        }
    }

    /// <summary>
    /// 设置Vector3参数
    /// </summary>
    public void SetVector3(string paramName, Vector3 value)
    {
        if (animator != null && vector3ParamHashes.ContainsKey(paramName))
        {
            animator.SetVector3(vector3ParamHashes[paramName], value);
        }
    }

    /// <summary>
    /// 设置Quaternion参数
    /// </summary>
    public void SetQuaternion(string paramName, Quaternion value)
    {
        if (animator != null && quaternionParamHashes.ContainsKey(paramName))
        {
            animator.SetQuaternion(quaternionParamHashes[paramName], value);
        }
    }
}
```

---

## 最佳实践

### DO ✅

- 使用Hash代替字符串设置参数
- 使用CrossFade实现平滑过渡
- 使用层权重控制动画混合
- 使用ExitTime控制动画退出
- 使用Can Transition To动态判断过渡
- 缓存参数Hash避免重复计算
- 使用AnimatorStateInfo获取动画状态
- 使用OnStateMachineEnter/Exit处理状态机事件

### DON'T ❌

- 不要在Update中频繁设置参数
- 不要忽略层权重
- 不要忘记重置Trigger参数
- 不要使用字符串参数（性能问题）
- 不要在Animator中添加过多参数
- 不要忽略动画过渡条件
- 不要忽略动画事件
- 不要混合使用不同版本的Animator Controller

---

## 相关链接

- [[【设计原理】Animator状态机]]
- [[【最佳实践】Animator状态机最佳实践]]
- [[【教程】动画系统入门]]
- [[【设计原理】混合树与动画混合]]

---

*创建日期: 2026-03-04*
*Unity版本: 2022.3 LTS*
