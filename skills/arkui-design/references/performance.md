# ArkUI 性能清单

> 配合 `../SKILL.md` 使用。渲染原理、列表优化、状态粒度、build 优化禁忌。

## 目录

- [渲染原理](#渲染原理)
- [长列表：LazyForEach + IDataSource](#长列表lazyforeach--idatasource)
- [组件复用 @Reusable](#组件复用-reusable)
- [状态粒度](#状态粒度)
- [build() 优化禁忌](#build-优化禁忌)
- [其他](#其他)

---

## 渲染原理

```
状态变化 → ArkUI 重新执行相关组件的 build() → 对比新旧 UI 树 → 只更新差异
```

所以性能的核心是两条：**减少不必要的状态变化**、**缩小单次 build() 的工作量**。

---

## 长列表：LazyForEach + IDataSource

大列表必须用 `LazyForEach`，配合 `IDataSource` 只渲染可见项。

```ts
interface DataChangeListener {
  onDataReloaded(): void
  onDataAdd?(index: number): void
  onDataDelete?(index: number): void
  onDataChange?(index: number): void
}

interface IDataSource {
  totalCount(): number
  getData(index: number): Item
  registerDataChangeListener(listener: DataChangeListener): void
  unregisterDataChangeListener(listener: DataChangeListener): void
}

class ItemDataSource implements IDataSource {
  private items: Item[] = []
  private listeners: DataChangeListener[] = []

  totalCount(): number { return this.items.length }
  getData(index: number): Item { return this.items[index] }
  registerDataChangeListener(l: DataChangeListener): void { this.listeners.push(l) }
  unregisterDataChangeListener(l: DataChangeListener): void {
    this.listeners = this.listeners.filter(x => x !== l)
  }

  private notify(): void { this.listeners.forEach(l => l.onDataReloaded()) }
  setData(items: Item[]): void { this.items = items; this.notify() }
  append(item: Item): void {
    this.items.push(item)
    this.listeners.forEach(l => (l.onDataAdd ? l.onDataAdd(this.items.length - 1) : l.onDataReloaded()))
  }
}
```

使用：

```ts
LazyForEach(this.dataSource, (item: Item) => {
  ListItem() { ItemView({ item: item }) }
}, (item: Item) => item.id)        // 稳定唯一 key
```

**要点：**

- **key 必须稳定且唯一**（业务 id），不要用 `index`。
- 数据变化走 listener 通知（`onDataReloaded` / `onDataAdd` 等），不要重建 `dataSource`。
- 局部增删用对应的细粒度通知（`onDataAdd` / `onDataDelete`），少用 `onDataReloaded` 全量刷新。

---

## 组件复用 @Reusable

列表项 / 频繁出现消失的组件加 `@Reusable`，框架复用实例而非销毁重建。

```ts
@Reusable @Component struct ItemView {
  @State item: Item | null = null

  aboutToReuse(params: Record<string, Object>): void {
    // 复用时重置状态
  }

  build() { /* ... */ }
}
```

**要点：**

- 同一组件有不同形态（如多种卡片样式）时，用 `reuseId` 区分复用池，避免形态错配。
- 复用初始化放 `aboutToReuse`，**别放 `aboutToAppear`**（`aboutToAppear` 只在首次创建时执行一次）。
- 配合 `LazyForEach` 使用效果最佳。

---

## 状态粒度

- **粒度过粗**：一个大对象一个 `@State`，任一属性变都重渲染整块。
- **粒度过细**：大量小 `@State`，管理成本高、易乱。
- **原则**：按「会一起变化的最小单元」拆分；把高频变化的字段独立出来，避免拖累整块重渲染。
- 嵌套要细粒度观察 → `@Observed` + `@ObjectLink`（见 `state-management.md`）。

---

## build() 优化禁忌

`build()` 必须轻、纯：

- ✕ 发请求、开定时器、读写文件。
- ✕ 修改状态（会触发循环刷新）。
- ✕ 重计算（大数据遍历、复杂转换）—— 预计算后存 `@State` 或派生属性。
- ✕ `new` 大对象（每次 build 都构造）。
- ✕ 内联复杂匿名函数构造（高频创建）。
- ✓ 派生值用 getter，或在状态变化时算好缓存。

---

## 其他

- 避免不必要的全局监听刷新；优先局部状态。
- 图片等资源懒加载、指定尺寸，避免布局抖动。
- 布局扁平（见 `components-and-layout.md` 嵌套约束）。
- 动画用 `transform` / `opacity` 等可合成属性，减少重排。
- **用 DevEco Studio 的性能分析工具定位真实瓶颈，不要盲猜优化。**
