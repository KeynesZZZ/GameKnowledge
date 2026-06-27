---
title: 【笔记】tolua入门与调用机制
tags: ["Unity", "热更新", "Lua", "tolua", "笔记"]
category: 高级主题
created: "2026-06-26"
updated: "2026-06-26"
description: toLua# 的定位、Wrap 绑定机制、LuaState 与 C#↔Lua 双向调用方式
status: 待验证
validation: 未实测
related: ["[[tolua专题索引]]", "[[【笔记】tolua性能与GC优化]]", "[[【设计原理】热更新方案对比]]"]
author: llm
---

# 【笔记】tolua入门与调用机制

> toLua# 的定位、Wrap 绑定机制、LuaState 与 C#↔Lua 双向调用方式。

## 文档定位

从底层绑定机制角度理解 toLua#（tolua#）这套 Unity Lua 方案：它如何把 C# 类型暴露给 Lua、C# 又如何调用 Lua。读完应能解释「为什么改了 C# 类要重新 Generate Wrap」「Lua 里 `CS.UnityEngine.Transform` 是怎么来的」。选型对比见 [[【设计原理】热更新方案对比]]，性能与 GC 见 [[【笔记】tolua性能与GC优化]]。

## 一、toLua# 是什么

toLua# 是 topameng 维护的 Unity Lua 框架（仓库 `topameng/tolua`），底层基于 LuaInterface，可挂 LuaJIT 2.1 或 Lua 5.1。它的核心价值是「把任意 C# 类型自动绑定到 Lua」，从而支持把业务逻辑写在 Lua 里、再通过下发 Lua 代码实现热更新。

> 与 xLua/HybridCLR 的本质差异：toLua# 是「在 Lua 里写逻辑」，C# 侧代码不可热更；xLua 的 Hotfix 可在运行时替换 C# 方法体；HybridCLR 则用原生 AOT+解释器直接跑 C#。详见 [[【设计原理】热更新方案对比]]。

## 二、核心：Wrap 机制

toLua# 不在运行时用反射去调用 C#（那样太慢），而是**为每个要导出的 C# 类型预生成一份静态绑定类（Wrap）**：

1. 在 `CustomSettings.cs` 的 `bindType` 数组里登记要导出的 C# 类型。
2. 通过 Unity 菜单 `Lua → Generate Wrap`，toLua# 反射这些类型，为每个类型生成一个 `[Type]Wrap` 静态类（如 `UnityEngine_TransformWrap`），其中包含一个 `Register` 方法，负责把方法/属性/字段以 Lua metatable 的形式压入 Lua 栈。
3. 运行时 `LuaBinder.Bind(L)` 依次调用所有 Wrap 的 `Register`，完成类型注册。

```csharp
// CustomSettings.cs —— 声明哪些 C# 类型要导出给 Lua
public static BindType[] bindType = {
    _GT(typeof(Transform)),
    _GT(typeof(GameObject)),
    _GT(typeof(Vector3)),
    // ... 新用到的 C# 类型必须加在这里
};
```

**关键推论**：Wrap 是 C# 代码，随 App 编译发布。因此「Lua 里新用到一个没登记的 C# 类型」在运行时会找不到该类型（典型报错 `attempt to index a nil value`）。这是热更最常见的坑，详见 [[【踩坑】tolua热更新常见坑]]。

## 三、LuaState：解释器实例

`LuaState` 封装了一个 `lua_State*` 指针，是 C# 侧操作 Lua 的入口：

```csharp
LuaState lua = new LuaState();
lua.Start();                                   // 打开标准库，注册所有 Wrap 类型
lua.DoString("print('hello from lua')");       // 执行字符串
lua.DoFile("main");                            // 执行脚本（按 _PACKAGE_PATH 查找）
lua.CheckTop();                                // 检查栈平衡
lua.Dispose();                                 // 释放
```

`LuaBinder.Bind(L)` 通常在 `Start()` 内部或紧随其后调用，把前面生成的 Wrap 全部注册进这个 Lua state。

## 四、C# 调用 Lua

```csharp
// 方式一：直接执行并拿返回值
object[] ret = lua.DoString("return 1 + 2");

// 方式二：拿到 LuaFunction 引用后反复 Call（推荐，避免重复查找）
LuaFunction add = lua.GetFunction("Add");
object[] r = add.Call(1, 2);   // 调用 Lua 里的 function Add(a, b)
```

> `GetFunction` 是一次表查找。热路径里应**缓存 `LuaFunction`/`LuaTable` 引用**而非每帧重新 Get，否则既慢又产生 GC。详见 [[【笔记】tolua性能与GC优化]]。

## 五、Lua 调用 C#

注册完成后，C# 类型在 Lua 里通过 `CS` 命名空间根访问：

```lua
-- CS 是 toLua# 注册的根，下面按命名空间展开
local go = CS.UnityEngine.GameObject("Cube")
go.transform.position = CS.UnityEngine.Vector3(0, 1, 0)

-- 注册过的静态方法 / 实例方法 / 属性都可直接用
local t = go:GetComponent(typeof(CS.UnityEngine.Transform))
```

`CS.UnityEngine.Transform` 这条链路上的每个节点，都来自对应 Wrap 在注册阶段往 Lua 里塞的 metatable。

## 六、值类型与对象引用

- **值类型**（Vector3/Quaternion/Color 等）：toLua# 对常用 Unity 值类型有快路径（用固定缓冲池减少分配），但每次跨边界仍有拷贝开销。
- **引用类型**：C# 对象传给 Lua 时，toLua# 通过一个 ObjectMap（int handle → C# 对象）维护引用，Lua 侧拿到的是 handle；被 Lua 持有的对象不会进 GC，直到 Lua 侧释放。

## 小结

| 概念 | 作用 | 热更含义 |
|------|------|----------|
| `CustomSettings.bindType` | 声明要导出的 C# 类型 | 加新 C# 类型需改它并重生成 Wrap |
| Wrap 类 | 为每个类型生成静态绑定，避免运行时反射 | C# 代码，**不可热更** |
| `LuaState` | Lua 解释器入口 | Lua 脚本可热更 |
| `CS.*` | Lua 侧访问 C# 类型的根 | 取决于 Wrap 是否已注册 |

## 相关链接

- [[tolua专题索引]]
- [[【笔记】tolua性能与GC优化]]
- [[【踩坑】tolua热更新常见坑]]
- [[【设计原理】热更新方案对比]]
- [[【教程】打包与热更新]]
