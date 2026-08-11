# 组件与布局详解

> 配合 `../SKILL.md` 使用。常用内置组件要点、布局容器详解、Navigation 导航、嵌套约束。

## 目录

- [常用内置组件](#常用内置组件)
- [布局容器详解](#布局容器详解)
- [嵌套约束](#嵌套约束)
- [Navigation 导航](#navigation-导航)

---

## 常用内置组件

| 组件 | 要点 |
|------|------|
| `Text` | 富文本用 `Span`；长文本配 `maxLines` + `textOverflow` 截断 |
| `Image` | 优先资源引用；指定宽高避免布局抖动；大图异步加载 |
| `Button` | `type`（Capsule / Circle / Normal）；纯文字按钮直接传字符串 |
| `TextInput` / `TextArea` | `placeholder`、`onChange`、`InputType` 控制键盘类型 |
| `Column` / `Row` | 主轴 `justifyContent` / 交叉轴 `alignItems` / `spacing` |
| `Stack` | `alignContent` 对齐；后声明者在上层 |
| `List` / `ListItem` | 滚动列表；分组用 `ListItemGroup`；大列表配 `LazyForEach` |
| `Grid` / `GridItem` | `rowsTemplate` / `columnsTemplate` 定义行列 |
| `Swiper` | 轮播：`autoPlay` / `loop` / `indicator` |
| `Tabs` / `TabContent` | 标签页，`TabBar` 与内容联动 |

---

## 布局容器详解

### Column / Row（首选）

- 主轴对齐：`justifyContent(FlexStart | Center | FlexEnd | SpaceBetween | SpaceAround | SpaceEvenly)`
- 交叉轴对齐：`alignItems`（Column 用 `HorizontalAlign`，Row 用 `VerticalAlign`）
- `spacing`：子元素间距
- **能用 Column / Row 解决就别上 Flex。**

### Stack

- 层叠；`alignContent` 控制对齐。
- 子元素后声明者在上层。

### Flex（谨慎）

- 支持 `wrap`（换行）。
- **性能低于 Column / Row**，只在必须换行或复杂弹性分配时用。

### Grid

- `rowsTemplate` / `columnsTemplate` 定义网格骨架，配合 `GridItem`。

### RelativeContainer（减少嵌套）

- 用锚点（`alignRules`）相对定位子元素。
- 适合把多层 Column / Row 嵌套压平成一层。

---

## 嵌套约束

- **目标**：嵌套深度控制在 ~5 层以内。
- **代价**：深嵌套 → 布局计算慢、维护难、性能差。
- **手段**：
  - 用 `RelativeContainer` 扁平化相对关系。
  - 抽 `@Component` / `@Builder` 减少单个 build() 的层级。
  - 用 `@Styles` / `@Extend` 复用样式，而非堆嵌套容器只为复用样式。

---

## Navigation 导航

新项目统一用 `Navigation` + `NavPathStack`，弃用 `@ohos.router`。

### 基本结构

```ts
@Entry @Component struct App {
  pathStack: NavPathStack = new NavPathStack()

  @Builder pageMap(name: string) {
    if (name === 'detail') { DetailPage() }
  }

  build() {
    Navigation(this.pathStack) {
      Column() { Text('home') }          // 首页内容
    }
    .navDestination(this.pageMap)
    .mode(NavigationMode.Stack)
  }
}
```

### 跳转与传参

```ts
this.pathStack.pushPath({ name: 'detail', param: { id: 1 } })
this.pathStack.pop()
this.pathStack.pop({ from: 'detail' })    // 带返回值
```

### NavDestination（目标页根）

```ts
@Component struct DetailPage {
  build() {
    NavDestination() {
      Text('detail')
    }
    .title('详情')
    .onShown(() => {})
    .onHidden(() => {})
  }
}
```

### 要点

- **路由表统一管理**（`@Builder pageMap` 或 NavPathStack 配置），别散落各处。
- 传参在目标页用明确 `interface` 接收（呼应 `harmonyos-arkts` 的类型规范，不要 `any` / `ESObject` 一把梭）。
- 转场动画用 Navigation 默认或统一自定义，不要每页一个风格。
- 需要返回数据用 `pop` 的返回值或回调，不要靠全局状态旁路。
