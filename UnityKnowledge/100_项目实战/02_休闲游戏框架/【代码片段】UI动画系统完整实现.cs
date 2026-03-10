// ============================================================================
// UI动画系统完整实现
// ============================================================================
// 包含以下核心类:
// 1. UIAnimType      - 动画类型枚举
// 2. UIAnimClip      - 动画片段定义 + 工厂方法
// 3. UIAnimNode      - 动画节点树结构
// 4. UIAnimConfig    - 显示/隐藏动画配置
// 5. UIComplexAnimator - 动画执行器
// 6. UIAnimator      - 高层API封装
//
// 依赖: DOTween, UniTask, TextMeshPro
// Unity版本: 2021.3+
// ============================================================================

using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using DG.Tweening;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Game.UI
{
    #region 枚举定义

    /// <summary>
    /// 动画类型枚举
    /// </summary>
    public enum UIAnimType
    {
        // 透明度
        Fade,
        Alpha,

        // 缩放
        Scale,
        ScaleX,
        ScaleY,
        ScaleZ,
        PunchScale,
        ShakeScale,

        // 移动
        Move,
        MoveX,
        MoveY,
        MoveFrom,
        PunchPosition,
        ShakePosition,

        // 旋转
        Rotate,
        RotateX,
        RotateY,
        RotateZ,
        PunchRotation,
        ShakeRotation,

        // 颜色
        Color,
        Gradient,

        // 文字
        TextColor,
        TextAlpha,
        TextFontSize,
        TextMaxVisible,
        TextCount,          // 数字滚动
        Typewriter,         // 打字机效果

        // 进度
        FillAmount,
        SliderValue,

        // 路径
        Path,
        PathConstantSpeed,

        // 材质
        MaterialColor,
        MaterialFloat,

        // 控制
        Callback,
        Delay
    }

    /// <summary>
    /// 动画节点类型
    /// </summary>
    public enum UIAnimNodeType
    {
        Single,     // 单一动画
        Sequence,   // 序列（依次播放）
        Parallel    // 并行（同时播放）
    }

    #endregion

    #region UIAnimClip - 动画片段

    /// <summary>
    /// 动画片段（不可变结构体）
    /// 包含单个动画的所有配置信息
    /// </summary>
    public readonly struct UIAnimClip
    {
        /// <summary>动画类型</summary>
        public UIAnimType Type { get; }

        /// <summary>持续时间（秒）</summary>
        public float Duration { get; }

        /// <summary>缓动类型</summary>
        public Ease EaseType { get; }

        /// <summary>结束值（类型根据动画类型而定）</summary>
        public object EndValue { get; }

        /// <summary>起始值（可选）</summary>
        public object StartValue { get; }

        /// <summary>目标路径（相对于当前RectTransform）</summary>
        public string TargetPath { get; }

        /// <summary>循环次数（-1为无限循环）</summary>
        public int Loops { get; }

        /// <summary>循环类型</summary>
        public LoopType LoopType { get; }

        /// <summary>回调函数</summary>
        public Action Callback { get; }

        /// <summary>是否相对变化</summary>
        public bool IsRelative { get; }

        /// <summary>震动强度（用于Shake类型）</summary>
        public float ShakeStrength { get; }

        /// <summary>震动振动次数</summary>
        public int ShakeVibrato { get; }

        /// <summary>路径点（用于Path动画）</summary>
        public Vector3[] PathWaypoints { get; }

        /// <summary>路径类型</summary>
        public PathMode PathMode { get; }

        /// <summary>路径分辨率</summary>
        public PathType PathType { get; }

        public UIAnimClip(
            UIAnimType type,
            float duration,
            Ease easeType = Ease.Linear,
            object endValue = null,
            object startValue = null,
            string targetPath = null,
            int loops = 1,
            LoopType loopType = LoopType.Restart,
            Action callback = null,
            bool isRelative = false,
            float shakeStrength = 10f,
            int shakeVibrato = 10,
            Vector3[] pathWaypoints = null,
            PathMode pathMode = PathMode.Full3D,
            PathType pathType = PathType.CatmullRom)
        {
            Type = type;
            Duration = duration;
            EaseType = easeType;
            EndValue = endValue;
            StartValue = startValue;
            TargetPath = targetPath;
            Loops = loops;
            LoopType = loopType;
            Callback = callback;
            IsRelative = isRelative;
            ShakeStrength = shakeStrength;
            ShakeVibrato = shakeVibrato;
            PathWaypoints = pathWaypoints;
            PathMode = pathMode;
            PathType = pathType;
        }

        /// <summary>设置目标路径</summary>
        public UIAnimClip WithTarget(string path) =>
            new UIAnimClip(Type, Duration, EaseType, EndValue, StartValue, path,
                Loops, LoopType, Callback, IsRelative, ShakeStrength, ShakeVibrato,
                PathWaypoints, PathMode, PathType);

        /// <summary>设置缓动类型</summary>
        public UIAnimClip WithEase(Ease ease) =>
            new UIAnimClip(Type, Duration, ease, EndValue, StartValue, TargetPath,
                Loops, LoopType, Callback, IsRelative, ShakeStrength, ShakeVibrato,
                PathWaypoints, PathMode, PathType);

        /// <summary>设置循环</summary>
        public UIAnimClip WithLoops(int loops, LoopType loopType = LoopType.Restart) =>
            new UIAnimClip(Type, Duration, EaseType, EndValue, StartValue, TargetPath,
                loops, loopType, Callback, IsRelative, ShakeStrength, ShakeVibrato,
                PathWaypoints, PathMode, PathType);

        /// <summary>设置回调</summary>
        public UIAnimClip WithCallback(Action callback) =>
            new UIAnimClip(Type, Duration, EaseType, EndValue, StartValue, TargetPath,
                Loops, LoopType, callback, IsRelative, ShakeStrength, ShakeVibrato,
                PathWaypoints, PathMode, PathType);

        #region 工厂方法 - 透明度

        /// <summary>透明度渐变到目标值</summary>
        public static UIAnimClip Fade(float endAlpha, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Fade, duration, ease, endAlpha);

        /// <summary>透明度从start到end</summary>
        public static UIAnimClip FadeFromTo(float startAlpha, float endAlpha, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Fade, duration, ease, endAlpha, startAlpha);

        /// <summary>淡入（0→1）</summary>
        public static UIAnimClip FadeIn(float duration, Ease ease = Ease.Linear) =>
            FadeFromTo(0f, 1f, duration, ease);

        /// <summary>淡出（1→0）</summary>
        public static UIAnimClip FadeOut(float duration, Ease ease = Ease.Linear) =>
            FadeFromTo(1f, 0f, duration, ease);

        #endregion

        #region 工厂方法 - 缩放

        /// <summary>缩放到目标值</summary>
        public static UIAnimClip Scale(Vector3 endScale, float duration, Ease ease = Ease.OutBack) =>
            new UIAnimClip(UIAnimType.Scale, duration, ease, endScale);

        /// <summary>缩放到统一值</summary>
        public static UIAnimClip Scale(float uniformScale, float duration, Ease ease = Ease.OutBack) =>
            Scale(new Vector3(uniformScale, uniformScale, uniformScale), duration, ease);

        /// <summary>从0缩放到1</summary>
        public static UIAnimClip ScaleFromZero(float duration, Ease ease = Ease.OutBack) =>
            new UIAnimClip(UIAnimType.Scale, duration, ease, Vector3.one, Vector3.zero);

        /// <summary>缩放到0</summary>
        public static UIAnimClip ScaleToZero(float duration, Ease ease = Ease.InBack) =>
            new UIAnimClip(UIAnimType.Scale, duration, ease, Vector3.zero, null);

        /// <summary>缩放X轴</summary>
        public static UIAnimClip ScaleX(float endX, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.ScaleX, duration, ease, endX);

        /// <summary>缩放Y轴</summary>
        public static UIAnimClip ScaleY(float endY, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.ScaleY, duration, ease, endY);

        /// <summary>缩放冲击效果</summary>
        public static UIAnimClip PunchScale(Vector3 punch, float duration, int vibrato = 10) =>
            new UIAnimClip(UIAnimType.PunchScale, duration, Ease.Linear, punch,
                isRelative: true, shakeVibrato: vibrato);

        /// <summary>缩放震动效果</summary>
        public static UIAnimClip ShakeScale(float strength, float duration, int vibrato = 10) =>
            new UIAnimClip(UIAnimType.ShakeScale, duration, Ease.Linear, null,
                shakeStrength: strength, shakeVibrato: vibrato);

        #endregion

        #region 工厂方法 - 移动

        /// <summary>移动到目标位置</summary>
        public static UIAnimClip Move(Vector2 endPos, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.Move, duration, ease, endPos);

        /// <summary>移动X轴</summary>
        public static UIAnimClip MoveX(float endX, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveX, duration, ease, endX);

        /// <summary>移动Y轴</summary>
        public static UIAnimClip MoveY(float endY, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveY, duration, ease, endY);

        /// <summary>从指定位置移动到当前位置</summary>
        public static UIAnimClip MoveFrom(Vector2 startPos, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveFrom, duration, ease, null, startPos);

        /// <summary>从左侧滑入</summary>
        public static UIAnimClip SlideInFromLeft(float offset, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveFrom, duration, ease, null, new Vector2(-offset, 0));

        /// <summary>从右侧滑入</summary>
        public static UIAnimClip SlideInFromRight(float offset, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveFrom, duration, ease, null, new Vector2(offset, 0));

        /// <summary>从上方滑入</summary>
        public static UIAnimClip SlideInFromTop(float offset, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveFrom, duration, ease, null, new Vector2(0, offset));

        /// <summary>从下方滑入</summary>
        public static UIAnimClip SlideInFromBottom(float offset, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.MoveFrom, duration, ease, null, new Vector2(0, -offset));

        /// <summary>位置冲击效果</summary>
        public static UIAnimClip PunchPosition(Vector2 punch, float duration, int vibrato = 10) =>
            new UIAnimClip(UIAnimType.PunchPosition, duration, Ease.Linear, punch,
                isRelative: true, shakeVibrato: vibrato);

        /// <summary>位置震动效果</summary>
        public static UIAnimClip Shake(float strength, float duration, int vibrato = 10) =>
            new UIAnimClip(UIAnimType.ShakePosition, duration, Ease.Linear, null,
                shakeStrength: strength, shakeVibrato: vibrato);

        #endregion

        #region 工厂方法 - 旋转

        /// <summary>旋转到目标角度</summary>
        public static UIAnimClip Rotate(Vector3 endRotation, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Rotate, duration, ease, endRotation);

        /// <summary>绕Z轴旋转</summary>
        public static UIAnimClip RotateZ(float endZ, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.RotateZ, duration, ease, endZ);

        /// <summary>无限旋转（spin）</summary>
        public static UIAnimClip Spin(float duration, int direction = 1) =>
            new UIAnimClip(UIAnimType.RotateZ, duration, Ease.Linear,
                direction > 0 ? 360f : -360f, isRelative: true, loops: -1);

        /// <summary>旋转冲击效果</summary>
        public static UIAnimClip PunchRotation(Vector3 punch, float duration, int vibrato = 10) =>
            new UIAnimClip(UIAnimType.PunchRotation, duration, Ease.Linear, punch,
                isRelative: true, shakeVibrato: vibrato);

        #endregion

        #region 工厂方法 - 颜色

        /// <summary>颜色渐变</summary>
        public static UIAnimClip Color(Color endColor, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Color, duration, ease, endColor);

        /// <summary>颜色从start到end</summary>
        public static UIAnimClip ColorFromTo(Color startColor, Color endColor, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Color, duration, ease, endColor, startColor);

        /// <summary>渐变颜色</summary>
        public static UIAnimClip Gradient(Gradient gradient, float duration) =>
            new UIAnimClip(UIAnimType.Gradient, duration, Ease.Linear, gradient);

        #endregion

        #region 工厂方法 - 文字

        /// <summary>文字颜色</summary>
        public static UIAnimClip TextColor(Color endColor, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.TextColor, duration, ease, endColor);

        /// <summary>文字透明度</summary>
        public static UIAnimClip TextAlpha(float endAlpha, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.TextAlpha, duration, ease, endAlpha);

        /// <summary>打字机效果</summary>
        public static UIAnimClip Typewriter(float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.Typewriter, duration, ease);

        /// <summary>数字滚动（从start到end）</summary>
        public static UIAnimClip TextCount(int start, int end, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.TextCount, duration, ease, end, start);

        /// <summary>文字大小</summary>
        public static UIAnimClip TextFontSize(float endSize, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.TextFontSize, duration, ease, endSize);

        #endregion

        #region 工厂方法 - 进度

        /// <summary>填充量（Image）</summary>
        public static UIAnimClip FillAmount(float endValue, float duration, Ease ease = Ease.Linear) =>
            new UIAnimClip(UIAnimType.FillAmount, duration, ease, endValue);

        /// <summary>滑动条值</summary>
        public static UIAnimClip SliderValue(float endValue, float duration, Ease ease = Ease.OutQuad) =>
            new UIAnimClip(UIAnimType.SliderValue, duration, ease, endValue);

        #endregion

        #region 工厂方法 - 路径

        /// <summary>沿路径移动</summary>
        public static UIAnimClip Path(Vector3[] waypoints, float duration, PathType pathType = PathType.CatmullRom) =>
            new UIAnimClip(UIAnimType.Path, duration, Ease.Linear, waypoints, pathType: pathType);

        #endregion

        #region 工厂方法 - 控制

        /// <summary>延迟</summary>
        public static UIAnimClip Delay(float duration) =>
            new UIAnimClip(UIAnimType.Delay, duration);

        /// <summary>回调</summary>
        public static UIAnimClip Callback(Action callback) =>
            new UIAnimClip(UIAnimType.Callback, 0f, callback: callback);

        #endregion
    }

    #endregion

    #region UIAnimNode - 动画节点

    /// <summary>
    /// 动画节点（树结构）
    /// 支持 Single/Sequence/Parallel 三种类型
    /// </summary>
    public class UIAnimNode
    {
        /// <summary>节点类型</summary>
        public UIAnimNodeType NodeType { get; }

        /// <summary>动画片段（仅Single类型有效）</summary>
        public UIAnimClip? Clip { get; }

        /// <summary>子节点列表（仅Sequence/Parallel类型有效）</summary>
        public List<UIAnimNode> Children { get; }

        /// <summary>节点名称（用于调试）</summary>
        public string Name { get; set; }

        private UIAnimNode(UIAnimNodeType nodeType, UIAnimClip? clip = null, string name = null)
        {
            NodeType = nodeType;
            Clip = clip;
            Children = new List<UIAnimNode>();
            Name = name ?? nodeType.ToString();
        }

        #region 工厂方法

        /// <summary>创建单一动画节点</summary>
        public static UIAnimNode Single(UIAnimClip clip, string name = null) =>
            new UIAnimNode(UIAnimNodeType.Single, clip, name);

        /// <summary>创建序列节点（依次播放）</summary>
        public static UIAnimNode Sequence(params UIAnimNode[] children)
        {
            var node = new UIAnimNode(UIAnimNodeType.Sequence, name: "Sequence");
            node.Children.AddRange(children);
            return node;
        }

        /// <summary>创建并行节点（同时播放）</summary>
        public static UIAnimNode Parallel(params UIAnimNode[] children)
        {
            var node = new UIAnimNode(UIAnimNodeType.Parallel, name: "Parallel");
            node.Children.AddRange(children);
            return node;
        }

        #endregion

        #region 链式方法

        /// <summary>添加子节点</summary>
        public UIAnimNode AddChild(UIAnimNode child)
        {
            Children.Add(child);
            return this;
        }

        /// <summary>设置名称</summary>
        public UIAnimNode WithName(string name)
        {
            Name = name;
            return this;
        }

        #endregion
    }

    #endregion

    #region UIAnimConfig - 动画配置

    /// <summary>
    /// UI动画配置（用于Show/Hide动画）
    /// </summary>
    [Serializable]
    public class UIAnimConfig
    {
        /// <summary>动画节点</summary>
        public UIAnimNode AnimNode { get; set; }

        /// <summary>预设名称</summary>
        public string PresetName { get; set; }

        /// <summary>是否播放动画</summary>
        public bool PlayAnimation { get; set; } = true;

        /// <summary>动画时长缩放（用于统一调整速度）</summary>
        public float TimeScale { get; set; } = 1f;

        /// <summary>创建默认配置（无动画）</summary>
        public static UIAnimConfig None => new UIAnimConfig { PlayAnimation = false };

        /// <summary>创建淡入动画配置</summary>
        public static UIAnimConfig FadeIn(float duration = 0.3f) =>
            new UIAnimConfig
            {
                AnimNode = UIAnimNode.Single(UIAnimClip.FadeIn(duration))
            };

        /// <summary>创建淡出动画配置</summary>
        public static UIAnimConfig FadeOut(float duration = 0.3f) =>
            new UIAnimConfig
            {
                AnimNode = UIAnimNode.Single(UIAnimClip.FadeOut(duration))
            };

        /// <summary>创建弹窗出现动画（淡入+缩放）</summary>
        public static UIAnimConfig PopupShow(float duration = 0.3f) =>
            new UIAnimConfig
            {
                AnimNode = UIAnimNode.Parallel(
                    UIAnimNode.Single(UIAnimClip.FadeIn(duration * 0.7f)),
                    UIAnimNode.Single(UIAnimClip.ScaleFromZero(duration).WithEase(Ease.OutBack))
                )
            };

        /// <summary>创建弹窗关闭动画（淡出+缩放）</summary>
        public static UIAnimConfig PopupHide(float duration = 0.2f) =>
            new UIAnimConfig
            {
                AnimNode = UIAnimNode.Parallel(
                    UIAnimNode.Single(UIAnimClip.FadeOut(duration)),
                    UIAnimNode.Single(UIAnimClip.ScaleToZero(duration).WithEase(Ease.InBack))
                )
            };

        /// <summary>创建滑入动画</summary>
        public static UIAnimConfig SlideIn(float offset, float duration = 0.3f, Ease ease = Ease.OutQuad) =>
            new UIAnimConfig
            {
                AnimNode = UIAnimNode.Parallel(
                    UIAnimNode.Single(UIAnimClip.FadeIn(duration * 0.5f)),
                    UIAnimNode.Single(UIAnimClip.SlideInFromLeft(offset, duration, ease))
                )
            };
    }

    #endregion

    #region UIComplexAnimator - 动画执行器

    /// <summary>
    /// 复杂动画执行器
    /// 将UIAnimNode树转换为DOTween Tweens并执行
    /// </summary>
    public static class UIComplexAnimator
    {
        // 存储当前播放的Tweens（用于停止/暂停）
        private static readonly Dictionary<RectTransform, List<Tween>> _activeTweens = new();

        #region 公开API

        /// <summary>
        /// 播放动画
        /// </summary>
        /// <param name="target">目标RectTransform</param>
        /// <param name="node">动画节点</param>
        /// <param name="ct">取消令牌</param>
        public static async UniTask PlayAsync(RectTransform target, UIAnimNode node, CancellationToken ct = default)
        {
            if (node == null || target == null) return;

            try
            {
                var tcs = new UniTaskCompletionSource();

                // 创建Tweens
                var tweens = CreateTweens(target, node);

                // 存储活跃的Tweens
                if (!_activeTweens.ContainsKey(target))
                    _activeTweens[target] = new List<Tween>();
                _activeTweens[target].AddRange(tweens);

                // 注册取消
                ct.Register(() =>
                {
                    KillTweens(target);
                    tcs.TrySetCanceled();
                });

                // 最后一个Tween完成时触发完成
                if (tweens.Count > 0)
                {
                    var lastTween = tweens[tweens.Count - 1];
                    lastTween.OnComplete(() =>
                    {
                        CleanupTweens(target);
                        tcs.TrySetResult();
                    });
                }
                else
                {
                    tcs.TrySetResult();
                }

                await tcs.Task;
            }
            catch (OperationCanceledException)
            {
                KillTweens(target);
                throw;
            }
        }

        /// <summary>
        /// 停止目标上的所有动画
        /// </summary>
        public static void Stop(RectTransform target)
        {
            KillTweens(target);
        }

        /// <summary>
        /// 暂停目标上的所有动画
        /// </summary>
        public static void Pause(RectTransform target)
        {
            if (_activeTweens.TryGetValue(target, out var tweens))
            {
                foreach (var tween in tweens)
                {
                    if (tween != null && tween.IsActive())
                        tween.Pause();
                }
            }
        }

        /// <summary>
        /// 恢复目标上的所有动画
        /// </summary>
        public static void Resume(RectTransform target)
        {
            if (_activeTweens.TryGetValue(target, out var tweens))
            {
                foreach (var tween in tweens)
                {
                    if (tween != null && tween.IsActive())
                        tween.Play();
                }
            }
        }

        #endregion

        #region Tween创建

        /// <summary>
        /// 根据节点类型创建Tweens
        /// </summary>
        private static List<Tween> CreateTweens(RectTransform target, UIAnimNode node)
        {
            var tweens = new List<Tween>();

            switch (node.NodeType)
            {
                case UIAnimNodeType.Single:
                    var tween = CreateSingleTween(target, node.Clip.Value);
                    if (tween != null) tweens.Add(tween);
                    break;

                case UIAnimNodeType.Sequence:
                    tweens.AddRange(CreateSequenceTweens(target, node));
                    break;

                case UIAnimNodeType.Parallel:
                    tweens.AddRange(CreateParallelTweens(target, node));
                    break;
            }

            return tweens;
        }

        /// <summary>
        /// 创建单一Tween
        /// </summary>
        private static Tween CreateSingleTween(RectTransform rootTarget, UIAnimClip clip)
        {
            // 解析目标
            Transform targetTrans;
            if (!string.IsNullOrEmpty(clip.TargetPath))
            {
                targetTrans = rootTarget.Find(clip.TargetPath);
                if (targetTrans == null)
                {
                    Debug.LogWarning($"[UIAnim] 目标路径未找到: {clip.TargetPath}");
                    return null;
                }
            }
            else
            {
                targetTrans = rootTarget;
            }

            // 根据动画类型创建Tween
            return clip.Type switch
            {
                // 透明度
                UIAnimType.Fade => CreateFadeTween(targetTrans, clip),
                UIAnimType.Alpha => CreateAlphaTween(targetTrans, clip),

                // 缩放
                UIAnimType.Scale => CreateScaleTween(targetTrans, clip),
                UIAnimType.ScaleX => CreateScaleXTween(targetTrans, clip),
                UIAnimType.ScaleY => CreateScaleYTween(targetTrans, clip),
                UIAnimType.PunchScale => CreatePunchScaleTween(targetTrans, clip),
                UIAnimType.ShakeScale => CreateShakeScaleTween(targetTrans, clip),

                // 移动
                UIAnimType.Move => CreateMoveTween(targetTrans, clip),
                UIAnimType.MoveX => CreateMoveXTween(targetTrans, clip),
                UIAnimType.MoveY => CreateMoveYTween(targetTrans, clip),
                UIAnimType.MoveFrom => CreateMoveFromTween(targetTrans, clip),
                UIAnimType.PunchPosition => CreatePunchPositionTween(targetTrans, clip),
                UIAnimType.ShakePosition => CreateShakePositionTween(targetTrans, clip),

                // 旋转
                UIAnimType.Rotate => CreateRotateTween(targetTrans, clip),
                UIAnimType.RotateZ => CreateRotateZTween(targetTrans, clip),
                UIAnimType.PunchRotation => CreatePunchRotationTween(targetTrans, clip),

                // 颜色
                UIAnimType.Color => CreateColorTween(targetTrans, clip),
                UIAnimType.Gradient => CreateGradientTween(targetTrans, clip),

                // 文字
                UIAnimType.TextColor => CreateTextColorTween(targetTrans, clip),
                UIAnimType.TextAlpha => CreateTextAlphaTween(targetTrans, clip),
                UIAnimType.Typewriter => CreateTypewriterTween(targetTrans, clip),
                UIAnimType.TextCount => CreateTextCountTween(targetTrans, clip),

                // 进度
                UIAnimType.FillAmount => CreateFillAmountTween(targetTrans, clip),
                UIAnimType.SliderValue => CreateSliderValueTween(targetTrans, clip),

                // 路径
                UIAnimType.Path => CreatePathTween(targetTrans, clip),

                // 控制
                UIAnimType.Delay => CreateDelayTween(clip),
                UIAnimType.Callback => CreateCallbackTween(clip),

                _ => null
            };
        }

        #region 透明度Tweens

        private static Tween CreateFadeTween(Transform target, UIAnimClip clip)
        {
            var canvasGroup = target.GetComponent<CanvasGroup>();
            if (canvasGroup != null)
            {
                if (clip.StartValue != null)
                {
                    canvasGroup.alpha = (float)clip.StartValue;
                }
                return canvasGroup.DOFade((float)clip.EndValue, clip.Duration)
                    .SetEase(clip.EaseType)
                    .SetLoops(clip.Loops, clip.LoopType);
            }

            // 尝试Graphic
            var graphic = target.GetComponent<Graphic>();
            if (graphic != null)
            {
                var endColor = graphic.color;
                endColor.a = (float)clip.EndValue;

                if (clip.StartValue != null)
                {
                    var startColor = graphic.color;
                    startColor.a = (float)clip.StartValue;
                    graphic.color = startColor;
                }

                return graphic.DOColor(endColor, clip.Duration)
                    .SetEase(clip.EaseType)
                    .SetLoops(clip.Loops, clip.LoopType);
            }

            return null;
        }

        private static Tween CreateAlphaTween(Transform target, UIAnimClip clip)
        {
            var canvasGroup = target.GetComponent<CanvasGroup>();
            if (canvasGroup == null)
                canvasGroup = target.gameObject.AddComponent<CanvasGroup>();

            return canvasGroup.DOFade((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        #endregion

        #region 缩放Tweens

        private static Tween CreateScaleTween(Transform target, UIAnimClip clip)
        {
            var endScale = (Vector3)clip.EndValue;

            if (clip.StartValue != null)
            {
                target.localScale = (Vector3)clip.StartValue;
            }

            return target.DOScale(endScale, clip.Duration)
                .SetEase(clip.EaseType)
                .SetLoops(clip.Loops, clip.LoopType);
        }

        private static Tween CreateScaleXTween(Transform target, UIAnimClip clip)
        {
            return target.DOScaleX((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateScaleYTween(Transform target, UIAnimClip clip)
        {
            return target.DOScaleY((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreatePunchScaleTween(Transform target, UIAnimClip clip)
        {
            return target.DOPunchScale((Vector3)clip.EndValue, clip.Duration, clip.ShakeVibrato)
                .SetRelative(true);
        }

        private static Tween CreateShakeScaleTween(Transform target, UIAnimClip clip)
        {
            return target.DOShakeScale(clip.Duration, clip.ShakeStrength, clip.ShakeVibrato);
        }

        #endregion

        #region 移动Tweens

        private static Tween CreateMoveTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            var endPos = (Vector2)clip.EndValue;
            return rectTransform.DOAnchorPos(endPos, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateMoveXTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            return rectTransform.DOAnchorPosX((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateMoveYTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            return rectTransform.DOAnchorPosY((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateMoveFromTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            var startPos = (Vector2)clip.StartValue;
            var originalPos = rectTransform.anchoredPosition;
            rectTransform.anchoredPosition = startPos;

            return rectTransform.DOAnchorPos(originalPos, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreatePunchPositionTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            return rectTransform.DOPunchAnchorPos((Vector2)clip.EndValue, clip.Duration, clip.ShakeVibrato);
        }

        private static Tween CreateShakePositionTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            return rectTransform.DOShakeAnchorPos(clip.Duration, clip.ShakeStrength, clip.ShakeVibrato);
        }

        #endregion

        #region 旋转Tweens

        private static Tween CreateRotateTween(Transform target, UIAnimClip clip)
        {
            return target.DORotate((Vector3)clip.EndValue, clip.Duration, RotateMode.FastBeyond360)
                .SetEase(clip.EaseType)
                .SetLoops(clip.Loops, clip.LoopType);
        }

        private static Tween CreateRotateZTween(Transform target, UIAnimClip clip)
        {
            var endValue = (float)clip.EndValue;
            return target.DORotate(new Vector3(0, 0, endValue), clip.Duration, RotateMode.FastBeyond360)
                .SetEase(clip.EaseType)
                .SetLoops(clip.Loops, clip.LoopType)
                .SetRelative(clip.IsRelative);
        }

        private static Tween CreatePunchRotationTween(Transform target, UIAnimClip clip)
        {
            return target.DOPunchRotation((Vector3)clip.EndValue, clip.Duration, clip.ShakeVibrato);
        }

        #endregion

        #region 颜色Tweens

        private static Tween CreateColorTween(Transform target, UIAnimClip clip)
        {
            var graphic = target.GetComponent<Graphic>();
            if (graphic == null) return null;

            if (clip.StartValue != null)
            {
                graphic.color = (Color)clip.StartValue;
            }

            return graphic.DOColor((Color)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateGradientTween(Transform target, UIAnimClip clip)
        {
            var graphic = target.GetComponent<Graphic>();
            if (graphic == null) return null;

            return graphic.DOGradientColor((Gradient)clip.EndValue, clip.Duration);
        }

        #endregion

        #region 文字Tweens

        private static Tween CreateTextColorTween(Transform target, UIAnimClip clip)
        {
            var tmp = target.GetComponent<TMP_Text>();
            if (tmp == null) return null;

            return tmp.DOColor((Color)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateTextAlphaTween(Transform target, UIAnimClip clip)
        {
            var tmp = target.GetComponent<TMP_Text>();
            if (tmp == null) return null;

            var endColor = tmp.color;
            endColor.a = (float)clip.EndValue;
            return tmp.DOColor(endColor, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateTypewriterTween(Transform target, UIAnimClip clip)
        {
            var tmp = target.GetComponent<TMP_Text>();
            if (tmp == null) return null;

            tmp.maxVisibleCharacters = 0;
            int totalChars = tmp.textInfo.characterCount;

            return DOTween.To(
                () => tmp.maxVisibleCharacters,
                x => tmp.maxVisibleCharacters = x,
                totalChars,
                clip.Duration
            ).SetEase(clip.EaseType);
        }

        private static Tween CreateTextCountTween(Transform target, UIAnimClip clip)
        {
            var tmp = target.GetComponent<TMP_Text>();
            if (tmp == null) return null;

            int start = clip.StartValue != null ? (int)clip.StartValue : 0;
            int end = (int)clip.EndValue;

            return DOTween.To(
                () => start,
                x =>
                {
                    tmp.text = x.ToString();
                    start = x;
                },
                end,
                clip.Duration
            ).SetEase(clip.EaseType);
        }

        #endregion

        #region 进度Tweens

        private static Tween CreateFillAmountTween(Transform target, UIAnimClip clip)
        {
            var image = target.GetComponent<Image>();
            if (image == null) return null;

            return image.DOFillAmount((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        private static Tween CreateSliderValueTween(Transform target, UIAnimClip clip)
        {
            var slider = target.GetComponent<Slider>();
            if (slider == null) return null;

            return slider.DOValue((float)clip.EndValue, clip.Duration)
                .SetEase(clip.EaseType);
        }

        #endregion

        #region 路径Tweens

        private static Tween CreatePathTween(Transform target, UIAnimClip clip)
        {
            var rectTransform = target as RectTransform;
            if (rectTransform == null) return null;

            var waypoints = (Vector3[])clip.EndValue;
            return rectTransform.DOPath(waypoints, clip.Duration, clip.PathType, PathMode.TopDown2D)
                .SetEase(clip.EaseType);
        }

        #endregion

        #region 控制Tweens

        private static Tween CreateDelayTween(UIAnimClip clip)
        {
            return DOVirtual.DelayedCall(clip.Duration, null);
        }

        private static Tween CreateCallbackTween(UIAnimClip clip)
        {
            return DOVirtual.DelayedCall(0f, clip.Callback);
        }

        #endregion

        #region 序列/并行动画

        private static List<Tween> CreateSequenceTweens(RectTransform target, UIAnimNode node)
        {
            var tweens = new List<Tween>();
            var sequence = DOTween.Sequence();

            foreach (var child in node.Children)
            {
                var childTweens = CreateTweens(target, child);
                foreach (var tween in childTweens)
                {
                    sequence.Append(tween);
                }
                tweens.AddRange(childTweens);
            }

            // 返回序列中所有Tweens（序列会自动管理）
            return tweens;
        }

        private static List<Tween> CreateParallelTweens(RectTransform target, UIAnimNode node)
        {
            var tweens = new List<Tween>();

            foreach (var child in node.Children)
            {
                var childTweens = CreateTweens(target, child);
                tweens.AddRange(childTweens);
            }

            return tweens;
        }

        #endregion

        #endregion

        #region 清理

        private static void KillTweens(RectTransform target)
        {
            if (_activeTweens.TryGetValue(target, out var tweens))
            {
                foreach (var tween in tweens)
                {
                    if (tween != null && tween.IsActive())
                    {
                        tween.Kill(complete: false);
                    }
                }
                tweens.Clear();
            }
        }

        private static void CleanupTweens(RectTransform target)
        {
            if (_activeTweens.TryGetValue(target, out var tweens))
            {
                tweens.Clear();
                _activeTweens.Remove(target);
            }
        }

        #endregion
    }

    #endregion

    #region UIAnimator - 高层API

    /// <summary>
    /// UI动画器（高层API封装）
    /// 提供便捷的动画播放方法
    /// </summary>
    public static class UIAnimator
    {
        // 默认动画配置
        private static readonly Dictionary<string, UIAnimConfig> _defaultShowConfigs = new();
        private static readonly Dictionary<string, UIAnimConfig> _defaultHideConfigs = new();

        /// <summary>
        /// 注册默认动画配置
        /// </summary>
        public static void RegisterDefaultConfig(string viewName, UIAnimConfig showConfig, UIAnimConfig hideConfig)
        {
            _defaultShowConfigs[viewName] = showConfig;
            _defaultHideConfigs[viewName] = hideConfig;
        }

        /// <summary>
        /// 播放显示动画
        /// </summary>
        public static async UniTask PlayShowAsync(RectTransform target, string viewName, UIAnimConfig config = null, CancellationToken ct = default)
        {
            if (target == null) return;

            // 确保有CanvasGroup
            var canvasGroup = target.GetComponent<CanvasGroup>();
            if (canvasGroup == null)
                canvasGroup = target.gameObject.AddComponent<CanvasGroup>();

            // 激活对象
            target.gameObject.SetActive(true);

            // 获取配置
            var animConfig = config;
            if (animConfig == null && _defaultShowConfigs.TryGetValue(viewName, out var defaultConfig))
            {
                animConfig = defaultConfig;
            }

            // 播放动画
            if (animConfig != null && animConfig.PlayAnimation && animConfig.AnimNode != null)
            {
                await UIComplexAnimator.PlayAsync(target, animConfig.AnimNode, ct);
            }
            else
            {
                // 无动画，直接显示
                canvasGroup.alpha = 1f;
                target.localScale = Vector3.one;
            }
        }

        /// <summary>
        /// 播放隐藏动画
        /// </summary>
        public static async UniTask PlayHideAsync(RectTransform target, string viewName, UIAnimConfig config = null, CancellationToken ct = default)
        {
            if (target == null) return;

            // 获取配置
            var animConfig = config;
            if (animConfig == null && _defaultHideConfigs.TryGetValue(viewName, out var defaultConfig))
            {
                animConfig = defaultConfig;
            }

            // 播放动画
            if (animConfig != null && animConfig.PlayAnimation && animConfig.AnimNode != null)
            {
                await UIComplexAnimator.PlayAsync(target, animConfig.AnimNode, ct);
            }

            // 隐藏对象
            target.gameObject.SetActive(false);
        }

        /// <summary>
        /// 播放自定义动画
        /// </summary>
        public static UniTask PlayAsync(RectTransform target, UIAnimNode node, CancellationToken ct = default)
        {
            return UIComplexAnimator.PlayAsync(target, node, ct);
        }

        /// <summary>
        /// 停止动画
        /// </summary>
        public static void Stop(RectTransform target)
        {
            UIComplexAnimator.Stop(target);
        }

        /// <summary>
        /// 暂停动画
        /// </summary>
        public static void Pause(RectTransform target)
        {
            UIComplexAnimator.Pause(target);
        }

        /// <summary>
        /// 恢复动画
        /// </summary>
        public static void Resume(RectTransform target)
        {
            UIComplexAnimator.Resume(target);
        }
    }

    #endregion
}

// ============================================================================
// 使用示例
// ============================================================================

/*
// 示例1：简单淡入淡出
await UIAnimator.PlayShowAsync(panel.RectTransform, "MyPanel", UIAnimConfig.FadeIn(0.3f));
await UIAnimator.PlayHideAsync(panel.RectTransform, "MyPanel", UIAnimConfig.FadeOut(0.3f));

// 示例2：弹窗动画
var showAnim = UIAnimConfig.PopupShow(0.3f);
var hideAnim = UIAnimConfig.PopupHide(0.2f);
await UIAnimator.PlayShowAsync(panel.RectTransform, "Popup", showAnim);
await UIAnimator.PlayHideAsync(panel.RectTransform, "Popup", hideAnim);

// 示例3：复杂组合动画
var complexAnim = UIAnimNode.Sequence(
    // 背景
    UIAnimNode.Parallel(
        UIAnimNode.Single(UIAnimClip.Fade(0.8f, 0.2f).WithTarget("Background")),
        UIAnimNode.Single(UIAnimClip.ScaleFromZero(0.3f).WithTarget("Panel"))
    ),
    // 金币飞入
    UIAnimNode.Single(UIAnimClip.Path(waypoints, 0.5f).WithTarget("Coin")),
    // 数字滚动
    UIAnimNode.Single(UIAnimClip.TextCount(0, 1000, 1f).WithTarget("Amount")),
    // 按钮
    UIAnimNode.Single(UIAnimClip.ScaleFromZero(0.2f).WithTarget("ClaimBtn"))
);

await UIAnimator.PlayAsync(rootTransform, complexAnim);

// 示例4：列表项依次出现
var listAnim = UIAnimNode.Sequence(
    UIAnimNode.Single(UIAnimClip.ScaleFromZero(0.15f).WithTarget("Item1")),
    UIAnimNode.Single(UIAnimClip.ScaleFromZero(0.15f).WithTarget("Item2")),
    UIAnimNode.Single(UIAnimClip.ScaleFromZero(0.15f).WithTarget("Item3"))
);

// 示例5：打字机效果
var typewriter = UIAnimNode.Single(UIAnimClip.Typewriter(2f));
await UIAnimator.PlayAsync(textRect, typewriter);

// 示例6：无限旋转
var spinAnim = UIAnimNode.Single(UIAnimClip.Spin(1f));
await UIAnimator.PlayAsync(iconRect, spinAnim);

// 示例7：震动效果
var shakeAnim = UIAnimNode.Single(UIAnimClip.Shake(10f, 0.3f));
await UIAnimator.PlayAsync(buttonRect, shakeAnim);
*/
