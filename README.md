# HarmonyOS Development Skills

> 面向 HarmonyOS / 鸿蒙开发的 Claude Code 技能集合。

本仓库收录 HarmonyOS 开发相关的 [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)。每个技能是一个自包含的目录，安装后 Claude Code 会在对应场景**自动加载并遵循其中的规范**——写代码、审查代码、排错时无需手动提醒。

## 技能清单

| 技能 | 触发场景 | 简介 |
|------|----------|------|
| **[harmonyos-arkts](./skills/harmonyos-arkts/)** | 编写 / 修改 / 重构 / 审查 `.ets`，TS→ArkTS 迁移，ArkTS 编译报错 | ArkTS 语言层开发规范、合规审查与编译排错。自带机械审查脚本。 |

> 规划中：ArkUI 状态管理技能（`@State` / `@Prop` / `@Builder` 等），与 `harmonyos-arkts` 的语言层规则互补。

## 目录结构

```
harmonyos-development-skills/
├── README.md
├── LICENSE                               # MIT
└── skills/
    └── harmonyos-arkts/
        ├── SKILL.md                      # 主技能文件（触发即加载）
        ├── scripts/
        │   └── arkts_lint.py             # 机械审查脚本
        └── references/
            └── migration-and-review.md   # 迁移/审查详细参考
```

技能放在 `skills/` 目录下，每个技能一个子目录，符合 [`skills`](https://github.com/vercel-labs/skills) 工具的发现规范。每个技能目录的约定：

- `SKILL.md`（必需）—— 入口，含 `name` / `description` frontmatter + 核心规范，控制在 ~500 行内。
- `scripts/` —— 确定性、可重复的工作交给脚本（扫描、转换、校验）。
- `references/` —— SKILL.md 放不下的详细参考，按需查阅。

## 前置条件

- **Claude Code**（CLI / 桌面应用 / IDE 插件，任一即可）
- **Node.js 16+**（用于 `npx` 安装）
- **Python 3**（运行审查脚本 `arkts_lint.py`；macOS 自带，Linux / Windows 用户请确认 `python3 --version` 可用——Windows 下可能需用 `python` 替代 `python3`）

## 安装

用 [`skills`](https://github.com/vercel-labs/skills) CLI 一键安装（全局，Claude Code）：

```bash
npx skills add flyingTodream/harmonyos-development-skills --skill harmonyos-arkts -a claude-code -g
```

- `--skill harmonyos-arkts` 指定技能（省略则交互选择，`--all` 装全部）
- `-a claude-code` 目标 agent
- `-g` 全局安装到 `~/.claude/skills/`（去掉则装到项目 `.claude/skills/`）

安装后**重启 Claude Code 会话**即生效。更新已安装的技能：

```bash
npx skills update
```

## 使用

### harmonyos-arkts

技能会自动触发，也可以在会话中用 `/harmonyos-arkts` 显式调用。三种典型入口：

**① 写 / 改 `.ets` 代码**
直接写即可，硬性规则（禁 `any`、固定数据结构、禁动态语法等）默认生效。

**② 审查现有代码（Code Review）**
先用脚本做机械扫描，再由 AI 做语义审查：

```bash
# 扫描文件或目录，分级输出 ERROR / WARN / INFO
python3 ~/.claude/skills/harmonyos-arkts/scripts/arkts_lint.py src/

# 重定向到文件时关闭颜色
python3 ~/.claude/skills/harmonyos-arkts/scripts/arkts_lint.py src/ --no-color > review.txt

# 退出码：存在 ERROR 红线 → 1（可接入 CI / pre-commit）
```

**③ 处理 ArkTS 编译报错**
把完整错误信息贴给 Claude，它会按技能第 7 节的流程处理（确认 SDK 版本 → 优先修类型 → 最后才用断言，禁止 `any` / `@ts-ignore` 绕过）。

## 新增技能

为本仓库贡献新技能时，遵循以下约定：

1. **一个技能一个子目录**，放在 `skills/` 下，目录名 = SKILL.md 的 `name` 字段（kebab-case，全小写 + 连字符）。
2. **`SKILL.md` 自给自足**——核心规范放在正文，详细内容下沉到 `references/`，正文控制在 ~500 行内。
3. **`description` 是触发关键**——写清"做什么 + 何时触发"，并适度强调，确保该触发时必触发；同时划清与其他技能的边界。
4. **确定性工作脚本化**——审查、转换、校验等可重复操作写成 `scripts/`，避免每次让 AI 肉眼重复劳动。
5. **强调"为什么"**——规则要解释原因，而不是堆砌 MUST / NEVER。

> 新增技能后无需任何额外配置——`skills` 工具会自动发现 `skills/` 下所有含 `SKILL.md` 的子目录。

## License

[MIT](./LICENSE) © 2026 flyingTodream
