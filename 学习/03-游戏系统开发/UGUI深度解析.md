# UGUI深度解析

> 专题课程 | UI系统进阶

## 1. UGUI渲染机制

### 1.1 渲染架构

```
┌─────────────────────────────────────────────────────────────┐
│                    UGUI 渲染架构                              │
│                                                             │
│   Canvas                                                    │
│     │                                                       │
│     ├── CanvasRenderer (每个UI元素)                          │
│     │     ├── 网格生成                                       │
│     │     └── 材质设置                                       │
│     │                                                       │
│     ├── Graphic (基类)                                       │
│     │     ├── Image                                         │
│     │     ├── Text                                          │
│     │     └── RawImage                                      │
│     │                                                       │
│     └── 批处理规则                                           │
│           ├── 相同材质                                       │
│           ├── 相同纹理（图集）                                │
│           └── 层级连续                                       │
│                                                             │
│   渲染流程:                                                  │
│   Update() → Rebuild() → BatchBuild() → Draw()              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Canvas渲染模式详解

```csharp
using UnityEngine;

/// <summary>
/// Canvas渲染模式分析
/// </summary>
public class CanvasModeAnalysis : MonoBehaviour
{
    [Header("Overlay模式")]
    [SerializeField] private Canvas overlayCanvas;

    [Header("Camera模式")]
    [SerializeField] private Canvas cameraCanvas;
    [SerializeField] private Camera uiCamera;

    [Header("World模式")]
    [SerializeField] private Canvas worldCanvas;

    /*
    ========== Screen Space - Overlay ==========
    特点：
    - 渲染在场景最上层，不受相机影响
    - 直接渲染到屏幕
    - 适合：HUD、固定UI

    性能：
    - 最快的渲染模式
    - 不需要相机渲染
    - DrawCall合并效率最高

    ========== Screen Space - Camera ==========
    特点：
    - 相对于相机渲染
    - 可设置Plane Distance产生透视效果
    - 适合：需要3D效果的UI

    性能：
    - 需要额外相机
    - 可与场景物体产生遮挡关系

    ========== World Space ==========
    特点：
    - 作为3D物体存在于场景中
    - 可被遮挡、有深度
    - 适合：血条、对话框、物品标签

    性能：
    - 与场景物体一起渲染
    - 每个Canvas独立批处理
    */
}
```

### 1.3 批处理规则

```csharp
/// <summary>
/// UGUI批处理优化
/// </summary>
public static class UGUIBatchOptimizer
{
    /*
    ========== 合批条件 ==========

    1. 相同材质
       - 使用相同的Shader
       - 使用相同的材质属性

    2. 相同纹理（图集）
       - 同一Sprite Atlas
       - 纹理格式一致

    3. 层级连续
       - 中间没有其他材质的UI元素
       - 正确的Hierarchy顺序

    ========== 打断合批的因素 ==========

    1. 不同材质/纹理
    2. 不同的渲染层
    3. 遮罩（RectMask2D/Mask）
    4. 文字（每个字体纹理可能不同）
    5. 材质属性修改（颜色、透明度）
    */

    /// <summary>
    /// 分析Canvas的DrawCall
    /// </summary>
    public static void AnalyzeDrawCalls(Canvas canvas)
    {
        var graphics = canvas.GetComponentsInChildren<Graphic>(true);
        var batches = new List<BatchInfo>();

        BatchInfo currentBatch = null;

        foreach (var graphic in graphics)
        {
            if (!graphic.gameObject.activeInHierarchy) continue;

            var material = graphic.material;
            var texture = graphic.mainTexture;

            // 检查是否可以合并
            bool canBatch = currentBatch != null &&
                           currentBatch.Material == material &&
                           currentBatch.Texture == texture;

            if (!canBatch)
            {
                currentBatch = new BatchInfo
                {
                    Material = material,
                    Texture = texture,
                    Graphics = new List<Graphic>()
                };
                batches.Add(currentBatch);
            }

            currentBatch.Graphics.Add(graphic);
        }

        // 输出分析结果
        Debug.Log($"Canvas: {canvas.name}");
        Debug.Log($"Total DrawCalls: {batches.Count}");

        for (int i = 0; i < batches.Count; i++)
        {
            var batch = batches[i];
            Debug.Log($"Batch {i}: {batch.Graphics.Count} elements, " +
                     $"Texture: {batch.Texture?.name ?? "null"}");
        }
    }

    private class BatchInfo
    {
        public Material Material;
        public Texture Texture;
        public List<Graphic> Graphics;
    }

    /// <summary>
    /// 优化UI层级顺序
    /// </summary>
    public static void OptimizeHierarchyOrder(Transform parent)
    {
        var graphics = new List<Graphic>();

        foreach (Transform child in parent)
        {
            var graphic = child.GetComponent<Graphic>();
            if (graphic != null)
                graphics.Add(graphic);
        }

        // 按材质和纹理排序
        graphics.Sort((a, b) =>
        {
            int materialCompare = a.material.GetInstanceID().CompareTo(b.material.GetInstanceID());
            if (materialCompare != 0) return materialCompare;

            int textureCompare = (a.mainTexture?.GetInstanceID() ?? 0)
                .CompareTo(b.mainTexture?.GetInstanceID() ?? 0);
            return textureCompare;
        });

        // 重新排序
        for (int i = 0; i < graphics.Count; i++)
        {
            graphics[i].transform.SetSiblingIndex(i);
        }
    }
}
```

---

## 2. 事件系统

### 2.1 事件系统架构

```csharp
using UnityEngine;
using UnityEngine.EventSystems;
using System.Collections.Generic;

/// <summary>
/// UGUI事件系统详解
/// </summary>
public class EventSystemGuide : MonoBehaviour
{
    /*
    ========== 事件系统组件 ==========

    EventSystem
    ├── 管理输入事件
    ├── 处理射线检测
    └── 维护当前选中对象

    StandaloneInputModule
    ├── 处理鼠标/触摸输入
    ├── 处理键盘导航
    └── 处理控制器输入

    ========== 射线检测器 ==========

    GraphicRaycaster (Canvas)
    ├── 检测UI元素
    └── 只对Canvas内的Graphic有效

    PhysicsRaycaster (3D)
    ├── 检测3D物体
    └── 需要物体有Collider

    Physics2DRaycaster (2D)
    ├── 检测2D物体
    └── 需要物体有Collider2D
    */

    /// <summary>
    /// 自定义事件监听器
    /// </summary>
    public class CustomUIEventListener :
        MonoBehaviour,
        IPointerClickHandler,
        IPointerDownHandler,
        IPointerUpHandler,
        IPointerEnterHandler,
        IPointerExitHandler,
        IBeginDragHandler,
        IDragHandler,
        IEndDragHandler,
        IScrollHandler,
        ISelectHandler,
        IDeselectHandler
    {
        public System.Action<PointerEventData> OnClickEvent;
        public System.Action<PointerEventData> OnDownEvent;
        public System.Action<PointerEventData> OnUpEvent;
        public System.Action<PointerEventData> OnEnterEvent;
        public System.Action<PointerEventData> OnExitEvent;
        public System.Action<PointerEventData> OnBeginDragEvent;
        public System.Action<PointerEventData> OnDragEvent;
        public System.Action<PointerEventData> OnEndDragEvent;
        public System.Action<PointerEventData> OnScrollEvent;
        public System.Action<BaseEventData> OnSelectEvent;
        public System.Action<BaseEventData> OnDeselectEvent;

        public static CustomUIEventListener Get(GameObject go)
        {
            var listener = go.GetComponent<CustomUIEventListener>();
            if (listener == null)
                listener = go.AddComponent<CustomUIEventListener>();
            return listener;
        }

        public void OnPointerClick(PointerEventData eventData) => OnClickEvent?.Invoke(eventData);
        public void OnPointerDown(PointerEventData eventData) => OnDownEvent?.Invoke(eventData);
        public void OnPointerUp(PointerEventData eventData) => OnUpEvent?.Invoke(eventData);
        public void OnPointerEnter(PointerEventData eventData) => OnEnterEvent?.Invoke(eventData);
        public void OnPointerExit(PointerEventData eventData) => OnExitEvent?.Invoke(eventData);
        public void OnBeginDrag(PointerEventData eventData) => OnBeginDragEvent?.Invoke(eventData);
        public void OnDrag(PointerEventData eventData) => OnDragEvent?.Invoke(eventData);
        public void OnEndDrag(PointerEventData eventData) => OnEndDragEvent?.Invoke(eventData);
        public void OnScroll(PointerEventData eventData) => OnScrollEvent?.Invoke(eventData);
        public void OnSelect(BaseEventData eventData) => OnSelectEvent?.Invoke(eventData);
        public void OnDeselect(BaseEventData eventData) => OnDeselectEvent?.Invoke(eventData);
    }
}
```

### 2.2 射线检测优化

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

/// <summary>
/// 射线检测优化
/// </summary>
public static class RaycastOptimizer
{
    /*
    ========== Raycast Target优化 ==========

    原则：只对需要交互的UI元素开启Raycast Target

    需要开启的：
    - Button
    - Toggle
    - 滑动区域
    - 可点击的Image

    不需要开启的：
    - 纯显示的Image
    - 纯显示的Text
    - 装饰性元素
    - 背景图
    */

    /// <summary>
    /// 批量设置Raycast Target
    /// </summary>
    public static void SetRaycastTargetRecursive(GameObject root, bool enabled)
    {
        var graphics = root.GetComponentsInChildren<Graphic>(true);
        foreach (var graphic in graphics)
        {
            // 只有在有交互组件时才开启
            var hasInteractable = graphic.GetComponent<IPointerClickHandler>() != null ||
                                 graphic.GetComponent<IPointerDownHandler>() != null ||
                                 graphic.GetComponent<IPointerUpHandler>() != null ||
                                 graphic.GetComponent<IDragHandler>() != null;

            graphic.raycastTarget = enabled && hasInteractable;
        }
    }

    /// <summary>
    /// 统计Raycast Target数量
    /// </summary>
    public static int CountRaycastTargets(Canvas canvas)
    {
        int count = 0;
        var graphics = canvas.GetComponentsInChildren<Graphic>(true);

        foreach (var graphic in graphics)
        {
            if (graphic.raycastTarget)
                count++;
        }

        return count;
    }

    /// <summary>
    /// 输出所有Raycast Target
    /// </summary>
    public static void LogRaycastTargets(Canvas canvas)
    {
        var graphics = canvas.GetComponentsInChildren<Graphic>(true);
        int count = 0;

        foreach (var graphic in graphics)
        {
            if (graphic.raycastTarget)
            {
                Debug.Log($"Raycast Target: {graphic.gameObject.name}", graphic.gameObject);
                count++;
            }
        }

        Debug.Log($"Total Raycast Targets: {count}");
    }
}

/// <summary>
/// 自定义GraphicRaycaster优化版
/// </summary>
public class OptimizedGraphicRaycaster : GraphicRaycaster
{
    [Header("Optimization")]
    [SerializeField] private bool ignoreReversedGraphics = true;
    [SerializeField] private bool blockAllOnFirstHit = false;

    // 缓存
    private List<Graphic> m_RaycastResults = new List<Graphic>();

    public override void Raycast(PointerEventData eventData, List<RaycastResult> resultAppendList)
    {
        if (canvas == null) return;

        var eventCamera = eventData.pressEventCamera;
        if (eventCamera == null && canvas.renderMode != RenderMode.ScreenSpaceOverlay)
            return;

        // 获取射线
        Vector2 localPoint;
        if (!GetLocalPoint(eventData, out localPoint)) return;

        // 检测
        m_RaycastResults.Clear();
        Raycast(canvas, eventCamera, localPoint, m_RaycastResults);

        // 转换结果
        foreach (var graphic in m_RaycastResults)
        {
            if (blockAllOnFirstHit && resultAppendList.Count > 0)
                break;

            resultAppendList.Add(new RaycastResult
            {
                gameObject = graphic.gameObject,
                module = this,
                distance = 0,
                index = resultAppendList.Count,
                depth = graphic.depth,
                sortingLayer = canvas.sortingLayerID,
                sortingOrder = canvas.sortingOrder,
                worldPosition = Vector3.zero,
                worldNormal = Vector3.zero
            });
        }
    }

    private bool GetLocalPoint(PointerEventData eventData, out Vector2 localPoint)
    {
        return RectTransformUtility.ScreenPointToLocalPointInRectangle(
            canvas.transform as RectTransform,
            eventData.position,
            eventData.pressEventCamera,
            out localPoint);
    }

    private void Raycast(Canvas canvas, Camera eventCamera, Vector2 pointerPosition, List<Graphic> results)
    {
        var graphics = GraphicRegistry.GetRaycastableGraphicsForCanvas(canvas);

        for (int i = 0; i < graphics.Count; i++)
        {
            var graphic = graphics[i];
            if (graphic.depth == -1 || !graphic.raycastTarget || !graphic.IsActive())
                continue;

            if (!RectTransformUtility.RectangleContainsScreenPoint(
                graphic.rectTransform, pointerPosition, eventCamera))
                continue;

            if (ignoreReversedGraphics && eventCamera != null)
            {
                var dir = graphic.rectTransform.position - eventCamera.transform.position;
                if (Vector3.Dot(dir, eventCamera.transform.forward) <= 0)
                    continue;
            }

            results.Add(graphic);
        }

        results.Sort((g1, g2) => g2.depth.CompareTo(g1.depth));
    }
}
```

---

## 3. 布局系统

### 3.1 布局组件原理

```csharp
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 布局系统详解
/// </summary>
public class LayoutSystemGuide : MonoBehaviour
{
    /*
    ========== 布局组件层级 ==========

    LayoutGroup (基类)
    ├── HorizontalLayoutGroup    水平排列
    ├── VerticalLayoutGroup      垂直排列
    └── GridLayoutGroup          网格排列

    LayoutElement
    └── 覆盖子物体的布局属性

    ContentSizeFitter
    └── 根据子物体调整自身大小

    ScrollRect
    └── 滚动视图容器

    ========== 布局计算流程 ==========

    1. LayoutRebuilder.MarkLayoutForRebuild(rectTransform)
       标记需要重建

    2. LayoutRebuilder.Rebuild()
       执行重建（在Canvas.willRenderCanvases）

    3. 计算顺序：
       - CalcAlongInvisibliAxis (水平/垂直)
       - SetLayoutAlongAxis
       - SetLayoutInput
    */

    /// <summary>
    /// 自定义布局组
    /// </summary>
    public class FlowLayoutGroup : LayoutGroup
    {
        [Header("Flow Layout Settings")]
        [SerializeField] private float spacing = 10f;
        [SerializeField] private float cellWidth = 100f;
        [SerializeField] private float cellHeight = 100f;

        public override void CalculateLayoutInputHorizontal()
        {
            base.CalculateLayoutInputHorizontal();
            CalculateLayout();
        }

        public override void CalculateLayoutInputVertical()
        {
            CalculateLayout();
        }

        public override void SetLayoutHorizontal()
        {
            SetLayout();
        }

        public override void SetLayoutVertical()
        {
            SetLayout();
        }

        private void CalculateLayout()
        {
            int itemCount = rectChildren.Count;
            if (itemCount == 0) return;

            float containerWidth = rectTransform.rect.width - padding.horizontal;
            int cellsPerRow = Mathf.Max(1, Mathf.FloorToInt((containerWidth + spacing) / (cellWidth + spacing)));
            int rows = Mathf.CeilToInt((float)itemCount / cellsPerRow);

            float totalWidth = Mathf.Min(cellsPerRow, itemCount) * cellWidth + (Mathf.Min(cellsPerRow, itemCount) - 1) * spacing;
            float totalHeight = rows * cellHeight + (rows - 1) * spacing;

            SetLayoutInputForAxis(totalWidth + padding.horizontal, totalWidth + padding.horizontal, -1, 0);
            SetLayoutInputForAxis(totalHeight + padding.vertical, totalHeight + padding.vertical, -1, 1);
        }

        private void SetLayout()
        {
            int itemCount = rectChildren.Count;
            if (itemCount == 0) return;

            float containerWidth = rectTransform.rect.width - padding.horizontal;
            int cellsPerRow = Mathf.Max(1, Mathf.FloorToInt((containerWidth + spacing) / (cellWidth + spacing)));

            float startX = padding.left;
            float startY = padding.top;

            for (int i = 0; i < itemCount; i++)
            {
                int row = i / cellsPerRow;
                int col = i % cellsPerRow;

                float x = startX + col * (cellWidth + spacing);
                float y = startY + row * (cellHeight + spacing);

                var child = rectChildren[i];
                SetChildAlongAxis(child, 0, x, cellWidth);
                SetChildAlongAxis(child, 1, y, cellHeight);
            }
        }
    }
}
```

### 3.2 虚拟列表（性能优化）

```csharp
using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

/// <summary>
/// 虚拟列表 - 大数据量优化
/// </summary>
[RequireComponent(typeof(ScrollRect))]
public class VirtualList : MonoBehaviour
{
    [Header("Settings")]
    [SerializeField] private GameObject itemPrefab;
    [SerializeField] private RectTransform content;
    [SerializeField] private float itemHeight = 100f;
    [SerializeField] private float spacing = 10f;
    [SerializeField] private int bufferCount = 2;

    private ScrollRect scrollRect;
    private List<RectTransform> itemPool = new List<RectTransform>();
    private List<object> dataList = new List<object>();

    private int firstVisibleIndex;
    private int lastVisibleIndex;
    private int poolSize;

    public System.Action<int, GameObject, object> OnUpdateItem;

    private void Awake()
    {
        scrollRect = GetComponent<ScrollRect>();
        scrollRect.onValueChanged.AddListener(OnScroll);
    }

    /// <summary>
    /// 设置数据
    /// </summary>
    public void SetData(List<object> data)
    {
        dataList = data;

        // 计算content高度
        float totalHeight = data.Count * itemHeight + (data.Count - 1) * spacing;
        content.sizeDelta = new Vector2(content.sizeDelta.x, totalHeight);

        // 计算需要的池大小
        float viewportHeight = scrollRect.viewport.rect.height;
        poolSize = Mathf.CeilToInt(viewportHeight / (itemHeight + spacing)) + bufferCount * 2;

        // 初始化池
        InitializePool();

        // 初始显示
        UpdateVisibleItems();
    }

    private void InitializePool()
    {
        // 清理旧的
        foreach (var item in itemPool)
        {
            if (item != null)
                Destroy(item.gameObject);
        }
        itemPool.Clear();

        // 创建新的
        for (int i = 0; i < poolSize; i++)
        {
            var go = Instantiate(itemPrefab, content);
            var rect = go.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0, 1);
            rect.anchorMax = new Vector2(1, 1);
            rect.pivot = new Vector2(0.5f, 1);
            rect.sizeDelta = new Vector2(0, itemHeight);
            go.SetActive(false);
            itemPool.Add(rect);
        }
    }

    private void OnScroll(Vector2 position)
    {
        UpdateVisibleItems();
    }

    private void UpdateVisibleItems()
    {
        if (dataList.Count == 0) return;

        float contentY = content.anchoredPosition.y;
        float viewportHeight = scrollRect.viewport.rect.height;

        // 计算可见范围
        firstVisibleIndex = Mathf.FloorToInt(contentY / (itemHeight + spacing));
        lastVisibleIndex = Mathf.CeilToInt((contentY + viewportHeight) / (itemHeight + spacing));

        // 添加缓冲
        firstVisibleIndex = Mathf.Max(0, firstVisibleIndex - bufferCount);
        lastVisibleIndex = Mathf.Min(dataList.Count - 1, lastVisibleIndex + bufferCount);

        // 隐藏所有
        foreach (var item in itemPool)
            item.gameObject.SetActive(false);

        // 显示可见的
        int poolIndex = 0;
        for (int i = firstVisibleIndex; i <= lastVisibleIndex && poolIndex < itemPool.Count; i++)
        {
            var item = itemPool[poolIndex];
            float y = -i * (itemHeight + spacing);
            item.anchoredPosition = new Vector2(0, y);
            item.gameObject.SetActive(true);

            // 更新内容
            OnUpdateItem?.Invoke(i, item.gameObject, dataList[i]);

            poolIndex++;
        }
    }

    /// <summary>
    /// 刷新单个项
    /// </summary>
    public void RefreshItem(int index)
    {
        if (index >= firstVisibleIndex && index <= lastVisibleIndex)
        {
            int poolIndex = index - firstVisibleIndex;
            if (poolIndex >= 0 && poolIndex < itemPool.Count)
            {
                OnUpdateItem?.Invoke(index, itemPool[poolIndex].gameObject, dataList[index]);
            }
        }
    }

    /// <summary>
    /// 滚动到指定项
    /// </summary>
    public void ScrollTo(int index)
    {
        float y = index * (itemHeight + spacing);
        content.anchoredPosition = new Vector2(content.anchoredPosition.x, y);
    }

    private void OnDestroy()
    {
        if (scrollRect != null)
            scrollRect.onValueChanged.RemoveListener(OnScroll);
    }
}

// 使用示例
public class VirtualListExample : MonoBehaviour
{
    [SerializeField] private VirtualList virtualList;

    private void Start()
    {
        // 创建测试数据
        var data = new List<object>();
        for (int i = 0; i < 1000; i++)
        {
            data.Add(new ItemData { Index = i, Name = $"Item {i}" });
        }

        virtualList.OnUpdateItem = OnUpdateItem;
        virtualList.SetData(data);
    }

    private void OnUpdateItem(int index, GameObject item, object data)
    {
        var itemData = (ItemData)data;
        var text = item.GetComponentInChildren<Text>();
        if (text != null)
            text.text = itemData.Name;
    }

    private class ItemData
    {
        public int Index;
        public string Name;
    }
}
```

---

## 4. 遮罩与裁剪

```csharp
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// 遮罩系统详解
/// </summary>
public class MaskSystemGuide : MonoBehaviour
{
    /*
    ========== 遮罩类型 ==========

    1. Mask (Stencil Buffer)
       - 使用模板缓冲区
       - 支持任意形状
       - 打断合批
       - 性能开销较大

    2. RectMask2D (Clipping)
       - 只支持矩形
       - 不打断合批
       - 性能好
       - 适合列表项裁剪

    ========== 选择建议 ==========

    - 矩形裁剪 → RectMask2D
    - 圆形/不规则 → Mask
    - 列表滚动 → RectMask2D
    - 头像圆角 → Mask (或Shader)
    */

    /// <summary>
    /// 圆形遮罩（Shader实现，不打断合批）
    /// </summary>
    public class CircleMask : MonoBehaviour, IMaterialModifier
    {
        [SerializeField] private float radius = 50f;
        [SerializeField] private Vector2 center = new Vector2(0.5f, 0.5f);
        [SerializeField] private bool softEdge = true;
        [SerializeField] private float softness = 5f;

        private Material maskMaterial;
        private static Shader maskShader;

        public Material GetModifiedMaterial(Material baseMaterial)
        {
            if (maskShader == null)
                maskShader = Shader.Find("UI/CircleMask");

            if (maskMaterial == null)
                maskMaterial = new Material(maskShader);

            maskMaterial.SetFloat("_Radius", radius);
            maskMaterial.SetVector("_Center", center);
            maskMaterial.SetFloat("_SoftEdge", softEdge ? 1f : 0f);
            maskMaterial.SetFloat("_Softness", softness);

            return maskMaterial;
        }
    }
}

/*
CircleMask Shader:

Shader "UI/CircleMask"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Radius ("Radius", Float) = 50
        _Center ("Center", Vector) = (0.5, 0.5, 0, 0)
        _SoftEdge ("Soft Edge", Float) = 1
        _Softness ("Softness", Float) = 5
    }

    SubShader
    {
        Tags { "Queue" = "Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            sampler2D _MainTex;
            float _Radius;
            float2 _Center;
            float _SoftEdge;
            float _Softness;

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);

                float2 pixelPos = i.uv * _ScreenParams.xy;
                float2 centerPos = _Center * _ScreenParams.xy;
                float dist = distance(pixelPos, centerPos);

                float alpha = 1;
                if (_SoftEdge > 0.5)
                {
                    alpha = smoothstep(_Radius + _Softness, _Radius - _Softness, dist);
                }
                else
                {
                    alpha = step(dist, _Radius);
                }

                col.a *= alpha;
                return col;
            }
            ENDCG
        }
    }
}
*/
```

---

## 5. 图集与Sprite优化

```csharp
using UnityEngine;
using UnityEngine.U2D;
using UnityEngine.UI;
using System.Collections.Generic;

/// <summary>
/// 图集管理
/// </summary>
public class AtlasManager : MonoBehaviour
{
    /*
    ========== Sprite Atlas ==========

    优点：
    - 自动合并Sprite
    - 减少DrawCall
    - 支持多分辨率
    - 运行时加载

    配置：
    - Include in Build: 是
    - Allow Rotation: 否（避免旋转问题）
    - Tight Packing: 是（节省空间）
    - Padding: 2-4像素（防止 bleeding）
    */

    [Header("Atlases")]
    [SerializeField] private SpriteAtlas uiAtlas;
    [SerializeField] private SpriteAtlas iconAtlas;

    private Dictionary<string, Sprite> spriteCache = new Dictionary<string, Sprite>();

    /// <summary>
    /// 获取Sprite
    /// </summary>
    public Sprite GetSprite(string spriteName)
    {
        if (spriteCache.TryGetValue(spriteName, out var sprite))
            return sprite;

        // 从图集获取
        sprite = uiAtlas.GetSprite(spriteName);
        if (sprite == null)
            sprite = iconAtlas.GetSprite(spriteName);

        if (sprite != null)
            spriteCache[spriteName] = sprite;

        return sprite;
    }

    /// <summary>
    /// 预加载Sprite
    /// </summary>
    public void PreloadSprites(string[] spriteNames)
    {
        foreach (var name in spriteNames)
        {
            GetSprite(name);
        }
    }

    /// <summary>
    /// 清除缓存
    /// </summary>
    public void ClearCache()
    {
        spriteCache.Clear();
        Resources.UnloadUnusedAssets();
    }
}

/// <summary>
/// 动态图集（运行时合并）
/// </summary>
public class DynamicAtlas
{
    private Texture2D atlasTexture;
    private Rect[] uvRects;
    private Dictionary<string, int> spriteIndexMap = new Dictionary<string, int>();
    private int currentIndex = 0;

    public DynamicAtlas(int size)
    {
        atlasTexture = new Texture2D(size, size, TextureFormat.RGBA32, false);
        atlasTexture.filterMode = FilterMode.Bilinear;
        atlasTexture.wrapMode = TextureWrapMode.Clamp;
    }

    /// <summary>
    /// 添加Sprite到动态图集
    /// </summary>
    public bool AddSprite(string name, Texture2D texture)
    {
        if (spriteIndexMap.ContainsKey(name))
            return true;

        // 简化实现，实际需要更复杂的打包算法
        // 这里假设是固定大小的格子
        int cellSize = 64;
        int cellsPerRow = atlasTexture.width / cellSize;

        int x = (currentIndex % cellsPerRow) * cellSize;
        int y = (currentIndex / cellsPerRow) * cellSize;

        if (y + cellSize > atlasTexture.height)
            return false; // 图集已满

        // 复制像素
        Graphics.CopyTexture(texture, 0, 0, 0, 0, texture.width, texture.height,
                           atlasTexture, 0, 0, x, y);

        spriteIndexMap[name] = currentIndex;
        currentIndex++;

        return true;
    }

    public Texture2D GetAtlasTexture() => atlasTexture;

    public Rect GetUVRect(string name)
    {
        if (!spriteIndexMap.TryGetValue(name, out int index))
            return Rect.zero;

        int cellSize = 64;
        int cellsPerRow = atlasTexture.width / cellSize;

        float x = (index % cellsPerRow) * cellSize / (float)atlasTexture.width;
        float y = 1f - ((index / cellsPerRow + 1) * cellSize / (float)atlasTexture.height);
        float w = cellSize / (float)atlasTexture.width;
        float h = cellSize / (float)atlasTexture.height;

        return new Rect(x, y, w, h);
    }
}
```

---

## 6. UGUI性能优化清单

```
┌─────────────────────────────────────────────────────────────┐
│                   UGUI 性能优化清单                           │
│                                                             │
│  1. Canvas优化                                              │
│     ├── 分离动态/静态UI到不同Canvas                          │
│     ├── 避免深层嵌套                                        │
│     └── 使用合适的渲染模式                                   │
│                                                             │
│  2. DrawCall优化                                            │
│     ├── 使用Sprite Atlas                                   │
│     ├── 减少材质数量                                        │
│     ├── 优化层级顺序                                        │
│     └── 避免打断合批（Mask、文字）                           │
│                                                             │
│  3. Raycast优化                                             │
│     ├── 关闭不必要的Raycast Target                          │
│     └── 使用RectMask2D替代Mask                              │
│                                                             │
│  4. 布局优化                                                │
│     ├── 避免过多LayoutGroup嵌套                             │
│     ├── 大列表使用虚拟列表                                   │
│     └── 缓存布局计算结果                                    │
│                                                             │
│  5. 内存优化                                                │
│     ├── 合理使用图集大小                                    │
│     ├── 及时卸载不用的Sprite                                │
│     └── 避免大纹理                                          │
│                                                             │
│  6. 文字优化                                                │
│     ├── 使用TextMeshPro                                    │
│     ├── 限制字体纹理大小                                    │
│     └── 缓存文字网格                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| Canvas渲染 | Overlay/Camera/World模式选择 |
| 批处理 | 相同材质+纹理+连续层级 |
| 事件系统 | IPointerHandler接口族 |
| 射线检测 | 减少Raycast Target |
| 布局系统 | LayoutGroup、虚拟列表 |
| 遮罩 | RectMask2D优先于Mask |
| 图集 | Sprite Atlas、动态图集 |

### 性能优化优先级

```
1. 减少DrawCall（图集、层级）
2. 关闭不必要的Raycast Target
3. 使用虚拟列表处理大数据
4. 分离动态/静态UI
5. 使用RectMask2D替代Mask
6. 使用TextMeshPro
```

---

## 延伸阅读

- [Unity UI Best Practices](https://docs.unity3d.com/Manual/UIBestPracticeGuides.html)
- [UGUI Source Code](https://github.com/Unity-Technologies/uGUI)
- [TextMeshPro](https://docs.unity3d.com/Packages/com.unity.textmeshpro@latest)
