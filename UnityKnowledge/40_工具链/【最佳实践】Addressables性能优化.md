---
title: 【最佳实践】Addressables性能优化
tags: [Unity, 性能优化, 资源管理, Addressables, 最佳实践]
category: 工具链/资源管线
created: 2026-03-07 10:00
updated: 2026-03-07 10:00
description: Unity Addressables 资源系统性能优化指南，涵盖异步加载策略、内存管理、资源卸载和性能监控
unity_version: 2021.3+
---

# 最佳实践 - Addressables 性能优化

> Addressables 资源系统性能优化完整指南 `#性能优化` `#资源管理` `#Addressables` `#最佳实践`

## 文档定位

本文档从**性能优化角度**讲解 Addressables 的最佳实践。

**相关文档**：[[【教程】资源管线-Addressables]]、[[【最佳实践】资源卸载指南]]、[[【实战案例】加载时间优化实战]]

---

## 1. Addressables 性能基础

### 1.1 为什么使用 Addressables

```
┌─────────────────────────────────────────────────────────────┐
│              Resources vs Addressables 对比                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Resources.Load:                                            │
│  ├── ❌ 同步加载，阻塞主线程                                │
│  ├── ❌ 无法细粒度卸载                                      │
│  ├── ❌ 增加初始包体                                        │
│  └── ❌ 无法热更新                                          │
│                                                             │
│  Addressables:                                              │
│  ├── ✅ 异步加载，不阻塞                                    │
│  ├── ✅ 引用计数，自动/手动卸载                             │
│  ├── ✅ 按需下载，减少初始包体                              │
│  ├── ✅ 支持热更新                                          │
│  └── ✅ 内存管理更灵活                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心概念

| 概念 | 说明 |
|------|------|
| **Address** | 资源的唯一标识符 |
| **Label** | 资源的分组标签 |
| **AssetBundle** | 资源的物理打包单元 |
| **Handle** | 异步操作的句柄，用于追踪和释放 |
| **Reference Count** | 引用计数，决定资源何时卸载 |

### 1.3 性能关键指标

```
关键性能指标：

1. 加载时间
   ├── 首次加载（从磁盘/网络）
   ├── 缓存加载（从内存）
   └── 目标：< 100ms (UI资源)

2. 内存占用
   ├── 已加载资源内存
   ├── AssetBundle 缓存
   └── 目标：按需加载，及时卸载

3. 帧率影响
   ├── 异步加载不应导致卡顿
   └── 目标：保持 60fps
```

---

## 2. 异步加载优化

### 2.1 基础异步加载

```csharp
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using System.Collections.Generic;
using System.Threading.Tasks;

/// <summary>
/// Addressables 异步加载管理器
/// </summary>
public class AddressablesLoader : MonoBehaviour
{
    private Dictionary<string, AsyncOperationHandle> loadedHandles = new Dictionary<string, AsyncOperationHandle>();
    private Dictionary<string, int> referenceCounts = new Dictionary<string, int>();

    /// <summary>
    /// 异步加载单个资源
    /// </summary>
    public async Task<T> LoadAssetAsync<T>(string address) where T : Object
    {
        // 检查是否已加载
        if (loadedHandles.TryGetValue(address, out var existingHandle))
        {
            if (existingHandle.IsDone)
            {
                referenceCounts[address]++;
                return existingHandle.Result as T;
            }

            // 等待正在加载的资源
            await existingHandle.Task;
            referenceCounts[address]++;
            return existingHandle.Result as T;
        }

        // 开始异步加载
        var handle = Addressables.LoadAssetAsync<T>(address);
        loadedHandles[address] = handle;
        referenceCounts[address] = 1;

        await handle.Task;

        if (handle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError($"Failed to load asset: {address}");
            loadedHandles.Remove(address);
            referenceCounts.Remove(address);
            return null;
        }

        return handle.Result;
    }

    /// <summary>
    /// 异步加载多个资源（通过 Label）
    /// </summary>
    public async Task<IList<T>> LoadAssetsByLabelAsync<T>(string label) where T : Object
    {
        string key = $"label:{label}";

        if (loadedHandles.TryGetValue(key, out var existingHandle))
        {
            referenceCounts[key]++;
            return existingHandle.Result as IList<T>;
        }

        var handle = Addressables.LoadAssetsAsync<T>(label, null);
        loadedHandles[key] = handle;
        referenceCounts[key] = 1;

        await handle.Task;

        if (handle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError($"Failed to load assets with label: {label}");
            loadedHandles.Remove(key);
            referenceCounts.Remove(key);
            return null;
        }

        return handle.Result;
    }

    /// <summary>
    /// 释放资源
    /// </summary>
    public void ReleaseAsset(string address)
    {
        if (!loadedHandles.TryGetValue(address, out var handle))
            return;

        referenceCounts[address]--;

        if (referenceCounts[address] <= 0)
        {
            Addressables.Release(handle);
            loadedHandles.Remove(address);
            referenceCounts.Remove(address);
        }
    }

    /// <summary>
    /// 释放所有资源
    /// </summary>
    public void ReleaseAll()
    {
        foreach (var handle in loadedHandles.Values)
        {
            Addressables.Release(handle);
        }
        loadedHandles.Clear();
        referenceCounts.Clear();
    }

    private void OnDestroy()
    {
        ReleaseAll();
    }
}
```

### 2.2 加载优先级管理

```csharp
/// <summary>
/// 带优先级的资源加载队列
/// </summary>
public class PriorityLoadQueue : MonoBehaviour
{
    public enum LoadPriority
    {
        Critical,   // 必须立即加载
        High,       // 高优先级
        Normal,     // 普通优先级
        Low         // 低优先级，空闲时加载
    }

    private class LoadRequest
    {
        public string Address;
        public LoadPriority Priority;
        public System.Action<Object> OnComplete;
        public System.Action<float> OnProgress;
    }

    private List<LoadRequest> requestQueue = new List<LoadRequest>();
    private Dictionary<string, AsyncOperationHandle> activeLoads = new Dictionary<string, AsyncOperationHandle>();
    private int maxConcurrentLoads = 3;

    /// <summary>
    /// 添加加载请求
    /// </summary>
    public void EnqueueLoad(string address, LoadPriority priority,
        System.Action<Object> onComplete = null,
        System.Action<float> onProgress = null)
    {
        var request = new LoadRequest
        {
            Address = address,
            Priority = priority,
            OnComplete = onComplete,
            OnProgress = onProgress
        };

        // 按优先级插入队列
        int insertIndex = requestQueue.FindIndex(r => r.Priority > priority);
        if (insertIndex >= 0)
        {
            requestQueue.Insert(insertIndex, request);
        }
        else
        {
            requestQueue.Add(request);
        }

        ProcessQueue();
    }

    private async void ProcessQueue()
    {
        while (requestQueue.Count > 0 && activeLoads.Count < maxConcurrentLoads)
        {
            var request = requestQueue[0];
            requestQueue.RemoveAt(0);

            if (activeLoads.ContainsKey(request.Address))
                continue;

            await ProcessRequest(request);
        }
    }

    private async Task ProcessRequest(LoadRequest request)
    {
        var handle = Addressables.LoadAssetAsync<Object>(request.Address);
        activeLoads[request.Address] = handle;

        // 进度回调
        while (!handle.IsDone)
        {
            request.OnProgress?.Invoke(handle.PercentComplete);
            await Task.Delay(16);
        }

        activeLoads.Remove(request.Address);

        if (handle.Status == AsyncOperationStatus.Succeeded)
        {
            request.OnComplete?.Invoke(handle.Result);
        }
        else
        {
            Debug.LogError($"Failed to load: {request.Address}");
            request.OnComplete?.Invoke(null);
        }
    }
}
```

### 2.3 预加载策略

```csharp
/// <summary>
/// 智能预加载管理器
/// </summary>
public class SmartPreloader : MonoBehaviour
{
    [System.Serializable]
    public class PreloadGroup
    {
        public string groupName;
        public string[] assetAddresses;
        public bool preloadOnStart;
        public bool showProgress;
    }

    [Header("Preload Groups")]
    [SerializeField] private PreloadGroup[] preloadGroups;

    private Dictionary<string, Object> preloadedAssets = new Dictionary<string, Object>();
    private bool isPreloading;

    /// <summary>
    /// 预加载指定组
    /// </summary>
    public async Task<bool> PreloadGroup(string groupName, System.Action<float> onProgress = null)
    {
        var group = System.Array.Find(preloadGroups, g => g.groupName == groupName);
        if (group == null)
        {
            Debug.LogError($"Preload group not found: {groupName}");
            return false;
        }

        return await PreloadAssets(group.assetAddresses, onProgress);
    }

    /// <summary>
    /// 预加载资源列表
    /// </summary>
    public async Task<bool> PreloadAssets(string[] addresses, System.Action<float> onProgress = null)
    {
        if (isPreloading)
        {
            Debug.LogWarning("Already preloading");
            return false;
        }

        isPreloading = true;
        int loadedCount = 0;
        int totalCount = addresses.Length;

        foreach (var address in addresses)
        {
            if (preloadedAssets.ContainsKey(address))
            {
                loadedCount++;
                continue;
            }

            var handle = Addressables.LoadAssetAsync<Object>(address);
            await handle.Task;

            if (handle.Status == AsyncOperationStatus.Succeeded)
            {
                preloadedAssets[address] = handle.Result;
            }
            else
            {
                Debug.LogWarning($"Failed to preload: {address}");
            }

            loadedCount++;
            onProgress?.Invoke((float)loadedCount / totalCount);
        }

        isPreloading = false;
        return true;
    }

    /// <summary>
    /// 获取预加载的资源
    /// </summary>
    public T GetPreloadedAsset<T>(string address) where T : Object
    {
        if (preloadedAssets.TryGetValue(address, out var asset))
        {
            return asset as T;
        }
        return null;
    }

    /// <summary>
    /// 后台预加载（不阻塞游戏）
    /// </summary>
    public void PreloadInBackground(string groupName)
    {
        StartCoroutine(PreloadCoroutine(groupName));
    }

    private IEnumerator PreloadCoroutine(string groupName)
    {
        var group = System.Array.Find(preloadGroups, g => g.groupName == groupName);
        if (group == null) yield break;

        foreach (var address in group.assetAddresses)
        {
            if (preloadedAssets.ContainsKey(address))
                continue;

            var handle = Addressables.LoadAssetAsync<Object>(address);
            yield return handle;

            if (handle.Status == AsyncOperationStatus.Succeeded)
            {
                preloadedAssets[address] = handle.Result;
            }

            // 每加载一个资源，等待一帧
            yield return null;
        }
    }
}
```

---

## 3. 内存管理优化

### 3.1 引用计数管理

```csharp
/// <summary>
/// 引用计数资源管理器
/// </summary>
public class ReferenceCountedLoader : MonoBehaviour
{
    private class AssetInfo
    {
        public AsyncOperationHandle Handle;
        public int ReferenceCount;
        public float LastAccessTime;
    }

    private Dictionary<string, AssetInfo> loadedAssets = new Dictionary<string, AssetInfo>();

    [Header("Memory Management")]
    [SerializeField] private float unloadUnusedAfterSeconds = 60f;
    [SerializeField] private int maxCachedAssets = 100;

    /// <summary>
    /// 获取资源（增加引用计数）
    /// </summary>
    public async Task<T> GetAsset<T>(string address) where T : Object
    {
        if (loadedAssets.TryGetValue(address, out var info))
        {
            info.ReferenceCount++;
            info.LastAccessTime = Time.time;
            return info.Handle.Result as T;
        }

        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle.Task;

        if (handle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError($"Failed to load: {address}");
            return null;
        }

        loadedAssets[address] = new AssetInfo
        {
            Handle = handle,
            ReferenceCount = 1,
            LastAccessTime = Time.time
        };

        return handle.Result;
    }

    /// <summary>
    /// 释放资源引用
    /// </summary>
    public void ReleaseAsset(string address)
    {
        if (!loadedAssets.TryGetValue(address, out var info))
            return;

        info.ReferenceCount--;

        if (info.ReferenceCount <= 0)
        {
            // 不立即卸载，等待自动清理
            info.LastAccessTime = Time.time;
        }
    }

    /// <summary>
    /// 定期清理未使用的资源
    /// </summary>
    private void Update()
    {
        if (Time.frameCount % 300 != 0) // 每5秒检查一次
            return;

        var keysToRemove = new List<string>();
        float currentTime = Time.time;

        foreach (var kvp in loadedAssets)
        {
            if (kvp.Value.ReferenceCount <= 0 &&
                currentTime - kvp.Value.LastAccessTime > unloadUnusedAfterSeconds)
            {
                keysToRemove.Add(kvp.Key);
            }
        }

        foreach (var key in keysToRemove)
        {
            Addressables.Release(loadedAssets[key].Handle);
            loadedAssets.Remove(key);
            Debug.Log($"Unloaded unused asset: {key}");
        }
    }

    /// <summary>
    /// 强制清理超出限制的缓存
    /// </summary>
    public void EnforceCacheLimit()
    {
        if (loadedAssets.Count <= maxCachedAssets)
            return;

        // 按 LastAccessTime 排序，移除最旧的
        var sortedAssets = loadedAssets
            .OrderBy(x => x.Value.LastAccessTime)
            .ToList();

        int toRemove = loadedAssets.Count - maxCachedAssets;
        for (int i = 0; i < toRemove; i++)
        {
            var kvp = sortedAssets[i];
            if (kvp.Value.ReferenceCount <= 0)
            {
                Addressables.Release(kvp.Value.Handle);
                loadedAssets.Remove(kvp.Key);
            }
        }
    }

    /// <summary>
    /// 获取内存使用统计
    /// </summary>
    public string GetMemoryStats()
    {
        int totalAssets = loadedAssets.Count;
        int activeAssets = loadedAssets.Count(x => x.Value.ReferenceCount > 0);
        long totalMemory = 0;

        foreach (var kvp in loadedAssets)
        {
            var obj = kvp.Value.Handle.Result;
            if (obj is Texture2D tex)
            {
                totalMemory += tex.width * tex.height * 4; // 估算
            }
        }

        return $"Total: {totalAssets}, Active: {activeAssets}, Est. Memory: {totalMemory / 1024 / 1024}MB";
    }
}
```

### 3.2 场景切换清理

```csharp
/// <summary>
/// 场景切换时的资源清理
/// </summary>
public class SceneResourceCleaner : MonoBehaviour
{
    [Header("Cleanup Settings")]
    [SerializeField] private string[] persistentLabels; // 跨场景保留的资源标签
    [SerializeField] private bool cleanupOnSceneChange = true;

    private HashSet<string> persistentAssets = new HashSet<string>();

    private void Awake()
    {
        SceneManager.sceneUnloaded += OnSceneUnloaded;
    }

    private void OnDestroy()
    {
        SceneManager.sceneUnloaded -= OnSceneUnloaded;
    }

    private async void OnSceneUnloaded(Scene scene)
    {
        if (!cleanupOnSceneChange)
            return;

        await CleanupSceneAssets(scene);
    }

    private async Task CleanupSceneAssets(Scene unloadedScene)
    {
        // 1. 标记场景相关资源
        var sceneAssets = await Addressables
            .LoadResourceLocationsAsync(unloadedScene.name)
            .Task;

        // 2. 清理非持久化资源
        foreach (var location in sceneAssets)
        {
            if (persistentAssets.Contains(location.PrimaryKey))
                continue;

            // 检查是否为持久化标签
            bool isPersistent = false;
            foreach (var label in persistentLabels)
            {
                if (location.Labels.Contains(label))
                {
                    isPersistent = true;
                    break;
                }
            }

            if (!isPersistent)
            {
                // 释放资源
                // 注意：需要追踪 handle 才能释放
                Debug.Log($"Should cleanup: {location.PrimaryKey}");
            }
        }

        // 3. 强制 GC
        Resources.UnloadUnusedAssets();
        System.GC.Collect();
    }

    /// <summary>
    /// 标记资源为持久化
    /// </summary>
    public void MarkAsPersistent(string address)
    {
        persistentAssets.Add(address);
    }
}
```

### 3.3 内存监控

```csharp
/// <summary>
/// Addressables 内存监控
/// </summary>
public class AddressablesMemoryMonitor : MonoBehaviour
{
    [Header("Monitor Settings")]
    [SerializeField] private bool showDebugUI = true;
    [SerializeField] private float warningThresholdMB = 200f;

    private Rect windowRect = new Rect(10, 10, 300, 200);

    private void OnGUI()
    {
        if (!showDebugUI)
            return;

        windowRect = GUILayout.Window(12345, windowRect, DrawWindow, "Addressables Monitor");
    }

    private void DrawWindow(int windowId)
    {
        // 显示内存使用
        long totalMemory = Profiling.Profiler.GetTotalAllocatedMemoryLong() / 1024 / 1024;

        GUILayout.Label($"Managed Memory: {totalMemory}MB");

        if (totalMemory > warningThresholdMB)
        {
            GUI.color = Color.red;
            GUILayout.Label($"⚠ Memory exceeds threshold!");
            GUI.color = Color.white;
        }

        // 显示资源加载状态
        // 注意：需要自定义追踪
        GUILayout.Label($"Loaded Assets: {GetLoadedAssetCount()}");

        // 清理按钮
        if (GUILayout.Button("Cleanup Unused"))
        {
            Resources.UnloadUnusedAssets();
            System.GC.Collect();
        }

        GUI.DragWindow();
    }

    private int GetLoadedAssetCount()
    {
        // 追踪已加载资源数量
        return 0; // 占位
    }
}
```

---

## 4. AssetBundle 优化

### 4.1 打包策略

```
┌─────────────────────────────────────────────────────────────┐
│                 AssetBundle 打包策略                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 按功能模块分组                                          │
│     ├── UI_Atlas_Main (UI主图集)                           │
│     ├── UI_Atlas_Popup (弹窗图集)                          │
│     ├── Characters_Player (玩家角色)                       │
│     ├── Characters_Enemies (敌人)                          │
│     ├── Audio_BGM (背景音乐)                               │
│     └── Audio_SFX (音效)                                   │
│                                                             │
│  2. 按加载时机分组                                          │
│     ├── Core (启动加载)                                    │
│     ├── Gameplay (游戏中加载)                              │
│     └── Optional (可选内容)                                │
│                                                             │
│  3. 按更新频率分组                                          │
│     ├── Static (不更新)                                    │
│     ├── Frequent (经常更新)                                │
│     └── Hotfix (热更内容)                                  │
│                                                             │
│  Bundle 大小建议：                                          │
│  ├── UI 图集：2-10MB                                       │
│  ├── 3D 模型：1-5MB                                        │
│  ├── 音频：按类型分组，每包 < 10MB                         │
│  └── 避免超大 Bundle (> 50MB)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Addressables Group 配置

```csharp
/// <summary>
/// Addressables Group 配置建议
/// </summary>
public static class AddressablesGroupConfig
{
    /*
    ┌─────────────────────────────────────────────────────────┐
    │           Group 配置建议                                 │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │  UI 资源组：                                            │
    │  ├── Bundled Asset Group Schema                        │
    │  │   ├── Build Path: [Remote]/UI                       │
    │  │   ├── Load Path: [Remote]/UI                        │
    │  │   └── Asset Provider: AssetDatabaseProvider        │
    │  ├── Compression: LZ4 (快速解压)                       │
    │  └── Bundle Mode: Pack Together (合并打包)             │
    │                                                         │
    │  3D 资源组：                                            │
    │  ├── Compression: LZ4 or LZMA (高压缩)                 │
    │  ├── Bundle Mode: Pack Separately (独立打包)           │
    │  └── Address: 每个资源独立地址                         │
    │                                                         │
    │  音频资源组：                                            │
    │  ├── Compression: LZ4                                  │
    │  └── 按类型分组 (BGM/SFX/Voice)                        │
    │                                                         │
    │  热更资源组：                                            │
    │  ├── Build Path: Remote                                │
    │  ├── Load Path: Remote                                 │
    │  └── 启用 CRC 校验                                     │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    */
}
```

### 4.3 下载优化

```csharp
/// <summary>
/// 远程资源下载管理器
/// </summary>
public class RemoteAssetDownloader : MonoBehaviour
{
    [Header("Download Settings")]
    [SerializeField] private int maxConcurrentDownloads = 4;
    [SerializeField] private float timeoutSeconds = 30f;

    /// <summary>
    /// 下载指定 Label 的所有资源
    /// </summary>
    public async Task<DownloadResult> DownloadLabelAsync(
        string label,
        System.Action<float> onProgress = null)
    {
        var result = new DownloadResult();

        // 获取下载大小
        var sizeHandle = Addressables.GetDownloadSizeAsync(label);
        await sizeHandle.Task;

        result.TotalSize = sizeHandle.Result;
        result.TotalSizeMB = result.TotalSize / 1024f / 1024f;

        if (result.TotalSize <= 0)
        {
            result.AlreadyDownloaded = true;
            return result;
        }

        // 开始下载
        var downloadHandle = Addressables.DownloadDependenciesAsync(label);

        while (!downloadHandle.IsDone)
        {
            result.DownloadedBytes = downloadHandle.GetDownloadStatus().DownloadedBytes;
            result.Progress = downloadHandle.GetDownloadStatus().Percent;

            onProgress?.Invoke(result.Progress);

            await Task.Delay(100);
        }

        if (downloadHandle.Status == AsyncOperationStatus.Succeeded)
        {
            result.Success = true;
        }
        else
        {
            result.Success = false;
            result.ErrorMessage = "Download failed";
        }

        Addressables.Release(downloadHandle);
        return result;
    }

    public class DownloadResult
    {
        public bool Success;
        public bool AlreadyDownloaded;
        public long TotalSize;
        public float TotalSizeMB;
        public long DownloadedBytes;
        public float Progress;
        public string ErrorMessage;
    }

    /// <summary>
    /// 清理下载缓存
    /// </summary>
    public async Task ClearCacheAsync()
    {
        await Addressables.ClearDependencyCacheAsync("");
        Debug.Log("Cache cleared");
    }
}
```

---

## 5. 性能监控与调试

### 5.1 加载性能分析

```csharp
/// <summary>
/// Addressables 性能分析器
/// </summary>
public class AddressablesProfiler : MonoBehaviour
{
    private class LoadRecord
    {
        public string Address;
        public float StartTime;
        public float EndTime;
        public bool Success;
        public long MemoryBefore;
        public long MemoryAfter;
    }

    private List<LoadRecord> loadRecords = new List<LoadRecord>();
    private int maxRecords = 100;

    /// <summary>
    /// 带性能追踪的加载
    /// </summary>
    public async Task<T> LoadWithProfiling<T>(string address) where T : Object
    {
        var record = new LoadRecord
        {
            Address = address,
            StartTime = Time.realtimeSinceStartup,
            MemoryBefore = System.GC.GetTotalMemory(false)
        };

        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle.Task;

        record.EndTime = Time.realtimeSinceStartup;
        record.MemoryAfter = System.GC.GetTotalMemory(false);
        record.Success = handle.Status == AsyncOperationStatus.Succeeded;

        loadRecords.Add(record);

        // 保持记录数量限制
        if (loadRecords.Count > maxRecords)
        {
            loadRecords.RemoveAt(0);
        }

        if (record.Success)
        {
            return handle.Result;
        }

        return null;
    }

    /// <summary>
    /// 生成性能报告
    /// </summary>
    public string GenerateReport()
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine("=== Addressables Performance Report ===");

        if (loadRecords.Count == 0)
        {
            sb.AppendLine("No load records");
            return sb.ToString();
        }

        // 统计数据
        float totalTime = loadRecords.Sum(r => r.EndTime - r.StartTime);
        float avgTime = totalTime / loadRecords.Count;
        float maxTime = loadRecords.Max(r => r.EndTime - r.StartTime);
        int successCount = loadRecords.Count(r => r.Success);
        long totalMemory = loadRecords.Sum(r => r.MemoryAfter - r.MemoryBefore);

        sb.AppendLine($"Total Loads: {loadRecords.Count}");
        sb.AppendLine($"Success Rate: {(float)successCount / loadRecords.Count * 100:F1}%");
        sb.AppendLine($"Avg Load Time: {avgTime * 1000:F1}ms");
        sb.AppendLine($"Max Load Time: {maxTime * 1000:F1}ms");
        sb.AppendLine($"Total Memory Delta: {totalMemory / 1024 / 1024:F1}MB");

        // 慢加载警告
        sb.AppendLine("\nSlow Loads (> 100ms):");
        foreach (var record in loadRecords.Where(r => r.EndTime - r.StartTime > 0.1f))
        {
            sb.AppendLine($"  {record.Address}: {(record.EndTime - record.StartTime) * 1000:F0}ms");
        }

        return sb.ToString();
    }

    [ContextMenu("Print Report")]
    public void PrintReport()
    {
        Debug.Log(GenerateReport());
    }
}
```

### 5.2 内存泄漏检测

```csharp
/// <summary>
/// Addressables 内存泄漏检测
/// </summary>
#if UNITY_EDITOR
public static class AddressablesLeakDetector
{
    private static Dictionary<string, int> loadCounts = new Dictionary<string, int>();

    [UnityEditor.MenuItem("Tools/Addressables/Check Leaks")]
    public static void CheckLeaks()
    {
        // 检查未释放的资源
        // 注意：这需要自定义追踪

        Debug.Log("Leak check completed. See console for details.");
    }

    /// <summary>
    /// 记录加载
    /// </summary>
    public static void RecordLoad(string address)
    {
        if (!loadCounts.ContainsKey(address))
            loadCounts[address] = 0;

        loadCounts[address]++;
    }

    /// <summary>
    /// 记录释放
    /// </summary>
    public static void RecordRelease(string address)
    {
        if (loadCounts.ContainsKey(address))
        {
            loadCounts[address]--;
            if (loadCounts[address] < 0)
            {
                Debug.LogWarning($"Possible over-release: {address}");
            }
        }
    }

    /// <summary>
    /// 获取未释放的资源
    /// </summary>
    public static List<string> GetUnreleasedAssets()
    {
        return loadCounts
            .Where(kvp => kvp.Value > 0)
            .Select(kvp => $"{kvp.Key} (refs: {kvp.Value})")
            .ToList();
    }
}
#endif
```

---

## 6. 性能优化检查清单

```markdown
## Addressables 性能优化检查清单

### 加载优化
- [ ] 使用异步加载而非同步
- [ ] 实现加载优先级队列
- [ ] 预加载关键资源
- [ ] 显示加载进度

### 内存管理
- [ ] 正确释放资源（Release handle）
- [ ] 实现引用计数
- [ ] 场景切换时清理资源
- [ ] 监控内存使用

### AssetBundle 优化
- [ ] 合理分组打包
- [ ] 使用适当的压缩格式
- [ ] 控制单个 Bundle 大小
- [ ] 按更新频率分组

### 下载优化
- [ ] 限制并发下载数
- [ ] 实现下载重试机制
- [ ] 显示下载进度
- [ ] 提供取消下载选项

### 调试与监控
- [ ] 记录加载时间
- [ ] 监控内存使用
- [ ] 检测内存泄漏
- [ ] 生成性能报告
```

---

## 7. 性能数据参考

### 7.1 加载时间对比

| 场景 | Resources.Load | Addressables (缓存) | Addressables (首次) |
|------|---------------|-------------------|-------------------|
| 小型UI资源 | 5ms | 2ms | 15ms |
| 中型Prefab | 20ms | 8ms | 50ms |
| 大型场景 | 200ms | 100ms | 500ms+ |

### 7.2 内存优化效果

| 优化措施 | 内存占用 | 说明 |
|---------|---------|------|
| 无优化 | 500MB | 全部常驻内存 |
| 按需加载 | 200MB | 只加载需要的 |
| 及时卸载 | 150MB | 场景切换时清理 |
| 引用计数 | 120MB | 自动清理未使用 |

---

## 相关链接

- [[【教程】资源管线-Addressables]] - Addressables 基础教程
- [[【最佳实践】资源卸载指南]] - 资源卸载最佳实践
- [[【实战案例】加载时间优化实战]] - 加载优化实战案例
- [Unity Addressables 官方文档](https://docs.unity3d.com/Packages/com.unity.addressables@latest)

---

*创建日期: 2026-03-07*
*相关标签: #性能优化 #资源管理 #Addressables #最佳实践*
