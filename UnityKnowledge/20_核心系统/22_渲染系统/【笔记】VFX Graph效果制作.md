---
title: 【笔记】VFX Graph效果制作
tags: ["Unity", "渲染", "VFX Graph", "粒子系统", "GPU粒子", "特效", "视觉特效", "笔记"]
category: 核心系统/渲染系统
created: "2026-07-01"
updated: "2026-07-01"
description: VFX Graph 七大战斗特效的完整制作方案——命中迸溅、刀光拖尾、爆炸链式 GPU Event、AOE 地面圈、区域填充、死亡爆裂、护盾光环，附 Output 模式与 Blend Mode 选型。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@latest
  - https://blog.unity.com/engine-platform/vfx-graph-in-unity-2022-lts-and-unity-6
  - "[[【笔记】大规模技能特效方案]]"
related: ["[[【笔记】大规模技能特效方案]]", "[[【教程】ComputeShader入门]]", "[[【教程】渲染管线基础]]", "[[渲染系统专题索引]]", "[[../25_DOTS技术栈/DOTS专题索引]]"]
---

# VFX Graph 效果制作

> [[【笔记】大规模技能特效方案]] 讲了 ECS 如何驱动 VFX Graph，本文聚焦 VFX Graph 编辑器内部——如何用 Context/Block 节点图实际制作七种常见战斗特效。

## 文档定位

VFX Graph 是 Unity 的 GPU 粒子系统（Compute Shader 驱动），与 CPU 粒子系统（ParticleSystem）完全不同。本文不重复 VFX Graph 窗口/操作基础（见[官方手册](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@latest)），而是直接给出每种效果的 Block 配置方案。

---

## VFX Graph 数据流回顾

```
Spawn Context          Initialize Context           Update Context           Output Context
 (什么时候生)     →     (生出来什么样)         →     (每帧怎么变)        →    (怎么画)
─────────────         ──────────────              ──────────────           ──────────────
· Single Burst        · Position (形状)            · Force (重力/风)        · Quad (面片)
· Constant Rate       · Lifetime                   · Velocity (阻力)        · Mesh (模型)
· GPU Event           · Color / Size               · Collision (碰撞)       · Trail (拖尾)
· Periodic Burst      · Velocity (方向)            · Size/Life 衰减          · Line (线条)
                      · Angle                      · Color 渐变              · Point (点)
                                                                            · Strip (条带)
```

粒子从 Spawn 到 Output 是**单向流水线**——先决定「怎么生」（Spawn/Init），再决定「怎么变」（Update），最后决定「怎么画」（Output）。

---

## 效果 1：命中迸溅（Hit Spark）

**视觉特征**：瞬时闪光 + 火花散射。被攻击时 0.1 秒内的即时反馈。

### Block 配置

```
Spawn:
  [Single Burst: count = 30]              ← 一次性发射 30 个粒子

Initialize:
  [Set Position: Random Sphere (r = 0.1)] ← 从一个点散开
  [Set Velocity: Random Sphere (speed 3..8)]
  [Set Lifetime: Random (0.3..0.6)]
  [Set Size: Random (0.02..0.08)]
  [Set Color over Life: Gradient]
    → 白(0s) → 黄(0.1s) → 橙(0.2s) → 红(0.3s) → 透明(0.6s)
    // 渐变模拟热量冷却

Update:
  [Force: (0, -9.8, 0)]                   // 重力
  [Drag: 2.0]                              // 空气阻力（速度衰减）
  [Kill: Age > Lifetime]                   // 自动死亡（内置）

Output (Quad):
  [Orient: Face Camera]                    // 始终面向相机
  [Blend Mode: Additive]                   // 叠加发光
  [Color Map: Spark Sprite]                // 火花贴图（径向渐变小亮点）
```

### 调参要点

| 参数 | 小值效果 | 大值效果 | 实战经验 |
|------|---------|---------|---------|
| Spawn count | 稀疏（廉价） | 密集（昂贵） | 近景 30~50，远景降到 5~10 |
| Speed | 缓慢飘 | 猛烈迸射 | 命中 speed=3~8；爆炸 speed=8~20 |
| Lifetime | 一闪而过 | 拖尾长 | 命中 0.3~0.6s；爆炸碎片 1.0~2.0s |
| Drag | 无阻力（惯性大） | 快速减速 | 火花用 1~3；碎片用 0.1~0.5 |

---

## 效果 2：刀光拖尾（Sword Trail / Ribbon）

**视觉特征**：弧形光带跟随武器挥动轨迹。RTS/动作游戏最频繁的特效。

### 核心技术：Strip Output

Strip（条带）模式将相邻粒子用三角带连成连续面片——粒子留在生成位置，自然形成轨迹：

```
时间 t=0    t=0.1    t=0.2    t=0.3
  ●─────────●─────────●─────────●     粒子留在生成位置
  │ ╲     ╱ │ ╲     ╱ │ ╲     ╱ │
  │  ╲   ╱  │  ╲   ╱  │  ╲   ╱  │     GPU 自动连接相邻粒子
  │   ╲ ╱   │   ╲ ╱   │   ╲ ╱   │     → 连续三角带 = 拖尾面片
  ▼    ▼    ▼    ▼    ▼    ▼    ▼
  Strip Mesh = 武器挥动轨迹的弧形光带
```

### Block 配置

```
Spawn:
  [Constant Rate: 40/秒]                  ← 持续发射，密度决定拖尾平滑度

Initialize:
  [Set Position from GraphicsBuffer]       ← 从 ECS 传入武器尖端坐标
  [Set Lifetime: 0.3]                      ← 短命，快速消失
  [Set Color: 白蓝色]                       ← 刀光质感

Update:
  (无运动——粒子留在原位形成轨迹)
  [Size over Life: Curve]
    → 头部宽(1.0) → 尾部细(0.1)            // 拖尾收尖

Output (Strip):
  [Particle Strips: Connected]              ← 顺序连接相邻粒子
  [Set Width over Life: Curve(宽→窄)]
  [Set Color over Life: Gradient(亮→暗)]
  [UV Map: Scroll Speed = 3.0]             ← 纹理沿条带流动 → 刀光流动感
  [Blend Mode: Additive]
  [Texture: Beam/Slash Sprite]
```

### Strip vs Trail 的区别

| 特性 | Strip Output | Trail（ParticleSystem） |
|------|-------------|----------------------|
| 实现 | GPU 粒子三角带连接 | CPU 端逐帧采样位置 |
| 性能 | GPU 自动 | CPU 每帧计算 |
| 大规模 | 10w 单位可并行 | 10w TrailRenderer 爆炸 |
| 形状控制 | Width/Color/UV 沿条带 | 固定宽度渐变 |

> 大规模场景的刀光方案选型见 [[【笔记】大规模技能特效方案]] 第七章。

---

## 效果 3：爆炸（Explosion）

**视觉特征**：强光闪 + 冲击波 + 火球 + 碎片 + 烟雾。这是最复杂的特效——需要 **GPU Event 链式触发**。

### GPU Event 链式架构

一个主事件触发多个子粒子系统，全部在 GPU 端完成：

```
主 Spawn Event (爆炸触发)
    │
    ├──→ Output A: 闪光 (Flash)
    │    Quad × 1, scale=5, lifetime=0.1s, 全白 Additive
    │
    ├──→ GPU Event → 子 Spawn B: 火球 (Fireball)
    │    Sphere 粒子向外膨胀, 颜色 黄→红→黑, 0.5s
    │
    ├──→ GPU Event → 子 Spawn C: 冲击波 (Shockwave)
    │    Ring 模型向外扩大, scale 0→10, 0.3s, 白色半透明
    │
    ├──→ GPU Event → 子 Spawn D: 碎片 (Debris)
    │    Mesh 粒子随机飞出, 重力+碰撞反弹, 1.0s
    │
    └──→ GPU Event → 子 Spawn E: 烟雾 (Smoke)
         Quad 向上飘, 逐渐放大+变暗, 2.0s
```

### Block 配置

**主 Spawn（触发器）**：

```
Spawn:
  [Single Burst: count = 1]                ← 触发一次
  [GPU Event: On Die → Spawn Fireball]     ← 死亡时触发各子事件
  [GPU Event: On Die → Spawn Shockwave]
  [GPU Event: On Die → Spawn Debris]
  [GPU Event: On Die → Spawn Smoke]

Initialize:
  [Set Lifetime: 0.05]                     ← 主粒子几乎瞬时死亡 → 立刻触发子事件
```

**子事件 B — 火球**：

```
Spawn (GPU Event B):
  [Count: 20]

Initialize:
  [Set Position: Random Sphere (r = 0.2)]
  [Set Velocity: Random Sphere (speed 2..5)]
  [Set Lifetime: Random (0.3..0.5)]
  [Set Color over Life: Gradient]
    → 白(0s) → 黄(0.1s) → 橙(0.2s) → 暗红(0.3s) → 黑烟(0.5s)

Update:
  [Drag: 3.0]                              ← 快速减速
  [Size over Life: Curve(小→大)]            ← 膨胀

Output (Quad):
  [Orient: Face Camera]
  [Blend: Additive]
  [Texture: Soft Circle Sprite]
```

**子事件 C — 冲击波**：

```
Spawn (GPU Event C):
  [Count: 1]

Initialize:
  [Set Position: (center.x, groundY, center.z)]
  [Set Lifetime: 0.3]

Update:
  [Scale over Life: Curve]
    → 0.0(0s) → 10.0(0.3s)                 ← 从 0 扩大到 10
  [Color over Life: Gradient(白→透明)]

Output (Mesh):
  [Mesh: Ring 模型（空心圆环）]
  [Orient: Y-Axis Flat]                    ← 平贴地面
  [Blend: Additive]
```

**子事件 D — 碎片**：

```
Spawn (GPU Event D):
  [Count: 15]

Initialize:
  [Set Position: Random Sphere (r = 0.1)]
  [Set Velocity: Random Sphere (speed 5..12)]
  [Set Lifetime: Random (0.8..1.2)]
  [Set Angular Velocity: Random (各轴 0..10)]  ← 旋转
  [Set Mesh Index: Random (0..4)]              ← 随机碎块模型

Update:
  [Force: (0, -9.8, 0)]
  [Collision: Plane (y = 0)]
  [Bounce: 0.3]
  [Drag: 0.2]

Output (Mesh):
  [Mesh: 碎块模型数组]
  [Blend: Opaque]                               ← 碎片不透明
```

**子事件 E — 烟雾**：

```
Spawn (GPU Event E):
  [Count: 30]
  [Delay: 0.2]                                ← 延迟 0.2s 出现（爆炸后冒烟）

Initialize:
  [Set Position: Random Sphere (r = 0.5)]
  [Set Velocity: (0, 1.5, 0)]                 ← 向上飘
  [Set Lifetime: Random (1.5..2.5)]
  [Set Size: Random (0.5..1.0)]

Update:
  [Size over Life: Curve(小→大×3)]            ← 膨胀
  [Color over Life: Gradient(深灰→浅灰→透明)]
  [Force: (wind.x, -0.3, wind.z)]

Output (Quad):
  [Orient: Face Camera]
  [Blend: Alpha Blend]                         ← 烟雾用 Alpha 而非 Additive
  [Texture: Soft Smoke Sprite]
```

---

## 效果 4：AOE 地面圈（Ground Circle）

**视觉特征**：地面发光圆环，标记技能范围。

### 方案 A：Ring 粒子（简单高效）

```
Spawn:
  [Single Burst: count = 1]

Initialize:
  [Set Position: (center.x, groundY + 0.01, center.z)]  ← 略高于地面防 Z-fight
  [Set Lifetime: skillDuration]
  [Set Scale: (radius * 2, 1, radius * 2)]

Update:
  [Scale over Life: Curve]
    → 0.95(0s) → 1.0(0.5s) → 0.95(1.0s) → 1.0(1.5s)...
    // 用 Sin 曲线做呼吸脉冲

Output (Mesh):
  [Mesh: Ring 模型]
  [Orient: Y-Axis Flat]
  [Color: 团队色 (蓝/红)]
  [Blend: Alpha Blend]
  [Cull: None]                                 ← 双面渲染
```

### 方案 B：Decal 投影（精确贴地）

```
适合地形起伏大的场景：
  · 用 URP/HDRP Decal Projector 投射到地面
  · 优点：跟随地形高度，不穿地
  · 缺点：移动端 Decal 性能差，不适合大规模

VFX Graph 配合：
  · VFX 粒子作为 Decal 载体
  · Position = 技能中心，Rotation = 地面法线对齐
  · Output 用 Decal Shader（而非 Standard）
```

---

## 效果 5：区域填充（火墙 / 毒雾）

**视觉特征**：持续区域内的密集粒子。RTS 的毒雾、火墙、治疗阵。

### 核心要点

1. **密度公式**：`Spawn Rate = 期望密度 × 区域面积`
   - 火墙 2m × 5m = 10m²，密度 3 粒子/m² → Rate = 30/秒
2. **Curl Noise 湍流**是区域特效的灵魂
3. **Alpha Blend**（不是 Additive）——烟雾要遮挡而非发光

### Block 配置

```
Spawn:
  [Constant Rate: 30]                        ← 持续发射
  // Rate = 密度(3/m²) × 面积(10m²)

Initialize:
  [Set Position: Box(width, height, depth)]   ← 按区域形状
  [Set Velocity: (0, 1.5, 0)]                 ← 向上飘
  [Set Lifetime: Random(1.0..2.0)]
  [Set Size: Random(0.3..0.8)]
  [Set Color over Life: Gradient]
    // 火墙：底=蓝白(高温) → 中=橙红 → 顶=暗红 → 透明
    // 毒雾：底=亮绿 → 中=深绿 → 顶=灰绿 → 透明

Update:
  [Force: (wind.x, -0.5, wind.z)]             ← 轻微下沉 + 风力
  [Noise Force: Curl Noise]
    · Amplitude = 1.5
    · Frequency = 0.5
    · Drag = 0.3
  [Size over Life: Curve × 1.5]               ← 膨胀

Output (Quad):
  [Orient: Face Camera]
  [Blend: Alpha Blend]                         ← 关键：不是 Additive！
  [Texture: Soft Smoke Sprite]
  [Color Map over Life: Gradient]
```

### Curl Noise 的视觉效果

```
无 Noise（喷泉感）       有 Curl Noise（真实湍流）
  ↑ ↑ ↑                    ↗ ↖ ↗
  ↑ ↑ ↑                    ↖ ↗ ↖     ← 自然卷曲
  ↑ ↑ ↑                    ↗ ↖ ↗     ← 看起来像真实火焰/烟雾
  ─────                    ─────
```

---

## 效果 6：死亡爆裂（Death Burst）

**视觉特征**：单位死亡时模型碎裂 + 能量释放。

### GPU Event 链

```
死亡事件 →
  ├── 碎裂碎片 (Mesh 粒子, 模型碎块, 重力 + 碰撞反弹)
  ├── 能量扩散 (Ring 向外扩大, Additive)
  └── 灵魂上升 (Strip 条带从死亡点向上升, 0.8s)
```

### 碎片碎块的 Block

```
Spawn (GPU Event):
  [Count: Random(5..10)]

Initialize:
  [Set Position: Random Sphere (r = 0.3)]     ← 从身体范围散开
  [Set Velocity: Random Sphere (speed 5..12)]
  [Set Angular Velocity: Random (各轴 0..15)]  ← 旋转
  [Set Lifetime: Random(0.8..1.5)]
  [Set Mesh Index: Random (0..4)]              ← 随机选碎块模型

Update:
  [Force: (0, -9.8, 0)]
  [Collision: Plane (y = 0)]                   ← 地面碰撞
  [Bounce: 0.3]                                ← 弹跳
  [Drag: 0.15]

Output (Mesh):
  [Mesh: 碎块模型数组]                           ← 3~5 种预制作碎块
  [Blend: Opaque]
  [Orient: Along Velocity]                     ← 朝运动方向
```

---

## 效果 7：护盾光环（Shield Aura）

**视觉特征**：围绕单位的半透明球壳 + 受击波纹。

### 护盾本体（持续效果）

```
Spawn:
  [Constant Rate: 5]                         ← 低频持续

Initialize:
  [Set Position: Random Sphere (r = shieldRadius)]
  [Set Lifetime: 2.0]
  [Set Size: Random(0.3..0.6)]
  [Set Color: 团队色 × Fresnel]               ← 边缘亮、正面暗

Update:
  [Velocity: Orbital (角速度 0.5)]             ← 环绕旋转
  [Size over Life: Curve(淡入→稳定→淡出)]

Output (Quad):
  [Orient: Face Away from Center]             ← 面朝外
  [Blend: Additive]
  [Texture: Hex/Shield Pattern Sprite]
```

### 受击波纹（GPU Event 触发）

```
被打时 → GPU Event

Spawn:
  [Count: 1]

Initialize:
  [Set Position: 命中点]
  [Set Scale: 0]

Update:
  [Scale Lerp: 0 → 2]                         ← 快速扩散
  [Color over Life: Gradient(亮白→透明)]

Output (Mesh):
  [Mesh: Ring]
  [Orient: Face Hit Direction]
  [Blend: Additive]
```

---

## Output 模式速查

| Output 类型 | 渲染方式 | 适用效果 | 性能 | 顶点数/粒子 |
|------------|---------|---------|------|-----------|
| **Quad** | 双三角面片（面向相机） | 通用：火花/烟雾/雨雪 | 最快 | 4 |
| **Mesh** | 指定模型 | 碎片/3D 物体 | 中等 | 模型顶点数 |
| **Point** | 单像素/小方块 | 远景粉尘/星空 | 最快 | 1 |
| **Strip** | 三角带连接相邻粒子 | 拖尾/刀光/闪电 | 较快 | 2N（连续） |
| **Line** | 线段（两点） | 闪电/激光 | 快 | 2 |

> **大规模场景首选 Quad 和 Point**——顶点数最少，GPU 合批效率最高。Mesh 仅用于少量关键碎片。

---

## Blend Mode 选择

```
Additive（叠加）                   Alpha Blend（透明混合）
─────────────────                 ─────────────────────
颜色相加：dst += src               颜色覆盖：dst = lerp(dst, src, alpha)
越叠越亮                           前面挡后面
─────────────────                 ─────────────────────
✅ 闪光/火花/能量/魔法             ✅ 烟雾/粉尘/半透明物体
✅ 暗背景效果好                     ✅ 亮背景也能看到
❌ 亮背景过曝                       ❌ 不发光
❌ 无深度排序问题                   ❌ 深度排序敏感（需 Sort）
─────────────────                 ─────────────────────
大规模友好（无需排序）              大规模需注意排序开销
```

> **大规模场景尽量用 Additive**——不需要按深度排序，GPU 合批效率更高。Alpha Blend 粒子在数千个时会因排序开销卡帧。

---

## 大规模场景与 ECS 衔接

以上所有效果的 **Spawn 触发方式**在大规模场景中需要改变：

```
少量场景（传统）                    大规模场景（10w 单位）
────────────                      ────────────────
C# SendEvent()                    GraphicsBuffer 批量写入
逐条触发                           一次写入 N 个事件
主线程瓶颈                         GPU Event 全 GPU 处理

VFX.SendEvent("OnHit", vfxData)   graphicsBuffer.SetData(events)
                                  → VFX Graph GPU Event 自动读取
```

> 完整的 ECS 事件 → VFX Graph 桥接方案见 [[【笔记】大规模技能特效方案]]。

---

## 速查清单

- [ ] 命中迸溅：Single Burst + Random Sphere + Additive Quad，count 30~50
- [ ] 刀光拖尾：Strip Output + Width Curve（宽→窄）+ UV Scroll
- [ ] 爆炸：GPU Event 链式触发（Flash → Fireball + Shockwave + Debris + Smoke）
- [ ] AOE 圈：Ring 粒子 + Scale 脉冲；地形起伏大用 Decal
- [ ] 区域填充：Box Position + Curl Noise 湍流 + Alpha Blend（不是 Additive）
- [ ] 死亡爆裂：GPU Event → Mesh 碎片 + 重力碰撞 + Ring 能量扩散
- [ ] 护盾：Fresnel 色 + Orbital Velocity 环绕 + 受击 GPU Event 波纹
- [ ] Output 选型：通用 Quad / 拖尾 Strip / 碎片 Mesh / 远景 Point
- [ ] Blend：发光用 Additive（无需排序），遮挡用 Alpha Blend（需排序）
- [ ] 大规模：用 GraphicsBuffer 替代 SendEvent，全 GPU 事件驱动

---

## 相关链接

- [[【笔记】大规模技能特效方案]] — ECS 事件驱动 VFX Graph 的架构方案
- [[【教程】ComputeShader入门]] — VFX Graph 底层用的 Compute Shader 基础
- [[【教程】渲染管线基础]] — URP/HDRP 渲染管线
- [VFX Graph 官方手册](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@latest)
- [Unity 6 VFX Graph 新功能](https://blog.unity.com/engine-platform/vfx-graph-in-unity-2022-lts-and-unity-6)
- [VFX Graph 示例项目 (UnityTechnologies)](https://github.com/Unity-Technologies/VisualEffectGraph-Samples)
