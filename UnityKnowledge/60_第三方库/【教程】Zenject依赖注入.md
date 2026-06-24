---
title: 【教程】Zenject依赖注入
tags: ["Unity", "第三方库", "Zenject", "教程"]
category: 第三方库
created: "2026-03-05 08:44"
updated: "2026-05-29 00:00"
description: Zenject依赖注入框架教程
unity_version: 2021.3+
status: 待验证
validation: Demo验证
related: ["[[【教程】UniTask异步编程]]", "[[../10_架构设计/【教程】依赖注入与服务定位器]]"]
author: llm
---

# Zenject 依赖注入

> Zenject/Extenject依赖注入框架指南

## 文档定位

Zenject（现Extenject）是Unity中最流行的依赖注入框架。本文档介绍其核心概念（容器、绑定、Installer）、注入方式（构造函数/属性/方法注入）、生命周期管理以及避免循环依赖的最佳实践。

---

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

- [[../10_架构设计/【教程】依赖注入与服务定位器]]
- [[../10_架构设计/【最佳实践】依赖注入使用指南]]
