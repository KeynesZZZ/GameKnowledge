---
title: 【教程】Odin Inspector
tags: [Unity, 第三方库, Odin, 教程]
category: 第三方库
created: 2026-03-05 08:44
updated: 2026-03-05 08:44
description: Odin Inspector编辑器扩展教程
unity_version: 2021.3+
---
# Odin Inspector

> Odin Inspector编辑器增强指南

## 文档定位

本文档从**使用角度**讲解Odin Inspector。

**相关文档**：[[【教程】Odin Inspector]]

---

## 概述

Odin Inspector大幅增强Unity Inspector功能。

## 常用特性

```csharp
public class Example : MonoBehaviour
{
    [Title("Basic Settings")]
    [LabelText("Player Name")]
    public string playerName;

    [Range(0, 100)]
    [OnValueChanged("OnSpeedChanged")]
    public float speed;

    [FoldoutGroup("Advanced")]
    [ShowIf("showAdvanced")]
    public string advancedSetting;

    [Button("Reset")]
    private void ResetValues()
    {
        speed = 10f;
    }

    [AssetsOnly]
    public GameObject prefab;

    [SceneObjectsOnly]
    public Transform target;

    private void OnSpeedChanged()
    {
        Debug.Log($"Speed changed to {speed}");
    }
}
```

## 自定义绘制

```csharp
[DrawWithUnity]
public Vector3 customVector;

[HideLabel]
[TextArea(5, 10)]
public string description;
```

## 相关链接

- [编辑器扩展](../40_工具链/Editor扩展开发.md)
