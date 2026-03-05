---
title: 【代码片段】TCP客户端
tags: [Unity, 网络系统, TCP, 代码片段]
category: 核心系统/网络系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: TCP客户端连接代码实现
unity_version: 2021.3+
---
# 代码片段 - TCP客户端

> Unity中基于Socket的TCP客户端实现 `#网络编程` `#TCP` `#Socket`

## 基础TCP客户端

### 简单实现

```csharp
using System;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

/// <summary>
/// 简单的TCP客户端示例
/// </summary>
public class SimpleTcpClient : MonoBehaviour
{
    [SerializeField] private string serverIp = "127.0.0.1";
    [SerializeField] private int serverPort = 8888;

    private TcpClient tcpClient;
    private NetworkStream stream;

    /// <summary>
    /// 连接服务器
    /// </summary>
    public async void Connect()
    {
        try
        {
            tcpClient = new TcpClient();
            await tcpClient.ConnectAsync(serverIp, serverPort);
            stream = tcpClient.GetStream();

            Debug.Log($"已连接到服务器 {serverIp}:{serverPort}");

            // 开始接收消息
            _ = ReceiveMessagesAsync();
        }
        catch (Exception ex)
        {
            Debug.LogError($"连接失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 发送消息
    /// </summary>
    public async void Send(string message)
    {
        if (stream == null || !stream.CanWrite)
        {
            Debug.LogError("未连接");
            return;
        }

        try
        {
            byte[] data = Encoding.UTF8.GetBytes(message);
            byte[] lengthPrefix = BitConverter.GetBytes(data.Length);

            // 发送长度前缀 + 数据
            await stream.WriteAsync(lengthPrefix, 0, lengthPrefix.Length);
            await stream.WriteAsync(data, 0, data.Length);

            Debug.Log($"已发送: {message}");
        }
        catch (Exception ex)
        {
            Debug.LogError($"发送失败: {ex.Message}");
        }
    }

    /// <summary>
    /// 接收消息循环
    /// </summary>
    private async System.Threading.Tasks.Task ReceiveMessagesAsync()
    {
        var lengthBuffer = new byte[4];
        var receiveBuffer = new byte[4096];

        try
        {
            while (tcpClient.Connected)
            {
                // 1. 读取消息长度
                int bytesRead = await ReadExactAsync(stream, lengthBuffer, 0, 4);
                if (bytesRead == 0) break;

                int messageLength = BitConverter.ToInt32(lengthBuffer, 0);

                // 2. 读取消息内容
                if (messageLength > receiveBuffer.Length)
                {
                    Debug.LogError($"消息过长: {messageLength}");
                    break;
                }

                bytesRead = await ReadExactAsync(stream, receiveBuffer, 0, messageLength);
                if (bytesRead == 0) break;

                string message = Encoding.UTF8.GetString(receiveBuffer, 0, messageLength);
                Debug.Log($"收到: {message}");

                // 触发事件（在主线程）
                OnMessageReceived?.Invoke(message);
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"接收错误: {ex.Message}");
        }
        finally
        {
            Disconnect();
        }
    }

    /// <summary>
    /// 精确读取指定字节数
    /// </summary>
    private static async System.Threading.Tasks.Task<int> ReadExactAsync(
        NetworkStream stream, byte[] buffer, int offset, int count)
    {
        int totalRead = 0;
        while (totalRead < count)
        {
            int read = await stream.ReadAsync(buffer, offset + totalRead, count - totalRead);
            if (read == 0) return 0;  // 连接关闭
            totalRead += read;
        }
        return totalRead;
    }

    /// <summary>
    /// 断开连接
    /// </summary>
    public void Disconnect()
    {
        stream?.Close();
        tcpClient?.Close();
        stream = null;
        tcpClient = null;
        Debug.Log("已断开连接");
    }

    /// <summary>
    /// 消息接收事件
    /// </summary>
    public event Action<string> OnMessageReceived;

    private void OnDestroy()
    {
        Disconnect();
    }
}
```

---

## 完整TCP客户端（带重连）

```csharp
using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

/// <summary>
/// 支持自动重连的TCP客户端
/// </summary>
public class TcpClientWithReconnect : MonoBehaviour
{
    [Header("连接配置")]
    [SerializeField] private string serverIp = "127.0.0.1";
    [SerializeField] private int serverPort = 8888;
    [SerializeField] private float reconnectInterval = 5f;
    [SerializeField] private int maxReconnectAttempts = 5;

    [Header("缓冲区配置")]
    [SerializeField] private int sendBufferSize = 8192;
    [SerializeField] private int receiveBufferSize = 8192;

    public bool IsConnected => tcpClient?.Connected ?? false;

    public event Action OnConnected;
    public event Action OnDisconnected;
    public event Action<string> OnMessageReceived;
    public event Action<Exception> OnError;

    private TcpClient tcpClient;
    private NetworkStream stream;
    private CancellationTokenSource cts;
    private int reconnectAttempts;
    private bool isReconnecting;
    private readonly object sendLock = new object();

    /// <summary>
    /// 开始连接
    /// </summary>
    public void Connect()
    {
        if (IsConnected) return;

        cts = new CancellationTokenSource();
        _ = ConnectAsync(cts.Token);
    }

    private async Task ConnectAsync(CancellationToken cancellationToken)
    {
        try
        {
            tcpClient = new TcpClient
            {
                SendBufferSize = sendBufferSize,
                ReceiveBufferSize = receiveBufferSize,
                NoDelay = true  // 禁用Nagle算法，减少延迟
            };

            Debug.Log($"正在连接 {serverIp}:{serverPort}...");

            await tcpClient.ConnectAsync(serverIp, serverPort, cancellationToken);

            stream = tcpClient.GetStream();
            reconnectAttempts = 0;
            isReconnecting = false;

            Debug.Log("连接成功");
            OnConnected?.Invoke();

            // 开始接收
            await ReceiveLoopAsync(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            Debug.Log("连接被取消");
        }
        catch (Exception ex)
        {
            HandleConnectionError(ex);
        }
    }

    /// <summary>
    /// 接收消息循环
    /// </summary>
    private async Task ReceiveLoopAsync(CancellationToken cancellationToken)
    {
        var lengthBuffer = new byte[4];

        try
        {
            while (!cancellationToken.IsCancellationRequested && IsConnected)
            {
                // 读取长度前缀
                if (!await ReadExactAsync(lengthBuffer, cancellationToken))
                    break;

                int messageLength = BitConverter.ToInt32(lengthBuffer, 0);

                // 防止恶意数据
                if (messageLength <= 0 || messageLength > 1024 * 1024)
                {
                    OnError?.Invoke(new Exception($"无效的消息长度: {messageLength}"));
                    break;
                }

                // 读取消息体
                var messageBuffer = new byte[messageLength];
                if (!await ReadExactAsync(messageBuffer, cancellationToken))
                    break;

                string message = Encoding.UTF8.GetString(messageBuffer);

                // 在主线程触发事件
                UnityMainThreadDispatcher.Enqueue(() =>
                {
                    OnMessageReceived?.Invoke(message);
                });
            }
        }
        catch (Exception ex)
        {
            if (!cancellationToken.IsCancellationRequested)
            {
                OnError?.Invoke(ex);
            }
        }
        finally
        {
            HandleDisconnection();
        }
    }

    /// <summary>
    /// 精确读取
    /// </summary>
    private async Task<bool> ReadExactAsync(byte[] buffer, CancellationToken cancellationToken)
    {
        int offset = 0;
        int remaining = buffer.Length;

        while (remaining > 0)
        {
            int read = await stream.ReadAsync(buffer, offset, remaining, cancellationToken);
            if (read == 0) return false;

            offset += read;
            remaining -= read;
        }

        return true;
    }

    /// <summary>
    /// 发送消息（线程安全）
    /// </summary>
    public bool Send(string message)
    {
        if (!IsConnected || stream == null) return false;

        lock (sendLock)
        {
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                byte[] lengthPrefix = BitConverter.GetBytes(data.Length);

                // 一次性发送长度+数据
                var packet = new byte[4 + data.Length];
                Buffer.BlockCopy(lengthPrefix, 0, packet, 0, 4);
                Buffer.BlockCopy(data, 0, packet, 4, data.Length);

                stream.Write(packet, 0, packet.Length);
                return true;
            }
            catch (Exception ex)
            {
                OnError?.Invoke(ex);
                return false;
            }
        }
    }

    /// <summary>
    /// 异步发送
    /// </summary>
    public async Task<bool> SendAsync(string message)
    {
        if (!IsConnected || stream == null) return false;

        try
        {
            byte[] data = Encoding.UTF8.GetBytes(message);
            byte[] lengthPrefix = BitConverter.GetBytes(data.Length);

            await stream.WriteAsync(lengthPrefix, 0, 4);
            await stream.WriteAsync(data, 0, data.Length);
            return true;
        }
        catch (Exception ex)
        {
            OnError?.Invoke(ex);
            return false;
        }
    }

    /// <summary>
    /// 处理连接错误
    /// </summary>
    private void HandleConnectionError(Exception ex)
    {
        Debug.LogError($"连接错误: {ex.Message}");
        OnError?.Invoke(ex);

        if (!isReconnecting && reconnectAttempts < maxReconnectAttempts)
        {
            isReconnecting = true;
            reconnectAttempts++;
            Debug.Log($"将在 {reconnectInterval} 秒后尝试重连 ({reconnectAttempts}/{maxReconnectAttempts})");
            Invoke(nameof(Connect), reconnectInterval);
        }
        else
        {
            HandleDisconnection();
        }
    }

    /// <summary>
    /// 处理断开连接
    /// </summary>
    private void HandleDisconnection()
    {
        bool wasConnected = IsConnected;

        stream?.Close();
        stream = null;
        tcpClient?.Close();
        tcpClient = null;

        if (wasConnected)
        {
            Debug.Log("连接已断开");
            OnDisconnected?.Invoke();
        }
    }

    /// <summary>
    /// 断开连接
    /// </summary>
    public void Disconnect()
    {
        isReconnecting = false;
        reconnectAttempts = maxReconnectAttempts;  // 阻止重连
        cts?.Cancel();
        HandleDisconnection();
    }

    private void OnDestroy()
    {
        Disconnect();
        cts?.Dispose();
    }
}

/// <summary>
/// 主线程调度器（简化版）
/// </summary>
public static class UnityMainThreadDispatcher
{
    private static readonly System.Collections.Concurrent.ConcurrentQueue<Action> queue
        = new System.Collections.Concurrent.ConcurrentQueue<Action>();

    public static void Enqueue(Action action)
    {
        queue.Enqueue(action);
    }

    // 需要在MonoBehaviour的Update中调用
    public static void Update()
    {
        while (queue.TryDequeue(out var action))
        {
            action?.Invoke();
        }
    }
}
```

---

## 消息协议设计

### 基础消息格式

```
┌────────────┬────────────┬─────────────────┐
│ Length (4) │ Type (2)   │ Payload (N)     │
│ 字节       │ 字节       │ 字节            │
└────────────┴────────────┴─────────────────┘
```

### 消息类型定义

```csharp
/// <summary>
/// 消息类型枚举
/// </summary>
public enum MessageType : short
{
    // 系统消息 0-99
    Heartbeat = 0,
    Handshake = 1,
    Disconnect = 2,

    // 登录消息 100-199
    LoginRequest = 100,
    LoginResponse = 101,

    // 游戏消息 200-299
    PlayerMove = 200,
    PlayerAttack = 201,
    ItemPickup = 202,
}

/// <summary>
/// 消息基类
/// </summary>
public interface IMessage
{
    MessageType Type { get; }
    byte[] Serialize();
    void Deserialize(byte[] data);
}

/// <summary>
/// 消息序列化工具
/// </summary>
public static class MessageSerializer
{
    /// <summary>
    /// 序列化完整消息包
    /// </summary>
    public static byte[] SerializePacket(IMessage message)
    {
        var payload = message.Serialize();
        var packet = new byte[6 + payload.Length];  // 4(length) + 2(type) + payload

        // 写入长度（不包含自身）
        BitConverter.TryWriteBytes(packet.AsSpan(0, 4), payload.Length + 2);

        // 写入消息类型
        BitConverter.TryWriteBytes(packet.AsSpan(4, 2), (short)message.Type);

        // 写入负载数据
        Buffer.BlockCopy(payload, 0, packet, 6, payload.Length);

        return packet;
    }

    /// <summary>
    /// 解析消息类型
    /// </summary>
    public static MessageType ParseMessageType(byte[] data, int offset = 0)
    {
        return (MessageType)BitConverter.ToInt16(data, offset);
    }
}
```

### 具体消息示例

```csharp
/// <summary>
/// 玩家移动消息
/// </summary>
public struct PlayerMoveMessage : IMessage
{
    public MessageType Type => MessageType.PlayerMove;

    public int PlayerId;
    public float X;
    public float Y;
    public float Z;
    public float Timestamp;

    public byte[] Serialize()
    {
        var data = new byte[20];  // 4 + 4 + 4 + 4 + 4
        int offset = 0;

        BitConverter.TryWriteBytes(data.AsSpan(offset), PlayerId); offset += 4;
        BitConverter.TryWriteBytes(data.AsSpan(offset), X); offset += 4;
        BitConverter.TryWriteBytes(data.AsSpan(offset), Y); offset += 4;
        BitConverter.TryWriteBytes(data.AsSpan(offset), Z); offset += 4;
        BitConverter.TryWriteBytes(data.AsSpan(offset), Timestamp);

        return data;
    }

    public void Deserialize(byte[] data)
    {
        int offset = 0;
        PlayerId = BitConverter.ToInt32(data, offset); offset += 4;
        X = BitConverter.ToSingle(data, offset); offset += 4;
        Y = BitConverter.ToSingle(data, offset); offset += 4;
        Z = BitConverter.ToSingle(data, offset); offset += 4;
        Timestamp = BitConverter.ToSingle(data, offset);
    }
}

/// <summary>
/// 登录请求消息
/// </summary>
public struct LoginRequestMessage : IMessage
{
    public MessageType Type => MessageType.LoginRequest;

    public string Username;
    public string Token;

    public byte[] Serialize()
    {
        var usernameBytes = Encoding.UTF8.GetBytes(Username ?? "");
        var tokenBytes = Encoding.UTF8.GetBytes(Token ?? "");

        var data = new byte[4 + usernameBytes.Length + 4 + tokenBytes.Length];
        int offset = 0;

        // 用户名
        BitConverter.TryWriteBytes(data.AsSpan(offset), usernameBytes.Length); offset += 4;
        Buffer.BlockCopy(usernameBytes, 0, data, offset, usernameBytes.Length); offset += usernameBytes.Length;

        // Token
        BitConverter.TryWriteBytes(data.AsSpan(offset), tokenBytes.Length); offset += 4;
        Buffer.BlockCopy(tokenBytes, 0, data, offset, tokenBytes.Length);

        return data;
    }

    public void Deserialize(byte[] data)
    {
        int offset = 0;

        int usernameLen = BitConverter.ToInt32(data, offset); offset += 4;
        Username = Encoding.UTF8.GetString(data, offset, usernameLen); offset += usernameLen;

        int tokenLen = BitConverter.ToInt32(data, offset); offset += 4;
        Token = Encoding.UTF8.GetString(data, offset, tokenLen);
    }
}
```

---

## 最佳实践

### 1. 使用对象池减少GC

```csharp
// 使用ArrayPool<byte>减少内存分配
using System.Buffers;

public async Task<byte[]> ReceiveMessageAsync()
{
    // 先读取长度
    var lengthBuffer = ArrayPool<byte>.Shared.Rent(4);
    try
    {
        await ReadExactAsync(stream, lengthBuffer, 4);
        int length = BitConverter.ToInt32(lengthBuffer, 0);

        // 租用足够大的缓冲区
        var buffer = ArrayPool<byte>.Shared.Rent(length);
        try
        {
            await ReadExactAsync(stream, buffer, length);

            // 复制数据返回（因为buffer会被归还）
            var result = new byte[length];
            Buffer.BlockCopy(buffer, 0, result, 0, length);
            return result;
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
        }
    }
    finally
    {
        ArrayPool<byte>.Shared.Return(lengthBuffer);
    }
}
```

### 2. 心跳机制

```csharp
/// <summary>
/// TCP心跳管理
/// </summary>
public class TcpHeartbeat
{
    private readonly TcpClientWithReconnect client;
    private readonly float heartbeatInterval;
    private float lastSendTime;
    private float lastReceiveTime;
    private readonly float timeout;

    public TcpHeartbeat(TcpClientWithReconnect client, float interval = 30f, float timeout = 60f)
    {
        this.client = client;
        this.heartbeatInterval = interval;
        this.timeout = timeout;
    }

    public void Update()
    {
        if (!client.IsConnected) return;

        float now = Time.time;

        // 发送心跳
        if (now - lastSendTime >= heartbeatInterval)
        {
            SendHeartbeat();
            lastSendTime = now;
        }

        // 检测超时
        if (now - lastReceiveTime >= timeout)
        {
            Debug.LogWarning("心跳超时，断开连接");
            client.Disconnect();
        }
    }

    private void SendHeartbeat()
    {
        var heartbeat = new HeartbeatMessage
        {
            Timestamp = Time.time
        };
        client.Send(MessageSerializer.SerializePacket(heartbeat));
    }

    public void OnMessageReceived()
    {
        lastReceiveTime = Time.time;
    }
}
```

### 3. 消息队列处理

```csharp
/// <summary>
/// 线程安全的消息队列
/// </summary>
public class MessageQueue
{
    private readonly ConcurrentQueue<byte[]> queue = new ConcurrentQueue<byte[]>();
    private const int MaxQueueSize = 1000;

    public bool Enqueue(byte[] message)
    {
        if (queue.Count >= MaxQueueSize)
        {
            Debug.LogWarning("消息队列已满，丢弃旧消息");
            queue.TryDequeue(out _);
        }

        queue.Enqueue(message);
        return true;
    }

    public bool TryDequeue(out byte[] message)
    {
        return queue.TryDequeue(out message);
    }

    public int Count => queue.Count;
}
```

---

## 相关链接

- [WebSocket客户端](代码片段-WebSocket客户端.md)
- [网络同步模型](最佳实践-网络同步模型.md)
- [网络问题清单](踩坑记录-网络常见问题.md)
