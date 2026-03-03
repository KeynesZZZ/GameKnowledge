# 休闲游戏云存档系统

> 跨平台云存档完整实现，支持iOS/Android/微信/抖音小游戏 `#云存档` `#跨平台` `#完整项目`

## 项目概述

### 支持平台

| 平台 | 云服务 | 状态 |
|------|--------|------|
| iOS/Android | Firebase / PlayFab | ✅ |
| 微信小游戏 | 微信云开发 | ✅ |
| 抖音小游戏 | 抖音云开发 | ✅ |
| 华为快游戏 | 华为AGC | ✅ |
| WebGL通用 | REST API | ✅ |
| PC单机 | 本地存储 | ✅ |

### 核心功能

```
┌─────────────────────────────────────────────────────────────┐
│                    云存档系统功能                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  基础功能：                                                 │
│  ├─ 多存档槽（3个槽位）                                    │
│  ├─ 自动存档                                               │
│  ├─ 手动存档/读档                                          │
│  └─ 存档删除                                               │
│                                                             │
│  云同步：                                                   │
│  ├─ 自动同步（网络恢复后）                                 │
│  ├─ 手动同步                                               │
│  ├─ 离线支持（本地缓存）                                   │
│  └─ 冲突解决                                               │
│                                                             │
│  数据安全：                                                 │
│  ├─ AES加密                                                │
│  ├─ 数据校验                                               │
│  └─ 版本控制                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    系统架构                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              ┌─────────────────────────┐                   │
│              │   CloudSaveManager      │                   │
│              │   (统一入口)            │                   │
│              └───────────┬─────────────┘                   │
│                          │                                  │
│          ┌───────────────┼───────────────┐                 │
│          │               │               │                 │
│          ▼               ▼               ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Platform    │ │ Cloud       │ │ Local       │          │
│  │ Detector    │ │ Provider    │ │ Cache       │          │
│  │ (平台检测)  │ │ (云服务)    │ │ (本地缓存)  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 文档目录

| 编号 | 文档 | 内容 |
|------|------|------|
| 01 | [需求分析与架构](./01-需求分析与架构.md) | 需求、技术选型、整体架构 |
| 02 | [核心数据结构](./02-核心数据结构.md) | SaveData、SlotData、同步状态 |
| 03 | [平台检测系统](./03-平台检测系统.md) | WebGL平台检测、JS交互 |
| 04 | [Provider接口设计](./04-Provider接口设计.md) | ICloudProvider、工厂模式 |
| 05 | [海外平台实现](./05-海外平台实现.md) | Firebase/PlayFab集成 |
| 06 | [微信小游戏实现](./06-微信小游戏实现.md) | 微信云开发、云函数 |
| 07 | [抖音小游戏实现](./07-抖音小游戏实现.md) | 抖音云开发、云函数 |
| 08 | [本地缓存与离线](./08-本地缓存与离线.md) | 跨平台本地存储、离线队列 |
| 09 | [冲突解决策略](./09-冲突解决策略.md) | 版本比较、时间戳、合并 |
| 10 | [统一管理器实现](./10-统一管理器实现.md) | CloudSaveManager完整实现 |
| 11 | [UI组件与集成](./11-UI组件与集成.md) | 存档槽UI、冲突对话框 |

> **注意**: 所有异步操作使用 **UniTask** 而非 Task，确保与Unity良好集成。

---

## 快速开始

### 1. 初始化

```csharp
// 游戏启动时初始化
CloudSaveManager.Initialize(new CloudSaveConfig
{
    maxSlots = 3,
    autoSaveInterval = 300f,  // 5分钟
    enableEncryption = true,
    encryptionKey = "your-secret-key"
});
```

### 2. 保存游戏

```csharp
using Cysharp.Threading.Tasks;

// 创建存档数据
var saveData = new GameSaveData
{
    level = currentPlayerLevel,
    coins = currentCoins,
    inventory = inventoryItems,
    playTime = totalPlayTime
};

// 保存到槽位0
var result = await CloudSaveManager.SaveAsync(0, saveData);

if (result.success)
{
    Debug.Log("保存成功");
}
```

### 3. 加载游戏

```csharp
using Cysharp.Threading.Tasks;

var result = await CloudSaveManager.LoadAsync(0);

if (result.success)
{
    var saveData = result.data;
    ApplySaveData(saveData);
}
```

### 4. 监听事件

```csharp
CloudSaveManager.OnSyncComplete += (result) =>
{
    Debug.Log($"同步完成: {result.status}");
};

CloudSaveManager.OnConflictDetected += (localData, cloudData) =>
{
    // 显示冲突解决UI
    ShowConflictDialog(localData, cloudData);
};
```

---

## 代码结构

```
Scripts/
└── CloudSave/
    ├── Core/
    │   ├── CloudSaveManager.cs      ← 统一管理器
    │   ├── CloudSaveConfig.cs       ← 配置
    │   └── CloudSaveData.cs         ← 数据结构
    │
    ├── Platform/
    │   ├── PlatformDetector.cs      ← 平台检测
    │   └── PlatformType.cs          ← 平台枚举
    │
    ├── Providers/
    │   ├── ICloudProvider.cs        ← 接口定义
    │   ├── FirebaseProvider.cs      ← Firebase实现
    │   ├── WeChatProvider.cs        ← 微信实现
    │   ├── DouyinProvider.cs        ← 抖音实现
    │   └── LocalProvider.cs         ← 纯本地实现
    │
    ├── Cache/
    │   ├── LocalCache.cs            ← 本地缓存
    │   └── OfflineQueue.cs          ← 离线队列
    │
    └── UI/
        ├── SaveSlotUI.cs            ← 存档槽UI
        └── ConflictDialog.cs        ← 冲突对话框
```

---

## 性能指标

| 指标 | 目标值 |
|------|--------|
| 本地存档延迟 | < 50ms |
| 云端存档延迟 | < 2s |
| 存档数据大小 | < 100KB |
| 离线队列容量 | 100条操作 |
| 自动存档间隔 | 可配置（默认5分钟） |

---

## 相关链接

- [10_架构设计/系统架构-存档系统](../../10_架构设计/系统架构-存档系统.md)
- [10_架构设计/设计原理-为什么要用设计模式](../../10_架构设计/设计原理-为什么要用设计模式.md)
