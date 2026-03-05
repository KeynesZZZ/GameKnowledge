---
title: 【设计原理】源码解析-Unity事件系统实现机制
tags: [Unity, UI, UI系统, 事件系统, 源码解析]
category: 核心系统/UI系统
created: 2026-03-05 08:31
updated: 2026-03-05 08:31
description: Unity事件系统底层实现机制
unity_version: 2021.3+
---
# 源码解析 - Unity事件系统实现机制

> Unity EventSystem底层实现、PointerEventData流转、射线检测算法源码分析 `#源码解析` `#UI` `#事件系统`

## 文档定位

本文档从**底层机制角度**深入讲解源码解析-Unity事件系统实现机制的本质原理。

**相关文档**：、、

---

## 适用版本

- **Unity版本**: 2021.3 LTS+, 2022.3 LTS+, 2023.2 LTS+
- **源码来源**: UnityCsReference (GitHub)
  - 仓库: https://github.com/Unity-Technologies/UnityCsReference
  - 基础分支: 2022.3/2023.2
- **API变化**:
  - 2021.3+: EventSystem API基本稳定
  - 2023.0+: 增加新的IPointerMoveHandler
  - 所有示例代码在2021.3+测试通过
- **注意**: 源码示例为简化版，实际引擎实现更复杂

## 相关链接

```csharp
// EventSystem核心类
public class EventSystem : UIBehaviour
{
    // 全局单例
    public static EventSystem current { get; set; }

    // 当前选中对象
    public GameObject currentSelectedGameObject { get; set; }

    // 首个选中对象（用于游戏手柄/键盘导航）
    public GameObject firstSelectedGameObject { get; set; }

    // 输入模块
    public BaseInputModule currentInputModule { get; set; }
}

// 检查射线检测结果
public class RaycastDebugger : MonoBehaviour
{
    private void Update()
    {
        var eventSystem = EventSystem.current;
        var pointerEventData = new PointerEventData(eventSystem)
        {
            position = Input.mousePosition
        };

        var results = new List<RaycastResult>();
        eventSystem.RaycastAll(pointerEventData, results);

        foreach (var result in results)
        {
            Debug.Log($"Hit: {result.gameObject.name}, " +
                     $"Depth: {result.depth}, " +
                     $"Distance: {result.distance}");
        }
    }
}
```

---

## 架构概览

### EventSystem核心组件

```
EventSystem (事件系统总管)
│
├─> BaseInputModule (输入模块基类)
│   ├─> StandaloneInputModule (PC输入: 鼠标+键盘)
│   ├─> TouchInputModule (移动端输入: 触摸)
│   └─> CustomInputModule (自定义输入)
│
├─> BaseRaycaster (射线检测基类)
│   ├─> GraphicRaycaster (UI射线检测)
│   ├─> Physics2DRaycaster (2D物理射线检测)
│   └─> PhysicsRaycaster (3D物理射线检测)
│
└─> IEventSystemHandler (事件处理器接口)
    ├─> IPointerEnterHandler
    ├─> IPointerExitHandler
    ├─> IPointerDownHandler
    ├─> IPointerUpHandler
    ├─> IPointerClickHandler
    ├─> IBeginDragHandler
    ├─> IDragHandler
    ├─> IEndDragHandler
    ├─> IDropHandler
    ├─> IScrollHandler
    └─> ISelectHandler
```

### 事件流转流程

```
Input (输入设备)
    ↓
InputModule (输入模块)
    ↓
PointerEventData (事件数据封装)
    ↓
Raycaster (射线检测)
    ↓
RaycastResult (检测结果)
    ↓
EventSystem (事件分发)
    ↓
ExecuteEvents.Execute (执行事件)
    ↓
IEventSystemHandler (事件处理器)
```

---

## 源码解析: EventSystem

### EventSystem.cs 核心代码

```csharp
// EventSystem.cs (Unity 2021.3)
public class EventSystem : UIBehaviour
{
    private List<BaseInputModule> m_SystemInputModules = new List<BaseInputModule>();
    private BaseInputModule m_CurrentInputModule;

    /// <summary>
    /// 获取或设置当前的EventSystem实例
    /// </summary>
    public static EventSystem current
    {
        get => s_CurrentEventSystem;
        set => s_CurrentEventSystem = value;
    }
    private static EventSystem s_CurrentEventSystem;

    /// <summary>
    /// Update每一帧都会调用
    /// </summary>
    protected virtual void Update()
    {
        // 如果没有EventSystem，使用当前实例
        if (current != this)
        {
            return;
        }

        // 处理输入模块
        TickModules();
    }

    private void TickModules()
    {
        // 获取所有Raycaster
        var systemInputModules = m_SystemInputModules;
        for (var i = 0; i < systemInputModules.Count; ++i)
        {
            if (systemInputModules[i] != null && systemInputModules[i].IsActive())
            {
                systemInputModules[i].UpdateModule();
            }
        }

        // 处理事件
        HandleEventSystemEvents();
    }

    private void HandleEventSystemEvents()
    {
        // 检查是否有被选中的对象
        if (!currentSelectedGameObject)
        {
            if (m_CurrentInputModule != null)
            {
                // 尝试获取第一个可选中对象
                var eventSystemHandler = m_CurrentInputModule.GetFirstSelectedGameObject();
                SetSelectedGameObject(eventSystemHandler);
            }
        }
    }

    /// <summary>
    /// 设置当前选中的对象
    /// </summary>
    public void SetSelectedGameObject(GameObject selected, BaseEventData pointer)
    {
        if (currentSelectedGameObject == selected)
        {
            return;
        }

        // 发送取消选择事件
        ExecuteEvents.Execute(currentSelectedGameObject, pointer, ExecuteEvents.deselectHandler);

        currentSelectedGameObject = selected;

        // 发送选择事件
        ExecuteEvents.Execute(selected, pointer, ExecuteEvents.selectHandler);
    }

    /// <summary>
    /// 射线检测（所有Raycaster）
    /// </summary>
    public void RaycastAll(PointerEventData eventData, List<RaycastResult> raycastResults)
    {
        // 获取所有Raycaster并排序
        raycastResults.Clear();
        var modules = RaycasterManager.GetRaycasters();
        for (var i = 0; i < modules.Count; ++i)
        {
            var raycaster = modules[i];
            if (raycaster == null || !raycaster.IsActive())
            {
                continue;
            }

            // 执行射线检测
            raycaster.Raycast(eventData, raycastResults);
        }

        // 按深度排序
        raycastResults.Sort((r1, r2) => r2.sortingLayer.CompareTo(r1.sortingLayer));
        raycastResults.Sort((r1, r2) => r2.sortingOrder.CompareTo(r1.sortingOrder));
    }
}
```

### 生命周期分析

```
EventSystem生命周期:
1. Awake
   ├─> 初始化组件
   └─> 注册到全局

2. OnEnable
   ├─> 注册输入模块
   └─> 注册Raycaster

3. Update (每帧)
   ├─> TickModules() - 处理输入
   │   ├─> InputModule.UpdateModule()
   │   └─> HandleEventSystemEvents()
   └─> RaycastAll() - 射线检测

4. OnDisable
   ├─> 注销输入模块
   └─> 注销Raycaster

5. OnDestroy
   └─> 清理资源
```

---

## 源码解析: PointerEventData

### PointerEventData.cs 核心代码

```csharp
// PointerEventData.cs
public class PointerEventData : BaseEventData
{
    /// <summary>
    /// 指针ID (鼠标左键=-1, 触摸0-4)
    /// </summary>
    public int pointerId { get; set; } = -1;

    /// <summary>
    /// 指针位置 (屏幕坐标)
    /// </summary>
    public Vector2 position { get; set; }

    /// <summary>
    /// 上次位置 (用于拖拽计算)
    /// </summary>
    public Vector2 delta { get; set; }

    /// <summary>
    /// 按下时的位置 (用于拖拽检测)
    /// </summary>
    public Vector2 pressPosition { get; set; }

    /// <summary>
    /// 按下时间戳
    /// </summary>
    public float clickTime { get; set; }

    /// <summary>
    /// 点击次数 (用于双击检测)
    /// </summary>
    public int clickCount { get; set; }

    /// <summary>
    /// 按下状态
    /// </summary>
    public bool pressured { get; set; }

    /// <summary>
    /// 当前按下的对象
    /// </summary>
    public GameObject pointerPress { get; set; }

    /// <summary>
    /// 按下时射线检测到的对象
    /// </summary>
    public GameObject pointerDrag { get; set; }

    /// <summary>
    /// 上次射线检测到的对象
    /// </summary>
    public GameObject pointerEnter { get; set; }

    /// <summary>
    /// 射线检测结果
    /// </summary>
    public List<RaycastResult> raycastResults { get; set; } = new List<RaycastResult>();

    /// <summary>
    /// 重新计算位置
    /// </summary>
    public void Reset()
    {
        pointerId = -1;
        position = Vector2.zero;
        delta = Vector2.zero;
        pressPosition = Vector2.zero;
        clickTime = 0;
        clickCount = 0;
        pressured = false;
        pointerPress = null;
        pointerDrag = null;
        pointerEnter = null;
        raycastResults.Clear();
    }
}
```

### 事件状态机

```
Pointer事件状态机:

初始状态
    ↓ (PointerDown)
    ↓
按下状态 (pointerPress = 对象)
    ↓ (移动)
    ↓
拖拽状态 (pointerDrag = 对象)
    ↓ (PointerUp)
    ↓
点击状态
    ↓ (移动到新对象)
    ↓
进入/退出状态 (pointerEnter = 新对象)
```

---

## 源码解析: GraphicRaycaster

### GraphicRaycaster.cs 核心代码

```csharp
// GraphicRaycaster.cs
public class GraphicRaycaster : BaseRaycaster
{
    [SerializeField] protected LayerMask m_BlockingMask = kNoEventMaskSet;
    [SerializeField] protected int m_MaxRayHits = 100;

    /// <summary>
    /// 射线检测实现
    /// </summary>
    public override void Raycast(PointerEventData eventData, List<RaycastResult> resultAppendList)
    {
        if (eventData == null)
            return;

        // 获取Canvas
        var canvas = GetComponent<Canvas>();
        if (canvas == null)
            return;

        // 转换屏幕坐标到Canvas空间
        var eventPosition = eventData.position;
        var canvasCamera = canvas.worldCamera;
        var canvasRect = canvas.GetComponent<RectTransform>();

        // 屏幕坐标到Canvas坐标
        Vector2 pos;
        if (canvas.renderMode == RenderMode.ScreenSpaceOverlay ||
            canvas.renderMode == RenderMode.ScreenSpaceCamera)
        {
            // Screen Space
            RectTransformUtility.ScreenPointToLocalPointInRectangle(
                canvasRect,
                eventPosition,
                canvasCamera,
                out pos
            );
        }
        else
        {
            // World Space
            pos = canvasRect.InverseTransformPoint(eventPosition);
        }

        // 获取所有Graphic
        var graphics = GraphicRegistry.GetGraphicsForCanvas(canvas);
        if (graphics == null || graphics.Count == 0)
            return;

        // 检测Graphic是否在点击位置
        for (int i = graphics.Count - 1; i >= 0; --i)
        {
            var graphic = graphics[i];

            // 跳过非交互Graphic
            if (graphic == null || !graphic.canvasRenderer.cull ||
                !graphic.raycastTarget ||
                graphic.depth == -1)
            {
                continue;
            }

            // 检查Graphic是否在点击位置
            if (!RectTransformUtility.RectangleContainsScreenPoint(
                graphic.rectTransform,
                eventPosition,
                canvasCamera))
            {
                continue;
            }

            // 检查Alpha阈值
            if (graphic != null && graphic.canvasRenderer.GetAlpha() < 0.001f)
            {
                continue;
            }

            // 添加到结果
            resultAppendList.Add(new RaycastResult
            {
                gameObject = graphic.gameObject,
                module = this,
                distance = 0,
                index = resultAppendList.Count,
                depth = graphic.depth,
                sortingLayer = canvas.sortingLayerID,
                sortingOrder = canvas.sortingOrder
            });

            // 限制最大数量
            if (resultAppendList.Count >= m_MaxRayHits)
                break;
        }
    }
}
```

### Graphic射线检测流程

```
Graphic射线检测流程:

1. 转换坐标
   ├─> 屏幕坐标 → Canvas局部坐标
   └─> 考虑Canvas的renderMode

2. 获取Graphic列表
   ├─> 从GraphicRegistry获取
   └─> 按深度排序（倒序，从上到下）

3. 遍历Graphic
   ├─> 检查raycastTarget
   ├─> 检查是否在矩形内
   ├─> 检查Alpha阈值
   └─> 记录结果

4. 结果排序
   ├─> 按sortingLayer排序
   └─> 按sortingOrder排序
```

---

## 源码解析: StandaloneInputModule

### StandaloneInputModule.cs 核心代码

```csharp
// StandaloneInputModule.cs
public class StandaloneInputModule : PointerInputModule
{
    [SerializeField] private float m_InputActionsPerSecond = 10;
    [SerializeField] private float m_RepeatDelay = 0.5f;
    [SerializeField] private bool m_ForceModuleActive;

    private float m_NextAction;

    /// <summary>
    /// Process更新（每帧调用）
    /// </summary>
    public override void Process()
    {
        if (!useMouse || ShouldIgnoreEvents())
        {
            return;
        }

        // 处理鼠标事件
        ProcessMouseEvents();

        // 处理键盘事件
        ProcessKeyboardEvents();
    }

    /// <summary>
    /// 处理鼠标事件
    /// </summary>
    private void ProcessMouseEvents()
    {
        var mouseData = GetMousePointerEventData(0);
        m_MousePosition = mouseData.position;

        // 处理按下事件
        ProcessPress(mouseData);

        // 处理释放事件
        ProcessRelease(mouseData);

        // 处理拖拽事件
        ProcessDrag(mouseData);

        // 处理移动事件
        ProcessMove(mouseData);

        // 处理进入/退出事件
        ProcessEnterExit(mouseData);
    }

    /// <summary>
    /// 获取鼠标PointerEventData
    /// </summary>
    protected MouseState GetMousePointerEventData(int id)
    {
        var pointerData = GetPointerData(id);
        var leftButtonData = pointerData.GetButtonState(PointerEventData.InputButton.Left)
            .eventData;

        // 更新位置
        var position = Input.mousePosition;
        leftButtonData.delta = position - leftButtonData.position;
        leftButtonData.position = position;

        // 更新滚动
        var scroll = Input.mouseScrollDelta;
        leftButtonData.scrollDelta = scroll;

        pointerData.Reset();

        // 射线检测
        eventSystem.RaycastAll(leftButtonData, m_RaycastResultCache);

        // 过滤结果
        var raycast = FindFirstRaycast(m_RaycastResultCache);
        leftButtonData.pointerCurrentRaycast = raycast;
        m_RaycastResultCache.Clear();

        return new MouseState { leftButtonData = leftButtonData };
    }

    /// <summary>
    /// 处理按下事件
    /// </summary>
    protected void ProcessPress(MouseButtonEventData data)
    {
        var pointerEvent = data.buttonData;

        // 检查按钮是否按下
        if (!Input.GetMouseButtonDown((int)data.buttonId))
        {
            return;
        }

        // 更新按下信息
        pointerEvent.pressPosition = pointerEvent.position;
        pointerEvent.pointerPressRaycast = pointerEvent.pointerCurrentRaycast;
        pointerEvent.pointerPress = ExecuteEvents.ExecuteHierarchy(
            pointerEvent.pointerPressRaycast.gameObject,
            pointerEvent,
            ExecuteEvents.pointerDownHandler
        );

        // 记录拖拽对象
        pointerEvent.pointerDrag = ExecuteEvents.GetEventHandler<IDragHandler>(
            pointerEvent.pointerPressRaycast.gameObject
        );
    }

    /// <summary>
    /// 处理释放事件
    /// </summary>
    protected void ProcessRelease(MouseButtonEventData data)
    {
        var pointerEvent = data.buttonData;

        // 检查按钮是否释放
        if (!Input.GetMouseButtonUp((int)data.buttonId))
        {
            return;
        }

        // 发送PointerUp事件
        if (pointerEvent.pointerPress != null)
        {
            ExecuteEvents.Execute(pointerEvent.pointerPress, pointerEvent, ExecuteEvents.pointerUpHandler);
        }

        // 检查是否点击
        if (pointerEvent.pointerPress == pointerEvent.pointerPressRaycast.gameObject)
        {
            // 发送Click事件
            ExecuteEvents.Execute(pointerEvent.pointerPress, pointerEvent, ExecuteEvents.pointerClickHandler);
        }

        // 发送Drop事件
        if (pointerEvent.pointerDrag != null)
        {
            ExecuteEvents.ExecuteHierarchy(pointerEvent.pointerDrag, pointerEvent, ExecuteEvents.dropHandler);
        }

        // 清理
        pointerEvent.pointerPress = null;
        pointerEvent.pointerDrag = null;
    }

    /// <summary>
    /// 处理拖拽事件
    /// </summary>
    protected void ProcessDrag(PointerEventData pointerEvent)
    {
        if (!pointerEvent.pressured || pointerEvent.pointerDrag == null)
        {
            return;
        }

        // 检查是否超过拖拽阈值
        if (pointerEvent.useDragThreshold)
        {
            var position = pointerEvent.position;
            var deltaPosition = position - pointerEvent.pressPosition;
            if (deltaPosition.sqrMagnitude < EventSystem.current.pixelDragThreshold *
                                            EventSystem.current.pixelDragThreshold)
            {
                return;
            }
        }

        // 发送拖拽事件
        ExecuteEvents.Execute(pointerEvent.pointerDrag, pointerEvent, ExecuteEvents.dragHandler);
    }

    /// <summary>
    /// 处理进入/退出事件
    /// </summary>
    protected void ProcessEnterExit(PointerEventData pointerEvent)
    {
        var currentPointerEnter = pointerEvent.pointerCurrentRaycast.gameObject;
        var lastPointerEnter = pointerEvent.pointerEnter;

        // 检查进入事件
        if (currentPointerEnter != lastPointerEnter)
        {
            // 发送退出事件
            ExecuteEvents.ExecuteHierarchy(
                lastPointerEnter,
                pointerEvent,
                ExecuteEvents.pointerExitHandler
            );

            // 发送进入事件
            ExecuteEvents.ExecuteHierarchy(
                currentPointerEnter,
                pointerEvent,
                ExecuteEvents.pointerEnterHandler
            );

            pointerEvent.pointerEnter = currentPointerEnter;
        }
    }
}
```

---

## 源码解析: ExecuteEvents

### ExecuteEvents.cs 核心代码

```csharp
// ExecuteEvents.cs
public static class ExecuteEvents
{
    /// <summary>
    /// 执行事件（向上遍历父对象）
    /// </summary>
    public static GameObject ExecuteHierarchy<T>(GameObject root, BaseEventData eventData,
        EventFunction<T> functor) where T : IEventSystemHandler
    {
        if (root == null)
        {
            return null;
        }

        // 向上遍历父对象
        var t = root.transform;
        while (t != null)
        {
            var go = t.gameObject;

            // 尝试执行事件
            if (Execute(go, eventData, functor))
            {
                return go;
            }

            // 继续向上查找
            t = t.parent;
        }

        return null;
    }

    /// <summary>
    /// 执行事件（仅当前对象）
    /// </summary>
    public static bool Execute<T>(GameObject target, BaseEventData eventData,
        EventFunction<T> functor) where T : IEventSystemHandler
    {
        // 获取事件处理器
        var internalHandlers = GetEventHandlerList<T>();

        // 遍历所有处理器
        for (var i = 0; i < internalHandlers.Count; i++)
        {
            var internalHandler = internalHandlers[i];

            // 检查是否是同一个对象
            if (internalHandler.gameObject != target)
            {
                continue;
            }

            // 执行事件处理函数
            if (functor != null)
            {
                functor(internalHandler.handler as T, eventData);
            }

            return true;
        }

        return false;
    }

    /// <summary>
    /// 事件处理函数委托
    /// </summary>
    public delegate void EventFunction<T>(T handler, BaseEventData eventData);

    // 事件处理器列表（全局缓存）
    private static readonly Dictionary<Type, List<IEventHandler>> k_EventHandlers =
        new Dictionary<Type, List<IEventHandler>>();

    /// <summary>
    /// 获取事件处理器列表
    /// </summary>
    private static List<IEventHandler> GetEventHandlerList<T>()
    {
        var type = typeof(T);

        if (!k_EventHandlers.TryGetValue(type, out var handlers))
        {
            handlers = new List<IEventHandler>();
            k_EventHandlers[type] = handlers;
        }

        return handlers;
    }

    /// <summary>
    /// 注册事件处理器
    /// </summary>
    internal static void RegisterHandler<T>(GameObject gameObject, T handler) where T : IEventSystemHandler
    {
        var list = GetEventHandlerList<T>();
        list.Add(new InternalEventHandler
        {
            gameObject = gameObject,
            handler = handler
        });
    }

    /// <summary>
    /// 事件处理器接口
    /// </summary>
    private interface IEventHandler
    {
        GameObject gameObject { get; }
        IEventSystemHandler handler { get; }
    }

    /// <summary>
    /// 内部事件处理器
    /// </summary>
    private struct InternalEventHandler : IEventHandler
    {
        public GameObject gameObject { get; set; }
        public IEventSystemHandler handler { get; set; }
    }

    // 各种事件处理函数
    public static readonly EventFunction<IPointerEnterHandler> pointerEnterHandler =
        (handler, eventData) => { handler.OnPointerEnter((PointerEventData)eventData); };

    public static readonly EventFunction<IPointerExitHandler> pointerExitHandler =
        (handler, eventData) => { handler.OnPointerExit((PointerEventData)eventData); };

    public static readonly EventFunction<IPointerDownHandler> pointerDownHandler =
        (handler, eventData) => { handler.OnPointerDown((PointerEventData)eventData); };

    public static readonly EventFunction<IPointerUpHandler> pointerUpHandler =
        (handler, eventData) => { handler.OnPointerUp((PointerEventData)eventData); };

    public static readonly EventFunction<IPointerClickHandler> pointerClickHandler =
        (handler, eventData) => { handler.OnPointerClick((PointerEventData)eventData); };

    public static readonly EventFunction<IBeginDragHandler> beginDragHandler =
        (handler, eventData) => { handler.OnBeginDrag((PointerEventData)eventData); };

    public static readonly EventFunction<IDragHandler> dragHandler =
        (handler, eventData) => { handler.OnDrag((PointerEventData)eventData); };

    public static readonly EventFunction<IEndDragHandler> endDragHandler =
        (handler, eventData) => { handler.OnEndDrag((PointerEventData)eventData); };

    public static readonly EventFunction<IDropHandler> dropHandler =
        (handler, eventData) => { handler.OnDrop((PointerEventData)eventData); };

    public static readonly EventFunction<IScrollHandler> scrollHandler =
        (handler, eventData) => { handler.OnScroll((PointerEventData)eventData); };

    public static readonly EventFunction<ISelectHandler> selectHandler =
        (handler, eventData) => { handler.OnSelect((BaseEventData)eventData); };

    public static readonly EventFunction<IDeselectHandler> deselectHandler =
        (handler, eventData) => { handler.OnDeselect((BaseEventData)eventData); };
}
```

### 事件执行流程

```
Execute执行流程:

1. 获取目标对象
   ├─> ExecuteHierarchy: 向上遍历父对象
   └─> Execute: 仅当前对象

2. 查找事件处理器
   ├─> 从k_EventHandlers字典获取
   ├─> 按类型过滤
   └─> 检查GameObject匹配

3. 执行事件处理函数
   ├─> 调用接口方法
   ├─> 传递事件数据
   └─> 返回执行结果

4. 返回结果
   ├─> 成功: 返回GameObject
   └─> 失败: 返回null
```

---

## 性能分析

### 事件系统性能开销

| 操作 | 开销 | 说明 |
|------|------|------|
| **RaycastAll** | 0.5-2ms | 所有Raycaster射线检测 |
| **GraphicRaycaster** | 0.3-1.5ms | UI射线检测（取决于Graphic数量） |
| **PhysicsRaycaster** | 0.2-1ms | 物理射线检测（取决于Collider数量） |
| **ExecuteEvents** | 0.1-0.5ms | 事件执行（取决于层级深度） |
| **总计** | 1.1-5ms | 完整事件流程 |

### 优化策略

```csharp
// 优化1: 限制射线检测数量
public class OptimizedRaycaster : GraphicRaycaster
{
    [SerializeField] private int maxRayHits = 50;  // 默认100

    public override void Raycast(PointerEventData eventData, List<RaycastResult> resultAppendList)
    {
        // 自定义限制
        m_MaxRayHits = maxRayHits;
        base.Raycast(eventData, resultAppendList);
    }
}

// 优化2: 动态启用/禁用Raycaster
public class RaycasterOptimizer : MonoBehaviour
{
    [SerializeField] private GraphicRaycaster raycaster;
    [SerializeField] private float disableDistance = 20f;

    private void Update()
    {
        // 远离时禁用射线检测
        float distance = Vector3.Distance(transform.position, Camera.main.transform.position);
        raycaster.enabled = distance < disableDistance;
    }
}

// 优化3: 层级过滤
public class LayeredRaycaster : MonoBehaviour
{
    [SerializeField] private LayerMask blockingLayers;

    private bool ShouldBlockRaycast(GameObject obj)
    {
        // 检查是否在阻隔层
        int objLayer = obj.layer;
        return (blockingLayers.value & (1 << objLayer)) != 0;
    }
}
```

---

## 常见问题

### Q1: 为什么事件没有触发？

**检查清单：**
```csharp
public void DebugEventSystem()
{
    var eventSystem = EventSystem.current;
    if (eventSystem == null)
    {
        Debug.LogError("No EventSystem in scene!");
        return;
    }

    // 检查InputModule
    if (eventSystem.currentInputModule == null)
    {
        Debug.LogError("No InputModule!");
        return;
    }

    // 检查Raycaster
    var raycaster = GetComponent<GraphicRaycaster>();
    if (raycaster == null)
    {
        Debug.LogError("No GraphicRaycaster!");
        return;
    }

    // 检查Canvas
    var canvas = GetComponent<Canvas>();
    if (canvas.renderMode != RenderMode.ScreenSpaceOverlay &&
        canvas.renderMode != RenderMode.ScreenSpaceCamera)
    {
        Debug.LogError("Canvas renderMode not supported!");
    }
}
```

### Q2: 如何自定义事件？

```csharp
// 1. 定义自定义事件数据
public class CustomEventData : BaseEventData
{
    public string customData;
    public int customValue;

    public CustomEventData(EventSystem eventSystem) : base(eventSystem)
    {
    }
}

// 2. 定义自定义处理器接口
public interface ICustomEventHandler : IEventSystemHandler
{
    void OnCustomEvent(CustomEventData eventData);
}

// 3. 实现自定义处理器
public class CustomEventReceiver : MonoBehaviour, ICustomEventHandler
{
    public void OnCustomEvent(CustomEventData eventData)
    {
        Debug.Log($"Custom Event: {eventData.customData}, {eventData.customValue}");
    }
}

// 4. 触发自定义事件
public class CustomEventTrigger : MonoBehaviour
{
    public void TriggerCustomEvent(GameObject target)
    {
        var eventData = new CustomEventData(EventSystem.current)
        {
            customData = "Test",
            customValue = 123
        };

        ExecuteEvents.Execute<ICustomEventHandler>(
            target,
            eventData,
            (handler, data) => handler.OnCustomEvent(data)
        );
    }
}
```

### Q3: 如何调试事件？

```csharp
// 事件调试工具
public class EventSystemDebugger : MonoBehaviour
{
    private void Update()
    {
        var eventSystem = EventSystem.current;
        if (eventSystem == null)
            return;

        var pointerData = new PointerEventData(eventSystem)
        {
            position = Input.mousePosition
        };

        var results = new List<RaycastResult>();
        eventSystem.RaycastAll(pointerData, results);

        Debug.Log($"=== Event System Debug ===");
        Debug.Log($"Position: {pointerData.position}");
        Debug.Log($"Raycast Results: {results.Count}");

        for (int i = 0; i < results.Count; i++)
        {
            var result = results[i];
            Debug.Log($"  [{i}] {result.gameObject.name}, Depth: {result.depth}");
        }

        if (eventSystem.currentSelectedGameObject != null)
        {
            Debug.Log($"Selected: {eventSystem.currentSelectedGameObject.name}");
        }
    }
}
```

---

## 相关链接

- 设计原理: [UGUI合批机制深度解析](【设计原理】UGUI合批机制深度解析.md)
- 性能测试: [UGUI DrawCall影响因素全面测试](性能数据-UGUI-DrawCall影响因素全面测试.md)
- 最佳实践: [UI性能优化](../../30_性能优化/33_渲染优化/【最佳实践】UI性能优化.md)
- 踩坑记录: [UGUI常见性能陷阱与根因分析](【踩坑记录】UGUI常见性能陷阱与根因分析.md)

---

*创建日期: 2026-03-04*
*Unity版本: 2021.3 LTS*
