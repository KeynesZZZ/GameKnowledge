---
title: 【踩坑记录】iOS常见问题清单
tags: [Unity, 平台适配, iOS, 踩坑记录]
category: 平台适配
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: Unity iOS平台常见问题
unity_version: 2021.3+
---
# iOS 常见问题清单

> iOS平台开发常见问题与解决方案 `#iOS` `#平台适配` `#踩坑记录`

## 文档定位

本文档从**问题解决角度**记录iOS常见问题清单的常见问题和解决方案。

**相关文档**：[[【踩坑记录】iOS常见问题清单]]

---

## 内存管理

### 内存限制

| 设备 | 内存限制 | 建议 |
|------|----------|------|
| iPhone 8 | ~1.5GB | 预留200MB |
| iPhone X | ~3GB | 预留300MB |
| iPhone 12+ | ~4GB | 预留400MB |

### 内存警告处理

```csharp
public class IOSMemoryHandler : MonoBehaviour
{
    private void Awake()
    {
        Application.lowMemory += OnLowMemory;
    }

    private void OnLowMemory()
    {
        Debug.Log("iOS Memory Warning!");

        // 1. 清理缓存
        Resources.UnloadUnusedAssets();

        // 2. 释放对象池
        ObjectPoolManager.Instance.ClearAll();

        // 3. 卸载未使用资源
        Addressables.ClearResourceCache();

        // 4. GC回收
        GC.Collect();
    }

    private void OnDestroy()
    {
        Application.lowMemory -= OnLowMemory;
    }
}
```

### 常见内存问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 启动崩溃 | 首场景资源过大 | 分帧加载 |
| 运行崩溃 | 内存泄漏 | 使用Memory Profiler |
| 后台崩溃 | 内存不足被杀 | 释放资源进入后台 |

---

## 性能优化

### 启动时间

```csharp
// iOS要求启动时间 < 20秒

// ✅ 延迟初始化
[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
static void DelayedInit()
{
    // 非关键初始化延迟到首帧后
}

// ✅ 分帧加载
async UniTaskVoid LoadAssetsAsync()
{
    foreach (var asset in assets)
    {
        await LoadAssetAsync(asset);
        await UniTask.Yield();  // 分帧
    }
}
```

### 省电优化

```csharp
// 降低帧率
Application.targetFrameRate = 30;

// 使用OnDemandRendering（Unity 2020+）
using UnityEngine.Rendering;

public class PowerSaver : MonoBehaviour
{
    private void Start()
    {
        // 非交互时降低渲染频率
        OnDemandRendering.renderFrameInterval = 2;  // 每2帧渲染1次
    }

    public void OnUserInteraction()
    {
        OnDemandRendering.renderFrameInterval = 1;  // 恢复正常
    }
}
```

---

## 系统集成

### Info.plist配置

```xml
<!-- 必需的权限声明 -->
<key>NSCameraUsageDescription</key>
<string>需要相机权限用于拍照功能</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>需要相册权限用于保存图片</string>

<key>NSMicrophoneUsageDescription</key>
<string>需要麦克风权限用于录音功能</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>需要位置信息用于附近功能</string>

<!-- 网络配置 -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>

<!-- 后台模式 -->
<key>UIBackgroundModes</key>
<array>
    <string>audio</string>
    <string>remote-notification</string>
</array>
```

### 代码配置

```csharp
// PlayerSettings设置
// File > Build Settings > Player Settings > iOS

// 运行时检查
#if UNITY_IOS
void CheckIOSVersion()
{
    string version = UnityEngine.iOS.Device.systemVersion;
    Debug.Log($"iOS Version: {version}");
}
#endif
```

---

## 输入处理

### 触屏事件

```csharp
public class TouchHandler : MonoBehaviour
{
    private void Update()
    {
        if (Input.touchCount > 0)
        {
            Touch touch = Input.GetTouch(0);

            switch (touch.phase)
            {
                case TouchPhase.Began:
                    OnTouchBegan(touch.position);
                    break;
                case TouchPhase.Moved:
                    OnTouchMoved(touch.position);
                    break;
                case TouchPhase.Ended:
                    OnTouchEnded(touch.position);
                    break;
            }
        }
    }

    private void OnTouchBegan(Vector2 position) { }
    private void OnTouchMoved(Vector2 position) { }
    private void OnTouchEnded(Vector2 position) { }
}
```

### 手势识别

```csharp
public class GestureHandler : MonoBehaviour
{
    [SerializeField] private float pinchScale = 0.5f;
    [SerializeField] private float swipeThreshold = 100f;

    private Vector2 touchStartPos;

    // 捏合
    public void OnPinch(float delta)
    {
        Camera.main.orthographicSize -= delta * pinchScale;
    }

    // 滑动
    public void OnSwipe(Vector2 delta)
    {
        if (delta.magnitude > swipeThreshold)
        {
            if (Mathf.Abs(delta.x) > Mathf.Abs(delta.y))
            {
                // 水平滑动
                if (delta.x > 0) OnSwipeRight();
                else OnSwipeLeft();
            }
            else
            {
                // 垂直滑动
                if (delta.y > 0) OnSwipeUp();
                else OnSwipeDown();
            }
        }
    }
}
```

---

## 音频

### 后台播放

```csharp
// 1. Info.plist添加
// <key>UIBackgroundModes</key>
// <array><string>audio</string></array>

// 2. 代码设置
public class BackgroundAudio : MonoBehaviour
{
    private void Start()
    {
        AudioSettings.iOSSpeakerMode = iOSSpeakerMode.ForceSpeaker;
    }
}
```

### 音频格式

| 格式 | 建议 |
|------|------|
| BGM | AAC/MP3 (压缩) |
| 音效 | WAV/CAF (无损) |
| 语音 | AAC |

---

## 网络

### 网络状态

```csharp
public class NetworkStatus : MonoBehaviour
{
    private void Update()
    {
        switch (Application.internetReachability)
        {
            case NetworkReachability.NotReachable:
                OnNetworkLost();
                break;
            case NetworkReachability.ReachableViaCarrierDataNetwork:
                OnMobileNetwork();
                break;
            case NetworkReachability.ReachableViaLocalAreaNetwork:
                OnWiFiNetwork();
                break;
        }
    }
}
```

### HTTPS配置

```csharp
// iOS 9+要求ATS (App Transport Security)
// 默认要求HTTPS

// 允许HTTP（开发环境）
// Info.plist:
// <key>NSAppTransportSecurity</key>
// <dict>
//     <key>NSAllowsArbitraryLoads</key>
//     <true/>
// </dict>

// 生产环境应使用HTTPS
```

---

## 存储

### 文件路径

```csharp
public class IOSStorage
{
    // 持久化存储路径
    public static string PersistentPath => Application.persistentDataPath;

    // 临时缓存路径
    public static string CachePath => Application.temporaryCachePath;

    // iOS Documents目录（会被iCloud备份）
    public static string DocumentsPath
    {
        get
        {
#if UNITY_IOS
            return System.IO.Path.Combine(
                System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments),
                "Documents"
            );
#else
            return PersistentPath;
#endif
        }
    }

    // 不备份的目录
    public static string NoBackupPath
    {
        get
        {
            var path = System.IO.Path.Combine(PersistentPath, "NoBackup");
            if (!System.IO.Directory.Exists(path))
            {
                System.IO.Directory.CreateDirectory(path);
            }
            return path;
        }
    }
}
```

### iCloud

```csharp
// 避免iCloud备份大文件
// 使用 "do not backup" 标记

#if UNITY_IOS
[DllImport("__Internal")]
private static extern void SetSkipBackupFlag(string path);

public static void MarkAsNoBackup(string filePath)
{
    SetSkipBackupFlag(filePath);
}
#endif
```

---

## 常见崩溃

### 崩溃类型

| 崩溃 | 原因 | 解决方案 |
|------|------|----------|
| 0x8badf00d | 启动超时 | 优化启动流程 |
| 0xdead10cc | 后台占用资源 | 进入后台释放资源 |
| 0xc00010ff | 内存不足 | 减少内存占用 |
| Exception | C#异常 | 添加try-catch |

### 调试技巧

```csharp
// 捕获未处理异常
private void Awake()
{
    Application.logMessageReceived += OnLogMessage;
}

private void OnLogMessage(string condition, string stackTrace, LogType type)
{
    if (type == LogType.Exception)
    {
        // 上报错误
        AnalyticsManager.ReportError(condition, stackTrace);
    }
}
```

---

## 审核注意事项

### 必查清单

- [ ] Info.plist权限描述完整
- [ ] 隐私政策链接有效
- [ ] 内购使用IAP
- [ ] 登录使用Sign in with Apple（如有第三方登录）
- [ ] 无废弃API警告
- [ ] 64位支持
- [ ] 启动图符合要求
- [ ] App图标符合要求

### 常见拒审原因

1. **功能问题** - 崩溃、卡顿、功能不完整
2. **设计问题** - 违反HIG、UI不友好
3. **隐私问题** - 权限说明不清、数据收集不透明
4. **内购问题** - 绕过IAP、价格显示不清

---

## 相关链接

- [Android 专项](【最佳实践】Android专项.md)
- [性能优化](../30_性能优化/)
- [官方文档](https://docs.unity3d.com/Manual/ios.html)
