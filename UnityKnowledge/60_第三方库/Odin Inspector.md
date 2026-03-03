# Odin Inspector

> Odin Inspector编辑器增强指南

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
