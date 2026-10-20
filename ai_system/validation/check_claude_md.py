#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""check_claude_md.py — `CLAUDE.md`（项目指令文件）可核验声明的**对账**设施。

`CLAUDE.md` 是每会话启动**必然加载**的唯一文档，却长期处于零自动维护：pre-commit
11 个钩子对根目录零命中、CI 十条一致性命令零命中、`ai_system/validation/` 无一脚本
以它为输入。它的正确性此前完全依赖人工编辑与逐会话的模型自觉。

本设施**不是闸门**，是一份可复跑的对账报告：把 `CLAUDE.md` 里**机器可核验的声明**
拿去与现场实盘比对。判定层规则（一条规则是否仍有效、某段复述是否已漂移）**不在**
本设施能力内，回落人读——`project/standards/05` §3 明写此边界。

检查项
------
| 节 | 检查 | 判定 |
|:--:|------|:---:|
| A | **含 `/` 的根相对路径**存在性 | FAIL 影响退出码 |
| B | 点名命令行参数在**同行宿主脚本**源码中存在 | FAIL 影响退出码 |
| C | 计数型声明候选（清单，供人过 判定三问） | INFO |
| D | 墓碑体量与 🔴 语义分布（规则 vs 变更史） | INFO |
| E | 体量（每会话强制加载成本） | INFO |
| A′ | 无 `/` 的具名引用（后缀表头 / 禁用旧名 / 已删对象 / 域词） | INFO，**不判定** |

设计说明
--------
* **为什么建它**（`standards/06` §3-1「默认拒绝 · 实证解锁」要求两条同时满足）：
  - **a. 复发实证**：同一需求已**三度**以一次性脚本形态出现并全部丢弃——
    `sandbox/_scripts/archive/_apply_claude_md_review_fixes.py`（2026-09-08，已归档）、
    `sandbox/_scripts/tmp/discipline_audit_20260914.py` + `discipline_audit2_20260914.py`
    （2026-09-14，共 322 行，**git 未跟踪** ⇒ 会被 GC），以及 2026-09-19 本设施的立项会话
    又临时手写了一个路径探针。不是预判，是已发生三次的重复劳动。
  - **b. 简化/替代了什么**：替代「每次维护现场重写一个一次性探针」这一重复劳动本身。
    **不新增闸门、不新增计数设施、不进 pre-commit、不进 CI**——与同目录
    `check_memory.py` 同型（按需运行、不在任何闸门内）。
* **为什么不做闸门**（`standards/06` §3.1 ①：阻断面 ⊆ 控制面）：`CLAUDE.md` 的历史欠账
  不该拦住一次与它无关的提交。任何「提交即校验」形态都会把存量问题变成所有人的阻断源。
* **口径纪律**（`standards/06` §3.1 ③）：A 节的候选总数与各类之和**同屏对拍**，差额须为 0；
  判据只打印匹配数而不与实盘对拍者，视为未验证。
* 🔴 **首版被实盘打回的两处判据错配**（留档，防重犯——`standards/06` §3.1 ③「假 FAIL 与假 PASS
  同源」的又一实例）：
  1. **A 节原判「全部 token」⇒ 12 处假 FAIL**：命中的是**后缀表头**（`_analysis.md` 是「完整格式」
     表的列头，真身是 `{STEM}_analysis.md`）、**禁用旧名**（`paper.md` 等按定义就不存在）、
     **历史实证引文**（`chain_20260727_220000.yml` 是「mtime 与声称不符」那件事的引证）、
     **脚本自己的删除记录**（`chain_profile.py` / `accumulation_check.py` 所在行原文写着「两脚本删除」）。
     ⇒ 判定面收窄为**含 `/` 的根相对路径**；无 `/` 的具名引用降为 A′ 信息节，**不判定**。
  2. **B 节原按「全文档 flag」判 ⇒ 15 处假 FAIL**：`--cached` / `--name-only` / `--pathspec-from-file`
     是 **git 自有开关**，`--fmt` / `--check-consistency` 属 `beijing_time.py`——原实现只拿
     `check_references.py` 作唯一语料，宿主全错。⇒ 改为**按行绑定宿主**：同一行能解析出唯一
     `.py` 宿主才判定，否则归「未归属」并原样打印（不隐藏、不误判）。
     后续又两修：**多宿主按开关反查**（同一脚本的**报错文案**会提到别的脚本的开关，
     裸子串匹配让两个宿主都「含全部开关」）；**开关声明判据**取 argparse ∪ 独立引号字面量
     （只认 argparse 会漏 `'--label' in sys.argv` 式手工解析，产出假 FAIL）。
  3. **链接文本一刀切 ⇒ 静默丢真引用**：首版把 markdown 链接**文本**整段剥掉（因为标签长得像路径），
     但 ``[`sandbox/_handoff/`](…/README.md)`` 的文本指的是**目录**、目标是其 README——
     全量前后对拍实测**丢了 2 个真引用**。⇒ 改为**强/弱两桶**：反引号跨度与链接目标是强引用
     （缺失计入 FAIL），链接文本是弱引用（缺失只报告）。两桶都收，不再静默丢。
* 🔴 **有意不做的检查**（`CLAUDE.md` §计数描述退役原则·判定三问已裁定；勿重新发明）：
  - ❌ **体量阈值告警**：`CLAUDE.md` 的体量是**数字**，不是阈值闸门。该成本已在
    「要不要再加一条」的决策点上由 E 节可见；设阈值即 §1 默认拒绝清单的「新增计数设施」。
  - ❌ **周期性提醒**：`standards/06` §2-2「按需驱动，禁止周期驱动」。
  - ❌ **规则有效性 / 复述是否漂移的语义判定**：无机械判据，回落人读（§3 边界）。
  - ❌ **墓碑条数上限**：D 节只报告占比；「该不该压缩」是判断，不是计数。

消费点与 cadence（设施活着的依据）
----------------------------------
* **谁跑**：AI 或用户，**按需**。入口：`project/standards/05` §3 与 `CLAUDE.md` 顶部指针行。
* **何时跑**：① 改 `CLAUDE.md` 前/后；② 执行任一设施退役后（`standards/06` §2-5）；
  ③ 用户 / 链显式触发。
* **不跑**：不进 pre-commit、不进 CI、不随会话收尾自动跑（同 `check_memory.py` 的按需定位）。

退役判据（依 `standards/06` §2-5）
----------------------------------
出现下列任一情形，本设施应退役：
1. **连续 3 次运行零发现**（A/B 两节全绿且 C/D/E 无新信息）⇒ 声明已收敛，降级为
   `project/standards/05` §3 的**复算命令清单**，删除本脚本；
2. `CLAUDE.md` 不再每会话加载（被分段加载 / `.claude/rules/` 等取代）⇒ 载体变了，失去对象；
3. 上游出现等价的官方机制（Claude Code 自带 `CLAUDE.md` 校验）⇒ 被覆盖。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = "CLAUDE.md"

# ---------------------------------------------------------------- 语料与索引


def _index_files() -> set[str]:
    """仓库内全部文件（tracked + untracked-but-not-ignored）的相对路径集合。"""
    out: set[str] = set()
    for extra in ([], ["--others", "--exclude-standard"]):
        try:
            r = subprocess.run(
                ["git", "ls-files", "-z"] + extra,
                cwd=ROOT, capture_output=True, check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return set()
        out.update(p.decode("utf-8", "replace") for p in r.stdout.split(b"\x00") if p)
    return out


def _read(rel: str) -> str:
    try:
        with open(os.path.join(ROOT, rel), "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


# ---------------------------------------------------------------- A. 路径

#: 只有以这些前缀开头的 token 才当作**仓库根相对**路径候选。本表须与**实际顶层目录**一致。
#: 🔴 6 个空壳目录（references / derivation_kb / data_kb / domain_kb / lab /
#:    meeting_notes）2026-10-05 起下沉至 `project/` 下 ⇒ 从本表**删除**。
#:    删条目不损覆盖：新路径以 `project/` 开头，已被本表覆盖；反之若改写成
#:    `project/references/` 一类，则是随目录增删漂移的镜像（本表只该列**顶层**）。
#: 🔴 同日新增顶层 `sandbox/` ⇒ 补入本表。**增删顶层目录时必须同批更新此处**：
#:    漏加不报错，只是该前缀下的 token 被静默丢弃、不参与 A 节校验（覆盖缺口，
#:    非假 FAIL —— 「不校验」与「校验通过」在输出上同形）。
ANCHORS = (
    ".claude/", ".github/", "ai_system/", "project/", "proposals/",
    "coordination/", "sandbox/",
)
#: 占位符 / 示例 / 通配 —— 判为「示例」而非「死链」。
PLACEHOLDER = re.compile(r"[{}<>*]|\.\.\.|YYYY|MM|DD|NNN|v0\.X")
#: 形如 xxx.py / xxx.md 的具名文件候选。
FILENAME = re.compile(r"^[A-Za-z0-9_.\-]+\.(py|md|json|ya?ml|js|toml|cfg|txt)$")
#: 形如 check_references 的无扩展名设施名候选。**必须 snake_case ≥2 段**——
#: 放成 `^[A-Za-z]\w{3,}$` 会把 `commit` / `changed` / `author` / `Skill` / `HEAD`
#: 一类散文词全收进来（首版实测 A′ 膨胀到 117 条，八成是噪声）。
STEMNAME = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
#: 无扩展名 token 的**解析域**：只有落在这些目录下的同名文件才算「设施名简写」。
#: 不在全域解析——否则 `quark` / `workflow` / `adapters` 一类散文词会被解析到随机同名文件，
#: 产出「看起来成功」的假解析（`standards/06` §3.1 ③ 假 PASS 形态）。
FACILITY_DIRS = (
    "ai_system/validation/", "ai_system/workflows/",
    "ai_system/scripts/reusable/", ".claude/commands/", ".claude/skills/",
)
#: 尾随标点（中英文）。
TRAIL = ".,;:)]}>、，。；：）"


#: markdown 链接：**目标是引用面，文本不是**。
LINK = re.compile(r"\[([^\]\n]*)\]\(([^)\n]*)\)")


def _tokens(text: str):
    """抽取候选 token → (行号集合, 是否**强引用**)。

    **强引用** = 反引号跨度 或 markdown 链接**目标**——作者的引用面。
    **弱引用** = markdown 链接**文本**——多数时候也是引用（``[`sandbox/_handoff/`](…/README.md)``
    指的是**目录**，目标是其 README），但**标签**也长这样
    （``[`project/standards/05`](…/05_….md)`` 只是简称）。
    两者不可由机械判据区分，故**都收进候选、分桶判定**：
    强引用缺失计入 FAIL，弱引用缺失只作 WARN 打印——避免「一刀切剥链接文本」
    静默丢掉真引用（`standards/06` §3.1 ③ 假 PASS 形态），也避免标签误报成死链。
    """
    bt = re.compile(r"`([^`\n]+)`")
    cand: dict[str, list] = {}

    def add(tok: str, i: int, strong: bool) -> None:
        for part in tok.split():
            # 链接里常写成 [`path`](target)：文本带反引号，须一并剥，
            # 否则 `startswith(ANCHORS)` 失配 ⇒ 弱引用桶恒空（实测踩过）。
            part = part.strip("`").split("#")[0].strip().rstrip(TRAIL)
            if not part:
                continue
            if part.startswith(ANCHORS) or FILENAME.match(part) or STEMNAME.match(part):
                cur = cand.setdefault(part, [set(), False])
                cur[0].add(i)
                cur[1] = cur[1] or strong

    for i, ln in enumerate(text.splitlines(), 1):
        for m in LINK.finditer(ln):
            add(m.group(1), i, False)            # 链接文本 = 弱
            add(m.group(2), i, True)             # 链接目标 = 强
        for tok in bt.findall(LINK.sub(" ", ln)):  # 已计过的链接部分不重复计
            add(tok, i, True)
    return cand


def _classify(cands: dict, files: set[str]):
    """判定面 = 含 `/` 的根相对路径；其余具名 token 归 A′（信息，不判定）。"""
    base_map: dict[str, list[str]] = {}
    stem_map: dict[str, list[str]] = {}
    for rel in files:
        base_map.setdefault(os.path.basename(rel), []).append(rel)
        if rel.startswith(FACILITY_DIRS):
            stem_map.setdefault(os.path.splitext(os.path.basename(rel))[0], []).append(rel)

    ok, short, demo, dead, warn, named = [], [], [], [], [], []
    for tok, (lines, strong) in sorted(cands.items()):
        if "/" not in tok:                       # A′：无 `/` ⇒ 不判存在性
            if PLACEHOLDER.search(tok) or tok.startswith("_"):
                continue                         # 后缀表头 / 含占位符 ⇒ 连信息价值也没有
            hits = base_map.get(tok, []) or stem_map.get(tok, [])
            named.append((tok, lines, hits[0] if len(hits) == 1 else ""))
            continue
        if PLACEHOLDER.search(tok):
            demo.append((tok, lines, "占位/示例"))
            continue
        if os.path.exists(os.path.join(ROOT, tok.rstrip("/"))):
            ok.append((tok, lines, ""))
            continue
        hits = base_map.get(os.path.basename(tok), [])
        if len(hits) == 1:
            short.append((tok, lines, hits[0]))
        elif strong:
            dead.append((tok, lines, ""))
        else:
            warn.append((tok, lines, ""))
    return ok, short, demo, dead, warn, named


# ---------------------------------------------------------------- B. 参数

FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]{1,})")
PYPATH = re.compile(r"^[A-Za-z0-9_.\-/]+\.py$")


#: 开关的两种**声明形态**：argparse 声明，或独立引号字面量（`'--label' in sys.argv` 式手工解析）。
_DECL = (
    r"add_argument\(\s*[\"']{f}[\"']",       # argparse
    r"[\"']{f}[\"']",                        # 独立引号字面量（手工 argv 解析 / 子进程转发）
)


def _declared(src: str, flag: str) -> bool:
    """该脚本是否**认得**这个开关。

    🔴 判据必须排除「整文件裸子串」形态——脚本的**报错文案**里会提到别的脚本的开关
    （实测：`check_memos.py:208` 的修复提示含 `render_memos.py --write`），
    裸子串匹配会让两个宿主都「含全部开关」，多宿主反查即失效
    （`standards/06` §3.1 ③ 口径失配的又一形态）。
    但也不能只认 `add_argument(`——实测 `cleanup_checkpoints.py:39` 用
    `'--label' in sys.argv` 手工解析，只认 argparse 会产出**假 FAIL**。
    故取两形态之并，均要求 flag 被引号完整包裹。
    """
    return any(re.search(p.format(f=re.escape(flag)), src) for p in _DECL)


def _section_b(text: str, files: set[str]):
    """CLAUDE.md 点名的命令行开关是否在其**同行宿主脚本**中存在。

    宿主绑定是刻意的：`--cached` / `--name-only` 等属 **git 自有开关**，若按全文档 flag
    去比对项目脚本源码，会产出成片假 FAIL（首版实测 15 处）。只有同一行能解析出唯一
    `.py` 宿主时才判定；否则归「未归属」原样打印。
    """
    base_map: dict[str, list[str]] = {}
    for rel in files:
        base_map.setdefault(os.path.basename(rel), []).append(rel)

    judged, unassigned, missing = 0, [], []
    section_hosts: set[str] = set()          # 本节（截至上一个标题）出现过的宿主
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.startswith("#"):
            section_hosts = set()
        flags = sorted(set(FLAG.findall(ln)))
        hosts = []
        for m in re.finditer(r"[A-Za-z0-9_.\-/]+\.py", ln):
            tok = m.group(0)
            if os.path.exists(os.path.join(ROOT, tok)):
                hosts.append(tok)
            else:
                h = base_map.get(os.path.basename(tok), [])
                if len(h) == 1:
                    hosts.append(h[0])
        hosts = sorted(set(hosts))
        section_hosts |= set(hosts)
        if not flags:
            continue
        # 多宿主：按「哪个宿主声明了全部这些开关」反查，唯一命中即绑定
        if len(hosts) > 1:
            match = [h for h in hosts if all(_declared(_read(h), f) for f in flags)]
            hosts = match if len(match) == 1 else []
        # 无自身宿主：节内指代消解（「该脚本」）——仅当本节唯一宿主时成立
        if not hosts and len(section_hosts) == 1:
            hosts = list(section_hosts)
        if len(hosts) != 1:
            unassigned.append((i, flags, len(hosts)))
            continue
        src = _read(hosts[0])
        for f in flags:
            judged += 1
            if not _declared(src, f):
                missing.append((i, f, hosts[0]))
    return missing, judged, unassigned


# ---------------------------------------------------------------- C. 计数候选

COUNTDECL = re.compile(r"[0-9]+\s*(个|篇|处|次|条|项|行|列|文件|模块|工作流|目录)")


def _section_c(text: str) -> list:
    hits = []
    for i, ln in enumerate(text.splitlines(), 1):
        if COUNTDECL.search(ln):
            s = ln.strip()
            hits.append((i, s[:110] + ("..." if len(s) > 110 else "")))
    return hits


# ---------------------------------------------------------------- D. 墓碑

def _section_d(text: str) -> dict:
    lines = text.splitlines()
    idx = [i for i, l in enumerate(lines, 1) if l.startswith("#") and not l.startswith("####")]
    tomb = []
    for n, i in enumerate(idx):
        if "已退役" not in lines[i - 1]:
            continue
        end = idx[n + 1] - 1 if n + 1 < len(idx) else len(lines)
        tomb.append((i, end, end - i + 1, lines[i - 1].strip()))
    tomb_lines = sum(t[2] for t in tomb)

    hist, rule = [], []
    for i, l in enumerate(lines, 1):
        if "\U0001F534" not in l:
            continue
        (hist if re.search(r"20\d\d-\d\d-\d\d|已退役|退役|废止|原「|原先", l) else rule).append(i)
    return {
        "tombstones": tomb,
        "tomb_lines": tomb_lines,
        "total_lines": len(lines),
        "red_total": len(hist) + len(rule),
        "red_hist": hist,
        "red_rule": rule,
    }


# ---------------------------------------------------------------- 输出

def _hr(title: str) -> None:
    print()
    print("=" * 78)
    print("# " + title)
    print("=" * 78)


def _lines_of(ls: set[int]) -> str:
    return ",".join(str(x) for x in sorted(ls))


def main() -> int:
    ap = argparse.ArgumentParser(description="CLAUDE.md 可核验声明对账（按需，非闸门）")
    ap.add_argument("--doc", default=DOC, help="被对账的文档（默认 CLAUDE.md）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    path = os.path.join(ROOT, args.doc)
    if not os.path.exists(path):
        print("找不到 %s" % args.doc)
        return 1
    text = _read(args.doc)
    files = _index_files()

    ok, short, demo, dead, warn, named = _classify(_tokens(text), files)
    miss_flags, n_judged, unassigned = _section_b(text, files)
    c_hits = _section_c(text)
    d = _section_d(text)

    total_lines = len(text.splitlines())
    cjk = len(re.findall(r"[一-鿿]", text))

    fails = len(dead) + len(miss_flags)
    n_path = len(ok) + len(short) + len(demo) + len(dead) + len(warn)

    if args.json:
        print(json.dumps({
            "doc": args.doc,
            "chars": len(text), "lines": total_lines, "cjk": cjk,
            "path_candidates": n_path, "path_ok": len(ok), "path_short": len(short),
            "path_demo": len(demo), "path_dead": [t for t, _, _ in dead],
            "path_weak_warn": [t for t, _, _ in warn],
            "named_refs": len(named),
            "flags_judged": n_judged, "flags_missing": [f for _, f, _ in miss_flags],
            "flags_unassigned": len(unassigned),
            "count_candidates": len(c_hits),
            "tombstones": len(d["tombstones"]), "tomb_lines": d["tomb_lines"],
            "red_total": d["red_total"], "red_hist": len(d["red_hist"]),
            "red_rule": len(d["red_rule"]),
            "fails": fails,
        }, ensure_ascii=False, indent=2))
        return 1 if fails else 0

    print("CLAUDE.md 可核验声明对账 — %s" % args.doc)
    print("（本脚本按需运行，**不进 pre-commit / 不进 CI**；判定规则见 project/standards/05）")

    _hr("A. 根相对路径存在性（判定面 = 含 `/` 的 token）")
    print("  候选 = %d：直接存在 %d / 唯一 basename 简写 %d / 示例占位 %d / 🔴 死链 %d / 弱引用待看 %d"
          % (n_path, len(ok), len(short), len(demo), len(dead), len(warn)))
    total5 = len(ok) + len(short) + len(demo) + len(dead) + len(warn)
    print("  [对拍] 五类之和 = %d，与候选差额 = %d（须为 0）" % (total5, n_path - total5))
    if dead:
        print("  —— 🔴 死链明细（强引用缺失，计入退出码）——")
        for tok, lines, _ in dead:
            print("    L%-14s %s" % (_lines_of(lines), tok))
    if warn:
        print("  —— 弱引用缺失（链接**文本**，只报告不判定）——")
        print("    链接文本多为引用（如指向目录），但也可能是纯标签，机械判据分不开。")
        for tok, lines, _ in warn:
            print("    L%-14s %s" % (_lines_of(lines), tok))
    if short:
        print("  —— 简写解析（信息）——")
        for tok, lines, tgt in short:
            print("    L%-14s %-36s → %s" % (_lines_of(lines), tok, tgt))

    _hr("A′. 无 `/` 的具名引用（信息，**不判定**）")
    n_hit = sum(1 for _, _, t in named if t)
    print("  %d 个：唯一解析 %d，其余 %d 个列于下。" % (len(named), n_hit, len(named) - n_hit))
    print("  🔴 未解析**不等于失效**——含禁用旧名（`paper.md` 按定义就不该存在）、")
    print("  已删对象（`chain_profile.py` 所在行原文写着「两脚本删除」）、历史实证引文、")
    print("  字段名与散文域词。此处只提供清单，判定回落人读（standards/05 §3 边界）。")
    for tok, lines, tgt in named:
        if tgt:
            continue
        print("    L%-14s %s" % (_lines_of(lines), tok))

    _hr("B. 点名命令行参数（按行绑定宿主脚本）")
    print("  可判定开关 %d 个，其中宿主源码中未找到 = %d；未归属（同行无唯一 .py 宿主）行 = %d"
          % (n_judged, len(miss_flags), len(unassigned)))
    for i, f, host in miss_flags:
        print("    🔴 L%-6d %-22s 宿主 %s" % (i, f, host))
    if unassigned:
        print("  —— 未归属（原样打印，不判定）——")
        for i, flags, nh in unassigned:
            print("    L%-6d 宿主候选 %d 个  %s" % (i, nh, " ".join(flags)))

    _hr("C. 计数型声明候选（清单，不判定）")
    print("  命中 %d 行。🔴 本清单**不是缺陷清单**——按 CLAUDE.md §计数描述退役原则·判定三问，" % len(c_hits))
    print("  校验断言 / 规则阈值 / 历史冻结文本属保留类；请逐条过人读，勿机械清理。")
    for i, s in c_hits:
        print("    L%-6d %s" % (i, s))

    _hr("D. 墓碑体量与 🔴 语义分布")
    print("  含「已退役」的小节 = %d 个，合计 %d 行 / %d 行 = %.1f%%（每会话常驻上下文）"
          % (len(d["tombstones"]), d["tomb_lines"], d["total_lines"],
             100.0 * d["tomb_lines"] / max(d["total_lines"], 1)))
    for i, end, size, head in d["tombstones"]:
        print("    L%-5d..%-5d %2d 行  %s" % (i, end, size, head))
    print()
    print("  含 🔴 的行 = %d：变更史/退役记录 %d，当前规则 %d"
          % (d["red_total"], len(d["red_hist"]), len(d["red_rule"])))
    print("    🔴 的语义是「此处是硬约束」，用于变更史会稀释该信号（standards/05 §2）。")
    print("    —— 变更史明细 ——")
    for i in d["red_hist"]:
        print("    L%-6d %s" % (i, text.splitlines()[i - 1].strip()[:96]))

    _hr("E. 体量（每会话强制加载成本）")
    ascii_n = len(text) - cjk
    lo = cjk * 1.0 + ascii_n / 4.0            # 中文 1 token/字，ASCII 4 char/token
    hi = cjk * 1.5 + ascii_n / 4.0            # 中文 1.5 token/字
    print("  %d 字符 / %d 行（其中中文字 %d，非中文 %d）" % (len(text), total_lines, cjk, ascii_n))
    print("  粗估常驻 %.1fk–%.1fk tokens（口径：中文 1–1.5 token/字 × 非中文 4 char/token）"
          % (lo / 1000.0, hi / 1000.0))
    print("  🔴 供决策参考，**不设阈值**（CLAUDE.md §计数描述退役原则·判定三问）。")

    _hr("判定")
    if fails:
        print("  FAIL — 死链 %d + 未解析开关 %d；须在同一会话内修复（standards/05 §3）。" % (len(dead), len(miss_flags)))
    else:
        print("  PASS — A/B 两节无发现；C/D/E 为信息，供人读。")
    return 1 if fails else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
