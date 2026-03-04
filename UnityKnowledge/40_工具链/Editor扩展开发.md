# Editor扩展开发

> Unity编辑器扩展开发指南

## 概述

Unity编辑器扩展可以大幅提升开发效率，本文介绍常用扩展方式。

## EditorWindow

### 创建自定义窗口

```csharp
public class MyToolWindow : EditorWindow
{
    [MenuItem("Tools/My Tool")]
    public static void ShowWindow()
    {
        GetWindow<MyToolWindow>("My Tool");
    }

    private void OnGUI()
    {
        GUILayout.Label("My Custom Tool", EditorStyles.boldLabel);

        if (GUILayout.Button("Do Something"))
        {
            Debug.Log("Button clicked!");
        }
    }
}
```

## CustomEditor

### 自定义Inspector

```csharp
[CustomEditor(typeof(MyComponent))]
public class MyComponentEditor : Editor
{
    private SerializedProperty speedProp;
    private SerializedProperty nameProp;

    private void OnEnable()
    {
        speedProp = serializedObject.FindProperty("speed");
        nameProp = serializedObject.FindProperty("name");
    }

    public override void OnInspectorGUI()
    {
        serializedObject.Update();

        EditorGUILayout.PropertyField(speedProp);
        EditorGUILayout.PropertyField(nameProp);

        if (GUILayout.Button("Reset"))
        {
            speedProp.floatValue = 1f;
            nameProp.stringValue = "Default";
        }

        serializedObject.ApplyModifiedProperties();
    }
}
```

## PropertyDrawer

### 自定义属性绘制

```csharp
[CustomPropertyDrawer(typeof(RangeAttribute))]
public class RangeDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        var range = attribute as RangeAttribute;
        EditorGUI.Slider(position, property, range.min, range.max, label);
    }
}
```

## Gizmos & Handles

### 场景可视化

```csharp
public class MyGizmos : MonoBehaviour
{
    private void OnDrawGizmos()
    {
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, 1f);
    }

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.green;
        Gizmos.DrawRay(transform.position, transform.forward * 5f);
    }
}
```

## 相关链接

- [编辑器扩展学习路径](../40_工具链/编辑器扩展/教程-编辑器扩展_学习路径.md)
