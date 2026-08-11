# 迁移与审查参考

> 配合 `../SKILL.md` 使用。日常编码看 SKILL.md 即可；本文档用于 **TypeScript → ArkTS 迁移**、**理解 ArkTS 与 TS 的本质差异**、**正式 Code Review**。

## 目录

- [TypeScript → ArkTS 迁移检查表](#typescript--arkts-迁移检查表)
- [ArkTS 与 TypeScript 的核心区别](#arkts-与-typescript-的核心区别)
- [最重要的开发规则（五大原则）](#最重要的开发规则五大原则)
- [Code Review 强制检查清单](#code-review-强制检查清单)

---

## TypeScript → ArkTS 迁移检查表

把 TypeScript 代码搬进 ArkTS 工程时，逐项排查。任何一项命中，都必须在迁移过程中改掉，不要"先跑起来再说"。

```
□ any
□ unknown
□ var
□ 解构（对象 / 数组）
□ for...in
□ 动态增加对象属性
□ delete
□ 动态属性访问（固定结构上用 obj[key]）
□ Object / Function 宽泛类型
□ @ts-ignore
□ @ts-nocheck
□ eval
□ new Function
□ 动态 this
□ bind / call / apply
□ 隐式类型转换（含 == 宽松比较）
□ 未初始化的类属性
□ 不明确的 null（未用 | null 或 ?）
□ JSON.parse 后未定型的动态数据
□ API 返回的 any
□ 模块循环依赖
□ TypeScript 特有的高级类型（条件类型 / 映射类型 / 模板字面量类型 / 类型体操）
□ 当前 ArkTS 编译器不支持的 TS 语法
```

### 迁移的正确顺序

```
先定义数据结构（interface / class / type / Record）
        ↓
再实现业务逻辑
        ↓
通过编译器检查
        ↓
最后运行
```

迁移不是"改后缀"，而是**重新建立数据模型**。原 TS 代码里所有依赖运行时动态行为的地方，都要先找到 ArkTS 类型系统内的等价方案，再落地。

---

## ArkTS 与 TypeScript 的核心区别

理解这个差异，能解释为什么同样的代码在 TS 里"没问题"、在 ArkTS 里不合格。

| 维度 | TypeScript | ArkTS |
|------|-----------|-------|
| 定位 | JavaScript 的超集 | HarmonyOS 应用开发语言 |
| 强调 | 动态能力兼容、开发灵活性、运行时行为 | 静态类型、确定的数据结构、编译期检查、运行性能 |
| 合格标准 | 能运行 → 可以接受 | 能通过正确的类型检查 **+** 符合语言限制 **+** 符合 HarmonyOS 运行环境 |

换句话说：

- **TypeScript** 的思维："TS 能运行就行""运行时不会有问题""属性后面再加""类型不对直接 as any"。
- **ArkTS** 的思维：上面这些全部不成立。代码必须先在编译期就站得住，再谈运行。

这也是为什么 ArkTS 不接受"把 TS 代码改个 `.ets` 后缀"——动态行为被砍掉后，原本靠运行时兜底的代码会直接编译失败，强行用 `any` 绕过又违背了 ArkTS 的设计初衷。

---

## 最重要的开发规则（五大原则）

ArkTS 开发必须遵循这五条原则。它们是 SKILL.md 里所有具体规则的源头。

### 第一原则：禁止逃避类型系统

不要使用 `any`、不必要的 `unknown`、`@ts-ignore`、`@ts-nocheck`、`as any`。这是底线。

### 第二原则：数据结构必须明确

优先用 `interface`、`class`、`type`、`Record` 表达数据。数据结构是 ArkTS 代码的地基，地基不明确，上层逻辑全是悬空的。

### 第三原则：避免动态对象操作

不要 `obj[key] = value`、`delete obj[key]`、`obj.newProperty = value`——除非对象本身明确声明为适合动态访问的 `Record` 类型。

### 第四原则：避免 TypeScript 动态语法

尤其注意：解构、`for...in`、动态 `this`、`bind/call/apply`、隐式类型转换、动态代码执行（`eval` / `new Function`）。这些都是从 TS 搬过来最容易踩的坑。

### 第五原则：类型问题优先从设计上解决

推荐的链路：

```
正确的数据模型
    ↓
正确的函数签名
    ↓
正确的 API 类型
    ↓
类型推断
    ↓
必要时类型断言
```

而不是：

```
编译报错 → as any → @ts-ignore
```

前者是"设计驱动"，后者是"报错驱动"。ArkTS 要求前者。

---

## Code Review 强制检查清单

每次新增或修改 ArkTS 代码时，Code Review 必须覆盖以下条目。和 SKILL.md 末尾的"交付前自检清单"相比，这里是**审查者视角**的完整版：

1. 是否存在 `any`
2. 是否存在不必要的 `unknown`
3. 是否存在 `@ts-ignore`
4. 是否存在 `@ts-nocheck`
5. 是否存在解构
6. 是否存在 `for...in`
7. 是否存在动态增加对象属性
8. 是否存在 `delete`
9. 是否存在动态 `this`
10. 是否存在 `bind` / `call` / `apply`
11. 是否存在隐式类型转换
12. 类属性是否初始化
13. `null` 是否明确声明
14. API 数据是否类型化
15. JSON 数据是否类型化
16. 是否使用宽泛的 `Object` / `Function`
17. 是否存在动态代码执行（`eval` / `new Function` / `with`）
18. 是否存在循环依赖
19. 是否使用了当前 ArkTS 编译器不支持的 TypeScript 语法
20. 是否可以通过更好的类型设计减少 `as` 断言

第 20 条尤其值得审查者关注：`as` 用得多，往往不是断言的问题，而是**上游数据模型没定义好**的症状。审查时应追问"这个 `as` 能不能用一个 interface 消掉"。
