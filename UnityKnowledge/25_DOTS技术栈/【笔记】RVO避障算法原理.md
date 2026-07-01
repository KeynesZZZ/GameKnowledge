---
title: 【笔记】RVO避障算法原理
tags: ["Unity", "DOTS", "DOTS技术栈", "RVO", "ORCA", "避障", "算法", "线性规划", "速度障碍", "笔记"]
category: DOTS技术栈
created: "2026-07-01"
updated: "2026-07-01"
description: 从 VO 速度障碍到 RVO 互惠避让再到 ORCA 半平面——完整推演大规模局部避障算法的数学原理、几何构造、线性规划求解与工程优化。
unity_version: 2022.3 LTS+ / Unity 6
status: 待验证
author: llm
sources:
  - "[[【片段】RVO2局部避障ECS移植]]"
  - "[[【笔记】大规模单位AI决策与寻路]]"
  - "https://gamma.cs.unc.edu/RVO/ (原始 RVO 论文, van den Berg et al., 2008)"
  - "https://gamma.cs.unc.edu/ORCA/ (ORCA 论文, van den Berg et al., 2011)"
  - "https://gamma.cs.unc.edu/RVO2/ (RVO2 库实现)"
  - "https://www.meltycriss.com/2017/01/14/paper-orca/ (ORCA 论文逐段精读, meltycriss)"
  - "https://zhuanlan.zhihu.com/p/74888471 (ORCA 算法详解, 知乎)"
  - "https://blog.csdn.net/u012740992/article/details/89397714 (ORCA 原理与实现, CSDN)"
related: ["[[【片段】RVO2局部避障ECS移植]]", "[[【笔记】大规模单位AI决策与寻路]]", "[[【片段】FlowField流场Job实现]]", "[[【片段】UniformGrid空间分区Job实现]]", "[[DOTS专题索引]]"]
---

# RVO 避障算法原理

> [[【片段】RVO2局部避障ECS移植]] 给了完整的 Burst ECS 代码，本文讲透算法本身——从 VO 到 RVO 到 ORCA 的完整推演，让代码里的每一行数学都有对应。

## 问题背景

Flow Field（[[【片段】FlowField流场Job实现]]）给了全局方向，但单位朝同一方向走会重叠穿模。需要一个**局部避障**算法：让每个单位感知邻居、调整速度、互不穿透。

```
没有避障                        有避障（ORCA）
━━━━━━━                        ━━━━━━━━━
  →→→→→                          →→  →→
  →→→→→     全部叠在一起          →→  →→     自然分散
  →→→→→                          →→  →→
  →→→→→                          →→  →→
```

---

## 一、朴素方案为什么不行

### 方案 A：Boids 分离力

```
离最近邻居太近 → 施加排斥力推开

问题：
  1. 高密度区弹跳抖动（排斥力反复加/撤）
  2. 瓶颈处死锁堆积（排斥力互相抵消）
  3. 无法预判（只在已经太近时才反应）
```

### 方案 B：直接用 VO

```
VO 理论正确，但会导致震荡：

  t=0: A 向左避开 B，B 也向左避开 A → 两人偏到同一边
  t=1: 发现还对着 → 同时改向右
  t=2: 又偏了 → 再改...
  → 永远无法稳定错开
```

**根因**：双方各自独立做完整避让 → 做了重复工作 → 过度反应。

---

## 二、VO（Velocity Obstacle）—— 速度障碍

### 核心思想

在**速度空间**（而非位置空间）中定义「禁区」。如果我的速度落在这个区域内，未来 τ 秒内一定会和对方碰撞。

### 几何构造

```
位置空间                           速度空间（VO）
──────────                        ──────────────

     B (半径 rB)                       VO 是一个截断圆锥
     ●                                ╱ ╲
   ╱ ╲                              ╱   ╲
 ╱     ╲                           ╱     ╲
╱  A    ╲         ───→          ╱  VO    ╲
●(rA)    ╲                     ╱  禁区     ╲
           ╲                  ╱______________╲
            ╲                  ↑
             ╲                截断点 = pAB / τ

pAB = pB - pA（相对位置向量）
圆锥方向 = pAB 归一化
圆锥半角 = arcsin((rA + rB) / |pAB|)
截断距离 = |pAB| / τ（τ = 预见时间窗）
```

**VO 的含义**：A 的速度如果落在 VO 内，意味着朝着 B 的方向移动太快，τ 秒内会撞上 B。

**A 的策略**：选一个落在所有邻居 VO 之外的速度，且尽量接近期望速度（来自 Flow Field）。

### VO 的致命缺陷

双方各自独立做**完整**避让 → 做了双倍工作 → 过度反应 → 震荡。

---

## 三、RVO（Reciprocal VO）—— 互惠避让

### 核心改进

> 如果 A 假设 B 会承担**一半**的避让责任，A 自己也只承担一半，就不会做重复避让。

```
VO 方案：A 做全部避让，B 也做全部避让
         → 双倍避让 → 过度反应 → 震荡

RVO 方案：A 做一半避让，假设 B 也做另一半
         → 恰好够 → 稳定错开
```

### 数学表达

```
VO^τ_{A|B} = { v : 未来 τ 秒内 v 导致碰撞 }

RVO^τ_{A|B} = { v : 2v - v_A ∈ VO^τ_{A|B} }
                       ↑
                   2 倍因子 = 双方各承担一半
```

**直觉理解**：A 把自己的避让量减半（`v_A + u/2`），因为 B 也会避让 `u/2`，合起来就是完整的 `u`。

### 为什么 RVO 消除了震荡

```
t=0: A 只让一半（假设 B 会让另一半），B 也只让一半
     → A 偏左半步 + B 偏右半步 = 恰好错开
     → 稳定！

为什么不会重复偏？
  因为 RVO 考虑了对方当前速度：
  如果 B 已经在避让（B 的速度已偏移），A 计算时看到 B 的速度已经偏了
  → VO 区域跟着转 → A 需要的额外避让更小
  → 自然收敛而非震荡
```

---

## 四、ORCA（Optimal Reciprocal Velocity Obstacle）

ORCA 是 RVO2 库实际使用的最终算法——把 RVO 从「速度障碍集合」简化为**一条半平面**，大幅简化求解。

### 关键洞见

> 不需要计算完整的圆锥形 VO，只需算出 VO 边界上**离当前相对速度最近的点** `u`，由此定义一条半平面。

### 逐步几何构造

#### 步骤 1：相对量

```
pAB = pB - pA          （A 看 B 的相对位置）
vAB = vA - vB          （A 看 B 的相对速度）
rAB = rA + rB          （合并半径）
```

> **Minkowski sum 视角**（形式化定义）：两个圆盘 A(rA)、B(rB) 的碰撞等价于一个**合并圆盘** D(rAB) 的点碰撞。即将 A 缩成点、B 膨胀为半径 rAB 的圆。在速度空间中，`CA^τ = D(rAB) ⊕ (-D(rAB))` 的截断版本就是 VO 圆锥——截断圆锥是 Minkowski sum 在时间窗 τ 上的投影。这是 ORCA 形式化推导的几何基础。

#### 步骤 2：判断状态并计算修正向量 u

**情况 A：还没碰（|pAB| > rAB）**

在速度空间画截断圆锥。`vAB` 落在圆锥内 → 需要修正。

```
    圆锥边界
     ╱
   ╱
 ╱  ·u  ← VO 边界上离 vAB 最近的点
╱   ↑
   vAB（当前相对速度，在禁区内）
───── 截断底 = pAB/τ

u = 从 vAB 指向最近边界点的修正向量
```

圆锥边界最近点分三种子情况：

```
子情况 1：vAB 投影在截断圆上（正面冲撞）
  · w = vAB - pAB/τ
  · unitW = normalize(w)
  · u = unitW * rAB - vAB    （修正到截断圆边）

子情况 2：vAB 落在圆锥左侧 leg
  · 用 2D 叉积 det() 判断左右
  · u = dot(vAB, legDir) * legDir - vAB

子情况 3：vAB 落在圆锥右侧 leg
  · 对称处理
```

**情况 B：已经碰了（|pAB| ≤ rAB）**

圆锥退化（截断底为负），`u` 指向「推开方向」：

```
u 方向 = normalize(vAB - pAB/τ)
u 大小 = rAB/τ - |pAB|... → 正值（要把两个球推开）
```

#### 步骤 3：半责任 → 半平面

```
完整修正 = u
A 的责任 = u / 2

A 的 ORCA 半平面：
  line.point    = vA + u/2       ← 半平面经过此点
  line.direction = perpendicular(u) ← 半平面方向

  安全区域 = half-plane 中 dot(v - point, normal) ≥ 0 的那侧
```

```
       可行区（安全）       line.direction
         ↕   ↗─────────────────── →
         ↗ .point (= vA + u/2)
       ↗
  禁区 ↗                        ← ORCA line
     (VO 侧)
```

A 对每个邻居 B 算一条 ORCA line。N 个邻居 → N 条半平面。

### ORCA 的两条正确性保证

> 来源：meltycriss 逐段精读笔记 + ORCA 原始论文 (van den Berg et al., 2011)。

ORCA 之所以是「最优」的，因为它满足两条数学性质：

**性质 1：互惠无碰撞（Reciprocally Collision Avoiding）**

```
如果 A 和 B 都选择各自 ORCA 半平面安全侧的速度，
则他们在 τ 秒内不会碰撞。

直觉：A 让了 u/2，B 让了 u/2，合起来 u → 完整修正。
证明：|vA_new - vB_new - pAB/τ| ≥ rAB/τ
     （新的相对速度落在 VO 之外）
```

**性质 2：互惠最大可行域（Reciprocally Maximal）**

```
在所有满足性质 1 的半平面分割方案中，
ORCA 给 A 和 B 的可行域并集最大。

含义：不存在另一种「让法」让双方都获得更大的速度选择空间。
     ORCA 是帕累托最优——它最大化了双方的自由度。

这是「Optimal」一词的来源。
```

> **面试要点**：ORCA 的「O」来自 Reciprocally Maximal 性质。它不只是「能避障」，而是「在所有避障方案中最不限制自由度」。

---

## 五、线性规划求最优速度

N 条半平面 + 1 个速度圆（|v| ≤ maxSpeed），求最接近期望速度 `v_pref` 的可行点：

```
minimize  |v - v_pref|
subject to  v 在所有 ORCA 半平面的安全侧
            |v| ≤ maxSpeed
```

这是 **2D 线性规划**。RVO2 用三个函数解决：

### LinearProgram1：单约束下求可行点

```
在 lineNo 这条线 + 已有约束 0..lineNo-1 的交集下，
求可行线段 [tLeft, tRight]，再取最接近 v_pref 的点。

几何本质：速度圆与一条线的交集 = 一段弧/线段，
         再被其他线裁剪 → 最终可行区间。
```

### LinearProgram2：逐条加入约束

```
从最优解 v_pref 开始（如果在速度圆内）
逐条检查 N 条 line：
  如果当前解违反了第 i 条 → 调用 LP1 重解
  如果 LP1 无解 → 记录失败索引，停止

全部通过 → 完美，直接用结果
某条失败 → 进入 LP3 兜底
```

### LinearProgram3：兜底（3D 投影法）

```
当约束相互矛盾（无法全部满足）时：
  保留已满足的约束，
  对违反的约束按「违反程度」从大到小处理，
  用 3D 投影法找到「最远可行解」。

保证：永远有输出，不会卡死。
代价：牺牲部分约束（某些邻居可能被穿模），但不会 NaN/崩溃。
```

#### LP3 的几何直觉：在不平整曲面上找最低点

> 来源：CSDN 文章。

```
想象约束半平面是一把把刀，从速度空间里切去「禁区」。
LP2 失败 = 刀太多，切完之后没有一块区域同时满足所有刀。

LP3 的做法（3D 投影法）：
  1. 把 2D 问题升维到 3D：z 轴 = 违反约束的距离
  2. 每条约束变成一个斜面（满足的一侧 z=0 平坦，违反的一侧 z>0 上升）
  3. 在这个 3D 地形上找「最低点」= 违反最少的解

       z（违反量）
       ↑     ╱╲ ← 最违反的约束面
       │   ╱  ╲
       │ ╱     ╲
       │───────── ← 满足的约束面（z=0）
       └──────────→ v 空间（速度 2D）
              ↑
           最低点 = LP3 结果
```

**直觉理解**：LP2 要求所有约束都满足（z=0 处有解），做不到就放弃；LP3 找的是「爬最少的坡」= 违反最少的可行解，保证总是有输出。

### LP 的直觉

```
v_pref（期望速度，Flow Field 给）
  ·
  │
  │  ← 从 v_pref 出发，朝可行域移动
  │
  · ← 最终速度（可行域内离 v_pref 最近的点）

可行域 = 所有半平面的交集 ∩ 速度圆
```

### LP2 中 optVelocity 的三种选择策略

> **这是将 ORCA 从理论落地到工程时最关键的决策点**，三篇参考文章都重点强调了这个问题。

LP2 的目标函数是 `minimize |v - optVelocity|`，但 `optVelocity` 怎么选？有三种策略：

| 策略 | optVelocity = | LP 永远有解？ | 行为特点 | 适用场景 |
|------|---------------|---------------|----------|----------|
| **保守策略** | `0`（零向量） | **是**（原点一定在速度圆内，半平面约束总可满足） | 密集时单位停下不动 → **死锁** | 理论分析、证明 |
| **贪婪策略** | `v_pref`（期望速度） | **否**（约束矛盾时无解 → 需要 LP3 兜底） | 朝目标尽量走，但 LP3 兜底可能穿模 | 低密度、开阔场 |
| **惯性策略** | `v_curr`（当前速度） | **否**（但比贪婪好，因为 v_curr 通常已满足大部分约束） | **平滑自然**，惯性大→转向慢，惯性小→灵活 | **工业标准（RVO2 默认）** |

```
三种策略的直观对比（单位被多个邻居包围的密集场景）：

  v_pref（贪婪）                    v_curr（惯性）              0（保守）
    ·← 朝目标走                      ·← 保持当前方向             ·← 原点（停下）
   ╱ ╲                              ╱                           ●
  ╱ LP ╲ 可行域                     ╱ LP 可行域               LP 可行域
 ╱  无解  ╲                        ╱  有解                    ╱╲
┌── LP3 ──┐                      ●→ 最终速度                 ●→ 零速度
 v_pref 太远 → LP2 失败 → LP3    v_curr 离可行域近 → 平滑    死锁：全员停下
```

**为什么惯性策略最好？**

```
1. v_curr 是上一帧的实际速度 → 天然满足大部分上一帧已满足的约束
   → LP2 逐条检查时，前几条大概率已满足 → 快速收敛

2. v_curr ≠ v_pref → 不会像贪婪策略那样执意冲目标
   → 在密集场景下自然减速但不完全停下 → 避免死锁

3. 与速度平滑（lerp）配合：
   vel = lerp(vel, newVel, 0.3)
   若 optVelocity = v_curr ≈ vel → newVel 与 vel 差异小 → 平滑度极高
```

> **代码对应**：RVO2 库 `linearProgram2` 中 `optVelocity = agent->velocity_`，不是 `agent->prefVelocity_`。我们在 [[【片段】RVO2局部避障ECS移植]] 的 LP2 调用中传的 `optVelocity` 应为**当前速度**而非期望速度。LP2 在 `directionOpt=false` 模式下求的是最接近 `optVelocity` 的可行点。

---

## 六、静态障碍处理

ORCA 的半责任（`0.5 * u`）适用于**互惠**对象（会动的单位）。静态障碍（墙、岩石）不会避让你，需要**全责**：

```
互惠避障（单位 vs 单位）：
  line.point = selfVel + 0.5 * u    ← 各让一半

静态避障（单位 vs 墙）：
  line.point = selfVel + 1.0 * u    ← 自己全让

实现：computeORCALines 时区分邻居类型，
      障碍物的 line 不乘 0.5。
```

### 静态障碍的三个工程要点

> 来源：CSDN 文章与 RVO2 库文档。

**① 障碍物用 v_opt = 0**

```
障碍物的 ORCA line 构建中，optVelocity 取零向量。
原因：障碍物不动，相对速度 = 单位自身速度。
用 v_opt = 0 → LP 求解时更保守 → 单位会主动绕开障碍。

代码体现：对障碍物建 line 时，relVel = selfVel（而不是 selfVel - otherVel）
         因为 otherVel = 0。
```

**② 障碍物用更小的 τ（timeHorizonObst）**

```
单位 vs 单位：     timeHorizon = 1.5~2.0s   （预见足够远，提前避让）
单位 vs 障碍物：   timeHorizonObst = 0.5~1.0s（更近才反应，避免过早绕弯）

RVO2 库区分两套时间窗：
  agent 时间窗 → 灵活避让（远距离就开始偏转）
  obstacle 时间窗 → 保守绕行（近距离才转，避免在宽阔走廊里贴墙走）
```

**③ 线段障碍（Line Segment Obstacles）**

```
墙不是点，是有长度的线段。RVO2 处理方式：

  障碍 = 有向线段 (vertex₁ → vertex₂)
  构建的 ORCA line 不是一条，而是最多三条：
    1. 左 leg（从 vertex₁ 方向延伸的约束）
    2. 右 leg（从 vertex₂ 方向延伸的约束）
    3. 若单位离线段太近 → 截断圆约束

  +---vertex₁----------vertex₂---+
  左 leg ↗                    ↗ 右 leg
         禁区（墙背后）
```

> 工程实现中，障碍线段由导航网格（NavMesh）的边界提取。RVO2 库的 `addObstacle()` 接受顶点序列，自动连接成闭合多边形。

---

## 七、完整算法流程

```
每个单位每帧（10w 并行）：

1. 查邻居
   UniformGrid 3×3 邻域 → 过滤 NeighborDist → 得到 ≤ MaxNeighbors 个邻居

2. 逐邻居建 ORCA line
   for each neighbor j:
     a. relPos = j.pos - self.pos
     b. relVel = self.vel - j.vel
     c. 判断状态（未碰/已碰/圆锥/左右 leg）
     d. 计算 u（最小修正向量）
     e. line.point = self.vel + 0.5 * u    ← 半责任
     f. line.direction = perpendicular(u)

3. 线性规划求最优速度
   LP2(所有 lines, maxSpeed, v_curr) → newVel    ← optVelocity = 当前速度（惯性策略）
   如果 LP2 失败 → LP3 兜底（3D 投影法）

4. 写回速度
   vel = lerp(vel, newVel, 0.3)   ← 平滑（防抖动）
```

> 代码实现（computeORCALines / linearProgram1/2/3 的完整 Burst 移植）见 [[【片段】RVO2局部避障ECS移植]]。

---

## 八、与其他避障方案对比

| 方案 | 原理 | 防穿模 | 防震荡 | 性能 | 适用 |
|------|------|--------|--------|------|------|
| **Boids Separation** | 排斥力推开 | 弱 | 抖动 | 最快 | 群鸟/鱼群（不在乎穿模） |
| **Social Force** | 社会力（排斥+吸引+摩擦） | 中 | 中 | 中 | 人群模拟 |
| **Steering Behaviors** | 转向行为（避让/到达） | 弱 | 中 | 快 | 少量角色 |
| **VO** | 速度障碍 | 强 | **震荡** | 中 | 理论好但不实用 |
| **RVO** | 互惠速度障碍 | 强 | 强 | 中 | 学术完整 |
| **ORCA** | 最优半平面 + LP | 强 | 强 | **最优** | **工业标准** |

> ORCA 是大规模局部避障的事实标准（RVO2 库被 StarCraft II 等使用）。

---

## 九、大规模工程优化

```
10w 单位 ORCA 的瓶颈不在算法，在邻域查询：

  per unit cost = 邻域查询 O(k) + 建线 O(k) + LP O(k²)
                                    ↑              ↑
                              k=邻居数         k 很小时可忽略
```

### 优化策略

| 策略 | 效果 | 说明 |
|------|------|------|
| **MaxNeighbors 截断（10~20）** | 控 O(k²) | 高密度区只取最近 N 个邻居 |
| **NeighborDist 限制（4~8m）** | 控 O(k) | 超过则邻居爆炸 |
| **分帧轮询（60 桶）** | 降 60x | 每单位每秒算一次，中间帧用上次速度（惯性） |
| **远景降级** | 降参与率 | 近景 ORCA / 中景简化（3 邻居）/ 远景纯 Flow Field + 分离力 |
| **Flow Field + ORCA 混合** | 全局+局部 | Flow Field 全局方向 O(1) + ORCA 局部冲突 |

### 分层 LOD 策略

```
近景 (< 30m):  完整 ORCA（N 邻居 + LP），每帧或每 2 帧算
中景 (30~80m): 简化 ORCA（只查 3 个最近邻居），每 5 帧算
远景 (> 80m):  纯 Flow Field + 简单分离力（无 ORCA）
```

---

## 十、参数调优

| 参数 | 含义 | 起步值 | 调大效果 | 调小效果 |
|------|------|--------|---------|---------|
| `NeighborDist` | 邻居查询半径 | 4~8m | 更早避让（平滑），CPU 更贵 | 反应迟钝，易穿模 |
| `TimeHorizon` | 避障预见时间窗 | 1.0~2.0s | 更早避让（优雅），约束更多 | 临时急转，抖动 |
| `MaxNeighbors` | 最大邻居数 | 10~20 | 更精确，CPU 更贵 | 高密度区忽略远处邻居 |
| `Radius` | 单位碰撞半径 | 模型真实半径 | 间隔大（不挤），瓶颈处堵塞 | 间隔小，易穿模 |
| `MaxSpeed` | 最大速度 | Flow Field 上限 | — | — |

> 调大 `TimeHorizon`/`NeighborDist` → 避让更早更平滑但 CPU 更贵；调小 → 易抖动穿模。10w 单位时优先压 `MaxNeighbors` 和 `NeighborDist`。

---

## 十一、避坑

| 现象 | 根因 / 处置 |
|------|------------|
| 单位抖动（来回弹跳） | `TimeHorizon` 太小或速度未平滑 → 加 `lerp(vel, newVel, 0.3)` |
| 高密度区穿模 | `MaxNeighbors` 截断太激进 → 适当增大（15~20） |
| 高密度区死锁停步 | `optVelocity = v_pref`（贪婪）或 `= 0`（保守）→ 改 `v_curr`（惯性策略） |
| 瓶颈处堵塞堆积 | `Radius` 太大 + `NeighborDist` 太大 → 瓶颈处临时降半径 |
| LP 频繁失败 | 约束矛盾太多（极密场景）→ LP3 兜底有输出但可能穿模，属于预期行为 |
| 速度突变 | ORCA 每帧重算且无平滑 → 帧间速度 `lerp` |
| 静态障碍穿透 | 障碍 line 用了半责任（0.5）→ 改全责（1.0），且 `timeHorizonObst < timeHorizon` |
| 墙角卡住 | 障碍只用点障碍没用线段障碍 → 用 `addObstacle()` 加线段（NavMesh 边界） |
| Grid 读到半更新数据 | BuildGrid 与 Avoidance 的 JobHandle 未接依赖 → `[UpdateAfter]` 或分帧 |
| Burst 编译失败 | `NativeMultiHashMap.Enumerator` 在 Burst 中枚举需特定写法 → 见 [[【片段】RVO2局部避障ECS移植]] |

---

## 面试速答

> "RVO 是解决大规模局部避障的标准算法。核心思想是在速度空间定义速度障碍（VO）——如果我的速度落在这个区域内就会撞上对方。朴素 VO 有震荡问题——双方各自完整避让会重复偏移。ORCA 的改进是让双方各承担一半避让责任，把圆锥形 VO 简化为一条半平面，这条半平面满足互惠无碰撞和互惠最大可行域两条性质——这也是 'Optimal' 的来源。最后用 2D 线性规划在所有约束下求最接近**当前速度**（惯性策略，而非期望速度）的可行解，LP2 失败时 LP3 兜底保证永远有输出。静态障碍用全责（不乘 0.5）且更短的时间窗。大规模场景下我们用 UniformGrid 做 O(1) 邻域查询 + MaxNeighbors 截断 + 分帧轮询来控制开销，配合 Flow Field 全局寻路使用。"

---

## 速查清单

- [ ] VO = 速度空间的禁区（截断圆锥），速度在内 = 未来会碰
- [ ] VO 震荡根因 = 双方各自完整避让 → 过度反应 → RVO 各让一半解决
- [ ] ORCA = 把 VO 简化为半平面（取 VO 边界离 vAB 最近点 → 半责任 → line）
- [ ] ORCA 「Optimal」= 互惠无碰撞 + 互惠最大可行域（帕累托最优）
- [ ] 求 u → line.point = vA + u/2 → line.direction = perp(u)
- [ ] LP2 的 optVelocity = **v_curr（当前速度/惯性策略）**，不是 v_pref
- [ ] optVelocity 三策略：保守（0，死锁）/ 贪婪（v_pref，LP 失败多）/ **惯性（v_curr，最佳）**
- [ ] LP3 兜底 = 3D 投影法，在「违反量」地形上找最低点
- [ ] 静态障碍：全责（不乘 0.5）+ 更短 τ（timeHorizonObst）+ 线段障碍
- [ ] Flow Field（全局方向）+ ORCA（局部避障）= 大规模标准组合
- [ ] ORCA 是局部算法，必须配合全局寻路（Flow Field / A*）使用
- [ ] 大规模优化：MaxNeighbors 截断 + NeighborDist 限制 + 分帧轮询 + LOD 降级
- [ ] 速度平滑 `lerp(vel, newVel, 0.3)` 防抖动

---

## 相关链接

- [[【片段】RVO2局部避障ECS移植]] — 完整 Burst ECS 代码（computeORCALines / linearProgram1/2/3）
- [[【笔记】大规模单位AI决策与寻路]] — Flow Field + ORCA 混合策略
- [[【片段】FlowField流场Job实现]] — 全局寻路（ORCA 的方向来源）
- [[【片段】UniformGrid空间分区Job实现]] — 邻域查询（ORCA 的邻居来源）
- [RVO 原始论文 (van den Berg et al., 2008)](https://gamma.cs.unc.edu/RVO/)
- [ORCA 论文 (van den Berg et al., 2011)](https://gamma.cs.unc.edu/ORCA/)
- [RVO2 库](https://gamma.cs.unc.edu/RVO2/)
- [ORCA 论文逐段精读 (meltycriss)](https://www.meltycriss.com/2017/01/14/paper-orca/)
- [ORCA 算法详解 (知乎)](https://zhuanlan.zhihu.com/p/74888471)
- [ORCA 原理与实现 (CSDN)](https://blog.csdn.net/u012740992/article/details/89397714)
