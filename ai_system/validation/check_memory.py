#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""check_memory.py — 跨会话记忆系统（用户级 memory/ + MEMORY.md）的**读侧/维护侧**设施。

与备忘录系统 `check_memos.py` 同构、不同层：备忘录是**仓内治理层**（有编号、有终态、
进 pre-commit/CI）；记忆是**用户级、跨项目、无编号、无终态**，且目录在 git 之外 ⇒
**任何「提交即校验」机制都装不上**。故本设施**不进 pre-commit、不进 CI**，
挂载点为 `/闭环本会话` §3「记忆沉淀」（每会话必经，见下）。原挂载点（已废弃的会话报告工作流）Phase 5f 已于 2026-10-05 废弃。

闸门
----
| 闸门 | 判定 | 严重度 | 退出码 |
|:---:|------|:---:|:---:|
| G_mem_1 | 结构：**索引↔磁盘双向（🔄 按链接计数，支持「家族行」；🆕 2026-09-29 起为两级形态下的三级对账 = 一级 `MEMORY.md` → 二级 `_topics/` → 磁盘）**、断链（含二级断链）、孤儿、悬空 `[[互链]]`、frontmatter 必填、`name`==文件名、`type` 值域 | FAIL（悬空互链、**家族行缺共享 hook** 降为 WARN） | 影响 |
| G_mem_2 | 加载预算：`MEMORY.md` 体积（每会话必载）× 索引行数 + 正文合计；按 **harness 真值**分档（上限 25,000 字符 / 200 行；警戒 0.8、目标 0.7）⇒ 越线列最长 hook 的行 | INFO / WARN | 不影响（**不自动删**；写入侧另设硬闸门，见 §读侧/写侧边界） |
| G_mem_3 | 引用失效：记忆正文提到的设施名在「仓库 / 用户级 / 记忆目录」三基准下均不存在 | WARN | 不影响 |
| G_mem_4 | 单篇体量（🆕 2026-09-29；🔴 2026-10-01 立场收窄）：单篇记忆文件超 harness 的 **recall 上限常量**（4,096 B / 200 行；与索引的 25,000 是两个独立常量）。⚠️ **按常量与告警文案推定**「越限者对其他会话的 recall 只显示前 4,096 B」，**该截断路径在本环境未获实测证实**（三条阴性读数，见常量块的 2026-10-01 订正） | WARN | 不影响（**只报告**；**读数不等同已证实的实害**；正文处置须用户逐条裁决） |

设计说明
--------
* **为什么是这几个闸门**（2026-09-17 设计期实测，非预判；🆕 2026-09-29 增列 G_mem_4——
  它是 harness 单篇 recall 上限的**唯一**读数面，此前零覆盖；方法论见记忆
  `heterogeneous-corpus-heuristic-parity-test`「白名单最小化 + 全量对拍」）：
  - **G_mem_3 是核心价值**。`standards/06` §2-5 指出退役残留有**四层**，第四层（记忆层）
    「不在仓库内、无 grep 面、无 CI，是唯一不会被任何闸门发现的残层」，并给了历史实证：
    删除 `chain_profile.py` 后 5 条记忆仍引用它。本闸门即该条**程序化的检索手段**。
  - **G_mem_1 的价值是「替代」而非「预防」**：2026-09-14→09-17 有 11 个记忆维护脚本
    写在 gitignored 的 `sandbox/_scripts/tmp/`，其中至少 2 个各自实现了一遍这五类检查
    （`check_memory_consistency.py` / `_memory_selfcheck.py`）。本闸门把反复重写的东西
    收进一个活下去的形态（`standards/06` §3-1b「说明它简化或替代了什么」）。
  - **G_mem_2 只报告不判定**：`MEMORY.md` 每会话必载且单调增长（实测 2026-07/08/09 新增
    1/23/100 条），该成本在「要不要再加一条」的决策点上不可见。它是给 Phase 5f 看的**数字**，
    不是阈值闸门（阈值类设施见 `standards/06` §1 默认拒绝清单）。
    🔴 **2026-09-29 部分订正**：读侧仍是「只报告、不影响退出码」（阈值不动退出码是本设施的
    既定边界，改它会卡死所有会话收尾）；但**写入侧**新增了一条 **fail-closed 硬闸门**——
    仅当某次写入会把索引**推过 harness 读上限**（越过即「尾部条目每次加载被静默丢弃」，
    属硬故障）时拒绝写入。**不是新阈值**：它用的是 harness 自己的上限，且读侧早在用同一个
    `capacity_state()`。警戒线/目标线仍一律只报告、交人裁决。
* **G_mem_3 分两个桶，是本闸门能收敛的关键**：`standards/06` §2-5 ④ 要求逐条判
  「**历史案例（可留）** / 现行指引（须改）」，而历史案例**本来就会**提到已亡设施。
  故按「记忆自己是否已显式标注该设施不存在」机械分桶：
  - **待裁决桶**（未标注）⇒ 红灯，须处置
  - **已标注桶**（历史案例）⇒ 不计入判定，但**始终打印**（不隐藏任何条目）
  这样本闸门的**目标态（全绿）有了明确含义**：每条已亡设施引用都已被标注为历史。
  🔴 不做这个区分，闸门会对已正确标注的历史案例**永远报警且永不收敛**，随即被忽略。
* **被实测否决的三个候补**（有意不建，勿重新发明；口径与数据见会话报告 2026-09-17）：
  - ❌ **近重复/去重**：description Jaccard≥0.22 → **0 对**；`name` 词集 Jaccard≥0.4 → **0 对**。
    语料里没有机械可判的重复（同族记忆如三条 pre-commit stash 是**不同失效模式**，非重复）。
  - ❌ **零入链（孤链）**：123 条中 44 条无入链，样本全是正常独立记忆 ⇒ 无判别力。
  - ❌ **按时间陈旧度**：记忆无「活动」字段（`modified` 与 mtime 实测 17 处不同日、3 处缺失，
    不可作依据）；且**间隔本身不防 drift**（`standards/06` §1 默认拒绝「定期间隔提醒」）。
* 🔴 **设计期被实测抓出的两处自身缺陷**（留档，防重犯）：
  1. **前缀截断假 FAIL**：`FACILITY_RE` 原无扩展名后的 `(?![\w])` 前瞻 ⇒ `benchmarks.json`
     被截成 `benchmarks.js` 报「已亡设施」。2/4 条首轮发现是此假阳性。
  2. **退役残留扫描的子串自反**：`--retire` 的 ① 层唯一命中是本脚本**自己源码里的字面量**；
     且 ④ 层原扫整个 `~/.claude/projects/`（含会话转录），一跑 38KB。两处均已修
     （`--exclude=本文件名` + ④ 层收窄到记忆目录 + 单行截断 + 剔 frontmatter 区）。
* **口径纪律**（`standards/06` §3.1 ③）：每个计数类判据都在同一输出里同时打印
  「匹配数」与「实盘条目数」，差额为 0 或已解释。

消费点与 cadence（设施活着的依据）
----------------------------------
* **谁跑**：AI，在 `/闭环本会话` **§3「记忆沉淀」**（挂载步骤，每会话必经）
* **何时跑**：每个会话收尾，Phase 5f 内**先于** 5f-3 fast-exit（否则不加记忆的会话永不运行，
  而恰恰是那些会话最该退役；见记忆 `trigger-layer-facility-two-checks` ①）
* **看什么**：G_mem_1 FAIL → 当次修复；G_mem_3 候选与 G_mem_4 越限清单 → 并入 5f-4 的
  AskUserQuestion 一并裁决（**同一次用户交互**，不新增确认点；G_mem_4 **禁自动改写正文**）；
  **G_mem_2 越预算（WARN）→ 按它列出的最长 hook 清单压行**（`--replace-line`，只压 hook 不删条目），
  该动作**不新增确认点**（压 hook 不改记忆内容，细节本就在正文）

退役判据（`standards/06` §2-5；满足任一即应退役）
------------------------------------------------
1. **挂载点消失**：Phase 5f-0 段被移除/重构 ⇒ 本设施已无消费者，立即退役。
2. **价值未被证明**：审查者判定「连续 3 次运行（每会话一次）的输出未改变任何决定」
   （即：无一条记忆因 G_mem_3 被改指/标注/退役，**且 G_mem_2 的预算绊线一次都未触发**）⇒ 退役。
   🔴 判据是**价值**不是**运行次数**——挂载点在 Phase 5f 内，运行有保证，故「零运行」不会发生。
   🔴 注意「未触发」的两种读法：索引面若长期**远低于**预算，本绊线的价值同样未被证明
   （此时应下调预算或退役该子闸门，而非留着当装饰）。
3. G_mem_3 的载体若被上游统一（例如记忆引用基准被规范化到可直接对账的另一设施）⇒ 退役 G_mem_3。

🔴 **便捷退役**：跑 `python ai_system/validation/check_memory.py --retire`——打印本设施的
**全部落点（现场 grep，非硬编码清单）** + `standards/06` §2-5 **四层残留扫描的实跑结果**
+ 逐步移除清单。

读侧/写侧边界
-------------
本脚本**默认只读**（G_mem_1–4 不改任何文件）。写侧（Phase 5f-5）的写操作有三个：
`--append-line` / `--replace-line`（写一级 `MEMORY.md`）、`--append-member`
（两级形态下写二级 `_topics/<topic>.md`，**不适用容量闸门**——二级文件不在每会话必载面）、
`--remove-line`（退役）。它们用于向索引追加 / 替换 / 删除行——
`MEMORY.md` 是**多会话共用**的索引文件，用 Edit/sed 直接插行会粘行或破坏行尾（本项目已实证，
见记忆 `edit-tool-crlf-line-merge`）。该工具按**字节**操作、**保持文件原行尾**、**幂等**。
🆕 2026-09-29：该工具另带**写入侧容量闸门**——写出前用读侧同一个 `capacity_state()` 判定，
**越 harness 读上限即 ABORT**（越限后尾部条目每次加载被静默丢弃，属硬故障）；
过警戒线/目标线只打印提示，不阻断（阈值不动退出码的边界不变）。
🔴 2026-09-19 订正：原文写「`MEMORY.md` 是 **CRLF**」——**与语料实盘不符**（实测该文件与
记忆目录 129 条中的 125 条均为**纯 LF**），该措辞曾令写侧以 CRLF 为硬前置 ⇒ 两个写入口
**一律 ABORT、完全不可用**。判据已改为「**纯单一行尾**（LF / CRLF 均可），按原行尾回写」，
混合行尾仍 fail-closed（见 `_dominant_eol`）。

用法
----
    python ai_system/validation/check_memory.py                  # 维护报告（默认）
    python ai_system/validation/check_memory.py --json           # 机器可读
    python ai_system/validation/check_memory.py --retire         # 退役清单 + 四层残留扫描
    python ai_system/validation/check_memory.py --append-line <slug> --line-file <path>
    python ai_system/validation/check_memory.py --replace-line <slug> --line-file <path>
    python ai_system/validation/check_memory.py --remove-line <slug>     # 退役：删索引行
    python ai_system/validation/check_memory.py --append-member <TOPIC> --line-file <path>  # 两级形态：写二级

    --memory-dir PATH   覆盖记忆目录（默认自动探测；env: NOMOS_MEMORY_DIR）
    --repo PATH         覆盖仓库根（默认由本文件位置回推）

退出码：0 = 无 G_mem_1 结构问题（含 WARN/INFO）；1 = G_mem_1 FAIL；2 = 用法/环境错误。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

INDEX_NAME = "MEMORY.md"
REQUIRED_FIELDS = ("name", "description")
VALID_TYPES = {"user", "feedback", "project", "reference"}
CHARS_PER_TOKEN = 3.0  # 中文口径粗估（2026-09-17 实测：20,444 字符 ≈ 6.8k token）——**仅用于展示**

# ── G_mem_2 预算（🆕 2026-09-21；🔴 2026-09-29 **重标：锚到 harness 真值**）──────────
# `MEMORY.md` 是**唯一每会话必载**的记忆面（正文按需召回，不构成固定成本）⇒ 需要绊线。
#
# 🔴 旧实现锚的是**自标定值** `INDEX_TOKEN_BUDGET = 6700`（≈20,100 字符，2026-09-21 用
#   「实盘 × CLAUDE.md 成本取对数中点」估出）。2026-09-29 回源发现该估计**几乎正中 harness
#   自己的警戒线**（20,000 字符，差 0.5%）——但它锚的是**警戒线**而非**目标线**，且**只看
#   字符、不看行**（家族行形态下「行」会先越线）。故改为直接采用 harness 真值。
#
# **真值来源**（须回源复核，勿凭记忆）：Claude Code v2.1.284 内嵌模块 `bin/claude.exe`
#   （npm 全局包 @anthropic-ai/claude-code；字节偏移 ≈203,977,848，chunk `chunk-1r52y9vj.js`）：
#     var Oc="MEMORY.md", HN=200, Yq=25000, N3n=4*Yq, Uye=200, PJ=4096;
#     function x5e(t){let r=t.trim();return{lineCount:jt(r,"\n")+1,byteCount:r.length}}
#     var Fxn=0.8, htt=0.7;                  // Bbe(): 两维取 frac 大者，frac<Fxn ⇒ 不报
#     function Bt(t){let e=t/1024; …`${e.toFixed(1)}KB`}
#   ⇒ `Yq=25000` 是**字符**上限（字段名 `byteCount` **误导**——实现是 JS `String.length`），
#     `HN=200` 是**行**上限；`Bt()` 把它当字节 ÷1024 显示 ⇒ 25,000 字符印成 “24.4KB”、
#     目标 17,500 印成 “17.1KB”（交接单 §3-1 里那三个数即由此而来）。
#   库内可引用真源：`ai_system/official_docs/claude_code/sub-agents.md:634`
#     （“the first 200 lines or 25KB of MEMORY.md … whichever comes first”）。
#   超上限的后果**不是**读不到文件，而是**尾部条目在每一次加载时被静默丢弃**（harness 原文：
#     “everything past the limit is silently dropped each time the index is loaded”）⇒ 硬边界。
#
# 语义：**绊线，不是配额**——越线只列清单交人裁决；🔴 **禁止自动删任何记忆**
# （合并/删除的召回代价已被 2026-09-18 的全库扫描实测证否：一族只省 ≈109 token/会话；
#  2026-09-29 复核：一级压实 20,508→18,006 字符后 **10 分钟内**被并行会话增量抹平）。
INDEX_CHAR_CAP = 25000    # Yq：字符上限（harness 真值）
INDEX_LINE_CAP = 200      # HN：行上限（harness 真值）
WARN_FRAC = 0.8           # Fxn：警戒比例（harness 真值）
TARGET_FRAC = 0.7         # htt：目标比例（harness 真值）
INDEX_CHAR_WARN = int(INDEX_CHAR_CAP * WARN_FRAC)      # 20,000 字符
INDEX_CHAR_TARGET = int(INDEX_CHAR_CAP * TARGET_FRAC)  # 17,500 字符
INDEX_LINE_WARN = int(INDEX_LINE_CAP * WARN_FRAC)      # 160 行
INDEX_LINE_TARGET = int(INDEX_LINE_CAP * TARGET_FRAC)  # 140 行
BUDGET_TOP_N = 10  # 越线时列出 hook 最长的 N 行
HOOK_RE = re.compile(r"^- \[(.*?)\]\((.*?)\)\s*—\s*(.*)$", re.M)

# 由本文件位置回推仓库根：ai_system/validation/check_memory.py -> repo
REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# 记忆目录探测
# ---------------------------------------------------------------------------


def find_memory_dir(override: str | None = None) -> Path | None:
    """按 参数 > env > 自动探测 的顺序定位记忆目录；找不到返回 None（不报错）。"""
    cands: list[Path] = []
    if override:
        cands.append(Path(override))
    env = os.environ.get("NOMOS_MEMORY_DIR")
    if env:
        cands.append(Path(env))
    home = Path.home()
    base = home / ".claude" / "projects"
    if base.is_dir():
        # 🔴 2026-10-05 订正：原实现是 `base.glob("*<原项目名>*")` —— 硬编码了**原项目名**。
        # 本骨架的 cwd 派生 slug 是 `c--nomos`，与该模式**恒不相交** ⇒
        # 记忆设施在本仓**静默空转**（`find_memory_dir` 返回 None，读侧打印「未找到」、
        # 写侧无从落笔）。它的注释自称「按 glob 探测而非硬编码单一拼写」(D--Nomos/d--Nomos)，
        # 而模式本身就是硬编码的 —— 注释与代码互相矛盾，属 `standards/06` §3.1 ③ 同族。
        # 改由**本仓路径**派生 slug：`C:\nomos` → `c--nomos`（盘符与分隔符各变一个 `-`，小写）。
        # 与项目名无关，换任何仓库名都成立。
        _map = str.maketrans({":": "-", "\\": "-", "/": "-"})
        slug = str(REPO_ROOT).lower().translate(_map).lstrip("-")
        cands.append(base / slug / "memory")
        cands.append(base / ("-" + slug) / "memory")   # 盘符前带 `-` 的写法
    for c in cands:
        if c.is_dir() and (c / INDEX_NAME).exists():
            return c
    return None


# ---------------------------------------------------------------------------
# 读取
# ---------------------------------------------------------------------------


def read_index_bytes(mem: Path) -> bytes:
    return (mem / INDEX_NAME).read_bytes()


def load_memories(mem: Path) -> dict[str, str]:
    """slug -> 正文。排除一级索引与二级索引目录（`_topics/` 是**分组索引**，非内容条目）。

    ⚠️ 排除**由非递归 `glob("*.md")` 实现**（不是显式过滤）——改成 `rglob` 会把
    `_topics/` 一并并入 G_mem_1/2/3/4 的读数面。
    理由：官方文档（`ai_system/official_docs/claude_code/memory.md:517-525`）的官方形态是
    「`MEMORY.md` + 每记忆一个 topic 文件（**扁平、同级**）」，而 `_topics/<topic>.md` 是本项目
    **增设的分组层**（内容 = 成员链接表，不是记忆正文）⇒ 不属本闸门度量的"记忆正文"。
    🔴 **未定项**：harness 的单篇 recall 上限（G_mem_4）**是否触达 `_topics/` 无定论**——
    二进制有常量（`PJ=4096`）与告警原文，但官方文档对 **recall 层空白**（只述加载面，
    且 `memory.md:539` 明写该 200 行/25KB 限「applies only to `MEMORY.md`」）。
    验证协议见方案 `proposals/2026/09/29/2026-09-29_记忆系统两级索引方案.md` §1.4。
    """
    out: dict[str, str] = {}
    for p in sorted(mem.glob("*.md")):
        if p.name == INDEX_NAME:
            continue
        out[p.stem] = p.read_text(encoding="utf-8", errors="replace")
    return out


TOPIC_DIR = "_topics"   # 二级索引目录（🔴 与 MEMORY.md 同类：指引件，非记忆条目）


def load_topic_links(mem: Path) -> tuple[dict[str, list[str]], list[str]]:
    """读二级索引 → (topic_slug -> [成员 slug], 全部被链接成员 slug)。

    目录不存在时返回空集 ⇒ **向后兼容扁平形态**：本函数在迁移前零作用，
    故读写两侧可分批落地而不破坏现行状态。
    """
    topic_dir = mem / TOPIC_DIR
    by_topic: dict[str, list[str]] = {}
    members: list[str] = []
    if not topic_dir.is_dir():
        return by_topic, members
    for p in sorted(topic_dir.glob("*.md")):
        slugs = _slugs_on_line(p.read_text(encoding="utf-8", errors="replace"))
        by_topic[p.stem] = list(dict.fromkeys(slugs))
        members.extend(by_topic[p.stem])
    return by_topic, members


# ---------------------------------------------------------------------------
# G_mem_1 结构
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r"^\s*-\s*\[[^\]]*\]\(([^)]+\.md)\)", re.M)
WIKI_RE = re.compile(r"\[\[([^\]]+)\]\]")
# 反引号内是代码/模板/正则，其中的 [[..]] 不是互链（本项目已实证的校验器盲区）
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")

# 🔴 2026-09-28 **家族行（C）**：一条索引行可含 1..N 个链接，形态
#   `- [A](a.md) · [B](b.md) — 共享 hook`。**收面按链接计数**（本正则取一行内全部链接），
#   不再要求「一文件一行」。理由：harness 对 MEMORY.md 有**行数**硬限（200 行读取截断、
#   建议压到 140），而 170 条记忆在「一文件一行」下 = 170 行 ⇒ 两条约束不可同时成立。
#   对冲在写侧：`--remove-line` 对家族行**只摘该链**、`--replace-line` 要求 slug 集合不变。
ANY_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+\.md)\)")


def _link_count(raw_line: bytes) -> int:
    """一行里 `[label](x.md)` 链接的个数。"""
    return len(ANY_LINK_RE.findall(raw_line.decode("utf-8", "replace")))


def _slugs_on_line(line: str) -> list[str]:
    """一行里全部链接的 slug（**不限行首**）。家族行支持的核心读取面。"""
    return [os.path.basename(x)[:-3] for x in ANY_LINK_RE.findall(line)]


def gate_structure(mem: Path, index_text: str, bodies: dict[str, str]) -> dict:
    hard: list[tuple[str, str]] = []   # 机械可修的确定缺陷 → FAIL
    soft: list[tuple[str, str]] = []   # 候选，需内容层裁决 → WARN
    disk = set(bodies)

    # 🔴 2026-09-28 **口径反转（C）**：**家族行合法**——一条索引行可含 1..N 个链接。
    #   收面由「行首链接」（旧 `LINK_RE`）改为「`- ` 行内的**全部**链接」。
    #   为什么反转：harness 对 `MEMORY.md` 有**行数**硬限（200 行处读取截断，建议压到 140），
    #   而「一文件一行」口径下 170 条记忆 = 170 行 ⇒ 两条约束**不可同时成立**。
    #   家族行是唯一既保召回（170 条全部仍被索引）又压行数的形态。
    #   ⚠️ 代价与对冲：家族行的**删除**必须「只摘该链、不整行删」——见 `remove_index_line`
    #   的新守卫（旧实现取行首链接定位整行，会把同行其余记忆一并抹掉，而记忆层是
    #   `standards/06` §2-5 自述「唯一无 grep 面、无 CI」的残层，此类丢失事后不可发现）。
    indexed_lines = [(i, ln) for i, ln in enumerate(index_text.split("\n"), 1)
                     if ln.lstrip().startswith("- ")]
    linked_slugs: set[str] = set()
    for i, ln in indexed_lines:
        slugs_here = _slugs_on_line(ln)
        linked_slugs |= set(slugs_here)
        # 家族行的**最小形态**：须带共享 hook（` — ` 之后非空），否则该族的召回线索缺失。
        if len(slugs_here) > 1 and not re.search(r"—\s*\S", ln):
            soft.append(("家族行缺共享 hook（` — ` 之后为空）——召回线索缺失",
                         f"{INDEX_NAME}:{i}（{len(slugs_here)} 个链接）"))

    # 🔴 2026-09-29 两级索引：一级行指向 `_topics/<topic>.md` 时，成员在二级文件里。
    #    成员**不是**孤儿，主题文件**也不是**记忆条目——两条集合必须分开维护。
    #    🔴 形态判定用**「一级链接里是否出现主题文件」**而非「`_topics/` 目录是否存在」：
    #    否则过渡态（目录已建、MEMORY.md 仍扁平）会把全部扁平链接判成 stray 硬错。
    by_topic, member_slugs = load_topic_links(mem)
    topic_slugs = set(by_topic)
    if linked_slugs & topic_slugs:
        stray = linked_slugs - topic_slugs
        if stray:
            hard.append(("一级索引混入非主题链接（两级形态下不允许）",
                         f"{INDEX_NAME}：{', '.join(sorted(stray)[:5])}"))
        linked_slugs = set(member_slugs)
        for t in sorted(topic_slugs):
            for s in by_topic[t]:
                if s not in disk:
                    hard.append(("二级索引断链（指向不存在的记忆文件）",
                                 f"{TOPIC_DIR}/{t}.md -> {s}.md"))
        for s in sorted({x for x in member_slugs if member_slugs.count(x) > 1}):
            soft.append(("成员在多条主题中重复登记（须择一）", s))

    for slug in sorted(linked_slugs - disk):
        hard.append(("索引断链（索引行指向不存在的文件）", f"{slug}.md"))
    for slug in sorted(disk - linked_slugs):
        hard.append(("孤儿文件（磁盘有、索引无）", f"{slug}.md"))

    for slug, text in sorted(bodies.items()):
        # 悬空互链：剥掉行内代码后再扫（防模板占位符/正则误报）。
        # 🔴 判定为 WARN 而非 FAIL：记忆写入约定**显式允许**前向链接
        #    （"a [[name]] that doesn't match an existing memory yet is fine"），
        #    故「悬空」与「有意的前向链接」机械上不可分——只出候选，裁决回落内容层
        #    （standards/06 §3.1 ③）。
        stripped = CODE_SPAN_RE.sub("", text)
        for target in sorted({t for t in WIKI_RE.findall(stripped) if t != "name"}):
            if target not in disk:
                soft.append(("悬空互链 [[…]]（可能是前向链接，需裁决）", f"{slug}.md → [[{target}]]"))

        if not text.startswith("---"):
            hard.append(("无 frontmatter", f"{slug}.md"))
            continue
        fm = text.split("---", 2)[1]
        for key in REQUIRED_FIELDS:
            if not re.search(rf"^{key}\s*:", fm, re.M):
                hard.append((f"缺字段 {key}", f"{slug}.md"))
        m_type = re.search(r"^\s*type\s*:\s*(\S+)", fm, re.M)
        if not m_type:
            hard.append(("缺字段 metadata.type", f"{slug}.md"))
        elif m_type.group(1).strip("\"'") not in VALID_TYPES:
            hard.append((f"type 值域外（{m_type.group(1)}）", f"{slug}.md"))
        m_name = re.search(r"^name\s*:\s*(\S+)", fm, re.M)
        if m_name and m_name.group(1).strip("\"'") != slug:
            hard.append((f"name≠文件名（{m_name.group(1)}）", f"{slug}.md"))

    return {
        "id": "G_mem_1",
        "name": "结构",
        "severity": "FAIL" if hard else ("WARN" if soft else "OK"),
        "disk_files": len(disk),
        # 🔴 C 口径反转后「行数」不再等于「条数」：index_rows = 索引**行**数（家族行算 1 行），
        #   index_unique = 被索引的**记忆条**数（家族行按链接数计）。二者不等是该形态的正常特征。
        "index_rows": len(indexed_lines),
        "index_unique": len(linked_slugs),
        "problems": [{"kind": k, "who": w, "severity": "FAIL"} for k, w in hard]
                    + [{"kind": k, "who": w, "severity": "WARN"} for k, w in soft],
    }


# ---------------------------------------------------------------------------
# G_mem_2 加载预算（只报告）
# ---------------------------------------------------------------------------


def _harness_len(text: str) -> int:
    """harness 口径的字符数 = JS `String.length`（UTF-16 码元；astral 字符计 2）。

    真值 = 内嵌 `x5e()` 的 `byteCount: r.length`（字段名误导，单位是**字符**而非字节）。
    Python `len()` 对 astral 字符（emoji / CJK 扩展）计 1 ⇒ 恰在阈值边界上**低估**，
    故照 JS 口径复算（本项目已多次实证「口径差一点 ⇒ 判定反转」）。
    """
    return len(text) + sum(1 for ch in text if ord(ch) > 0xFFFF)


def capacity_state(raw: bytes) -> dict:
    """按 harness 真值判定 `MEMORY.md`（字节）的容量档位——**读侧与写侧共用同一个判据**。

    档位（自轻到重）：`ok` < 目标 < `past_target` < 警戒 < `warn` < 上限 < `over`。
    harness 取**字符**与**行**两维 frac 的**大者**判警（`Bbe()`），此处同口径；
    `binding` 记下是哪一维在压线（家族行形态下通常是「行」）。
    """
    text = raw.decode("utf-8", "replace")
    # 🔴 2026-09-29 订正：harness 的 `x5e()` 是 `let r=t.trim()` 之后才计数
    #    （`byteCount: r.length` / `lineCount: jt(r,"\n")+1`）⇒ 两端空白不计入。
    #    首版未 trim，MEMORY.md 的尾换行被多算 1 字符（18,501 vs harness 的 18,500）——
    #    恰在阈值边界上会**反转判定**（本项目已多次实证「口径差一点 ⇒ 结论反」）。
    trimmed = text.strip()
    chars = _harness_len(trimmed)
    lines = trimmed.count("\n") + 1 if trimmed else 0
    fr_c, fr_l = chars / INDEX_CHAR_CAP, lines / INDEX_LINE_CAP
    frac = max(fr_c, fr_l)
    if fr_c > 1 or fr_l > 1:
        level = "over"
    elif frac >= WARN_FRAC:
        level = "warn"
    elif frac >= TARGET_FRAC:
        level = "past_target"
    else:
        level = "ok"
    return {"bytes": len(raw), "chars": chars, "lines": lines,
            "frac_chars": fr_c, "frac_lines": fr_l,
            "binding": "chars" if fr_c >= fr_l else "lines",
            "frac": frac, "level": level}


# ── G_mem_4 单篇体量（🆕 2026-09-29）──────────────────────────────────────────
# harness 对**单篇记忆文件**另设 recall 上限（与索引的 Yq 是**两个独立常量**）：
#   byteCap = PJ  = 4096（**字节**；此路径用真 Buffer.byteLength，非 String.length）
#   lineCap = Uye = 200
# 真源：bin/claude.exe 内嵌 `ktt()`，告警原文「recall shows other sessions only the first
#   4096 bytes of a memory file, so everything past that is invisible unless they open it」。
# 🔴 只报告不判定：正文处置是**内容决策**，须用户逐条裁决（同 G_mem_3 的双桶模式）。
# 🆕 2026-10-01 官方文档回源：`ai_system/official_docs/claude_code/memory.md:539` 明写
#   「**This limit applies only to `MEMORY.md`**」、`:541`「doesn't load topic files at startup」
#   ⇒ **加载面**（startup load）确实只含 `MEMORY.md`。但本闸门量的 4,096 B 属**召回层**
#   （recall），官方文档对该层**通篇空白** ⇒ 两层不同、互不矛盾。故本闸门**维持只报告**；
#   `_topics/` 是否在其作用域内待跨会话验证（方案 §1.4 的验证协议）。
# 🔴🔴 2026-10-01 **口径订正（本闸门立场收窄，勿再按旧措辞理解）**：本环境（CLI 2.1.285）**实测未见
#   任何模型侧 4,096 B 截断路径**——① 启动注入面只有 `MEMORY.md`（无条目正文）；② 显式 Read
#   一篇 9,095 B 文件**完整返回无截断**；③ **写入探针**：向记忆目录写 6,465 B 合规件，
#   **Write 与 Edit 两条路径均未回** harness 的 `over recall limit` 告警。
#   ⇒ 本闸门**不是**「已证实的截断读数」，而是「**按 harness 常量与告警文案推定的越限读数，
#   其作用域在本环境未获证实**」。只报告不判定——正文处置仍是内容决策，但不该被读成
#   「不拆就有实害」。理由见项目台账中的对应决策记录。
PER_MEM_BYTE_CAP = 4096
PER_MEM_LINE_CAP = 200


def gate_per_memory(bodies: dict[str, str]) -> dict:
    rows = []
    for slug, text in sorted(bodies.items()):
        n_bytes = len(text.encode("utf-8"))          # 该路径用真字节，不是字符
        stripped = text.strip()
        n_lines = stripped.count("\n") + 1 if stripped else 0
        if n_bytes > PER_MEM_BYTE_CAP or n_lines > PER_MEM_LINE_CAP:
            rows.append((n_bytes, n_lines, slug))
    rows.sort(reverse=True)
    return {
        "id": "G_mem_4", "name": "单篇体量",
        "severity": "WARN" if rows else "OK",
        "byte_cap": PER_MEM_BYTE_CAP, "line_cap": PER_MEM_LINE_CAP,
        "memories": len(bodies), "over": len(rows),
        "over_pct": round(100.0 * len(rows) / max(len(bodies), 1), 1),
        "top": rows[:BUDGET_TOP_N],
    }


def gate_budget(index_bytes: bytes, bodies: dict[str, str], index_text: str) -> dict:
    body_chars = sum(len(t) for t in bodies.values())
    rows = len(LINK_RE.findall(index_text))
    st = capacity_state(index_bytes)
    est_tokens = round(st["chars"] / CHARS_PER_TOKEN)
    # 越线时给出「压哪几行」的清单（按 hook 长度降序）——只列，不动手
    # 🔴 group(2) 是链接目标（已含 `.md`）——取 slug 时须剥一次，否则清单会印成 `x.md.md`
    #    （2026-09-21 设计期自测踩中：只跑「未越线」态看不出来，靠正向对照才暴露）
    # 🔴 家族行的 slug 取**第一个链接**并标注（2026-09-29 订正）：`HOOK_RE` 的 `\((.*?)\)`
    #    在家族行上会一路扩到最后一个链接，旧实现遂把**整串链接**当 slug 印出来
    #    （`--replace-line` 照抄必 ABORT）。hook 长度本身无此问题，仅标签受影响。
    hooks = []
    for m in HOOK_RE.finditer(index_text):
        line_slugs = _slugs_on_line(m.group(0))
        label = line_slugs[0] if line_slugs else m.group(2)
        if len(line_slugs) > 1:
            label += "（家族行）"
        hooks.append((len(m.group(3)), label))
    hooks.sort(reverse=True)
    return {
        "id": "G_mem_2",
        "name": "加载预算",
        "severity": "WARN" if st["level"] in ("warn", "over") else "INFO",
        **st,
        "index_rows": rows,
        "est_tokens_each_session": est_tokens,
        "body_chars_total": body_chars,
        "memories": len(bodies),
        # hook 长度分布——「压哪几行」的依据；与条目数无关（条目数不花每会话的钱）
        "hook_median": sorted(h for h, _ in hooks)[len(hooks) // 2] if hooks else 0,
        "hooks_over_80": sum(1 for h, _ in hooks if h > 80),
        "top_hooks": hooks[:BUDGET_TOP_N] if st["level"] != "ok" else [],
    }


# ---------------------------------------------------------------------------
# G_mem_3 引用失效（核心）
# ---------------------------------------------------------------------------

# 设施类（脚本/注册表）：正文任意位置（含散文）出现的具体文件名
# 🔴 扩展名后必须加 (?![\w]) 负向前瞻——否则 `.json` 会被截成 `.js` 命中
#    （2026-09-17 设计期自身踩中：`benchmarks.json` → `benchmarks.js` 假 FAIL，
#     同族记忆 `verification-check-substring-self-defeat` 的「前缀截断」形态）
FACILITY_RE = re.compile(
    r"(?<![\w./\\-])([A-Za-z0-9_][A-Za-z0-9_.\-]*\.(?:py|js|yml|yaml|sh))(?![\w])")
# 文档类：只认**带路径**的（裸 `X.md` 多为后缀模式如 `_analysis.md`，误报率高）
DOCPATH_RE = re.compile(
    r"(?<![\w./\\-])([A-Za-z0-9_][A-Za-z0-9_\-]*(?:/[A-Za-z0-9_.\-]+)+\.md)(?![\w])")

# 占位符/模板/正则形态——一律不判定（它们是**语法**不是**文件名**）
PLACEHOLDER_CHARS = set("<>{}*|[]\\^$+()?")
MIN_STEM = 5  # 去扩展名后的最小长度；`b.md` / `__t.py` / `xxx.md` 这类占位符靠它滤掉


def _is_judgeable(token: str) -> bool:
    if any(ch in PLACEHOLDER_CHARS for ch in token):
        return False
    if "..." in token or " " in token or "\t" in token:
        return False
    stem = Path(token).stem
    return len(stem) >= MIN_STEM


def _resolves(token: str, repo: Path, mem: Path, repo_index: set[str]) -> bool:
    """三基准解析：含路径者试仓库根；一律试全仓 basename；`~` 试用户级；试记忆目录。"""
    base = Path(token).name
    if "/" in token or "\\" in token:
        if (repo / token.lstrip("/\\")).exists():
            return True
    if token.startswith("~"):
        if Path(os.path.expanduser(token)).exists():
            return True
    if base in repo_index:
        return True
    if (mem / base).exists():
        return True
    if Path(os.path.expanduser(f"~/.claude/scripts/{base}")).exists():
        return True
    return False


def build_repo_index(repo: Path) -> set[str]:
    names = set()
    for p in repo.rglob("*"):
        if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
            names.add(p.name)
    return names


# 退役标注的机械判据：记忆自己是否已显式声明该设施不存在。
# 🔴 为何必须区分两个桶：`standards/06` §2-5 ④ 要求逐条判「**历史案例（可留）** / 现行指引（须改）」——
#    而历史案例**本来就会**提到已亡设施（那正是它的内容）。若不区分，本闸门将对
#    「已正确标注的历史案例」**永远报警且永不收敛**，随即被忽略 ⇒ 退化成噪声设施。
#    区分之后，本闸门的目标态（全绿）有了明确含义：
#    **每条已亡设施引用都已被标注为历史**；红灯 = 存在**未标注**的失效引用。
# 🔴 标注词**不带 `已` 前缀**：2026-09-17 实测，本仓历史标注的实际措辞是
#    「（该脚本已于 2026-09-15 随 #130/#119 补完**退役删除**）」——形式是
#    「已于 <日期> … 退役删除」，既非「已退役」也非「已删除」。按带前缀的窄词表
#    会把这 3 条**已正确标注**的记忆误报为待裁决（同族：记忆
#    `verification-check-substring-self-defeat`「判据表与语料形态不匹配」）。
#    放宽的代价（一个段落里谈别的事而恰含「删除」）由「已标注」桶**始终打印**兜底——
#    报告不隐藏任何条目，人可复核。
RETIRED_MARKERS = ("退役", "删除", "废弃", "废除", "移除", "不再存在", "已下线")


def _para_of(text: str, idx: int) -> str:
    start = text.rfind("\n\n", 0, idx)
    end = text.find("\n\n", idx)
    return text[(start + 2) if start >= 0 else 0: end if end >= 0 else len(text)]


def _has_marker(s: str) -> bool:
    return any(m in s for m in RETIRED_MARKERS)


def _is_annotated(text: str, token: str) -> bool:
    """该记忆是否已把此设施**显式标注**为已亡（历史案例，可留）。

    判据（宽松侧取或）：frontmatter `description` 含标注词，**或**该 token 的
    **每一处**出现所在段落都含标注词（「每一处」防止「一处标注、另一处仍在下指令」漏网）。
    """
    desc = re.search(r"^description:\s*(.+)$", text, re.M)
    if desc and _has_marker(desc.group(1)):
        return True
    occ = list(re.finditer(re.escape(token), text))
    return bool(occ) and all(_has_marker(_para_of(text, m.start())) for m in occ)


def gate_references(bodies: dict[str, str], repo: Path, mem: Path) -> dict:
    repo_index = build_repo_index(repo)
    seen: Counter[str] = Counter()
    judgeable: Counter[str] = Counter()
    skipped: Counter[str] = Counter()
    unresolved: dict[str, set[str]] = {}    # token -> {记忆}，**未标注** ⇒ 待裁决
    annotated: dict[str, set[str]] = {}     # token -> {记忆}，已标注 ⇒ 历史案例，可留

    for slug, text in sorted(bodies.items()):
        tokens = set(FACILITY_RE.findall(text)) | set(DOCPATH_RE.findall(text))
        for token in sorted(tokens):
            seen[token] += 1
            if not _is_judgeable(token):
                skipped[token] += 1
                continue
            judgeable[token] += 1
            if _resolves(token, repo, mem, repo_index):
                continue
            bucket = annotated if _is_annotated(text, token) else unresolved
            bucket.setdefault(token, set()).add(slug)

    return {
        "id": "G_mem_3",
        "name": "引用失效",
        "severity": "WARN" if unresolved else "OK",
        "tokens_seen": len(seen),                 # 实盘：出现过的不同设施名
        "tokens_judgeable": len(judgeable),       # 判定口径：通过形态过滤的
        "tokens_skipped": len(skipped),           # 差额（占位符/正则/裸 md）
        "memories_with_tokens": sum(1 for t in bodies.values() if FACILITY_RE.findall(t)),
        "skipped_tokens": sorted(skipped),
        "unresolved": [
            {"token": t, "memories": sorted(ms)} for t, ms in sorted(unresolved.items())
        ],
        "annotated": [
            {"token": t, "memories": sorted(ms)} for t, ms in sorted(annotated.items())
        ],
    }


# ---------------------------------------------------------------------------
# 报告
# ---------------------------------------------------------------------------


def render_report(struct: dict, budget: dict, refs: dict, per_mem: dict) -> str:
    L: list[str] = []
    L.append("═══ 记忆维护报告（check_memory.py）═══")
    L.append("")

    n_hard = sum(1 for p in struct["problems"] if p["severity"] == "FAIL")
    n_soft = len(struct["problems"]) - n_hard
    tag1 = "✅ 通过" if n_hard == 0 and n_soft == 0 else (
        f"❌ FAIL（{n_hard} 处）" if n_hard else f"⚠️  {n_soft} 处待裁决")
    L.append(f"[G_mem_1] 结构      {tag1}"
             f"（磁盘 {struct['disk_files']} 个 ↔ 索引 {struct['index_rows']} 行"
             f"，其中被索引的记忆 {struct['index_unique']} 条）")
    for p in sorted(struct["problems"], key=lambda x: x["severity"]):
        mark = "❌" if p["severity"] == "FAIL" else "⚠️ "
        L.append(f"    {mark} [{p['kind']}] {p['who']}")

    b = budget
    tag2 = {"ok": "ℹ️  ", "past_target": "⚠️  ", "warn": "🔴 ", "over": "❌ "}[b["level"]]
    L.append(f"[G_mem_2] 加载预算  {tag2}"
             f"{INDEX_NAME} {b['chars']:,} 字符 / {b['lines']} 行"
             f"（harness 上限 {INDEX_CHAR_CAP:,} 字符 / {INDEX_LINE_CAP} 行；"
             f"警戒 {INDEX_CHAR_WARN:,} / {INDEX_LINE_WARN}、目标 {INDEX_CHAR_TARGET:,} / {INDEX_LINE_TARGET}）"
             f"｜占上限 {100 * b['frac_chars']:.1f}% 字符 / {100 * b['frac_lines']:.1f}% 行"
             f"｜瓶颈维 = {b['binding']}")
    L.append(f"          ≈ {b['est_tokens_each_session']:,} token（每会话必载）｜{b['bytes']:,} B"
             f"｜索引 {b['index_rows']} 行｜正文合计 {b['body_chars_total']:,} 字符 / {b['memories']} 条"
             f"｜hook 中位 {b['hook_median']}、>80 的 {b['hooks_over_80']} 行")
    if b["level"] == "past_target":
        L.append(f"    ⚠️  已过 harness **目标线**（{INDEX_CHAR_TARGET:,} 字符 / {INDEX_LINE_TARGET} 行）"
                 f"——**压实已无余量**（2026-09-29 实测：一级压实后 10 分钟内被并行会话增量抹平）"
                 f"⇒ 新增条目**优先并入既有条目**；结构性处置见工作台账 #286（两级索引）")
    elif b["level"] == "warn":
        L.append(f"    🔴 已过 harness **警戒线**（{INDEX_CHAR_WARN:,} 字符 / {INDEX_LINE_WARN} 行）"
                 f"——harness 自身也会在写入后自行报警。索引面是**唯一每会话必载**的记忆成本 ⇒ 压 hook"
                 f"（细节本就在正文里，召回靠关键词不靠长度）；**不要删条目**（合并/删除的召回代价已实测证否）")
    elif b["level"] == "over":
        L.append(f"    ❌ **越过 harness 读上限**（{INDEX_CHAR_CAP:,} 字符 / {INDEX_LINE_CAP} 行）"
                 f"——超出部分的条目在**每一次加载时被静默丢弃**（尾部不可见）⇒ 这是硬故障不是告警。"
                 f"写入侧已 fail-closed 拒绝继续追加；先压 hook / 合并条目再写")
    for n, (ln, slug) in enumerate(b["top_hooks"], 1):
        L.append(f"      {n:>2}. [{ln} 字符] {slug}.md")

    nun = len(refs["unresolved"])
    nan = len(refs.get("annotated", []))
    L.append(f"[G_mem_3] 引用失效  {'✅ 通过' if nun == 0 else f'⚠️  {nun} 个设施名已亡且未标注'}"
             f"（实盘 {refs['tokens_seen']} 个设施名 = 判定 {refs['tokens_judgeable']}"
             f" + 形态过滤 {refs['tokens_skipped']}"
             f"，差额 {refs['tokens_seen'] - refs['tokens_judgeable'] - refs['tokens_skipped']}"
             f"；另 {nan} 个已亡但**已标注为历史**）")
    for item in refs["unresolved"]:
        L.append(f"    🔴 {item['token']}  ← {len(item['memories'])} 条记忆引用："
                 f"{', '.join(item['memories'])}")
    for item in refs.get("annotated", []):
        L.append(f"    ✅（已标注为历史，可留）{item['token']}  ← "
                 f"{len(item['memories'])} 条：{', '.join(item['memories'])}")
    if refs.get("skipped_tokens"):
        L.append(f"    （形态过滤项，未判定：{', '.join(refs['skipped_tokens'])}）")

    pm = per_mem
    L.append(f"[G_mem_4] 单篇体量  "
             + (f"⚠️  {pm['over']} / {pm['memories']} 篇越 harness recall 上限"
                f"（{pm['byte_cap']:,} B / {pm['line_cap']} 行）——"
                f"按 harness 常量与告警文案**推定**「对其他会话的 recall 只显示前 "
                f"{pm['byte_cap']:,} B」；⚠️ **该截断路径在本环境未获实测证实**（作用域待定，"
                f"见本文件 G_mem_4 常量块的 2026-10-01 口径订正），**读数不等同已证实的实害**"
                if pm["over"] else "ℹ️  无越限篇目"))
    for n, (nb, nl, slug) in enumerate(pm["top"], 1):
        L.append(f"      {n:>2}. [{nb:,} B / {nl} 行] {slug}.md")

    L.append("")
    if n_hard:
        L.append(f"结论：❌ G_mem_1 结构有 {n_hard} 处硬缺陷——**当次修复**（机械可修）。")
    elif nun or n_soft:
        parts = []
        if nun:
            parts.append(f"{nun} 项引用失效")
        if n_soft:
            parts.append(f"{n_soft} 处悬空互链")
        L.append(f"结论：⚠️ {' + '.join(parts)} 待裁决 → 并入 Phase 5f-4 的用户确认一并裁决："
                 f"逐条改指新设施 / 标注「已退役」/ 保留为历史案例。")
        L.append("      🔴 裁决前先回源读上下文：三类合法情形——历史案例记录（可留）、"
                 "有意的前向链接（可留）、现行指引指向已亡对象（须改）。")
    else:
        L.append("结论：✅ 无待裁决项。")
    L.append(f"      预算读数供 5f-4 决策参考：再加 1 条 ≈ +{budget['chars'] // max(budget['index_rows'], 1)} 字符"
             f"（索引行均值）到每会话必载面。")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# 退役模式（用户显式要求：设施须便于退役）
# ---------------------------------------------------------------------------

RETIRE_TOKEN = "check_memory"
RETIRE_CRITERIA = [
    "① 挂载点消失：`/闭环本会话` §3 段落被移除/重构 ⇒ 无消费者，立即退役。",
    "② 价值未被证明：审查者判定「连续 3 次运行输出未改变任何决定」⇒ 退役（判据是价值，不是运行次数）；"
    "🔴 含 G_mem_2：其预算自 2026-09-29 起锚的是 **harness 真值**（不再自调数值）⇒ 判据改为"
    "「连续 3 次运行的容量档位与清单未改变任何决定」；若索引面长期停在 `ok` 档，"
    "该绊线的价值同样未被证明 ⇒ 退役该子闸门，不要留着当装饰。",
    "③ G_mem_3 载体被上游统一 ⇒ 退役 G_mem_3（保留 G_mem_1/2）。",
]

# 排除自身文件：否则 ①层必然命中本脚本源码里的字面量（子串自反，见记忆
# `verification-check-substring-self-defeat`——「失败信号与真失败同形」）
SELF_NAME = "check_memory.py"
_EXCL = [f"--exclude={SELF_NAME}", "--exclude-dir=__pycache__"]

# 落点扫描面：**长期存在的登记/挂载面**（transient 的 sandbox 留档不算登记面）
SURFACES = ["ai_system/workflows/", "ai_system/context/", "CLAUDE.md",
            ".pre-commit-config.yaml", ".github/", ".claude/"]
MAX_SHOW = 12


def _layers(mem: Path | None) -> list[tuple[str, list[str]]]:
    """standards/06 §2-5 四层残留核查配方（逐层给命令并实跑）。"""
    t = RETIRE_TOKEN
    layers = [
        ("①闸门层", ["grep", "-rn", *_EXCL, t,
                     ".pre-commit-config.yaml", ".github/workflows/", "ai_system/validation/"]),
        ("②工作流正文指令层", ["grep", "-rn", *_EXCL, t, "ai_system/workflows/", "CLAUDE.md"]),
        ("③虚假宣称层", ["bash", "-c",
                         f"grep -rnE '{t}' ai_system/workflows/ | grep -E '校验|检查|闸门|强制' || true"]),
    ]
    if mem is not None:
        layers.append(("④记忆层", ["grep", "-rn", t, str(mem)]))
    else:
        layers.append(("④记忆层", []))  # 本机无记忆目录 → 空命令
    return layers


def run_retire(mem: Path | None, repo: Path) -> int:
    L: list[str] = []
    L.append("═══ 退役清单 — check_memory.py ═══")
    L.append("")
    L.append("退役判据（standards/06 §2-5；满足任一即应退役）：")
    for c in RETIRE_CRITERIA:
        L.append("  " + c)
    L.append("")

    self_path = Path(__file__).resolve()
    try:
        self_disp = self_path.relative_to(repo)
    except ValueError:
        self_disp = self_path
    L.append("落点（**现场 grep，非硬编码清单**——真值来源即下列命令）：")
    L.append(f"  0. {self_disp}   ← 本文件（删除即去主体）")
    hits = _grep(["grep", "-rn", *_EXCL, RETIRE_TOKEN, *SURFACES], repo)
    for i, line in enumerate(hits[:MAX_SHOW], 1):
        L.append(f"  {i}. {line}")
    if len(hits) > MAX_SHOW:
        L.append(f"  … 另 {len(hits) - MAX_SHOW} 处（命令：grep -rn {RETIRE_TOKEN} "
                 f"{' '.join(SURFACES)}）")
    if not hits:
        L.append("  （除本文件外无任何登记/挂载面引用——说明已被卸载，可直接删除本文件）")
    L.append("")

    L.append("四层残留扫描（standards/06 §2-5 配方，实跑）：")
    for layer, cmd in _layers(mem):
        if not cmd:
            L.append(f"  {layer}：∅ 本机无记忆目录（记忆在 git 之外，换机即不存在）—— 跳过")
            continue
        out = _grep(cmd, repo, strip_frontmatter=True)
        L.append(f"  {layer}：{'命中 ' + str(len(out)) + ' 处' if out else '✅ 无残留'}")
        for line in out[:MAX_SHOW]:
            L.append(f"      {line}")
        if len(out) > MAX_SHOW:
            L.append(f"      … 另 {len(out) - MAX_SHOW} 处")
    L.append("")

    L.append("移除清单（按序）：")
    L.append(f"  1. 删除本文件 {self_disp}")
    L.append("  2. 移除 `.claude/commands/闭环本会话.md` 的 **§3 记忆沉淀** 整段"
             "（②层 grep 给出确切行号）；删后重跑本命令，②层应归零")
    L.append("  3. 按四层扫描结果逐层清零——③④ 两层最易漏"
             "（③伪装成安全网、④无 CI 面，见 standards/06 §2-5）")
    L.append("  4. 在会话报告 §3.3 记一笔退役裁决（standards/06 §2-5 退役对称性）")
    L.append("")
    L.append("🔴 本命令只**报告**，不执行删除——删除是不可逆操作，须用户显式确认。")
    print("\n".join(L))
    return 0


_FM_END: dict[str, int] = {}


def _frontmatter_end(rel: str, cwd: Path) -> int:
    """返回该文件 frontmatter 块的结束行号（0 = 无 frontmatter）。"""
    if rel in _FM_END:
        return _FM_END[rel]
    end = 0
    try:
        text = (cwd / rel).read_text(encoding="utf-8", errors="replace")
        if text.startswith("---"):
            for i, ln in enumerate(text.split("\n")[1:], 2):
                if ln.strip() == "---":
                    end = i
                    break
    except Exception:
        end = 0
    _FM_END[rel] = end
    return end


def _grep(cmd: list[str], cwd: Path, strip_frontmatter: bool = False) -> list[str]:
    """跑 grep，返回 `文件:行号: 摘要`。

    🔴 两处必要的后处理（2026-09-17 实测：不做则输出 38KB 不可读）：
    1. **截断单行**——本仓 `changelog:` 字段可达 10KB 量级（会话报告工作流曾使用多行块标量），不截断则一行刷屏。
    2. **剔除 frontmatter 区**（可选）——`standards/06` §2-5 ② 的判据是「是否仍在**指令**写/读」，
       changelog/登记字段属**历史记录**，不是残留；且长 changelog 会把
       ③虚假宣称层（正则含「校验|闸门」）**假命中**成残留。
    """
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except Exception as e:  # pragma: no cover
        return [f"<grep 失败：{e}>"]
    out = []
    for ln in (r.stdout or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit():
            rel, no, text = parts[0], int(parts[1]), parts[2]
            if strip_frontmatter and no <= _frontmatter_end(rel, cwd):
                continue
            text = text.strip()
            if len(text) > 160:
                text = text[:160] + " …[截断]"
            out.append(f"{rel}:{no}: {text}")
        else:
            out.append(ln[:200])
    return out


# ---------------------------------------------------------------------------
# 写侧工具（MEMORY.md 按字节 + 保持原行尾 + 幂等）
# ---------------------------------------------------------------------------


def _slug_from_line(line: str) -> str | None:
    m = re.search(r"\]\(([^)]+)\)", line)
    if not m:
        return None
    name = Path(m.group(1)).name
    return name[:-3] if name.endswith(".md") else name


def _dominant_eol(raw: bytes) -> bytes | None:
    """返回文件的**主导行尾**（纯 CRLF → b"\\r\\n"；纯 LF → b"\\n"）；混入两种 → None。

    🔴 2026-09-19 订正：原判据**硬编码「必须纯 CRLF」**，与语料实盘不符——实测记忆目录
    129 条中 **125 条为纯 LF**，`MEMORY.md` 自身也是纯 LF ⇒ 写侧两个入口
    （`--append-line` / `--replace-line`）**一律 ABORT、完全不可用**，Phase 5f-5 无从执行。
    本守卫的**目的**是「不破坏文件自身的行尾」，而非「必须是 CRLF」
    ⇒ 改为「保持原行尾」，混合行尾仍拒绝（`standards/06` §3.1 ③：匹配口径须与语料实盘对拍）。
    """
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    if crlf and lf:
        return None
    return b"\r\n" if crlf else b"\n"


def remove_index_line(mem: Path, slug: str) -> int:
    """按字节删除某条记忆的索引行（**退役**动作）。

    退役 = 删索引行（= 每会话必载的那份成本）+ 删除正文文件。本函数只做前者。
    🔴 命中数必须**恰为 1**：0 说明 slug 写错或已退役，>1 说明索引已损坏——
    两种情况都拒绝写入（fail-closed），不做「尽力而为」的部分删除。
    """
    p = mem / INDEX_NAME
    raw = p.read_bytes()
    EOL = _dominant_eol(raw)
    if EOL is None:
        print(f"ABORT: {INDEX_NAME} 混入两种行尾（CRLF {raw.count(b'\r\n')} / "
              f"LF {raw.count(b'\n') - raw.count(b'\r\n')}）——先人工确认行尾，勿在此状态下写入。")
        return 2
    lines = raw.split(EOL)
    hits = [i for i, ln in enumerate(lines)
            if slug in _slugs_on_line(ln.decode("utf-8", "replace"))]
    if len(hits) != 1:
        print(f"ABORT: --remove-line {slug} 命中 {len(hits)} 行（预期 1）——"
              f"0 = 未索引或 slug 写错；>1 = 索引损坏（同一 slug 出现两处）。不写。")
        return 2
    i = hits[0]
    old_line = lines[i].decode("utf-8", "replace")
    others = [s for s in _slugs_on_line(old_line) if s != slug]
    if others:
        # 🆕 C（2026-09-28）：**家族行只摘该链**——保留同行其余链接与共享 hook。
        #   旧实现按行首链接定位**整行** ⇒ 对家族行首链接执行退役会整行删除、
        #   连带把同行其余记忆从索引抹掉（正文仍在 ⇒ 变孤儿 + 每会话不再加载）。
        new_line = ANY_LINK_RE.sub(
            lambda m: "" if os.path.basename(m.group(1))[:-3] == slug else m.group(0),
            old_line)
        new_line = re.sub(r"^(-\s*)·\s*", r"\1", new_line)      # 首链接被摘 ⇒ 清前导「· 」
        new_line = re.sub(r"(\s*·\s*)+", " · ", new_line)        # 折叠分隔符
        new_line = re.sub(r"\s*·\s*—\s*", " — ", new_line)       # 末链接被摘 ⇒ 修「· —」
        new_line = new_line.rstrip()
        assert set(_slugs_on_line(new_line)) == set(others), "摘链后 slug 集合异常"
        lines[i] = new_line.encode("utf-8")
        removed, action = old_line, "UNLINK(%d→%d)" % (len(others) + 1, len(others))
    else:
        removed, action = lines.pop(i), "REMOVE"
    out = EOL.join(lines)
    if _dominant_eol(out) != EOL:
        print("ABORT: 写出前自检失败（行尾不再是原行尾）—— 不写。")
        return 2
    if not out.endswith(EOL):
        out += EOL
    p.write_bytes(out)
    print(f"{action} {slug}  行 {len(removed)} 字符  字节 {len(raw)} -> {len(out)}  "
          f"EOL {'CRLF' if EOL == b'\r\n' else 'LF'}")
    return 0


def write_index_line(mem: Path, slug: str, line: str, replace: bool) -> int:
    p = mem / INDEX_NAME
    raw = p.read_bytes()
    EOL = _dominant_eol(raw)
    if EOL is None:
        print(f"ABORT: {INDEX_NAME} 混入两种行尾（CRLF {raw.count(b'\r\n')} / "
              f"LF {raw.count(b'\n') - raw.count(b'\r\n')}）——先人工确认行尾，勿在此状态下写入。")
        return 2
    new = line.rstrip("\r\n").encode("utf-8")

    # 🔴 slug **必须取自行本身**，不能信调用方传的 `--append-line` 值。
    #    2026-09-17 实证：传了与行内链接不一致的 slug（`s1` vs
    #    `gate-must-have-convergent-green-state`）⇒ 幂等守卫**永不命中**，同一行被追加两次。
    #    故此处以行内 slug 为准，且与调用方声明不一致时 **fail-closed 拒绝写入**。
    derived = _slug_from_line(line.rstrip("\r\n"))
    if not derived:
        print(f"ABORT: --line-file 内容里找不到 `](<slug>.md)` 形式的链接，无法判定幂等键—— 不写。")
        return 2
    line_slugs = _slugs_on_line(line.rstrip("\r\n"))
    if slug not in line_slugs:
        # 🔴 C（2026-09-28）：原判据要求 slug == **行首**链接；家族行下放宽为
        #   「slug 须出现在行内」——否则对家族行的第 2..N 个链接无法用本入口替换。
        print(f"ABORT: --append-line/--replace-line 的 slug（{slug}）不在 --line-file 的链接集"
              f"（{line_slugs}）内 —— 不写。幂等键取自行本身，请让二者一致。")
        return 2

    lines = raw.split(EOL)
    hits = [i for i, ln in enumerate(lines)
            if slug in _slugs_on_line(ln.decode("utf-8", "replace"))]

    if replace:
        if len(hits) != 1:
            print(f"ABORT: --replace-line 命中 {len(hits)} 行（预期 1）—— 不写。")
            return 2
        old_slugs = set(_slugs_on_line(lines[hits[0]].decode("utf-8", "replace")))
        if len(old_slugs) > 1:
            # 🆕 C：家族行替换须**保持同一 slug 集合**——防「压 hook」时误丢同行记忆。
            if set(line_slugs) != old_slugs:
                print(f"ABORT: --replace-line {slug} 命中的是**家族行**（{len(old_slugs)} 个链接）——"
                      f"替换后 slug 集合须与原文一致（原 {sorted(old_slugs)} vs 新 {sorted(line_slugs)}），"
                      f"否则会静默丢弃同行记忆。不写。")
                return 2
        lines[hits[0]] = new
        action = "REPLACE"
    else:
        if hits:
            print(f"SKIP（幂等）：{slug} 已在索引中（含家族行内），未写入。")
            return 0
        if lines and lines[-1] == b"":
            lines[-1] = new
        else:
            lines.append(new)
        action = "APPEND"
    out = EOL.join(lines)
    if not out.endswith(EOL):
        out += EOL
    if _dominant_eol(out) != EOL:
        print("ABORT: 写出前自检失败（行尾不再是原行尾）—— 不写。")
        return 2

    # 🔴 写入侧容量闸门（🆕 2026-09-29）：**fail-closed 先于副作用**。
    #    越过 harness 读上限后，超出部分的条目在**每一次加载时被静默丢弃**（尾部不可见）
    #    ⇒ 拒绝写入，先处置再重试。判据与读侧共用 `capacity_state`（同口径，不另立阈值）。
    st = capacity_state(out)
    if st["level"] == "over":
        print(f"ABORT: 本次写入会把 {INDEX_NAME} 推过 harness 读上限"
              f"（{st['chars']:,} 字符 / {st['lines']} 行 vs 上限 "
              f"{INDEX_CHAR_CAP:,} / {INDEX_LINE_CAP}）——\n"
              f"  超出部分的条目会在**每一次加载时被静默丢弃**（尾部不可见）⇒ 不写。\n"
              f"  先处置再重试：① 压最长 hook（--replace-line，只压 hook 不删条目）；"
              f"② 合并同族条目（准入判据见本文件 G_mem 家族说明）；"
              f"③ 结构性处置见工作台账 #286（两级索引）。")
        return 2
    if st["level"] != "ok":
        print(f"⚠️  写入后 {INDEX_NAME} 为上限的 {100 * st['frac_chars']:.1f}%（字符）/ "
              f"{100 * st['frac_lines']:.1f}%（行）＝ {st['chars']:,} 字符 / {st['lines']} 行"
              f"（{'已过警戒线' if st['level'] == 'warn' else '已过目标线'}；瓶颈维 {st['binding']}）")
    p.write_bytes(out)
    print(f"{action} {slug}  字节 {len(raw)} -> {len(out)}  "
          f"EOL {'CRLF' if EOL == b'\r\n' else 'LF'}")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def append_member_line(mem: Path, topic: str, line_file: str) -> int:
    """把一行成员索引写进二级索引 `_topics/<topic>.md`（两级形态的写入口）。

    与 `write_index_line()` **同构**（按字节、保持原行尾、幂等、slug 取自行本身、
    命中数守卫），差别只有两点：
      ① 目标文件为 `mem/_topics/<topic>.md`，不存在则创建（行尾取 LF）；
      ② **不做容量闸门**——二级文件不在每会话必载面，不适用 25,000 字符 / 200 行上限。
    🔴 不复用 `write_index_line()` 指向二级文件：它内嵌 `INDEX_NAME` 与容量闸门，语义不同。
    """
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", topic):
        print(f"ABORT: topic 只允许 [A-Za-z0-9_-]（收到 {topic!r}）—— 不写。")
        return 2
    line = Path(line_file).read_text(encoding="utf-8").rstrip("\r\n")
    if not line:
        print("ABORT: --line-file 为空 —— 不写。")
        return 2
    derived = _slug_from_line(line)
    if not derived or derived not in _slugs_on_line(line):
        print("ABORT: 行内找不到 `](<slug>.md)` 形式的链接（幂等键取自行本身）—— 不写。")
        return 2
    topic_dir = mem / TOPIC_DIR
    topic_dir.mkdir(parents=True, exist_ok=True)
    p = topic_dir / f"{topic}.md"
    EOL = _dominant_eol(p.read_bytes()) if p.exists() else b"\n"
    if EOL is None:
        print(f"ABORT: {TOPIC_DIR}/{topic}.md 混入两种行尾 —— 先人工确认，勿写入。")
        return 2
    lines = p.read_bytes().split(EOL) if p.exists() else []
    if any(derived in _slugs_on_line(x.decode("utf-8", "replace")) for x in lines):
        print(f"SKIP（幂等）：{derived} 已在 {TOPIC_DIR}/{topic}.md 中，未写入。")
        return 0
    out = EOL.join([x for x in lines if x != b""] + [line.encode("utf-8")]) + EOL
    if _dominant_eol(out) != EOL:
        print("ABORT: 写出前自检失败（行尾不再是原行尾）—— 不写。")
        return 2
    p.write_bytes(out)
    print(f"APPEND-MEMBER {derived} -> {TOPIC_DIR}/{topic}.md  "
          f"EOL {'CRLF' if EOL == b'\\r\\n' else 'LF'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="跨会话记忆系统读侧/维护侧设施")
    ap.add_argument("--memory-dir")
    ap.add_argument("--repo", default=str(REPO_ROOT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--retire", action="store_true")
    ap.add_argument("--append-line", metavar="SLUG")
    ap.add_argument("--append-member", metavar="TOPIC",
                    help="两级形态：把成员行追加进 _topics/<TOPIC>.md（幂等；不存在则新建）")
    ap.add_argument("--replace-line", metavar="SLUG")
    ap.add_argument("--remove-line", metavar="SLUG", help="退役：按字节删除该记忆的索引行")
    ap.add_argument("--line-file", help="包含索引行（--append-line/--replace-line 用）")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    mem = find_memory_dir(args.memory_dir)

    if args.retire:
        return run_retire(mem, repo)

    if mem is None:
        msg = ("⚠️ 未找到记忆目录（git 之外，用户级）。若本机无此设施，属正常：\n"
               "   试过：--memory-dir / $NOMOS_MEMORY_DIR / ~/.claude/projects/<本仓 slug>/memory\n"
               "   本设施在无记忆目录的机器上**静默跳过**，不影响任何流程。")
        if args.json:
            print(json.dumps({"ok": True, "skipped": True, "reason": "memory dir not found"},
                             ensure_ascii=False, indent=2))
        else:
            print(msg)
        return 0

    if args.remove_line:
        return remove_index_line(mem, args.remove_line)

    if args.append_member:
        if not args.line_file:
            print("用法错误：--append-member 需要 --line-file <path>", file=sys.stderr)
            return 2
        return append_member_line(mem, args.append_member, args.line_file)

    if args.append_line or args.replace_line:
        if not args.line_file:
            print("用法错误：--append-line/--replace-line 需要 --line-file <path>", file=sys.stderr)
            return 2
        line = Path(args.line_file).read_text(encoding="utf-8")
        slug = args.append_line or args.replace_line
        return write_index_line(mem, slug, line, replace=bool(args.replace_line))

    index_bytes = read_index_bytes(mem)
    index_text = index_bytes.decode("utf-8", errors="replace")
    bodies = load_memories(mem)

    struct = gate_structure(mem, index_text, bodies)
    budget = gate_budget(index_bytes, bodies, index_text)
    refs = gate_references(bodies, repo, mem)
    per_mem = gate_per_memory(bodies)

    if args.json:
        print(json.dumps({"memory_dir": str(mem), "repo": str(repo),
                          "gates": [struct, budget, refs, per_mem]},
                         ensure_ascii=False, indent=2))
    else:
        print(render_report(struct, budget, refs, per_mem))

    return 1 if any(p["severity"] == "FAIL" for p in struct["problems"]) else 0


if __name__ == "__main__":
    sys.exit(main())
