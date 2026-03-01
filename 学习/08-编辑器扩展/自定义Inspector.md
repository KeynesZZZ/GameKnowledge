# 自定义 Inspector

> 第2课 | 编辑器扩展模块

## 1. CustomEditor 基础

### 1.1 基本用法

```csharp
using UnityEditor;
using UnityEngine;

// 目标组件
public class Player : MonoBehaviour
{
    public string playerName = "Player";
    public int level = 1;
    public float health = 100f;
    public bool isAlive = true;
}

// 自定义 Inspector
[CustomEditor(typeof(Player))]
public class PlayerEditor : Editor
{
    // 获取序列化属性
    private SerializedProperty playerNameProp;
    private SerializedProperty levelProp;
    private SerializedProperty healthProp;
    private SerializedProperty isAliveProp;

    private void OnEnable()
    {
        // 查找属性
        playerNameProp = serializedObject.FindProperty("playerName");
        levelProp = serializedObject.FindProperty("level");
        healthProp = serializedObject.FindProperty("health");
        isAliveProp = serializedObject.FindProperty("isAlive");
    }

    public override void OnInspectorGUI()
    {
        // 更新序列化对象
        serializedObject.Update();

        // 自定义绘制
        EditorGUILayout.PropertyField(playerNameProp, new GUIContent("角色名称"));
        EditorGUILayout.PropertyField(levelProp, new GUIContent("等级"));
        EditorGUILayout.PropertyField(healthProp, new GUIContent("生命值"));
        EditorGUILayout.PropertyField(isAliveProp, new GUIContent("存活"));

        // 应用修改
        serializedObject.ApplyModifiedProperties();
    }
}
```

### 1.2 完全自定义

```csharp
[CustomEditor(typeof(Player))]
public class PlayerEditorFull : Editor
{
    private Player player;

    private void OnEnable()
    {
        player = (Player)target;
    }

    public override void OnInspectorGUI()
    {
        // 不调用 base.OnInspectorGUI()

        EditorGUILayout.LabelField("角色信息", EditorStyles.boldLabel);
        EditorGUILayout.Space(10);

        // 直接访问字段
        player.playerName = EditorGUILayout.TextField("名称", player.playerName);
        player.level = EditorGUILayout.IntSlider("等级", player.level, 1, 100);

        EditorGUILayout.Space(5);

        // 带颜色的生命值
        GUI.color = player.health > 50 ? Color.green : (player.health > 20 ? Color.yellow : Color.red);
        player.health = EditorGUILayout.Slider("生命值", player.health, 0, 100);
        GUI.color = Color.white;

        // 进度条显示
        Rect progressRect = GUILayoutUtility.GetRect(0, 20);
        EditorGUI.ProgressBar(progressRect, player.health / 100f, $"HP: {player.health:F0}/100");

        EditorGUILayout.Space(10);

        // 按钮
        if (GUILayout.Button("重置生命值"))
        {
            Undo.RecordObject(player, "Reset Health");
            player.health = 100;
            EditorUtility.SetDirty(player);
        }

        // 警告信息
        if (player.health <= 0)
        {
            EditorGUILayout.HelpBox("角色已死亡!", MessageType.Error);
        }
    }
}
```

---

## 2. PropertyDrawer

### 2.1 自定义属性绘制器

```csharp
using UnityEngine;

// 自定义类型
[System.Serializable]
public class RangeInt
{
    public int min;
    public int max;

    public RangeInt(int min, int max)
    {
        this.min = min;
        this.max = max;
    }
}

// 属性绘制器
[CustomPropertyDrawer(typeof(RangeInt))]
public class RangeIntDrawer : PropertyDrawer
{
    public override void OnGUI(Rect position, SerializedProperty property, GUIContent label)
    {
        // 开始属性
        EditorGUI.BeginProperty(position, label, property);

        // 查找子属性
        var minProp = property.FindPropertyRelative("min");
        var maxProp = property.FindPropertyRelative("max");

        // 计算布局
        float labelWidth = EditorGUIUtility.labelWidth;
        float fieldWidth = (position.width - labelWidth) / 2 - 5;

        // 绘制标签
        position = EditorGUI.PrefixLabel(position, GUIUtility.GetControlID(FocusType.Passive), label);

        // 绘制两个字段
        int indent = EditorGUI.indentLevel;
        EditorGUI.indentLevel = 0;

        // Min 字段
        Rect minRect = new Rect(position.x, position.y, fieldWidth, position.height);
        EditorGUIUtility.labelWidth = 30;
        minProp.intValue = EditorGUI.IntField(minRect, "Min", minProp.intValue);

        // Max 字段
        Rect maxRect = new Rect(position.x + fieldWidth + 10, position.y, fieldWidth, position.height);
        maxProp.intValue = EditorGUI.IntField(maxRect, "Max", maxProp.intValue);

        EditorGUI.indentLevel = indent;
        EditorGUIUtility.labelWidth = labelWidth;

        // 验证范围
        if (minProp.intValue > maxProp.intValue)
            minProp.intValue = maxProp.intValue;

        EditorGUI.EndProperty();
    }
}
```

### 2.2 使用自定义属性

```csharp
public class Weapon : MonoBehaviour
{
    public RangeInt damageRange;  // 使用自定义绘制器
    public RangeInt durabilityRange;

    // Inspector 会自动使用 RangeIntDrawer
}
```

---

## 3. DecoratorDrawer

### 3.1 自定义装饰器

```csharp
using UnityEngine;

// 自定义属性
[AttributeUsage(AttributeTargets.Field, AllowMultiple = true)]
public class SectionHeaderAttribute : PropertyAttribute
{
    public string Header { get; }
    public Color Color { get; set; } = Color.white;

    public SectionHeaderAttribute(string header)
    {
        Header = header;
    }
}

// 装饰器绘制器
[CustomPropertyDrawer(typeof(SectionHeaderAttribute))]
public class SectionHeaderDrawer : DecoratorDrawer
{
    public override void OnGUI(Rect position)
    {
        var attr = (SectionHeaderAttribute)attribute;

        // 绘制分隔线
        position.y += 5;
        EditorGUI.DrawRect(new Rect(position.x, position.y, position.width, 2), attr.Color);
        position.y += 5;

        // 绘制标题
        GUIStyle style = new GUIStyle(EditorStyles.boldLabel)
        {
            normal = { textColor = attr.Color }
        };
        EditorGUI.LabelField(position, attr.Header, style);
    }

    public override float GetHeight()
    {
        return 30f;
    }
}
```

### 3.2 使用装饰器

```csharp
public class Character : MonoBehaviour
{
    [SectionHeader("基础属性", Color = Color.cyan)]
    public string name;
    public int level;

    [SectionHeader("战斗属性", Color = Color.red)]
    public float attack;
    public float defense;

    [SectionHeader("生命属性", Color = Color.green)]
    public float health;
    public float mana;
}
```

---

## 4. 高级技巧

### 4.1 条件显示

```csharp
[CustomEditor(typeof(Enemy))]
public class EnemyEditor : Editor
{
    private Enemy enemy;

    public override void OnInspectorGUI()
    {
        enemy = (Enemy)target;

        // 基础属性
        enemy.enemyType = (EnemyType)EditorGUILayout.EnumPopup("类型", enemy.enemyType);

        EditorGUILayout.Space(10);

        // 根据类型显示不同选项
        switch (enemy.enemyType)
        {
            case EnemyType.Melee:
                DrawMeleeOptions();
                break;

            case EnemyType.Ranged:
                DrawRangedOptions();
                break;

            case EnemyType.Magic:
                DrawMagicOptions();
                break;
        }
    }

    private void DrawMeleeOptions()
    {
        EditorGUILayout.LabelField("近战设置", EditorStyles.boldLabel);
        enemy.attackRange = EditorGUILayout.FloatField("攻击范围", enemy.attackRange);
        enemy.attackSpeed = EditorGUILayout.FloatField("攻击速度", enemy.attackSpeed);
    }

    private void DrawRangedOptions()
    {
        EditorGUILayout.LabelField("远程设置", EditorStyles.boldLabel);
        enemy.projectilePrefab = (GameObject)EditorGUILayout.ObjectField(
            "投射物", enemy.projectilePrefab, typeof(GameObject), false
        );
        enemy.projectileSpeed = EditorGUILayout.FloatField("投射速度", enemy.projectileSpeed);
    }

    private void DrawMagicOptions()
    {
        EditorGUILayout.LabelField("魔法设置", EditorStyles.boldLabel);
        enemy.manaCost = EditorGUILayout.FloatField("法力消耗", enemy.manaCost);
        enemy.spellType = (SpellType)EditorGUILayout.EnumPopup("法术类型", enemy.spellType);
    }
}
```

### 4.2 只读模式

```csharp
[CustomEditor(typeof(ReadOnlyExample))]
public class ReadOnlyEditor : Editor
{
    private bool isReadOnly = false;

    public override void OnInspectorGUI()
    {
        // 只读开关
        isReadOnly = EditorGUILayout.Toggle("只读模式", isReadOnly);

        EditorGUILayout.Space(5);

        EditorGUI.BeginDisabledGroup(isReadOnly);
        {
            base.OnInspectorGUI();
        }
        EditorGUI.EndDisabledGroup();

        // 或者只读特定字段
        EditorGUI.BeginDisabledGroup(true);
        EditorGUILayout.TextField("ID", System.Guid.NewGuid().ToString());
        EditorGUI.EndDisabledGroup();
    }
}
```

### 4.3 预览区域

```csharp
[CustomEditor(typeof(PreviewObject))]
[CanEditMultipleObjects]
public class PreviewObjectEditor : Editor
{
    private PreviewObject obj;
    private Texture2D previewTexture;

    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();

        EditorGUILayout.Space(10);

        // 预览区域
        Rect previewRect = GUILayoutUtility.GetRect(200, 200, GUILayout.ExpandWidth(true));

        if (previewTexture != null)
        {
            EditorGUI.DrawPreviewTexture(previewRect, previewTexture);
        }
        else
        {
            EditorGUI.DrawRect(previewRect, new Color(0.2f, 0.2f, 0.2f));
            GUIStyle centeredStyle = new GUIStyle(EditorStyles.label) { alignment = TextAnchor.MiddleCenter };
            EditorGUI.LabelField(previewRect, "无预览", centeredStyle);
        }
    }

    // 自定义资源预览（在 Project 窗口）
    public override Texture2D RenderStaticPreview(string assetPath, Object[] subAssets, int width, int height)
    {
        // 返回自定义预览图
        return base.RenderStaticPreview(assetPath, subAssets, width, height);
    }
}
```

---

## 5. 多对象编辑

### 5.1 CanEditMultipleObjects

```csharp
[CustomEditor(typeof(MultiTarget))]
[CanEditMultipleObjects]  // 支持多选
public class MultiTargetEditor : Editor
{
    private SerializedProperty valueProp;

    private void OnEnable()
    {
        valueProp = serializedObject.FindProperty("value");
    }

    public override void OnInspectorGUI()
    {
        serializedObject.Update();

        EditorGUILayout.PropertyField(valueProp);

        // 显示混合值指示
        if (valueProp.hasMultipleDifferentValues)
        {
            EditorGUILayout.HelpBox("选中的对象有不同的值", MessageType.Info);
        }

        serializedObject.ApplyModifiedProperties();
    }
}
```

---

## 本课小结

### Editor vs PropertyDrawer

| 特性 | Editor | PropertyDrawer |
|------|--------|----------------|
| 作用范围 | 整个组件 | 单个属性 |
| 继承 | Editor | PropertyDrawer |
| 用途 | 组件 Inspector | 自定义类型显示 |

### 常用 EditorGUI 方法

| 方法 | 用途 |
|------|------|
| TextField | 文本输入 |
| IntField/FloatField | 数字输入 |
| Toggle | 开关 |
| Popup | 下拉选择 |
| ObjectField | 对象选择 |
| ColorField | 颜色选择 |
| ProgressBar | 进度条 |
| HelpBox | 帮助信息 |

---

## 延伸阅读

- [CustomEditor 官方文档](https://docs.unity3d.com/ScriptReference/CustomEditor.html)
- [PropertyDrawer 官方文档](https://docs.unity3d.com/ScriptReference/PropertyDrawer.html)
