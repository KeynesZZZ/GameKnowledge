# Android 专项

> Android平台专项优化与注意事项

## 概述

Android平台碎片化严重，需要特别注意兼容性。

## 分辨率适配

```csharp
// 安全区域适配
Rect safeArea = Screen.safeArea;
// 调整UI布局
```

## 性能分级

```csharp
// 根据设备性能调整画质
public enum PerformanceLevel
{
    Low,
    Medium,
    High
}

public PerformanceLevel DetectPerformance()
{
    int processorCount = SystemInfo.processorCount;
    int memory = SystemInfo.systemMemorySize;

    if (processorCount >= 8 && memory >= 6000)
        return PerformanceLevel.High;
    else if (processorCount >= 4 && memory >= 3000)
        return PerformanceLevel.Medium;
    else
        return PerformanceLevel.Low;
}
```

## 注意事项

1. **权限** - 在AndroidManifest.xml中声明
2. **64位** - Google Play要求64位支持
3. **ABI** - 注意arm64-v8a和armeabi-v7a

## 相关链接

- [性能优化](../30_性能优化/)
