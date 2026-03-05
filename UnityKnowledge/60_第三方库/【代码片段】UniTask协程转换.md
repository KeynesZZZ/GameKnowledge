---
title: 【代码片段】UniTask协程转换
tags: [Unity, 第三方库, UniTask, 代码片段]
category: 第三方库
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: 协程转UniTask代码片段
unity_version: 2021.3+
---
# 代码片段 - UniTask协程转换

> Coroutine到UniTask的迁移对照表 `#第三方库` `#异步编程` `#代码片段`

## 完整对照表

| Coroutine | UniTask | 说明 |
|-----------|---------|------|
| `yield return null` | `await UniTask.Yield()` | 等待一帧 |
| `yield return new WaitForEndOfFrame()` | `await UniTask.WaitForEndOfFrame()` | 等待帧末 |
| `yield return new WaitForFixedUpdate()` | `await UniTask.WaitForFixedUpdate()` | 等待FixedUpdate |
| `yield return new WaitForSeconds(1f)` | `await UniTask.Delay(TimeSpan.FromSeconds(1f))` | 等待秒数 |
| `yield return new WaitForSecondsRealtime(1f)` | `await UniTask.Delay(TimeSpan.FromSeconds(1f), ignoreTimeScale: true)` | 忽略时间缩放 |
| `yield return new WaitUntil(() => cond)` | `await UniTask.WaitUntil(() => cond)` | 等待条件为true |
| `yield return new WaitWhile(() => cond)` | `await UniTask.WaitWhile(() => cond)` | 等待条件为false |
| `yield return StartCoroutine(Co())` | `await CoAsync()` | 等待协程/任务 |
| `yield return www` | `await webRequest.ToUniTask()` | 网络请求 |
| `yield return asyncOp` | `await asyncOp.ToUniTask()` | 异步操作 |

---

## 转换示例

### 1. 基础等待

```csharp
// ========== Coroutine ==========
IEnumerator ExampleCoroutine()
{
    Debug.Log("Start");
    yield return new WaitForSeconds(1f);
    Debug.Log("1 second later");
    yield return null;
    Debug.Log("Next frame");
}

// ========== UniTask ==========
async UniTaskVoid ExampleUniTask()
{
    Debug.Log("Start");
    await UniTask.Delay(TimeSpan.FromSeconds(1f));
    Debug.Log("1 second later");
    await UniTask.Yield();
    Debug.Log("Next frame");
}
```

### 2. 条件等待

```csharp
// ========== Coroutine ==========
private bool isLoaded = false;

IEnumerator WaitForLoadCoroutine()
{
    yield return new WaitUntil(() => isLoaded);
    Debug.Log("Loaded!");
}

// ========== UniTask ==========
private bool isLoaded = false;

async UniTaskVoid WaitForLoadUniTask()
{
    await UniTask.WaitUntil(() => isLoaded);
    Debug.Log("Loaded!");
}
```

### 3. 循环动画

```csharp
// ========== Coroutine ==========
IEnumerator PulseCoroutine()
{
    while (true)
    {
        transform.localScale = Vector3.one * 1.1f;
        yield return new WaitForSeconds(0.5f);
        transform.localScale = Vector3.one;
        yield return new WaitForSeconds(0.5f);
    }
}

// ========== UniTask ==========
async UniTaskVoid PulseUniTask(CancellationToken ct)
{
    while (!ct.IsCancellationRequested)
    {
        transform.localScale = Vector3.one * 1.1f;
        await UniTask.Delay(TimeSpan.FromSeconds(0.5f), cancellationToken: ct);
        transform.localScale = Vector3.one;
        await UniTask.Delay(TimeSpan.FromSeconds(0.5f), cancellationToken: ct);
    }
}
```

### 4. 资源加载

```csharp
// ========== Coroutine ==========
IEnumerator LoadSceneCoroutine(string sceneName)
{
    var op = SceneManager.LoadSceneAsync(sceneName);
    while (!op.isDone)
    {
        loadingBar.value = op.progress;
        yield return null;
    }
    OnSceneLoaded();
}

// ========== UniTask ==========
async UniTaskVoid LoadSceneUniTask(string sceneName)
{
    var op = SceneManager.LoadSceneAsync(sceneName);
    await op.ToUniTask(Progress.Create<float>(p => loadingBar.value = p));
    OnSceneLoaded();
}
```

### 5. 网络请求

```csharp
// ========== Coroutine ==========
IEnumerator FetchDataCoroutine(string url)
{
    using (var www = UnityWebRequest.Get(url))
    {
        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.Success)
        {
            OnDataReceived(www.downloadHandler.text);
        }
        else
        {
            OnError(www.error);
        }
    }
}

// ========== UniTask ==========
async UniTaskVoid FetchDataUniTask(string url, CancellationToken ct = default)
{
    try
    {
        using var request = UnityWebRequest.Get(url);
        await request.SendWebRequest().ToUniTask(cancellationToken: ct);

        if (request.result == UnityWebRequest.Result.Success)
        {
            OnDataReceived(request.downloadHandler.text);
        }
        else
        {
            OnError(request.error);
        }
    }
    catch (OperationCanceledException)
    {
        Debug.Log("Request cancelled");
    }
}
```

### 6. 带返回值

```csharp
// ========== Coroutine (需要回调) ==========
void LoadTextureCoroutine(string url, Action<Texture2D> callback)
{
    StartCoroutine(LoadTextureInternal(url, callback));
}

IEnumerator LoadTextureInternal(string url, Action<Texture2D> callback)
{
    using (var www = UnityWebRequestTexture.GetTexture(url))
    {
        yield return www.SendWebRequest();
        if (www.result == UnityWebRequest.Result.Success)
        {
            callback(((DownloadHandlerTexture)www.downloadHandler).texture);
        }
        else
        {
            callback(null);
        }
    }
}

// ========== UniTask (直接返回) ==========
async UniTask<Texture2D> LoadTextureUniTask(string url, CancellationToken ct = default)
{
    using var request = UnityWebRequestTexture.GetTexture(url);
    await request.SendWebRequest().ToUniTask(cancellationToken: ct);

    if (request.result == UnityWebRequest.Result.Success)
    {
        return ((DownloadHandlerTexture)request.downloadHandler).texture;
    }
    return null;
}

// 调用对比
LoadTextureCoroutine("url", texture => { /* 使用texture */ });
var texture = await LoadTextureUniTask("url");
```

### 7. 嵌套协程

```csharp
// ========== Coroutine ==========
IEnumerator ParentCoroutine()
{
    yield return StartCoroutine(ChildCoroutine1());
    yield return StartCoroutine(ChildCoroutine2());
    Debug.Log("All done");
}

IEnumerator ChildCoroutine1()
{
    yield return new WaitForSeconds(1f);
    Debug.Log("Child 1 done");
}

IEnumerator ChildCoroutine2()
{
    yield return new WaitForSeconds(0.5f);
    Debug.Log("Child 2 done");
}

// ========== UniTask ==========
async UniTaskVoid ParentUniTask()
{
    await ChildUniTask1();
    await ChildUniTask2();
    Debug.Log("All done");
}

async UniTask ChildUniTask1()
{
    await UniTask.Delay(TimeSpan.FromSeconds(1f));
    Debug.Log("Child 1 done");
}

async UniTask ChildUniTask2()
{
    await UniTask.Delay(TimeSpan.FromSeconds(0.5f));
    Debug.Log("Child 2 done");
}
```

### 8. 并行执行

```csharp
// ========== Coroutine (复杂) ==========
IEnumerator ParallelCoroutine()
{
    int completed = 0;

    StartCoroutine(Task1Coroutine(() => completed++));
    StartCoroutine(Task2Coroutine(() => completed++));
    StartCoroutine(Task3Coroutine(() => completed++));

    yield return new WaitUntil(() => completed >= 3);
    Debug.Log("All parallel tasks done");
}

// ========== UniTask (简单) ==========
async UniTaskVoid ParallelUniTask()
{
    await UniTask.WhenAll(
        Task1UniTask(),
        Task2UniTask(),
        Task3UniTask()
    );
    Debug.Log("All parallel tasks done");
}
```

### 9. 取消支持

```csharp
// ========== Coroutine (手动取消) ==========
private bool isCancelled = false;

IEnumerator CancellableCoroutine()
{
    for (int i = 0; i < 100; i++)
    {
        if (isCancelled) yield break;
        yield return new WaitForSeconds(0.1f);
        Debug.Log(i);
    }
}

void Cancel()
{
    isCancelled = true;
}

// ========== UniTask (CancellationToken) ==========
private CancellationTokenSource cts;

async UniTaskVoid CancellableUniTask()
{
    try
    {
        for (int i = 0; i < 100; i++)
        {
            await UniTask.Delay(100, cancellationToken: cts.Token);
            Debug.Log(i);
        }
    }
    catch (OperationCanceledException)
    {
        Debug.Log("Cancelled");
    }
}

void Cancel()
{
    cts.Cancel();
}
```

### 10. 超时处理

```csharp
// ========== Coroutine (复杂) ==========
IEnumerator TimeoutCoroutine(float timeout)
{
    float elapsed = 0f;
    bool completed = false;

    StartCoroutine(WorkCoroutine(() => completed = true));

    while (!completed && elapsed < timeout)
    {
        elapsed += Time.deltaTime;
        yield return null;
    }

    if (!completed)
    {
        Debug.Log("Timeout!");
    }
}

// ========== UniTask (内置) ==========
async UniTaskVoid TimeoutUniTask()
{
    try
    {
        await WorkUniTask().Timeout(TimeSpan.FromSeconds(5f));
    }
    catch (TimeoutException)
    {
        Debug.Log("Timeout!");
    }
}
```

---

## 迁移检查清单

### 转换前检查

- [ ] 识别所有 `yield return` 语句
- [ ] 确定是否有返回值需求
- [ ] 检查是否需要取消支持
- [ ] 评估是否需要并行执行

### 转换后验证

- [ ] 行为与原协程一致
- [ ] 异常处理完整
- [ ] 取消逻辑正确
- [ ] 无内存泄漏

---

## 常见陷阱

### 1. 忘记Forget()

```csharp
// ❌ 错误 - UniTaskVoid必须调用Forget
async UniTaskVoid DoSomething()
{
    await UniTask.Delay(1000);
}
DoSomething();  // 不会执行！

// ✅ 正确
DoSomething().Forget();
```

### 2. 使用Thread.Sleep

```csharp
// ❌ 错误 - 阻塞主线程
async UniTaskVoid Wrong()
{
    Thread.Sleep(1000);  // 阻塞！
}

// ✅ 正确
async UniTaskVoid Correct()
{
    await UniTask.Delay(1000);  // 不阻塞
}
```

### 3. 异常未处理

```csharp
// ❌ 错误 - 异常被静默忽略
async UniTaskVoid Unsafe()
{
    throw new Exception("Error");  // 丢失
}
Unsafe().Forget();

// ✅ 正确
async UniTaskVoid Safe()
{
    try
    {
        throw new Exception("Error");
    }
    catch (Exception e)
    {
        Debug.LogException(e);
    }
}
Safe().Forget();
```

---

## 相关链接

- [UniTask 异步编程](UniTask%20异步编程.md)
- [高级编程](../36_高级编程/教程-)
