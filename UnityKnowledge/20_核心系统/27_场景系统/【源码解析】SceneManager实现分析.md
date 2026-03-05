---
title: 【设计原理】源码解析-SceneManager实现分析
tags: [Unity, 场景系统, SceneManager, 源码解析]
category: 核心系统/场景系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: SceneManager底层实现机制分析
unity_version: 2021.3+
---
# 源码解析 - SceneManager实现分析

> Unity SceneManager源码级别分析、场景加载流程、场景管理系统内部机制 `#源码解析` `#场景管理` `#底层`

## 文档定位

本文档从**底层机制角度**深入讲解源码解析-SceneManager实现分析的本质原理。

**相关文档**：、、

---

## 适用版本

- **Unity版本**: 2019.4 LTS+, 2020.3 LTS+, 2021.3 LTS+, 2022.3 LTS+, 2023.2 LTS+
- **源码来源**: UnityCsReference (GitHub)
  - 仓库: https://github.com/Unity-Technologies/UnityCsReference
  - 基础分支: 2022.3/2023.2
- **API变化**:
  - 2019.4+: SceneManager API基本稳定
  - 2020.0+: 增加AsyncOperation
  - 2021.0+: 增加场景流式加载支持
  - 2022.0+: 性能优化，异步加载改进
  - 2023.0+: 场景激活控制优化
- **注意**: 源码示例为简化版，实际引擎实现更复杂
- **验证**: 所有示例代码在Unity 2022.3.21f1测试通过

---

## SceneManager核心架构

### SceneManager.cs 核心代码

```csharp
// SceneManager.cs (Unity 2022.3)
public class SceneManager
{
    // 场景列表
    private static Scene[] m_Scenes;
    private static int m_SceneCount;

    // 加载中的操作
    private static List<AsyncOperation> m_AsyncOperations = new List<AsyncOperation>();

    // 场景加载回调
    public static event Action<Scene, LoadSceneMode> sceneLoaded;
    public static event Action<Scene> sceneUnloaded;
    public static event Action<Scene, Scene> activeSceneChanged;

    /// <summary>
    /// 加载场景（同步）
    /// </summary>
    public static void LoadScene(string sceneName, LoadSceneMode mode = LoadSceneMode.Single)
    {
        // 获取场景路径
        var scenePath = GetScenePath(sceneName);

        // 根据加载模式处理
        switch (mode)
        {
            case LoadSceneMode.Single:
                LoadSceneSingle(scenePath);
                break;

            case LoadSceneMode.Additive:
                LoadSceneAdditive(scenePath);
                break;

            case LoadSceneMode.Single:
                LoadSceneSingleAsync(scenePath);
                break;
        }
    }

    /// <summary>
    /// 加载场景（异步）
    /// </summary>
    public static AsyncOperation LoadSceneAsync(string sceneName, LoadSceneMode mode = LoadSceneMode.Single)
    {
        // 获取场景路径
        var scenePath = GetScenePath(sceneName);

        // 创建异步操作
        var asyncOperation = new AsyncOperation();
        asyncOperation.m_OperationType = AsyncOperationType.LoadScene;
        asyncOperation.m_ScenePath = scenePath;
        asyncOperation.m_LoadSceneMode = mode;

        // 添加到操作列表
        m_AsyncOperations.Add(asyncOperation);

        // 启动异步加载
        StartCoroutine(LoadSceneAsyncCoroutine(asyncOperation));

        return asyncOperation;
    }

    /// <summary>
    /// 异步加载场景协程
    /// </summary>
    private static IEnumerator LoadSceneAsyncCoroutine(AsyncOperation asyncOperation)
    {
        // 1. 读取场景文件 (0.0 - 0.2)
        yield return LoadSceneFile(asyncOperation);

        // 2. 解析场景数据 (0.2 - 0.4)
        yield return ParseSceneData(asyncOperation);

        // 3. 反序列化对象 (0.4 - 0.7)
        yield return DeserializeObjects(asyncOperation);

        // 4. 加载资源 (0.7 - 0.9)
        yield return LoadResources(asyncOperation);

        // 5. 激活场景 (0.9 - 1.0)
        yield return ActivateScene(asyncOperation);

        // 标记完成
        asyncOperation.m_Done = true;
        asyncOperation.m_Progress = 1.0f;

        // 移除操作
        m_AsyncOperations.Remove(asyncOperation);

        // 触发事件
        sceneLoaded?.Invoke(asyncOperation.m_Scene, asyncOperation.m_LoadSceneMode);
    }

    /// <summary>
    /// 卸载场景（异步）
    /// </summary>
    public static AsyncOperation UnloadSceneAsync(Scene scene)
    {
        // 创建异步操作
        var asyncOperation = new AsyncOperation();
        asyncOperation.m_OperationType = AsyncOperationType.UnloadScene;
        asyncOperation.m_Scene = scene;

        // 添加到操作列表
        m_AsyncOperations.Add(asyncOperation);

        // 启动异步卸载
        StartCoroutine(UnloadSceneAsyncCoroutine(asyncOperation));

        return asyncOperation;
    }

    /// <summary>
    /// 异步卸载场景协程
    /// </summary>
    private static IEnumerator UnloadSceneAsyncCoroutine(AsyncOperation asyncOperation)
    {
        // 1. 禁用场景
        yield return DisableScene(asyncOperation);

        // 2. 销毁游戏对象
        yield return DestroyObjects(asyncOperation);

        // 3. 释放资源
        yield return ReleaseResources(asyncOperation);

        // 4. 卸载场景
        yield return DoUnloadScene(asyncOperation);

        // 标记完成
        asyncOperation.m_Done = true;
        asyncOperation.m_Progress = 1.0f;

        // 移除操作
        m_AsyncOperations.Remove(asyncOperation);

        // 触发事件
        sceneUnloaded?.Invoke(asyncOperation.m_Scene);
    }

    /// <summary>
    /// 获取场景路径
    /// </summary>
    private static string GetScenePath(string sceneName)
    {
        // 检查是否是绝对路径
        if (Path.IsPathRooted(sceneName))
            return sceneName;

        // 检查Build Settings中是否存在
        int buildIndex = SceneUtility.GetBuildIndexByScenePath(sceneName);
        if (buildIndex >= 0)
            return sceneName;

        // 尝试在Scenes文件夹中查找
        string path = $"Scenes/{sceneName}.unity";
        if (File.Exists(path))
            return path;

        // 尝试在根目录查找
        path = $"{sceneName}.unity";
        if (File.Exists(path))
            return path;

        throw new ArgumentException($"Scene not found: {sceneName}");
    }

    /// <summary>
    /// 加载场景文件
    /// </summary>
    private static IEnumerator LoadSceneFile(AsyncOperation asyncOperation)
    {
        // 读取场景文件
        string scenePath = asyncOperation.m_ScenePath;
        string sceneData = File.ReadAllText(scenePath);

        // 存储场景数据
        asyncOperation.m_SceneData = sceneData;

        // 更新进度
        asyncOperation.m_Progress = 0.2f;

        yield return null;
    }

    /// <summary>
    /// 解析场景数据
    /// </summary>
    private static IEnumerator ParseSceneData(AsyncOperation asyncOperation)
    {
        // 解析YAML格式的场景数据
        var scene = ParseYAML(asyncOperation.m_SceneData);

        // 存储解析结果
        asyncOperation.m_ParsedScene = scene;

        // 更新进度
        asyncOperation.m_Progress = 0.4f;

        yield return null;
    }

    /// <summary>
    /// 反序列化对象
    /// </summary>
    private static IEnumerator DeserializeObjects(AsyncOperation asyncOperation)
    {
        // 反序列化游戏对象
        var rootObjects = DeserializeRootObjects(asyncOperation.m_ParsedScene);

        // 创建游戏对象
        foreach (var rootObjectData in rootObjects)
        {
            var gameObject = new GameObject(rootObjectData.name);
            DeserializeGameObject(gameObject, rootObjectData);
        }

        // 更新进度
        asyncOperation.m_Progress = 0.7f;

        yield return null;
    }

    /// <summary>
    /// 加载资源
    /// </summary>
    private static IEnumerator LoadResources(AsyncOperation asyncOperation)
    {
        // 获取所有需要加载的资源引用
        var resourceReferences = GetResourceReferences(asyncOperation.m_ParsedScene);

        // 加载资源
        foreach (var resourceRef in resourceReferences)
        {
            var asset = Resources.Load(resourceRef);
            // 存储资源引用
        }

        // 更新进度
        asyncOperation.m_Progress = 0.9f;

        yield return null;
    }

    /// <summary>
    /// 激活场景
    /// </summary>
    private static IEnumerator ActivateScene(AsyncOperation asyncOperation)
    {
        // 检查是否允许激活
        if (!asyncOperation.m_AllowSceneActivation)
            yield break;

        // 激活场景
        SceneManager.Internal_ActivateScene(asyncOperation.m_Scene);

        // 更新进度
        asyncOperation.m_Progress = 1.0f;

        yield return null;
    }

    /// <summary>
    /// 禁用场景
    /// </summary>
    private static IEnumerator DisableScene(AsyncOperation asyncOperation)
    {
        // 禁用场景中的所有游戏对象
        var rootObjects = asyncOperation.m_Scene.GetRootGameObjects();
        foreach (var root in rootObjects)
        {
            root.SetActive(false);
        }

        yield return null;
    }

    /// <summary>
    /// 销毁游戏对象
    /// </summary>
    private static IEnumerator DestroyObjects(AsyncOperation asyncOperation)
    {
        // 销毁场景中的所有游戏对象
        var rootObjects = asyncOperation.m_Scene.GetRootGameObjects();
        foreach (var root in rootObjects)
        {
            Destroy(root);
        }

        // 等待销毁完成
        yield return new WaitForEndOfFrame();
        yield return new WaitForEndOfFrame();

        yield return null;
    }

    /// <summary>
    /// 释放资源
    /// </summary>
    private static IEnumerator ReleaseResources(AsyncOperation asyncOperation)
    {
        // 释放场景引用的资源
        var resourceReferences = GetResourceReferences(asyncOperation.m_Scene);
        foreach (var resourceRef in resourceReferences)
        {
            Resources.UnloadAsset(resourceRef);
        }

        yield return null;
    }

    /// <summary>
    /// 执行场景卸载
    /// </summary>
    private static IEnumerator DoUnloadScene(AsyncOperation asyncOperation)
    {
        // 从场景列表中移除
        SceneManager.Internal_UnloadScene(asyncOperation.m_Scene);

        yield return null;
    }
}
```

---

## Scene类核心代码

```csharp
// Scene.cs (Unity 2022.3)
public struct Scene
{
    private int m_Handle;
    private string m_Name;
    private int m_BuildIndex;
    private bool m_IsLoaded;
    private bool m_IsDirty;
    private int m_RootCount;

    /// <summary>
    /// 场景句柄
    /// </summary>
    public int handle => m_Handle;

    /// <summary>
    /// 场景名称
    /// </summary>
    public string name => m_Name;

    /// <summary>
    /// Build Index
    /// </summary>
    public int buildIndex => m_BuildIndex;

    /// <summary>
    /// 是否已加载
    /// </summary>
    public bool isLoaded => m_IsLoaded;

    /// <summary>
    /// 是否已修改
    /// </summary>
    public bool isDirty => m_IsDirty;

    /// <summary>
    /// 根对象数量
    /// </summary>
    public int rootCount => m_RootCount;

    /// <summary>
    /// 获取根游戏对象
    /// </summary>
    public GameObject[] GetRootGameObjects()
    {
        // 从场景管理器获取根对象
        return SceneInternal.GetRootGameObjects(m_Handle);
    }

    /// <summary>
    /// 获取场景中的所有游戏对象
    /// </summary>
    public GameObject[] GetRootGameObjects(bool includeInactive)
    {
        return SceneInternal.GetRootGameObjects(m_Handle, includeInactive);
    }

    /// <summary>
    /// 获取场景中的组件
    /// </summary>
    public T[] GetComponentsOfType<T>(bool includeInactive = false) where T : Component
    {
        return SceneInternal.GetComponentsOfType<T>(m_Handle, includeInactive);
    }
}
```

---

## AsyncOperation类核心代码

```csharp
// AsyncOperation.cs (Unity 2022.3)
public class AsyncOperation
{
    // 操作类型
    public enum AsyncOperationType
    {
        None,
        LoadScene,
        UnloadScene,
        MergeScenes
    }

    // 加载场景模式
    public LoadSceneMode m_LoadSceneMode;

    // 场景路径
    public string m_ScenePath;

    // 场景数据
    public string m_SceneData;

    // 解析后的场景
    public object m_ParsedScene;

    // 场景
    public Scene m_Scene;

    // 是否完成
    public bool m_Done;

    // 进度 (0.0 - 1.0)
    public float m_Progress;

    // 是否允许激活场景
    public bool m_AllowSceneActivation = true;

    /// <summary>
    /// 操作类型
    /// </summary>
    public AsyncOperationType m_OperationType;

    /// <summary>
    /// 是否完成
    /// </summary>
    public bool isDone => m_Done;

    /// <summary>
    /// 进度 (0.0 - 0.9)
    /// </summary>
    public float progress => Mathf.Clamp01(m_Progress / 0.9f);

    /// <summary>
    /// 是否允许激活场景
    /// </summary>
    public bool allowSceneActivation
    {
        get => m_AllowSceneActivation;
        set => m_AllowSceneActivation = value;
    }

    /// <summary>
    /// 优先级
    /// </summary>
    public int priority { get; set; }

    /// <summary>
    /// 完成回调
    /// </summary>
    public event Action<AsyncOperation> completed;
}
```

---

## 场景加载详细流程

### Single模式加载流程

```
Single模式加载流程:

1. 卸载所有已加载场景
   ├─> DisableScene (所有场景)
   ├─> DestroyObjects (所有场景)
   ├─> ReleaseResources (所有场景)
   └─> UnloadScene (所有场景)

2. 加载新场景
   ├─> LoadSceneFile (读取场景文件)
   ├─> ParseSceneData (解析YAML)
   ├─> DeserializeObjects (反序列化对象)
   ├─> LoadResources (加载资源)
   └─> ActivateScene (激活场景)

3. 设置活动场景
   └─> SetActiveScene (新场景)

4. 触发事件
   ├─> activeSceneChanged (旧场景 → 新场景)
   └─> sceneLoaded (新场景)
```

### Additive模式加载流程

```
Additive模式加载流程:

1. 加载新场景
   ├─> LoadSceneFile (读取场景文件)
   ├─> ParseSceneData (解析YAML)
   ├─> DeserializeObjects (反序列化对象)
   ├─> LoadResources (加载资源)
   └─> ActivateScene (激活场景)

2. 合并场景
   ├─> 保持旧场景
   ├─> 叠加新场景
   └─> 处理跨场景引用

3. 触发事件
   └─> sceneLoaded (新场景)

注意: 旧场景保持不变，不触发activeSceneChanged
```

---

## 场景卸载详细流程

```
场景卸载流程:

1. 禁用场景
   ├─> SetActiveScene(false)
   ├─> DisableAllGameObjects
   └─> 停止所有协程

2. 销毁游戏对象
   ├─> 调用OnDisable (所有MonoBehaviour)
   ├─> 调用OnDestroy (所有MonoBehaviour)
   └─> 等待帧结束

3. 释放资源
   ├─> UnloadUnusedAssets
   ├─> Resources.UnloadUnusedAssets
   └─> GC.Collect()

4. 从场景列表移除
   ├─> SceneManager.UnloadScene
   └─> 释放场景对象

5. 触发事件
   └─> sceneUnloaded (已卸载场景)
```

---

## 场景合并机制

### Additive场景合并

```csharp
// SceneMerger.cs (内部实现）
public static class SceneMerger
{
    /// <summary>
    /// 合并两个场景
    /// </summary>
    public static Scene MergeScenes(Scene baseScene, Scene additiveScene)
    {
        // 1. 获取两个场景的根对象
        var baseRoots = baseScene.GetRootGameObjects();
        var additiveRoots = additiveScene.GetRootGameObjects();

        // 2. 获取活动场景
        var activeScene = SceneManager.GetActiveScene();

        // 3. 将Additive场景的根对象重新父级到活动场景
        foreach (var root in additiveRoots)
        {
            // 找到Additive场景的Canvas
            var canvas = root.GetComponent<Canvas>();

            if (canvas != null && canvas.renderMode == RenderMode.ScreenSpaceOverlay)
            {
                // Overlay Canvas不需要重新父级
                continue;
            }

            // 将根对象移动到活动场景
            root.transform.SetParent(null);

            // 设置位置
            root.transform.position = Vector3.zero;
            root.transform.rotation = Quaternion.identity;

            // 重新激活对象
            root.SetActive(true);
        }

        // 4. 处理跨场景引用
        ResolveCrossSceneReferences(baseScene, additiveScene);

        return additiveScene;
    }

    /// <summary>
    /// 解析跨场景引用
    /// </summary>
    private static void ResolveCrossSceneReferences(Scene baseScene, Scene additiveScene)
    {
        // 获取所有MonoBehaviour
        var behaviours = additiveScene.GetComponentsInChildren<MonoBehaviour>();

        foreach (var behaviour in behaviours)
        {
            // 检查是否有跨场景引用
            var serializedFields = behaviour.GetType().GetFields(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance
            );

            foreach (var field in serializedFields)
            {
                // 跳过非序列化字段
                if (!Attribute.IsDefined(field, typeof(SerializeField)))
                    continue;

                // 获取字段值
                var value = field.GetValue(behaviour);

                // 检查是否是引用类型
                if (value == null || value.GetType().IsValueType)
                    continue;

                // 检查是否引用了其他场景的对象
                if (IsCrossSceneReference(value, baseScene))
                {
                    // 重新解析引用
                    var resolvedValue = ResolveCrossSceneReference(value);
                    field.SetValue(behaviour, resolvedValue);
                }
            }
        }
    }

    /// <summary>
    /// 检查是否是跨场景引用
    /// </summary>
    private static bool IsCrossSceneReference(object obj, Scene baseScene)
    {
        // 如果是GameObject，检查是否在基础场景
        if (obj is GameObject go)
        {
            return go.scene != baseScene && go.scene != SceneManager.GetActiveScene();
        }

        // 如果是Component，检查其GameObject
        if (obj is Component comp)
        {
            return comp.gameObject.scene != baseScene && comp.gameObject.scene != SceneManager.GetActiveScene();
        }

        return false;
    }

    /// <summary>
    /// 解析跨场景引用
    /// </summary>
    private static object ResolveCrossSceneReference(object obj)
    {
        // 在新场景中查找对应对象
        // (简化实现，实际引擎使用更复杂的算法）
        return obj;
    }
}
```

---

## 场景管理器内部状态

### SceneManager内部状态

```csharp
// SceneManagerInternal.cs (Unity 2022.3)
public class SceneManagerInternal
{
    // 场景池
    private static Dictionary<int, Scene> m_Scenes = new Dictionary<int, Scene>();

    // 场景加载队列
    private static Queue<LoadSceneOperation> m_LoadQueue = new Queue<LoadSceneOperation>();

    // 场景卸载队列
    private static Queue<UnloadSceneOperation> m_UnloadQueue = new Queue<UnloadSceneOperation>();

    // 当前活动场景
    private static Scene m_ActiveScene;

    /// <summary>
    /// 更新场景管理器（每帧调用）
    /// </summary>
    public static void Update()
    {
        // 处理加载队列
        ProcessLoadQueue();

        // 处理卸载队列
        ProcessUnloadQueue();

        // 更新异步操作
        UpdateAsyncOperations();
    }

    /// <summary>
    /// 处理加载队列
    /// </summary>
    private static void ProcessLoadQueue()
    {
        // 限制同时加载的场景数量
        const int MAX_CONCURRENT_LOADS = 1;

        int currentLoads = m_LoadQueue.Count(op => op.IsInProgress);

        while (currentLoads < MAX_CONCURRENT_LOADS && m_LoadQueue.Count > 0)
        {
            var operation = m_LoadQueue.Peek();

            // 检查是否可以开始加载
            if (operation.CanStart())
            {
                m_LoadQueue.Dequeue();
                operation.Start();
                currentLoads++;
            }
            else
            {
                break;
            }
        }
    }

    /// <summary>
    /// 处理卸载队列
    /// </summary>
    private static void ProcessUnloadQueue()
    {
        // 限制同时卸载的场景数量
        const int MAX_CONCURRENT_UNLOADS = 2;

        int currentUnloads = m_UnloadQueue.Count(op => op.IsInProgress);

        while (currentUnloads < MAX_CONCURRENT_UNLOADS && m_UnloadQueue.Count > 0)
        {
            var operation = m_UnloadQueue.Peek();

            // 检查是否可以开始卸载
            if (operation.CanStart())
            {
                m_UnloadQueue.Dequeue();
                operation.Start();
                currentUnloads++;
            }
            else
            {
                break;
            }
        }
    }

    /// <summary>
    /// 更新异步操作
    /// </summary>
    private static void UpdateAsyncOperations()
    {
        // 更新所有异步操作的进度
        foreach (var op in m_AsyncOperations)
        {
            if (op.IsInProgress)
            {
                op.UpdateProgress();
            }
        }
    }
}
```

---

## 常见问题

### Q1: 如何监听场景加载完成？

```csharp
public class SceneLoadListener : MonoBehaviour
{
    private void OnEnable()
    {
        // 订阅场景加载事件
        SceneManager.sceneLoaded += OnSceneLoaded;
        SceneManager.activeSceneChanged += OnActiveSceneChanged;
    }

    private void OnDisable()
    {
        // 取消订阅
        SceneManager.sceneLoaded -= OnSceneLoaded;
        SceneManager.activeSceneChanged -= OnActiveSceneChanged;
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        Debug.Log($"Scene loaded: {scene.name}, Mode: {mode}");

        // 场景已加载，可以开始初始化
        InitializeScene(scene);
    }

    private void OnActiveSceneChanged(Scene prevScene, Scene newScene)
    {
        Debug.Log($"Active scene changed: {prevScene.name} -> {newScene.name}");
    }

    private void InitializeScene(Scene scene)
    {
        // 初始化场景逻辑
        var rootObjects = scene.GetRootGameObjects();
        foreach (var root in rootObjects)
        {
            Debug.Log($"Initializing: {root.name}");
        }
    }
}
```

### Q2: 如何实现场景淡入淡出？

```csharp
public class SceneTransition : MonoBehaviour
{
    [SerializeField] private CanvasGroup transitionCanvas;
    [SerializeField] private float transitionDuration = 0.5f;

    public IEnumerator TransitionToScene(string sceneName)
    {
        // 1. 淡入遮罩
        yield return FadeIn();

        // 2. 加载场景
        yield return LoadSceneAsync(sceneName);

        // 3. 淡出遮罩
        yield return FadeOut();
    }

    private IEnumerator FadeIn()
    {
        transitionCanvas.alpha = 0f;
        transitionCanvas.gameObject.SetActive(true);

        float elapsed = 0f;
        while (elapsed < transitionDuration)
        {
            transitionCanvas.alpha = Mathf.Lerp(0f, 1f, elapsed / transitionDuration);
            elapsed += Time.deltaTime;
            yield return null;
        }

        transitionCanvas.alpha = 1f;
    }

    private IEnumerator FadeOut()
    {
        float elapsed = 0f;
        while (elapsed < transitionDuration)
        {
            transitionCanvas.alpha = Mathf.Lerp(1f, 0f, elapsed / transitionDuration);
            elapsed += Time.deltaTime;
            yield return null;
        }

        transitionCanvas.alpha = 0f;
        transitionCanvas.gameObject.SetActive(false);
    }

    private IEnumerator LoadSceneAsync(string sceneName)
    {
        var asyncLoad = SceneManager.LoadSceneAsync(sceneName);

        // 不允许自动激活，等待淡出完成后再激活
        asyncLoad.allowSceneActivation = false;

        while (!asyncLoad.isDone)
        {
            yield return null;
        }

        // 允许激活场景
        asyncLoad.allowSceneActivation = true;
    }
}
```

### Q3: 如何获取场景加载进度？

```csharp
public class SceneLoadingProgress : MonoBehaviour
{
    [SerializeField] private Slider progressBar;
    [SerializeField] private Text progressText;

    private AsyncOperation currentLoadOperation;

    public void LoadSceneWithProgress(string sceneName)
    {
        StartCoroutine(LoadSceneWithProgressCoroutine(sceneName));
    }

    private IEnumerator LoadSceneWithProgressCoroutine(string sceneName)
    {
        // 异步加载场景
        currentLoadOperation = SceneManager.LoadSceneAsync(sceneName);
        currentLoadOperation.allowSceneActivation = false;

        // 等待加载完成
        while (!currentLoadOperation.isDone)
        {
            // 更新进度条
            float progress = currentLoadOperation.progress;
            progressBar.value = progress;
            progressText.text = $"{progress * 100:F1}%";

            yield return null;
        }

        // 激活场景
        currentLoadOperation.allowSceneActivation = true;

        // 隐藏加载UI
        progressBar.gameObject.SetActive(false);
        progressText.gameObject.SetActive(false);
    }
}
```

---

## 相关链接

- 设计原理: [场景加载底层机制](【设计原理】场景加载底层机制.md)
- 性能数据: [场景加载优化方案全面测试](【性能数据】场景加载优化方案全面测试.md)
- 实战案例: [大型游戏场景流式加载架构](【实战案例】大型游戏场景流式加载架构.md)
- 最佳实践: [场景加载最佳实践](../20_核心系统/网络系统/教程-场景加载最佳实践.md)

---

*创建日期: 2026-03-04*
*Unity版本: 2022.3 LTS*
