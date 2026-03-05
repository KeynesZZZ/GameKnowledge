---
title: 【设计原理】Unity网络同步
tags: [Unity, 高级主题, 网络同步, 设计原理]
category: 高级主题
created: 2026-03-05 08:41
updated: 2026-03-05 08:41
description: Unity网络同步原理与实现
unity_version: 2021.3+
---
# Unity网络同步

> 专题课程 | 多人游戏开发核心

## 1. 网络基础架构

### 1.1 网络模型对比

```
┌─────────────────────────────────────────────────────────────┐
│                    网络架构模型对比                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 服务器 authoritative                   │   │
│  │  ┌─────────┐                                         │   │
│  │  │ Server  │ ← 所有逻辑在服务器计算                    │   │
│  │  │  (权威)  │ ← 客户端只发送输入                       │   │
│  │  └────┬────┘                                         │   │
│  │       │                                              │   │
│  │  ┌────┴────┬─────────┬─────────┐                    │   │
│  │  ↓         ↓         ↓         ↓                    │   │
│  │ ┌───┐    ┌───┐    ┌───┐    ┌───┐                   │   │
│  │ │C1 │    │C2 │    │C3 │    │C4 │                   │   │
│  │ └───┘    └───┘    └───┘    └───┘                   │   │
│  │  优点：安全、一致、防作弊                              │   │
│  │  缺点：延迟感明显                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   P2P (Peer-to-Peer)                  │   │
│  │                                                     │   │
│  │          ┌───┐                                      │   │
│  │     ┌────│P1 │────┐                                │   │
│  │     │    └───┘    │                                │   │
│  │    ↓              ↓                                │   │
│  │  ┌───┐          ┌───┐                              │   │
│  │  │P2 │──────────│P3 │                              │   │
│  │  └───┘          └───┘                              │   │
│  │  优点：无服务器成本                                  │   │
│  │  缺点：同步复杂、难以防作弊                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              客户端预测 + 服务器校验                   │   │
│  │                                                     │   │
│  │  Client                    Server                   │   │
│  │  ┌────────┐               ┌────────┐               │   │
│  │  │输入    │ ───────────→  │模拟    │               │   │
│  │  │本地模拟│               │校验    │               │   │
│  │  │立即反馈│ ←───────────  │纠正    │               │   │
│  │  └────────┘               └────────┘               │   │
│  │  优点：低延迟感、安全                                  │   │
│  │  缺点：实现复杂                                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 网络延迟与抖动

```csharp
using UnityEngine;

/// <summary>
/// 网络延迟模拟与分析
/// </summary>
public class NetworkLatencySimulator : MonoBehaviour
{
    /*
    ========== 网络延迟概念 ==========

    RTT (Round Trip Time): 往返时延
    - 客户端发送 → 服务器接收 → 服务器处理 → 客户端接收

    Ping: 网络可达性测试
    - 通常等于 RTT

    Jitter (抖动): 延迟变化
    - 连续Ping之间的差异
    - 影响游戏平滑度

    Packet Loss (丢包): 数据包丢失率
    - 影响游戏可靠性

    ========== 典型延迟范围 ==========

    本地网络:     < 1ms
    同城:         5-20ms
    同国:         20-50ms
    跨国:         50-150ms
    跨洲:         150-300ms

    ========== 游戏类型延迟要求 ==========

    格斗/音游:    < 16ms (1帧)
    FPS:          < 50ms
    MOBA:         < 100ms
    回合制/MMO:   < 200ms
    */

    [Header("Simulation Settings")]
    [SerializeField] private bool simulateLag = true;
    [SerializeField] private int minLatencyMs = 50;
    [SerializeField] private int maxLatencyMs = 150;
    [SerializeField] private float jitterPercent = 0.2f;
    [SerializeField] private float packetLossPercent = 0.01f;

    /// <summary>
    /// 模拟网络延迟
    /// </summary>
    public float GetSimulatedLatency()
    {
        if (!simulateLag) return 0;

        float baseLatency = Random.Range(minLatencyMs, maxLatencyMs);
        float jitter = baseLatency * jitterPercent * (Random.value * 2 - 1);
        return baseLatency + jitter;
    }

    /// <summary>
    /// 模拟丢包
    /// </summary>
    public bool ShouldDropPacket()
    {
        return Random.value < packetLossPercent;
    }
}
```

---

## 2. Unity网络解决方案

### 2.1 方案对比

```csharp
/// <summary>
/// Unity网络方案对比
/// </summary>
public class NetworkSolutionsComparison
{
    /*
    ========== 主流方案对比 ==========

    ┌─────────────────┬────────────────────────────────────┐
    │    方案         │              特点                   │
    ├─────────────────┼────────────────────────────────────┤
    │ Netcode for     │ Unity官方、免费、GameObject导向    │
    │ GameObjects     │ 适合：中小型游戏                    │
    ├─────────────────┼────────────────────────────────────┤
    │ Mirror          │ 开源、免费、社区活跃               │
    │                 │ 适合：各类多人游戏                  │
    ├─────────────────┼────────────────────────────────────┤
    │ Photon          │ 商业、云端托管、快速接入           │
    │ (PUN2/Fusion)   │ 适合：快速开发、不需要自建服务器    │
    ├─────────────────┼────────────────────────────────────┤
    │ NGO (Netcode    │ Unity官方、ECS导向                │
    │ for Entities)   │ 适合：高性能、大量网络对象         │
    ├─────────────────┼────────────────────────────────────┤
    │ LiteNetLib      │ 轻量、高性能、UDP                 │
    │                 │ 适合：需要底层控制的场景           │
    └─────────────────┴────────────────────────────────────┘

    ========== 选择建议 ==========

    入门学习:     Mirror (文档丰富、社区活跃)
    官方推荐:     Netcode for GameObjects
    快速上线:     Photon (无需服务器运维)
    高性能需求:   Netcode for Entities
    商业项目:     根据预算和需求选择
    */
}
```

### 2.2 Netcode for GameObjects 基础

```csharp
using Unity.Netcode;
using UnityEngine;

/// <summary>
/// NGO (Netcode for GameObjects) 基础示例
/// </summary>
public class BasicNetworkSetup : MonoBehaviour
{
    /*
    ========== NGO 核心组件 ==========

    NetworkManager
    ├── 管理网络连接
    ├── 启动服务器/客户端
    └── 管理网络对象

    NetworkObject
    ├── 标识网络对象
    ├── 管理对象生命周期
    └── 处理所有权

    NetworkBehaviour
    ├── 网络脚本的基类
    ├── 提供RPC
    └── 提供网络变量
    */

    private void Start()
    {
        // 启动网络管理器
        NetworkManager.Singleton.OnClientConnectedCallback += OnClientConnected;
        NetworkManager.Singleton.OnClientDisconnectCallback += OnClientDisconnected;
    }

    public void StartHost()
    {
        NetworkManager.Singleton.StartHost();
        Debug.Log("Started as Host");
    }

    public void StartServer()
    {
        NetworkManager.Singleton.StartServer();
        Debug.Log("Started as Server");
    }

    public void StartClient()
    {
        NetworkManager.Singleton.StartClient();
        Debug.Log("Started as Client");
    }

    private void OnClientConnected(ulong clientId)
    {
        Debug.Log($"Client {clientId} connected");
    }

    private void OnClientDisconnected(ulong clientId)
    {
        Debug.Log($"Client {clientId} disconnected");
    }
}

/// <summary>
/// 网络玩家控制器
/// </summary>
public class NetworkPlayerController : NetworkBehaviour
{
    [Header("Movement")]
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private CharacterController controller;

    // 网络变量 - 自动同步
    private NetworkVariable<Vector3> position = new NetworkVariable<Vector3>();
    private NetworkVariable<Quaternion> rotation = new NetworkVariable<Quaternion>();
    private NetworkVariable<int> health = new NetworkVariable<int>(100);

    public override void OnNetworkSpawn()
    {
        if (IsOwner)
        {
            // 本地玩家初始化
            Debug.Log($"I am the owner of {NetworkObjectId}");
        }
        else
        {
            // 远程玩家初始化
            Debug.Log($"This is a remote player {NetworkObjectId}");
        }
    }

    private void Update()
    {
        // 只有拥有者可以控制
        if (!IsOwner) return;

        // 本地输入处理
        float h = Input.GetAxis("Horizontal");
        float v = Input.GetAxis("Vertical");

        Vector3 move = new Vector3(h, 0, v) * moveSpeed * Time.deltaTime;
        controller.Move(move);

        // 更新网络变量（自动同步到其他客户端）
        if (IsServer)
        {
            position.Value = transform.position;
            rotation.Value = transform.rotation;
        }
        else
        {
            // 客户端请求服务器更新
            UpdatePositionServerRpc(transform.position, transform.rotation);
        }
    }

    // 服务器RPC - 客户端调用，服务器执行
    [ServerRpc]
    private void UpdatePositionServerRpc(Vector3 newPosition, Quaternion newRotation)
    {
        position.Value = newPosition;
        rotation.Value = newRotation;
    }

    // 客户端RPC - 服务器调用，所有客户端执行
    [ClientRpc]
    private void TakeDamageClientRpc(int damage, ClientRpcParams rpcParams = default)
    {
        health.Value -= damage;
        Debug.Log($"Took {damage} damage, health: {health.Value}");
    }

    public void ApplyDamage(int damage)
    {
        if (IsServer)
        {
            health.Value -= damage;
            TakeDamageClientRpc(damage);
        }
        else
        {
            ApplyDamageServerRpc(damage);
        }
    }

    [ServerRpc]
    private void ApplyDamageServerRpc(int damage)
    {
        health.Value -= damage;
        TakeDamageClientRpc(damage);
    }
}
```

### 2.3 Mirror 基础示例

```csharp
using Mirror;
using UnityEngine;

/// <summary>
/// Mirror 网络管理器
/// </summary>
public class CustomNetworkManager : NetworkManager
{
    public override void OnStartServer()
    {
        base.OnStartServer();
        Debug.Log("Server started");
    }

    public override void OnStopServer()
    {
        base.OnStopServer();
        Debug.Log("Server stopped");
    }

    public override void OnClientConnect()
    {
        base.OnClientConnect();
        Debug.Log("Connected to server");
    }

    public override void OnClientDisconnect()
    {
        base.OnClientDisconnect();
        Debug.Log("Disconnected from server");
    }

    public override void OnServerAddPlayer(NetworkConnectionToClient conn)
    {
        // 生成玩家对象
        GameObject player = Instantiate(playerPrefab);
        NetworkServer.AddPlayerForConnection(conn, player);
    }
}

/// <summary>
/// Mirror 玩家控制器
/// </summary>
public class MirrorPlayerController : NetworkBehaviour
{
    [Header("Movement")]
    [SerializeField] private float moveSpeed = 5f;

    // 同步变量
    [SyncVar] private int health = 100;
    [SyncVar] private Vector3 syncPosition;
    [SyncVar] private Quaternion syncRotation;

    private void Update()
    {
        if (!isLocalPlayer) return;

        // 本地输入
        float h = Input.GetAxis("Horizontal");
        float v = Input.GetAxis("Vertical");

        Vector3 move = new Vector3(h, 0, v) * moveSpeed * Time.deltaTime;
        transform.Translate(move);

        // 发送命令到服务器
        CmdUpdatePosition(transform.position, transform.rotation);
    }

    // Command - 客户端调用，服务器执行
    [Command]
    private void CmdUpdatePosition(Vector3 position, Quaternion rotation)
    {
        syncPosition = position;
        syncRotation = rotation;
    }

    // ClientRpc - 服务器调用，客户端执行
    [ClientRpc]
    private void RpcTakeDamage(int damage)
    {
        Debug.Log($"Took {damage} damage");
    }

    public void ApplyDamage(int damage)
    {
        if (isServer)
        {
            health -= damage;
            RpcTakeDamage(damage);
        }
    }

    // TargetRpc - 服务器调用，特定客户端执行
    [TargetRpc]
    private void TargetShowDamageEffect(NetworkConnection target)
    {
        // 只在目标客户端显示特效
        Debug.Log("Showing damage effect");
    }
}
```

---

## 3. 状态同步

### 3.1 状态同步原理

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 状态同步系统
/// </summary>
public class StateSynchronization : MonoBehaviour
{
    /*
    ========== 状态同步 vs 帧同步 ==========

    状态同步：
    - 同步游戏对象的状态（位置、旋转、属性）
    - 服务器计算状态，客户端接收
    - 客户端可以预测
    - 带宽消耗较大

    帧同步（Lockstep）：
    - 同步玩家输入
    - 所有客户端独立计算
    - 需要确定性计算
    - 带宽消耗小

    ========== 状态同步频率 ==========

    典型设置：10-20次/秒
    - 10 Hz: 每100ms同步一次
    - 20 Hz: 每50ms同步一次

    平衡点：
    - 更高频率 = 更平滑，但带宽更大
    - 更低频率 = 节省带宽，但可能卡顿
    */

    [Header("Sync Settings")]
    [SerializeField] private float syncInterval = 0.05f; // 20 Hz
    [SerializeField] private bool useInterpolation = true;
    [SerializeField] private float interpolationDelay = 0.1f; // 100ms延迟

    private float lastSyncTime;

    /// <summary>
    /// 网络状态快照
    /// </summary>
    public struct StateSnapshot
    {
        public float timestamp;
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 velocity;
    }

    private Queue<StateSnapshot> snapshotBuffer = new Queue<StateSnapshot>();

    /// <summary>
    /// 添加状态快照
    /// </summary>
    public void AddSnapshot(StateSnapshot snapshot)
    {
        snapshotBuffer.Enqueue(snapshot);

        // 限制缓冲区大小
        while (snapshotBuffer.Count > 20)
        {
            snapshotBuffer.Dequeue();
        }
    }

    /// <summary>
    /// 插值获取当前状态
    /// </summary>
    public StateSnapshot GetInterpolatedState()
    {
        float renderTime = Time.time - interpolationDelay;

        // 找到两个快照进行插值
        StateSnapshot[] snapshots = snapshotBuffer.ToArray();

        for (int i = 0; i < snapshots.Length - 1; i++)
        {
            if (snapshots[i].timestamp <= renderTime && snapshots[i + 1].timestamp >= renderTime)
            {
                float t = (renderTime - snapshots[i].timestamp) /
                         (snapshots[i + 1].timestamp - snapshots[i].timestamp);

                return Interpolate(snapshots[i], snapshots[i + 1], t);
            }
        }

        // 没有足够的快照，返回最新的
        return snapshots.Length > 0 ? snapshots[snapshots.Length - 1] : default;
    }

    private StateSnapshot Interpolate(StateSnapshot from, StateSnapshot to, float t)
    {
        return new StateSnapshot
        {
            timestamp = Mathf.Lerp(from.timestamp, to.timestamp, t),
            position = Vector3.Lerp(from.position, to.position, t),
            rotation = Quaternion.Slerp(from.rotation, to.rotation, t),
            velocity = Vector3.Lerp(from.velocity, to.velocity, t)
        };
    }
}
```

### 3.2 客户端预测与服务器调和

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 客户端预测 + 服务器调和
/// </summary>
public class ClientPrediction : MonoBehaviour
{
    [Header("Settings")]
    [SerializeField] private float reconciliationThreshold = 0.5f;
    [SerializeField] private int maxPendingMoves = 30;

    /// <summary>
    /// 玩家输入
    /// </summary>
    public struct PlayerInput
    {
        public uint sequence;
        public float timestamp;
        public Vector2 moveDirection;
        public bool jump;
    }

    /// <summary>
    /// 移动预测结果
    /// </summary>
    public struct PredictedMove
    {
        public PlayerInput input;
        public Vector3 predictedPosition;
        public Quaternion predictedRotation;
    }

    /// <summary>
    /// 服务器状态
    /// </summary>
    public struct ServerState
    {
        public uint lastProcessedSequence;
        public Vector3 position;
        public Quaternion rotation;
    }

    private Queue<PredictedMove> pendingMoves = new Queue<PredictedMove>();
    private uint currentSequence;
    private Vector3 serverPosition;

    /// <summary>
    /// 处理本地输入
    /// </summary>
    public void ProcessInput(Vector2 moveDirection, bool jump)
    {
        // 创建输入
        var input = new PlayerInput
        {
            sequence = currentSequence++,
            timestamp = Time.time,
            moveDirection = moveDirection,
            jump = jump
        };

        // 本地预测
        var predictedMove = PredictMove(input);
        pendingMoves.Enqueue(predictedMove);

        // 应用预测
        transform.position = predictedMove.predictedPosition;
        transform.rotation = predictedMove.predictedRotation;

        // 发送到服务器
        SendInputToServer(input);

        // 限制队列大小
        while (pendingMoves.Count > maxPendingMoves)
        {
            pendingMoves.Dequeue();
        }
    }

    private PredictedMove PredictMove(PlayerInput input)
    {
        Vector3 move = new Vector3(input.moveDirection.x, 0, input.moveDirection.y);

        // 简单的移动预测
        Vector3 newPosition = transform.position + move * Time.deltaTime * 5f;
        Quaternion newRotation = transform.rotation;

        if (move != Vector3.zero)
        {
            newRotation = Quaternion.LookRotation(move);
        }

        return new PredictedMove
        {
            input = input,
            predictedPosition = newPosition,
            predictedRotation = newRotation
        };
    }

    /// <summary>
    /// 接收服务器状态
    /// </summary>
    public void OnServerStateReceived(ServerState state)
    {
        serverPosition = state.position;

        // 移除已处理的预测
        while (pendingMoves.Count > 0)
        {
            var move = pendingMoves.Peek();
            if (move.input.sequence <= state.lastProcessedSequence)
            {
                pendingMoves.Dequeue();
            }
            else
            {
                break;
            }
        }

        // 检查是否需要调和
        float error = Vector3.Distance(state.position, transform.position);

        if (error > reconciliationThreshold)
        {
            // 需要调和 - 使用服务器位置
            Reconcile(state);
        }
    }

    /// <summary>
    /// 调和客户端状态
    /// </summary>
    private void Reconcile(ServerState state)
    {
        // 使用服务器状态
        transform.position = state.position;
        transform.rotation = state.rotation;

        // 重新应用未处理的预测
        foreach (var move in pendingMoves)
        {
            transform.position = move.predictedPosition;
            transform.rotation = move.predictedRotation;
        }
    }

    private void SendInputToServer(PlayerInput input)
    {
        // 实际实现中通过网络发送
        // NetworkManager.Send(input);
    }

    /// <summary>
    /// 可视化调试
    /// </summary>
    private void OnDrawGizmos()
    {
        // 客户端预测位置
        Gizmos.color = Color.green;
        Gizmos.DrawWireSphere(transform.position, 0.3f);

        // 服务器确认位置
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(serverPosition, 0.35f);

        // 预测路径
        Gizmos.color = Color.yellow;
        var prevPos = transform.position;
        foreach (var move in pendingMoves)
        {
            Gizmos.DrawLine(prevPos, move.predictedPosition);
            prevPos = move.predictedPosition;
        }
    }
}
```

---

## 4. 延迟补偿

### 4.1 Lag Compensation 系统

```csharp
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 延迟补偿系统（用于服务器端）
/// </summary>
public class LagCompensation : MonoBehaviour
{
    /// <summary>
    /// 玩家状态历史记录
    /// </summary>
    public struct PlayerStateRecord
    {
        public float timestamp;
        public Vector3 position;
        public Quaternion rotation;
        public Bounds bounds;
    }

    private Dictionary<int, List<PlayerStateRecord>> playerHistory = new Dictionary<int, List<PlayerStateRecord>>();
    private float recordInterval = 0.02f; // 50fps
    private float historyDuration = 1f;   // 保留1秒历史

    /// <summary>
    /// 记录玩家状态
    /// </summary>
    public void RecordPlayerState(int playerId, Vector3 position, Quaternion rotation, Bounds bounds)
    {
        if (!playerHistory.ContainsKey(playerId))
        {
            playerHistory[playerId] = new List<PlayerStateRecord>();
        }

        var history = playerHistory[playerId];

        // 添加新记录
        history.Add(new PlayerStateRecord
        {
            timestamp = Time.time,
            position = position,
            rotation = rotation,
            bounds = bounds
        });

        // 清理过期记录
        float cutoffTime = Time.time - historyDuration;
        history.RemoveAll(r => r.timestamp < cutoffTime);
    }

    /// <summary>
    /// 回退时间进行检测
    /// </summary>
    public PlayerStateRecord? GetPlayerStateAtTime(int playerId, float targetTime)
    {
        if (!playerHistory.TryGetValue(playerId, out var history))
            return null;

        if (history.Count < 2)
            return null;

        // 找到目标时间点的两个记录
        for (int i = 0; i < history.Count - 1; i++)
        {
            if (history[i].timestamp <= targetTime && history[i + 1].timestamp >= targetTime)
            {
                // 插值
                float t = (targetTime - history[i].timestamp) /
                         (history[i + 1].timestamp - history[i].timestamp);

                return new PlayerStateRecord
                {
                    timestamp = targetTime,
                    position = Vector3.Lerp(history[i].position, history[i + 1].position, t),
                    rotation = Quaternion.Slerp(history[i].rotation, history[i + 1].rotation, t),
                    bounds = InterpolateBounds(history[i].bounds, history[i + 1].bounds, t)
                };
            }
        }

        return null;
    }

    private Bounds InterpolateBounds(Bounds a, Bounds b, float t)
    {
        return new Bounds
        {
            center = Vector3.Lerp(a.center, b.center, t),
            size = Vector3.Lerp(a.size, b.size, t)
        };
    }

    /// <summary>
    /// 处理射击请求（带延迟补偿）
    /// </summary>
    public bool ProcessShotRequest(int shooterId, Vector3 origin, Vector3 direction, float shooterLatency)
    {
        // 计算射击时刻（当前时间 - 玩家延迟）
        float shotTime = Time.time - shooterLatency;

        // 回退所有玩家到射击时刻
        Dictionary<int, PlayerStateRecord> rewoundStates = new Dictionary<int, PlayerStateRecord>();

        foreach (var kvp in playerHistory)
        {
            int playerId = kvp.Key;
            if (playerId == shooterId) continue; // 跳过射击者

            var state = GetPlayerStateAtTime(playerId, shotTime);
            if (state.HasValue)
            {
                rewoundStates[playerId] = state.Value;
            }
        }

        // 在回退的时间点进行射线检测
        foreach (var kvp in rewoundStates)
        {
            var state = kvp.Value;

            Ray ray = new Ray(origin, direction);
            if (state.bounds.IntersectRay(ray))
            {
                // 命中！
                Debug.Log($"Player {kvp.Key} hit (lag compensated)");
                return true;
            }
        }

        return false;
    }
}
```

### 4.2 插值与外推

```csharp
using UnityEngine;

/// <summary>
/// 网络插值器
/// </summary>
public class NetworkInterpolator : MonoBehaviour
{
    [Header("Settings")]
    [SerializeField] private float interpolationDelay = 0.1f;
    [SerializeField] private bool useExtrapolation = true;
    [SerializeField] private float maxExtrapolationTime = 0.5f;

    // 接收到的网络状态
    private struct NetworkState
    {
        public float timestamp;
        public Vector3 position;
        public Quaternion rotation;
        public Vector3 velocity;
    }

    private NetworkState? previousState;
    private NetworkState? currentState;

    /// <summary>
    /// 接收网络更新
    /// </summary>
    public void OnNetworkUpdate(Vector3 position, Quaternion rotation, Vector3 velocity)
    {
        previousState = currentState;
        currentState = new NetworkState
        {
            timestamp = Time.time,
            position = position,
            rotation = rotation,
            velocity = velocity
        };
    }

    private void Update()
    {
        if (!currentState.HasValue) return;

        float renderTime = Time.time - interpolationDelay;

        if (previousState.HasValue && previousState.Value.timestamp <= renderTime && currentState.Value.timestamp >= renderTime)
        {
            // 插值
            Interpolate(renderTime);
        }
        else if (useExtrapolation && currentState.Value.timestamp < renderTime)
        {
            // 外推
            Extrapolate(renderTime);
        }
    }

    private void Interpolate(float renderTime)
    {
        float t = (renderTime - previousState.Value.timestamp) /
                 (currentState.Value.timestamp - previousState.Value.timestamp);

        transform.position = Vector3.Lerp(previousState.Value.position, currentState.Value.position, t);
        transform.rotation = Quaternion.Slerp(previousState.Value.rotation, currentState.Value.rotation, t);
    }

    private void Extrapolate(float renderTime)
    {
        float extrapolationTime = renderTime - currentState.Value.timestamp;

        if (extrapolationTime > maxExtrapolationTime)
        {
            // 外推时间太长，停止
            return;
        }

        // 使用速度外推位置
        Vector3 extrapolatedPosition = currentState.Value.position + currentState.Value.velocity * extrapolationTime;
        transform.position = extrapolatedPosition;
    }

    /// <summary>
    /// 可视化调试
    /// </summary>
    private void OnDrawGizmos()
    {
        if (currentState.HasValue)
        {
            // 当前插值位置
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(transform.position, 0.3f);

            // 最新网络位置
            Gizmos.color = Color.red;
            Gizmos.DrawWireSphere(currentState.Value.position, 0.35f);
        }
    }
}
```

---

## 5. RPC设计模式

### 5.1 RPC最佳实践

```csharp
using Unity.Netcode;
using UnityEngine;

/// <summary>
/// RPC 设计模式与最佳实践
/// </summary>
public class RPCBestPractices : NetworkBehaviour
{
    /*
    ========== RPC 类型 ==========

    [ServerRpc]
    - 客户端调用，服务器执行
    - 需要 IsServer 检查
    - 参数会被序列化传输

    [ClientRpc]
    - 服务器调用，所有客户端执行
    - 可以指定接收者

    [TargetRpc] (Mirror)
    - 服务器调用，特定客户端执行

    ========== RPC 命名规范 ==========

    ServerRpc:   XxxServerRpc
    ClientRpc:   XxxClientRpc
    TargetRpc:   TargetXxx

    ========== 最佳实践 ==========

    1. 减少 RPC 调用频率
    2. 合并多个参数到一个 RPC
    3. 使用 NetworkVariable 替代频繁 RPC
    4. 避免 RPC 中传递大对象
    5. 使用可靠性参数
    */

    #region ServerRPC Examples

    // 基础 ServerRpc
    [ServerRpc]
    private void RequestSpawnServerRpc(int prefabId, Vector3 position)
    {
        // 只在服务器执行
        if (!IsServer) return;

        SpawnObject(prefabId, position);
    }

    // 带客户端参数的 ServerRpc
    [ServerRpc]
    private void SendMessageServerRpc(string message, ServerRpcParams rpcParams = default)
    {
        ulong senderId = rpcParams.Receive.SenderClientId;
        Debug.Log($"Player {senderId} says: {message}");

        // 广播给所有客户端
        ReceiveMessageClientRpc(senderId, message);
    }

    // 带可靠性设置的 ServerRpc
    [ServerRpc(Delivery = RpcDelivery.Reliable)]
    private void ImportantActionServerRpc(int actionId)
    {
        // 必须可靠送达
    }

    [ServerRpc(Delivery = RpcDelivery.Unreliable)]
    private void FrequentUpdateServerRpc(Vector3 position)
    {
        // 高频更新，可以丢包
    }

    #endregion

    #region ClientRPC Examples

    // 基础 ClientRpc
    [ClientRpc]
    private void ReceiveMessageClientRpc(ulong senderId, string message)
    {
        Debug.Log($"Received from {senderId}: {message}");
    }

    // 指定接收者的 ClientRpc
    [ClientRpc]
    private void NotifyClientRpc(ClientRpcParams rpcParams = default)
    {
        // 只通知特定客户端
    }

    // 带可靠性设置的 ClientRpc
    [ClientRpc(Delivery = RpcDelivery.Reliable)]
    private void GameStateChangeClientRpc(int newState)
    {
        // 游戏状态改变必须可靠
    }

    #endregion

    #region Optimized Patterns

    // 使用 NetworkVariable 替代频繁 RPC
    private NetworkVariable<int> score = new NetworkVariable<int>();

    // 错误：每帧发送 RPC
    private void UpdateBad()
    {
        if (!IsOwner) return;
        UpdatePositionServerRpc(transform.position); // 太频繁！
    }

    // 正确：使用 NetworkVariable
    private NetworkVariable<Vector3> networkPosition = new NetworkVariable<Vector3>();

    private void UpdateGood()
    {
        if (!IsOwner) return;

        if (IsServer)
        {
            networkPosition.Value = transform.position;
        }
        else
        {
            UpdatePositionServerRpc(transform.position);
        }
    }

    // 合并多个参数
    [ServerRpc]
    private void UpdatePlayerStateServerRpc(PlayerStateData state)
    {
        // 一次发送多个数据
    }

    [System.Serializable]
    private struct PlayerStateData : INetworkSerializable
    {
        public Vector3 position;
        public Quaternion rotation;
        public int health;
        public int ammo;

        public void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter
        {
            serializer.SerializeValue(ref position);
            serializer.SerializeValue(ref rotation);
            serializer.SerializeValue(ref health);
            serializer.SerializeValue(ref ammo);
        }
    }

    #endregion

    private void SpawnObject(int prefabId, Vector3 position)
    {
        // 生成对象逻辑
    }
}
```

### 5.2 事件系统

```csharp
using Unity.Netcode;
using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 网络事件系统
/// </summary>
public class NetworkEventSystem : NetworkBehaviour
{
    // 使用 ClientRpc 广播事件
    public delegate void NetworkEventHandler(ulong clientId, params object[] args);

    private Dictionary<string, NetworkEventHandler> eventHandlers = new Dictionary<string, NetworkEventHandler>();

    /// <summary>
    /// 注册事件
    /// </summary>
    public void RegisterEvent(string eventName, NetworkEventHandler handler)
    {
        if (!eventHandlers.ContainsKey(eventName))
        {
            eventHandlers[eventName] = handler;
        }
        else
        {
            eventHandlers[eventName] += handler;
        }
    }

    /// <summary>
    /// 触发事件（服务器）
    /// </summary>
    public void TriggerEvent(string eventName, params object[] args)
    {
        if (IsServer)
        {
            BroadcastEventClientRpc(eventName, SerializeArgs(args));
        }
        else
        {
            TriggerEventServerRpc(eventName, SerializeArgs(args));
        }
    }

    [ServerRpc]
    private void TriggerEventServerRpc(string eventName, byte[] serializedArgs, ServerRpcParams rpcParams = default)
    {
        BroadcastEventClientRpc(eventName, serializedArgs);
    }

    [ClientRpc]
    private void BroadcastEventClientRpc(string eventName, byte[] serializedArgs, ClientRpcParams rpcParams = default)
    {
        ulong senderId = rpcParams.Receive.SenderClientId;
        object[] args = DeserializeArgs(serializedArgs);

        if (eventHandlers.TryGetValue(eventName, out var handler))
        {
            handler?.Invoke(senderId, args);
        }
    }

    private byte[] SerializeArgs(object[] args)
    {
        // 简化实现，实际需要使用 Protocol Buffers 或其他序列化
        return System.Array.Empty<byte>();
    }

    private object[] DeserializeArgs(byte[] data)
    {
        return new object[0];
    }
}

/// <summary>
/// 使用示例
/// </summary>
public class NetworkEventExample : NetworkBehaviour
{
    private NetworkEventSystem eventSystem;

    private void Start()
    {
        eventSystem = GetComponent<NetworkEventSystem>();

        // 注册事件
        eventSystem.RegisterEvent("OnPlayerDeath", HandlePlayerDeath);
        eventSystem.RegisterEvent("OnItemCollected", HandleItemCollected);
    }

    private void HandlePlayerDeath(ulong clientId, params object[] args)
    {
        int score = (int)args[0];
        Debug.Log($"Player {clientId} died with score {score}");
    }

    private void HandleItemCollected(ulong clientId, params object[] args)
    {
        int itemId = (int)args[0];
        Debug.Log($"Player {clientId} collected item {itemId}");
    }

    public void OnPlayerDeath(int finalScore)
    {
        eventSystem.TriggerEvent("OnPlayerDeath", finalScore);
    }
}
```

---

## 6. 房间与匹配

```csharp
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 房间管理系统
/// </summary>
public class RoomManager : MonoBehaviour
{
    /// <summary>
    /// 房间数据
    /// </summary>
    public class Room
    {
        public string roomId;
        public string roomName;
        public int maxPlayers;
        public int currentPlayerCount;
        public string hostId;
        public RoomState state;
        public List<PlayerInfo> players = new List<PlayerInfo>();
    }

    public struct PlayerInfo
    {
        public string playerId;
        public string playerName;
        public bool isReady;
        public int teamId;
    }

    public enum RoomState
    {
        Waiting,    // 等待玩家
        Ready,      // 准备开始
        Playing,    // 游戏中
        Finished    // 游戏结束
    }

    private Dictionary<string, Room> rooms = new Dictionary<string, Room>();
    private Dictionary<string, string> playerToRoom = new Dictionary<string, string>();

    public event System.Action<Room> OnRoomCreated;
    public event System.Action<Room> OnRoomUpdated;
    public event System.Action<Room> OnRoomDestroyed;

    /// <summary>
    /// 创建房间
    /// </summary>
    public Room CreateRoom(string hostId, string roomName, int maxPlayers)
    {
        string roomId = GenerateRoomId();

        var room = new Room
        {
            roomId = roomId,
            roomName = roomName,
            maxPlayers = maxPlayers,
            hostId = hostId,
            state = RoomState.Waiting
        };

        rooms[roomId] = room;
        OnRoomCreated?.Invoke(room);

        // 房主自动加入
        JoinRoom(roomId, hostId, "Player1");

        return room;
    }

    /// <summary>
    /// 加入房间
    /// </summary>
    public bool JoinRoom(string roomId, string playerId, string playerName)
    {
        if (!rooms.TryGetValue(roomId, out var room))
            return false;

        if (room.currentPlayerCount >= room.maxPlayers)
            return false;

        if (room.state != RoomState.Waiting)
            return false;

        var playerInfo = new PlayerInfo
        {
            playerId = playerId,
            playerName = playerName,
            isReady = false,
            teamId = room.currentPlayerCount
        };

        room.players.Add(playerInfo);
        room.currentPlayerCount++;
        playerToRoom[playerId] = roomId;

        OnRoomUpdated?.Invoke(room);
        return true;
    }

    /// <summary>
    /// 离开房间
    /// </summary>
    public void LeaveRoom(string playerId)
    {
        if (!playerToRoom.TryGetValue(playerId, out var roomId))
            return;

        if (!rooms.TryGetValue(roomId, out var room))
            return;

        room.players.RemoveAll(p => p.playerId == playerId);
        room.currentPlayerCount--;
        playerToRoom.Remove(playerId);

        if (room.currentPlayerCount == 0)
        {
            // 房间为空，销毁
            rooms.Remove(roomId);
            OnRoomDestroyed?.Invoke(room);
        }
        else
        {
            // 转移房主
            if (room.hostId == playerId && room.players.Count > 0)
            {
                room.hostId = room.players[0].playerId;
            }

            OnRoomUpdated?.Invoke(room);
        }
    }

    /// <summary>
    /// 设置准备状态
    /// </summary>
    public void SetReady(string playerId, bool isReady)
    {
        if (!playerToRoom.TryGetValue(playerId, out var roomId))
            return;

        if (!rooms.TryGetValue(roomId, out var room))
            return;

        int index = room.players.FindIndex(p => p.playerId == playerId);
        if (index >= 0)
        {
            var player = room.players[index];
            player.isReady = isReady;
            room.players[index] = player;

            // 检查是否所有人准备好了
            CheckAllReady(room);

            OnRoomUpdated?.Invoke(room);
        }
    }

    private void CheckAllReady(Room room)
    {
        if (room.currentPlayerCount < 2) return;

        bool allReady = room.players.TrueForAll(p => p.isReady);

        if (allReady)
        {
            room.state = RoomState.Ready;
            // 通知可以开始游戏
        }
    }

    /// <summary>
    /// 获取房间列表
    /// </summary>
    public List<Room> GetRoomList()
    {
        var result = new List<Room>();
        foreach (var room in rooms.Values)
        {
            if (room.state == RoomState.Waiting)
            {
                result.Add(room);
            }
        }
        return result;
    }

    private string GenerateRoomId()
    {
        return System.Guid.NewGuid().ToString().Substring(0, 8);
    }
}
```

---

## 7. 网络优化清单

```
┌─────────────────────────────────────────────────────────────┐
│                   网络优化最佳实践                            │
│                                                             │
│  1. 带宽优化                                                │
│     ├── 使用压缩格式（VarInt、ZigZag）                       │
│     ├── 减少同步频率                                        │
│     ├── 只同步必要数据                                      │
│     └── 使用位掩码压缩标志位                                │
│                                                             │
│  2. 延迟优化                                                │
│     ├── 客户端预测                                          │
│     ├── 服务器调和                                          │
│     ├── 延迟补偿（射击检测）                                 │
│     └── 插值/外推                                           │
│                                                             │
│  3. 可靠性优化                                              │
│     ├── 关键数据用可靠通道                                  │
│     ├── 位置更新用不可靠通道                                │
│     ├── 重要事件确认机制                                    │
│     └── 丢包重传策略                                        │
│                                                             │
│  4. 安全性                                                  │
│     ├── 服务器权威                                          │
│     ├── 输入验证                                            │
│     ├── 反作弊检测                                          │
│     └── 加密敏感数据                                        │
│                                                             │
│  5. 断线处理                                                │
│     ├── 断线重连                                            │
│     ├── 心跳检测                                            │
│     ├── 超时处理                                            │
│     └── 状态恢复                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| 网络模型 | 服务器权威、P2P、客户端预测 |
| 网络方案 | NGO、Mirror、Photon选择 |
| 状态同步 | 插值、外推、快照缓冲 |
| 客户端预测 | 本地模拟、服务器调和 |
| 延迟补偿 | 回退时间、历史记录 |
| RPC模式 | ServerRpc、ClientRpc、TargetRpc |
| 房间系统 | 创建、加入、匹配 |

### 网络同步流程

```
客户端                     服务器
  │                          │
  │──── 输入 ─────────────→  │
  │     (ServerRpc)          │
  │                          │── 处理输入
  │                          │── 更新状态
  │←──── 状态更新 ──────────│
  │     (ClientRpc/          │
  │      NetworkVariable)    │
  │                          │
  │── 本地预测               │
  │── 插值显示               │
  │── 服务器调和             │
```

---

## 延伸阅读

- [Netcode for GameObjects](https://docs-multiplayer.unity3d.com/netcode-for-gameobjects/)
- [Mirror Documentation](https://mirror-networking.gitbook.io/)
- [Photon Documentation](https://doc.photonengine.com/)
- [Gabriel Gambetta - Fast-Paced Multiplayer](https://www.gabrielgambetta.com/client-server-game-architecture.html)
- [Valve - Source Engine Networking](https://developer.valvesoftware.com/wiki/Source_Multiplayer_Networking)
