---
title: 【笔记】Lua语法速查
tags: ["Unity", "热更新", "Lua", "tolua", "笔记"]
category: 高级主题
created: "2026-06-26"
updated: "2026-06-26"
description: 面向 tolua/Unity 热更的 Lua 语法速查（以 Lua 5.1/LuaJIT 为准），含类型、运算符、table、metatable 面向对象与 C# 开发者易错点
status: 待验证
validation: 未实测
related: ["[[tolua专题索引]]", "[[【笔记】tolua入门与调用机制]]", "[[【笔记】tolua性能与GC优化]]"]
author: llm
---

# 【笔记】Lua语法速查

> 面向 tolua/Unity 热更的 Lua 语法速查，以 **Lua 5.1 / LuaJIT**（toLua# 默认）为准。

## 文档定位

写 toLua# 热更逻辑前需要的 Lua 语言基础。只讲语法要点与对 C# 开发者最易错的点，不讲 toLua# 绑定机制（见 [[【笔记】tolua入门与调用机制]]）。版本以 Lua 5.1 / LuaJIT 为准，版本差异处单独标注。

## 一、变量与作用域

```lua
x = 10          -- 默认是【全局变量】（除非用 local）
local y = 20    -- 局部变量，作用域到所在块结束
do
  local y = 1   -- 屏蔽外层 y
end
print(y)        -- 20
```

> **易错**：Lua 里忘写 `local` 就是全局变量，会污染 `_G` 且影响 JIT 优化。**默认都加 `local`**，需要全局时再显式声明。

## 二、数据类型

8 种：`nil`、`boolean`、`number`、`string`、`table`、`function`、`thread`（协程）、`userdata`（C/Lua 绑定的原生对象，toLua# 传过来的 C# 对象就是它）。

| 类型 | 说明 | 备注 |
|------|------|------|
| `nil` | 缺省值 | 判断「未定义」用 `== nil` |
| `boolean` | `true`/`false` | **只有 `false` 和 `nil` 为假**，`0`、`""` 都为真 |
| `number` | 数值 | Lua 5.1/LuaJIT 中**全是 double**（无整数子类型）；5.3+ 才有整数 |
| `string` | 不可变字节串 | `..` 连接，`#s` 取长度 |
| `table` | 唯一的结构 | 既当数组又当字典，见下 |
| `function` | 第一类值 | 可赋值、传参、返回 |
| `thread` | 协程 | `coroutine.create` 等 |
| `userdata` | 原生对象 | toLua# 的 C# 对象在 Lua 侧即 userdata |

> **给 C# 开发者**：Lua 5.1/LuaJIT 没有 `int`/`float` 之分，全是 double；没有 `&&`/`||`，用 `and`/`or`；没有 `!=`，用 `~=`。

## 三、运算符

```lua
-- 算术
1 + 2      -- 3
7 / 2      -- 3.5  （5.1 没有整数除法 //，5.3+ 才有）
2 ^ 10     -- 1024.0（幂，注意结果是浮点）
7 % 3      -- 1

-- 比较（注意 ~= 是不等）
a == b
a ~= b     -- 等价于 C# 的 !=
-- 大小只对 number/string 有定义

-- 逻辑（短路，返回的是操作数本身而非布尔）
a and b    -- a 为真则返回 b，否则返回 a
a or b     -- a 为真则返回 a，否则返回 b
nil or "default"   -- "default"
false or "default" -- "default"
0 or "x"    -- 0      （0 为真！）

-- 字符串连接
"Hello, " .. "Lua"   -- "Hello, Lua"

-- 长度
#t         -- table 的「数组部分」长度
#s         -- 字符串字节长度
```

> **常用惯用法**：
> - 默认值：`local name = arg or "default"`
> - 三元：`cond and x or y`（仅当 x 不为 false/nil 时等价三元；不保险时用 `if`）

## 四、控制流

```lua
-- 条件
if x > 0 then
  print("正")
elseif x == 0 then
  print("零")
else
  print("负")
end

-- 数值 for：for i = 起始, 终止[, 步长]
for i = 1, 5 do print(i) end       -- 1 2 3 4 5
for i = 10, 1, -2 do print(i) end  -- 10 8 6 4 2

-- 泛型 for
for k, v in pairs(t) do print(k, v) end   -- 遍历所有键（顺序不定）
for i, v in ipairs(t) do print(i, v) end  -- 只遍历数组部分 1..n，遇 nil 停

-- while / repeat
while x > 0 do x = x - 1 end
repeat x = x + 1 until x >= 10
```

> **易错**：Lua 5.1 **没有 `continue`**。LuaJIT/5.2+ 可用 `goto continue` 模拟（在循环末尾放 `::continue::`）。也没有 `switch`，常用 table 派发代替。

## 五、函数

```lua
-- 多返回值
local function divmod(a, b)
  return a // b, a % b   -- 5.1 无 //，写 math.floor(a/b)
end
local q, r = divmod(17, 5)

-- 可变参数
local function sum(...)
  local s = 0
  for _, v in ipairs({...}) do s = s + v end
  return s
end
sum(1, 2, 3)   -- 6

-- 匿名函数 / 第一类值
local add = function(a, b) return a + b end
local list = { function() end, function() end }

-- 方法调用语法糖：冒号隐式传 self
local obj = {hp = 100}
function obj:damage(n)        -- 等价 obj.damage = function(self, n)
  self.hp = self.hp - n
end
obj:damage(20)               -- 等价 obj.damage(obj, 20)
```

> `:` 与 `.` 的区别是 tolua 里调用 C# 方法的高频坑：C# 实例方法在 Lua 里用 `obj:Method()`（带 self），静态方法用 `CS.Type.StaticMethod()`（点）。

## 六、table（核心）

table 是 Lua 唯一的数据结构，既是数组又是字典：

```lua
-- 数组（注意：索引从 1 开始！）
local arr = {10, 20, 30}
print(arr[1])   -- 10   （不是 arr[0]）

-- 字典
local cfg = { name = "hero", hp = 100 }
print(cfg.name, cfg["hp"])   -- hero 100

-- 混用 + 显式键
local t = { "a", "b", x = 1, [5] = "five" }

-- 增删改
t.newKey = "v"      -- 新增
t.x = nil           -- 删除（赋 nil 即删除）
```

> **易错**：
> - **索引从 1 开始**，和 C# 数组/List 完全相反。
> - `#t` 只对「连续的正整数键 1..n」有意义，有空洞（中间 nil）时结果不确定。
> - `ipairs` 遇第一个 nil 即停，且只走数组部分；`pairs` 走全部键但顺序不定。需要有序遍历数组用 `ipairs` 或数值 `for`。

## 七、面向对象：metatable + `:` 糖

Lua 没有类，用 table + metatable 模拟：

```lua
local Hero = {}
Hero.__index = Hero            -- 关键：找不到字段时回退到 Hero 自己

function Hero.new(name, hp)
  local self = setmetatable({}, Hero)
  self.name = name
  self.hp = hp
  return self
end

function Hero:damage(n)        -- 方法，self 是实例
  self.hp = self.hp - n
end

local h = Hero.new("A", 100)
h:damage(30)
print(h.hp)                    -- 70
```

原理：`h` 没有 `damage` 字段时，Lua 查 `h` 的 metatable 的 `__index`，指向 `Hero`，于是找到 `Hero.damage`。把 `__index` 设成另一个 table 即实现「继承」。

常用元方法（metamethod）：

| 元方法 | 触发 |
|--------|------|
| `__index` | 读不存在的字段（继承/默认值） |
| `__newindex` | 写新字段（拦截赋值） |
| `__add`/`__sub`/`__mul`… | 运算符重载 `+ - *` |
| `__eq`/`__lt`/`__le` | `== < <=` |
| `__call` | 把 table 当函数调用 |
| `__tostring` | `tostring(t)` / print |

## 八、闭包与 upvalue

```lua
local function counter()
  local n = 0
  return function()       -- 闭包，捕获外层 n 作为 upvalue
    n = n + 1
    return n
  end
end
local c = counter()
print(c(), c(), c())      -- 1 2 3
```

闭包是 Lua 实现「私有状态」「回调」「迭代器」的核心手段，热更里大量用于事件回调与状态封装。

## 九、模块与 require

```lua
-- mymod.lua
local M = {}
function M.foo() print("foo") end
return M

-- 使用
local mymod = require("mymod")   -- 按 package.path 查找，只加载一次
mymod.foo()
```

toLua# 里 `require` 的搜索路径由 `LuaState` 的 `_PACKAGE_PATH` / searcher 决定，热更下发的 Lua 文件就是靠这套机制加载。

## 十、给 C# 开发者的易错点速查

| C# 习惯 | Lua 实际 | 正确写法 |
|---------|----------|----------|
| `a[0]` 首元素 | **索引从 1 开始** | `a[1]` |
| `a != b` | 没有 `!=` | `a ~= b` |
| `a && b` / `a \|\| b` | 没有 `&&`/`\|\|` | `a and b` / `a or b` |
| `s1 + s2` 拼串 | `+` 不是拼串 | `s1 .. s2` |
| `if (x)` 隐式布尔 | `0`/`""` 为真 | 显式 `if x ~= nil and x ~= false` |
| `int`/`float` | 全是 double | 注意 `7/2 == 3.5` |
| `continue` | 5.1 没有 | `goto continue`（LuaJIT） |
| `obj.Method()` | 实例方法要 self | `obj:Method()` |
| 位运算 `& \| ^ ~` | 5.1 没有 | LuaJIT 用 `bit.band` 等 |

## 相关链接

- [[tolua专题索引]]
- [[【笔记】tolua入门与调用机制]]
- [[【笔记】tolua性能与GC优化]]
- [[【踩坑】tolua热更新常见坑]]
