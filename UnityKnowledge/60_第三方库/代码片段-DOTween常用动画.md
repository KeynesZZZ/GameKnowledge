# 代码片段 - DOTween常用动画

> 可复用的DOTween动画效果库 `#第三方库` `#动画` `#代码片段`

## 弹出动画

### 缩放弹出

```csharp
public static class DOTweenExtensions
{
    /// <summary>
    /// 弹出动画 - 从0缩放到目标大小
    /// </summary>
    public static Tween DOPopOut(this Transform transform, float duration = 0.3f, Ease ease = Ease.OutBack)
    {
        transform.localScale = Vector3.zero;
        return transform.DOScale(1f, duration).SetEase(ease);
    }

    /// <summary>
    /// 收回动画 - 缩放到0
    /// </summary>
    public static Tween DOPopIn(this Transform transform, float duration = 0.2f, Ease ease = Ease.InBack)
    {
        return transform.DOScale(0f, duration).SetEase(ease);
    }

    /// <summary>
    /// 弹跳弹出
    /// </summary>
    public static Tween DOBounceOut(this Transform transform, float duration = 0.5f)
    {
        transform.localScale = Vector3.zero;
        return transform.DOScale(1f, duration).SetEase(Ease.OutBounce);
    }
}

// 使用
transform.DOPopOut();
await transform.DOPopIn().AsyncWaitForCompletion();
```

### 弹窗动画

```csharp
public class PopupAnimation : MonoBehaviour
{
    [Header("Animation Settings")]
    [SerializeField] private float showDuration = 0.3f;
    [SerializeField] private float hideDuration = 0.2f;
    [SerializeField] private Ease showEase = Ease.OutBack;
    [SerializeField] private Ease hideEase = Ease.InBack;

    private Tween currentTween;

    public Tween Show()
    {
        currentTween?.Kill();
        gameObject.SetActive(true);
        transform.localScale = Vector3.zero;

        currentTween = transform.DOScale(1f, showDuration)
            .SetEase(showEase)
            .SetUpdate(true);

        return currentTween;
    }

    public async UniTask ShowAsync()
    {
        await Show().AsyncWaitForCompletion();
    }

    public Tween Hide()
    {
        currentTween?.Kill();

        currentTween = transform.DOScale(0f, hideDuration)
            .SetEase(hideEase)
            .SetUpdate(true)
            .OnComplete(() => gameObject.SetActive(false));

        return currentTween;
    }

    public async UniTask HideAsync()
    {
        await Hide().AsyncWaitForCompletion();
    }

    private void OnDestroy()
    {
        currentTween?.Kill();
    }
}
```

---

## UI反馈动画

### 按钮点击

```csharp
public class ButtonAnimation : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
{
    [Header("Settings")]
    [SerializeField] private float pressedScale = 0.9f;
    [SerializeField] private float duration = 0.1f;

    private Vector3 originalScale;
    private Tween scaleTween;
    private bool isPressed;

    private void Awake()
    {
        originalScale = transform.localScale;
    }

    public void OnPointerDown(PointerEventData eventData)
    {
        isPressed = true;
        scaleTween?.Kill();
        scaleTween = transform.DOScale(originalScale * pressedScale, duration)
            .SetEase(Ease.OutQuad);
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        if (!isPressed) return;
        isPressed = false;
        PlayReleaseAnimation();
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        if (!isPressed) return;
        isPressed = false;
        PlayReleaseAnimation();
    }

    private void PlayReleaseAnimation()
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

### 悬停效果

```csharp
public class HoverAnimation : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    [Header("Settings")]
    [SerializeField] private float hoverScale = 1.1f;
    [SerializeField] private float duration = 0.2f;

    private Vector3 originalScale;
    private Tween scaleTween;

    private void Awake()
    {
        originalScale = transform.localScale;
    }

    public void OnPointerEnter(PointerEventData eventData)
    {
        scaleTween?.Kill();
        scaleTween = transform.DOScale(originalScale * hoverScale, duration)
            .SetEase(Ease.OutQuad);
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        scaleTween?.Kill();
        scaleTween = transform.DOScale(originalScale, duration)
            .SetEase(Ease.OutQuad);
    }

    private void OnDestroy()
    {
        scaleTween?.Kill();
    }
}
```

---

## 循环动画

### 呼吸效果

```csharp
public static class BreathingAnimation
{
    public static Tween Play(Transform transform, float minScale = 0.95f, float maxScale = 1.05f, float duration = 1f)
    {
        return transform.DOScale(maxScale, duration)
            .SetEase(Ease.InOutSine)
            .SetLoops(-1, LoopType.Yoyo);
    }
}

// 使用
private Tween breathingTween;

void Start()
{
    breathingTween = BreathingAnimation.Play(transform);
}

void OnDestroy()
{
    breathingTween?.Kill();
}
```

### 浮动效果

```csharp
public class FloatingAnimation : MonoBehaviour
{
    [SerializeField] private float floatHeight = 10f;
    [SerializeField] private float duration = 2f;
    [SerializeField] private bool playOnStart = true;

    private Vector3 originalPos;
    private Tween floatTween;

    private void Start()
    {
        originalPos = transform.localPosition;

        if (playOnStart)
        {
            Play();
        }
    }

    public void Play()
    {
        floatTween?.Kill();
        floatTween = transform.DOLocalMoveY(originalPos.y + floatHeight, duration)
            .SetEase(Ease.InOutSine)
            .SetLoops(-1, LoopType.Yoyo);
    }

    public void Stop()
    {
        floatTween?.Kill();
        transform.localPosition = originalPos;
    }

    private void OnDestroy()
    {
        floatTween?.Kill();
    }
}
```

### 旋转动画

```csharp
public static class RotateAnimation
{
    /// <summary>
    /// 持续旋转
    /// </summary>
    public static Tween Spin(Transform transform, float duration = 1f, RotateMode mode = RotateMode.FastBeyond360)
    {
        return transform.DORotate(new Vector3(0, 0, 360), duration, mode)
            .SetEase(Ease.Linear)
            .SetLoops(-1, LoopType.Restart);
    }

    /// <summary>
    /// 摆动旋转
    /// </summary>
    public static Tween Wiggle(Transform transform, float angle = 15f, float duration = 0.5f)
    {
        return transform.DORotate(new Vector3(0, 0, angle), duration)
            .SetEase(Ease.InOutSine)
            .SetLoops(-1, LoopType.Yoyo);
    }
}

// 使用
RotateAnimation.Spin(transform, 2f);
RotateAnimation.Wiggle(transform, 10f, 0.3f);
```

---

## 特效动画

### 震动效果

```csharp
public static class ShakeEffects
{
    /// <summary>
    /// 位置震动
    /// </summary>
    public static Tween Shake(Transform transform, float duration = 0.5f, float strength = 0.5f, int vibrato = 10)
    {
        return transform.DOShakePosition(duration, strength, vibrato);
    }

    /// <summary>
    /// 旋转震动
    /// </summary>
    public static Tween ShakeRotation(Transform transform, float duration = 0.5f, float strength = 10f)
    {
        return transform.DOShakeRotation(duration, new Vector3(0, 0, strength));
    }

    /// <summary>
    /// 缩放震动
    /// </summary>
    public static Tween ShakeScale(Transform transform, float duration = 0.3f, float strength = 0.1f)
    {
        return transform.DOShakeScale(duration, strength);
    }
}

// 使用
ShakeEffects.Shake(cameraTransform, 0.3f, 0.2f);
ShakeEffects.ShakeScale(buttonTransform, 0.2f, 0.1f);
```

### 冲击效果

```csharp
public static class PunchEffects
{
    /// <summary>
    /// 位置冲击
    /// </summary>
    public static Tween PunchPosition(Transform transform, Vector3 punch, float duration = 0.5f, int vibrato = 10, float elasticity = 1f)
    {
        return transform.DOPunchPosition(punch, duration, vibrato, elasticity);
    }

    /// <summary>
    /// 缩放冲击
    /// </summary>
    public static Tween PunchScale(Transform transform, Vector3 punch, float duration = 0.5f)
    {
        return transform.DOPunchScale(punch, duration);
    }

    /// <summary>
    /// 旋转冲击
    /// </summary>
    public static Tween PunchRotation(Transform transform, Vector3 punch, float duration = 0.5f)
    {
        return transform.DOPunchRotation(punch, duration);
    }
}

// 使用 - 点击时弹跳
PunchEffects.PunchScale(buttonTransform, Vector3.one * 0.2f, 0.3f);
```

---

## 过渡动画

### 淡入淡出

```csharp
public static class FadeEffects
{
    /// <summary>
    /// 淡入CanvasGroup
    /// </summary>
    public static Tween FadeIn(CanvasGroup group, float duration = 0.3f)
    {
        group.alpha = 0f;
        group.blocksRaycasts = true;
        return group.DOFade(1f, duration)
            .SetEase(Ease.OutQuad)
            .OnComplete(() => group.interactable = true);
    }

    /// <summary>
    /// 淡出CanvasGroup
    /// </summary>
    public static Tween FadeOut(CanvasGroup group, float duration = 0.3f)
    {
        group.interactable = false;
        return group.DOFade(0f, duration)
            .SetEase(Ease.OutQuad)
            .OnComplete(() => group.blocksRaycasts = false);
    }

    /// <summary>
    /// 淡入Image
    /// </summary>
    public static Tween FadeIn(Image image, float duration = 0.3f)
    {
        var color = image.color;
        color.a = 0f;
        image.color = color;
        return image.DOFade(1f, duration);
    }

    /// <summary>
    /// 淡入Text
    /// </summary>
    public static Tween FadeIn(Text text, float duration = 0.3f)
    {
        var color = text.color;
        color.a = 0f;
        text.color = color;
        return text.DOFade(1f, duration);
    }
}
```

### 滑动动画

```csharp
public static class SlideEffects
{
    /// <summary>
    /// 从左侧滑入
    /// </summary>
    public static Tween SlideFromLeft(RectTransform rect, float duration = 0.3f, float offset = -500f)
    {
        var targetPos = rect.anchoredPosition;
        rect.anchoredPosition = new Vector2(offset, targetPos.y);
        return rect.DOAnchorPos(targetPos, duration).SetEase(Ease.OutQuad);
    }

    /// <summary>
    /// 从右侧滑入
    /// </summary>
    public static Tween SlideFromRight(RectTransform rect, float duration = 0.3f, float offset = 500f)
    {
        var targetPos = rect.anchoredPosition;
        rect.anchoredPosition = new Vector2(offset, targetPos.y);
        return rect.DOAnchorPos(targetPos, duration).SetEase(Ease.OutQuad);
    }

    /// <summary>
    /// 从上方滑入
    /// </summary>
    public static Tween SlideFromTop(RectTransform rect, float duration = 0.3f, float offset = 500f)
    {
        var targetPos = rect.anchoredPosition;
        rect.anchoredPosition = new Vector2(targetPos.x, offset);
        return rect.DOAnchorPos(targetPos, duration).SetEase(Ease.OutQuad);
    }

    /// <summary>
    /// 从下方滑入
    /// </summary>
    public static Tween SlideFromBottom(RectTransform rect, float duration = 0.3f, float offset = -500f)
    {
        var targetPos = rect.anchoredPosition;
        rect.anchoredPosition = new Vector2(targetPos.x, offset);
        return rect.DOAnchorPos(targetPos, duration).SetEase(Ease.OutQuad);
    }
}
```

---

## 数值动画

### 数字滚动

```csharp
public class NumberRollAnimation : MonoBehaviour
{
    [SerializeField] private Text text;
    [SerializeField] private float duration = 0.5f;
    [SerializeField] private string format = "N0";

    private int currentValue;
    private Tween rollTween;

    public void SetValue(int value, bool animated = true)
    {
        rollTween?.Kill();

        if (animated)
        {
            rollTween = DOTween.To(
                () => currentValue,
                x => {
                    currentValue = x;
                    text.text = x.ToString(format);
                },
                value,
                duration
            ).SetEase(Ease.OutQuad);
        }
        else
        {
            currentValue = value;
            text.text = value.ToString(format);
        }
    }

    private void OnDestroy()
    {
        rollTween?.Kill();
    }
}
```

### 进度条动画

```csharp
public class ProgressAnimation : MonoBehaviour
{
    [SerializeField] private Image fillImage;
    [SerializeField] private Text percentText;
    [SerializeField] private float duration = 0.3f;

    private Tween fillTween;

    public void SetProgress(float value)
    {
        fillTween?.Kill();
        fillTween = fillImage.DOFillAmount(value, duration)
            .SetEase(Ease.OutQuad);

        if (percentText != null)
        {
            float currentPercent = fillImage.fillAmount * 100;
            DOTween.To(
                () => currentPercent,
                x => percentText.text = $"{x:F0}%",
                value * 100,
                duration
            );
        }
    }

    private void OnDestroy()
    {
        fillTween?.Kill();
    }
}
```

---

## 序列动画模板

### 依次出现

```csharp
public static class SequenceEffects
{
    /// <summary>
    /// 子物体依次弹出
    /// </summary>
    public static Sequence StaggerPopOut(Transform parent, float delay = 0.1f, float duration = 0.3f)
    {
        var sequence = DOTween.Sequence();

        for (int i = 0; i < parent.childCount; i++)
        {
            var child = parent.GetChild(i);
            child.localScale = Vector3.zero;

            sequence.Insert(i * delay, child.DOScale(1f, duration).SetEase(Ease.OutBack));
        }

        return sequence;
    }

    /// <summary>
    /// 子物体依次淡入
    /// </summary>
    public static Sequence StaggerFadeIn(Transform parent, float delay = 0.05f, float duration = 0.2f)
    {
        var sequence = DOTween.Sequence();

        for (int i = 0; i < parent.childCount; i++)
        {
            var canvasGroup = parent.GetChild(i).GetComponent<CanvasGroup>();
            if (canvasGroup != null)
            {
                canvasGroup.alpha = 0f;
                sequence.Insert(i * delay, canvasGroup.DOFade(1f, duration));
            }
        }

        return sequence;
    }
}

// 使用
await SequenceEffects.StaggerPopOut(container).AsyncWaitForCompletion();
```

---

## 相关链接

- [DOTween 深度使用](DOTween%20深度使用.md)
- [动画系统](../20_核心系统/动画系统/)
