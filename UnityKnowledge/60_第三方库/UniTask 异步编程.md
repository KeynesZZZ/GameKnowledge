# UniTask 异步编程

> Unity专用零GC异步解决方案完整指南 `#第三方库` `#异步编程` `#最佳实践`

## 快速参考

```csharp
// async/await
public async UniTaskVoid LoadDataAsync()
{
    var data = await LoadFromServer();
    ProcessData(data);
}

// 协程转换
await UniTask.Yield();
await UniTask.Delay(TimeSpan.FromSeconds(1));
await UniTask.WaitUntil(() => isReady);
```

---

## 为什么选择UniTask

| 对比项 | Task | Coroutine | UniTask |
|--------|------|-----------|---------|
| GC分配 | 有 | 有 | **零GC** |
| 返回值 | 支持 | 不支持 | **支持** |
| 异常处理 | 完整 | 困难 | **完整** |
| 取消支持 | 有 | 需手动 | **内置** |
| Unity集成 | 弱 | 强 | **强** |

---

## API速查表

### 等待

| 方法 | 说明 | 示例 |
|------|------|------|
| `UniTask.Yield` | 等待一帧 | `await UniTask.Yield()` |
| `UniTask.NextFrame` | 等待下一帧 | `await UniTask.NextFrame()` |
| `UniTask.WaitForEndOfFrame` | 等待帧末 | `await UniTask.WaitForEndOfFrame()` |
| `UniTask.Delay` | 延迟 | `await UniTask.Delay(1000)` |
| `UniTask.DelayFrame` | 延迟帧数 | `await UniTask.DelayFrame(10)` |
| `UniTask.WaitUntil` | 等待条件 | `await UniTask.WaitUntil(() => ready)` |
| `UniTask.WaitWhile` | 等待条件为false | `await UniTask.WaitWhile(() => loading)` |

### Unity集成

| 方法 | 说明 | 示例 |
|------|------|------|
| `StartCoroutine` | 协程转UniTask | `await StartCoroutine(Co())` |
| `ToUniTask` | AsyncOperation转换 | `op.ToUniTask()` |
| `GetAwaiter` | Unity对象等待 | `await resourceLoadOp` |

### 并发控制

| 方法 | 说明 | 示例 |
|------|------|------|
| `UniTask.WhenAll` | 全部完成 | `await UniTask.WhenAll(tasks)` |
| `UniTask.WhenAny` | 任一完成 | `await UniTask.WhenAny(tasks)` |
| `UniTask.Lazy` | 延迟执行 | `var lazy = UniTask.Lazy(Func)` |

---

## 基础用法

### 异步方法定义

```csharp
// 无返回值 - 使用UniTaskVoid
public async UniTaskVoid DoSomethingAsync()
{
    await UniTask.Delay(1000);
    Debug.Log("Done");
}

// 有返回值 - 使用UniTask<T>
public async UniTask<string> LoadTextAsync(string path)
{
    var text = await File.ReadAllTextAsync(path);
    return text;
}

// 调用方式
DoSomethingAsync().Forget();  // 不等待结果
var result = await LoadTextAsync("path");  // 等待结果
```

### 取消支持

```csharp
public async UniTask LongOperationAsync(CancellationToken ct)
{
    for (int i = 0; i < 100; i++)
    {
        ct.ThrowIfCancellationRequested();  // 检查取消
        await UniTask.Delay(100, cancellationToken: ct);
        Debug.Log($"Progress: {i}%");
    }
}

// 使用方式
private CancellationTokenSource cts;

void Start()
{
    cts = new CancellationTokenSource();
    LongOperationAsync(cts.Token).Forget();
}

void Cancel()
{
    cts.Cancel();
    cts.Dispose();
    cts = null;
}
```

### 超时处理

```csharp
public async UniTask<string> FetchWithTimeout(string url, float timeoutSeconds)
{
    try
    {
        var result = await UniTask.Timeout(
            FetchFromServer(url),
            TimeSpan.FromSeconds(timeoutSeconds)
        );
        return result;
    }
    catch (TimeoutException)
    {
        Debug.Log("Request timed out");
        return null;
    }
}

// 或使用CancellationTokenSource
public async UniTask<string> FetchWithCancellationToken(string url, float timeout)
{
    using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(timeout));
    return await FetchFromServer(url, cts.Token);
}
```

---

## 协程迁移

### 对照表

| 协程 | UniTask |
|------|---------|
| `yield return null` | `await UniTask.Yield()` |
| `yield return new WaitForSeconds(1f)` | `await UniTask.Delay(TimeSpan.FromSeconds(1f))` |
| `yield return new WaitForEndOfFrame()` | `await UniTask.WaitForEndOfFrame()` |
| `yield return new WaitUntil(() => cond)` | `await UniTask.WaitUntil(() => cond)` |
| `yield return new WaitWhile(() => cond)` | `await UniTask.WaitWhile(() => cond)` |
| `yield return StartCoroutine(Co())` | `await CoAsync()` |
| `yield return www` | `await www.ToUniTask()` |
| `yield return asyncOp` | `await asyncOp.ToUniTask()` |

### 迁移示例

```csharp
// 协程版本
private IEnumerator LoadSceneCoroutine(string sceneName)
{
    var op = SceneManager.LoadSceneAsync(sceneName);
    while (!op.isDone)
    {
        Debug.Log($"Loading: {op.progress * 100}%");
        yield return null;
    }
    Debug.Log("Scene loaded");
}

// UniTask版本
private async UniTaskVoid LoadSceneAsync(string sceneName)
{
    var op = SceneManager.LoadSceneAsync(sceneName);
    await op.ToUniTask(Progress.Create<float>(p =>
        Debug.Log($"Loading: {p * 100}%")
    ));
    Debug.Log("Scene loaded");
}
```

---

## 常用代码片段

### 资源加载

```csharp
public class ResourceLoader : MonoBehaviour
{
    public async UniTask<GameObject> LoadPrefabAsync(string path, CancellationToken ct = default)
    {
        var op = Resources.LoadAsync<GameObject>(path);
        await op.ToUniTask(cancellationToken: ct);

        if (op.asset == null)
        {
            throw new Exception($"Failed to load: {path}");
        }

        return op.asset as GameObject;
    }

    public async UniTask InstantiateAsync(string path, Vector3 position, CancellationToken ct = default)
    {
        var prefab = await LoadPrefabAsync(path, ct);
        Instantiate(prefab, position, Quaternion.identity);
    }
}
```

### 网络请求

```csharp
public class WebClient : MonoBehaviour
{
    public async UniTask<string> GetAsync(string url, CancellationToken ct = default)
    {
        using var request = UnityWebRequest.Get(url);
        await request.SendWebRequest().ToUniTask(cancellationToken: ct);

        if (request.result == UnityWebRequest.Result.Success)
        {
            return request.downloadHandler.text;
        }

        throw new Exception($"Request failed: {request.error}");
    }

    public async UniTask<Texture2D> GetTextureAsync(string url, CancellationToken ct = default)
    {
        using var request = UnityWebRequestTexture.GetTexture(url);
        await request.SendWebRequest().ToUniTask(cancellationToken: ct);

        if (request.result == UnityWebRequest.Result.Success)
        {
            return ((DownloadHandlerTexture)request.downloadHandler).texture;
        }

        throw new Exception($"Failed to load texture: {request.error}");
    }
}
```

### 进度报告

```csharp
public class ProgressExample : MonoBehaviour
{
    [SerializeField] private Slider progressBar;
    [SerializeField] private Text progressText;

    public async UniTaskVoid LoadWithProgress()
    {
        var progress = Progress.Create<float>(value =>
        {
            progressBar.value = value;
            progressText.text = $"{value * 100:F0}%";
        });

        await DownloadFileAsync("url", progress);
        Debug.Log("Download complete!");
    }

    private async UniTask DownloadFileAsync(string url, IProgress<float> progress)
    {
        using var request = UnityWebRequest.Get(url);
        var op = request.SendWebRequest();

        while (!op.isDone)
        {
            progress?.Report(op.progress);
            await UniTask.Yield();
        }

        progress?.Report(1f);
    }
}
```

### 并行执行

```csharp
public async UniTask LoadAllAssetsAsync()
{
    // 并行加载多个资源
    var tasks = new[]
    {
        LoadAssetAsync("Asset1"),
        LoadAssetAsync("Asset2"),
        LoadAssetAsync("Asset3")
    };

    // 等待全部完成
    var results = await UniTask.WhenAll(tasks);

    // 或者等待任意一个完成
    var (index, result) = await UniTask.WhenAny(tasks);
    Debug.Log($"First completed: {index}");
}
```

### 重试机制

```csharp
public async UniTask<T> RetryAsync<T>(
    Func<UniTask<T>> action,
    int maxRetries = 3,
    int delayMs = 1000)
{
    for (int i = 0; i < maxRetries; i++)
    {
        try
        {
            return await action();
        }
        catch (Exception e)
        {
            if (i == maxRetries - 1)
                throw;

            Debug.LogWarning($"Retry {i + 1}/{maxRetries}: {e.Message}");
            await UniTask.Delay(delayMs);
        }
    }

    throw new Exception("Should not reach here");
}

// 使用
var result = await RetryAsync(() => FetchFromServer(url), 3, 1000);
```

### 帧分片处理

```csharp
public class FrameSlicing : MonoBehaviour
{
    // 将大量工作分帧执行，避免卡顿
    public async UniTask ProcessLargeDataAsync(List<Item> items, CancellationToken ct = default)
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        for (int i = 0; i < items.Count; i++)
        {
            ProcessItem(items[i]);

            // 每处理50个或超过16ms，等待下一帧
            if (i % 50 == 0 || stopwatch.ElapsedMilliseconds > 16)
            {
                await UniTask.Yield(ct);
                stopwatch.Restart();
            }
        }
    }

    private void ProcessItem(Item item)
    {
        // 处理逻辑
    }
}
```

---

## 与Unity生命周期集成

### MonoBehaviour扩展

```csharp
public static class MonoBehaviourExtensions
{
    // 等待销毁时自动取消
    public static async UniTask WaitUntilDestroyed(this MonoBehaviour target, CancellationToken ct = default)
    {
        try
        {
            await UniTask.WaitUntil(() => target == null, cancellationToken: ct);
        }
        catch (OperationCanceledException)
        {
            // 正常取消
        }
    }
}

// 使用
public class MyComponent : MonoBehaviour
{
    private async UniTaskVoid DoWorkAsync()
    {
        var cts = new CancellationTokenSource();

        // 销毁时自动取消
        this.GetCancellationTokenOnDestroy().Register(() => cts.Cancel());

        await LongOperationAsync(cts.Token);
    }
}
```

### PlayerLoop集成

```csharp
// 在特定PlayerLoop时机执行
public async UniTaskVoid ExecuteAtSpecificTime()
{
    await UniTask.Yield(PlayerLoopTiming.PreUpdate);
    Debug.Log("PreUpdate");

    await UniTask.Yield(PlayerLoopTiming.Update);
    Debug.Log("Update");

    await UniTask.Yield(PlayerLoopTiming.PostLateUpdate);
    Debug.Log("PostLateUpdate");
}
```

---

## 错误处理

```csharp
public async UniTaskVoid SafeExecuteAsync()
{
    try
    {
        await RiskyOperationAsync();
    }
    catch (OperationCanceledException)
    {
        Debug.Log("Operation was cancelled");
    }
    catch (TimeoutException)
    {
        Debug.Log("Operation timed out");
    }
    catch (Exception e)
    {
        Debug.LogException(e);
    }
    finally
    {
        // 清理资源
    }
}

// 静默忽略异常
public async UniTaskVoid SilentAsync()
{
    await RiskyOperationAsync().SuppressCancellationThrow();
}
```

---

## 性能对比

| 操作 | Coroutine | UniTask | 性能提升 |
|------|-----------|---------|----------|
| 等待1帧 | 0.3μs + GC | 0.1μs | 3x |
| 等待1秒 | 0.3μs + GC | 0.1μs | 3x |
| 1000次等待 | 300μs + 80KB | 100μs | 3x + 零GC |

---

## 常见问题

### Q: UniTaskVoid vs UniTask?

```csharp
// UniTaskVoid - fire-and-forget，不能await
public async UniTaskVoid FireAndForget()
{
    await UniTask.Delay(1000);
}
FireAndForget().Forget();  // 必须调用Forget()

// UniTask - 可以await，可以获取返回值
public async UniTask<string> GetValue()
{
    await UniTask.Delay(1000);
    return "result";
}
var result = await GetValue();
```

### Q: 如何在非MonoBehaviour中使用?

```csharp
// 静态方法中直接使用
public static class GameLogic
{
    public static async UniTask<int> CalculateAsync()
    {
        await UniTask.Delay(100);
        return 42;
    }
}

// 需要CancellationToken时传入
public static async UniTask ProcessAsync(CancellationToken ct)
{
    await UniTask.Delay(1000, cancellationToken: ct);
}
```

### Q: 如何调试?

```csharp
// 使用UniTaskTracker（仅开发环境）
#if UNITY_EDITOR
[MenuItem("Tools/UniTask Tracker")]
static void OpenTracker()
{
    UniTaskTrackerWindow.OpenWindow();
}
#endif

// 添加追踪标签
await UniTask.Delay(1000).AttachExternalTrace("MyDelay");
```

---

## 最佳实践

### DO ✅

- 使用CancellationToken支持取消
- 在OnDestroy时取消正在进行的任务
- 使用UniTaskVoid用于fire-and-forget场景
- 合理使用WhenAll/WhenAny进行并发控制
- 处理异常避免静默失败

### DON'T ❌

- 不要忘记调用Forget() on UniTaskVoid
- 不要在UniTask中使用Thread.Sleep（用UniTask.Delay）
- 不要忽略OperationCanceledException
- 不要在热路径中频繁创建CancellationTokenSource

---

## 相关链接

- GitHub: [UniTask](https://github.com/Cysharp/UniTask)
- 高级编程: [高级编程学习路径](../36_高级编程/教程-高级编程_学习路径.md)
