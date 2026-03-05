---
title: 【踩坑记录】Android常见问题清单
tags: [Unity, 平台适配, Android, 踩坑记录]
category: 平台适配
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: Unity Android平台常见问题
unity_version: 2021.3+
---
# Android 常见问题清单

> Android平台开发常见问题与解决方案 `#Android` `#平台适配` `#踩坑记录`

## 设备兼容性

### 分辨率适配

```csharp
public class ResolutionAdapter : MonoBehaviour
{
    [SerializeField] private Canvas canvas;

    private void Start()
    {
        AdaptToScreen();
    }

    private void AdaptToScreen()
    {
        float aspectRatio = (float)Screen.width / Screen.height;

        // 常见比例
        // 16:9 = 1.778 (1920x1080)
        // 18:9 = 2.000 (2160x1080)
        // 19.5:9 = 2.167 (2340x1080)
        // 20:9 = 2.222 (2400x1080)

        if (aspectRatio > 2.0f)
        {
            // 长屏适配
            canvas.scaleFactor = CalculateLongScreenScale(aspectRatio);
        }
    }

    private float CalculateLongScreenScale(float aspectRatio)
    {
        // 根据实际需求调整
        return 1f + (aspectRatio - 1.778f) * 0.1f;
    }
}
```

### 安全区域

```csharp
public class SafeAreaAdapter : MonoBehaviour
{
    [SerializeField] private RectTransform panel;

    private void Start()
    {
        ApplySafeArea();
    }

    private void ApplySafeArea()
    {
        Rect safeArea = Screen.safeArea;

        // 转换为锚点
        Vector2 anchorMin = safeArea.position;
        Vector2 anchorMax = safeArea.position + safeArea.size;

        anchorMin.x /= Screen.width;
        anchorMin.y /= Screen.height;
        anchorMax.x /= Screen.width;
        anchorMax.y /= Screen.height;

        panel.anchorMin = anchorMin;
        panel.anchorMax = anchorMax;
    }
}
```

### 性能分级

```csharp
public class DevicePerformance
{
    public enum Level
    {
        Low,
        Medium,
        High
    }

    public static Level DetectPerformance()
    {
        int cpuCount = SystemInfo.processorCount;
        int memoryMB = SystemInfo.systemMemorySize;
        string gpu = SystemInfo.graphicsDeviceName.ToLower();

        // 高端设备
        if (cpuCount >= 8 && memoryMB >= 6000)
        {
            if (gpu.Contains("adreno 650") ||
                gpu.Contains("mali-g77") ||
                gpu.Contains("mali-g78"))
            {
                return Level.High;
            }
        }

        // 中端设备
        if (cpuCount >= 6 && memoryMB >= 4000)
        {
            return Level.Medium;
        }

        return Level.Low;
    }

    public static void ApplyQualitySettings(Level level)
    {
        switch (level)
        {
            case Level.High:
                QualitySettings.SetQualityLevel(5);
                Application.targetFrameRate = 60;
                break;
            case Level.Medium:
                QualitySettings.SetQualityLevel(3);
                Application.targetFrameRate = 60;
                break;
            case Level.Low:
                QualitySettings.SetQualityLevel(1);
                Application.targetFrameRate = 30;
                break;
        }
    }
}
```

---

## 系统集成

### AndroidManifest配置

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.company.game">

    <!-- 权限 -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <!-- 可选权限 -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <!-- 特性 -->
    <uses-feature android:glEsVersion="0x00030000" android:required="true" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/app_icon"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/app_icon_round"
        android:supportsRtl="true">

        <activity android:name="com.unity3d.player.UnityPlayerActivity"
            android:configChanges="mcc|mnc|locale|touchscreen|keyboard|keyboardHidden|navigation|orientation|screenLayout|uiMode|screenSize|smallestScreenSize|fontScale|layoutDirection|density"
            android:hardwareAccelerated="true"
            android:launchMode="singleTask"
            android:screenOrientation="portrait">

            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

    </application>
</manifest>
```

### 运行时权限

```csharp
#if UNITY_ANDROID
using UnityEngine.Android;
#endif

public class AndroidPermissionHandler : MonoBehaviour
{
    public void RequestStoragePermission()
    {
#if UNITY_ANDROID
        if (!Permission.HasUserAuthorizedPermission(Permission.ExternalStorageWrite))
        {
            Permission.RequestUserPermission(Permission.ExternalStorageWrite);
        }
#endif
    }

    public void RequestCameraPermission()
    {
#if UNITY_ANDROID
        if (!Permission.HasUserAuthorizedPermission(Permission.Camera))
        {
            Permission.RequestUserPermission(Permission.Camera);
        }
#endif
    }

    private void Update()
    {
#if UNITY_ANDROID
        // 检查权限结果
        if (Permission.HasUserAuthorizedPermission(Permission.ExternalStorageWrite))
        {
            // 权限已授予
        }
#endif
    }
}
```

---

## 输入处理

### 返回键

```csharp
public class BackButtonHandler : MonoBehaviour
{
    private bool canExit;

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            HandleBackButton();
        }
    }

    private void HandleBackButton()
    {
        if (UIManager.Instance.HasOpenPopup())
        {
            UIManager.Instance.CloseTopPopup();
        }
        else if (UIManager.Instance.CurrentScreen != ScreenType.Main)
        {
            UIManager.Instance.GoBack();
        }
        else
        {
            HandleExit();
        }
    }

    private void HandleExit()
    {
        if (canExit)
        {
            QuitGame();
        }
        else
        {
            canExit = true;
            Toast.Show("再按一次退出游戏");
            StartCoroutine(ResetExitFlag());
        }
    }

    private IEnumerator ResetExitFlag()
    {
        yield return new WaitForSeconds(2f);
        canExit = false;
    }

    private void QuitGame()
    {
#if UNITY_ANDROID
        // Android上不要使用Application.Quit()
        // 使用移动到后台
        AndroidJavaClass activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
        AndroidJavaObject currentActivity = activity.GetStatic<AndroidJavaObject>("currentActivity");
        currentActivity.Call<bool>("moveTaskToBack", true);
#else
        Application.Quit();
#endif
    }
}
```

### 触屏与鼠标

```csharp
public class InputAdapter : MonoBehaviour
{
    public bool IsTouchDevice => Input.touchSupported && Input.touchCount > 0;

    public Vector2 GetInputPosition()
    {
        if (IsTouchDevice)
        {
            return Input.GetTouch(0).position;
        }
        return Input.mousePosition;
    }

    public bool GetInputDown()
    {
        if (IsTouchDevice)
        {
            return Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Began;
        }
        return Input.GetMouseButtonDown(0);
    }

    public bool GetInputUp()
    {
        if (IsTouchDevice)
        {
            return Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Ended;
        }
        return Input.GetMouseButtonUp(0);
    }
}
```

---

## 存储

### 文件路径

```csharp
public class AndroidStorage
{
    // 应用私有存储（卸载清除）
    public static string InternalPath => Application.persistentDataPath;

    // 外部存储（需要权限）
    public static string ExternalPath
    {
        get
        {
#if UNITY_ANDROID
            using (AndroidJavaClass jc = new AndroidJavaClass("android.os.Environment"))
            {
                string path = jc.CallStatic<string>("getExternalStorageDirectory");
                return System.IO.Path.Combine(path, "MyGame");
            }
#else
            return Application.persistentDataPath;
#endif
        }
    }

    // 缓存目录（系统可能清理）
    public static string CachePath => Application.temporaryCachePath;
}
```

### SharedPreferences

```csharp
public class AndroidPrefs
{
#if UNITY_ANDROID
    private static AndroidJavaObject GetPreferences()
    {
        using (AndroidJavaClass unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using (AndroidJavaObject currentActivity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
        {
            return currentActivity.Call<AndroidJavaObject>("getSharedPreferences", "GamePrefs", 0);
        }
    }

    public static void SetString(string key, string value)
    {
        using (var prefs = GetPreferences())
        using (var editor = prefs.Call<AndroidJavaObject>("edit"))
        {
            editor.Call<AndroidJavaObject>("putString", key, value);
            editor.Call<bool>("apply");
        }
    }

    public static string GetString(string key, string defaultValue = "")
    {
        using (var prefs = GetPreferences())
        {
            return prefs.Call<string>("getString", key, defaultValue);
        }
    }
#endif
}
```

---

## 网络

### 网络状态

```csharp
public class AndroidNetworkStatus
{
    public enum NetworkType
    {
        None,
        WiFi,
        Mobile,
        Other
    }

#if UNITY_ANDROID
    public static NetworkType GetNetworkType()
    {
        using (AndroidJavaClass unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
        using (AndroidJavaObject currentActivity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity"))
        using (AndroidJavaObject connectivityManager = currentActivity.Call<AndroidJavaObject>("getSystemService", "connectivity"))
        using (AndroidJavaObject networkInfo = connectivityManager.Call<AndroidJavaObject>("getActiveNetworkInfo"))
        {
            if (networkInfo == null || !networkInfo.Call<bool>("isConnected"))
            {
                return NetworkType.None;
            }

            int type = networkInfo.Call<int>("getType");
            // TYPE_WIFI = 1, TYPE_MOBILE = 0
            if (type == 1) return NetworkType.WiFi;
            if (type == 0) return NetworkType.Mobile;
            return NetworkType.Other;
        }
    }
#endif
}
```

---

## 常见问题

### 黑屏/白屏

```csharp
// 1. 检查OpenGL ES版本
// PlayerSettings > Other Settings > Graphics APIs
// 确保OpenGLES3在列表中

// 2. 检查启动图配置
// PlayerSettings > Splash Image

// 3. 检查首场景是否过大
```

### 启动慢

```csharp
// 优化方案：
// 1. 减少首场景资源
// 2. 使用空场景+加载场景
// 3. 延迟初始化

// Splash Screen后快速显示
[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSplashScreen)]
static void BeforeSplash()
{
    // 预加载关键资源
}
```

### 发热严重

```csharp
// 1. 限制帧率
Application.targetFrameRate = 30;

// 2. 降低画质
QualitySettings.SetQualityLevel(1);

// 3. 减少物理更新
Time.fixedDeltaTime = 0.02f;  // 50Hz

// 4. 使用OnDemandRendering
OnDemandRendering.renderFrameInterval = 2;
```

### 安装失败

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| INSTALL_FAILED_INSUFFICIENT_STORAGE | 存储空间不足 | 提示用户清理空间 |
| INSTALL_FAILED_VERSION_DOWNGRADE | 版本降级 | 增加版本号 |
| INSTALL_PARSE_FAILED_NO_CERTIFICATES | 签名问题 | 重新签名 |
| INSTALL_FAILED_UPDATE_INCOMPATIBLE | 包名冲突 | 卸载旧版本 |

---

## 发布清单

### 构建设置

- [ ] Package Name正确
- [ ] Version Number递增
- [ ] Keystore配置正确
- [ ] Target API Level设置
- [ ] Minimum API Level设置
- [ ] Architecture (ARM64)

### 图标与资源

- [ ] 各密度图标完整
- [ ] 启动图配置
- [ ] 广告图符合要求

### 权限检查

- [ ] 最小权限原则
- [ ] 权限说明文档

### Google Play

- [ ] 内容分级问卷
- [ ] 隐私政策链接
- [ ] 目标受众设置
- [ ] App Bundle格式

---

## 相关链接

- [iOS 专项](iOS%20专项.md)
- [性能优化](../30_性能优化/)
- [官方文档](https://docs.unity3d.com/Manual/android.html)
