# iOS 专项

> iOS平台专项优化与注意事项

## 概述

iOS平台有其特殊的限制和优化要求。

## 内存限制

| 设备 | 内存限制 |
|------|----------|
| iPhone 8 | ~1.5GB |
| iPhone 12 | ~3GB |
| iPhone 14 Pro | ~4GB |

## 性能优化

### 启动时间

```csharp
// 延迟初始化非必要模块
[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
static void DelayedInit()
{
    // 推迟到首帧后初始化
}
```

### 省电优化

- 降低帧率到30fps
- 减少后台活动
- 使用OnDemandRendering

## 注意事项

1. **AOT编译** - 不支持运行时代码生成
2. **App Store审核** - 注意隐私权限声明
3. **签名** - 需要正确的Provisioning Profile

## 相关链接

- [性能优化](../30_性能优化/)
