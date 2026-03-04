# 源码解析 - Input System底层实现机制

> Unity Input System InputDevice抽象、Event Queue处理、Binding匹配算法源码分析 `#源码解析` `#输入系统` `#底层`

## 快速参考

```csharp
// Input System核心类
public class InputSystem
{
    public static InputSystem current { get; }
    public static IReadOnlyList<InputDevice> devices { get; }
    public static InputDevice GetDevice(string layoutName);

    public static void AddDevice(InputDevice device);
    public static void RemoveDevice(InputDevice device);

    public static void QueueEvent(InputEventPtr eventPtr);
    public static void Update();
}

// 获取当前设备
var keyboard = Keyboard.current;
var mouse = Mouse.current;
var gamepad = Gamepad.current;

// 读取输入
if (keyboard.wKey.wasPressedThisFrame)
{
    // W键按下
}

Vector2 mousePosition = mouse.position.ReadValue();
```

---

## 架构概览

### Input System核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                 Input System Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  InputDevice │  │InputControl  │  │InputEventPtr │      │
│  │   (设备)     │  │  (控件)     │  │  (事件指针)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │              Event Queue (事件队列)                  │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │            InputActionState (动作状态)               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│  │  │ Started │→ │Performed│→ │Canceled │           │   │
│  │  └─────────┘  └─────────┘  └─────────┘           │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │          InputProcessor (输入处理器)                 │   │
│  └────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │         IInputInteraction (交互处理器)              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 源码解析: InputSystem

### InputSystem.cs 核心代码

```csharp
// InputSystem.cs (Unity 2021.3)
public partial class InputSystem
{
    // 设备列表
    private List<InputDevice> m_Devices = new List<InputDevice>();

    // 事件队列
    private FourCC m_EventQueue;

    // 当前帧
    private int m_CurrentUpdate;

    // 是否已初始化
    private bool m_IsInitialized;

    /// <summary>
    /// 单例
    /// </summary>
    public static InputSystem current => s_Instance;
    private static InputSystem s_Instance;

    /// <summary>
    /// 获取所有设备
    /// </summary>
    public static IReadOnlyList<InputDevice> devices => s_Instance?.m_Devices;

    /// <summary>
    /// 添加设备
    /// </summary>
    public static void AddDevice(InputDevice device)
    {
        if (device == null)
            throw new ArgumentNullException(nameof(device));

        // 检查设备是否已存在
        if (s_Instance.m_Devices.Contains(device))
            return;

        // 添加到设备列表
        s_Instance.m_Devices.Add(device);

        // 添加设备到InputSystem
        s_Instance.AddDeviceInternal(device);

        // 触发设备添加事件
        s_Instance.onDeviceChange?.Invoke(
            new InputDeviceChangeInfo
            {
                deviceId = device.id,
                change = InputDeviceChange.Added,
                device = device
            });
    }

    /// <summary>
    /// 移除设备
    /// </summary>
    public static void RemoveDevice(InputDevice device)
    {
        if (device == null)
            return;

        // 从设备列表移除
        s_Instance.m_Devices.Remove(device);

        // 从InputSystem移除设备
        s_Instance.RemoveDeviceInternal(device);

        // 触发设备移除事件
        s_Instance.onDeviceChange?.Invoke(
            new InputDeviceChangeInfo
            {
                deviceId = device.id,
                change = InputDeviceChange.Removed,
                device = device
            });
    }

    /// <summary>
    /// 更新Input System
    /// </summary>
    public static void Update()
    {
        if (!s_Instance.m_IsInitialized)
            return;

        // 更新帧计数
        s_Instance.m_CurrentUpdate++;

        // 处理事件队列
        s_Instance.ProcessEvents();

        // 更新所有设备
        s_Instance.UpdateDevices();

        // 更新InputAction
        s_Instance.UpdateActions();
    }

    /// <summary>
    /// 处理事件队列
    /// </summary>
    private unsafe void ProcessEvents()
    {
        // 遍历事件队列
        var eventQueue = m_EventQueue;
        var eventCount = eventQueue.Count;

        for (int i = 0; i < eventCount; i++)
        {
            var eventPtr = eventQueue[i];

            // 处理事件
            ProcessEvent(eventPtr);
        }

        // 清空事件队列
        eventQueue.Clear();
    }

    /// <summary>
    /// 处理单个事件
    /// </summary>
    private unsafe void ProcessEvent(InputEventPtr eventPtr)
    {
        // 获取设备ID
        var deviceId = eventPtr.deviceId;

        // 查找设备
        var device = m_Devices.FirstOrDefault(d => d.id == deviceId);
        if (device == null)
            return;

        // 处理设备事件
        device.OnEvent(eventPtr);
    }

    /// <summary>
    /// 更新所有设备
    /// </summary>
    private void UpdateDevices()
    {
        foreach (var device in m_Devices)
        {
            device.Update();
        }
    }

    /// <summary>
    /// 更新InputAction
    /// </summary>
    private void UpdateActions()
    {
        // 遍历所有启用的Action
        foreach (var action in m_EnabledActions)
        {
            action.Update();
        }
    }
}
```

---

## 源码解析: InputDevice

### InputDevice.cs 核心代码

```csharp
// InputDevice.cs (Unity 2021.3)
public abstract class InputDevice : IInputStateCallbackReceiver
{
    // 设备ID
    public int id { get; }

    // 设备名称
    public string name { get; }

    // 设备布局
    public InputControlLayout layout { get; }

    // 设备状态
    protected InputState m_State;

    // 控件列表
    private List<InputControl> m_Controls = new List<InputControl>();

    /// <summary>
    /// 构造函数
    /// </summary>
    protected InputDevice()
    {
        id = s_NextDeviceId++;
        m_State = new InputState(this);
    }

    /// <summary>
    /// 添加控件
    /// </summary>
    protected T AddControl<T>(string name, string layout = null)
        where T : InputControl, new()
    {
        var control = new T();
        control.name = name;

        // 设置控件布局
        if (!string.IsNullOrEmpty(layout))
        {
            control.layout = InputSystem.LoadControlLayout(layout);
        }

        // 添加到控件列表
        m_Controls.Add(control);

        // 添加到状态
        m_State.AddControl(control);

        return control;
    }

    /// <summary>
    /// 更新设备
    /// </summary>
    public void Update()
    {
        // 读取设备输入
        Read();

        // 更新控件状态
        UpdateControls();
    }

    /// <summary>
    /// 读取设备输入（子类实现）
    /// </summary>
    protected abstract void Read();

    /// <summary>
    /// 更新控件状态
    /// </summary>
    private void UpdateControls()
    {
        foreach (var control in m_Controls)
        {
            // 检查控件值是否改变
            if (control.CheckStateChange())
            {
                // 触发控件改变事件
                onControlChange?.Invoke(control);
            }
        }
    }

    /// <summary>
    /// 处理事件
    /// </summary>
    public void OnEvent(InputEventPtr eventPtr)
    {
        // 更新设备状态
        m_State.ApplyEvent(eventPtr);
    }

    /// <summary>
    /// 查找子控件
    /// </summary>
    public InputControl TryGetChildControl(string path)
    {
        // 解析路径
        var parts = path.Split('/');

        InputControl currentControl = null;

        foreach (var part in parts)
        {
            if (currentControl == null)
            {
                // 查找顶级控件
                currentControl = m_Controls.FirstOrDefault(c => c.name == part);
            }
            else
            {
                // 查找子控件
                currentControl = currentControl.TryGetChildControl(part);
            }

            if (currentControl == null)
                return null;
        }

        return currentControl;
    }
}
```

### Keyboard实现

```csharp
// Keyboard.cs
public class Keyboard : InputDevice
{
    // 键位控件
    public KeyControl aKey { get; }
    public KeyControl bKey { get; }
    public KeyControl cKey { get; }
    // ... 所有键位

    /// <summary>
    /// 构造函数
    /// </summary>
    public Keyboard()
    {
        // 添加所有键位控件
        aKey = AddControl<KeyControl>("a", "Key");
        bKey = AddControl<KeyControl>("b", "Key");
        cKey = AddControl<KeyControl>("c", "Key");
        // ...

        // 设置设备布局
        layout = InputSystem.LoadControlLayout("Keyboard");
    }

    /// <summary>
    /// 读取键盘输入
    /// </summary>
    protected override void Read()
    {
        // 读取系统键盘状态
        var keyState = GetSystemKeyState();

        // 更新键位控件
        foreach (var control in m_Controls.OfType<KeyControl>())
        {
            bool pressed = keyState[control.keyCode];
            control.WriteValueIntoState(pressed ? 1 : 0, m_State);
        }
    }

    /// <summary>
    /// 获取系统键盘状态
    /// </summary>
    private bool[] GetSystemKeyState()
    {
        // 调用底层API获取键盘状态
        return NativeInput.GetKeyState();
    }
}
```

### Mouse实现

```csharp
// Mouse.cs
public class Mouse : InputDevice
{
    // 鼠标控件
    public AxisControl position { get; }
    public ButtonControl leftButton { get; }
    public ButtonControl rightButton { get; }
    public ButtonControl middleButton { get; }
    public AxisControl scroll { get; }
    public AxisControl delta { get; }

    // 上次位置
    private Vector2 m_LastPosition;

    /// <summary>
    /// 构造函数
    /// </summary>
    public Mouse()
    {
        // 添加鼠标控件
        position = AddControl<AxisControl>("position", "Axis");
        leftButton = AddControl<ButtonControl>("leftButton", "Button");
        rightButton = AddControl<ButtonControl>("rightButton", "Button");
        middleButton = AddControl<ButtonControl>("middleButton", "Button");
        scroll = AddControl<AxisControl>("scroll", "Axis");
        delta = AddControl<AxisControl>("delta", "Axis");

        // 设置设备布局
        layout = InputSystem.LoadControlLayout("Mouse");
    }

    /// <summary>
    /// 读取鼠标输入
    /// </summary>
    protected override void Read()
    {
        // 读取系统鼠标状态
        var mouseState = NativeInput.GetMouseState();

        // 更新位置
        position.WriteValueIntoState(mouseState.position, m_State);

        // 更新按钮状态
        leftButton.WriteValueIntoState(mouseState.leftButton ? 1 : 0, m_State);
        rightButton.WriteValueIntoState(mouseState.rightButton ? 1 : 0, m_State);
        middleButton.WriteValueIntoState(mouseState.middleButton ? 1 : 0, m_State);

        // 更新滚轮
        scroll.WriteValueIntoState(mouseState.scroll, m_State);

        // 计算增量
        Vector2 deltaValue = mouseState.position - m_LastPosition;
        delta.WriteValueIntoState(deltaValue, m_State);

        // 保存位置
        m_LastPosition = mouseState.position;
    }
}
```

---

## 源码解析: InputControl

### InputControl.cs 核心代码

```csharp
// InputControl.cs
public abstract class InputControl : IInputStateCallbackReceiver
{
    // 控件名称
    public string name { get; }

    // 控件布局
    public InputControlLayout layout { get; }

    // 父控件
    public InputControl parent { get; }

    // 子控件列表
    private List<InputControl> m_Children = new List<InputControl>();

    // 状态
    protected InputState m_State;

    /// <summary>
    /// 读取当前值
    /// </summary>
    public T ReadValue<T>()
    {
        return m_State.ReadValue<T>(this);
    }

    /// <summary>
    /// 检查状态是否改变
    /// </summary>
    public bool CheckStateChange()
    {
        var currentValue = ReadValueAsObject();
        var previousValue = m_PreviousValue;

        if (!Equals(currentValue, previousValue))
        {
            m_PreviousValue = currentValue;
            return true;
        }

        return false;
    }

    /// <summary>
    /// 写入值到状态
    /// </summary>
    public void WriteValueIntoState<T>(T value, InputState state)
    {
        state.WriteValue(value, this);
    }

    /// <summary>
    /// 查找子控件
    /// </summary>
    public InputControl TryGetChildControl(string name)
    {
        return m_Children.FirstOrDefault(c => c.name == name);
    }

    /// <summary>
    /// 处理事件
    /// </summary>
    public void OnEvent(InputEventPtr eventPtr)
    {
        // 更新状态
        m_State.ApplyEvent(eventPtr);
    }
}
```

---

## 源码解析: InputState

### InputState.cs 核心代码

```csharp
// InputState.cs
public class InputState
{
    // 设备
    private InputDevice m_Device;

    // 状态数据
    private byte[] m_StateData;

    // 控件状态索引
    private Dictionary<InputControl, int> m_ControlStateIndices = new();

    /// <summary>
    /// 构造函数
    /// </summary>
    public InputState(InputDevice device)
    {
        m_Device = device;
        AllocateStateData();
    }

    /// <summary>
    /// 分配状态数据
    /// </summary>
    private unsafe void AllocateStateData()
    {
        int totalSize = 0;

        // 计算总大小
        foreach (var control in m_Device.m_Controls)
        {
            m_ControlStateIndices[control] = totalSize;
            totalSize += control.layout.stateSize;
        }

        // 分配内存
        m_StateData = new byte[totalSize];
    }

    /// <summary>
    /// 读取值
    /// </summary>
    public T ReadValue<T>(InputControl control)
    {
        int offset = m_ControlStateIndices[control];
        int size = UnsafeUtility.SizeOf<T>();

        if (offset + size > m_StateData.Length)
            throw new ArgumentOutOfRangeException(nameof(control));

        // 读取数据
        unsafe
        {
            fixed (byte* data = m_StateData)
            {
                T value = UnsafeUtility.Read<T>(data + offset);
                return value;
            }
        }
    }

    /// <summary>
    /// 写入值
    /// </summary>
    public void WriteValue<T>(T value, InputControl control)
    {
        int offset = m_ControlStateIndices[control];
        int size = UnsafeUtility.SizeOf<T>();

        if (offset + size > m_StateData.Length)
            throw new ArgumentOutOfRangeException(nameof(control));

        // 写入数据
        unsafe
        {
            fixed (byte* data = m_StateData)
            {
                UnsafeUtility.Write(data + offset, value);
            }
        }
    }

    /// <summary>
    /// 应用事件
    /// </summary>
    public void ApplyEvent(InputEventPtr eventPtr)
    {
        // 读取事件数据
        int offset = eventPtr.controlOffset;
        int size = eventPtr.controlSize;

        // 检查边界
        if (offset + size > m_StateData.Length)
            return;

        // 写入事件数据
        unsafe
        {
            byte* eventData = (byte*)eventPtr.ToPointer();
            fixed (byte* data = m_StateData)
            {
                UnsafeUtility.MemCopy(eventData, data + offset, size);
            }
        }
    }
}
```

---

## 源码解析: InputAction

### InputAction.cs 核心代码

```csharp
// InputAction.cs
public class InputAction : IInputAction
{
    // 动作名称
    public string name { get; }

    // 动作类型
    public InputActionType type { get; }

    // 绑定列表
    private List<InputBinding> m_Bindings = new List<InputBinding>();

    // 交互处理器
    private IInputInteraction m_Interaction;

    // 处理器列表
    private List<InputProcessor> m_Processors = new List<InputProcessor>();

    // 是否已启用
    private bool m_Enabled;

    /// <summary>
    /// 添加绑定
    /// </summary>
    public InputBinding AddBinding(string path)
    {
        var binding = new InputBinding(path);
        m_Bindings.Add(binding);
        return binding;
    }

    /// <summary>
    /// 启用动作
    /// </summary>
    public void Enable()
    {
        if (m_Enabled)
            return;

        // 启用所有绑定
        foreach (var binding in m_Bindings)
        {
            binding.Enable();
        }

        m_Enabled = true;
    }

    /// <summary>
    /// 禁用动作
    /// </summary>
    public void Disable()
    {
        if (!m_Enabled)
            return;

        // 禁用所有绑定
        foreach (var binding in m_Bindings)
        {
            binding.Disable();
        }

        m_Enabled = false;
    }

    /// <summary>
    /// 更新动作
    /// </summary>
    public void Update()
    {
        if (!m_Enabled)
            return;

        // 更新所有绑定
        foreach (var binding in m_Bindings)
        {
            binding.Update();
        }
    }

    /// <summary>
    /// 触发回调
    /// </summary>
    public void Trigger(InputAction.CallbackContext context)
    {
        // 应用处理器
        foreach (var processor in m_Processors)
        {
            context.value = processor.Process(context.value, context.control);
        }

        // 应用交互
        if (m_Interaction != null)
        {
            m_Interaction.Process(this, context);
        }

        // 触发回调
        onPerformed?.Invoke(context);
    }

    /// <summary>
    /// 回调事件
    /// </summary>
    public event Action<InputAction.CallbackContext> onPerformed;
}
```

---

## 源码解析: InputBinding

### InputBinding.cs 核心代码

```csharp
// InputBinding.cs
public struct InputBinding : IEquatable<InputBinding>
{
    // 绑定路径
    public string path;

    // 交互配置
    public string interactions;

    // 处理器配置
    public string processors;

    // 控制组
    public string groups;

    // 动作名称
    public string action;

    // 绑定的控件
    private InputControl m_Control;

    /// <summary>
    /// 解析绑定
    /// </summary>
    public bool Parse(out InputControl control)
    {
        // 解析路径
        var parts = path.Split('/');

        if (parts.Length < 2)
        {
            control = null;
            return false;
        }

        string deviceType = parts[0].Substring(1, parts[0].Length - 2);
        string controlPath = string.Join("/", parts, 1, parts.Length - 1);

        // 查找设备
        var device = InputSystem.devices.FirstOrDefault(d => d.layout.name == deviceType);
        if (device == null)
        {
            control = null;
            return false;
        }

        // 查找控件
        control = device.TryGetChildControl(controlPath);

        if (control == null)
        {
            return false;
        }

        m_Control = control;
        return true;
    }

    /// <summary>
    /// 启用绑定
    /// </summary>
    public void Enable()
    {
        if (!Parse(out var control))
            return;

        // 添加监听器
        control.onControlChange += OnControlChange;
    }

    /// <summary>
    /// 禁用绑定
    /// </summary>
    public void Disable()
    {
        if (m_Control == null)
            return;

        // 移除监听器
        m_Control.onControlChange -= OnControlChange;
    }

    /// <summary>
    /// 控件改变回调
    /// </summary>
    private void OnControlChange(InputControl control)
    {
        // 创建回调上下文
        var context = new InputAction.CallbackContext
        {
            control = control,
            value = control.ReadValueAsObject(),
            phase = InputActionPhase.Performed
        };

        // 触发动作
        // (需要关联的InputAction)
    }
}
```

---

## 源码解析: Event Queue

### Event Queue实现

```csharp
// InputEventQueue.cs (简化版)
public class InputEventQueue
{
    // 事件列表
    private List<InputEvent> m_Events = new List<InputEvent>();

    // 事件索引
    private int m_EventIndex;

    /// <summary>
    /// 队列事件
    /// </summary>
    public void QueueEvent(InputEventPtr eventPtr)
    {
        // 添加到队列
        m_Events.Add(eventPtr);

        // 触发事件队列更新
        InputSystem.current.QueueEvent(eventPtr);
    }

    /// <summary>
    /// 处理事件
    /// </summary>
    public void ProcessEvents()
    {
        for (int i = 0; i < m_Events.Count; i++)
        {
            var eventPtr = m_Events[i];

            // 处理事件
            ProcessEvent(eventPtr);
        }

        // 清空队列
        m_Events.Clear();
    }

    /// <summary>
    /// 处理单个事件
    /// </summary>
    private void ProcessEvent(InputEventPtr eventPtr)
    {
        // 获取设备ID
        var deviceId = eventPtr.deviceId;

        // 查找设备
        var device = InputSystem.devices.FirstOrDefault(d => d.id == deviceId);
        if (device == null)
            return;

        // 处理设备事件
        device.OnEvent(eventPtr);
    }
}
```

---

## Binding匹配算法

### 匹配流程

```
输入事件
    ↓
解析设备路径
    ├─> <Keyboard>/w
    ├─> <Mouse>/leftButton
    └─> <Gamepad>/buttonSouth
    ↓
查找设备
    ├─> Keyboard.current
    ├─> Mouse.current
    └─> Gamepad.current
    ↓
查找控件
    ├─> device.wKey
    ├─> device.leftButton
    └─> device.buttonSouth
    ↓
检查控制组
    ├─> KeyboardMouse
    ├─> Gamepad
    └─> Touch
    ↓
匹配成功
    ↓
触发InputAction
```

### 匹配实现

```csharp
// BindingMatcher.cs
public class BindingMatcher
{
    /// <summary>
    /// 匹配绑定
    /// </summary>
    public static bool Match(InputBinding binding, InputEventPtr eventPtr)
    {
        // 解析绑定路径
        var parts = binding.path.Split('/');

        if (parts.Length < 2)
            return false;

        string deviceType = parts[0].Substring(1, parts[0].Length - 2);
        string controlPath = string.Join("/", parts, 1, parts.Length - 1);

        // 获取设备
        var device = InputSystem.devices.FirstOrDefault(d => d.layout.name == deviceType);
        if (device == null)
            return false;

        // 获取控件
        var control = device.TryGetChildControl(controlPath);
        if (control == null)
            return false;

        // 检查设备ID
        if (eventPtr.deviceId != device.id)
            return false;

        // 检查控制ID
        if (eventPtr.controlId != control.id)
            return false;

        return true;
    }

    /// <summary>
    /// 匹配复合绑定
    /// </summary>
    public static bool MatchComposite(InputBinding binding, InputEventPtr[] events)
    {
        // 解析复合绑定
        var compositeType = GetCompositeType(binding.path);

        switch (compositeType)
        {
            case "2DVector":
                return Match2DVector(binding, events);

            case "Axis":
                return MatchAxis(binding, events);

            case "OneModifier":
                return MatchOneModifier(binding, events);

            case "TwoModifiers":
                return MatchTwoModifiers(binding, events);

            default:
                return false;
        }
    }

    /// <summary>
    /// 匹配2D向量
    /// </summary>
    private static bool Match2DVector(InputBinding binding, InputEventPtr[] events)
    {
        // 2D向量需要4个方向键
        bool up = false, down = false, left = false, right = false;

        foreach (var eventPtr in events)
        {
            if (Match(binding, eventPtr))
            {
                var direction = GetCompositeDirection(eventPtr);

                switch (direction)
                {
                    case "Up":
                        up = true;
                        break;
                    case "Down":
                        down = true;
                        break;
                    case "Left":
                        left = true;
                        break;
                    case "Right":
                        right = true;
                        break;
                }
            }
        }

        // 至少需要一个方向
        return up || down || left || right;
    }
}
```

---

## 性能分析

### 输入系统开销

| 操作 | 开销 | 说明 |
|------|------|------|
| **设备轮询** | 0.05-0.15ms | 读取硬件状态 |
| **事件队列处理** | 0.02-0.08ms | 处理事件 |
| **Binding匹配** | 0.01-0.05ms | 匹配绑定 |
| **处理器执行** | 0.02-0.10ms | 执行处理器 |
| **回调触发** | 0.01-0.03ms | 调用回调 |
| **总计** | 0.11-0.41ms | 完整流程 |

### 优化策略

```csharp
// 优化1: 减少Binding数量
public class OptimizedBindings : MonoBehaviour
{
    [SerializeField] private InputAction moveAction;

    private void Start()
    {
        // 只添加必要的Binding
        moveAction.AddBinding("<Keyboard>/w");
        moveAction.AddBinding("<Keyboard>/s");
        moveAction.AddBinding("<Keyboard>/a");
        moveAction.AddBinding("<Keyboard>/d");

        // 不要添加过多备用Binding
    }
}

// 优化2: 使用事件替代轮询
public class EventDriven : MonoBehaviour
{
    [SerializeField] private InputAction jumpAction;

    private void OnEnable()
    {
        // 使用事件
        jumpAction.performed += OnJumpPerformed;
    }

    private void OnJumpPerformed(InputAction.CallbackContext context)
    {
        // 跳跃逻辑
    }
}

// 优化3: 减少处理器数量
public class OptimizedProcessors : MonoBehaviour
{
    [SerializeField] private InputAction moveAction;

    private void Start()
    {
        // 只在必要时添加处理器
        if (Application.platform == RuntimePlatform.Android)
        {
            moveAction.bindings[0].addProcessor<StickDeadzoneProcessor>();
        }
    }
}
```

---

## 常见问题

### Q1: 如何自定义InputDevice？

```csharp
// 自定义设备
public class CustomDevice : InputDevice
{
    public ButtonControl customButton { get; }

    public CustomDevice()
    {
        // 添加自定义控件
        customButton = AddControl<ButtonControl>("customButton", "Button");

        // 设置设备布局
        layout = InputSystem.LoadControlLayout("CustomDevice");
    }

    protected override void Read()
    {
        // 读取自定义设备输入
        bool pressed = ReadCustomInput();
        customButton.WriteValueIntoState(pressed ? 1 : 0, m_State);
    }

    private bool ReadCustomInput()
    {
        // 读取自定义硬件输入
        return false;
    }
}

// 注册自定义设备
InputSystem.AddDevice(new CustomDevice());
```

### Q2: 如何调试输入事件？

```csharp
// 输入调试器
public class InputDebugger : MonoBehaviour
{
    private void Update()
    {
        // 检查键盘输入
        if (Keyboard.current != null)
        {
            foreach (var key in Keyboard.current.allKeys)
            {
                if (key.wasPressedThisFrame)
                {
                    Debug.Log($"Key pressed: {key.name}");
                }
            }
        }

        // 检查鼠标输入
        if (Mouse.current != null)
        {
            if (Mouse.current.leftButton.wasPressedThisFrame)
            {
                Debug.Log($"Mouse pressed at: {Mouse.current.position.ReadValue()}");
            }
        }

        // 检查手柄输入
        if (Gamepad.current != null)
        {
            if (Gamepad.current.buttonSouth.wasPressedThisFrame)
            {
                Debug.Log($"Gamepad button pressed");
            }
        }
    }
}
```

---

## 相关链接

- 设计原理: [新输入系统架构深度解析](设计原理-新输入系统架构深度解析.md)
- 性能数据: [输入系统性能基准测试](性能数据-输入系统性能基准测试.md)
- 实战案例: [多平台输入统一架构设计](实战案例-多平台输入统一架构设计.md)
- 最佳实践: [输入系统使用指南](../../学习/01-脚本与架构/输入系统使用指南.md)

---

*创建日期: 2026-03-04*
*Unity版本: 2021.3 LTS*
*Input System版本: 1.3.0*
