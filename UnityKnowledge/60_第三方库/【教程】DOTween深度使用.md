---
title: 【教程】DOTween深度使用
tags: [Unity, 第三方库, DOTween, 教程]
category: 第三方库
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: DOTween动画库深度使用教程
unity_version: 2021.3+
---
# DOTween 深度使用

> Unity最流行的动画补间库完整指南 `#第三方库` `#动画` `#最佳实践`

## 文档定位

本文档从**使用角度**讲解DOTween深度使用。

**相关文档**：[[【代码片段】DOTween常用动画]]、[[【教程】DOTween深度使用]]

---

## 相关链接

```csharp
// 基础动画
transform.DOMove(targetPos, 1f);

// 链式调用
transform.DOMove(targetPos, 1f)
    .SetEase(Ease.OutQuad)
    .SetLoops(3, LoopType.Yoyo)
    .OnComplete(() => Debug.Log("Done"));

// 序列动画
var sequence = DOTween.Sequence();
sequence.Append(transform.DOMoveX(5f, 1f));
sequence.Append(transform.DORotate(new Vector3(0, 180, 0), 0.5f));
sequence.Join(transform.DOScale(1.5f, 0.5f));
```

---

## 初始化配置

```csharp
// 推荐初始化方式
[RuntimeInitializeOnLoadMethod]
static void InitDOTween()
{
    DOTween.Init(
        recycleAllByDefault: true,      // 默认回收所有Tween
        useSafeMode: true,              // 安全模式（自动处理空引用）
        logBehaviour: LogBehaviour.ErrorsOnly
    );
}

// 或在Awake中
void Awake()
{
    DOTween.Init(true, true, LogBehaviour.Verbose);
}
```

---

## API速查表

### Transform 动画

| 方法 | 说明 | 示例 |
|------|------|------|
| `DOMove` | 移动到目标位置 | `transform.DOMove(target, 1f)` |
| `DOMoveX/Y/Z` | 单轴移动 | `transform.DOMoveX(5f, 1f)` |
| `DOLocalMove` | 本地坐标移动 | `transform.DOLocalMove(target, 1f)` |
| `DORotate` | 旋转到目标角度 | `transform.DORotate(new Vector3(0, 90, 0), 1f)` |
| `DORotateQuaternion` | 旋转到四元数 | `transform.DORotateQuaternion(targetRot, 1f)` |
| `DOScale` | 缩放 | `transform.DOScale(2f, 1f)` |
| `DOPunchPosition` | 冲击位置 | `transform.DOPunchPosition(Vector3.up, 1f, 10, 1)` |
| `DOShakePosition` | 震动位置 | `transform.DOShakePosition(1f, 0.5f)` |
| `DOLookAt` | 看向目标 | `transform.DOLookAt(target, 1f)` |

### UI 动画

| 方法 | 说明 | 示例 |
|------|------|------|
| `DOFade` | 透明度 | `image.DOFade(0f, 1f)` |
| `DOColor` | 颜色 | `image.DOColor(Color.red, 1f)` |
| `DOFillAmount` | 填充量 | `image.DOFillAmount(1f, 1f)` |
| `DOAnchorPos` | 锚点位置 | `rectTransform.DOAnchorPos(Vector2.zero, 1f)` |
| `DOSizeDelta` | 尺寸 | `rectTransform.DOSizeDelta(new Vector2(100, 100), 1f)` |
| `DOPivot` | 轴心 | `rectTransform.DOPivot(new Vector2(0.5f, 0.5f), 1f)` |

### 数值动画

| 方法 | 说明 | 示例 |
|------|------|------|
| `DOTween.To` | 通用数值动画 | `DOTween.To(() => val, x => val = x, target, 1f)` |
| `DOValue` | Slider值 | `slider.DOValue(1f, 1f)` |
| `DONormalizedPos` | ScrollRect位置 | `scrollRect.DONormalizedPos(Vector2.zero, 1f)` |

---

## 缓动函数 (Ease)

### 常用缓动

```csharp
// 线性
.SetEase(Ease.Linear)

// 缓入（开始慢）
.SetEase(Ease.InQuad)
.SetEase(Ease.InCubic)
.SetEase(Ease.InExpo)

// 缓出（结束慢）
.SetEase(Ease.OutQuad)      // 最常用
.SetEase(Ease.OutCubic)
.SetEase(Ease.OutBounce)    // 弹跳效果

// 缓入缓出
.SetEase(Ease.InOutQuad)
.SetEase(Ease.InOutCubic)

// 弹性
.SetEase(Ease.OutBack)      // 超出后回弹
.SetEase(Ease.OutElastic)   // 弹性效果

// 自定义曲线
.SetEase(myAnimationCurve);
```

### 缓动选择指南

| 效果 | 推荐 | 用途 |
|------|------|------|
| 自然移动 | OutQuad | UI、角色移动 |
| 强调效果 | OutBack | 弹窗、按钮 |
| 物理感 | OutBounce | 落地、碰撞 |
| 优雅过渡 | InOutQuad | 淡入淡出 |
| 轻快感 | OutCubic | 快速响应 |

---

## 序列动画 (Sequence)

### 基础序列

```csharp
// 创建序列
var sequence = DOTween.Sequence();

// 依次执行
sequence.Append(transform.DOMoveX(5f, 1f));      // 第1秒
sequence.Append(transform.DOMoveY(3f, 0.5f));    // 第1.5秒
sequence.Append(transform.DOScale(2f, 0.5f));    // 第2秒

// 同时执行
sequence.Append(transform.DOMoveX(5f, 1f));
sequence.Join(transform.DORotate(new Vector3(0, 180, 0), 1f));  // 与上一个同时

// 插入到指定时间点
sequence.Insert(0.5f, transform.DOScale(1.2f, 0.3f));  // 0.5秒时开始

// 添加间隔
sequence.AppendInterval(0.5f);

// 添加回调
sequence.AppendCallback(() => Debug.Log("Step complete"));
```

### 序列控制

```csharp
// 播放控制
sequence.Play();
sequence.Pause();
sequence.Restart();
sequence.Rewind();
sequence.Complete();

// 速度控制
sequence.timeScale = 2f;  // 2倍速

// 循环
sequence.SetLoops(3, LoopType.Yoyo);

// 回调
sequence.OnStart(() => Debug.Log("Started"))
        .OnComplete(() => Debug.Log("Completed"))
        .OnKill(() => Debug.Log("Killed"));
```

---

## 常用代码片段

### 弹窗动画

```csharp
public class Popup : MonoBehaviour
{
    [SerializeField] private float duration = 0.3f;
    private Tween showTween;

    public void Show()
    {
        transform.localScale = Vector3.zero;
        showTween?.Kill();
        showTween = transform.DOScale(1f, duration)
            .SetEase(Ease.OutBack)
            .OnStart(() => gameObject.SetActive(true));
    }

    public void Hide()
    {
        showTween?.Kill();
        showTween = transform.DOScale(0f, duration)
            .SetEase(Ease.InBack)
            .OnComplete(() => gameObject.SetActive(false));
    }

    private void OnDestroy()
    {
        showTween?.Kill();
    }
}
```

### 按钮反馈

```csharp
public class ButtonFeedback : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
{
    [SerializeField] private float pressScale = 0.95f;
    [SerializeField] private float duration = 0.1f;

    private Vector3 originalScale;
    private Tween scaleTween;

    private void Awake()
    {
        originalScale = transform.localScale;
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        scaleTween?.Kill();
        scaleTween = transform.DOScale(originalScale * pressScale, duration)
            .SetEase(Ease.OutQuad);
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        scaleTween?.Kill();
        scaleTween = transform.DOScale(originalScale, duration)
            .SetEase(Ease.OutBack);
    }

    private void OnDestroy()
    {
        scaleTween?.Kill();
    }
}
```

### 循环动画

```csharp
// 呼吸效果
public class BreathingEffect : MonoBehaviour
{
    [SerializeField] private float minScale = 0.9f;
    [SerializeField] private float maxScale = 1.1f;
    [SerializeField] private float duration = 1f;

    private void Start()
    {
        transform.DOScale(maxScale, duration)
            .SetEase(Ease.InOutSine)
            .SetLoops(-1, LoopType.Yoyo);
    }

    private void OnDestroy()
    {
        transform.DOKill();
    }
}

// 浮动效果
public class FloatingEffect : MonoBehaviour
{
    [SerializeField] private float floatHeight = 0.5f;
    [SerializeField] private float duration = 2f;

    private Vector3 originalPos;

    private void Start()
    {
        originalPos = transform.position;
        transform.DOMoveY(originalPos.y + floatHeight, duration)
            .SetEase(Ease.InOutSine)
            .SetLoops(-1, LoopType.Yoyo);
    }

    private void OnDestroy()
    {
        transform.DOKill();
    }
}
```

### 数字滚动

```csharp
public class NumberCounter : MonoBehaviour
{
    [SerializeField] private Text text;
    [SerializeField] private float duration = 1f;

    private int currentValue;
    private Tween countTween;

    public void SetNumber(int targetValue)
    {
        countTween?.Kill();
        countTween = DOTween.To(
            () => currentValue,
            x => {
                currentValue = x;
                text.text = x.ToString("N0");  // 格式化：1,000
            },
            targetValue,
            duration
        ).SetEase(Ease.OutQuad);
    }

    private void OnDestroy()
    {
        countTween?.Kill();
    }
}
```

### 进度条动画

```csharp
public class ProgressBar : MonoBehaviour
{
    [SerializeField] private Image fillImage;
    [SerializeField] private float duration = 0.5f;

    private Tween fillTween;

    public void SetProgress(float value, bool animated = true)
    {
        fillTween?.Kill();

        if (animated)
        {
            fillTween = fillImage.DOFillAmount(value, duration)
                .SetEase(Ease.OutQuad);
        }
        else
        {
            fillImage.fillAmount = value;
        }
    }

    public void SetColor(Color color)
    {
        fillImage.DOColor(color, duration);
    }

    private void OnDestroy()
    {
        fillTween?.Kill();
    }
}
```

### 摄像机震动

```csharp
public class CameraShake : MonoBehaviour
{
    [SerializeField] private float intensity = 0.5f;
    [SerializeField] private float duration = 0.3f;

    private Vector3 originalPos;

    private void Awake()
    {
        originalPos = transform.localPosition;
    }

    public void Shake(float? customIntensity = null, float? customDuration = null)
    {
        transform.DOComplete();
        transform.DOShakePosition(
            customDuration ?? duration,
            customIntensity ?? intensity,
            vibrato: 10,
            randomness: 90,
            snapping: false,
            fadeOut: true
        ).OnComplete(() => transform.localPosition = originalPos);
    }
}
```

---

## 性能优化

### Tween复用

```csharp
// 复用Tween减少GC
public class TweenReuse : MonoBehaviour
{
    private Tween scaleTween;
    private Vector3 targetScale = Vector3.one;

    private void Awake()
    {
        scaleTween = transform.DOScale(targetScale, 0.3f)
            .SetAutoKill(false)      // 不自动销毁
            .SetRecyclable(true)     // 可回收
            .Pause();                // 初始暂停
    }

    public void AnimateScale(Vector3 target)
    {
        targetScale = target;
        scaleTween.ChangeEndValue(target, true).Restart();
    }

    private void OnDestroy()
    {
        scaleTween?.Kill();
    }
}
```

### 批量操作

```csharp
// 使用DOTween.KillAll清理
void OnDestroy()
{
    transform.DOKill();           // 清理该Transform的所有Tween
    DOTween.Kill(this);           // 清理该对象为target的所有Tween
}

// 暂停/恢复所有
DOTween.PauseAll();
DOTween.PlayAll();

// 使用ID管理
transform.DOMoveX(5f, 1f).SetId("MoveGroup");
DOTween.Pause("MoveGroup");
DOTween.Kill("MoveGroup");
```

### 安全模式

```csharp
// 初始化时启用安全模式
DOTween.Init(true, true, LogBehaviour.ErrorsOnly);

// 安全模式下，如果target为null，Tween会被自动Kill
// 避免空引用异常
```

---

## 常见问题

### Q: 如何让动画忽略Time.scale？

```csharp
transform.DOMove(target, 1f)
    .SetUpdate(true);  // 使用unscaledDeltaTime
```

### Q: 如何在动画中执行代码？

```csharp
transform.DOMove(target, 1f)
    .OnStart(() => Debug.Log("开始"))
    .OnUpdate(() => Debug.Log("更新中"))
    .OnComplete(() => Debug.Log("完成"))
    .OnKill(() => Debug.Log("被Kill"));
```

### Q: 如何延迟执行？

```csharp
// 方法1: DOVirtual.DelayedCall
DOVirtual.DelayedCall(1f, () => Debug.Log("1秒后执行"));

// 方法2: 序列动画
var seq = DOTween.Sequence();
seq.AppendInterval(1f);
seq.AppendCallback(() => Debug.Log("1秒后执行"));

// 方法3: 设置延迟
transform.DOMove(target, 1f).SetDelay(1f);
```

### Q: 如何中途改变动画目标？

```csharp
Tween tween = transform.DOMove(targetA, 5f);
// 2秒后改变目标
tween.ChangeEndValue(targetB, true);  // true = 计算剩余时间
```

---

## 最佳实践

### DO ✅

- 使用SafeMode防止空引用
- 复用Tween减少GC
- 在OnDestroy中Kill Tween
- 使用Sequence组织复杂动画
- 为需要管理的Tween设置Id

### DON'T ❌

- 不要在Update中创建Tween
- 不要忘记Kill导致内存泄漏
- 不要在回调中直接引用this（可能导致泄漏）
- 不要使用过长的动画时长

---

## 相关链接

- 官方文档: [DOTween Documentation](http://dotween.demigiant.com/documentation.php)
- 代码片段: [DOTween常用动画](【代码片段】DOTween常用动画.md)
- 动画系统: [动画系统](../20_核心系统/21_动画系统/)
