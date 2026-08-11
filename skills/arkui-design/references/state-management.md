# 状态管理详解

> 配合 `../SKILL.md` 使用。SKILL.md 给决策表，这里讲每个装饰器的观察范围、边界与陷阱。

## 目录

- [@State 观察范围](#state-观察范围)
- [@Prop / @Link](#prop--link)
- [@Observed + @ObjectLink（嵌套观察）](#observed--objectlink嵌套观察)
- [@Provide / @Consume](#provide--consume)
- [AppStorage / LocalStorage / PersistentStorage](#appstorage--localstorage--persistentstorage)
- [@Watch](#watch)
- [V2 装饰器动向](#v2-装饰器动向)
- [常见陷阱](#常见陷阱)

---

## @State 观察范围

`@State` 只观察「一层」：

- 简单类型（number / string / boolean）：值变化可观察。
- 对象 / Class 实例：其**直接属性**变化可观察。
- 对象的**嵌套属性**变化**不可观察**。
- 数组：增删元素、整体替换可观察；**数组元素的属性变化不可观察**（除非元素是 `@Observed` + `@ObjectLink`）。

```ts
@State user: User = new User()
// user.name = 'x'         → 刷新 ✓（直接属性）
// user.address.city = 'y' → 不刷新 ✕（嵌套属性）
```

要观察嵌套 → `@Observed` + `@ObjectLink`。

---

## @Prop / @Link

- **@Prop**（父→子单向）：子持有**副本**，父变同步覆盖子，子改不影响父。
  - 适合基本类型；复杂对象深拷贝有性能成本。
- **@Link**（父子双向）：共享同一数据源。
  - `@Link` **不加初始值**（`@Link x: number`，不是 `= 0`）。
  - 父传引用：`Child({ x: $this.x })`（`$` 前缀）。
  - 类型必须与父 `@State` 一致。

---

## @Observed + @ObjectLink（嵌套观察）

- `@Observed` 修饰 Class，让其实例的属性变化可被 `@ObjectLink` 观察。
- `@ObjectLink` 修饰子组件里的局部变量，引用一个 `@Observed` 实例；**不加初始值**（从父传入）。

```ts
@Observed
class Address { city: string = ''; street: string = '' }

@Observed
class User { name: string = ''; address: Address = new Address() }

@Component struct AddressView {
  @ObjectLink address: Address
  build() {
    Text(this.address.city).onClick(() => this.address.city = '上海')   // 可观察 ✓
  }
}
```

- **多层嵌套**：每一层都要是 `@Observed`，并在对应子组件用 `@ObjectLink` 接收。
- **数组元素**：元素是 `@Observed` class，列表项组件用 `@ObjectLink` 接收元素，元素属性变化可观察。

---

## @Provide / @Consume

- 祖先组件 `@Provide` 提供，任意层级后代 `@Consume` 消费。
- 匹配：默认按变量名；也可 `@Provide('key')` / `@Consume('key')` 显式指定。
- 双向：后代 `@Consume` 改了会同步回祖先。
- 适合：主题、登录态等真正跨层的状态。
- ✕ 别用来替代"懒得逐层传参"——那是组件拆分问题，不是状态管理问题。

---

## AppStorage / LocalStorage / PersistentStorage

| 机制 | 范围 | 持久化 | 用途 |
|------|------|--------|------|
| `AppStorage` | 应用全局 | 否（内存） | 全局状态（登录态、主题） |
| `LocalStorage` | 页面 / 局部共享 | 否 | 页面级共享，比 AppStorage 收敛 |
| `PersistentStorage` | 持久化到磁盘 | 是 | 需跨启动保留的少量配置 |

- `@StorageLink`（双向）/ `@StorageProp`（单向）连接 `AppStorage`。
- **克制**：全局状态越多越难追踪。组件内能解决的别上升。

---

## @Watch

```ts
@State @Watch('onCountChange') count: number = 0

onCountChange(propName: string): void {
  // count 变化时联动
}
```

- 用于联动 / 派生（如计数变化触发节流请求）。
- ✕ 别在 `@Watch` 里写复杂业务或改状态——它是钩子，容易引发循环刷新。

---

## V2 装饰器动向

ArkUI 正在演进出一套 V2 装饰器（`@ComponentV2` / `@Local` / `@Param` / `@Event` / `@ObservedV2` / `@Trace` / `@Computed` 等），目标是更精确的细粒度观察与不可变数据。

- 本规范以稳定成熟的 **V1**（`@State` / `@Prop` / `@Link` 等）为主。
- V2 细节随版本变化较快，使用前**务必查阅当前 HarmonyOS 官方文档**，不要凭记忆假设其行为。
- 新项目可评估 V2，但**团队统一选一套，不要 V1 / V2 混用**导致状态管理混乱。

---

## 常见陷阱

- `@State` 期望嵌套刷新却不刷新 → `@Observed` + `@ObjectLink`。
- `@Link` 加了初始值 / 父没传 `$` → 编译或运行错误。
- 数组元素属性变化不刷新 → 元素 `@Observed` + 列表项 `@ObjectLink`。
- `AppStorage` 滥用成全局传参通道 → 收敛到组件 / LocalStorage。
- `@Watch` 里改状态 → 循环刷新。
