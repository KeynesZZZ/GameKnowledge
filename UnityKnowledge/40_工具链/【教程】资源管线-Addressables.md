---
title: 【教程】资源管线-Addressables
tags: [Unity, 工具链, Addressables, 教程]
category: 工具链
created: 2026-03-05 08:42
updated: 2026-03-05 08:42
description: Unity Addressables资源系统教程
unity_version: 2021.3+
---
# 资源管线 - Addressables

> Unity官方资源管理系统完整指南 `#资源管理` `#热更新` `#工具链`

## 快速参考

```csharp
// 加载资源
var handle = Addressables.LoadAssetAsync<GameObject>("Prefab");
await handle.Task;

// 实例化
var instance = await Addressables.InstantiateAsync("Prefab").Task;

// 释放
Addressables.Release(handle);
Addressables.ReleaseInstance(instance);
```

---

## 基础配置

### 标记资源

```
1. 选中资源
2. Inspector中勾选 "Addressable"
3. 设置 Address (路径/名称)

快捷键: Alt+A (切换Addressable状态)
```

### Addressable Settings

```
Window > Asset Management > Addressables > Settings

关键设置：
├── Build Path: 构建输出路径
├── Load Path: 运行时加载路径
├── Build Addressables on Player Build: 构建时自动打包
└── Unique Bundle IDs: 避免Bundle冲突
```

### Group配置

```
Window > Asset Management > Addressables > Groups

Group设置：
├── Bundle Mode:
│   ├── Pack Separately: 每个资源单独打包
│   ├── Pack Together: 打包到一起
│   └── Pack Together By Label: 按标签打包
├── Compression:
│   ├── None: 不压缩（加载最快）
│   ├── LZ4: 快速压缩（推荐）
│   └── LZMA: 高压缩（加载慢）
└── Update Restriction: 更新限制
```

---

## 加载方式

### 异步加载

```csharp
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using System.Threading;

public class AddressablesLoader : MonoBehaviour
{
    // 基础加载
    public async UniTask<T> LoadAssetAsync<T>(string address, CancellationToken ct = default) where T : Object
    {
        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle.ToUniTask(cancellationToken: ct);

        if (handle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError($"Failed to load: {address}");
            return null;
        }

        return handle.Result;
    }

    // 带进度
    public async UniTask<T> LoadWithProgress<T>(string address, IProgress<float> progress) where T : Object
    {
        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle.ToUniTask(progress);
        return handle.Result;
    }

    // 多资源加载
    public async UniTask<IList<T>> LoadAssetsAsync<T>(IList<string> addresses) where T : Object
    {
        var handle = Addressables.LoadAssetsAsync<T>(addresses, null);
        await handle.ToUniTask();
        return handle.Result;
    }

    // 按标签加载
    public async UniTask<IList<T>> LoadByLabelAsync<T>(string label) where T : Object
    {
        var handle = Addressables.LoadAssetsAsync<T>(label, null);
        await handle.ToUniTask();
        return handle.Result;
    }
}
```

### 实例化

```csharp
public class AddressablesSpawner : MonoBehaviour
{
    // 实例化到场景
    public async UniTask<GameObject> InstantiateAsync(
        string address,
        Vector3 position = default,
        Quaternion rotation = default,
        Transform parent = null)
    {
        var handle = Addressables.InstantiateAsync(address, position, rotation, parent);
        await handle.ToUniTask();

        if (handle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError($"Failed to instantiate: {address}");
            return null;
        }

        return handle.Result;
    }

    // 使用对象池
    private Dictionary<string, Stack<GameObject>> pools = new();

    public async UniTask<GameObject> GetFromPool(string address)
    {
        if (pools.TryGetValue(address, out var pool) && pool.Count > 0)
        {
            var go = pool.Pop();
            go.SetActive(true);
            return go;
        }

        return await InstantiateAsync(address);
    }

    public void ReturnToPool(string address, GameObject go)
    {
        go.SetActive(false);
        go.transform.SetParent(transform);

        if (!pools.ContainsKey(address))
        {
            pools[address] = new Stack<GameObject>();
        }
        pools[address].Push(go);
    }
}
```

---

## 内存管理

### Handle管理

```csharp
public class AddressablesManager : MonoBehaviour
{
    private Dictionary<string, AsyncOperationHandle> handles = new();

    // 加载并缓存Handle
    public async UniTask<T> LoadAndCacheAsync<T>(string address) where T : Object
    {
        if (handles.TryGetValue(address, out var cachedHandle))
        {
            return cachedHandle.Result as T;
        }

        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle.ToUniTask();

        if (handle.Status == AsyncOperationStatus.Succeeded)
        {
            handles[address] = handle;
            return handle.Result;
        }

        return null;
    }

    // 释放指定资源
    public void Release(string address)
    {
        if (handles.TryGetValue(address, out var handle))
        {
            Addressables.Release(handle);
            handles.Remove(address);
        }
    }

    // 释放所有
    public void ReleaseAll()
    {
        foreach (var handle in handles.Values)
        {
            Addressables.Release(handle);
        }
        handles.Clear();
    }

    private void OnDestroy()
    {
        ReleaseAll();
    }
}
```

### 实例生命周期

```csharp
public class AddressablesInstance : MonoBehaviour
{
    private static Dictionary<GameObject, string> instanceAddresses = new();

    public static async UniTask<GameObject> Spawn(string address, Vector3 position)
    {
        var instance = await Addressables.InstantiateAsync(address, position, Quaternion.identity);

        if (instance.Status == AsyncOperationStatus.Succeeded)
        {
            instanceAddresses[instance.Result] = address;
            return instance.Result;
        }

        return null;
    }

    public static void Despawn(GameObject instance)
    {
        if (instanceAddresses.TryGetValue(instance, out var address))
        {
            Addressables.ReleaseInstance(instance);
            instanceAddresses.Remove(instance);
        }
        else
        {
            Destroy(instance);
        }
    }
}
```

### 内存清理

```csharp
public class AddressablesCleanup
{
    // 清理未使用的资源
    public static void CleanupUnusedAssets()
    {
        Resources.UnloadUnusedAssets();
        Addressables.CleanBundleCache();
    }

    // 清理指定资源
    public static void CleanupAsset(string address)
    {
        var handle = Addressables.LoadAssetAsync<Object>(address);
        Addressables.Release(handle);
    }

    // 检查内存使用
    public static long GetTotalMemoryUsage()
    {
        long total = 0;
        // 使用Profiler获取更多信息
        return total;
    }
}
```

---

## 热更新

### 检查更新

```csharp
public class AddressablesUpdater : MonoBehaviour
{
    public async UniTask<bool> CheckForUpdates()
    {
        var checkHandle = Addressables.CheckForCatalogUpdates();
        await checkHandle.ToUniTask();

        if (checkHandle.Status == AsyncOperationStatus.Failed)
        {
            Debug.LogError("Failed to check for updates");
            return false;
        }

        var catalogs = checkHandle.Result;
        Addressables.Release(checkHandle);

        return catalogs != null && catalogs.Count > 0;
    }

    public async UniTask UpdateCatalogs()
    {
        var checkHandle = Addressables.CheckForCatalogUpdates();
        await checkHandle.ToUniTask();

        if (checkHandle.Status != AsyncOperationStatus.Succeeded)
        {
            Addressables.Release(checkHandle);
            return;
        }

        var catalogs = checkHandle.Result;
        Addressables.Release(checkHandle);

        if (catalogs == null || catalogs.Count == 0)
        {
            Debug.Log("No updates available");
            return;
        }

        var updateHandle = Addressables.UpdateCatalogs(catalogs);
        await updateHandle.ToUniTask();

        Debug.Log($"Updated {catalogs.Count} catalogs");
        Addressables.Release(updateHandle);
    }

    // 完整更新流程
    public async UniTask<bool> FullUpdate()
    {
        // 1. 检查更新
        bool hasUpdates = await CheckForUpdates();
        if (!hasUpdates)
        {
            Debug.Log("Already up to date");
            return true;
        }

        // 2. 下载更新
        await UpdateCatalogs();

        // 3. 清理旧资源
        Addressables.CleanBundleCache();

        return true;
    }
}
```

### 下载进度

```csharp
public class DownloadProgress : MonoBehaviour
{
    [SerializeField] private Slider progressBar;
    [SerializeField] private Text progressText;

    public async UniTask DownloadWithProgress(IEnumerable<string> addresses)
    {
        long totalSize = await GetDownloadSizeAsync(addresses);

        if (totalSize == 0)
        {
            Debug.Log("All assets are already downloaded");
            return;
        }

        Debug.Log($"Total download size: {FormatBytes(totalSize)}");

        var downloadHandle = Addressables.DownloadDependenciesAsync(addresses, Addressables.MergeMode.Union);

        while (!downloadHandle.IsDone)
        {
            float progress = downloadHandle.GetDownloadStatus().Percent;
            progressBar.value = progress;
            progressText.text = $"{progress * 100:F0}%";

            await UniTask.Yield();
        }

        Addressables.Release(downloadHandle);
        Debug.Log("Download complete!");
    }

    private async UniTask<long> GetDownloadSizeAsync(IEnumerable<string> addresses)
    {
        var handle = Addressables.GetDownloadSizeAsync(addresses);
        await handle.ToUniTask();
        var size = handle.Result;
        Addressables.Release(handle);
        return size;
    }

    private string FormatBytes(long bytes)
    {
        string[] suffixes = { "B", "KB", "MB", "GB" };
        int i = 0;
        float size = bytes;

        while (size >= 1024 && i < suffixes.Length - 1)
        {
            size /= 1024;
            i++;
        }

        return $"{size:F2} {suffixes[i]}";
    }
}
```

---

## 错误处理

```csharp
public class SafeAddressablesLoader : MonoBehaviour
{
    public async UniTask<T> LoadSafeAsync<T>(string address) where T : Object
    {
        try
        {
            var handle = Addressables.LoadAssetAsync<T>(address);
            await handle.ToUniTask();

            if (handle.Status == AsyncOperationStatus.Failed)
            {
                Debug.LogError($"Failed to load asset: {address}");
                Addressables.Release(handle);
                return null;
            }

            return handle.Result;
        }
        catch (Exception e)
        {
            Debug.LogException(e);
            return null;
        }
    }

    // 带重试
    public async UniTask<T> LoadWithRetryAsync<T>(string address, int maxRetries = 3) where T : Object
    {
        for (int i = 0; i < maxRetries; i++)
        {
            try
            {
                var result = await LoadSafeAsync<T>(address);
                if (result != null)
                {
                    return result;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"Retry {i + 1}/{maxRetries}: {e.Message}");
            }

            await UniTask.Delay(1000);
        }

        Debug.LogError($"Failed after {maxRetries} retries: {address}");
        return null;
    }
}
```

---

## 性能优化

### 预加载

```csharp
public class AddressablesPreloader : MonoBehaviour
{
    [SerializeField] private string[] preloadLabels;

    private async void Start()
    {
        await PreloadByLabels(preloadLabels);
    }

    public async UniTask PreloadByLabels(string[] labels)
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        foreach (var label in labels)
        {
            var handle = Addressables.DownloadDependenciesAsync(label);
            await handle.ToUniTask();
            Addressables.Release(handle);
        }

        stopwatch.Stop();
        Debug.Log($"Preload completed in {stopwatch.ElapsedMilliseconds}ms");
    }
}
```

### 批量加载

```csharp
// 批量加载同一标签的资源
public async UniTask<IList<T>> LoadBatchAsync<T>(string label) where T : Object
{
    var locationsHandle = Addressables.LoadResourceLocationsAsync(label);
    await locationsHandle.ToUniTask();

    var locations = locationsHandle.Result;
    var handles = new AsyncOperationHandle<T>[locations.Count];

    for (int i = 0; i < locations.Count; i++)
    {
        handles[i] = Addressables.LoadAssetAsync<T>(locations[i]);
    }

    await UniTask.WhenAll(handles.Select(h => h.ToUniTask()));

    var results = new List<T>();
    foreach (var handle in handles)
    {
        if (handle.Status == AsyncOperationStatus.Succeeded)
        {
            results.Add(handle.Result);
        }
    }

    Addressables.Release(locationsHandle);
    return results;
}
```

---

## 最佳实践

### DO ✅

- 缓存Handle避免重复加载
- 使用标签管理资源组
- 实现下载进度反馈
- 正确释放资源避免内存泄漏

### DON'T ❌

- 不要忘记Release Handle
- 不要在Update中加载资源
- 不要混用Addressables和Resources
- 不要忽略加载失败

---

## 相关链接

- 深入学习: [打包与热更新](../35_高级主题/教程-打包与热更新.md)
- 热更新对比: [热更新方案对比](热更新方案对比.md)
- 官方文档: [Addressables Package](https://docs.unity3d.com/Packages/com.unity.addressables@latest)
