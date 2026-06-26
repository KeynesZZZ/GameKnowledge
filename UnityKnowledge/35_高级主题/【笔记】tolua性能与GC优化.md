---
title: 【笔记】tolua性能与GC优化
tags: ["Unity", "热更新", "Lua", "tolua", "性能优化", "笔记"]
category: 高级主题
created: "2026-06-26"
updated: "2026-06-26"
description: toLua# C#↔Lua 边界的调用开销、GC 来源、LuaJIT 平台差异与优化手段
status: 待验证
validation: 未实测
related: ["[[tolua专题索引]]", "[[【笔记】tolua入门与调用机制]]", "[[【踩坑】tolua热更新常见坑]]"]
author: llm
---

# 【笔记】tolua性能与GC优化

> toLua# C#↔Lua 边界的调用开销、GC 来源、LuaJIT 平台差异与优化手段。

## 文档定位

承接 [[【笔记】tolua入门与调用机制]]，聚焦「跨语言调用到底贵在哪、怎么减少 GC」。落地踩坑见 [[【踩坑】tolua热更新常见坑]]。

## 一、开销在边界上

toLua# 的性能瓶颈不在 Lua 本身的执行（LuaJIT 跑得很快），而在**每一次 C#↔Lua 边界跨越**：

- **入参转换**：C# 调 Lua 时，参数要逐一压到 Lua 栈；Lua 调 C# 时，Wrap 要从栈上取参并转成 C# 类型。
- **返回值转换**：同理反向。
- **对象引用维护**：传 C# 对象给 Lua 要查/建 ObjectMap handle；struct（Vector3 等）要拷贝或走缓冲池。

因此性能优化的总原则只有一条：**减少跨边界调用的次数与每次的代价**。

## 二、GC 来源（按频次）

| 来源 | 触发 | 量级 |
|------|------|------|
| `GetFunction`/`GetTable` | 每次按名字查 Lua 全局表 | 每帧多次则累积 |
| 值类型封送 | 每次传 Vector3 等 struct（非快路径时） | 高频调用显著 |
| 字符串拷贝 | C# string ↔ Lua string 转换 | 高频传字符串明显 |
| 装箱 | 枚举/对象用 `object` 传递时 | 隐蔽但持续 |
| delegate 包装 | Lua 注册 C# 回调 / 事件 += | 每次创建新 delegate |

在 Deep Profiler 里，典型调用栈会看到 `LuaInterface.LuaFunction.Call`、`ToLua.LuaToCSByString`、`ToLua.Push` 等，GC 都来自这条边界路径。

## 三、优化手段

### 1. 缓存 LuaFunction / LuaTable

```csharp
// ❌ 每帧重复查找 + GC
void Update() {
    lua.GetFunction("OnUpdate").Call(Time.deltaTime);
}

// ✅ 缓存引用，热路径只 Call
LuaFunction onUpdate;
void Start() { onUpdate = lua.GetFunction("OnUpdate"); }
void Update() { onUpdate.Call(Time.deltaTime); }
```

### 2. 批处理，降低跨边界频率

与其在 C# 里循环 1000 次每次调一次 Lua，不如把数据打包成一次调用，让循环在 Lua 内部完成。

```lua
-- 一次传入一帧的所有事件，Lua 内部遍历
function OnEventsBatch(events)
    for _, e in ipairs(events) do handle(e) end
end
```

### 3. 避免 Update 里高频小调用

`Update` 里每帧调 Lua 几十次是常见的隐形热点。能合并就合并，能用 C# 缓存状态就别每帧问 Lua。

### 4. 注意值类型

toLua# 对 Vector3/Quaternion/Vector2/Color 有固定缓冲快路径，但仍要控制频率；避免在边界上来回传递大 struct 数组。

### 5. 善用 LuaTable 池化

频繁构造临时 LuaTable 当参数会持续 GC，可复用 table。

## 四、LuaJIT 与平台差异（关键）

- **Android / Windows / Editor**：LuaJIT 可开启 JIT，Lua 执行接近原生速度。
- **iOS**：系统禁止可写可执行内存（W^X），**LuaJIT 的 JIT 被禁用，退回解释器模式**。Lua 仍能跑，但没有 JIT 加速。
- **推论**：iOS 上「Lua 逻辑热更」的执行效率明显低于 Android 的 JIT 模式，热点逻辑在 iOS 上可能成为帧率瓶颈。这是很多团队从 toLua# 迁移到 xLua（同样受此限制，但有 Hotfix）或 HybridCLR（原生 C#，无 Lua）的重要原因。

> 因此评估 toLua# 性能时，**务必以 iOS 解释器模式为基准**，不要拿 Editor/Android 的 JIT 数据外推。

## 五、定位流程

1. Deep Profiler 取一段 gameplay，按 GC Alloc 排序。
2. 聚焦 `LuaFunction.Call` / `ToLua.*` 调用栈，确认是否边界调用过频。
3. 对热点改用「缓存引用 + 批处理」，再对比 GC 与耗时。

## 相关链接

- [[tolua专题索引]]
- [[【笔记】tolua入门与调用机制]]
- [[【踩坑】tolua热更新常见坑]]
- [[【设计原理】热更新方案对比]]
