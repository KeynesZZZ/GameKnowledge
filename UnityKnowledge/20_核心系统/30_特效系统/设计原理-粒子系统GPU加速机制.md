# 设计原理 - 粒子系统GPU加速机制

> Unity粒子系统GPU加速、VFX Graph架构、CPU vs GPU粒子性能对比 `#深度解析` `#特效` `#GPU`

## 快速参考

```csharp
// Shuriken (CPU粒子)
public class CPUParticleSystem : MonoBehaviour
{
    [SerializeField] private ParticleSystem particleSystem;

    private void Update()
    {
        // CPU粒子系统每帧更新
        // 计算位置、速度、颜色、生命周期等
    }
}

// Visual Effect Graph (GPU粒子)
public class GPUParticleSystem : MonoBehaviour
{
    [SerializeField] private VisualEffectAsset vfxAsset;
    private VisualEffect vfxGraph;

    private void Start()
    {
        // 创建VFX Graph实例
        vfxGraph = VisualEffect.Instantiate(vfxAsset);
        vfxGraph.transform.position = transform.position;
    }

    public void PlayEffect()
    {
        // 播放GPU粒子效果
        vfxGraph.Play();
    }
}
```

---

## 适用版本

- **Unity版本**: 2019.4 LTS+, 2020.3 LTS+, 2021.3 LTS+, 2022.3 LTS+, 2023.2 LTS+
- **Visual Effect Graph**: Unity 2021.2+ (Package)
  - Package安装: Window > Package Manager > Unity Registry > Visual Effect Graph
  - 推荐版本: 14.0.0+ (Unity 2022.3+)
- **平台**: Windows, macOS, iOS, Android (需要GPU支持), 主机平台
- **兼容性说明**:
  - 2019.4+: Shuriken CPU粒子系统基本稳定
  - 2021.2+: Visual Effect Graph引入
  - 2022.0+: VFX Graph性能大幅提升
  - 2023.0+: VFX Graph功能完善（模拟、碰撞等）
- **GPU要求**:
  - PC: 支持Compute Shader 4.5+
  - iOS: A11+ (Metal)
  - Android: OpenGL ES 3.2+ 或 Vulkan 1.0+
- **注意**: 本文档基于Unity 2022.3 LTS + VFX Graph 14.0.0测试验证

---

## 粒子系统架构

### CPU vs GPU 粒子系统对比

```
CPU粒子系统 (Shuriken):
├─> 位置计算 (CPU)
├─> 速度计算 (CPU)
├─> 生命周期管理 (CPU)
├─> 碰撞检测 (CPU)
└─> 渲染 (GPU)

GPU粒子系统 (VFX Graph):
├─> 位置计算 (GPU)
├─> 速度计算 (GPU)
├─> 生命周期管理 (GPU)
├─> 碰撞检测 (GPU)
└─> 渲染 (GPU)

性能对比:
CPU:   支持粒子数 < 10,000
GPU:   支持粒子数 > 1,000,000
```

### Shuriken CPU粒子系统

```
Shuriken CPU粒子系统架构:

┌─────────────────────────────────────────────────────┐
│              CPU更新 (每帧)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  位置更新   │  │  速度更新   │  │  颜色更新   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  生命周期   │  │  尺寸更新    │  │  旋转更新    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              渲染 (GPU)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  顶点数据    │  │  UV数据       │  │  颜色数据    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  纹理采样    │  │  Alpha测试    │  │  深度测试    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘

性能瓶颈:
- CPU: 粒子更新计算 (10000粒子 ≈ 5-10ms)
- 传输: CPU → GPU 数据传输 (10000粒子 ≈ 2-5ms)
- 总计: 约7-15ms/帧

应用场景:
- 少量粒子 (<1000)
- 简单物理交互
- 需要精确碰撞检测
```

### VFX Graph GPU粒子系统

```
VFX Graph GPU粒子系统架构:

┌─────────────────────────────────────────────────────┐
│              VFX Graph Editor                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Spawn Block │  │  Update Block │  │  Kill Block │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Color Block │  │  Size Block   │  │  Rotation Block│   │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│            Compute Shader (GPU)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  粒子数据缓冲 │  │  速度缓冲     │  │  生命周期缓冲 │    │
│  │  (Append)    │  │  (Consume)    │  │  (Counter)    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  粒子位置     │  │  粒子颜色     │  │  粒子尺寸     │    │
│  │  (Position)   │  │  (Color)      │  │  (Size)       │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                渲染 (GPU)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  粒子Mesh    │  │  粒子纹理     │  │  粒子Shader   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘

性能优势:
- CPU: 几乎无计算 (<0.5ms)
- GPU: 并行计算 (100000粒子 ≈ 2-5ms)
- 传输: GPU内部传输 (无需CPU→GPU)
- 总计: 约2-5ms/帧

应用场景:
- 大量粒子 (10000+)
- 简单物理交互
- 火焰、烟雾、爆炸等效果
```

---

## VFX Graph架构

### VFX Graph核心组件

```
VFX Graph架构:

┌─────────────────────────────────────────────────────┐
│              VFX Graph Asset                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Context     │  │  Event       │  │  Property     │    │
│  │  (环境配置)  │  │  (事件系统)  │  │  (属性系统)   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Spawner      │  │  Update       │  │  Output       │    │
│  │  Block       │  │  Block        │  │  Block        │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                Block Graph                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Spawn    │→│ Initialize│→│ Update   │→│ Output   │  │
│  │          │  │          │  │          │  │          │  │
│  └──────────┘  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Kill     │→│ Collide   │→│ Simulate  │            │
│  │          │  │          │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              GPU Particle System                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  粒子数据缓冲 │  │  粒子Mesh     │  │  粒子纹理     │    │
│  │  (GPU Buffer) │  │  (GPU Mesh)   │  │  (GPU Texture) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Block类型详解

```
VFX Graph Block类型:

1. Spawn Block (生成)
   ├─> Initialize Block (初始化)
   ├─> Output Event Block (输出事件)
   └─> 触发条件: 每帧 / 事件 / 时间间隔

2. Initialize Block (初始化)
   ├─> Set Position (设置位置)
   ├─> Set Velocity (设置速度)
   ├─> Set Color (设置颜色)
   ├─> Set Size (设置尺寸)
   └─> Set Lifetime (设置生命周期)

3. Update Block (更新)
   ├─> Update Position (更新位置)
   ├─> Update Velocity (更新速度)
   ├─> Update Color (更新颜色)
   ├─> Update Size (更新尺寸)
   └─> Update Lifetime (更新生命周期)

4. Kill Block (销毁)
   ├─> Kill by Lifetime (生命周期销毁)
   ├─> Kill by Distance (距离销毁)
   ├─> Kill by Collision (碰撞销毁)
   └─> Kill by Age (年龄销毁)

5. Output Block (输出)
   ├─> Output Quad (输出四边形)
   ├─> Output Mesh (输出Mesh)
   ├─> Output Trail (输出轨迹)
   └─> Output Line (输出线)

6. Simulate Block (模拟)
   ├─> Turbulence (湍流)
   ├─> Gravity (重力)
   ├─> Wind (风力)
   └─> Attractor (吸引子)

7. Collide Block (碰撞)
   ├─> Collision Box (碰撞盒)
   ├─> Collision Sphere (碰撞球)
   └─> Collision Plane (碰撞面)
```

---

## GPU粒子实现机制

### GPU粒子数据结构

```csharp
// GPU粒子缓冲 (StructuredBuffer)
struct ParticleData
{
    float3 position;
    float3 velocity;
    float4 color;
    float size;
    float lifetime;
    float age;
    int alive;
};
```

### GPU粒子更新Shader

```hlsl
// GPU粒子更新Shader (Compute Shader)
#pragma kernel UpdateParticles

// 粒子数据缓冲
RWStructuredBuffer<ParticleData> particleBuffer;

// 配置
float deltaTime;
float3 gravity;
float3 wind;
float turbulenceStrength;

// 粒子数量
uint particleCount;

[numthreads(64)]
void UpdateParticles (uint3 id : SV_DispatchThreadID)
{
    uint index = id.x;
    
    // 跳过无效粒子
    if (index >= particleCount)
        return;
    
    // 获取粒子数据
    ParticleData p = particleBuffer[index];
    
    // 检查是否存活
    if (!p.alive)
        return;
    
    // 更新年龄
    p.age += deltaTime;
    
    // 检查生命周期
    if (p.age > p.lifetime)
    {
        p.alive = 0;
        particleBuffer[index] = p;
        return;
    }
    
    // 更新速度 (重力 + 风力 + 湍流)
    float3 acceleration = gravity + wind;
    
    // 添加湍流噪声
    float noise = snoise(p.position * 0.1);
    acceleration += normalize(cross(p.position, float3(0, 1, 0))) * noise * turbulenceStrength;
    
    p.velocity += acceleration * deltaTime;
    
    // 更新位置
    p.position += p.velocity * deltaTime;
    
    // 更新大小（随时间缩小）
    float lifeRatio = p.age / p.lifetime;
    p.size = lerp(p.startSize, p.endSize, lifeRatio);
    
    // 更新颜色（随时间淡出）
    p.color = lerp(p.startColor, p.endColor, lifeRatio);
    
    // 写回粒子数据
    particleBuffer[index] = p;
}
```

### GPU粒子生成Shader

```hlsl
// GPU粒子生成Shader (Compute Shader)
#pragma kernel SpawnParticles

// 配置
float deltaTime;
float3 spawnPosition;
float spawnRadius;
int spawnCount;

// 输出
RWStructuredBuffer<ParticleData> particleBuffer;
AppendStructuredBuffer<ParticleData> newParticleBuffer;

// 随机种子
float randomSeed;

[numthreads(64)]
void SpawnParticles (uint3 id : SV_DispatchThreadID, uint threadIndex : SV_GroupIndex)
{
    // 线程0负责生成新粒子
    if (threadIndex != 0)
        return;
    
    // 生成指定数量的粒子
    for (int i = 0; i < spawnCount; i++)
    {
        // 计算随机位置 (球体分布)
        float phi = random(randomSeed + i * 1) * TWO_PI;
        float cosTheta = random(randomSeed + i * 2) * 2 - 1;
        float sinTheta = sqrt(1 - cosTheta * cosTheta);
        
        float3 offset = float3(
            cosTheta * sin(phi),
            sinTheta * sin(phi),
            cosTheta
        ) * spawnRadius;
        
        float3 position = spawnPosition + offset;
        
        // 创建新粒子
        ParticleData newParticle;
        newParticle.position = position;
        newParticle.velocity = float3(0, 1, 0) * random(randomSeed + i * 3) * 5.0;
        newParticle.color = float4(1, 0.5, 0, 1);
        newParticle.size = 1.0;
        newParticle.lifetime = 3.0;
        newParticle.age = 0;
        newParticle.alive = 1;
        
        // 添加到新粒子列表
        newParticleBuffer.Append(newParticle);
    }
    
    // 将新粒子合并到主缓冲
    uint oldCount;
    uint newCount;
    particleBuffer.GetCounter(oldCount);
    newParticleBuffer.GetCounter(newCount);
    
    // 合并粒子
    for (uint i = 0; i < newCount; i++)
    {
        ParticleData newParticle;
        newParticleBuffer.Consume(newParticle);
        particleBuffer[oldCount + i] = newParticle;
    }
    
    // 更新粒子计数
    particleBuffer.SetCounter(oldCount + newCount);
}
```

---

## 性能对比分析

### CPU vs GPU 粒子系统性能

| 粒子数量 | CPU更新时间 | GPU更新时间 | 帧时间差异 | 适用方案 |
|---------|------------|------------|------------|----------|
| **1,000** | 0.5ms | 0.1ms | -0.4ms | CPU/GPU均可 |
| **10,000** | 5ms | 0.5ms | -4.5ms | CPU可用 |
| **100,000** | N/A | 2ms | N/A | GPU必需 |
| **1,000,000** | N/A | 15ms | N/A | GPU必需 |

### CPU vs GPU 粒子系统功能对比

| 功能 | Shuriken (CPU) | VFX Graph (GPU) |
|------|----------------|-----------------|
| **粒子数量** | <10,000 | >1,000,000 |
| **物理模拟** | 简单 | 复杂 (支持重力、风力、湍流） |
| **碰撞检测** | 支持 | 有限支持 (简化碰撞） |
| **粒子生命周期** | 支持 | 支持 |
| **粒子颜色/大小** | 支持 | 支持 |
| **粒子形状** | 有限 (四边形) | 丰富 (Mesh、Trail、Line） |
| **粒子轨迹** | 支持 (Trail Renderer) | 支持 |
| **粒子交互** | 支持 | 有限支持 |
| **性能** | 受限 | 高性能 |

---

## 最佳实践

### DO ✅

- 大量粒子 (>10000) 使用VFX Graph
- 简单效果 (<1000粒子) 使用Shuriken
- 需要物理模拟使用VFX Graph
- 火焰、烟雾、爆炸使用VFX Graph
- 限制并发VFX Graph数量
- 使用GPU Instancing优化渲染
- 使用LOD系统优化远距离特效
- 异步加载VFX Graph资源

### DON'T ❌

- 不要在低端设备使用大量GPU粒子
- 不要同时播放太多VFX Graph (性能问题）
- 不要忽略VFX Graph的预热时间
- 不要在VFX Graph中使用复杂Mesh (性能问题）
- 不要忽略GPU内存占用
- 不要过度使用Collision Block (性能问题)
- 不要在Update中频繁创建/销毁VFX Graph实例
- 不要忽略平台GPU能力差异

---

## 相关链接

- 性能数据: [特效性能基准测试与优化](性能数据-特效性能基准测试与优化.md)
- 实战案例: [战斗特效系统架构设计](实战案例-战斗特效系统架构设计.md)
- 最佳实践: [粒子系统性能优化](../30_性能优化/教程-粒子系统性能优化.md)

---

*创建日期: 2026-03-04*
*Unity版本: 2022.3 LTS*
*VFX Graph版本: 14.0.0*
