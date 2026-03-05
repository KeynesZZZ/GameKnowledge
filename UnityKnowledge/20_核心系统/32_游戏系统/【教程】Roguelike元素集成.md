---
title: 【教程】Roguelike元素集成
tags: [Unity, 游戏系统, Roguelike, 教程]
category: 核心系统/游戏系统
created: 2026-03-05 08:32
updated: 2026-03-05 08:32
description: Roguelike元素集成教程
unity_version: 2021.3+
---
# Roguelike元素集成

> 第5课 | 游戏系统开发模块

## 文档定位

本文档从**使用角度**讲解Roguelike元素集成。

**相关文档**：

---

## 1. Roguelike核心元素

```
┌─────────────────────────────────────────────────────────────┐
│                    Roguelike 核心元素                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  程序化生成 (Procedural Generation)                   │   │
│  │  ├── 随机地图/关卡                                     │   │
│  │  ├── 随机敌人配置                                      │   │
│  │  └── 随机奖励                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  永久死亡 (Permadeath)                                │   │
│  │  ├── 死亡后重新开始                                    │   │
│  │  └── 保留部分进度（Meta Progression）                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  构建系统 (Build System)                              │   │
│  │  ├── 每局不同的能力组合                                │   │
│  │  ├── 道具/装备系统                                     │   │
│  │  └── 升级选择                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  难度递增 (Scaling Difficulty)                        │   │
│  │  ├── 层数递增                                          │   │
│  │  ├── 敌人变强                                          │   │
│  │  └── Boss战                                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 地下城生成系统

### 2.1 地下城数据结构

```csharp
using System.Collections.Generic;

/// <summary>
/// 地下城房间类型
/// </summary>
public enum RoomType
{
    Normal,     // 普通战斗
    Elite,      // 精英战斗
    Boss,       // Boss战
    Shop,       // 商店
    Event,      // 随机事件
    Treasure,   // 宝藏
    Rest        // 休息点
}

/// <summary>
/// 地下城房间
/// </summary>
public class DungeonRoom
{
    public int Id { get; private set; }
    public int Floor { get; private set; }
    public RoomType Type { get; private set; }
    public List<int> NextRoomIds { get; private set; }
    public bool IsCleared { get; private set; }
    public bool IsAccessible { get; set; }

    // 房间内容
    public List<EnemyData> Enemies { get; private set; }
    public List<RewardData> Rewards { get; private set; }
    public ShopData Shop { get; private set; }
    public EventData Event { get; private set; }

    public DungeonRoom(int id, int floor, RoomType type)
    {
        Id = id;
        Floor = floor;
        Type = type;
        NextRoomIds = new List<int>();
        Enemies = new List<EnemyData>();
        Rewards = new List<RewardData>();
    }

    public void SetCleared()
    {
        IsCleared = true;
    }

    public void AddNextRoom(int roomId)
    {
        if (!NextRoomIds.Contains(roomId))
            NextRoomIds.Add(roomId);
    }
}

/// <summary>
/// 地下城数据
/// </summary>
public class DungeonData
{
    public int Seed { get; private set; }
    public int TotalFloors { get; private set; }
    public Dictionary<int, DungeonRoom> Rooms { get; private set; }
    public int CurrentRoomId { get; private set; }
    public List<int> VisitedRoomIds { get; private set; }

    public DungeonRoom CurrentRoom => Rooms.TryGetValue(CurrentRoomId, out var room) ? room : null;

    public DungeonData(int seed, int totalFloors)
    {
        Seed = seed;
        TotalFloors = totalFloors;
        Rooms = new Dictionary<int, DungeonRoom>();
        VisitedRoomIds = new List<int>();
    }

    public void AddRoom(DungeonRoom room)
    {
        Rooms[room.Id] = room;
    }

    public void SetCurrentRoom(int roomId)
    {
        CurrentRoomId = roomId;
        if (!VisitedRoomIds.Contains(roomId))
            VisitedRoomIds.Add(roomId);
    }

    public List<DungeonRoom> GetAccessibleRooms()
    {
        var accessible = new List<DungeonRoom>();
        var current = CurrentRoom;

        if (current != null)
        {
            foreach (var nextId in current.NextRoomIds)
            {
                if (Rooms.TryGetValue(nextId, out var room))
                    accessible.Add(room);
            }
        }

        return accessible;
    }
}
```

### 2.2 地下城生成器

```csharp
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 地下城生成器
/// </summary>
public class DungeonGenerator
{
    private System.Random random;
    private int nextRoomId = 0;

    [Header("Generation Settings")]
    private int roomsPerFloor = 3;
    private float eliteChance = 0.15f;
    private float shopChance = 0.1f;
    private float eventChance = 0.15f;
    private float treasureChance = 0.1f;
    private float restChance = 0.1f;

    public DungeonGenerator(int seed)
    {
        random = new System.Random(seed);
    }

    /// <summary>
    /// 生成完整地下城
    /// </summary>
    public DungeonData Generate(int totalFloors)
    {
        var dungeon = new DungeonData(random.Next(), totalFloors);

        // 逐层生成
        List<int> previousFloorRooms = new List<int>();

        for (int floor = 1; floor <= totalFloors; floor++)
        {
            var floorRooms = GenerateFloor(dungeon, floor, previousFloorRooms, floor == totalFloors);
            previousFloorRooms = floorRooms;
        }

        // 设置起始房间
        dungeon.SetCurrentRoom(1);

        return dungeon;
    }

    /// <summary>
    /// 生成单层房间
    /// </summary>
    private List<int> GenerateFloor(DungeonData dungeon, int floor, List<int> previousRooms, bool isBossFloor)
    {
        var floorRooms = new List<int>();

        if (floor == 1)
        {
            // 第一层：起始战斗
            var startRoom = CreateRoom(floor, RoomType.Normal);
            dungeon.AddRoom(startRoom);
            floorRooms.Add(startRoom.Id);
        }
        else if (isBossFloor)
        {
            // Boss层
            var bossRoom = CreateRoom(floor, RoomType.Boss);
            dungeon.AddRoom(bossRoom);
            floorRooms.Add(bossRoom.Id);

            // 连接上一层所有房间到Boss
            foreach (var prevId in previousRooms)
            {
                var prevRoom = dungeon.Rooms[prevId];
                prevRoom.AddNextRoom(bossRoom.Id);
            }
        }
        else
        {
            // 普通层
            int roomCount = roomsPerFloor + random.Next(-1, 2); // 2-4个房间

            for (int i = 0; i < roomCount; i++)
            {
                var roomType = DetermineRoomType(floor);
                var room = CreateRoom(floor, roomType);
                PopulateRoom(room, floor);

                dungeon.AddRoom(room);
                floorRooms.Add(room.Id);
            }

            // 连接上一层到这一层
            ConnectRooms(dungeon, previousRooms, floorRooms);
        }

        return floorRooms;
    }

    /// <summary>
    /// 决定房间类型
    /// </summary>
    private RoomType DetermineRoomType(int floor)
    {
        double roll = random.NextDouble();

        // 确保至少有一些普通战斗
        float normalChance = 1f - eliteChance - shopChance - eventChance - treasureChance - restChance;

        if (roll < eliteChance)
            return RoomType.Elite;
        if (roll < eliteChance + shopChance)
            return RoomType.Shop;
        if (roll < eliteChance + shopChance + eventChance)
            return RoomType.Event;
        if (roll < eliteChance + shopChance + eventChance + treasureChance)
            return RoomType.Treasure;
        if (roll < eliteChance + shopChance + eventChance + treasureChance + restChance)
            return RoomType.Rest;

        return RoomType.Normal;
    }

    /// <summary>
    /// 创建房间
    /// </summary>
    private DungeonRoom CreateRoom(int floor, RoomType type)
    {
        return new DungeonRoom(++nextRoomId, floor, type);
    }

    /// <summary>
    /// 填充房间内容
    /// </summary>
    private void PopulateRoom(DungeonRoom room, int floor)
    {
        switch (room.Type)
        {
            case RoomType.Normal:
                AddEnemies(room, floor, 1, 3);
                AddRewards(room, floor, 1);
                break;

            case RoomType.Elite:
                AddEnemies(room, floor, 1, 1, true);
                AddRewards(room, floor, 2);
                break;

            case RoomType.Boss:
                AddBoss(room, floor);
                AddRewards(room, floor, 3);
                break;

            case RoomType.Shop:
                room.Shop = GenerateShop(floor);
                break;

            case RoomType.Event:
                room.Event = GetRandomEvent();
                break;

            case RoomType.Treasure:
                AddRewards(room, floor, 2);
                break;

            case RoomType.Rest:
                // 休息点可以恢复生命值
                break;
        }
    }

    private void AddEnemies(DungeonRoom room, int floor, int minCount, int maxCount, bool isElite = false)
    {
        int count = minCount + random.Next(maxCount - minCount + 1);

        for (int i = 0; i < count; i++)
        {
            var enemy = GenerateEnemy(floor, isElite);
            room.Enemies.Add(enemy);
        }
    }

    private void AddBoss(DungeonRoom room, int floor)
    {
        var boss = GenerateBoss(floor);
        room.Enemies.Add(boss);
    }

    private void AddRewards(DungeonRoom room, int floor, int count)
    {
        for (int i = 0; i < count; i++)
        {
            var reward = GenerateReward(floor);
            room.Rewards.Add(reward);
        }
    }

    /// <summary>
    /// 连接两层房间
    /// </summary>
    private void ConnectRooms(DungeonData dungeon, List<int> upperRooms, List<int> lowerRooms)
    {
        if (upperRooms.Count == 0 || lowerRooms.Count == 0) return;

        // 确保每个上层房间至少连接一个下层房间
        foreach (var upperId in upperRooms)
        {
            int lowerIndex = random.Next(lowerRooms.Count);
            var upperRoom = dungeon.Rooms[upperId];
            upperRoom.AddNextRoom(lowerRooms[lowerIndex]);
        }

        // 确保每个下层房间至少被一个上层房间连接
        foreach (var lowerId in lowerRooms)
        {
            bool hasConnection = false;
            foreach (var upperId in upperRooms)
            {
                var upperRoom = dungeon.Rooms[upperId];
                if (upperRoom.NextRoomIds.Contains(lowerId))
                {
                    hasConnection = true;
                    break;
                }
            }

            if (!hasConnection)
            {
                int upperIndex = random.Next(upperRooms.Count);
                var upperRoom = dungeon.Rooms[upperRooms[upperIndex]];
                upperRoom.AddNextRoom(lowerId);
            }
        }
    }

    // ========== 内容生成 ==========

    private EnemyData GenerateEnemy(int floor, bool isElite)
    {
        float scaling = 1f + (floor - 1) * 0.15f;

        var enemy = new EnemyData
        {
            Id = isElite ? 100 + floor : floor,
            Name = isElite ? $"Elite_{floor}" : $"Enemy_{floor}",
            MaxHP = Mathf.RoundToInt((isElite ? 150 : 50) * scaling),
            Attack = Mathf.RoundToInt((isElite ? 15 : 8) * scaling),
            Defense = Mathf.RoundToInt((isElite ? 8 : 3) * scaling),
            Floor = floor,
            Behavior = isElite ? EnemyBehavior.Aggressive : EnemyBehavior.Random,
            ActionInterval = isElite ? 1 : 2
        };

        return enemy;
    }

    private EnemyData GenerateBoss(int floor)
    {
        float scaling = 1f + (floor - 1) * 0.3f;

        return new EnemyData
        {
            Id = 1000 + floor,
            Name = $"Boss_Floor{floor}",
            MaxHP = Mathf.RoundToInt(500 * scaling),
            Attack = Mathf.RoundToInt(25 * scaling),
            Defense = Mathf.RoundToInt(15 * scaling),
            Floor = floor,
            Behavior = EnemyBehavior.Aggressive,
            ActionInterval = 1
        };
    }

    private RewardData GenerateReward(int floor)
    {
        var reward = new RewardData();

        // 基于层数生成奖励
        int value = 10 + floor * 5 + random.Next(20);

        reward.Type = (RewardType)random.Next(0, 4);
        reward.Value = value;

        return reward;
    }

    private ShopData GenerateShop(int floor)
    {
        var shop = new ShopData
        {
            Items = new List<ShopItemData>()
        };

        // 生成3-5个商品
        int itemCount = 3 + random.Next(3);
        for (int i = 0; i < itemCount; i++)
        {
            shop.Items.Add(new ShopItemData
            {
                ItemId = random.Next(1, 20),
                Price = 50 + floor * 10 + random.Next(50)
            });
        }

        return shop;
    }

    private EventData GetRandomEvent()
    {
        // 随机事件
        return new EventData
        {
            EventId = random.Next(1, 10),
            Title = "神秘事件",
            Description = "你遇到了一个神秘的旅者..."
        };
    }
}

/// <summary>
/// 奖励数据
/// </summary>
public class RewardData
{
    public RewardType Type;
    public int Value;
    public int ItemId;
}

public enum RewardType
{
    Gold,
    Gem,
    Item,
    Card,
    Experience
}

/// <summary>
/// 商店数据
/// </summary>
public class ShopData
{
    public List<ShopItemData> Items;
}

public class ShopItemData
{
    public int ItemId;
    public int Price;
    public bool IsSold;
}

/// <summary>
/// 事件数据
/// </summary>
public class EventData
{
    public int EventId;
    public string Title;
    public string Description;
}
```

---

## 3. 道具与装备系统

### 3.1 道具数据结构

```csharp
using System.Collections.Generic;

/// <summary>
/// 道具类型
/// </summary>
public enum ItemType
{
    Consumable,    // 消耗品
    Equipment,     // 装备
    Passive,       // 被动物品
    Active         // 主动物品
}

/// <summary>
/// 装备槽位
/// </summary>
public enum EquipmentSlot
{
    Weapon,
    Armor,
    Accessory1,
    Accessory2
}

/// <summary>
/// 道具数据
/// </summary>
[System.Serializable]
public class ItemData
{
    public int Id;
    public string Name;
    public string Description;
    public ItemType Type;
    public int Rarity;  // 1-5稀有度
    public Sprite Icon;

    // 效果
    public List<ItemEffect> Effects;

    // 装备属性
    public EquipmentSlot? Slot;
    public int AttackBonus;
    public int DefenseBonus;
    public int HPBonus;

    // 主动物品
    public int Cooldown;
    public int EnergyCost;
}

/// <summary>
/// 道具效果
/// </summary>
[System.Serializable]
public class ItemEffect
{
    public ItemEffectType Type;
    public int Value;
    public float Percentage;
}

public enum ItemEffectType
{
    FlatAttack,
    FlatDefense,
    FlatHP,
    PercentAttack,
    PercentDefense,
    PercentHP,
    CriticalChance,
    CriticalDamage,
    LifeSteal,
    BonusGold,
    BonusDamage
}

/// <summary>
/// 道具实例（运行时）
/// </summary>
public class ItemInstance
{
    public ItemData Data { get; private set; }
    public int Id { get; private set; }

    public ItemInstance(ItemData data)
    {
        Data = data;
        Id = data.Id;
    }
}
```

### 3.2 背包与装备管理

```csharp
using System.Collections.Generic;

/// <summary>
/// 玩家背包
/// </summary>
public class PlayerInventory
{
    private List<ItemInstance> items = new List<ItemInstance>();
    private Dictionary<EquipmentSlot, ItemInstance> equipped = new Dictionary<EquipmentSlot, ItemInstance>();

    public int MaxItems { get; private set; } = 20;

    public IReadOnlyList<ItemInstance> Items => items;

    public event System.Action<ItemInstance> OnItemAdded;
    public event System.Action<ItemInstance> OnItemRemoved;
    public event System.Action<EquipmentSlot, ItemInstance> OnEquipmentChanged;

    /// <summary>
    /// 添加道具
    /// </summary>
    public bool AddItem(ItemInstance item)
    {
        if (items.Count >= MaxItems)
            return false;

        items.Add(item);
        OnItemAdded?.Invoke(item);
        return true;
    }

    /// <summary>
    /// 移除道具
    /// </summary>
    public void RemoveItem(ItemInstance item)
    {
        if (items.Remove(item))
        {
            OnItemRemoved?.Invoke(item);
        }
    }

    /// <summary>
    /// 装备道具
    /// </summary>
    public bool Equip(ItemInstance item)
    {
        if (item.Data.Type != ItemType.Equipment)
            return false;

        var slot = item.Data.Slot.Value;

        // 卸下当前装备
        if (equipped.TryGetValue(slot, out var currentEquipped))
        {
            Unequip(slot);
        }

        // 装备新道具
        items.Remove(item);
        equipped[slot] = item;

        OnEquipmentChanged?.Invoke(slot, item);
        return true;
    }

    /// <summary>
    /// 卸下装备
    /// </summary>
    public void Unequip(EquipmentSlot slot)
    {
        if (equipped.TryGetValue(slot, out var item))
        {
            if (items.Count < MaxItems)
            {
                equipped.Remove(slot);
                items.Add(item);
                OnEquipmentChanged?.Invoke(slot, null);
            }
        }
    }

    /// <summary>
    /// 获取装备
    /// </summary>
    public ItemInstance GetEquipment(EquipmentSlot slot)
    {
        return equipped.TryGetValue(slot, out var item) ? item : null;
    }

    /// <summary>
    /// 计算总属性加成
    /// </summary>
    public (int attack, int defense, int hp) GetTotalStats()
    {
        int totalAttack = 0;
        int totalDefense = 0;
        int totalHP = 0;

        foreach (var kvp in equipped)
        {
            var item = kvp.Value;
            totalAttack += item.Data.AttackBonus;
            totalDefense += item.Data.DefenseBonus;
            totalHP += item.Data.HPBonus;
        }

        // 被动物品效果
        foreach (var item in items)
        {
            if (item.Data.Type == ItemType.Passive)
            {
                totalAttack += item.Data.AttackBonus;
                totalDefense += item.Data.DefenseBonus;
                totalHP += item.Data.HPBonus;
            }
        }

        return (totalAttack, totalDefense, totalHP);
    }

    /// <summary>
    /// 获取所有被动效果
    /// </summary>
    public List<ItemEffect> GetPassiveEffects()
    {
        var effects = new List<ItemEffect>();

        foreach (var kvp in equipped)
        {
            if (kvp.Value.Data.Effects != null)
                effects.AddRange(kvp.Value.Data.Effects);
        }

        foreach (var item in items)
        {
            if (item.Data.Type == ItemType.Passive && item.Data.Effects != null)
                effects.AddRange(item.Data.Effects);
        }

        return effects;
    }
}
```

---

## 4. 难度递增系统

```csharp
using UnityEngine;

/// <summary>
/// 难度缩放系统
/// </summary>
public static class DifficultyScaler
{
    // 基础缩放参数
    private const float HP_SCALE_PER_FLOOR = 1.15f;
    private const float ATTACK_SCALE_PER_FLOOR = 1.10f;
    private const float DEFENSE_SCALE_PER_FLOOR = 1.08f;

    // Boss额外缩放
    private const float BOSS_HP_MULTIPLIER = 3.0f;
    private const float BOSS_ATTACK_MULTIPLIER = 1.5f;

    /// <summary>
    /// 缩放敌人属性
    /// </summary>
    public static void ScaleEnemy(EnemyData enemy, int floor, bool isBoss = false)
    {
        float floorMultiplier = Mathf.Pow(HP_SCALE_PER_FLOOR, floor - 1);

        enemy.MaxHP = Mathf.RoundToInt(enemy.MaxHP * floorMultiplier);
        enemy.Attack = Mathf.RoundToInt(enemy.Attack * Mathf.Pow(ATTACK_SCALE_PER_FLOOR, floor - 1));
        enemy.Defense = Mathf.RoundToInt(enemy.Defense * Mathf.Pow(DEFENSE_SCALE_PER_FLOOR, floor - 1));

        if (isBoss)
        {
            enemy.MaxHP = Mathf.RoundToInt(enemy.MaxHP * BOSS_HP_MULTIPLIER);
            enemy.Attack = Mathf.RoundToInt(enemy.Attack * BOSS_ATTACK_MULTIPLIER);
        }
    }

    /// <summary>
    /// 获取层对应的奖励质量
    /// </summary>
    public static int GetRewardQuality(int floor)
    {
        return Mathf.Clamp(floor, 1, 5);
    }

    /// <summary>
    /// 获取商店价格缩放
    /// </summary>
    public static float GetShopPriceScale(int floor)
    {
        return 1f + (floor - 1) * 0.2f;
    }

    /// <summary>
    /// 获取敌人数量
    /// </summary>
    public static int GetEnemyCount(int floor, RoomType roomType)
    {
        int baseCount = roomType switch
        {
            RoomType.Elite => 1,
            RoomType.Boss => 1,
            _ => 2 + Mathf.FloorToInt(floor / 3f)
        };

        return Mathf.Min(baseCount, 5);
    }
}
```

---

## 5. 进度保存与解锁

### 5.1 元进度系统

```csharp
using System.Collections.Generic;

/// <summary>
/// 元进度数据（跨存档）
/// </summary>
[System.Serializable]
public class MetaProgressData
{
    public int TotalRuns;
    public int HighestFloor;
    public int TotalKills;
    public int TotalGoldEarned;

    // 解锁项
    public List<int> UnlockedHeroes = new List<int>();
    public List<int> UnlockedItems = new List<int>();
    public List<int> UnlockedAchievements = new List<int>();

    // 成就进度
    public Dictionary<int, int> AchievementProgress = new Dictionary<int, int>();

    // 统计
    public Dictionary<int, int> HeroUsageCount = new Dictionary<int, int>();
    public Dictionary<int, int> ElementMatchCount = new Dictionary<int, int>();
}

/// <summary>
/// 元进度管理器
/// </summary>
public class MetaProgressManager : MonoSingleton<MetaProgressManager>
{
    private const string SAVE_KEY = "meta_progress";

    public MetaProgressData Data { get; private set; }

    public event System.Action<MetaProgressData> OnDataChanged;

    protected override void Awake()
    {
        base.Awake();
        Load();
    }

    private void Load()
    {
        string json = PlayerPrefs.GetString(SAVE_KEY, "");
        if (string.IsNullOrEmpty(json))
        {
            Data = new MetaProgressData();
            // 初始解锁
            Data.UnlockedHeroes.Add(1);
        }
        else
        {
            Data = JsonUtility.FromJson<MetaProgressData>(json);
        }
    }

    public void Save()
    {
        string json = JsonUtility.ToJson(Data);
        PlayerPrefs.SetString(SAVE_KEY, json);
        PlayerPrefs.Save();
        OnDataChanged?.Invoke(Data);
    }

    /// <summary>
    /// 记录一次运行
    /// </summary>
    public void RecordRun(int highestFloor, int kills, int gold, int heroId)
    {
        Data.TotalRuns++;
        Data.HighestFloor = Mathf.Max(Data.HighestFloor, highestFloor);
        Data.TotalKills += kills;
        Data.TotalGoldEarned += gold;

        if (!Data.HeroUsageCount.ContainsKey(heroId))
            Data.HeroUsageCount[heroId] = 0;
        Data.HeroUsageCount[heroId]++;

        // 检查解锁
        CheckUnlocks();

        Save();
    }

    /// <summary>
    /// 检查解锁条件
    /// </summary>
    private void CheckUnlocks()
    {
        // 基于进度的解锁
        if (Data.HighestFloor >= 3 && !Data.UnlockedHeroes.Contains(2))
        {
            Data.UnlockedHeroes.Add(2);
            EventBus.Publish(new UnlockEvent { Type = UnlockType.Hero, Id = 2 });
        }

        if (Data.HighestFloor >= 5 && !Data.UnlockedHeroes.Contains(3))
        {
            Data.UnlockedHeroes.Add(3);
            EventBus.Publish(new UnlockEvent { Type = UnlockType.Hero, Id = 3 });
        }

        if (Data.TotalKills >= 100 && !Data.UnlockedItems.Contains(101))
        {
            Data.UnlockedItems.Add(101);
            EventBus.Publish(new UnlockEvent { Type = UnlockType.Item, Id = 101 });
        }
    }

    public bool IsHeroUnlocked(int heroId)
        => Data.UnlockedHeroes.Contains(heroId);

    public bool IsItemUnlocked(int itemId)
        => Data.UnlockedItems.Contains(itemId);
}

public enum UnlockType
{
    Hero,
    Item,
    Achievement
}

public struct UnlockEvent
{
    public UnlockType Type;
    public int Id;
}
```

---

## 6. 完整Roguelike管理器

```csharp
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Roguelike运行数据
/// </summary>
public class RunData
{
    public int Seed;
    public int CurrentFloor;
    public DungeonData Dungeon;
    public Hero SelectedHero;
    public PlayerInventory Inventory;
    public int Gold;
    public int EnemiesKilled;

    // 当前运行中的加成
    public List<RunModifier> Modifiers = new List<RunModifier>();
}

/// <summary>
/// 运行修改器
/// </summary>
public class RunModifier
{
    public string Name;
    public ModifierType Type;
    public float Value;
}

public enum ModifierType
{
    DamageBonus,
    DefenseBonus,
    GoldBonus,
    HealthRegen,
    EnergyRegen
}

/// <summary>
/// Roguelike游戏管理器
/// </summary>
public class RoguelikeManager : MonoSingleton<RoguelikeManager>
{
    public RunData CurrentRun { get; private set; }
    public bool IsRunActive => CurrentRun != null;

    public event System.Action<RunData> OnRunStarted;
    public event System.Action<RunData> OnRunEnded;
    public event System.Action<int> OnFloorChanged;
    public event System.Action OnRoomCleared;

    /// <summary>
    /// 开始新运行
    /// </summary>
    public void StartNewRun(int heroId, int? seed = null)
    {
        int useSeed = seed ?? System.DateTime.Now.GetHashCode();

        CurrentRun = new RunData
        {
            Seed = useSeed,
            CurrentFloor = 1,
            Gold = 100,
            Inventory = new PlayerInventory()
        };

        // 创建英雄
        var heroConfig = ConfigManager.Load<HeroConfig>();
        var heroData = heroConfig.GetHero(heroId);
        CurrentRun.SelectedHero = new Hero();
        CurrentRun.SelectedHero.Initialize(heroData);

        // 生成地下城
        var generator = new DungeonGenerator(useSeed);
        CurrentRun.Dungeon = generator.Generate(10); // 10层

        OnRunStarted?.Invoke(CurrentRun);

        // 进入第一个房间
        EnterRoom(CurrentRun.Dungeon.CurrentRoomId);
    }

    /// <summary>
    /// 进入房间
    /// </summary>
    public void EnterRoom(int roomId)
    {
        CurrentRun.Dungeon.SetCurrentRoom(roomId);
        var room = CurrentRun.Dungeon.CurrentRoom;

        if (room == null) return;

        // 根据房间类型处理
        switch (room.Type)
        {
            case RoomType.Normal:
            case RoomType.Elite:
            case RoomType.Boss:
                StartCombat(room);
                break;

            case RoomType.Shop:
                OpenShop(room);
                break;

            case RoomType.Event:
                TriggerEvent(room);
                break;

            case RoomType.Treasure:
                CollectTreasure(room);
                break;

            case RoomType.Rest:
                Rest();
                break;
        }
    }

    private void StartCombat(DungeonRoom room)
    {
        // 初始化战斗
        var enemies = new List<Enemy>();
        foreach (var enemyData in room.Enemies)
        {
            var enemy = new Enemy();
            enemy.Initialize(enemyData);
            enemies.Add(enemy);
        }

        CombatManager.Instance.StartBattle(
            new List<Hero> { CurrentRun.SelectedHero },
            enemies
        );

        // 订阅战斗结束
        CombatManager.Instance.OnStateChanged += OnCombatStateChanged;
    }

    private void OnCombatStateChanged(CombatState state)
    {
        if (state == CombatState.Victory)
        {
            OnRoomCleared?.Invoke();

            var room = CurrentRun.Dungeon.CurrentRoom;
            room.SetCleared();

            // 领取奖励
            foreach (var reward in room.Rewards)
            {
                ClaimReward(reward);
            }

            CurrentRun.EnemiesKilled += room.Enemies.Count;
        }
        else if (state == CombatState.Defeat)
        {
            EndRun(false);
        }

        CombatManager.Instance.OnStateChanged -= OnCombatStateChanged;
    }

    private void OpenShop(DungeonRoom room)
    {
        // 打开商店界面
        EventBus.Publish(new ShopOpenedEvent { Shop = room.Shop });
    }

    private void TriggerEvent(DungeonRoom room)
    {
        // 触发随机事件
        EventBus.Publish(new EventTriggeredEvent { Event = room.Event });
        room.SetCleared();
    }

    private void CollectTreasure(DungeonRoom room)
    {
        foreach (var reward in room.Rewards)
        {
            ClaimReward(reward);
        }
        room.SetCleared();
    }

    private void Rest()
    {
        // 恢复30%生命值
        int healAmount = Mathf.RoundToInt(CurrentRun.SelectedHero.MaxHP * 0.3f);
        CurrentRun.SelectedHero.Heal(healAmount);

        EventBus.Publish(new RestEvent { HealAmount = healAmount });
    }

    private void ClaimReward(RewardData reward)
    {
        switch (reward.Type)
        {
            case RewardType.Gold:
                CurrentRun.Gold += reward.Value;
                break;

            case RewardType.Item:
                var itemData = ItemDatabase.GetItem(reward.ItemId);
                if (itemData != null)
                {
                    CurrentRun.Inventory.AddItem(new ItemInstance(itemData));
                }
                break;
        }

        EventBus.Publish(new RewardClaimedEvent { Reward = reward });
    }

    /// <summary>
    /// 前往下一个房间
    /// </summary>
    public void GoToNextRoom(int roomId)
    {
        var nextRoom = CurrentRun.Dungeon.Rooms.GetValueOrDefault(roomId);
        if (nextRoom == null) return;

        // 检查是否新层
        if (nextRoom.Floor > CurrentRun.CurrentFloor)
        {
            CurrentRun.CurrentFloor = nextRoom.Floor;
            OnFloorChanged?.Invoke(CurrentRun.CurrentFloor);
        }

        EnterRoom(roomId);
    }

    /// <summary>
    /// 结束运行
    /// </summary>
    public void EndRun(bool victory)
    {
        // 记录元进度
        MetaProgressManager.Instance.RecordRun(
            CurrentRun.CurrentFloor,
            CurrentRun.EnemiesKilled,
            CurrentRun.Gold,
            CurrentRun.SelectedHero.Id
        );

        OnRunEnded?.Invoke(CurrentRun);
        CurrentRun = null;
    }

    /// <summary>
    /// 获取可选择的下一个房间
    /// </summary>
    public List<DungeonRoom> GetNextRooms()
    {
        return CurrentRun.Dungeon.GetAccessibleRooms();
    }
}

// 事件定义
public struct ShopOpenedEvent { public ShopData Shop; }
public struct EventTriggeredEvent { public EventData Event; }
public struct RestEvent { public int HealAmount; }
public struct RewardClaimedEvent { public RewardData Reward; }

/// <summary>
/// 道具数据库（简化版）
/// </summary>
public static class ItemDatabase
{
    private static Dictionary<int, ItemData> items = new Dictionary<int, ItemData>();

    static ItemDatabase()
    {
        // 初始化道具数据
        items[1] = new ItemData
        {
            Id = 1,
            Name = "力量护符",
            Description = "攻击力+10",
            Type = ItemType.Passive,
            Rarity = 2,
            AttackBonus = 10
        };

        items[2] = new ItemData
        {
            Id = 2,
            Name = "铁甲",
            Description = "防御力+5",
            Type = ItemType.Equipment,
            Slot = EquipmentSlot.Armor,
            Rarity = 1,
            DefenseBonus = 5
        };
    }

    public static ItemData GetItem(int id)
    {
        return items.TryGetValue(id, out var item) ? item : null;
    }
}
```

---

## 本课小结

### 核心知识点

| 知识点 | 核心要点 |
|--------|----------|
| 地下城生成 | 房间连接、类型分配、内容填充 |
| 道具系统 | 类型、效果、装备管理 |
| 装备系统 | 槽位、属性加成、被动效果 |
| 难度递增 | 属性缩放、敌人数量、奖励质量 |
| 元进度 | 跨存档数据、解锁系统 |

### Roguelike流程

```
选择英雄 → 开始运行
     ↓
生成地下城（随机种子）
     ↓
进入房间 → 战斗/商店/事件/休息
     ↓
清除房间 → 获取奖励
     ↓
选择下一个房间
     ↓
（重复直到Boss层）
     ↓
胜利/失败 → 记录元进度
     ↓
返回主菜单
```

### 房间类型设计

| 类型 | 频率 | 内容 |
|------|------|------|
| Normal | 40% | 2-3个普通敌人 |
| Elite | 15% | 1个精英敌人 |
| Shop | 10% | 购买道具/装备 |
| Event | 15% | 随机事件 |
| Treasure | 10% | 免费奖励 |
| Rest | 10% | 恢复生命 |
| Boss | 每层末 | Boss战斗 |

---

## 相关链接

- [Roguelike Development](https://www.gamasutra.com/blogs/JoshGe/20181226/332424/How_to_Make_a_Roguelike.php)
- [Procedural Generation](https://www.procjam.com/)
- [Slay the Spire Design](https://www.gamedeveloper.com/design/designing-slay-the-spire-s-ranking-system)
