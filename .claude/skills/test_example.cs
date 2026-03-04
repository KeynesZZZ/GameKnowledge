using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// 测试文件 - 包含多个违反规则的代码
/// 用于演示规则检查SKILL
/// </summary>
public class PlayerController : MonoBehaviour
{
    // 违反 RULE-ARCH-006: 使用public字段暴露
    public float maxHealth = 100f;
    public float speed = 5f;

    private Rigidbody rb;
    private List<Enemy> enemies = new();
    private int score = 0;

    private void Start()
    {
        // 违反 RULE-ARCH-004: 在Start中使用GameObject.Find（虽然不是Update，但展示问题）
        var player = GameObject.Find("Player");
    }

    // 违反 RULE-GC-001: Update中字符串拼接
    // 违反 RULE-GC-003: Update中new集合
    // 违反 RULE-GC-004: Update中GetComponent
    // 违反 RULE-SAFE-003: Update中可能抛异常
    private void Update()
    {
        // CRITICAL: Update中new集合
        var items = new List<int>();

        // HIGH: Update中字符串拼接
        string info = "Score: " + score + " Health: " + maxHealth;

        // HIGH: Update中GetComponent
        var rigidbody = GetComponent<Rigidbody>();

        // CRITICAL: Update中可能抛异常
        if (enemies.Count > 0)
        {
            enemies[0].Attack();
        }
    }

    // 违反 RULE-MEM-001: 事件订阅但可能忘记取消
    private void OnEnable()
    {
        EventBus.Subscribe<PlayerEvent>(OnPlayerEvent);
    }

    private void OnPlayerEvent(PlayerEvent e)
    {
        Debug.Log("Player event received");
    }

    // 缺少配对的 OnDisable 取消订阅
}

// 事件类
public class PlayerEvent { }

// 事件总线（简化版）
public static class EventBus
{
    public static void Subscribe<T>(System.Action<T> handler) { }
    public static void Unsubscribe<T>(System.Action<T> handler) { }
}

// 敌人类
public class Enemy
{
    public void Attack() { }
}
