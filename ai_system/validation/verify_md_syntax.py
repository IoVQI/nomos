#!/usr/bin/env python3
"""
verify_md_syntax.py — Markdown 转录产物语法校验与 LaTeX ↔ MinerU 交叉校验

用法:
    verify_md_syntax.py <file.md> [--source {latex|mineru|unknown}] [--json] [--cross-check]
    verify_md_syntax.py --all [--source {latex|mineru}] [--json] [--cross-check]
    verify_md_syntax.py --fences-only <path|dir>...   # 只跑围栏配平；未标注 A 类 -> exit 1
                                                      # （pre-commit `files: \\.md$` 钩子用）

检查项:
    1. Math Block Pairing    — $$ \\begin{}...\\end{} 配对 (ERROR)
    2. Table Column Consistency — Markdown 表格列数一致性 (WARNING)
    3. Image Reference Validity  — ![](path) 文件存在性 (WARNING)
    4. LaTeX Residual Commands   — \\ref, \\cite 等未展开命令 (WARNING)
    5. UTF-8 Strict Decode       — 严格解码验证 (ERROR)
    6. Cross-check (--cross-check) — LaTeX ↔ MinerU 结构指纹比对 (ERROR/WARNING)
    7. Fence Balance         — 围栏未闭合（文件末仍在栏内 ⇒ 其后正文被渲染为代码块）(WARNING)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ── 3.1 Math Block Pairing ────────────────────────────────────────────────

_FENCE_RE = re.compile(r'^(?P<f>`{3,}|~{3,})(?P<rest>.*)$')


def _fence_parts(line):
    """行是围栏行则返回 (fence_char, run_len, info_string)，否则 None。

    🔴 info string 含 `$ \\ { }` 者判为**正文**而非围栏：LaTeX 语料里
    `~~~\\mbox{and}` / ``` ```\\begin{array} ``` 是间距命令或源码残片
    （2026-09-11 全量回归实证：误判为围栏会吞掉整段真实数学，4 份转录假 FAIL）。
    """
    m = _FENCE_RE.match(line.strip())
    if not m:
        return None
    rest = m.group('rest').strip()
    if any(ch in rest for ch in '$\\{}'):
        return None
    f = m.group('f')
    return f[0], len(f), rest


def _mask_code_spans(content):
    """把围栏代码块与行内代码跨度替换为**等长空白**（保留换行与行号）。

    2026-09-11 修复（工作备忘录 #186）：正文里写在行内代码中的 LaTeX 环境名
    （如 `\\begin{figure}`）与 `$$` 是**字面文本**而非数学——此前会被判为
    「Unclosed」。markdown 语义中代码跨度/围栏内一律为字面量，故先屏蔽再配对。
    等长替换保证行号/列号不漂移。

    围栏**必须有配对闭合行**才屏蔽（无闭合者按普通行处理）——宁可少屏蔽，
    也不把文件后半段整片吞成空白。
    """
    lines = content.split('\n')
    out = []
    i, n = 0, len(lines)
    while i < n:
        cand = _fence_parts(lines[i])
        if cand is not None:
            ch, ln = cand[0], cand[1]
            close = -1
            for k in range(i + 1, n):
                c2 = _fence_parts(lines[k])
                if c2 is not None and c2[0] == ch and c2[1] >= ln and c2[2] == '':
                    close = k
                    break
            if close != -1:
                for k in range(i, close + 1):
                    out.append(' ' * len(lines[k]))
                i = close + 1
                continue
        out.append(_mask_inline_code(lines[i]))
        i += 1
    return '\n'.join(out)


_CODE_TOKEN_RE = re.compile(
    r'\s*(?:\$\$|\\{1,2}[A-Za-z]+(?:\{[^{}]*\}|\[[^\[\]]*\])*)\s*\Z'
)


def _mask_inline_code(line):
    """屏蔽「整段恰为一个 LaTeX 记号」的行内代码跨度 `` `...` ``。

    🔴 **白名单，不是任意反引号对**：本仓语料里反引号大量用于 LaTeX 引号惯用法
    （`` `word' `` 单引号 / ``` ``word'' ``` 双引号，2026-09-11 全量实测多反引号串
    612 行、单反引号对遍布 LaTeX 源格式转录）。任意配对会把引号之间的**真实** `$$` /
    ``\\begin`` 一并屏蔽 → 假 FAIL（4 份转录实证：Kruger_etal_2025 / Barik_etal_2013 /
    Cai_2025 / Margueron_etal_2025）。

    故只屏蔽内容整体匹配 `_CODE_TOKEN_RE` 的跨度（`$$`、``\\begin{env}``、``\\end{env}`` 等
    单记号）——正是 #186 报告的场景；引号惯用法的跨度内容为散文，一律不动。
    未闭合/非白名单的反引号串按普通文本保留（宁可不屏蔽，也不吞掉真实内容）。

    🔴 2026-09-15 收窄修正（工作备忘录 #210）：原白名单只认「单反斜杠 + **至多一个**花括号组」，
    致 **≥2 组**的记号（`\\begin{frame}{标题}`、`\\csectionpage[序号]{小节名}`、
    `\\ctitlepage{…}{…}{…}`）不被屏蔽 → 被当真环境开启，报 `Unclosed` **假 FAIL**。
    现按**内容类**判定：可选 1–2 个反斜杠 + 命令名 + **任意个** `{…}` / `[…]` 组。

    过宽的两个护栏（这正是本条**没有**走「任意反引号配对」的原因，见上段 #186 实证）：
      ① 组之间**只允许空白**，不允许散文 ⇒ 引号惯用法跨度（`` `\\cite{a}' and `\\cite{b}' ``）
         依旧匹配不上，真实数学标记不会被一并屏蔽；
      ② 反引号**之外**的内容永不经过本正则（`_mask_inline_code` 只对单反引号跨度咨询它）
         ⇒ 正文里真正未闭合的 `\\begin{...}` 照旧 FAIL。
    """
    n = len(line)
    is_single = [False] * n          # 只认「长度恰为 1 的反引号串」
    i = 0
    while i < n:
        if line[i] != '`':
            i += 1
            continue
        j = i
        while j < n and line[j] == '`':
            j += 1
        if j - i == 1:
            is_single[i] = True
        i = j

    chars = list(line)
    i = 0
    while i < n:
        if not is_single[i]:
            i += 1
            continue
        k = i + 1
        while k < n and not is_single[k]:
            k += 1
        if k >= n:
            break  # 未闭合：按普通文本处理
        if _CODE_TOKEN_RE.match(line[i + 1:k]):
            for p in range(i, k + 1):
                chars[p] = ' '
            i = k + 1
        else:
            i += 1  # 非白名单形态：不消费，继续找下一个
    return ''.join(chars)


def check_math_pairing(content):
    """栈匹配：$$ 和 \\begin{env}...\\end{env} 的完整性。

    代码跨度/围栏内的字面 `$$`、`\\begin{...}` 先被屏蔽（2026-09-11，#186）。
    """
    errors = []
    lines = _mask_code_spans(content).split('\n')
    display_opened = False
    stack = []  # (line_no, env)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 独立 $$ 行（仅 $$，无其他内容）
        if stripped == '$$':
            display_opened = not display_opened
            continue

        # 统计行内所有 $$ 的出现次数
        dollar_count = stripped.count('$$')
        if dollar_count == 0:
            pass  # no $$ on this line
        elif stripped.startswith('$$') and stripped.endswith('$$') and dollar_count == 2:
            # $$\begin{aligned}...\end{aligned}$$ — 完整配对环境，不改变状态
            pass
        elif stripped.startswith('$$'):
            # 行首 $$ —— 显示数学开始
            if display_opened:
                errors.append({
                    'level': 'ERROR', 'line': i, 'type': 'math_pairing',
                    'detail': 'Nested $$ at start of line (already in display math)'
                })
            display_opened = True
            # 检查剩余部分（去掉开头 $$ 后）是否还有 $$（可能格式为 $$\begin{aligned}...$$）
            remainder = stripped[2:]
            if remainder.endswith('$$'):
                display_opened = False
            elif remainder.count('$$') % 2 != 0:
                display_opened = not display_opened
        elif stripped.endswith('$$'):
            # 行尾 $$ —— 显示数学结束
            if not display_opened:
                errors.append({
                    'level': 'ERROR', 'line': i, 'type': 'math_pairing',
                    'detail': 'Closing $$ at end of line without opening'
                })
            display_opened = False
        elif dollar_count % 2 == 1:
            # $$ 出现在行中间且为奇数个——显示数学状态翻转
            display_opened = not display_opened
        else:
            # $$ 出现在行中间且为偶数个——显示数学开+闭，状态不变
            pass

        # \begin{env} / \end{env}
        begins = re.findall(r'\\begin\{([^}]+)\}', stripped)
        ends   = re.findall(r'\\end\{([^}]+)\}', stripped)

        for env in begins:
            stack.append((i, env))
        for env in ends:
            if not stack:
                errors.append({
                    'level': 'ERROR', 'line': i, 'type': 'math_pairing',
                    'detail': f'\\end{{{env}}} without matching \\begin'
                })
            elif stack[-1][1] != env:
                errors.append({
                    'level': 'ERROR', 'line': i, 'type': 'math_pairing',
                    'detail': f'\\end{{{env}}} mismatches \\begin{{{stack[-1][1]}}} at line {stack[-1][0]}'
                })
                stack.pop()
            else:
                stack.pop()

    # 残留未闭合
    for line_no, env in stack:
        errors.append({
            'level': 'ERROR', 'line': line_no, 'type': 'math_pairing',
            'detail': f'Unclosed \\begin{{{env}}}'
        })
    if display_opened:
        errors.append({
            'level': 'ERROR', 'line': 0, 'type': 'math_pairing',
            'detail': 'Unclosed display math $$ block'
        })

    return len(errors) == 0, errors


def check_brace_balance(content):
    """
    检查 $$...$$ 和 $...$ 数学块内花括号 { } 配对完整性。
    检测 \\frac{ 或 \\sqrt{ 缺少闭合 } 导致的 KaTeX 解析错误。

    排除:
      - \\{ 和 \\} (转义字面量花括号)
      - \\begin{env}{opts} 中的 {opts} (列说明符，非分组括号)
    """
    errors = []
    math_blocks = []
    # 先屏蔽代码跨度/围栏（2026-09-11，#186）：否则行内代码里的 `$$` 会与后文
    # 真实的 $$ 误配对，圈出一段假数学块 → 假 brace_balance FAIL。
    masked = _mask_code_spans(content)
    for m in re.finditer(r'\$\$.*?\$\$|\$[^$]+\$', masked, re.DOTALL):
        math_blocks.append((m.start(), m.end(), m.group()))

    for start, end, block in math_blocks:
        # 移除转义花括号（\{ 和 \}）
        cleaned = block.replace('\\{', '').replace('\\}', '')
        # 移除 \begin{env}{opts} 中的列说明符括号
        # 如 \begin{array}{ll} → 移除 {ll}
        cleaned = re.sub(r'\\begin\{[^}]+}\{([^}]+)\}', r'\\begin{\1}', cleaned)
        # 移除 \left\{ 和 \right\}（它们是定界符，不是分组）
        cleaned = cleaned.replace('\\left\\{', '').replace('\\right\\}', '')
        # 移除 \bigl\{, \bigr\}, \Bigl\{, \Bigr\} 等
        cleaned = re.sub(r'\\[Bb]ig[glr]?\\\{', '', cleaned)
        cleaned = re.sub(r'\\[Bb]ig[glr]?\\\}', '', cleaned)

        opens = cleaned.count('{')
        closes = cleaned.count('}')
        if opens != closes:
            line_no = content[:start].count('\n') + 1
            delta = opens - closes
            direction = 'unclosed' if delta > 0 else 'extra closing'
            errors.append({
                'level': 'ERROR', 'line': line_no, 'type': 'brace_balance',
                'detail': f'{abs(delta)} {direction} braces ({{ = {opens}, }} = {closes}) in math block at col {start}'
            })

    return len(errors) == 0, errors


def check_eps_leak(content):
    """🔴 检测 Markdown 中错误内嵌的 EPS/PostScript 原始内容。"""
    errors = []
    markers = ['%!PS-Adobe', '%%BoundingBox', '%%LanguageLevel', '%%Creator', '%%EOF']
    for marker in markers:
        if marker in content:
            count = content.count(marker)
            errors.append({
                'level': 'ERROR', 'type': 'eps_leak',
                'detail': f'Raw EPS/PostScript content found: "{marker}" appears {count} time(s). '
                          'Run latex_to_markdown.py v1.5.0+ with _strip_raw_postscript() guard.'
            })
    # Deduplicate
    seen = set()
    unique = []
    for e in errors:
        if e['detail'] not in seen:
            seen.add(e['detail'])
            unique.append(e)
    return len(unique) == 0, unique


# ── 3.1b Fence Balance（围栏配平，GFM A 类）───────────────────────────────
# 🔴 与上方 3.1 的围栏工具**同源但不同事**：`_fence_parts` / `_mask_code_spans` 管的是
#    「围栏**内**要不要遮蔽」（工 #278），本函数管的是「围栏**是否配平**」（工 #279）。
#    两者判据**故意不一致** —— 差异与其正当性见 `check_fence_balance` docstring。

_GFM_FENCE_RE = re.compile(r'^(?P<indent> {0,3})(?P<f>`{3,}|~{3,})(?P<rest>.*)$')


def _gfm_fence(line):
    """按 GFM 规范判定该行是否为**围栏行**；是则返回 (字符, 连续长度, info 串)，否则 None。

    GFM §4.5（Code fences）两条易错规则：
      · 开栏 = 行首 **≤3 空格**缩进 + ≥3 连续 ` 或 ~；`~` 栏的 info 串无限制，
        **` 栏的 info 串内不得再含 `**；
      · 闭栏 = 同字符、连续长度 ≥ 开栏，且**除空白外无其他内容**。

    🔴 缩进上限必须判，不能 `line.strip()` 后匹配：4 空格以上是**缩进代码块**，不是围栏。
    本模块既有的 `_fence_parts` 走的是 `strip()` + 「info 串含 `$ \\ { }` 判为正文」的
    **LaTeX 语料口径**，那是为 math_pairing 的遮蔽服务的，不可挪用到这里（见下）。
    """
    m = _GFM_FENCE_RE.match(line)
    if not m:
        return None
    f = m.group('f')
    return f[0], len(f), m.group('rest')


def _scan_fences(content):
    """单遍状态机（**唯一实现**：`check_fence_balance` 与 `run_fences_only` 共用）。

    返回 `(unclosed, ambiguous)`：
      · `unclosed` = 文件末尾仍在栏内时，该开栏的 `(字符, 长度, 行号)`；配平则为 `None`（**A 类**）；
      · `ambiguous` = `[(行号, 所属开栏行号)]`，栏内「同字符且长度 ≥ 开栏、却带 info 串」的行
        —— GFM 下**不是**闭栏（**B 类**，是 A 类的常见成因）。

    🔴 只此一处状态机：`check_fence_balance` 的 A 类诊断与 `run_fences_only` 的 A/B 两路
    都从这里取，避免两份实现分叉（同族事故：执行器与校验器各写一份解析 → 格式演进后分叉）。
    """
    inside, ambiguous = None, []
    for lineno, line in enumerate(content.split('\n'), 1):
        parts = _gfm_fence(line)
        if parts is None:
            continue
        ch, run, rest = parts
        if inside is None:
            # GFM：反引号栏的 info 串内不得含反引号（含则整行不是围栏）
            if ch == '`' and '`' in rest:
                continue
            inside = (ch, run, lineno)
        elif ch == inside[0] and run >= inside[1]:
            if rest.strip() == '':
                inside = None            # 合法闭栏
            else:
                ambiguous.append((lineno, inside[2]))   # 同字符够长却带 info 串 ⇒ 非闭栏
    return inside, ambiguous


def check_fence_balance(content):
    """围栏配平（只报 **A 类**：文件末尾仍在栏内 ⇒ 其后正文被渲染为代码块）。

    判据真源 = GFM §4.5，由 `_gfm_fence` 实现（规则见其 docstring）。**不用朴素奇偶配对**：
    朴素口径把 `   ```yaml` 一类**带 info 串的行**当成闭栏 ⇒ 2026-09-27 对端会话据此
    误报过 3717 行（工作台账 #279）。口径差是实质的：同一语料上两种口径给出**不同**的文件集
    —— 复算见对照脚本 `sandbox/_scripts/archive/2026-09-27_fence_gate_contrast.py` 的 [C] 组
    （该组即断言「错误口径必须与 GFM 口径不一致」，两者相同即判 FAIL）。

    **为何只报 A 类、不报 B 类**（「带 info 串的疑似闭栏」）：
      · B 类不是缺陷本身，而是 A 类的**常见成因**（一个游离闭栏会把文件后半段吞掉）；
      · B 类在维护面有大量实例（真值：普查脚本 `2026-09-27_fence_balance_survey.py` 的
        B 类清单），逐例判定属 #279 **任务 3**（人工裁定，未放行）。若在此一并报告，
        会让任何以其为输入的自动面长期非零 ⇒ 闸门不收敛（`gate-must-have-convergent-green-state`）。
      故本函数对 B 类**不产出诊断**，但在 A 类诊断里附上「最后一条疑似闭栏」的行号，
      使告警可定位（不额外报告，只作附注）。

    🔴 **为何是 WARNING 而**不**阻断**（交接 §1 判据④要求写明）：
      1. **A 类剩余面全在非维护面**：`references/` 那 3 例（行首 LaTeX `~~~` 被 GFM 读作开栏）
         已于 2026-09-27 按 #279 任务 2 修掉（改编码不改内容：前缀空组 `{}`，数学内渲染逐位不变）；
         仍存在的 A 类只剩第三方克隆仓与沙箱产物 ⇒ 对它们阻断没有维护意义
         （同 `gate-scope-expansion-vs-legacy-ratchet`）。
      2. **不同渲染器口径不同**：本仓 LaTeX 语料里 `{}~~~\\mbox{and}` 一类行，GFM 读作开栏，
         而本模块 `_fence_parts` 的 LaTeX 口径读作正文。判据本身正确（GFM 就是会吞），
         但「该按哪个渲染器算数」是**判读问题**，不宜由它阻断提交。
      3. **阻断职责已由 `--fences-only` 承担**：本模块另有一路**显式门禁**（见
         `run_fences_only`），对「未标注的 A 类」非零退出，供 pre-commit 的 `.md` 级钩子消费。
         两路是**同一判据的两种严重度分层**，按调用者意图选择；本路保持信号层，
         以免 `--all` / CI 因非维护面转红（先例：`check_sandbox_layout.py` 的 S6，
         工作台账 #226，同为「必须机械有信号，但不阻断」）。
      退出码影响：本模块只按 **ERROR** 计退出码（`main` 的 `--all` 与逐文件两路皆是），
      故 WARNING 天然不阻断 —— 这是本判据**收敛**的机制性保证，不是「暂不接线」。

    ⚠️ **CI 可见性**：**是 CI 可见的**（`.github/workflows/test.yml` 跑 `--all`），但因上条
      故不改变 CI 红绿。反过来，pre-commit 面 `files: ^references/.*_extracted_text\\.md$`
      **只覆盖 references/** ⇒ 2026-09-27 那批真阳性（全在 `ai_system/` 与 `records/`）
      不在这两条自动面内，只有显式传路径或另接钩子才被扫到。这是**作用域事实**，非本判据的缺陷。

    与 `_fence_parts` 的关系（🈲 勿混为一谈）：`_fence_parts` 的 `info 串含 $ \\ { } ⇒ 正文`
    是**为遮蔽服务**的保守口径（宁可少屏蔽），本函数**不使用**它 —— 否则 `~~~\\mbox{and}`
    这类真会把文件吞成代码块的行会漏报。
    """
    unclosed, ambiguous = _scan_fences(content)
    if unclosed is None:
        return True, []
    ch, run, start = unclosed
    lines = content.split('\n')
    detail = (
        f'Unclosed {ch * 3} fence opened at L{start}: the remaining '
        f'{len(lines) - start} line(s) render as a code block (GFM). '
        f'Closing fence must be the same character, at least as long, '
        f'and carry no info string.'
    )
    last_amb = [ln for ln, op in ambiguous if op == start]
    if last_amb:
        # 🔴 detail 串**必须纯 ASCII**：本模块在 Windows GBK 控制台下直接 print，
        #    非 GBK 字符（2026-09-27 实测 `⇒` U+21D2）会让 print_result 崩在
        #    UnicodeEncodeError 上，把一个 WARNING 变成整个脚本的 traceback。
        detail += (f' [suspected culprit: L{last_amb[-1]} - same char & length '
                   f'but carries an info string, so not a closing fence in GFM]')
    return False, [{'level': 'WARNING', 'line': start, 'type': 'fence_balance',
                    'detail': detail}]


# ── 3.1c 围栏配平的「已标注桶」与 `--fences-only` 阻断模式 ─────────────────
# 🔴 桶与模式服务于 pre-commit 的 `files: \.md$` 钩子（#279）：那条钩子会把**非转录 md**
#    也喂进来，故须①只跑围栏判据、②对存量已裁定例设豁免，否则钩子永久红（不收敛）。

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: **已标注桶**（repo 相对路径 -> 豁免理由）：`--fences-only` 下**始终打印、不计判定**。
#: 用于第三方克隆仓、转录产物等**非维护面**文件。
#: 🔴 新增条目须逐条说明理由，**不得**为让钩子变绿而加。
FENCE_KNOWN_UNBALANCED: dict[str, str] = {}


def run_fences_only(paths, use_all=False, stream=None):
    """`--fences-only`：只跑围栏配平，且把**未标注**的 A 类判为失败（阻断模式）。

    与模块另两路（`--all` / 逐 positional）的差别——**后者一格不动**：

    | | 跑什么 | 退出码判据 |
    |---|---|---|
    | `--all` / 逐文件 | 全部检查 | 只按 **ERROR** 数（WARNING 从不阻断） |
    | `--fences-only` | **只跑**围栏判据（A 类 **+** B 类信号） | **未标注 A 类 > 0 即非零** |

    🆕 **B 类信号**（2026-09-28，工 #279 任务 3 结项时补）：B 类（栏内「同字符、长度 ≥ 开栏、
    却带 info 串」的行）**只打印 `NOTICE`、不计判定**。理由是它**是 A 类的前身**——
    同行数嵌套（引文里嵌代码块）在 GFM 下会被合并，再走一步就成 A 类；而在升级之前本模块
    **原本零信号**。之所以不阻断也不必分桶：本模式的消费者（pre-commit `files: \\.md$`）
    只喂**暂存件** ⇒ 天然只覆盖「你正在改的文件」，历史件不动就永不报警 —— 对已裁定不处置的
    存量条目不会持续噪报，闸门仍收敛。

    为何本模式只跑一条检查：其消费者（pre-commit `files: \\.md$`）会把**非转录 md** 也喂进来；
    跑全套会把那些文件的既有 ERROR（`math_pairing` / `residual_commands` 等）变成对**无关提交**
    的阻断——正是 2026-09-17 把 `--all` 从全仓收窄到逐暂存件的同一成因。

    为何本模式才阻断：WARNING 在**其余两路**是真 WARNING（判读问题 + 存量不可修，见
    `check_fence_balance` docstring），而本模式是**显式调用者要的窄门禁** —— 对「新引入的
    围栏不配平」应当阻断。两者不矛盾：同一判据，两处严重度按调用者意图分层。

    已标注桶（`FENCE_KNOWN_UNBALANCED`）**逐条打印理由**但不计判定 —— 分「待裁决 / 已标注」
    两桶且已标注桶始终打印，是闸门可收敛的前提（`gate-must-have-convergent-green-state`）。

    🔴 路径一律按**仓库根**（`REPO_ROOT`）归一到 repo 相对再查桶：否则从 `lab/` 之类的
    子目录调用时，桶里的相对路径匹配不上 ⇒ 豁免**静默失效**（钩子假装绿）。

    计数语义（`skip-is-not-pass-zero-case-gate`）：**一个文件都没扫到 = 判红**，不是通过——
    显式给了路径却零命中通常是路径写错，静默通过会再造一个空洞闸门。
    """
    stream = stream or sys.stdout
    if use_all:
        files, empty_dirs = find_extracted_text_files(), []
    else:
        files, empty_dirs = expand_paths(paths)

    # 🔴 只收 markdown：围栏配平**只定义在 markdown 上**。`expand_paths` 对**显式给的目录**
    #    已按 `**/*.md` 展开，但显式给的**文件**原样返回 —— 若把 `.png`/`.pdf` 喂进来，
    #    文本读+替换会造出大量 `~~~` 假阳性（2026-09-27 实证：全量已跟踪文件喂入 → 24 条
    #    诊断里 21 条来自图像/PDF）。被丢掉的入参**显式计数打印**，不静默吞。
    skipped_inputs = [p for p in files if not p.lower().endswith(('.md', '.markdown'))]
    files = [p for p in files if p.lower().endswith(('.md', '.markdown'))]

    def _rel(p):
        try:
            return os.path.relpath(os.path.abspath(p), REPO_ROOT).replace(os.sep, "/")
        except ValueError:
            # Windows 跨盘（仓库在 D:、临时文件在 C:）时 relpath 抛 ValueError。
            # 回落到绝对路径：它必然不在桶里 => 计入未标注，是**正确的失败方向**（fail-closed）。
            return os.path.abspath(p).replace(os.sep, "/")

    annotated, unannotated, unreadable, notices = [], [], [], []
    for p in files:
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except OSError as exc:
            unreadable.append((_rel(p), str(exc)))
            continue
        ok, diags = check_fence_balance(content)
        unclosed, ambiguous = _scan_fences(content)
        if ambiguous:
            # 🆕 2026-09-28（工 #279 任务 3 结项）：B 类**只打印、不计判定**。
            #    它是 A 类的**前身**——同行数嵌套（引文里嵌代码块）在 GFM 下会被合并，
            #    再走一步就变成 A 类；而在变成 A 类之前**本模块原本零信号**。
            #    钩子面是「暂存件」⇒ 天然只覆盖**你正在改的文件**，历史件不动就永不报警
            #    （故不破坏收敛性、也不需要桶）。🔴 打印**不参与**退出码判定。
            notices.append((_rel(p), len(ambiguous), ambiguous[0][0]))
        if ok:
            continue
        item = (_rel(p), diags[0].get('line', 0), diags[0].get('detail', ''))
        (annotated if item[0] in FENCE_KNOWN_UNBALANCED else unannotated).append(item)

    # 🔴 全部输出走 `stream`（含首尾两行）——2026-09-27 实证：漏掉 file= 的两行会打到
    #    真 stdout，调用方传入 StringIO 时只截到明细行、计数行丢失 ⇒ 断言读到 0。
    def _p(msg):
        print(msg, file=stream)

    _p("[fences-only] scope: fence-balance check ONLY (not the full check suite)")
    _p("[fences-only] scanned %d file(s) | triggered %d | annotated %d | notice %d"
       % (len(files), len(annotated) + len(unannotated), len(annotated), len(notices)))
    for path, n, first in notices:
        _p("  NOTICE (not counted) %s -- %d line(s) with an info string inside a fence "
           "(GFM reads them as content, not closers); first at L%d. "
           "Same -length nesting degrades; use a LONGER outer fence to nest." % (path, n, first))
    for path, line, _ in annotated:
        # 已标注桶**始终打印**（含理由）——豁免不等于隐身
        _p("  ANNOTATED (not counted) %s L%d -- %s"
           % (path, line, FENCE_KNOWN_UNBALANCED[path]))
    for path, line, detail in unannotated:
        _p("  UNANNOTATED %s L%d -- %s" % (path, line, detail))
    for path, err in unreadable:
        _p("  UNREADABLE %s -- %s" % (path, err))
    for d in empty_dirs:
        _p("  NO-MD-DIR %s -- 显式给的路径下没有 .md（路径写错？）" % d)
    if skipped_inputs:
        _p("  SKIPPED %d non-markdown input(s) -- 围栏配平只定义在 markdown 上"
           % len(skipped_inputs))

    failed = bool(unannotated) or bool(unreadable) or bool(empty_dirs) or len(files) == 0
    if len(files) == 0:
        _p("  NO-FILES -- scanned 0 files => 判红（零用例不是通过）")
    _p("[fences-only] verdict: %s" % ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


# ── 3.2 Table Column Consistency ──────────────────────────────────────────

def _count_cell_delimiters(stripped):
    """按 GFM 表格语义返回该行**单元格分隔符**个数（= 列数 - 1）。

    GFM 规范 §4.10（Tables）：「Include a pipe in a cell's content by escaping it,
    **including inside other inline spans**」——两层含义，方向相反，必须分开处理：

    | 形态 | 语义 | 计为分隔符？ |
    |---|---|---|
    | 裸 `|`（**含反引号代码跨度内**） | 单元格分隔符 | ✅ 是 |
    | 反斜杠转义的 `\\|` | 单元格内的**字面**竖线 | ❌ 否 |

    判据取「该 `|` 之前是否有**奇数个**连续反斜杠」（`\\\\|` 是「字面反斜杠 + 分隔符」，仍算分隔符）。

    🔴 修正：原实现 `stripped.count('|') - 1` 把转义竖线也算作分隔符 ⇒
    对合法的 `\\|` 报假 `Column count mismatch`（实证：某会话索引文件中形如 `tex\\|sty` 的单元格）。
    原注释把它记为「已知边界、属独立缺陷」，本函数即该缺陷的修复。
    """
    delimiters = 0
    backslash_run = 0                      # 紧邻的连续反斜杠数
    for ch in stripped:
        if ch == '\\':
            backslash_run += 1
            continue
        if ch == '|' and backslash_run % 2 == 0:
            delimiters += 1
        backslash_run = 0
    return delimiters - 1


def check_table_columns(content):
    """检查 Markdown 表格列数一致性。

    🔴 **先过 `_mask_code_spans`（2026-09-27，工作台账 #278）**：原实现读**裸 `content`**，
    与本模块的兄弟检查（`check_math_residue` / `check_residual_commands` / `check_math_pairing`）
    不同约定。后果：**围栏代码块内**用 `|` 画的 ASCII 图（如状态机图）与**示例表格**被当成
    真表格行参与计数 ⇒ 全仓 656 条诊断中 **102 条（15.5%）**是假阳性（实测，见下）。

    为什么是假阳性：markdown 语义中围栏内一律为**字面文本**，`|…|` 不是表格行。
    `_mask_code_spans` **等长**替换（保留换行与行宽）⇒ 本函数依赖的行号不漂移。

    验证据点（`sandbox/_scripts/archive/2026-09-27_memo278_*.py`）：
      · 全仓前/后逐文件 diff = **纯缩减**，消失 102 条、**新增 0 条**；
      · 102 条**全部**落在 GFM 规则定义的围栏内（独立复刻配对规则做的第三方判定），
        即无一遮蔽真缺陷；
      · 行内代码遮蔽（`_mask_inline_code`）对本检查贡献 **0 条**差异 —— 引入的语义变化
        严格限于「围栏代码块」这一件事，未夹带其它变更。
    """
    warnings = []
    lines = _mask_code_spans(content).split('\n')
    in_table = False
    expected_cols = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        is_table_row = stripped.startswith('|') and stripped.endswith('|')
        if not is_table_row:
            if in_table:
                in_table = False
                expected_cols = 0
            continue
        # 分隔行：**格数须与表头一致**（2026-09-26 工作台账 #277，对齐审计工作流 1b-1 的 D10 形态）
        # 🔴 原实现对分隔行直接 `continue` ⇒ 分隔行格数与表头不符属**判据盲区**，永不报警。
        #    实证：`chain_template_catalog.md` 链 11 步骤表曾「表头 5 列 / 分隔行 4 格」，本脚本与
        #    审计工作流 1b 双双判 PASS（GFM 列解析已异常）。列数一律以**该表自身表头**为准，不硬编码。
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            if in_table:
                sep_cols = _count_cell_delimiters(stripped)
                if sep_cols != expected_cols:
                    warnings.append({
                        'level': 'WARNING', 'line': i, 'type': 'table_columns',
                        'detail': f'Separator row has {sep_cols} columns vs header {expected_cols}'
                    })
            # 不在表内时保持原语义：孤立的 `|---|` 行不构成 GFM 表格，不据它起表。
            continue
        # 🔴 按**管道符个数**数列（2026-09-15，#213）：原实现 `[c for c in ... if c.strip()]`
        # 会把**空单元格一并丢弃** ⇒ 合法 GFM（空首格续行）报假警，且**反向漏检**真缺陷
        # （`proposals/_catalog.md` 有一行多出尾随空单元格，因被丢弃而 never 报警，实测）。
        cols = _count_cell_delimiters(stripped)
        if not in_table:
            in_table = True
            expected_cols = cols
        elif cols != expected_cols:
            warnings.append({
                'level': 'WARNING', 'line': i, 'type': 'table_columns',
                'detail': f'Column count mismatch: {cols} vs expected {expected_cols}'
            })
    return len(warnings) == 0, warnings


# ── 3.3 Image Reference Validity ──────────────────────────────────────────

def check_image_refs(md_path, content):
    """验证 ![](path) 指向的文件存在。"""
    warnings = []
    md_dir = os.path.dirname(os.path.abspath(md_path))
    refs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', content)
    for path in refs:
        if path.startswith('http'):
            continue
        full = os.path.join(md_dir, path)
        if not os.path.exists(full):
            warnings.append({
                'level': 'WARNING', 'type': 'image_ref',
                'detail': f'Image not found: {path}'
            })
    return len(warnings) == 0, warnings


# ── 3.4 LaTeX Residual Commands ───────────────────────────────────────────

def check_math_residue(content):
    """检测转录残留：__MATH_n__ 占位符泄漏 + KaTeX 非法内层环境。

    🆕 2026-09-17：原 math_pairing 只做 $$/\\begin-\\end 栈配对，对含 44 个
    __MATH_n__ 泄漏与 $$\\begin{equation}...\\end{equation}$$ 的破损 A1 产物
    实测判 PASS，故补齐此检查。
    """
    errors = []
    # 🔴 2026-09-17 执行期订正之三：接上与 `math_pairing` 等**同一套代码跨度屏蔽**。
    #    原实现直接读裸 `content`，而兄弟检查走 `_mask_code_spans` ⇒ 任何**在文档里
    #    讨论该环境**的内容（围栏代码块、行内单记号）都会被本检查误判为真缺陷
    #    （实证：本方案的 §3 规则表在围栏内仍被判 L6 ERROR）。屏蔽保持行数不变，
    #    故行号与 `__MATH_` 扫描不受影响。
    masked = _mask_code_spans(content)
    for i, line in enumerate(masked.split('\n'), 1):
        if re.search(r'__MATH_\d+__', line):
            errors.append({'level': 'ERROR', 'line': i, 'type': 'math_residue',
                           'detail': '__MATH_n__ placeholder leaked (math conversion failed)'})
    # 🔴 2026-09-17 执行期订正：原实现对该环境的**任何**出现都报 ERROR，与 detail
    #    自称的「inside $$」不符，全仓实测使 18 篇**既有**转录件（均为**独立**环境、
    #    非 $$ 内嵌）由 PASS 变 FAIL ⇒ 新检查反而阻断了无关文件的提交。
    #    现按自称语义分级：$$ 内嵌 = ERROR（KaTeX 必失败，本次要抓的正是它）；
    #    独立残留 = WARNING（确是 LaTeX 残留，但属另一类，可见不阻断）。
    spans = [(m.start(), m.end()) for m in re.finditer(r'\$\$.*?\$\$', masked, re.DOTALL)]
    for m in re.finditer(r'\\begin\{(equation\*?|eqnarray\*?|gather\*?|multline\*?)\}',
                         masked):
        line_no = content[:m.start()].count('\n') + 1
        nested = any(s <= m.start() < e for s, e in spans)
        errors.append({
            'level': 'ERROR' if nested else 'WARNING',
            'line': line_no, 'type': 'math_residue',
            'detail': ('env %s inside $$ (unsupported by KaTeX)' % m.group(1)) if nested
                      else ('standalone \\begin{%s} residue (not inside $$)' % m.group(1))})
    # 与 `check_residual_commands` 同约定：有条目即 False；**Verdict 由 diagnostics
    # 的 level 决定**（ERROR→FAIL / WARNING→WARNING），故独立残留不会阻断提交。
    return len(errors) == 0, errors


def check_residual_commands(content):
    """检测应被展开但未展开的 LaTeX 命令。"""
    warnings = []

    checks = [
        (r'\\ref\{', '\\ref'),
        (r'\\cite\{', '\\cite'),
        (r'\\newcommand', '\\newcommand'),
        (r'\\def\b', '\\def'),
        (r'\\input\{', '\\input'),
        (r'\\include\{', '\\include'),
    ]
    for pattern, label in checks:
        found = re.findall(pattern, content)
        if found:
            warnings.append({
                'level': 'WARNING', 'type': 'residual_commands',
                'detail': f'{len(found)} unresolved {label}'
            })
    return len(warnings) == 0, warnings


# ── 3.5 UTF-8 Strict Decode ───────────────────────────────────────────────

def check_utf8_strict(file_path):
    """严格 UTF-8 解码验证。"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
            f.read()
        return True, None
    except UnicodeDecodeError as e:
        return False, {
            'level': 'ERROR', 'type': 'utf8_decode',
            'detail': f'UTF-8 decode error at byte {e.start}: {e.reason}'
        }


# ── 3.6 Statistics ────────────────────────────────────────────────────────

def collect_stats(content, source='unknown'):
    return {
        'total_lines': len(content.split('\n')),
        'total_chars': len(content),
        # 🔴 口径修正（2026-09-28，工作台账 #282 缺陷 C）：原按「行首 $$」计数是**样式敏感**的——
        #    LaTeX 路径产物常写成缩进开定界 + 行中闭定界（`…\end{aligned}$$`），实测同一份 LaTeX 产物
        #    行式 **19** / 记号式 **34**（lat_to_markdown 转换器自报也是 34），而 MinerU 产物 36
        #    ⇒ 假 Δ=+17 超阈报 ERROR（非公式丢失，见 memo #282 证据段）。改按 `$$` 记号数 /2
        #    （排除 `\$\$` 转义），对两侧样式无关；Zhao&Lattimer 实测 Δ 由 +17 回到 +2（= 阈内）。
        'display_math_blocks': len(re.findall(r'(?<!\\)\$\$', content)) // 2,
        'inline_math': max(0, content.count('$') - content.count('$$') * 2),
        'tables': len(re.findall(r'^\|[\s\-:|]+\|$', content, re.MULTILINE)),
        'image_refs': len(re.findall(r'!\[[^\]]*\]\([^)]+\)', content)),
        'sections': len(re.findall(r'^## ', content, re.MULTILINE)),
        'source': source,
    }


# ── 3.7 Cross-check ───────────────────────────────────────────────────────

CROSS_THRESHOLDS = {
    'formula_delta': 2,
    'table_delta':   1,
    'section_delta': 2,
    'image_delta':   1,
}


# 命名契约（2026-09-28 裁定，工作台账 #282；真源 = literature_ingestion_workflow Phase 3c
# 🟢 辅助路径 + mineru_transcription_workflow §2 + CLAUDE.md「衍生文件命名」表）：
#   MinerU 主产物  = {STEM}_extracted_text.md
#   LaTeX 参考产物 = {STEM}_extracted_text_latex.md   （Phase 3c：`latex_to_markdown.py --out {STEM}_extracted_text_latex.md`）
MINERU_SUFFIX = '_extracted_text.md'
LATEX_SUFFIX = '_extracted_text_latex.md'


def _locate_counterpart(md_path):
    """定位另一侧转录产物 → (path | None, input_role, pair_role)。

    🔴 旧实现写死「输入=LaTeX、对照物 `{stem}_extracted_text_mineru.md`」——该命名**全仓零匹配**
    （`find references -name '*_mineru.md'` = 0）⇒ 任何输入都必走 blocked，cross-check 从未产出过
    任何结果（#282 缺陷 B）。现按上表**双侧互认**：输入任一侧都能定位另一侧（先精确名，
    再退化到同目录同后缀）；无已知后缀的输入一律 blocked（防与元数据/翻译件误配对）。
    """
    md_dir = os.path.dirname(os.path.abspath(md_path))
    base = os.path.basename(md_path)
    if base.endswith(LATEX_SUFFIX):
        stem, input_role, pair_role, pair_suffix = (
            base[:-len(LATEX_SUFFIX)], 'latex', 'mineru', MINERU_SUFFIX)
    elif base.endswith(MINERU_SUFFIX):
        stem, input_role, pair_role, pair_suffix = (
            base[:-len(MINERU_SUFFIX)], 'mineru', 'latex', LATEX_SUFFIX)
    else:
        return None, 'unknown', None
    exact = os.path.join(md_dir, stem + pair_suffix)
    if os.path.exists(exact):
        return exact, input_role, pair_role
    # 退化匹配：**限定同一 stem 前缀**（容许版本后缀一类变体）。
    # 🔴 不得放宽为「同目录同后缀任意文件」——那会在一个目录装有多篇论文时**跨论文配对**
    #    （合成语料实测：孤件 Paper_Z 被配上 Paper_X 的 LaTeX 产物，blocked 被静默绕过）。
    cands = sorted(f for f in os.listdir(md_dir)
                   if f.startswith(stem) and f.endswith(pair_suffix) and f != base)
    if cands:
        return os.path.join(md_dir, cands[0]), input_role, pair_role
    return None, input_role, pair_role


def cross_check_with_mineru(md_path, thresholds=None):
    """MinerU ↔ LaTeX 结构指纹比对（输入任一侧，自动定位对照物并按角色归位）。

    🔴 返回值恒为 **3 值** `(passed | None, diagnostics, cross_stats | None)`：
    `None` = blocked（无对照物 / 输入非转录产物）。旧实现 blocked 分支只回 2 值，
    而调用点（`verify_file`）拆 3 值 ⇒ 首跑即 `ValueError`（#282 缺陷 A）。
    """
    if thresholds is None:
        thresholds = CROSS_THRESHOLDS

    counterpart, input_role, pair_role = _locate_counterpart(md_path)
    if counterpart is None:
        detail = ('Input is not a transcription product ({STEM}_extracted_text.md / '
                  '{STEM}_extracted_text_latex.md).' if pair_role is None
                  else f'No {pair_role} counterpart found next to {os.path.basename(md_path)}.')
        return None, [{
            'level': 'INFO', 'type': 'cross_check_blocked',
            'detail': detail,
        }], None

    with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
        input_content = f.read()
    with open(counterpart, 'r', encoding='utf-8', errors='replace') as f:
        pair_content = f.read()

    s_in = collect_stats(input_content, input_role if input_role != 'unknown' else 'mineru')
    s_pair = collect_stats(pair_content, pair_role)
    # 下方诊断文案以 ms = MinerU、ls = LaTeX 为准 ⇒ **按角色归位**（变量名沿用，方向不变）。
    # ⚠️ 旧实现在此处把「输入」一律当 LaTeX（变量名 latex_content），一旦对照物找到就会**反向读数**
    #    （这是与缺陷 B 配套的第三处错位，随 B 一起修）。
    if input_role == 'latex':
        ls, ms = s_in, s_pair
    else:
        ls, ms = s_pair, s_in

    diagnostics = []
    d_f  = ms['display_math_blocks'] - ls['display_math_blocks']
    d_t  = ms['tables']              - ls['tables']
    d_s  = ms['sections']            - ls['sections']
    d_i  = ms['image_refs']          - ls['image_refs']

    # 🔴 级别契约（2026-09-28 修，工作台账 #282 缺陷 D）：本函数的产物是**两侧转录的差**，
    #    不是对被测文件语法正确性的判定 ⇒ 按消费方契约（literature_ingestion_workflow Phase 3c
    #    🟢 辅助路径：「Δ > 阈值 → 🟡 提示人工检查（**不阻断**）」「LaTeX 产物错误 → INFO 级别」）
    #    应为 WARNING。旧实现把公式/表格差报成 ERROR ⇒ verdict FAIL 且退出码非零，与契约相反；
    #    实测 6 组真实配对中 5 组因**计数口径差**（块拆分/合并、子图）被误判 FAIL。
    if d_f > thresholds['formula_delta']:
        diagnostics.append({
            'level': 'WARNING', 'type': 'cross_check',
            'detail': (f'MinerU +{d_f} display math blocks [M={ms["display_math_blocks"]} '
                       f'L={ls["display_math_blocks"]}] — possible formula loss in LaTeX parsing')
        })
    elif d_f < -thresholds['formula_delta']:
        diagnostics.append({
            'level': 'WARNING', 'type': 'cross_check',
            'detail': (f'LaTeX +{-d_f} display math blocks [L={ls["display_math_blocks"]} '
                       f'M={ms["display_math_blocks"]}] — possible MinerU OCR over-detection')
        })

    if d_t >= thresholds['table_delta']:
        diagnostics.append({
            'level': 'WARNING', 'type': 'cross_check',   # 级别契约同上（#282 缺陷 D）
            'detail': (f'MinerU +{d_t} table(s) [M={ms["tables"]} L={ls["tables"]}] '
                       f'— possible table conversion failure in LaTeX parsing')
        })

    if d_s > thresholds['section_delta']:
        diagnostics.append({
            'level': 'WARNING', 'type': 'cross_check',
            'detail': (f'MinerU +{d_s} section(s) [M={ms["sections"]} L={ls["sections"]}] '
                       f'— possible incomplete section parsing')
        })

    if d_i >= thresholds['image_delta']:
        diagnostics.append({
            'level': 'WARNING', 'type': 'cross_check',
            'detail': (f'MinerU +{d_i} image ref(s) [M={ms["image_refs"]} L={ls["image_refs"]}] '
                       f'— possible figure omission in LaTeX parsing')
        })

    passed = not any(d['level'] == 'ERROR' for d in diagnostics)
    return passed, diagnostics, {'latex': ls, 'mineru': ms, 'deltas': {
        'formula': d_f, 'tables': d_t, 'sections': d_s, 'images': d_i
    }}


# ── Main ──────────────────────────────────────────────────────────────────

def verify_file(md_path, source='unknown', cross_check=False, json_out=False):
    """对单个文件执行全部检查。"""
    result = {
        'file': md_path,
        'source': source,
        'checks': {},
        'stats': {},
        'diagnostics': [],
        'verdict': 'PASS',
    }

    # 预检：文件存在
    if not os.path.exists(md_path):
        result['verdict'] = 'FAIL'
        result['diagnostics'].append({
            'level': 'ERROR', 'type': 'file', 'detail': f'File not found: {md_path}'
        })
        return result

    # UTF-8 strict
    utf8_ok, utf8_err = check_utf8_strict(md_path)
    result['checks']['utf8_decode'] = utf8_ok
    if utf8_err:
        result['diagnostics'].append(utf8_err)

    # 读取内容
    with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 统计
    result['stats'] = collect_stats(content, source)

    # 独立检查
    for name, fn in [
        ('math_pairing',    lambda: check_math_pairing(content)),
        ('brace_balance',   lambda: check_brace_balance(content)),
        ('eps_leak',        lambda: check_eps_leak(content)),
        ('table_columns',   lambda: check_table_columns(content)),
        ('image_refs',      lambda: check_image_refs(md_path, content)),
        ('residual_commands', lambda: check_residual_commands(content)),
        ('math_residue',    lambda: check_math_residue(content)),
        ('fence_balance',   lambda: check_fence_balance(content)),
    ]:
        ok, items = fn()
        result['checks'][name] = ok
        result['diagnostics'].extend(items)

    # 交叉校验
    if cross_check:
        ok, diags, cross_stats = cross_check_with_mineru(md_path)
        if ok is None:
            # blocked — no MinerU output
            result['checks']['cross_check'] = 'BLOCKED'
        else:
            result['checks']['cross_check'] = ok
            result['cross_stats'] = cross_stats
        result['diagnostics'].extend(diags)

    # 判定
    errors = [d for d in result['diagnostics'] if d['level'] == 'ERROR']
    warnings = [d for d in result['diagnostics'] if d['level'] == 'WARNING']
    if errors:
        result['verdict'] = 'FAIL'
    elif warnings:
        result['verdict'] = 'WARNING'

    return result


def expand_paths(paths):
    """把 positional 路径展开为待检文件列表——目录按 `**/*.md` 递归。

    🆕 2026-09-22（工作台账 #264）：原先 positional 只收**文件**，传目录会
    以 `PermissionError` 崩掉（exit 1）。缺了「指向任意树」的能力，调用方就
    转而误用 `--all`（它是 references/ 专用）——三个活工作流因此把零覆盖的
    命令当成了自己产物的终验闸门。补上本能力即消掉那个诱因。

    返回 (files, empty_dirs)：空目录单列，由调用方判为 ERROR——显式给了路径
    却一个 `.md` 都没扫到，通常是路径写错，静默通过会再造一个空洞闸门。
    """
    import glob as _glob
    files, empty_dirs = [], []
    for p in paths:
        if os.path.isdir(p):
            found = sorted(_glob.glob(os.path.join(p, '**', '*.md'), recursive=True))
            if found:
                files.extend(found)
            else:
                empty_dirs.append(p)
        else:
            files.append(p)
    return files, empty_dirs


def find_extracted_text_files(references_root='project/references', source_filter=None):
    """扫描 project/references/ 下所有 _extracted_text.md。

    默认根随空壳目录 2026-10-05 下沉而更新（原为 `references`）。🔴 该默认值是
    `--all` 与 `--source` 的**唯一**扫描域来源；漏改会静默扫到不存在的目录，而 `main`
    在「0 文件」分支直接 `sys.exit(0)` —— 与「扫到了且全过」同形（空洞闸门形态）。
    """
    files = []
    for root, dirs, filenames in os.walk(references_root):
        for f in filenames:
            if not f.endswith('_extracted_text.md'):
                continue
            if f.endswith('_extracted_text_mineru.md'):
                continue  # MinerU 交叉产物不纳入独立检查
            full = os.path.join(root, f)
            # --source 过滤
            if source_filter == 'latex':
                # 检查是否有 _source.tar.gz（LaTeX 路径标志）
                if not os.path.exists(os.path.join(root, '_source.tar.gz')):
                    continue
            elif source_filter == 'mineru':
                if os.path.exists(os.path.join(root, '_source.tar.gz')):
                    continue
            files.append(full)
    return sorted(files)


def print_result(result):
    """终端格式化输出。"""
    s = result['stats']
    print(f"\n  File:     {result['file']}")
    print(f"  Source:   {result['source']}")
    print(f"  Lines:    {s.get('total_lines', '?')}  "
          f"Sections: {s.get('sections', '?')}  "
          f"Math: {s.get('display_math_blocks', '?')}  "
          f"Tables: {s.get('tables', '?')}")

    for check_name in ['math_pairing', 'brace_balance', 'eps_leak', 'table_columns', 'image_refs', 'residual_commands', 'fence_balance', 'utf8_decode']:
        status = result['checks'].get(check_name, '?')
        if status is True:
            icon = 'PASS'
        elif status is False:
            icon = 'FAIL'
        else:
            icon = str(status)
        print(f"  {check_name:20s}  {icon}")

    if 'cross_check' in result['checks']:
        cc = result['checks']['cross_check']
        icon = 'PASS' if cc is True else ('FAIL' if cc is False else str(cc))
        print(f"  {'cross_check':20s}  {icon}")
        if 'cross_stats' in result:
            cs = result['cross_stats']
            d = cs['deltas']
            print(f"    Deltas:  math={d['formula']:+d}  tables={d['tables']:+d}  "
                  f"sections={d['sections']:+d}  images={d['images']:+d}")

    for d in result['diagnostics']:
        line_info = f" L{d['line']}" if 'line' in d and d['line'] > 0 else ''
        print(f"    {d['level']:7s} [{d['type']}]{line_info}  {d['detail']}")

    print(f"\n  Verdict:  {result['verdict']}")
    return result['verdict']


def main():
    ap = argparse.ArgumentParser(description='Markdown transcription syntax validator')
    ap.add_argument('path', nargs='*',
                    help='文件或**目录**（目录按 **/*.md 递归）；多文件用于 pre-commit 逐暂存件检查')
    ap.add_argument('--all', action='store_true',
                    help='⚠️ 仅扫 project/references/ 下的 _extracted_text.md（**不是**「全仓 md」）；'
                         '要校验别的树请直接传目录，如 verify_md_syntax.py ai_system/official_docs')
    ap.add_argument('--source', choices=['latex', 'mineru', 'unknown'], default='unknown',
                    help='Transcription source filter')
    ap.add_argument('--json', action='store_true', dest='json_out', help='Output JSON')
    ap.add_argument('--cross-check', action='store_true', dest='cross_check',
                    help='Cross-check LaTeX vs MinerU structural fingerprints')
    ap.add_argument('--fences-only', action='store_true', dest='fences_only',
                    help='只跑围栏配平（check_fence_balance），且在**未标注**的 A 类上非零退出 '
                         '—— 供 pre-commit 的 `files: \\.md$` 钩子用。'
                         '⚠️ 本模式的退出码语义是阻断式；`--all` 与逐文件两路**不变**（只按 ERROR 计）')
    args = ap.parse_args()

    if args.fences_only:
        sys.exit(run_fences_only(args.path, use_all=args.all))

    if args.all:
        files = find_extracted_text_files(source_filter=args.source)
        # 🔴 作用域横幅（stderr——勿污染 stdout 的 --json 输出）。
        #    工作台账 #264：3 个活工作流曾把 `--all` 当作「通用 md 终验」，
        #    而其产物面（official_docs/ 镜像、derivation_kb notes/）根本不在扫描域内，
        #    FAIL 0 因而不是覆盖证据。横幅把真实作用域印在每次运行的输出里。
        print(f"[scope] --all = project/references/**/_extracted_text.md only — "
              f"{len(files)} file(s) scanned; NOT a repo-wide markdown gate.",
              file=sys.stderr)
        if not files:
            print('No _extracted_text.md files found.', file=sys.stderr)
            sys.exit(0)

        all_results = []
        total = {'PASS': 0, 'WARNING': 0, 'FAIL': 0}

        for f in files:
            r = verify_file(f, args.source, args.cross_check, args.json_out)
            all_results.append(r)
            total[r['verdict']] = total.get(r['verdict'], 0) + 1
            if not args.json_out:
                verdict = print_result(r)

        # 汇总
        # 🆕 2026-09-22（#264）：`--json` 时汇总行走 stderr——原先无条件打进 stdout，
        #    使 `--all --json` 的输出**不是合法 JSON**（2026-07-14 方案里正有
        #    `--all --json > x.json` 的用法）。JSON 由下方 json.dumps 独占 stdout。
        summary_stream = sys.stderr if args.json_out else sys.stdout
        print(f"\n{'='*60}", file=summary_stream)
        print(f"  Total: {len(files)} files  |  "
              f"PASS: {total['PASS']}  WARNING: {total['WARNING']}  FAIL: {total['FAIL']}",
              file=summary_stream)
        print(f"{'='*60}", file=summary_stream)

        if args.json_out:
            print(json.dumps(all_results, indent=2, ensure_ascii=False))

        sys.exit(0 if total['FAIL'] == 0 else (1 if total['FAIL'] <= 2 else 2))

    elif args.path:
        # 🆕 2026-09-17：支持多路径——pre-commit 的 `pass_filenames: true` 会一次传入
        #    全部暂存件（原先 nargs='?' 只收一个 ⇒ 多文件时报 unrecognized arguments）。
        #    退出码 = 各文件 ERROR 数的最大值（上限 255），任一文件有 ERROR 即非零。
        # 🆕 2026-09-22（#264）：目录参数按 **/*.md 递归展开；空目录判 ERROR
        #    （见 expand_paths 的 docstring）。
        paths, empty_dirs = expand_paths(args.path)
        for d in empty_dirs:
            print(f"ERROR: 目录下未找到任何 .md —— {d}（路径写错？）", file=sys.stderr)
        if not paths:
            sys.exit(1)
        rc = 1 if empty_dirs else 0
        for p in paths:
            r = verify_file(p, args.source, args.cross_check, args.json_out)
            if args.json_out:
                print(json.dumps(r, indent=2, ensure_ascii=False))
            else:
                print_result(r)
            errors = [d for d in r['diagnostics'] if d['level'] == 'ERROR']
            rc = max(rc, len(errors))
        sys.exit(min(255, rc))
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
