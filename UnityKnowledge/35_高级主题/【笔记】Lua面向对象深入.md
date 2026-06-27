---
title: 【笔记】Lua面向对象深入
tags: ["Unity", "热更新", "Lua", "tolua", "笔记"]
category: 高级主题
created: "2026-06-27"
updated: "2026-06-27"
description: 深入剖析 Lua 面向对象的 __index 查找机制、self 本质、生产级 class 实现、继承/super、读写不对称、原型 vs 闭包范式与性能代价
status: 待验证
validation: 未实测
related: ["[[tolua专题索引]]", "[[【笔记】Lua语法速查]]", "[[【笔记】tolua入门与调用机制]]", "[[【笔记】tolua性能与GC优化]]", "[[【踩坑】tolua热更新常见坑]]"]
author: llm
---

# 【笔记】Lua面向对象深入

> 把 Lua 的"面向对象"从语法糖讲到底层机制：`__index` 查找、`self` 本质、生产级 class、继承/super、读写不对称、原型 vs 闭包、性能代价。

## 文档定位

[[【笔记】Lua语法速查]] 第七节用 ~25 行给了 metatable OOP 的基础（`Hero` 例子 + `__index` 一句话原理）。本文在其基础上**深入到机制层**，解释"为什么这样写就能面向对象"。面向需要写/读 toLua# 热更里复杂 Lua OOP 框架的开发者。版本以 Lua 5.1 / LuaJIT（toLua# 默认）为准。

---

## 一、本质（3 句话）

1. **Lua 没有类、没有 `this`、没有继承关键字**。所谓 OOP，是「**table 当对象 + metatable 当类 + `__index` 当继承链**」用约定模拟出来的。
2. 一切都是 **table 的键**：字段是键、方法是键、类变量是键。没有 C# 那种"字段 vs 方法 vs 静态成员"的声明区分，全靠**访问语义**自然分化。
3. OOP 的全部魔法来自一个元方法：`__index`。理解 `__index` 的查找规则，就理解了 Lua OOP 的 90%。

---

## 二、`__index` 查找机制：读路径深度剖析

这是核心。**读 `t.k`（`t` 是 table）时，Lua 的完整算法：**

```
读 t.k：
  1. 看 t 本身有没有键 k → 有就直接返回
  2. 没有 → 看 t 有没有 metatable
     2a. 没有 metatable → 返回 nil
     2b. 有 metatable → 取它的 __index 字段：
         - 若 __index 是 table → 对【这个 table】重复步骤 1（递归）
         - 若 __index 是 function → 调用 __index(t, k)，用返回值
         - 若 __index 是 nil → 返回 nil
```

**关键认知：`__index` 只在"读到一个 `t` 里不存在的键"时才触发**，它是一个**回退兜底**，不是每次访问都走。

经典写法里这行是命门：

```lua
local Hero = {}
Hero.__index = Hero          -- 为什么"自己指向自己"？见下
```

为什么 `Hero.__index = Hero`？因为要让**实例的 metatable 是 `Hero`**，而实例访问方法时要回退到 `Hero`：

```lua
local h = setmetatable({}, Hero)   -- h 的 metatable = Hero
h:damage(10)
-- 读 h.damage：
--   1. h 本身没有 damage
--   2. h 的 metatable = Hero，取 Hero.__index = Hero
--   3. 在 Hero 里找 damage → 找到
```

`Hero.__index = Hero` 之所以成立，是因为设成自身后，「实例 → metatable(Hero) → Hero.__index(Hero) → Hero 里的方法」形成闭环。**`__index` 指向谁，谁就是"方法仓库"**。

> `__index` 还可以是 function——用于**动态查找/惰性属性/多继承**。原型委托式 OOP 用 table 形式；要按名字算派发就用 function 形式。

---

## 三、`self` 的真相：它就是第一个参数

Lua 没有 `this`。`:` 只是语法糖，**隐式把调用者作为第一个参数传进去**：

```lua
function Hero:damage(n)      -- 等价 function Hero.damage(self, n)
    self.hp = self.hp - n
end

h:damage(10)                 -- 等价 h.damage(h, 10)
h.damage(h, 10)              -- 完全等价
```

`self` 没有任何特殊地位，就是个普通局部变量，名字碰巧叫 `self`。这带来**类方法 vs 实例方法**的区分，全靠**用 `.` 还是 `:` 调用、接收者是谁**决定：

| 写法 | self 是谁 | 语义 |
|------|-----------|------|
| `Hero.new(...)` | nil（没人传） | 「静态/类方法」——通常返回一个新实例 |
| `Hero:new(...)` | `Hero` 自己 | 也是构造，但 self=类，便于继承时 `SubClass:new()` 自动用 SubClass |
| `h:damage(10)` | `h`（实例） | 「实例方法」——操作实例状态 |

`Hero.new`（点）和 `Hero:new`（冒号）都能做构造，差别在 `self`：用 `:` 时 `SubClass:new()` 里 `self` 是 `SubClass`，`setmetatable(o, self)` 会让实例的元表是子类——**这是继承能"复制"构造行为的关键**。所以**可被继承的类，构造器一律用 `:`**。

---

## 四、一个生产级 class 实现（逐行剖析）

[[【笔记】Lua语法速查]] 里的 `Hero` 是裸写。真实项目里大家会封装一个 `class()` 函数。下面是最小但完整的版本，支持继承、构造、super：

```lua
local function class(base)
    local cls = {}
    cls.base = base                                   -- 记住父类，供 super 查找

    if base then
        setmetatable(cls, { __index = base })         -- ① 类继承：cls 找不到的字段回退到 base
    end

    cls.__index = cls                                 -- ② 实例的 __index 指向 cls（方法仓库）

    function cls.new(...)                             -- ③ 构造器（用 . 调，self 不参与）
        local obj = setmetatable({}, cls)             --    实例的元表 = cls
        if obj.ctor then obj:ctor(...) end            --    自动调构造（obj.ctor 经继承链找到）
        return obj
    end

    return cls
end
```

**继承链 `instance → cls → base` 是怎么搭起来的**（最该想通的一点）：

```
obj 的 metatable = cls                   （setmetatable({}, cls)）
cls 的 metatable = {__index = base}      （继承时设的）

读 obj.foo：
  obj 没有 → 元表 cls 的 __index(=cls) → 查 cls
  cls 没有 → 元表 {__index=base} → 查 base
```

`cls.__index = cls`（实例向 cls 查方法）和 `setmetatable(cls, {__index=base})`（cls 向 base 查方法）是**两条不同方向**的委托链，拼起来才是完整继承。很多人写 OOP 框架出错，就是混淆了这两条。

**使用：**

```lua
local Animal = class()
function Animal:ctor(name) self.name = name end
function Animal:speak() return self.name .. " makes a sound" end

local Dog = class(Animal)                            -- 继承
function Dog:ctor(name, breed)
    self.base.ctor(self, name)                       -- super：调父类 ctor（见下坑）
    self.breed = breed
end
function Dog:speak() return self.name .. " barks" end   -- override

local d = Dog.new("Rex", "Lab")
print(d:speak())   -- Rex barks
```

---

## 五、super 的正确写法（高频坑）

Lua 没有 `base()` 关键字，调父类方法要手动：

```lua
function Dog:speak()
    -- ❌ 错：self.base:speak()
    --       等价 self.base.speak(self.base)，self 变成了 base，丢了 Dog 的状态
    -- ✅ 对：显式传 self
    self.base.speak(self)                            -- 或 Animal.speak(self)
    print(self.name .. " barks")
end
```

**铁律：调父类方法一律用 `.` 并手动传 `self`**，即 `self.base.method(self, ...)`。用 `:` 会让 self 变成父类表，状态错乱。多继承时 `base` 只能记一个，需要额外结构。

---

## 六、读 vs 写的不对称：`__index` vs `__newindex`

**这是 Lua OOP 和 C# 字段语义最大的差异**，很多人没意识到。

- **读** `t.k`：找不到 → 走 `__index` 委托（继承生效）
- **写** `t.k = v`：默认**直接在 `t` 上新建/覆盖键**，不经过父类、不委托

后果："实例字段覆盖类默认值"是自动发生的，但反之类变量不会被实例修改：

```lua
local Base = class()
Base.tag = "default"          -- 类默认值（所有实例共享读到它）

local a = Base.new()
print(a.tag)                  -- "default"（a 没有 tag，经 __index 读到 Base.tag）

a.tag = "mine"                -- 写！→ 在 a 上新建实例字段 tag，Base.tag 不变
print(a.tag)                  -- "mine"
print(Base.tag)               -- "default"   ← 类没被动
local b = Base.new()
print(b.tag)                  -- "default"   ← 新实例仍读类默认
```

这正好是 C# 里"实例字段遮蔽静态默认值"的效果，但 Lua 是**靠"读委托 + 写实例"的机制副作用**自然涌现的——没有任何额外声明。

**陷阱**：以为"在实例上改值会同步到类/所有实例"会踩坑。要让赋值也委托（写实例时转发到共享表），得用 `__newindex` 拦截，但通常不需要，理解这套语义即可。

---

## 七、两种 OOP 范式：原型委托 vs 闭包封装

上面都是**原型委托式**（metatable + `__index`），是 Lua 主流。还有**闭包式**，特点完全不同：

```lua
local function makeAccount(balance)
    -- balance 是 upvalue，外部【完全无法】直接访问 → 真私有
    return {
        deposit  = function(n) balance = balance + n end,
        withdraw = function(n) assert(n <= balance, "不足"); balance = balance - n end,
        get      = function() return balance end,
    }
end

local acc = makeAccount(100)
acc.deposit(50)
print(acc.get())              -- 150
print(acc.balance)            -- nil ！外部访问不到，真·private
```

| | 原型委托式（metatable） | 闭包式（closure） |
|---|---|---|
| 私有性 | **无**（约定 `_field` 或 `__newindex` 拦截） | **真私有**（upvalue 不可见） |
| 继承 | 天然支持（`__index` 链） | 不支持（要手动委托） |
| 每实例内存 | 小（方法共享，元表一份） | 大（**每个实例的每个方法都是独立闭包**） |
| 适用 | 大量同类对象、需要继承的领域模型 | 小而强封装的对象、状态机、迭代器 |

**热更实战里，主业务对象用原型式**（要继承、要省内存）；**事件回调/小型状态封装用闭包**。混用是常态。

---

## 八、访问控制与"接口"：Lua 没有的东西

- **private**：Lua 无关键字。约定 `_field`（下划线前缀=别碰）；要真私有就用闭包式或 `__newindex` 拦截写、`__index` 拦截读。
- **readonly**：用 `__newindex` 拦截赋值并报错。
- **interface / abstract**：**不存在**。Lua 是 **duck typing**——`walk()` 调用不关心你是什么类，只要有 `walk` 字段就行。"接口"靠 metatable 声明 + 运行时检查模拟：
  ```lua
  -- 假装 IDamageable：检查 obj 是否有 TakeDamage 方法
  local function implementsIDamageable(obj)
      return type(obj.TakeDamage) == "function"
  end
  ```
- **多态**：天然有——`d:speak()` 走各自类的方法，无需 `virtual`/`override` 关键字。

---

## 九、`.` vs `:` 最深的坑（C# 开发者必踩）

[[【笔记】Lua语法速查]] 提过一句，这里演示错误有多隐蔽：

```lua
function Hero:greet() print("hi " .. self.name) end

local h = Hero.new("A")        -- 假设构造已就绪
h.greet()                      -- ❌ 用 . 调，没传 self
-- → greet 的 self = 第一个实参 = nil
-- → self.name 报 attempt to index a nil value
```

更阴险的是**漏 self 不一定立刻崩**——方法体里没用到 `self` 时它"看起来"正常，直到某天加了 `self.xxx` 才炸。toLua# 里调 C# 实例方法同理：**实例方法用 `:`，静态方法用 `.`**（见 [[【笔记】Lua语法速查]] 第十节）。

---

## 十、性能代价

原型式 OOP 每次方法调用 `obj:m()` 都要走 metatable 链：

```
取 obj 的 metatable → 取 __index → 在 cls 哈希查 m
  → 没有再取 cls 的 metatable → ... 递归到找到
```

- 继承深度 D，最坏 **D 次元表查找 + D 次哈希查找** 才定位到方法。
- **iOS 上 LuaJIT 无 JIT**（见 [[【踩坑】tolua热更新常见坑]] 坑 2），这些查找全是解释器开销。深继承 + 热点方法（每帧调）会累积成帧率瓶颈。
- **优化手段**：
  - 局部化热点方法：`local speak = Dog.speak` 后 `speak(dog)`（脱离 metatable 查找）。
  - **控制继承深度**，热点对象别搞 5 层继承。
  - 注意：这比"跨 C#↔Lua 边界"的开销小一个量级——OOP 内部查找是次要矛盾，主要矛盾仍是边界次数（见 [[【笔记】tolua性能与GC优化]]）。但纯 Lua 密集逻辑里它就是主因。

---

## 十一、tolua / Unity 热更语境下的三点提醒

1. **C# 对象在 Lua 里是 `userdata`，不是 Lua table**。不能给 `CS.UnityEngine.Transform` 加 metatable 搞"继承"——它是宿主对象，OOP 规则不适用。**Lua OOP 只针对纯 Lua 端的对象**。绑定机制见 [[【笔记】tolua入门与调用机制]]。
2. **"会变的逻辑放 Lua"**：Lua 端的类、继承、多态都是纯 Lua，**不受 C# 重编译影响**——这正是热更的价值。但一旦 Lua 调用的 C# 接口签名变了，wrap 就对不上（[[【踩坑】tolua热更新常见坑]] 坑 3）。所以 Lua OOP 框架要**只依赖稳定的 C# 接口**。
3. **多数项目不裸写 `class()`**：用现成 OOP 库（lua-oo、xLua/slua 自带、30lines 风格的 class）。原理都是上面这套，理解机制后看任何库的源码都通透。方案选型见 [[【设计原理】热更新方案对比]]。

---

## 十二、速查：C# OOP vs Lua OOP

| C# | Lua 对应 | 怎么实现 |
|----|----------|----------|
| `class Foo {}` | `Foo = class()` | table + metatable |
| `new Foo()` | `Foo.new()` | `setmetatable({}, Foo)` |
| `this` | `self`（语法糖隐式传） | `:` 调用 |
| `class Foo : Bar` | `class(Bar)` | `setmetatable(cls, {__index=Bar})` |
| `base()` | `self.base.method(self)` | 手动，**必须用 `.`** |
| `virtual/override` | 无关键字，重定义方法即可 | duck typing 天然多态 |
| `private` | 无 | `_field` 约定 / 闭包式 / `__newindex` |
| `static` | 类 table 上的字段 | `Foo.sharedVal` |
| `interface` | 无 | duck typing + 运行时检查 |

---

## 相关链接

- [[tolua专题索引]]
- [[【笔记】Lua语法速查]] —— OOP 基础（本文在其上深入）
- [[【笔记】tolua入门与调用机制]] —— C# 对象如何以 userdata 暴露给 Lua
- [[【笔记】tolua性能与GC优化]] —— 边界开销是主因，OOP 查找是次因
- [[【踩坑】tolua热更新常见坑]] —— iOS 无 JIT、C# 签名变更等坑
