---
title: 【教程】EditorWindow开发
tags: [Unity, 工具链, EditorWindow, 教程]
category: 工具链
created: 2026-03-05 08:42
updated: 2026-03-05 08:42
description: Unity EditorWindow开发教程
unity_version: 2021.3+
---
# EditorWindow 开发

> 第1课 | 编辑器扩展模块

## 文档定位

本文档从**使用角度**讲解EditorWindow开发。

**相关文档**：[[../../40_工具链/【教程】Editor扩展开发]]、

---

## 1. 基础 EditorWindow

### 1.1 创建窗口

```csharp
using UnityEditor;
using UnityEngine;

public class MyWindow : EditorWindow
{
    // 菜单项
    [MenuItem("Tools/My Window")]
    public static void Open()
    {
        // 获取或创建窗口
        var window = GetWindow<MyWindow>();
        window.titleContent = new GUIContent("我的窗口");
        window.minSize = new Vector2(300, 200);
        window.Show();
    }

    // 绘制 GUI
    private void OnGUI()
    {
        GUILayout.Label("Hello, EditorWindow!", EditorStyles.boldLabel);

        if (GUILayout.Button("Click Me"))
        {
            Debug.Log("Button clicked!");
        }
    }
}
```

### 1.2 常用属性

```csharp
public class WindowProperties : EditorWindow
{
    private string windowTitle = "自定义窗口";
    private Vector2 minWindowSize = new Vector2(400, 300);
    private Vector2 maxWindowSize = new Vector2(800, 600);

    [MenuItem("Tools/Window Properties")]
    public static void Open()
    {
        var window = GetWindow<WindowProperties>();
        window.titleContent = new GUIContent(window.windowTitle);
        window.minSize = window.minWindowSize;
        window.maxSize = window.maxWindowSize;
        window.position = new Rect(100, 100, 500, 400);
        window.Show();
    }
}
```

---

## 2. GUI 控件

### 2.1 基础控件

```csharp
public class BasicControlsWindow : EditorWindow
{
    private string textField = "";
    private int intValue = 0;
    private float floatValue = 0.5f;
    private bool toggleValue = false;
    private int selectedOption = 0;
    private readonly string[] options = { "Option A", "Option B", "Option C" };

    private void OnGUI()
    {
        // 标签
        GUILayout.Label("基础控件演示", EditorStyles.boldLabel);

        // 文本框
        textField = EditorGUILayout.TextField("文本", textField);

        // 数字输入
        intValue = EditorGUILayout.IntField("整数", intValue);
        floatValue = EditorGUILayout.FloatField("浮点数", floatValue);
        floatValue = EditorGUILayout.Slider("滑块", floatValue, 0f, 1f);

        // 开关
        toggleValue = EditorGUILayout.Toggle("开关", toggleValue);

        // 下拉选择
        selectedOption = EditorGUILayout.Popup("选项", selectedOption, options);

        // 按钮
        EditorGUILayout.Space(10);

        if (GUILayout.Button("普通按钮", GUILayout.Height(30)))
        {
            Debug.Log("按钮被点击");
        }

        // 带颜色的按钮
        GUI.backgroundColor = Color.green;
        if (GUILayout.Button("绿色按钮"))
        {
            Debug.Log("绿色按钮");
        }
        GUI.backgroundColor = Color.white;  // 重置

        // 帮助框
        EditorGUILayout.HelpBox("这是一个帮助信息", MessageType.Info);
    }
}
```

### 2.2 布局

```csharp
private void OnGUI()
{
    // 水平布局
    EditorGUILayout.BeginHorizontal();
    {
        GUILayout.Button("左");
        GUILayout.Button("中");
        GUILayout.Button("右");
    }
    EditorGUILayout.EndHorizontal();

    EditorGUILayout.Space(10);

    // 垂直布局
    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
    {
        GUILayout.Label("垂直布局区域");
        GUILayout.Button("按钮 1");
        GUILayout.Button("按钮 2");
    }
    EditorGUILayout.EndVertical();

    EditorGUILayout.Space(10);

    // 滚动视图
    _scrollPosition = EditorGUILayout.BeginScrollView(_scrollPosition);
    {
        for (int i = 0; i < 50; i++)
        {
            GUILayout.Label($"Item {i}");
        }
    }
    EditorGUILayout.EndScrollView();
}
```

### 2.3 对象选择器

```csharp
public class ObjectSelectorWindow : EditorWindow
{
    private GameObject selectedObject;
    private Material selectedMaterial;
    private Texture2D selectedTexture;

    private void OnGUI()
    {
        // GameObject 选择
        selectedObject = (GameObject)EditorGUILayout.ObjectField(
            "GameObject",
            selectedObject,
            typeof(GameObject),
            true
        );

        // Material 选择
        selectedMaterial = (Material)EditorGUILayout.ObjectField(
            "Material",
            selectedMaterial,
            typeof(Material),
            false  // 不允许场景对象
        );

        // Texture 选择
        selectedTexture = (Texture2D)EditorGUILayout.ObjectField(
            "Texture",
            selectedTexture,
            typeof(Texture2D),
            false
        );
    }
}
```

---

## 3. 数据持久化

### 3.1 EditorPrefs

```csharp
public class PersistentWindow : EditorWindow
{
    private string savedText = "";
    private int savedInt = 0;

    private const string KEY_TEXT = "MyWindow_SavedText";
    private const string KEY_INT = "MyWindow_SavedInt";

    [MenuItem("Tools/Persistent Window")]
    public static void Open()
    {
        GetWindow<PersistentWindow>().Show();
    }

    private void OnEnable()
    {
        // 加载保存的数据
        savedText = EditorPrefs.GetString(KEY_TEXT, "");
        savedInt = EditorPrefs.GetInt(KEY_INT, 0);
    }

    private void OnDisable()
    {
        // 保存数据
        EditorPrefs.SetString(KEY_TEXT, savedText);
        EditorPrefs.SetInt(KEY_INT, savedInt);
    }

    private void OnGUI()
    {
        savedText = EditorGUILayout.TextField("文本", savedText);
        savedInt = EditorGUILayout.IntField("整数", savedInt);

        if (GUILayout.Button("重置"))
        {
            savedText = "";
            savedInt = 0;
            EditorPrefs.DeleteKey(KEY_TEXT);
            EditorPrefs.DeleteKey(KEY_INT);
        }
    }
}
```

### 3.2 ScriptableObject 配置

```csharp
// 配置文件
[CreateAssetMenu(fileName = "WindowConfig", menuName = "Config/WindowConfig")]
public class WindowConfig : ScriptableObject
{
    public string defaultText = "Hello";
    public int maxCount = 100;
    public Color themeColor = Color.blue;
}

// 窗口使用配置
public class ConfigurableWindow : EditorWindow
{
    private WindowConfig config;

    [MenuItem("Tools/Configurable Window")]
    public static void Open()
    {
        GetWindow<ConfigurableWindow>().Show();
    }

    private void OnGUI()
    {
        config = (WindowConfig)EditorGUILayout.ObjectField(
            "配置",
            config,
            typeof(WindowConfig),
            false
        );

        if (config != null)
        {
            EditorGUILayout.LabelField("默认文本:", config.defaultText);
            EditorGUILayout.IntField("最大数量:", config.maxCount);
            EditorGUILayout.ColorField("主题颜色:", config.themeColor);
        }
    }
}
```

---

## 4. 实用工具示例

### 4.1 批量重命名工具

```csharp
public class BatchRenamer : EditorWindow
{
    private string prefix = "";
    private string suffix = "";
    private string find = "";
    private string replace = "";
    private int startNumber = 1;

    [MenuItem("Tools/Batch Renamer")]
    public static void Open()
    {
        GetWindow<BatchRenamer>("批量重命名").Show();
    }

    private void OnGUI()
    {
        GUILayout.Label("批量重命名工具", EditorStyles.boldLabel);
        EditorGUILayout.Space(10);

        prefix = EditorGUILayout.TextField("前缀", prefix);
        suffix = EditorGUILayout.TextField("后缀", suffix);
        find = EditorGUILayout.TextField("查找", find);
        replace = EditorGUILayout.TextField("替换", replace);
        startNumber = EditorGUILayout.IntField("起始编号", startNumber);

        EditorGUILayout.Space(10);

        // 显示选中的对象
        GUILayout.Label($"选中对象: {Selection.gameObjects.Length} 个");

        EditorGUILayout.Space(10);

        GUI.enabled = Selection.gameObjects.Length > 0;

        if (GUILayout.Button("重命名", GUILayout.Height(30)))
        {
            RenameSelected();
        }

        GUI.enabled = true;
    }

    private void RenameSelected()
    {
        var objects = Selection.gameObjects;
        Undo.RecordObjects(objects, "Batch Rename");

        for (int i = 0; i < objects.Length; i++)
        {
            string newName = objects[i].name;

            if (!string.IsNullOrEmpty(find))
                newName = newName.Replace(find, replace);

            newName = prefix + newName + suffix;

            if (startNumber > 0)
                newName += (startNumber + i).ToString("D3");

            objects[i].name = newName;
        }

        AssetDatabase.SaveAssets();
    }
}
```

### 4.2 快速创建工具

```csharp
public class QuickCreator : EditorWindow
{
    [MenuItem("Tools/Quick Creator")]
    public static void Open()
    {
        GetWindow<QuickCreator>("快速创建").Show();
    }

    private void OnGUI()
    {
        GUILayout.Label("快速创建常用对象", EditorStyles.boldLabel);
        EditorGUILayout.Space(10);

        EditorGUILayout.BeginHorizontal();
        {
            if (GUILayout.Button("空对象", GUILayout.Height(40)))
                CreateEmptyObject();

            if (GUILayout.Button("UI Canvas", GUILayout.Height(40)))
                CreateUICanvas();

            if (GUILayout.Button("摄像机", GUILayout.Height(40)))
                CreateCamera();
        }
        EditorGUILayout.EndHorizontal();

        EditorGUILayout.BeginHorizontal();
        {
            if (GUILayout.Button("光源", GUILayout.Height(40)))
                CreateLight();

            if (GUILayout.Button("触发器", GUILayout.Height(40)))
                CreateTrigger();

            if (GUILayout.Button("音频源", GUILayout.Height(40)))
                CreateAudioSource();
        }
        EditorGUILayout.EndHorizontal();
    }

    private void CreateEmptyObject()
    {
        var go = new GameObject("New Object");
        Undo.RegisterCreatedObjectUndo(go, "Create Empty");
        Selection.activeGameObject = go;
    }

    private void CreateUICanvas()
    {
        var canvas = new GameObject("Canvas");
        canvas.AddComponent<Canvas>();
        canvas.AddComponent<UnityEngine.UI.CanvasScaler>();
        canvas.AddComponent<UnityEngine.UI.GraphicRaycaster>();
        Undo.RegisterCreatedObjectUndo(canvas, "Create Canvas");
        Selection.activeGameObject = canvas;
    }

    // ... 其他创建方法
}
```

---

## 5. 自动刷新

### 5.1 定时刷新

```csharp
public class AutoRefreshWindow : EditorWindow
{
    private float refreshInterval = 1f;
    private double lastRefreshTime;
    private bool autoRefresh = false;

    [MenuItem("Tools/Auto Refresh")]
    public static void Open()
    {
        GetWindow<AutoRefreshWindow>("自动刷新").Show();
    }

    private void OnGUI()
    {
        autoRefresh = EditorGUILayout.Toggle("自动刷新", autoRefresh);
        refreshInterval = EditorGUILayout.Slider("刷新间隔(秒)", refreshInterval, 0.1f, 5f);

        EditorGUILayout.Space(10);

        if (autoRefresh)
        {
            // 请求定时重绘
            wantsMouseEnterLeaveWindow = true;

            if (EditorApplication.timeSinceStartup - lastRefreshTime > refreshInterval)
            {
                lastRefreshTime = EditorApplication.timeSinceStartup;
                Refresh();
            }

            // 持续重绘
            Repaint();
        }
    }

    private void Refresh()
    {
        // 执行刷新逻辑
        Debug.Log($"刷新于 {System.DateTime.Now:HH:mm:ss}");
    }
}
```

---

## 本课小结

### EditorWindow 生命周期

| 方法 | 调用时机 |
|------|----------|
| OnEnable | 窗口打开时 |
| OnDisable | 窗口关闭时 |
| OnDestroy | 窗口销毁时 |
| OnGUI | 每帧绘制 |
| OnFocus | 获得焦点 |
| OnLostFocus | 失去焦点 |
| OnHierarchyChange | Hierarchy 变化 |
| OnProjectChange | Project 变化 |
| OnSelectionChange | 选择变化 |

### 常用 EditorGUILayout 方法

| 方法 | 用途 |
|------|------|
| TextField | 文本输入 |
| IntField/FloatField | 数字输入 |
| Toggle | 开关 |
| Popup | 下拉选择 |
| ObjectField | 对象选择 |
| Slider | 滑块 |
| ColorField | 颜色选择 |
| Foldout | 折叠面板 |

---

## 相关链接

- [EditorWindow 官方文档](https://docs.unity3d.com/ScriptReference/EditorWindow.html)
- [EditorGUILayout 官方文档](https://docs.unity3d.com/ScriptReference/EditorGUILayout.html)
