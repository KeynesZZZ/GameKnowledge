---
title: 【教程】Socket编程基础
tags: [Unity, 网络系统, Socket, 教程]
category: 核心系统/网络系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: Socket网络编程基础教程
unity_version: 2021.3+
---
# Socket 编程基础

> 第1课 | 网络编程实战模块

## 1. TCP 编程

### 1.1 TCP 服务器

```csharp
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

public class TcpServer
{
    private TcpListener listener;
    private int port = 8888;
    private bool isRunning = false;

    public async Task StartAsync()
    {
        listener = new TcpListener(IPAddress.Any, port);
        listener.Start();
        isRunning = true;

        Debug.Log($"服务器启动，监听端口 {port}");

        while (isRunning)
        {
            try
            {
                // 等待客户端连接
                TcpClient client = await listener.AcceptTcpClientAsync();
                _ = HandleClientAsync(client);  // 不等待，继续接受新连接
            }
            catch (Exception ex)
            {
                Debug.LogError($"接受连接失败: {ex.Message}");
            }
        }
    }

    private async Task HandleClientAsync(TcpClient client)
    {
        Debug.Log($"客户端连接: {((IPEndPoint)client.Client.RemoteEndPoint).Address}");

        try
        {
            using (client)
            {
                NetworkStream stream = client.GetStream();
                byte[] buffer = new byte[4096];

                while (client.Connected)
                {
                    // 读取数据
                    int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                    if (bytesRead == 0) break;  // 连接关闭

                    string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    Debug.Log($"收到: {message}");

                    // 回复
                    string response = $"Echo: {message}";
                    byte[] responseBytes = Encoding.UTF8.GetBytes(response);
                    await stream.WriteAsync(responseBytes, 0, responseBytes.Length);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"客户端处理错误: {ex.Message}");
        }

        Debug.Log("客户端断开");
    }

    public void Stop()
    {
        isRunning = false;
        listener?.Stop();
    }
}
```

### 1.2 TCP 客户端

```csharp
public class TcpClient
{
    private System.Net.Sockets.TcpClient client;
    private NetworkStream stream;
    private bool isConnected = false;

    public async Task ConnectAsync(string host, int port)
    {
        client = new System.Net.Sockets.TcpClient();
        await client.ConnectAsync(host, port);
        stream = client.GetStream();
        isConnected = true;

        Debug.Log($"已连接到 {host}:{port}");

        // 启动接收循环
        _ = ReceiveLoopAsync();
    }

    private async Task ReceiveLoopAsync()
    {
        byte[] buffer = new byte[4096];

        try
        {
            while (isConnected)
            {
                int bytesRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                if (bytesRead == 0)
                {
                    isConnected = false;
                    Debug.Log("服务器断开连接");
                    break;
                }

                string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                OnMessageReceived?.Invoke(message);
            }
        }
        catch (Exception ex)
        {
            Debug.LogError($"接收错误: {ex.Message}");
        }
    }

    public async Task SendAsync(string message)
    {
        if (!isConnected) return;

        byte[] data = Encoding.UTF8.GetBytes(message);
        await stream.WriteAsync(data, 0, data.Length);
    }

    public void Disconnect()
    {
        isConnected = false;
        stream?.Close();
        client?.Close();
    }

    public event Action<string> OnMessageReceived;
}
```

---

## 2. UDP 编程

### 2.1 UDP 服务器

```csharp
using System.Net;
using System.Net.Sockets;

public class UdpServer
{
    private UdpClient udpServer;
    private int port = 8889;
    private bool isRunning = false;

    public async Task StartAsync()
    {
        udpServer = new UdpClient(port);
        isRunning = true;

        Debug.Log($"UDP 服务器启动，端口 {port}");

        while (isRunning)
        {
            try
            {
                // 接收数据
                UdpReceiveResult result = await udpServer.ReceiveAsync();
                byte[] data = result.Buffer;
                IPEndPoint clientEP = result.RemoteEndPoint;

                string message = Encoding.UTF8.GetString(data);
                Debug.Log($"收到来自 {clientEP}: {message}");

                // 回复
                byte[] response = Encoding.UTF8.GetBytes($"Echo: {message}");
                await udpServer.SendAsync(response, response.Length, clientEP);
            }
            catch (Exception ex)
            {
                Debug.LogError($"UDP 接收错误: {ex.Message}");
            }
        }
    }

    public void Stop()
    {
        isRunning = false;
        udpServer?.Close();
    }
}
```

### 2.2 UDP 客户端

```csharp
public class UdpClient
{
    private System.Net.Sockets.UdpClient udpClient;
    private IPEndPoint serverEndPoint;
    private bool isRunning = false;

    public void Connect(string host, int port)
    {
        udpClient = new System.Net.Sockets.UdpClient();
        serverEndPoint = new IPEndPoint(IPAddress.Parse(host), port);
        isRunning = true;

        // UDP 是无连接的，这里只是设置目标地址
        _ = ReceiveLoopAsync();
    }

    private async Task ReceiveLoopAsync()
    {
        while (isRunning)
        {
            try
            {
                UdpReceiveResult result = await udpClient.ReceiveAsync();
                string message = Encoding.UTF8.GetString(result.Buffer);
                OnMessageReceived?.Invoke(message);
            }
            catch (Exception ex)
            {
                Debug.LogError($"UDP 接收错误: {ex.Message}");
            }
        }
    }

    public async Task SendAsync(string message)
    {
        byte[] data = Encoding.UTF8.GetBytes(message);
        await udpClient.SendAsync(data, data.Length, serverEndPoint);
    }

    public void Close()
    {
        isRunning = false;
        udpClient?.Close();
    }

    public event Action<string> OnMessageReceived;
}
```

---

## 3. 消息协议

### 3.1 消息格式设计

```csharp
// 消息头格式
// [长度(4字节)][类型(2字节)][数据(N字节)]

public enum MessageType : ushort
{
    Login = 1,
    LoginResult = 2,
    PlayerMove = 3,
    PlayerAttack = 4,
    Chat = 5
}

public class MessageProtocol
{
    private const int HEADER_SIZE = 6;  // 4 + 2

    // 编码消息
    public static byte[] Encode(MessageType type, byte[] data)
    {
        int totalLength = HEADER_SIZE + data.Length;
        byte[] buffer = new byte[totalLength];

        // 写入长度
        BitConverter.GetBytes(totalLength).CopyTo(buffer, 0);

        // 写入类型
        BitConverter.GetBytes((ushort)type).CopyTo(buffer, 4);

        // 写入数据
        data.CopyTo(buffer, HEADER_SIZE);

        return buffer;
    }

    // 解码消息
    public static (MessageType type, byte[] data) Decode(byte[] buffer)
    {
        if (buffer.Length < HEADER_SIZE)
            throw new Exception("消息太短");

        int length = BitConverter.ToInt32(buffer, 0);
        MessageType type = (MessageType)BitConverter.ToUInt16(buffer, 4);

        byte[] data = new byte[length - HEADER_SIZE];
        Array.Copy(buffer, HEADER_SIZE, data, 0, data.Length);

        return (type, data);
    }
}
```

### 3.2 消息处理器

```csharp
public class MessageHandler
{
    private Dictionary<MessageType, Action<byte[]>> handlers = new();

    public void RegisterHandler(MessageType type, Action<byte[]> handler)
    {
        handlers[type] = handler;
    }

    public void ProcessMessage(MessageType type, byte[] data)
    {
        if (handlers.TryGetValue(type, out var handler))
        {
            handler.Invoke(data);
        }
        else
        {
            Debug.LogWarning($"未注册的消息类型: {type}");
        }
    }
}

// 使用
public class GameClient : MonoBehaviour
{
    private MessageHandler messageHandler;

    private void Start()
    {
        messageHandler = new MessageHandler();

        // 注册处理器
        messageHandler.RegisterHandler(MessageType.LoginResult, OnLoginResult);
        messageHandler.RegisterHandler(MessageType.PlayerMove, OnPlayerMove);
    }

    private void OnLoginResult(byte[] data)
    {
        // 解析登录结果
        bool success = data[0] == 1;
        Debug.Log($"登录结果: {success}");
    }

    private void OnPlayerMove(byte[] data)
    {
        // 解析移动数据
        float x = BitConverter.ToSingle(data, 0);
        float y = BitConverter.ToSingle(data, 4);
        float z = BitConverter.ToSingle(data, 8);

        Debug.Log($"玩家移动到: ({x}, {y}, {z})");
    }
}
```

---

## 4. 粘包处理

### 4.1 接收缓冲区

```csharp
public class PacketReceiver
{
    private byte[] buffer = new byte[8192];
    private int bufferOffset = 0;

    public void OnDataReceived(byte[] data, int length)
    {
        // 将新数据追加到缓冲区
        Array.Copy(data, 0, buffer, bufferOffset, length);
        bufferOffset += length;

        // 处理完整的消息
        ProcessBuffer();
    }

    private void ProcessBuffer()
    {
        while (bufferOffset >= 4)  // 至少有长度字段
        {
            // 读取消息长度
            int messageLength = BitConverter.ToInt32(buffer, 0);

            if (bufferOffset < messageLength)
                break;  // 数据不完整，等待更多数据

            // 提取完整消息
            byte[] messageData = new byte[messageLength];
            Array.Copy(buffer, 0, messageData, 0, messageLength);

            // 处理消息
            var (type, data) = MessageProtocol.Decode(messageData);
            OnMessageReady?.Invoke(type, data);

            // 从缓冲区移除已处理的消息
            int remaining = bufferOffset - messageLength;
            if (remaining > 0)
            {
                Array.Copy(buffer, messageLength, buffer, 0, remaining);
            }
            bufferOffset = remaining;
        }
    }

    public event Action<MessageType, byte[]> OnMessageReady;
}
```

---

## 5. 心跳机制

### 5.1 心跳实现

```csharp
public class Heartbeat
{
    private float interval = 5f;  // 5秒
    private float timeout = 15f;  // 15秒超时
    private float lastSendTime;
    private float lastReceiveTime;
    private Action sendHeartbeat;
    private Action onTimeout;

    public void Initialize(Action sendHeartbeat, Action onTimeout)
    {
        this.sendHeartbeat = sendHeartbeat;
        this.onTimeout = onTimeout;
        lastReceiveTime = Time.time;
    }

    public void Update()
    {
        float now = Time.time;

        // 发送心跳
        if (now - lastSendTime >= interval)
        {
            sendHeartbeat?.Invoke();
            lastSendTime = now;
        }

        // 检测超时
        if (now - lastReceiveTime >= timeout)
        {
            Debug.LogWarning("连接超时");
            onTimeout?.Invoke();
        }
    }

    public void OnHeartbeatReceived()
    {
        lastReceiveTime = Time.time;
    }
}
```

---

## 本课小结

### TCP vs UDP

| 特性 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接 | 无连接 |
| 可靠性 | 可靠 | 不可靠 |
| 顺序 | 有序 | 无序 |
| 速度 | 较慢 | 较快 |
| 适用 | 回合制、聊天 | 实时对战 |

### 消息协议设计要点

1. **长度前缀** - 解决粘包问题
2. **类型标识** - 区分消息类型
3. **序列化** - Protobuf/MessagePack
4. **心跳机制** - 检测连接状态

---

## 延伸阅读

- [Socket 编程指南](https://docs.microsoft.com/en-us/dotnet/framework/network-programming/)
- [TCP/IP 详解](https://book.douban.com/subject/1088054/)
