---
name: harmonyos-arkts
description: HarmonyOS ArkTS 代码开发规范、合规审查与编译排错。只要任务涉及编写、修改、重构 ArkTS / .ets 文件，审核/检查现有 ArkTS 代码是否符合规范，把 TypeScript 迁移到 ArkTS，或处理 ArkTS 编译报错，就必须使用本技能——即使用户没有明确要求。提供硬性规则、TypeScript→ArkTS 决策表、修改已有代码守则、编译错误处理流程、机械审查脚本与分级 Code Review 报告。HarmonyOS / 鸿蒙开发、ArkTS 代码审查、TS→ArkTS 迁移、.ets 编译错误均应触发。边界：本技能只管 ArkTS「语言层」规则；ArkUI 状态管理（@State / @Prop / @Builder 等）属于独立技能，不要混淆。
---

# ArkTS 开发规范

## 1. 触发条件

只要满足以下任一情况，本技能的规则就默认生效（即使用户没说"按规范来"）：

- 编写、修改、重构 ArkTS / `.ets` 文件
- 审查 / 审核 / 检查现有 ArkTS 代码是否符合规范（Code Review、合规体检）
- 把 TypeScript / JavaScript 代码迁移到 ArkTS
- 处理 ArkTS 编译报错
- HarmonyOS / 鸿蒙应用开发中涉及 `.ets` 的任务

> 边界：ArkUI 声明式 UI 与状态管理（`@State` / `@Prop` / `@Link` / `@Builder` / `@Provide` / `@Consume` 等）属于独立技能，本技能**不覆盖**。不要把 ArkUI 状态管理规则和这里的语言层规则混在一起。

## 2. 适用范围

- 所有 `.ets` 文件里的 ArkTS 代码。
- 普通业务逻辑、数据模型、工具类、网络层等**语言层**代码。
- `.ts` / `.js` 与 ArkTS 的交互边界。
- 不适用：ArkUI 组件声明与状态管理（见独立技能）、原生 TS/JS 工程代码。

默认目标语言是 **ArkTS，不是普通 TypeScript**。不要把 TS 代码改个后缀就当作迁移完成。

---

## 3. 核心原则

### 3.1 为什么 ArkTS 要限制动态特性

ArkTS 基于 TypeScript，但刻意砍掉了一批动态特性。原因不是保守，而是目标不同：

- **编译期确定性**：HarmonyOS 要求编译器在打包阶段就掌握所有类型与对象结构，才能深度优化、提前排错。
- **运行时性能**：依赖运行时动态行为的代码（反射式属性增删、动态 `this`、`eval`）无法被静态优化，在端侧设备上代价很高。
- **可维护性**：固定结构 + 显式类型，重构时编译器能帮你兜底，而不是等线上崩。

理解了这一点，下面所有"禁止 X"就不再是死记硬背——它们都是为"让一切在编译期确定"服务。

### 3.2 心智模型

把每一段 ArkTS 代码往这个方向推：

```
动态       →  静态         （运行时才知道的，改成编译期就知道的）
隐式       →  显式         （推断不明确的地方，写出来）
不确定     →  明确类型     （不要 any，要 interface / class / type / Record）
运行时判断  →  编译期检查   （类型设计替代 as any）
动态对象    →  固定数据模型 （不要 obj[key]，要明确的字段）
```

### 3.3 五大原则

1. **禁止逃避类型系统**：不用 `any`、不必要的 `unknown`、`@ts-ignore`、`as any`。
2. **数据结构必须明确**：优先 `interface` / `class` / `type` / `Record`。
3. **避免动态对象操作**：不增删属性、不 `delete`、不 `obj.newProp`（除非对象明确是 `Record`）。
4. **避免 TS 动态语法**：不解构、不用 `for...in`、不动态 `this`、不隐式转换。
5. **类型问题优先从设计上解决**：修数据模型 > 修函数签名 > 修 API 类型 > 类型推断 > 必要时 `as`。

### 3.4 红线（绝对禁止，看到就改）

这些写法**任何时候**都不允许，包括"先临时跑通"：

| 禁止 | 替代 |
|------|------|
| `any`（含 `as any`、`x: any`、`<any>`） | `interface` / `class` / `type` / `Record` |
| `// @ts-ignore` / `// @ts-nocheck` | 修复类型 / 结构 |
| `eval()` / `new Function()` | 明确的逻辑 / 函数定义 |
| `with (obj) {}` | 显式访问对象属性 |
| `var` | `const`（优先）/ `let` |
| `throw '字符串'` / `throw 500` | `throw new Error(...)` |
| `new Proxy()` 自造响应式 | ArkUI 官方状态管理（`@State` 等） |

> 遇到编译错误的第一反应永远是**修类型 / 修结构**，不是绕过编译器（见第 7 节）。

---

## 4. 硬性规则

### 4.1 类型

**禁止 any，慎用 unknown。** 不要用 `any` 消错误；`unknown` 也不要当 `any` 的替身：

```ts
// ✕
const data: any = response
let value: unknown

// ✓
interface UserInfo { name: string; age: number }
const data: UserInfo = response
let value: string | number
```

**选对数据结构：**

- 数据模型（尤其 API 返回）→ `interface`
- 类型别名、联合类型、可空类型 → `type`
- 需要行为、封装、继承 → `class`
- 动态键值（HTTP header、字典）→ `Record<string, T>`

```ts
type RequestStatus = 'loading' | 'success' | 'error'
const headers: Record<string, string> = { 'Content-Type': 'application/json' }
```

**该写类型的地方不要靠推断。** 局部简单变量可省略；但公共变量、类属性、函数参数、函数返回值、API 数据、状态变量、集合都必须显式声明。

**类属性必须在构造完成后有确定值：**

```ts
// ✕
class User { name: string; age: number }

// ✓
class User {
  name: string = ''
  age: number = 0
  constructor(name: string, age: number) { this.name = name; this.age = age }
}
```

不要用 TS 参数属性简写（`constructor(public name: string)`），要显式声明属性。

**空值必须显式。** 不要把 `null` 塞进非空类型；可选字段用 `?`：

```ts
let user: UserInfo | null = null
interface UserInfo { name: string; avatar?: string }
```

**集合必须带类型参数：**

```ts
const users: UserInfo[] = []                 // 项目统一用 T[]，不用 Array<T>
const userMap: Map<number, UserInfo> = new Map()
const idSet: Set<number> = new Set()
```

**类型断言用 `as`，不用 `<T>`，但不滥用。** 连续 `as` 是类型设计缺陷的信号：

```ts
const user = data as UserInfo      // ✓
const user = <UserInfo>data        // ✕
```

类型处理优先级：`正确的类型定义 → 类型推断 → 联合类型 → 类型守卫 → as → 禁止 any`。

**显式类型转换，禁止隐式转换和宽松比较：**

```ts
// ✕
const n = +'123'
if (id == '123') {}

// ✓
const n: number = Number.parseInt('123', 10)
if (id === 123) {}
```

**不要写类型体操。** 条件类型、映射类型、模板字面量类型等复杂高级类型不用于核心业务。类型难读 = 数据模型该简化。泛型可以用，但要简单明确（如 `interface PageResult<T> { list: T[]; total: number }`）。

**数据边界要定型。** API 和 `JSON.parse` 的返回必须在出口就定型，不要让动态数据在业务层传播：

```ts
// ✕
const data: any = await request()
const parsed: any = JSON.parse(json)

// ✓
const data: UserInfo = await request()
function parseUser(json: string): UserInfo { return JSON.parse(json) as UserInfo }
```

**禁止宽泛 `Object` / `Function`：**

```ts
// ✕
const obj: Object = {}
let cb: Function

// ✓
const obj: Record<string, string> = {}
let cb: (value: string) => void
```

`enum`、`readonly` 按需使用，不要为用而用。

### 4.2 对象

**对象结构固定，禁止动态变形。** 对象一旦创建，结构就固定：

```ts
// ✕ 事后增删属性
const user = { name: 'Tom' }
user.age = 18
delete user.name

// ✓ 字段写进类型；可能不存在用 ?；key 真动态用 Record
interface UserInfo { name: string; age: number; avatar?: string }
```

> 核心判断：**固定结构用 interface/class；动态结构用 Record。** 拿不准就问"这些 key 现在能全列出来吗"。

**禁止解构 → 逐个赋值：**

```ts
// ✕
const { name, age } = user
const [first, second] = list

// ✓
const name: string = user.name
const first: UserInfo = list[0]
```

**禁止 `for...in` → `Object.keys()` + `for...of`：**

```ts
// ✕
for (const key in object) { console.info(key) }

// ✓
const keys: string[] = Object.keys(object)
for (const key of keys) { console.info(key) }
```

**固定结构禁止动态属性访问：**

```ts
// ✕
const key = 'name'
const value = user[key]

// ✓
const value: string = user.name
// （只有 Record 类型的对象才能用 data[key]）
```

遍历对象用 `Object.keys` / `Object.entries` / `Object.values`，但对象本身要有明确类型。`Reflect`、`Symbol` 扩展对象、`Proxy` 自造响应式都不要用（见红线）。

### 4.3 函数

**签名必须完整。** 参数类型、返回值类型都要写；公共方法和返回值类型是强制项：

```ts
// ✕
function getUser(id) {}
async function getData() {}

// ✓
function getUser(id: number): UserInfo { /* ... */ }
async function getData(): Promise<UserInfo> { /* ... */ }
function logout(): void {}
```

**回调优先箭头函数：**

```ts
const callback = (value: string): void => { console.info(value) }
users.forEach((user: UserInfo): void => { console.info(user.name) })
```

**不要动态 `this`。** 不用 `bind` / `call` / `apply` 改变 `this`，用箭头闭包明确指向：

```ts
// ✕
const fn = obj.method.bind(obj)

// ✓
const fn = (): void => { obj.method() }
```

### 4.4 异步与错误

**Promise 必须带类型，async/await 优先于 `.then` 链：**

```ts
async function loadUser(): Promise<UserInfo> {
  const user: UserInfo = await getUser()
  return user
}
```

**异常必须是 `Error` 或其子类；用 `try/catch` 捕获，不要依赖动态异常类型：**

```ts
// ✕
throw 'User not found'
throw 500

// ✓
throw new Error('User not found')

class BusinessError extends Error {
  code: number = 0
  constructor(code: number, message: string) { super(message); this.code = code }
}

try {
  await loadData()
} catch (error) {
  console.error(`load data failed: ${error}`)
}
```

### 4.5 模块

**明确导入，依赖单向，禁止循环依赖：**

```
Page → Service → Model        （公共逻辑抽到 Utils / Common / Model）
禁止 A → B → C → A；底层模块不反向依赖 UI 模块。
```

不要用动态 `import()` 路径做业务模块动态加载，除非当前版本明确支持且确有需要。

**`.ets` 与 `.ts` / `.js` 的边界：** 普通 `.ts` / `.js` 文件不要依赖 `.ets` UI 文件：

```ts
// ✕
import { HomePage } from './HomePage.ets'
```

公共业务逻辑放进合适的共享模块，保持分层干净。

---

## 5. TypeScript → ArkTS 决策表

遇到 TypeScript 代码（迁移、参考、复制）时，按此表决策：

| TS 写法 | 处理方式 |
|---------|----------|
| `any` | **必须重构** → 定义 `interface` / `type` / `Record` |
| `as any` | **必须重构** → 修数据模型或函数签名 |
| `@ts-ignore` | **必须删除** → 修复类型问题 |
| `var` | 改 `const` / `let` |
| `for...in` | 检查是否需要替代 → `Object.keys()` + `for...of` |
| 动态属性 `obj[key]` | 检查是否应该用 `Record`，固定结构则改成字段访问 |
| 动态 `this` | 检查是否可以用箭头函数替代 |
| 复杂类型体操 | **优先简化** → 用 `interface` / `type` / `enum` 表达 |
| 解构 `const {a} = x` | 根据当前 ArkTS 版本判断 → 保守起见逐个赋值 |
| `Proxy` | 根据实际用途判断 → 响应式需求交给 ArkUI 状态管理 |
| `Reflect` | 根据实际用途判断 → 固定结构直接访问，动态结构用 `Record` |

完整的迁移检查表见 `references/migration-and-review.md`。

---

## 6. AI 修改代码规则

### 6.1 写新代码时的默认执行规则

1. 默认目标语言是 **ArkTS，不是普通 TypeScript**——不把 TS 代码直接改后缀了事。
2. 所有 `.ets` 文件遵守本规范。
3. **永远不用 `any` 消除编译错误**，不加 `@ts-ignore` / `@ts-nocheck`。
4. **不把 TS 动态写法直接复制进 ArkTS**（解构、`for...in`、动态 `this`、隐式转换……）。
5. **API / JSON 数据必须先定义数据模型再用**。
6. **新增对象属性前，先确认数据模型是否需要扩展**——不要事后 `obj.newProp = ...`。
7. **不确定某个 TS 语法是否被当前 ArkTS 版本支持时，不假设支持**，采用更保守的写法。
8. **代码完成后主动自检**类型安全与语言兼容性（见第 8 节）。
9. **ArkUI 状态管理走独立的 ArkUI 技能**，不与本语言规则混淆。

### 6.2 修改已有代码：保守优先

修改存量代码时，本规范是约束自己的，不是用来大扫除的：

1. **优先保证原有功能不变。**
2. **不因为本技能的风格规则而进行无关重构。**
3. **不主动批量修改与当前任务无关的代码。**
4. **现有代码可以正常工作、仅存在风格差异时，不强制修改。**
5. **只有当违反规则会导致编译错误、运行错误、安全问题，或当前任务明确涉及该代码时，才进行修复。**

> 一句话：发现存量违规时**随相关改动逐步修复**，不要一次性大范围重构。

---

## 7. 编译错误处理流程

当 ArkTS 编译报错时，严格按以下顺序处理：

1. **阅读完整错误信息**——不要只看第一行。
2. **确认当前 HarmonyOS SDK / API 版本**——不同版本支持范围不同。
3. **确认该语法是否属于 ArkTS 当前版本支持范围**——不要因为 TS 支持就假设 ArkTS 支持。
4. **优先修改类型定义**（interface / type / 函数签名）。
5. **其次修改代码结构**（拆分、重组逻辑）。
6. **最后才考虑类型断言**（`as`），且不滥用。
7. **禁止使用 `any`、`@ts-ignore` 等方式绕过错误。**
8. **不要为了消除一个错误而改变无关业务逻辑。**

核心：报错是类型设计的反馈，不是要你关掉检查。

---

## 8. Code Review

当用户让你"审查 / 检查 / 审核"现有 ArkTS 代码，或你主动发现存量代码需要体检时，按**机械扫描 + 语义审查**两步走。

### 8.1 第 1 步：机械扫描（确定性检查，交给脚本）

本技能自带审查脚本，覆盖所有红线和高频动态语法（`any`、`@ts-ignore`、`eval`、`var`、解构、`for...in`、`bind/call/apply`、`==` 宽松比较、宽泛 `Object`/`Function` 等）：

```bash
python3 ~/.claude/skills/harmonyos-arkts/scripts/arkts_lint.py <文件或目录>
# 加 --no-color 重定向到文件；退出码：有 ERROR 返回 1，可接入 CI
```

输出按 🔴 ERROR / 🟡 WARN / 🔵 INFO 分级，每条带 `文件:行号`、规则编号、问题、修复建议。脚本只做文本模式匹配，可能有少量误报——它是"快速筛查"，不是类型检查器。

### 8.2 第 2 步：语义审查（脚本判不了的，由你来做）

脚本只能做模式匹配，以下必须基于上下文判断：

- 类型设计是否合理（能否用 `interface` 替代 `as` 断言链）
- 类属性是否**全部初始化**
- `null` / `undefined` 处理是否完备
- API、`JSON.parse` 返回是否在边界定型
- 模块是否存在**循环依赖**、`.ts/.js` 是否反向依赖 `.ets`
- `as` 断言是否滥用
- 是否用了当前 ArkTS 编译器不支持的 TS 语法

### 8.3 输出格式

用分级报告，按严重程度排序，每条给出**位置 + 问题 + 修复示例**：

```
## ArkTS 合规审查报告

扫描 X 个文件，命中 N 处问题。

### 🔴 ERROR（必须修复）
- `src/UserInfo.ets:10` — ARK001 使用 any
  问题：const data: any = response
  修复：定义 interface UserInfo { id: number; name: string } 替代 any。

### 🟡 WARN（应修复）
- ...

### 🔵 INFO（需人工确认）
- ...

### 总结
最严重问题集中在 ___；建议优先 ___。
（注：风格差异但能正常工作的代码，按第 6.2 节不强制改。）
```

完整的审查者视角检查清单（20 项）见 `references/migration-and-review.md`。

---

## 9. References

需要深入时查阅 `references/`：

- **`references/migration-and-review.md`** ——
  - TypeScript → ArkTS **迁移检查表**（完整逐项排查清单）
  - **ArkTS 与 TypeScript 的核心区别**（为什么这样限制）
  - **最重要的开发规则 / 五大原则**（详版）
  - **Code Review 强制检查清单**（审查者视角 20 项）

本技能的最终目标：

> **让代码的数据结构、类型关系、模块关系和运行行为，尽可能在编译期就确定下来。**
