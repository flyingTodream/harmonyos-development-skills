---
name: arkui-design
description: HarmonyOS ArkUI 声明式 UI 开发规范。只要任务涉及编写、修改、重构 ArkUI 界面（.ets 里的 @Component / build() / 状态管理 / 布局 / 动画 / 导航等）就必须使用本技能——即使用户没有明确要求。覆盖声明式心智模型、状态装饰器（@State / @Prop / @Link / @Provide / @Consume / @ObjectLink 等）选用决策、父子数据流、列表与渲染性能、布局容器选择、样式与主题、事件手势、动画转场、生命周期、Navigation 导航。HarmonyOS / 鸿蒙 UI 开发、ArkUI 页面编写、状态管理设计、列表性能优化均应触发。边界：本技能只管 ArkUI「UI 层」；ArkTS 语言层规则（any / 类型 / 解构 / 动态语法等）属于 harmonyos-arkts 技能，两者互补、不重叠。
---

# ArkUI 开发规范

## 贯穿主题

ArkUI 是声明式 UI 框架。它的灵魂用一句话讲清：

> **UI 是状态的函数——状态变，UI 自动更新。**

开发者的工作是声明「给定某个状态，视图应该长什么样」，以及「什么动作改变状态」。剩下的（何时重渲染、渲染什么）交给框架。理解这一点，下面所有规则都顺理成章——它们要么在帮你把「状态 → 视图」建得清晰，要么在阻止你回到命令式思维。

三条铁律：

1. **状态驱动**：UI 由状态计算得出；改状态，不要直接改 UI。
2. **数据单向流**：数据父→子向下流，事件子→父向上报。
3. **build() 纯渲染**：build() 只描述视图，不做副作用。

---

## 1. 触发条件与边界

**触发**：编写 / 修改 / 重构 ArkUI 界面（`.ets` 里的 `@Component`、`build()`、状态管理、布局、动画、导航），即使用户没说"按规范"。

**边界**：
- 本技能管 ArkUI「UI 层」：组件结构、状态管理、布局、样式、动画、导航、生命周期、性能。
- ArkTS「语言层」（`any` / 类型 / 解构 / 动态语法等）由 `harmonyos-arkts` 技能负责。写 `.ets` 时两者都适用，互补不冲突。

---

## 2. 核心心智模型

### 2.1 声明式 = 状态驱动

✕ 命令式：手动 show/hide、手动设文本、用全局变量驱动 UI、调用某个刷新 API。
✓ 声明式：定义状态，让 UI 表达状态；改状态，框架自动更新 UI。

```ts
// ✕ 命令式思维（ArkUI 里这条路根本走不通）
build() {
  Button('toggle').onClick(() => {
    // 试图"找到某组件再改它的属性" —— 错误思维
  })
}

// ✓ 声明式：状态驱动
@Entry @Component struct Page {
  @State visible: boolean = false
  build() {
    Column() {
      Button('toggle').onClick(() => this.visible = !this.visible)
      if (this.visible) { Text('hello') }
    }
  }
}
```

### 2.2 build() 是纯渲染

build() 必须**无副作用**：同样的状态 → 同样的视图。不要在 build() 里发请求、开定时器、修改状态、做重计算。这些放生命周期（`aboutToAppear`）或事件回调。

### 2.3 单一根节点

每个 `build()` 有且只有一个根容器；条件渲染的每个分支也各自只有一个根。

---

## 3. 组件结构

### 3.1 基本结构

```ts
@Component
struct MyCard {
  @State title: string = ''          // 状态必须初始化

  build() {                           // 有且只有一个 build()
    Column() {                        // 单一根容器
      Text(this.title).fontSize(16)
    }
  }
}
```

- 页面入口：`@Entry @Component struct`；可复用组件：`@Component struct`。
- 组件是 `struct`，不是 `class`。
- 状态变量（`@State` 等）**必须初始化**。

### 3.2 链式属性方法

属性用链式方法设置。建议按「尺寸 → 外观 → 文本 → 事件」分组，便于阅读：

```ts
Text(this.title)
  .width('100%').height(48)
  .backgroundColor('#F5F5F5').borderRadius(8)
  .fontSize(16).fontColor('#333')
  .onClick(() => {})
```

---

## 4. 状态装饰器决策 ★（核心）

选错装饰器是 ArkUI 最常见的 bug 源。**先用决策表，再写代码。**

### 4.1 决策表

| 需求 | 装饰器 | 说明 |
|------|--------|------|
| 组件内部状态，变化要刷新本组件 | `@State` | 最常用；只观察一层 |
| 父传子，子只读（父变→子同步，子改不影响父） | `@Prop` | 单向，子持有副本 |
| 父子双向同步 | `@Link` | 共享同一数据源；子不加初始值；父传 `$var` |
| 嵌套对象的属性变化要可观察 | `@Observed` + `@ObjectLink` | `@State` 只观察一层 |
| 跨多层组件共享 | `@Provide` + `@Consume` | 祖先 provide，后代 consume |
| 应用级全局状态 | `@StorageLink` / `@StorageProp` + `AppStorage` | 谨慎，见 §4.4 |
| 监听变化做联动 | `@Watch` | 只做派生/联动，别滥用 |

### 4.2 @Prop vs @Link（最常混用）

```ts
@Entry @Component struct Parent {
  @State count: number = 0
  build() {
    Column() {
      ReadOnlyChild({ count: this.count })    // @Prop：传值
      TwoWayChild({ count: $count })           // @Link：传引用（$ 前缀）
    }
  }
}

@Component struct ReadOnlyChild {
  @Prop count: number            // 单向：父变会同步，子改不影响父
  build() { Text(`${this.count}`) }
}

@Component struct TwoWayChild {
  @Link count: number            // 双向：不加初始值；父传 $count
  build() { Button('+').onClick(() => this.count++) }
}
```

> 经验：**默认用 @Prop。** 只有"子需要写回父"时才用 @Link。能用单向就别双向——单向数据流更易追踪。

### 4.3 @State 只观察一层

`@State` 修饰的对象，其**直接属性**变化可观察；**嵌套对象的属性**变化不可观察。要观察嵌套，用 `@Observed` + `@ObjectLink`：

```ts
@Observed
class Item {
  name: string = ''
  count: number = 0
}

@Component struct ItemView {
  @ObjectLink item: Item          // 引用 @Observed 对象，其属性变化可观察
  build() {
    Row() {
      Text(this.item.name)
      Button('+').onClick(() => this.item.count++)   // 会触发刷新
    }
  }
}
```

数组、Map、多层嵌套的观察陷阱见 `references/state-management.md`。

### 4.4 全局状态要克制

`AppStorage` / `@StorageLink` 是全局状态，**容易导致来源混乱、难以追踪**。原则：

- 只放真正全局的少量状态（登录态、主题、全局配置）。
- 业务页面的状态留在组件内（`@State`）或页面级（`LocalStorage`）。
- ✕ 不要为了"传参方便"把什么都塞进 AppStorage。

---

## 5. 数据流：单向向下、事件向上

```
父组件 ──数据（@Prop / 普通参数）──> 子组件
父组件 <──事件（回调函数）───────── 子组件
```

子组件要通知父，**父传一个回调给子，子在事件里调用它**——而不是子直接改父的状态（除非用 `@Link` 明确双向）。

```ts
@Component struct Child {
  @Prop value: number
  onSubmit: (v: number) => void = () => {}     // 回调：事件向上
  build() {
    Button('submit').onClick(() => this.onSubmit(this.value))
  }
}

@Component struct Parent {
  @State result: number = 0
  build() {
    Child({
      value: 10,
      onSubmit: (v: number) => { this.result = v }   // 父在回调里改自己的状态
    })
  }
}
```

跨多层共享用 `@Provide`/`@Consume`，但**别滥用**——层级太深本身就是组件拆分不到位的信号。

---

## 6. UI 与样式复用

### 6.1 @Builder 复用 UI 片段

重复的 UI 结构抽成 `@Builder`：

```ts
@Component struct Page {
  @Builder itemRow(label: string) {
    Row() { Text(label).fontSize(14) }.height(40)
  }
  build() {
    Column() {
      this.itemRow('A')
      this.itemRow('B')
    }
  }
}
```

- 复杂的、带状态的、多处复用的，抽成独立 `@Component`，别堆进一个超大 build()。
- 跨组件复用的 UI 用**全局 `@Builder function`**。

### 6.2 @BuilderParam 插槽

让自定义组件接收外部传入的 UI（类似 slot）：

```ts
@Component struct Card {
  @BuilderParam content: () => void
  build() { Column() { this.content() }.padding(12) }
}
// 使用
Card() {
  Text('插槽内容')
}
```

### 6.3 @Styles / @Extend 复用样式

```ts
@Styles function cardStyle() {
  .padding(12).backgroundColor('#FFF').borderRadius(8)
}
@Extend(Text) function titleStyle() {
  .fontSize(18).fontWeight(FontWeight.Bold)
}
// 使用：Text('x').titleStyle()
```

---

## 7. 列表与渲染性能 ★

### 7.1 长列表必须 LazyForEach

- 数据量小（几十条以内）：`ForEach` 可接受。
- 数据量大（百条以上）：**必须用 `LazyForEach`**（懒加载，只渲染可见项）。
- ✕ 千万不要对大列表用 ForEach——一次性渲染全部，卡顿 + 内存暴涨。

```ts
LazyForEach(this.dataSource, (item: Item) => {
  ListItem() { ItemView({ item: item }) }
}, (item: Item) => item.id)        // keyGenerator：必须稳定且唯一
```

- `LazyForEach` 配合 `IDataSource` 实现（见 `references/performance.md`）。
- **key 必须稳定且唯一**——用业务 id，不要用数组下标。key 错会导致复用错乱、状态串。

### 7.2 组件复用 @Reusable

列表项组件加 `@Reusable`，在 `aboutToReuse` 里重置状态，框架复用实例而非重建：

```ts
@Reusable @Component struct ItemView {
  @State item: Item | null = null
  aboutToReuse(params: Record<string, Object>): void {
    // 复用时重置；别把复用初始化放进 aboutToAppear
  }
  build() { /* ... */ }
}
```

---

## 8. 布局容器选择

| 场景 | 容器 |
|------|------|
| 垂直排列 | `Column` |
| 水平排列 | `Row` |
| 层叠 / 重叠 | `Stack` |
| 网格 | `Grid` + `GridItem` |
| 锚点 / 相对定位 | `RelativeContainer`（减少嵌套） |
| 换行 / 复杂弹性分配 | `Flex`（性能差，能用 Column/Row 就别用） |
| 列表滚动 | `List` |

原则：

- **优先 Column / Row**（性能最好）。
- **Flex 谨慎用**——比 Column/Row 慢，只在必须换行或复杂弹性分配时用。
- **嵌套别太深**——超过 ~5 层就考虑用 `RelativeContainer` 扁平化。深嵌套拖慢布局、难维护。

---

## 9. 样式与主题

### 9.1 链式属性 + attributeModifier

- 静态样式用链式属性方法。
- 需要动态 / 批量 / 条件设置时用 `attributeModifier`（AttributeModifier），别在链式调用里堆一堆三元表达式。

### 9.2 暗黑模式与响应式

- 颜色 / 资源走「暗黑模式适配」机制（资源目录限定词 `dark`），不要硬编码颜色。
- 响应式布局用断点（breakpoint）和媒体查询，为不同屏幕尺寸提供合理布局。

---

## 10. 事件与手势

### 10.1 基础事件

`.onClick`、`.onChange`、`.onTouch`。事件回调里**改状态**（触发声明式刷新），不要试图直接操作组件。

### 10.2 手势

手势（`PanGesture`、`SwipeGesture`、`PinchGesture` 等）有优先级（`default` / `high` / `low`）。多个手势组合用 `GestureGroup`（`parallel` / `sequence` / `exclusive`）。

✕ 不要让手势依赖"碰巧先识别"——明确设置优先级和组合模式。

---

## 11. 动画与转场

| 场景 | 方案 |
|------|------|
| 状态变化触发动画 | `animateTo`（显式动画） |
| 组件属性动画 | `.animation()`（属性动画） |
| 组件出现 / 消失 | `transition`（转场） |
| 共享元素过渡 | `sharedTransition` |

- **animateTo vs animation**：`animateTo` 包裹"改状态"的代码，该状态变化被动画；`.animation()` 加在组件上，其属性变化被动画。
- ✕ 不要在 build() 里写动画循环或定时器刷新——动画驱动状态，状态驱动 UI。
- 动画曲线 / 时长保持全局一致，别每个地方随手填。

---

## 12. 生命周期

| 钩子 | 时机 | 用途 |
|------|------|------|
| `aboutToAppear` | 组件创建后、build 前 | 初始化数据、发请求 |
| `aboutToDisappear` | 组件销毁前 | 清理定时器、订阅 |
| `onPageShow` | 页面显示 | 页面级刷新 |
| `onPageHide` | 页面隐藏 | 暂停轮询等 |
| `aboutToReuse` | `@Reusable` 组件复用时 | 重置状态 |

✕ 别在 build() 里做本该在生命周期做的事（请求、初始化、清理）。

---

## 13. 导航：Navigation + NavPathStack

- **新项目用 `Navigation` + `NavPathStack`**（声明式导航，能力完整、持续演进）。
- ✕ 不要用旧的 `@ohos.router`（push / replace / back）——已不推荐，新特性不支持。

```ts
@Entry @Component struct App {
  pathStack: NavPathStack = new NavPathStack()
  build() {
    Navigation(this.pathStack) {
      // 首页内容
    }
  }
}
```

详细用法（NavDestination、传参、返回、转场）见 `references/components-and-layout.md`。

---

## 14. 反模式清单

命中即改：

- ✕ 命令式思维：手动 show/hide、找组件改属性、用全局变量驱动 UI
- ✕ build() 里有副作用（请求、定时器、改状态、重计算）
- ✕ @State 粒度失当：整对象一个 @State（嵌套不刷新）或拆得过碎
- ✕ 该用 @Prop 却用 @Link（不必要的双向）
- ✕ 滥用 AppStorage 当全局传参通道
- ✕ 大列表用 ForEach 而非 LazyForEach
- ✕ LazyForEach key 用下标、或缺失（复用错乱）
- ✕ 布局嵌套过深、滥用 Flex
- ✕ 硬编码颜色、不适配暗黑模式
- ✕ 新项目用废弃的 Router 而非 Navigation

---

## 15. 速查表

### 状态装饰器速查

| 我要…… | 用 |
|--------|-----|
| 组件内状态 | `@State` |
| 父→子只读 | `@Prop` |
| 父↔子双向 | `@Link`（父传 `$`） |
| 嵌套对象属性可观察 | `@Observed` + `@ObjectLink` |
| 跨层共享 | `@Provide` + `@Consume` |
| 全局（克制用） | `AppStorage` + `@StorageLink` |
| 监听变化做联动 | `@Watch` |

### 布局速查

| 我要…… | 用 |
|--------|-----|
| 纵向 / 横向 | `Column` / `Row`（首选） |
| 重叠 | `Stack` |
| 网格 | `Grid` |
| 减少嵌套 | `RelativeContainer` |
| 换行弹性（慎用） | `Flex` |
| 滚动列表 | `List` |

### 性能速查

| 场景 | 要点 |
|------|------|
| 长列表 | `LazyForEach` + 稳定唯一 key + `@Reusable` |
| 嵌套深 | `RelativeContainer` 扁平化，控制在 ~5 层 |
| 弹性布局 | 优先 `Column` / `Row`，避免 `Flex` |
| build() | 纯渲染，无副作用、无重计算 |
| 全局状态 | 克制，别当传参通道 |

---

## 需要深入时

- **状态管理细节**（嵌套观察、数组 / Map、AppStorage vs LocalStorage、@Watch 陷阱、V2 装饰器动向）：`references/state-management.md`
- **组件与布局**（常用内置组件规范、布局容器详解、Navigation 导航、嵌套约束）：`references/components-and-layout.md`
- **性能**（IDataSource 实现、@Reusable 场景、状态粒度、build 优化清单）：`references/performance.md`
