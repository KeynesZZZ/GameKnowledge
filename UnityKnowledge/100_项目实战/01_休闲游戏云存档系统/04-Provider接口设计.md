# 04-Provider接口设计

> 云存档提供者接口的完整设计与工厂模式实现 `#接口设计` `#工厂模式` `#依赖注入`

## 一、接口架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Provider接口层次                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               ICloudProvider (核心接口)              │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  + SaveAsync(slot, data) : UniTask<SaveResult>      │   │
│  │  + LoadAsync(slot) : UniTask<LoadResult>            │   │
│  │  + DeleteAsync(slot) : UniTask<bool>                │   │
│  │  + GetSlotListAsync() : UniTask<List<SlotInfo>>     │   │
│  │  + IsAvailableAsync() : UniTask<bool>               │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│          ┌───────────────┼───────────────┐                 │
│          │               │               │                 │
│          ▼               ▼               ▼                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ BaseProvider│ │IAuthProvider│ │ICacheProvider│          │
│  │ (抽象基类)  │ │ (认证接口)  │ │ (缓存接口)  │          │
│  └──────┬──────┘ └─────────────┘ └─────────────┘          │
│         │                                                   │
│         ├──────────────┬──────────────┬─────────────┐      │
│         │              │              │             │      │
│         ▼              ▼              ▼             ▼      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Firebase  │  │ WeChat   │  │ Douyin   │  │  Local   │   │
│  │Provider  │  │ Provider │  │ Provider │  │ Provider │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心接口定义

### 2.1 ICloudProvider

```csharp
using System.Collections.Generic;
using Cysharp.Threading.Tasks;

namespace CloudSave.Core
{
    /// <summary>
    /// 云存档提供者核心接口
    /// 所有平台实现必须继承此接口
    /// </summary>
    public interface ICloudProvider
    {
        /// <summary>
        /// 提供者名称（用于日志和调试）
        /// </summary>
        string ProviderName { get; }

        /// <summary>
        /// 保存数据到云端
        /// </summary>
        /// <param name="slot">存档槽位索引</param>
        /// <param name="data">存档数据</param>
        /// <returns>保存结果</returns>
        UniTask<SaveResult> SaveAsync(int slot, CloudSaveData data);

        /// <summary>
        /// 从云端加载数据
        /// </summary>
        /// <param name="slot">存档槽位索引</param>
        /// <returns>加载结果</returns>
        UniTask<LoadResult> LoadAsync(int slot);

        /// <summary>
        /// 删除云端数据
        /// </summary>
        /// <param name="slot">存档槽位索引</param>
        /// <returns>是否成功</returns>
        UniTask<bool> DeleteAsync(int slot);

        /// <summary>
        /// 获取所有存档槽信息
        /// </summary>
        /// <returns>槽位信息列表</returns>
        UniTask<List<SlotInfo>> GetSlotListAsync();

        /// <summary>
        /// 检查服务是否可用
        /// </summary>
        /// <returns>是否可用</returns>
        UniTask<bool> IsAvailableAsync();

        /// <summary>
        /// 初始化提供者
        /// </summary>
        /// <returns>是否初始化成功</returns>
        UniTask<bool> InitializeAsync();
    }
}
```

### 2.2 IAuthProvider

```csharp
namespace CloudSave.Core
{
    /// <summary>
    /// 认证提供者接口
    /// 处理用户登录状态
    /// </summary>
    public interface IAuthProvider
    {
        /// <summary>
        /// 当前用户ID
        /// </summary>
        string CurrentUserId { get; }

        /// <summary>
        /// 是否已登录
        /// </summary>
        bool IsLoggedIn { get; }

        /// <summary>
        /// 登录
        /// </summary>
        UniTask<AuthResult> LoginAsync();

        /// <summary>
        /// 登出
        /// </summary>
        UniTask LogoutAsync();

        /// <summary>
        /// 获取认证令牌
        /// </summary>
        UniTask<string> GetAuthTokenAsync();
    }

    /// <summary>
    /// 认证结果
    /// </summary>
    public class AuthResult
    {
        public bool success;
        public string userId;
        public string errorMessage;
        public AuthProvider provider;

        public static AuthResult Succeeded(string userId, AuthProvider provider)
        {
            return new AuthResult
            {
                success = true,
                userId = userId,
                provider = provider
            };
        }

        public static AuthResult Failed(string error)
        {
            return new AuthResult
            {
                success = false,
                errorMessage = error
            };
        }
    }

    public enum AuthProvider
    {
        WeChat,
        Douyin,
        Firebase,
        Custom
    }
}
```

### 2.3 ICacheProvider

```csharp
namespace CloudSave.Core
{
    /// <summary>
    /// 本地缓存提供者接口
    /// </summary>
    public interface ICacheProvider
    {
        /// <summary>
        /// 保存到本地缓存
        /// </summary>
        bool SaveToLocal(int slot, CloudSaveData data);

        /// <summary>
        /// 从本地缓存加载
        /// </summary>
        CloudSaveData LoadFromLocal(int slot);

        /// <summary>
        /// 删除本地缓存
        /// </summary>
        bool DeleteFromLocal(int slot);

        /// <summary>
        /// 获取本地所有槽位信息
        /// </summary>
        List<SlotInfo> GetLocalSlotList();

        /// <summary>
        /// 清空所有缓存
        /// </summary>
        void ClearAllCache();
    }
}
```

---

## 三、抽象基类

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;
using Cysharp.Threading.Tasks;

namespace CloudSave.Core
{
    /// <summary>
    /// 云存档提供者抽象基类
    /// 提供通用功能实现
    /// </summary>
    public abstract class BaseCloudProvider : ICloudProvider
    {
        protected readonly ICacheProvider cacheProvider;
        protected readonly CloudSaveConfig config;
        protected bool isInitialized;

        public abstract string ProviderName { get; }

        protected BaseCloudProvider(ICacheProvider cacheProvider, CloudSaveConfig config)
        {
            this.cacheProvider = cacheProvider;
            this.config = config;
        }

        /// <summary>
        /// 初始化（子类可重写）
        /// </summary>
        public virtual async UniTask<bool> InitializeAsync()
        {
            if (isInitialized)
            {
                return true;
            }

            isInitialized = true;
            await UniTask.CompletedTask;
            return true;
        }

        /// <summary>
        /// 保存数据（模板方法）
        /// </summary>
        public virtual async UniTask<SaveResult> SaveAsync(int slot, CloudSaveData data)
        {
            // 1. 验证参数
            if (!ValidateSlot(slot))
            {
                return SaveResult.Failed("INVALID_SLOT", $"无效的存档槽位: {slot}");
            }

            if (data == null)
            {
                return SaveResult.Failed("NULL_DATA", "存档数据不能为空");
            }

            // 2. 先保存到本地
            bool localSaved = cacheProvider.SaveToLocal(slot, data);
            if (!localSaved)
            {
                Debug.LogWarning($"本地保存失败: slot={slot}");
            }

            // 3. 尝试同步到云端
            try
            {
                if (await IsAvailableAsync())
                {
                    return await SaveToCloudAsync(slot, data);
                }
                else
                {
                    // 云端不可用，仅本地保存成功
                    return SaveResult.Succeeded(data, false);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"云端保存失败: {e.Message}");
                // 云端失败但本地成功
                return SaveResult.Succeeded(data, false);
            }
        }

        /// <summary>
        /// 加载数据（模板方法）
        /// </summary>
        public virtual async UniTask<LoadResult> LoadAsync(int slot)
        {
            if (!ValidateSlot(slot))
            {
                return LoadResult.Failed("INVALID_SLOT", $"无效的存档槽位: {slot}");
            }

            try
            {
                // 1. 检查云端是否可用
                if (await IsAvailableAsync())
                {
                    // 2. 从云端加载
                    var cloudResult = await LoadFromCloudAsync(slot);

                    if (cloudResult.success)
                    {
                        // 3. 更新本地缓存
                        cacheProvider.SaveToLocal(slot, cloudResult.data);
                        return cloudResult;
                    }
                }

                // 4. 云端不可用或失败，从本地加载
                var localData = cacheProvider.LoadFromLocal(slot);
                if (localData != null)
                {
                    return LoadResult.Succeeded(localData, DataSource.LocalCache);
                }

                return LoadResult.Failed("NO_DATA", $"存档槽位 {slot} 没有数据");
            }
            catch (Exception e)
            {
                Debug.LogError($"加载存档失败: {e.Message}");

                // 尝试从本地恢复
                var localData = cacheProvider.LoadFromLocal(slot);
                if (localData != null)
                {
                    return LoadResult.Succeeded(localData, DataSource.LocalCache);
                }

                return LoadResult.Failed("LOAD_FAILED", e.Message);
            }
        }

        /// <summary>
        /// 删除数据
        /// </summary>
        public virtual async UniTask<bool> DeleteAsync(int slot)
        {
            if (!ValidateSlot(slot))
            {
                return false;
            }

            // 删除本地
            cacheProvider.DeleteFromLocal(slot);

            // 删除云端
            try
            {
                if (await IsAvailableAsync())
                {
                    return await DeleteFromCloudAsync(slot);
                }
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError($"删除云端存档失败: {e.Message}");
                return false;
            }
        }

        /// <summary>
        /// 获取槽位列表
        /// </summary>
        public virtual async UniTask<List<SlotInfo>> GetSlotListAsync()
        {
            var localSlots = cacheProvider.GetLocalSlotList();

            try
            {
                if (await IsAvailableAsync())
                {
                    var cloudSlots = await GetCloudSlotListAsync();

                    // 合并本地和云端信息
                    return MergeSlotInfo(localSlots, cloudSlots);
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"获取云端槽位信息失败: {e.Message}");
            }

            return localSlots;
        }

        /// <summary>
        /// 检查服务是否可用
        /// </summary>
        public abstract UniTask<bool> IsAvailableAsync();

        #region 子类必须实现的抽象方法

        /// <summary>
        /// 保存到云端（子类实现）
        /// </summary>
        protected abstract UniTask<SaveResult> SaveToCloudAsync(int slot, CloudSaveData data);

        /// <summary>
        /// 从云端加载（子类实现）
        /// </summary>
        protected abstract UniTask<LoadResult> LoadFromCloudAsync(int slot);

        /// <summary>
        /// 从云端删除（子类实现）
        /// </summary>
        protected abstract UniTask<bool> DeleteFromCloudAsync(int slot);

        /// <summary>
        /// 获取云端槽位列表（子类实现）
        /// </summary>
        protected abstract UniTask<List<SlotInfo>> GetCloudSlotListAsync();

        #endregion

        #region 辅助方法

        protected bool ValidateSlot(int slot)
        {
            return slot >= 0 && slot < config.maxSlots;
        }

        protected List<SlotInfo> MergeSlotInfo(List<SlotInfo> local, List<SlotInfo> cloud)
        {
            var result = new List<SlotInfo>();
            var cloudDict = new Dictionary<int, SlotInfo>();

            foreach (var slot in cloud)
            {
                cloudDict[slot.slotIndex] = slot;
            }

            for (int i = 0; i < config.maxSlots; i++)
            {
                var localSlot = local.Find(s => s.slotIndex == i);
                var cloudSlot = cloudDict.TryGetValue(i, out var cs) ? cs : null;

                if (localSlot != null && cloudSlot != null)
                {
                    // 两边都有数据，检查是否有冲突
                    var merged = localSlot.Clone();
                    merged.hasConflict = localSlot.timestamp != cloudSlot.timestamp;
                    merged.syncState = merged.hasConflict ? SyncState.Conflict : SyncState.Synced;
                    result.Add(merged);
                }
                else if (localSlot != null)
                {
                    localSlot.syncState = SyncState.PendingSync;
                    result.Add(localSlot);
                }
                else if (cloudSlot != null)
                {
                    cloudSlot.syncState = SyncState.Synced;
                    result.Add(cloudSlot);
                }
                else
                {
                    result.Add(SlotInfo.Empty(i));
                }
            }

            return result;
        }

        #endregion
    }
}
```

---

## 四、工厂模式实现

### 4.1 ProviderFactory

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;
using CloudSave.Platform;

namespace CloudSave.Core
{
    /// <summary>
    /// 云存档提供者工厂
    /// 根据平台自动创建对应的Provider
    /// </summary>
    public class CloudProviderFactory
    {
        private readonly CloudSaveConfig config;
        private readonly ICacheProvider cacheProvider;
        private readonly PlatformInfo platformInfo;

        // 缓存已创建的Provider
        private readonly Dictionary<CloudServiceType, ICloudProvider> providerCache = new();

        public CloudProviderFactory(
            CloudSaveConfig config,
            ICacheProvider cacheProvider,
            PlatformInfo platformInfo)
        {
            this.config = config;
            this.cacheProvider = cacheProvider;
            this.platformInfo = platformInfo;
        }

        /// <summary>
        /// 获取当前平台的Provider
        /// </summary>
        public ICloudProvider GetProvider()
        {
            return GetProvider(platformInfo.cloudService);
        }

        /// <summary>
        /// 获取指定类型的Provider
        /// </summary>
        public ICloudProvider GetProvider(CloudServiceType serviceType)
        {
            if (providerCache.TryGetValue(serviceType, out var cached))
            {
                return cached;
            }

            var provider = CreateProvider(serviceType);
            providerCache[serviceType] = provider;
            return provider;
        }

        private ICloudProvider CreateProvider(CloudServiceType serviceType)
        {
            return serviceType switch
            {
                CloudServiceType.Firebase => CreateFirebaseProvider(),
                CloudServiceType.PlayFab => CreatePlayFabProvider(),
                CloudServiceType.WeChatCloud => CreateWeChatProvider(),
                CloudServiceType.DouyinCloud => CreateDouyinProvider(),
                CloudServiceType.HuaweiAGC => CreateHuaweiProvider(),
                CloudServiceType.REST => CreateRESTProvider(),
                _ => CreateLocalProvider()
            };
        }

        #region 创建方法

        private ICloudProvider CreateFirebaseProvider()
        {
#if !UNITY_WEBGL || UNITY_EDITOR
            return new FirebaseProvider(cacheProvider, config);
#else
            Debug.LogWarning("WebGL不支持Firebase，使用本地Provider");
            return CreateLocalProvider();
#endif
        }

        private ICloudProvider CreatePlayFabProvider()
        {
#if !UNITY_WEBGL || UNITY_EDITOR
            return new PlayFabProvider(cacheProvider, config);
#else
            Debug.LogWarning("WebGL不支持PlayFab，使用本地Provider");
            return CreateLocalProvider();
#endif
        }

        private ICloudProvider CreateWeChatProvider()
        {
#if UNITY_WEBGL && !UNITY_EDITOR
            return new WeChatProvider(cacheProvider, config);
#else
            Debug.LogWarning("编辑器模式不支持微信Provider，使用本地Provider");
            return CreateLocalProvider();
#endif
        }

        private ICloudProvider CreateDouyinProvider()
        {
#if UNITY_WEBGL && !UNITY_EDITOR
            return new DouyinProvider(cacheProvider, config);
#else
            Debug.LogWarning("编辑器模式不支持抖音Provider，使用本地Provider");
            return CreateLocalProvider();
#endif
        }

        private ICloudProvider CreateHuaweiProvider()
        {
#if UNITY_WEBGL && !UNITY_EDITOR
            return new HuaweiProvider(cacheProvider, config);
#else
            return CreateLocalProvider();
#endif
        }

        private ICloudProvider CreateRESTProvider()
        {
            return new RESTProvider(cacheProvider, config);
        }

        private ICloudProvider CreateLocalProvider()
        {
            return new LocalProvider(cacheProvider, config);
        }

        #endregion

        /// <summary>
        /// 清除缓存
        /// </summary>
        public void ClearCache()
        {
            providerCache.Clear();
        }
    }
}
```

### 4.2 Builder模式

```csharp
namespace CloudSave.Core
{
    /// <summary>
    /// CloudSaveManager构建器
    /// 提供流式API配置
    /// </summary>
    public class CloudSaveBuilder
    {
        private CloudSaveConfig config = new CloudSaveConfig();
        private PlatformInfo platformInfo;
        private ICacheProvider cacheProvider;

        public CloudSaveBuilder()
        {
            config = CloudSaveConfig.Default;
        }

        /// <summary>
        /// 设置存档槽数量
        /// </summary>
        public CloudSaveBuilder WithMaxSlots(int maxSlots)
        {
            config.maxSlots = maxSlots;
            return this;
        }

        /// <summary>
        /// 启用自动保存
        /// </summary>
        public CloudSaveBuilder WithAutoSave(float interval = 300f)
        {
            config.enableAutoSave = true;
            config.autoSaveInterval = interval;
            return this;
        }

        /// <summary>
        /// 启用加密
        /// </summary>
        public CloudSaveBuilder WithEncryption(string key)
        {
            config.enableEncryption = true;
            config.EncryptionKey = key;
            return this;
        }

        /// <summary>
        /// 设置平台信息
        /// </summary>
        public CloudSaveBuilder WithPlatform(PlatformInfo info)
        {
            this.platformInfo = info;
            return this;
        }

        /// <summary>
        /// 设置缓存提供者
        /// </summary>
        public CloudSaveBuilder WithCacheProvider(ICacheProvider provider)
        {
            this.cacheProvider = provider;
            return this;
        }

        /// <summary>
        /// 启用调试模式
        /// </summary>
        public CloudSaveBuilder WithDebugMode(bool enabled = true)
        {
            config.enableDebugLog = enabled;
            return this;
        }

        /// <summary>
        /// 构建CloudSaveManager
        /// </summary>
        public CloudSaveManager Build()
        {
            // 使用默认值填充未设置的项
            platformInfo ??= new PlatformInfo
            {
                platform = PlatformType.Unknown,
                cloudService = CloudServiceType.LocalOnly
            };

            cacheProvider ??= new LocalCacheProvider(config);

            var factory = new CloudProviderFactory(config, cacheProvider, platformInfo);

            return new CloudSaveManager(config, factory, cacheProvider);
        }
    }
}
```

---

## 五、依赖注入集成

### 5.1 VContainer集成

```csharp
using VContainer;
using VContainer.Unity;

namespace CloudSave.DI
{
    /// <summary>
    /// 云存档系统VContainer配置
    /// </summary>
    public class CloudSaveInstaller : MonoInstaller
    {
        public CloudSaveConfig config;

        public override void Configure(IContainerBuilder builder)
        {
            // 注册配置
            builder.RegisterInstance(config);

            // 注册核心服务
            builder.Register<PlatformDetector>(Lifetime.Singleton);
            builder.Register<ICacheProvider, LocalCacheProvider>(Lifetime.Singleton);
            builder.Register<CloudProviderFactory>(Lifetime.Singleton);
            builder.Register<CloudSaveManager>(Lifetime.Singleton);

            // 注册接口
            builder.Register<ICloudSaveManager, CloudSaveManager>(Lifetime.Singleton);
        }
    }

    /// <summary>
    /// 使用示例
    /// </summary>
    public class GameLifetimeScope : LifetimeScope
    {
        protected override void Configure(IContainerBuilder builder)
        {
            // 配置云存档
            builder.RegisterInstance(new CloudSaveConfig
            {
                maxSlots = 3,
                enableAutoSave = true,
                autoSaveInterval = 300f,
                enableEncryption = true
            });

            builder.Register<CloudSaveManager>(Lifetime.Singleton);
        }
    }

    /// <summary>
    /// 在游戏中使用
    /// </summary>
    public class GameLoader : MonoBehaviour
    {
        [Inject] private CloudSaveManager saveManager;

        private async void Start()
        {
            var result = await saveManager.LoadAsync(0);
            if (result.success)
            {
                // 加载成功
            }
        }
    }
}
```

### 5.2 Zenject集成

```csharp
using Zenject;

namespace CloudSave.DI
{
    /// <summary>
    /// 云存档系统Zenject安装器
    /// </summary>
    public class CloudSaveInstaller : MonoInstaller
    {
        public CloudSaveConfig config;

        public override void InstallBindings()
        {
            // 绑定配置
            Container.BindInstance(config);

            // 绑定服务
            Container.Bind<PlatformDetector>().AsSingle();
            Container.Bind<ICacheProvider>().To<LocalCacheProvider>().AsSingle();
            Container.Bind<CloudProviderFactory>().AsSingle();
            Container.Bind<CloudSaveManager>().AsSingle();

            // 绑定接口
            Container.Bind<ICloudSaveManager>().To<CloudSaveManager>().AsSingle();
        }
    }
}
```

---

## 六、使用示例

```csharp
using UnityEngine;
using Cysharp.Threading.Tasks;

namespace CloudSave.Examples
{
    /// <summary>
    /// Provider接口使用示例
    /// </summary>
    public class ProviderExample : MonoBehaviour
    {
        private CloudSaveManager saveManager;

        private async void Start()
        {
            // 方式1: 使用Builder构建
            saveManager = new CloudSaveBuilder()
                .WithMaxSlots(3)
                .WithAutoSave(300f)
                .WithEncryption("my-secret-key")
                .WithDebugMode(true)
                .Build();

            // 初始化
            await saveManager.InitializeAsync();

            // 方式2: 直接配置
            var config = new CloudSaveConfig
            {
                maxSlots = 3,
                enableAutoSave = true
            };

            var detector = new PlatformDetector();
            var platformInfo = await detector.InitializeAsync();

            saveManager = new CloudSaveBuilder()
                .WithPlatform(platformInfo)
                .Build();

            await saveManager.InitializeAsync();
        }

        private async UniTaskVoid SaveGame()
        {
            var gameData = new GameSaveData
            {
                level = 10,
                coins = 1000
            };

            var result = await saveManager.SaveAsync(0, gameData);

            if (result.success)
            {
                Debug.Log($"保存成功，已同步: {result.syncedToCloud}");
            }
        }
    }
}
```

---

## 相关链接

- [03-平台检测系统](03-平台检测系统.md)
- [05-海外平台实现](05-海外平台实现.md)
- [06-微信小游戏实现](06-微信小游戏实现.md)
