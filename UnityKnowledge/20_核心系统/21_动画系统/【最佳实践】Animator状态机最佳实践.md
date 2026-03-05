---
title: 【最佳实践】Animator状态机最佳实践
tags: [Unity, 动画, 动画系统, 状态机, 最佳实践]
category: 核心系统/动画系统
created: 2026-03-05 08:30
updated: 2026-03-05 08:30
description: Animator状态机设计与优化最佳实践
unity_version: 2021.3+
---
# Animator 状态机最佳实践

> Unity动画控制器的优化与最佳实践 `#动画系统` `#最佳实践` `#性能优化`

## 文档定位

本文档从**最佳实践角度**总结Animator状态机最佳实践的推荐做法。

**相关文档**：、、

---

## 相关链接

```csharp
// 使用Hash避免字符串查找
private static readonly int SpeedHash = Animator.StringToHash("Speed");
animator.SetFloat(SpeedHash, currentSpeed);

// 使用触发器
animator.SetTrigger(AttackHash);

// 状态检查
if (animator.GetCurrentAnimatorStateInfo(0).shortNameHash == AttackStateHash)
{
    // 正在播放攻击动画
}
```

---

## 参数优化

### 使用Hash代替字符串

```csharp
// ❌ 错误 - 每次都会进行字符串查找
void Update()
{
    animator.SetFloat("Speed", speed);
    animator.SetBool("IsGrounded", isGrounded);
    animator.SetTrigger("Attack");
}

// ✅ 正确 - 缓存Hash值
private static readonly int SpeedHash = Animator.StringToHash("Speed");
private static readonly int IsGroundedHash = Animator.StringToHash("IsGrounded");
private static readonly int AttackHash = Animator.StringToHash("Attack");

void Update()
{
    animator.SetFloat(SpeedHash, speed);
    animator.SetBool(IsGroundedHash, isGrounded);
    animator.SetTrigger(AttackHash);
}
```

### 批量参数设置

```csharp
// 对于大量参数，考虑使用AnimatorOverrideController
// 或在LateUpdate中批量设置减少调用次数
```

---

## 状态检测

### 检测当前状态

```csharp
public class AnimationStateChecker : MonoBehaviour
{
    private Animator animator;

    // 缓存状态Hash
    private static readonly int IdleStateHash = Animator.StringToHash("Idle");
    private static readonly int RunStateHash = Animator.StringToHash("Run");
    private static readonly int AttackStateHash = Animator.StringToHash("Attack");

    private void Awake()
    {
        animator = GetComponent<Animator>();
    }

    public bool IsInAttackAnimation()
    {
        var stateInfo = animator.GetCurrentAnimatorStateInfo(0);
        return stateInfo.shortNameHash == AttackStateHash;
    }

    public bool IsAnimationComplete()
    {
        var stateInfo = animator.GetCurrentAnimatorStateInfo(0);
        return stateInfo.normalizedTime >= 1f;
    }

    public float GetAnimationProgress()
    {
        var stateInfo = animator.GetCurrentAnimatorStateInfo(0);
        return stateInfo.normalizedTime;
    }
}
```

### 状态机事件

```csharp
public class AnimationEvents : MonoBehaviour
{
    [SerializeField] private Animator animator;

    // 动画事件回调
    public void OnAnimationEvent(string eventName)
    {
        switch (eventName)
        {
            case "AttackHit":
                DealDamage();
                break;
            case "Footstep":
                PlayFootstepSound();
                break;
            case "AnimationEnd":
                OnAnimationComplete();
                break;
        }
    }

    // 使用StateMachineBehaviour替代（推荐）
    public class AttackStateBehaviour : StateMachineBehaviour
    {
        public override void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            // 进入攻击状态
        }

        public override void OnStateExit(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            // 退出攻击状态
            var player = animator.GetComponent<PlayerController>();
            player?.OnAttackComplete();
        }

        public override void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
        {
            // 在特定帧触发伤害
            if (stateInfo.normalizedTime >= 0.5f && stateInfo.normalizedTime < 0.6f)
            {
                // 触发伤害判定
            }
        }
    }
}
```

---

## 层级管理

### 多层动画

```csharp
public class LayeredAnimation : MonoBehaviour
{
    private Animator animator;

    // 层索引
    private const int BaseLayer = 0;
    private const int UpperBodyLayer = 1;

    private void Awake()
    {
        animator = GetComponent<Animator>();
    }

    public void PlayUpperBodyAnimation(string stateName)
    {
        // 在上半身层播放动画
        animator.CrossFade(stateName, 0.1f, UpperBodyLayer);
    }

    public void SetUpperBodyWeight(float weight)
    {
        // 设置上半身层权重（0-1）
        animator.SetLayerWeight(UpperBodyLayer, weight);
    }

    public void BlendToFullBody()
    {
        // 渐变到全身动画
        StartCoroutine(BlendWeight(UpperBodyLayer, 0f, 0.3f));
    }

    private IEnumerator BlendWeight(int layerIndex, float targetWeight, float duration)
    {
        float startWeight = animator.GetLayerWeight(layerIndex);
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float weight = Mathf.Lerp(startWeight, targetWeight, elapsed / duration);
            animator.SetLayerWeight(layerIndex, weight);
            yield return null;
        }

        animator.SetLayerWeight(layerIndex, targetWeight);
    }
}
```

---

## 动画优化

### 减少Animator组件数量

```csharp
// 对于简单动画，考虑使用Simple Animation或直接控制
public class SimpleAnimationController : MonoBehaviour
{
    [SerializeField] private Animation simpleAnimation;

    public void PlaySimple(string clipName)
    {
        simpleAnimation.Play(clipName);
    }
}

// 或使用DOTween替代简单动画
transform.DOScale(1.2f, 0.3f).SetEase(Ease.OutBack);
```

### 动画曲线优化

```csharp
// 在编辑器中减少曲线精度
// Animation > Optimization > Animation Compression: Optimal

// 运行时减少动画更新频率
public class AnimationOptimizer : MonoBehaviour
{
    [SerializeField] private Animator animator;
    [SerializeField] private float cullingDistance = 20f;

    private void Update()
    {
        float distance = Vector3.Distance(transform.position, Camera.main.transform.position);

        // 远距离时降低动画质量
        if (distance > cullingDistance)
        {
            animator.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
        }
        else
        {
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        }
    }
}
```

### GPU Skinning

```csharp
// 对于大量角色，启用GPU Skinning
// Project Settings > Player > Other Settings > GPU Skinning

// 运行时检查
if (SystemInfo.supportsComputeShaders)
{
    // 可以使用GPU Skinning
}
```

---

## 常见模式

### 角色动画控制器

```csharp
public class CharacterAnimator : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private Animator animator;
    [SerializeField] private CharacterController controller;

    [Header("Animation Parameters")]
    [SerializeField] private float animationSmoothTime = 0.1f;

    // Hash缓存
    private static readonly int SpeedHash = Animator.StringToHash("Speed");
    private static readonly int VerticalSpeedHash = Animator.StringToHash("VerticalSpeed");
    private static readonly int IsGroundedHash = Animator.StringToHash("IsGrounded");
    private static readonly int JumpHash = Animator.StringToHash("Jump");
    private static readonly int AttackHash = Animator.StringToHash("Attack");

    private float currentSpeed;

    private void Update()
    {
        UpdateMovementAnimation();
    }

    private void UpdateMovementAnimation()
    {
        // 平滑速度变化
        float targetSpeed = controller.velocity.magnitude;
        currentSpeed = Mathf.Lerp(currentSpeed, targetSpeed, animationSmoothTime * Time.deltaTime * 10f);

        animator.SetFloat(SpeedHash, currentSpeed);
        animator.SetFloat(VerticalSpeedHash, controller.velocity.y);
        animator.SetBool(IsGroundedHash, controller.isGrounded);
    }

    public void Jump()
    {
        animator.SetTrigger(JumpHash);
    }

    public void Attack()
    {
        animator.SetTrigger(AttackHash);
    }
}
```

### 动画回调管理

```csharp
public class AnimationCallbackReceiver : MonoBehaviour
{
    public event Action OnAttackHit;
    public event Action OnAttackEnd;
    public event Action OnFootstep;

    // 由Animation Event调用
    private void AttackHit() => OnAttackHit?.Invoke();
    private void AttackEnd() => OnAttackEnd?.Invoke();
    private void Footstep() => OnFootstep?.Invoke();
}

// 使用
public class CombatController : MonoBehaviour
{
    [SerializeField] private AnimationCallbackReceiver animReceiver;

    private void OnEnable()
    {
        animReceiver.OnAttackHit += HandleAttackHit;
        animReceiver.OnAttackEnd += HandleAttackEnd;
    }

    private void OnDisable()
    {
        animReceiver.OnAttackHit -= HandleAttackHit;
        animReceiver.OnAttackEnd -= HandleAttackEnd;
    }

    private void HandleAttackHit()
    {
        // 造成伤害
    }

    private void HandleAttackEnd()
    {
        // 攻击结束，可以输入下一个指令
    }
}
```

---

## 最佳实践清单

### DO ✅

- 使用Hash缓存参数名
- 使用StateMachineBehaviour处理状态逻辑
- 合理设置Culling Mode
- 对远处角色降低动画更新
- 使用Avatar Mask控制层级混合

### DON'T ❌

- 不要在Update中频繁调用SetTrigger
- 不要过度使用动画层
- 不要忽略动画压缩设置
- 不要在状态机中使用过多过渡
- 不要忘记清理动画事件订阅

---

## 相关链接

- 深入学习: [动画系统学习路径](../../20_核心系统/21_动画系统/【教程】动画系统学习路径.md)
- 代码片段: [DOTween常用动画](../../60_第三方库/【代码片段】DOTween常用动画.md)
