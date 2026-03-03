# Zenject 依赖注入

> Zenject/Extenject依赖注入框架指南

## 概述

Zenject（现Extenject）是Unity中最流行的DI框架。

## 基础用法

### 绑定

```csharp
public class GameInstaller : MonoInstaller
{
    public override void InstallBindings()
    {
        // 单例绑定
        Container.Bind<IInventoryService>()
            .To<InventoryService>()
            .AsSingle();

        // MonoBehaviour绑定
        Container.Bind<IPlayerController>()
            .To<PlayerController>()
            .FromComponentInNewPrefab(playerPrefab)
            .AsSingle();
    }
}
```

### 注入

```csharp
public class PlayerController : MonoBehaviour, IPlayerController
{
    [Inject] private IInventoryService inventory;

    private void Start()
    {
        inventory.AddItem("Sword");
    }
}
```

## 最佳实践

1. 优先使用接口绑定
2. 避免循环依赖
3. 使用Installer组织绑定

## 相关链接

- [依赖注入与服务定位器模式](../../学习/01-脚本与架构/依赖注入与服务定位器模式.md)
