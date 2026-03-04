# 代码片段 - WebSocket客户端

> Unity中WebSocket客户端实现方案 `#网络编程` `#WebSocket` `#实时通信`

## 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **WebSocketSharp** | 纯C#、无依赖 | 更新缓慢 | 简单项目 |
| **Native WebSocket** | 性能好、跨平台 | 需要原生插件 | 生产环境 |
| **Best HTTP/2** | 功能全、稳定 | 付费 | 商业项目 |
| **Unity Netcode** | 官方支持 | 学习曲线高 | 多人游戏 |

---

## 方案一：Native WebSocket（推荐）

### 安装

```bash
# 通过UPM安装
https://github.com/endel/NativeWebSocket.git#upm
```

### 基础实现

```csharp
using System;
using System.Text;
using System.Threading.Tasks;
using NativeWebSocket;
using UnityEngine;

/// <summary>
/// Native WebSocket客户端
/// </summary>
public class NativeWebSocketClient : MonoBehaviour
{
    [Header("连接配置")]
    [SerializeField] private string serverUrl = "ws://localhost:8080";
    [SerializeField] private float reconnectInterval = 5f;
    [SerializeField] private bool autoReconnect = true;

    public bool IsConnected { get; private set; }

    public event Action OnConnected;
    public event Action OnDisconnected;
    public event Action<string> OnMessageReceived;
    public event Action<byte[]> OnBinaryReceived;
    public event Action<string> OnError;

    private WebSocket websocket;

    /// <summary>
    /// 连接服务器
    /// </summary>
    public async Task ConnectAsync()
    {
        if (websocket != null)
        {
            Debug.LogWarning("已存在连接");
            return;
        }

        try
        {
            websocket = new WebSocket(serverUrl);

            // 注册事件
            websocket.OnOpen += OnWebSocketOpen;
            websocket.OnMessage += OnWebSocketMessage;
            websocket.OnError += OnWebSocketError;
            websocket.OnClose += OnWebSocketClose;

            Debug.Log($"正在连接: {serverUrl}");
            await websocket.Connect();
        }
        catch (Exception ex)
        {
            Debug.LogError($"连接失败: {ex.Message}");
            HandleError(ex.Message);
        }
    }

    private void OnWebSocketOpen()
    {
        IsConnected = true;
        Debug.Log("WebSocket连接已建立");
        OnConnected?.Invoke();
    }

    private void OnWebSocketMessage(byte[] data)
    {
        // 判断是文本还是二进制
        if (IsTextMessage(data))
        {
            string message = Encoding.UTF8.GetString(data);
            Debug.Log($"收到文本消息: {message}");
            OnMessageReceived?.Invoke(message);
        }
        else
        {
            Debug.Log($"收到二进制消息: {data.Length}字节");
            OnBinaryReceived?.Invoke(data);
        }
    }

    private void OnWebSocketError(string error)
    {
        Debug.LogError($"WebSocket错误: {error}");
        HandleError(error);
    }

    private void OnWebSocketClose(WebSocketCloseCode closeCode)
    {
        IsConnected = false;
        Debug.Log($"WebSocket关闭: {closeCode}");
        OnDisconnected?.Invoke();

        if (autoReconnect)
        {
            _ = ReconnectAsync();
        }
    }

    /// <summary>
    /// 发送文本消息
    /// </summary>
    public async Task SendTextAsync(string message)
    {
        if (!IsConnected || websocket == null)
        {
            Debug.LogWarning("未连接");
            return;
        }

        try
        {
            await websocket.SendText(message);
            Debug.Log($"已发送: {message}");
        }
        catch (Exception ex)
        {
            Debug.LogError($"发送失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 发送二进制消息
    /// </summary>
    public async Task SendBinaryAsync(byte[] data)
    {
        if (!IsConnected || websocket == null)
        {
            Debug.LogWarning("未连接");
            return;
        }

        try
        {
            await websocket.Send(data);
        }
        catch (Exception ex)
        {
            Debug.LogError($"发送失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 断开连接
    /// </summary>
    public async Task DisconnectAsync()
    {
        if (websocket == null) return;

        autoReconnect = false;
        try
        {
            await websocket.Close();
        }
        catch (Exception ex)
        {
            Debug.LogError($"断开连接错误: {ex.Message}");
        }
        finally
        {
            Cleanup();
        }
    }

    private async Task ReconnectAsync()
    {
        Debug.Log($"将在 {reconnectInterval} 秒后重连...");
        await Task.Delay(TimeSpan.FromSeconds(reconnectInterval));

        if (!IsConnected)
        {
            Cleanup();
            await ConnectAsync();
        }
    }

    private void HandleError(string error)
    {
        OnError?.Invoke(error);
    }

    private void Cleanup()
    {
        if (websocket != null)
        {
            websocket.OnOpen -= OnWebSocketOpen;
            websocket.OnMessage -= OnWebSocketMessage;
            websocket.OnError -= OnWebSocketError;
            websocket.OnClose -= OnWebSocketClose;
            websocket = null;
        }
        IsConnected = false;
    }

    private bool IsTextMessage(byte[] data)
    {
        // 简单判断：检查是否为有效UTF-8文本
        try
        {
            _ = Encoding.UTF8.GetString(data);
            return true;
        }
        catch
        {
            return false;
        }
    }

    // Native WebSocket需要在主线程调用DispatchMessageQueue
    private void Update()
    {
        websocket?.DispatchMessageQueue();
    }

    private async void OnDestroy()
    {
        await DisconnectAsync();
    }
}
```

---

## 方案二：WebSocketSharp

### 安装

```bash
# 通过NuGet或下载DLL
# https://github.com/sta/websocket-sharp
```

### 实现

```csharp
using System;
using System.Text;
using UnityEngine;
using WebSocketSharp;

/// <summary>
/// WebSocketSharp客户端
/// </summary>
public class WebSocketSharpClient : MonoBehaviour
{
    [SerializeField] private string serverUrl = "ws://localhost:8080";

    public bool IsConnected => websocket?.ReadyState == WebSocketState.Open;

    public event Action OnConnected;
    public event Action OnDisconnected;
    public event Action<string> OnMessageReceived;
    public event Action<string> OnError;

    private WebSocket websocket;

    public void Connect()
    {
        if (websocket != null)
        {
            Debug.LogWarning("已存在连接");
            return;
        }

        websocket = new WebSocket(serverUrl);

        websocket.OnOpen += (sender, e) =>
        {
            Debug.Log("WebSocket连接已建立");
            OnConnected?.Invoke();
        };

        websocket.OnMessage += (sender, e) =>
        {
            if (e.IsText)
            {
                Debug.Log($"收到消息: {e.Data}");
                OnMessageReceived?.Invoke(e.Data);
            }
            else if (e.IsBinary)
            {
                Debug.Log($"收到二进制数据: {e.RawData.Length}字节");
                // 处理二进制数据
            }
        };

        websocket.OnError += (sender, e) =>
        {
            Debug.LogError($"WebSocket错误: {e.Message}");
            OnError?.Invoke(e.Message);
        };

        websocket.OnClose += (sender, e) =>
        {
            Debug.Log($"WebSocket关闭: {e.Code} - {e.Reason}");
            OnDisconnected?.Invoke();
        };

        websocket.ConnectAsync();
    }

    public void Send(string message)
    {
        if (!IsConnected)
        {
            Debug.LogWarning("未连接");
            return;
        }

        websocket.Send(message);
    }

    public void Send(byte[] data)
    {
        if (!IsConnected)
        {
            Debug.LogWarning("未连接");
            return;
        }

        websocket.Send(data);
    }

    public void Disconnect()
    {
        if (websocket != null)
        {
            websocket.CloseAsync();
            websocket = null;
        }
    }

    private void OnDestroy()
    {
        Disconnect();
    }
}
```

---

## 完整消息处理系统

### 消息定义

```csharp
/// <summary>
/// WebSocket消息类型
/// </summary>
public enum WsMessageType : byte
{
    // 系统
    Heartbeat = 0,
    Auth = 1,

    // 游戏
    PlayerJoin = 10,
    PlayerLeave = 11,
    PlayerMove = 12,
    Chat = 20,
}

/// <summary>
/// 消息基类
/// </summary>
public interface IWsMessage
{
    WsMessageType Type { get; }
}

/// <summary>
/// 位置同步消息
/// </summary>
[Serializable]
public struct PlayerMoveMessage : IWsMessage
{
    public WsMessageType Type => WsMessageType.PlayerMove;

    public int playerId;
    public float x, y, z;
    public float timestamp;

    public static PlayerMoveMessage Create(int id, Vector3 pos)
    {
        return new PlayerMoveMessage
        {
            playerId = id,
            x = pos.x,
            y = pos.y,
            z = pos.z,
            timestamp = Time.time
        };
    }
}

/// <summary>
/// 聊天消息
/// </summary>
[Serializable]
public struct ChatMessage : IWsMessage
{
    public WsMessageType Type => WsMessageType.Chat;

    public int senderId;
    public string content;
    public long timestamp;
}
```

### 消息序列化（JSON）

```csharp
using UnityEngine;

/// <summary>
/// JSON消息序列化器
/// </summary>
public static class WsMessageSerializer
{
    /// <summary>
    /// 序列化消息为JSON
    /// </summary>
    public static string Serialize<T>(T message) where T : IWsMessage
    {
        var wrapper = new MessageWrapper<T>
        {
            type = (byte)message.Type,
            data = message
        };
        return JsonUtility.ToJson(wrapper);
    }

    /// <summary>
    /// 解析消息类型
    /// </summary>
    public static WsMessageType ParseType(string json)
    {
        var typeInfo = JsonUtility.FromJson<TypeOnly>(json);
        return (WsMessageType)typeInfo.type;
    }

    /// <summary>
    /// 反序列化消息
    /// </summary>
    public static T Deserialize<T>(string json) where T : IWsMessage
    {
        var wrapper = JsonUtility.FromJson<MessageWrapper<T>>(json);
        return wrapper.data;
    }

    [Serializable]
    private struct MessageWrapper<T>
    {
        public byte type;
        public T data;
    }

    [Serializable]
    private struct TypeOnly
    {
        public byte type;
    }
}
```

### 消息处理器

```csharp
using System.Collections.Generic;

/// <summary>
/// WebSocket消息分发器
/// </summary>
public class WsMessageDispatcher : MonoBehaviour
{
    private readonly Dictionary<WsMessageType, Action<string>> handlers
        = new Dictionary<WsMessageType, Action<string>>();

    /// <summary>
    /// 注册消息处理器
    /// </summary>
    public void Register<T>(Action<T> handler) where T : struct, IWsMessage
    {
        var type = default(T).Type;

        if (handlers.ContainsKey(type))
        {
            Debug.LogWarning($"消息类型 {type} 已有处理器，将被覆盖");
        }

        handlers[type] = json =>
        {
            var message = WsMessageSerializer.Deserialize<T>(json);
            handler(message);
        };
    }

    /// <summary>
    /// 注销消息处理器
    /// </summary>
    public void Unregister<T>() where T : struct, IWsMessage
    {
        var type = default(T).Type;
        handlers.Remove(type);
    }

    /// <summary>
    /// 分发消息
    /// </summary>
    public void Dispatch(string json)
    {
        try
        {
            var type = WsMessageSerializer.ParseType(json);

            if (handlers.TryGetValue(type, out var handler))
            {
                handler(json);
            }
            else
            {
                Debug.LogWarning($"未处理的消息类型: {type}");
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"消息解析失败: {ex.Message}");
        }
    }
}
```

### 完整客户端示例

```csharp
/// <summary>
/// 完整的WebSocket客户端
/// </summary>
public class GameWebSocketClient : MonoBehaviour
{
    [Header("配置")]
    [SerializeField] private string serverUrl = "ws://localhost:8080";
    [SerializeField] private float heartbeatInterval = 30f;

    private NativeWebSocketClient wsClient;
    private WsMessageDispatcher dispatcher;
    private float lastHeartbeatTime;

    public bool IsConnected => wsClient?.IsConnected ?? false;

    public event Action OnConnected;
    public event Action OnDisconnected;

    private void Awake()
    {
        wsClient = gameObject.AddComponent<NativeWebSocketClient>();
        dispatcher = new WsMessageDispatcher();

        SetupEventHandlers();
        RegisterMessageHandlers();
    }

    private void SetupEventHandlers()
    {
        wsClient.OnConnected += () =>
        {
            Debug.Log("已连接到服务器");
            OnConnected?.Invoke();

            // 发送认证
            SendAuth();
        };

        wsClient.OnDisconnected += () =>
        {
            Debug.Log("与服务器断开连接");
            OnDisconnected?.Invoke();
        };

        wsClient.OnMessageReceived += OnMessageReceived;
        wsClient.OnError += (error) => Debug.LogError($"连接错误: {error}");
    }

    private void RegisterMessageHandlers()
    {
        dispatcher.Register<PlayerMoveMessage>(OnPlayerMove);
        dispatcher.Register<ChatMessage>(OnChatMessage);
    }

    public async void Connect()
    {
        await wsClient.ConnectAsync();
    }

    public async void Disconnect()
    {
        await wsClient.DisconnectAsync();
    }

    /// <summary>
    /// 发送认证消息
    /// </summary>
    private void SendAuth()
    {
        var auth = new AuthMessage
        {
            token = PlayerPrefs.GetString("auth_token", ""),
            deviceId = SystemInfo.deviceUniqueIdentifier
        };
        Send(auth);
    }

    /// <summary>
    /// 发送消息
    /// </summary>
    public void Send<T>(T message) where T : struct, IWsMessage
    {
        string json = WsMessageSerializer.Serialize(message);
        _ = wsClient.SendTextAsync(json);
    }

    private void OnMessageReceived(string json)
    {
        dispatcher.Dispatch(json);
    }

    private void OnPlayerMove(PlayerMoveMessage msg)
    {
        // 处理玩家移动
        Debug.Log($"玩家 {msg.playerId} 移动到 ({msg.x}, {msg.y}, {msg.z})");
    }

    private void OnChatMessage(ChatMessage msg)
    {
        // 处理聊天消息
        Debug.Log($"[{msg.senderId}]: {msg.content}");
    }

    private void Update()
    {
        // 心跳
        if (IsConnected && Time.time - lastHeartbeatTime >= heartbeatInterval)
        {
            SendHeartbeat();
            lastHeartbeatTime = Time.time;
        }
    }

    private void SendHeartbeat()
    {
        var heartbeat = new HeartbeatMessage
        {
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
        };
        Send(heartbeat);
    }

    private async void OnDestroy()
    {
        await wsClient.DisconnectAsync();
    }
}

// 额外的消息类型
[Serializable]
public struct AuthMessage : IWsMessage
{
    public WsMessageType Type => WsMessageType.Auth;
    public string token;
    public string deviceId;
}

[Serializable]
public struct HeartbeatMessage : IWsMessage
{
    public WsMessageType Type => WsMessageType.Heartbeat;
    public long timestamp;
}
```

---

## 常见问题

### 1. 连接超时

```csharp
// 添加连接超时处理
public async Task ConnectWithTimeout(int timeoutMs = 5000)
{
    var cts = new System.Threading.CancellationTokenSource(timeoutMs);

    try
    {
        await websocket.Connect();
    }
    catch (OperationCanceledException)
    {
        Debug.LogError("连接超时");
        throw new TimeoutException("WebSocket连接超时");
    }
}
```

### 2. 消息分片

```csharp
// 处理大消息分片
private readonly List<byte> messageBuffer = new List<byte>();
private int expectedLength = -1;

private void OnBinaryMessage(byte[] data)
{
    if (expectedLength == -1)
    {
        // 读取消息头（前4字节为长度）
        expectedLength = BitConverter.ToInt32(data, 0);
        messageBuffer.AddRange(data.Skip(4));
    }
    else
    {
        messageBuffer.AddRange(data);
    }

    if (messageBuffer.Count >= expectedLength)
    {
        // 消息完整，处理
        ProcessCompleteMessage(messageBuffer.ToArray());
        messageBuffer.Clear();
        expectedLength = -1;
    }
}
```

### 3. 重连策略

```csharp
// 指数退避重连
private int retryCount = 0;
private const int MaxRetry = 10;

private async Task ReconnectWithBackoff()
{
    if (retryCount >= MaxRetry)
    {
        Debug.LogError("达到最大重连次数");
        return;
    }

    int delay = Mathf.Min(1000 * (1 << retryCount), 30000);  // 最大30秒
    retryCount++;

    Debug.Log($"将在 {delay/1000f:F1} 秒后重连 (第{retryCount}次)");
    await Task.Delay(delay);

    await ConnectAsync();
}
```

---

## 相关链接

- [TCP客户端](代码片段-TCP客户端.md)
- [网络同步模型](最佳实践-网络同步模型.md)
- [踩坑记录-网络常见问题](踩坑记录-网络常见问题.md)
