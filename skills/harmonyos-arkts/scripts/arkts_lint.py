#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkTS 规范机械审查脚本

对本技能（harmonyos-arkts）定义的红线与高频动态语法做确定性的文本扫描。
它能抓住"一眼就是违规"的问题；判不了的语义问题（类型设计是否合理、as 是否
滥用、类属性是否初始化、循环依赖等）交给 AI 在此基础上做二次审查。

用法:
    python3 arkts_lint.py <文件或目录...> [-q] [--no-color]
    python3 arkts_lint.py src/                     # 审查目录（递归）
    python3 arkts_lint.py src/MainAbility/pages/Index.ets   # 审查单文件

退出码: 存在 ERROR 级命中返回 1，否则 0（方便接入 CI / pre-commit）。

注意: 本脚本只做模式匹配，会有少量误报（字符串/注释里的命中）。它是"快速筛
查 + 提示"，不是类型检查器；最终结论以 ArkTS 编译器为准。
"""

import os
import re
import sys
import argparse

# 只扫描这些扩展名
INCLUDE_EXT = (".ets", ".ts")

# 递归扫描时跳过的目录名（依赖产物、构建产物、版本控制等）
EXCLUDE_DIRS = {
    "node_modules", "oh_modules", ".git", ".svn",
    "build", ".hvigor", ".idea", ".cxx", "test", "unittest",  # HarmonyOS 构建产物
    ".preview",
}

# 严重程度
ERROR = "ERROR"  # 红线，必须修复
WARN = "WARN"    # 动态语法 / 宽泛类型，应修复
INFO = "INFO"    # 需要人工确认（误报可能较大，或上下文相关）

# 规则表：每条规则 = 编号 / 严重程度 / 正则模式列表 / 一句话说明 / 修复建议
# 模式作用于"单行"文本（已剥离行尾换行）。多条模式任一命中即记一次违规。
RULES = [
    # ===== 红线（ERROR）=====
    {
        "id": "ARK001", "sev": ERROR,
        "title": "禁止 any 类型",
        "patterns": [r":\s*any\b", r"<\s*any\b", r"\bany\[\]", r"\bany\s*>"],
        "advice": "定义明确的数据模型替代：interface / class / type / Record。",
    },
    {
        "id": "ARK002", "sev": ERROR,
        "title": "禁止 as any 断言",
        "patterns": [r"\bas\s+any\b"],
        "advice": "不要用 as any 绕过类型检查；先修数据模型或函数签名。",
    },
    {
        "id": "ARK003", "sev": ERROR,
        "title": "禁止 @ts-ignore",
        "patterns": [r"@ts-ignore"],
        "advice": "修复类型/结构问题，不要让编译器闭嘴。",
    },
    {
        "id": "ARK004", "sev": ERROR,
        "title": "禁止 @ts-nocheck",
        "patterns": [r"@ts-nocheck"],
        "advice": "移除整文件类型关闭；逐个修复类型问题。",
    },
    {
        "id": "ARK005", "sev": ERROR,
        "title": "禁止 eval 动态执行",
        "patterns": [r"\beval\s*\("],
        "advice": "用明确的逻辑替代动态代码执行。",
    },
    {
        "id": "ARK006", "sev": ERROR,
        "title": "禁止 new Function 动态执行",
        "patterns": [r"\bnew\s+Function\s*\("],
        "advice": "用明确的函数定义替代。",
    },
    {
        "id": "ARK007", "sev": ERROR,
        "title": "禁止 with 语句",
        "patterns": [r"\bwith\s*\("],
        "advice": "with 引入动态作用域，ArkTS 不允许；显式访问对象属性。",
    },
    {
        "id": "ARK008", "sev": ERROR,
        "title": "禁止 var 声明",
        "patterns": [r"\bvar\s+"],
        "advice": "用 const（不可变优先）或 let。",
    },
    {
        "id": "ARK009", "sev": ERROR,
        "title": "禁止 throw 非异常值",
        "patterns": [r"\bthrow\s+['\"`\d]", r"\bthrow\s+\d"],
        "advice": "异常必须是 Error 或其子类：throw new Error('...')。",
    },
    {
        "id": "ARK010", "sev": ERROR,
        "title": "禁止 delete 删除属性",
        "patterns": [r"\bdelete\s+"],
        "advice": "用可选属性 ? 表达字段可能不存在，或重建符合目标结构的数据。",
    },
    {
        "id": "ARK011", "sev": ERROR,
        "title": "禁止 Proxy 自造响应式",
        "patterns": [r"\bnew\s+Proxy\s*\("],
        "advice": "响应式能力交给 ArkUI 官方状态管理（@State 等），不要自行实现。",
    },

    # ===== 动态语法 / 宽泛类型（WARN）=====
    {
        "id": "ARK101", "sev": WARN,
        "title": "禁止对象解构赋值",
        "patterns": [r"\b(?:const|let)\s+\{[^}]*\}\s*="],
        "advice": "逐个赋值：const name: string = user.name。",
    },
    {
        "id": "ARK102", "sev": WARN,
        "title": "禁止数组解构赋值",
        "patterns": [r"\b(?:const|let)\s+\[[^\]]*\]\s*="],
        "advice": "按下标取值：const first: UserInfo = list[0]。",
    },
    {
        "id": "ARK103", "sev": WARN,
        "title": "禁止 for...in 遍历",
        "patterns": [r"\bfor\s*\(\s*(?:const|let|var\s+)?\s*\w+\s+in\b"],
        "advice": "用 Object.keys() + for...of 遍历对象键。",
    },
    {
        "id": "ARK104", "sev": WARN,
        "title": "禁止 bind / call / apply 改变 this",
        "patterns": [r"\.\s*(?:bind|call|apply)\s*\("],
        "advice": "用箭头函数闭包明确指向：const fn = () => obj.method()。",
    },
    {
        "id": "ARK105", "sev": WARN,
        "title": "禁止 == / != 宽松比较（隐式转换）",
        "patterns": [r"(?<![=!<>])==(?!=)", r"(?<!!)!=(?!=)"],
        "advice": "用严格比较 === / !==，或先把数据显式转换成同类型。",
    },
    {
        "id": "ARK106", "sev": ERROR,
        "title": "禁止宽泛 Object 类型（ArkTS 编译报错）",
        "patterns": [r":\s*Object\b", r"<\s*Object\b"],
        "advice": "用具体 interface，或动态键值用 Record<string, T>。",
    },
    {
        "id": "ARK107", "sev": WARN,
        "title": "禁止宽泛 Function 类型",
        "patterns": [r":\s*Function\b"],
        "advice": "写明确签名：let cb: (value: string) => void。",
    },
    {
        "id": "ARK108", "sev": WARN,
        "title": "慎用 unknown（不要当 any 替身）",
        "patterns": [r":\s*unknown\b"],
        "advice": "优先明确类型或联合类型；用 unknown 时务必先收窄再使用。",
    },
    {
        "id": "ARK109", "sev": WARN,
        "title": "禁止动态属性访问（固定结构上用变量当 key）",
        "patterns": [r"\breturn\s+\w+\s*\[\s*\w+\s*\]"],
        "advice": "固定结构直接访问字段 user.name；只有 Record 类型才能 data[key]。",
    },
    {
        "id": "ARK110", "sev": WARN,
        "title": "禁止隐式数字转换",
        "patterns": [r"[\+\-\*\/]\s*['\"]"],
        "advice": "用 Number() / Number.parseInt() / Number.parseFloat() 显式转换。",
    },

    # ===== 需要人工确认（INFO）=====
    {
        "id": "ARK201", "sev": INFO,
        "title": "JSON.parse 结果需在边界定型",
        "patterns": [r"\bJSON\.parse\s*\("],
        "advice": "解析出口立刻定型：JSON.parse(json) as UserInfo；最好封装成函数。",
    },
    {
        "id": "ARK202", "sev": INFO,
        "title": "未声明类型的 import 可能引入动态模块",
        "patterns": [r"\bimport\s*\(\s*['\"]"],
        "advice": "确认是否为必要的动态加载；ArkTS 优先用静态 import。",
    },
    {
        "id": "ARK203", "sev": INFO,
        "title": "Reflect 动态对象操作",
        "patterns": [r"\bReflect\s*\."],
        "advice": "固定结构直接访问属性；动态结构用 Record<string, T>。",
    },
]

# 预编译
for _r in RULES:
    _r["_regexes"] = [re.compile(p) for p in _r["patterns"]]

SEV_ORDER = {ERROR: 0, WARN: 1, INFO: 2}
SEV_SYMBOL = {ERROR: "🔴", WARN: "🟡", INFO: "🔵"}

# ANSI 颜色（仅在 tty 输出时启用）
ANSI = {
    ERROR: "\033[31m",    # 红
    WARN: "\033[33m",     # 黄
    INFO: "\033[36m",     # 青
    "BOLD": "\033[1m",
    "DIM": "\033[2m",
    "RESET": "\033[0m",
}


def should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def iter_target_files(targets):
    """递归枚举要扫描的 .ets / .ts 文件。"""
    seen = set()
    for target in targets:
        if os.path.isfile(target):
            if target.endswith(INCLUDE_EXT):
                ab = os.path.abspath(target)
                if ab not in seen:
                    seen.add(ab)
                    yield target
            # 非代码文件直接忽略
        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                # 原地裁剪，阻止进入排除目录
                dirs[:] = [d for d in dirs if not should_skip_dir(d)]
                for f in files:
                    if f.endswith(INCLUDE_EXT):
                        path = os.path.join(root, f)
                        ab = os.path.abspath(path)
                        if ab not in seen:
                            seen.add(ab)
                            yield path
        else:
            print(f"警告: 跳过不存在的路径: {target}", file=sys.stderr)


def scan_file(path):
    """扫描单个文件，返回命中列表。每条 = (lineno, rule, line_text)。"""
    hits = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as e:
        print(f"警告: 无法读取 {path}: {e}", file=sys.stderr)
        return hits

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        for rule in RULES:
            for rx in rule["_regexes"]:
                if rx.search(line):
                    hits.append((i, rule, line))
                    break  # 同一规则在同一行只记一次
    return hits


def fmt(loc, sev, msg, use_color):
    if use_color:
        return f"{ANSI[sev]}{loc}{ANSI['RESET']} {ANSI[sev]}{msg}{ANSI['RESET']}"
    return f"{loc} {msg}"


def main():
    ap = argparse.ArgumentParser(
        description="ArkTS 规范机械审查（本技能 harmonyos-arkts 自带）")
    ap.add_argument("targets", nargs="+", help="要审查的文件或目录")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="只输出命中行，不输出汇总")
    ap.add_argument("--no-color", action="store_true",
                    help="关闭 ANSI 颜色（重定向到文件时建议使用）")
    args = ap.parse_args()

    use_color = (not args.no_color) and sys.stdout.isatty()

    all_hits = []  # (file, lineno, rule, line)
    file_count = 0
    for path in iter_target_files(args.targets):
        file_count += 1
        for lineno, rule, line in scan_file(path):
            all_hits.append((path, lineno, rule, line))

    if not args.quiet:
        print(f"扫描 {file_count} 个文件 (.ets/.ts)，命中 {len(all_hits)} 处可疑项。\n")

    # 按文件 → 严重程度 → 行号 排序输出
    all_hits.sort(key=lambda h: (
        h[0],
        SEV_ORDER[h[2]["sev"]],
        h[1],
    ))

    cur_file = None
    counts = {ERROR: 0, WARN: 0, INFO: 0}
    by_rule = {}
    for path, lineno, rule, line in all_hits:
        if path != cur_file:
            cur_file = path
            print(f"\n# {path}")
        sev = rule["sev"]
        counts[sev] += 1
        by_rule[rule["id"]] = by_rule.get(rule["id"], 0) + 1
        sym = SEV_SYMBOL[sev]
        sev_tag = sev
        code = line.strip()
        if use_color:
            code = f"{ANSI['DIM']}{code}{ANSI['RESET']}"
        print(f"  {sym} {sev_tag} {path}:{lineno}  {rule['id']}  {rule['title']}")
        print(f"      {lineno:>4} │ {code}")
        print(f"      建议 → {rule['advice']}")

    if not args.quiet:
        print("\n" + "=" * 60)
        print("汇总")
        print(f"  {SEV_SYMBOL[ERROR]} ERROR  {counts[ERROR]:>4}  （红线，必须修复）")
        print(f"  {SEV_SYMBOL[WARN]} WARN   {counts[WARN]:>4}  （动态语法 / 宽泛类型）")
        print(f"  {SEV_SYMBOL[INFO]} INFO   {counts[INFO]:>4}  （需人工确认）")
        if by_rule:
            top = sorted(by_rule.items(), key=lambda kv: -kv[1])[:5]
            print("  高频规则: " + ", ".join(f"{rid}×{n}" for rid, n in top))
        print("  注: 脚本仅做文本模式匹配，可能有少量误报；语义问题（类型设计、as 滥用、")
        print("      类属性初始化、循环依赖等）需由 AI 二次审查。最终以编译器为准。")

    # ERROR 存在则返回 1，便于 CI 拦截
    return 1 if counts[ERROR] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
