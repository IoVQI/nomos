#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""proposal-gen P2 门禁 G3 —— 逐条验证方案的每个 `old_string` 在目标文件中命中恰好 1 次。

用途
----
方案（`proposals/YYYY/MM/DD/*.md`）的 §3 编辑表以围栏块给出
`old_string` / `new_string` 对；目标文件由最近的「#### 步骤 X#…」标题行内
最后一个「路径形态」的反引号 token 决定（绝对路径或仓库相对路径均可）。本脚本机械核验**编辑锚点是否
真实、唯一**（对应 `proposal_audit_workflow` 的 FM-20 / D4），避免「凭记忆写
old_string」导致的落盘后 mismatch。

用法
----
    python ai_system/scripts/reusable/verify_proposal_anchors.py <proposal.md> [--json] [--strict]

退出码：全部唯一 → 0；任一失配 → 1；**有步骤头但一个块都没解析到 → 1**（见下）；
方案 status = 已执行 → 0（**跳过**，见下节）。

🔴 已执行方案：默认跳过（工作台账 #305，2026-10-01）
-----------------------------------------------------
方案一旦执行，其 §3 锚点 `old_string` 就**多半已被应用**（从目标文件中消失）⇒ 对已执行
方案跑本门禁会**恒报一片 ❌ 且 rc=1**。这是**预期读数、不是缺陷**，但审计/复跑已执行方案
的人极易把预期红读成缺陷。

实测规模（2026-10-01 全库普查，311 份方案）：含锚点块的 **42** 份，其中 status=`已执行`
**36** 份，当前**全部 rc=1**；另有 5 份 `待确认` + 1 份 `已确认`（后者的红是真读数，见下）。

故本脚本读方案 frontmatter 的 `status` 决定是否适用：

* `status` 以 **`已执行` / `已落盘`** 开头（容许前缀 `✅`、引号、括注）⇒ **默认跳过**：
  打印 `SKIP（已执行）` 横幅 + 逐条读数，退出码 **0**。此时**未做**唯一性核验。
* 其他状态（含 `待确认` / `draft` / `已确认` / `已废弃` / 无 frontmatter）⇒ 照常核验。
  🔴 刻意**不收** `已确认`——「已确认」= 决策已裁定，**不蕴含编辑已落盘**；实测
  `2026-09-20_D10表面终止判据与Love落点修复方案.md`（status=已确认）的 `new_string`
  只出现在 4/31 个目标中，即该方案**并未执行**，它的红是真读数。
* `--strict` 强制核验（忽略 status），用于「我怀疑 status 本身是错的」的场合。

⚠️ **跳过的边界**：跳过只作用于**锚点命中**类失配（`HIT_n` / `NO_TARGET` / `FILE_MISSING`）；
**解析面守卫（下节 #291 空块）与方案状态无关，仍报 rc=1**——它查的是「这份方案的锚点
当年有没有被验过」，与「是否已执行」是两个问题。

⚠️ **跳过 ≠ 通过**：横幅与 JSON 的 `mode` 字段都显式标 `skip-executed`，汇总行写
「跳过核验」而非「命中唯一 N / N」。**不要**把 rc=0 读成锚点唯一性通过。

⚠️ **反向也别外推**：已执行 **≠** 锚点必被消耗——插入类编辑（`new_string` 加在
`old_string` 之后）不消耗锚点。全库有 1 例已执行方案零失配（`2026-09-14_方案执行器
reusable化方案.md`）。故本脚本**不用**「已执行 ⇒ 应全红」做任何断言。

🔴 空块守卫（工作台账 #291，2026-09-29 实证）
-------------------------------------------
本脚本要求围栏**独立成行**：

    ```
    old_string:
    …
    new_string:
    …
    ```

若写成「```old_string:」同一行，`BLOCK_RE` 一个块都匹配不到，而旧版会**静默打印
「步骤头 26 个；old_string 块 0 个」并 `rc=0`**——门禁看似通过、实则**一个锚点都没验**。
这是「整齐的假绿」，比报错更危险（同族：零用例 / 真空通过 / 失效域恒绿）。
现加守卫：**有步骤头但块数为 0 ⇒ 非零退出**。仅在「有步骤头」时触发——库内大量
历史方案既无步骤头也无块，属旧体例，不得误伤（2026-09-29 全库 311 份普查：命中 1 份）。

⚠️ 未覆盖的相邻缺陷（**不属本条范围**，另案记录）：`old_string`/`new_string` **正文内部**
若含独立成行的 ``` 会把本条块提前截断、并吞掉其后的后续块 ⇒ 那些锚点同样被静默跳过。
2026-09-29 全库普查实测 2 例（`…计数描述退役批次3方案.md:275`、`…Lackey2006…:466`）。

🔴 行尾陷阱（2026-09-12 实证，务必保留本归一逻辑）
--------------------------------------------------
本仓库大部分 `.md` 在磁盘上是 **CRLF**（`.gitattributes` / `core.autocrlf` 所致），
而方案文件通常由编辑器写成 **LF**。若用二进制读取后再 `decode` 匹配，多行
`old_string` **必然失配**（单行锚点因不含换行而不受影响，故障呈「部分通过」的
迷惑形态）。

本脚本显式做 `\r\n → \n` 归一再比对；**不要**为了「更快」改成二进制匹配。
同源事故：同批的执行器 `archive/apply_proposal_edits.py` 首跑即因未归一而
4 个多行锚点全挂（当时校验器通过、执行器失败——即校验器对、执行器错）。
反向纪律：执行器回写时须把 `\n` 还原为目标文件原有的行尾。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

STEP_RE = re.compile(r"^####\s+步骤\s+([A-F0-9]+)\s*[：:]")
# 目标文件由步骤标题内**最后一个**「路径形态」的反引号 token 决定。
# 形态 = 含路径分隔符且以已知扩展名结尾——**绝对路径与仓库相对路径都收**。
# 🔴 2026-10-05：原正则只收 `[A-Za-z]:\...` / `[A-Za-z]:/...` **绝对路径**。本骨架统一
#    改用仓库相对路径后，它一个 target 都解析不出 ⇒ 每条都落 NO_TARGET、门禁整齐报红
#    （不报错，只给整齐的假红）。这属「正则表达不出该路径」同族缺陷——先例见
#    `verify_proposal_declarations.py` 的 PATH_TOKEN_RE 注释（.tex / .hpp 扩白名单）。
#    故此处与其**扩展名白名单对齐**，并显式收相对路径。
PATH_RE = re.compile(
    r"`([^`\s]*[\\/][^`\s]*\."
    r"(?:md|json|py|js|yml|yaml|toml|txt|tex|sty|hpp|cpp|h|cc|bat|sh))`")
BLOCK_RE = re.compile(r"^```\nold_string:\n(.*?)\nnew_string:\n(.*?)\n```$", re.S | re.M)

# 仓库根：本脚本位于 <repo>/ai_system/scripts/reusable/ ⇒ 上溯四层。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


def resolve_target(target):
    """把步骤标题里的 target 解析为可直接 open 的路径。

    绝对路径原样返回；**仓库相对路径按仓库根解析**——否则会相对 cwd 解析，
    从仓库外或其他子目录调用即 FILE_MISSING（又是一片整齐的假红）。
    """
    if os.path.isabs(target):
        return target
    return os.path.join(_REPO_ROOT, target.replace("\\", "/"))

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)
STATUS_RE = re.compile(r"^status:[ \t]*(.*?)[ \t]*$", re.M)
# 字面蕴含「编辑点已落盘」的 status 前缀（#305）。刻意窄：宁少收、由 --strict 兜底。
EXECUTED_PREFIXES = ("已执行", "已落盘")


def read_status(proposal_path):
    """读方案 frontmatter 的 status；无 frontmatter / 无该字段 → None。"""
    text = open(proposal_path, encoding="utf-8").read().lstrip("﻿")
    m = FM_RE.match(text)
    if not m:
        return None
    s = STATUS_RE.search(m.group(1))
    return s.group(1).strip().strip("\"'") if s else None


def is_executed(status):
    """status 是否表示「编辑点已落盘」。容许 ✅/✔ 前缀与前后空白。"""
    if not status:
        return False
    return status.lstrip("✅✔️ \t").startswith(EXECUTED_PREFIXES)


def parse(proposal_path):
    """→ (steps, edits)。edits 每项含 line/step/target/old/new。"""
    text = open(proposal_path, encoding="utf-8").read()
    lines = text.split("\n")

    steps = []
    for i, line in enumerate(lines):
        m = STEP_RE.match(line)
        if m:
            p = PATH_RE.findall(line)
            steps.append({"line": i, "step": m.group(1), "target": p[-1] if p else None})

    edits = []
    for m in BLOCK_RE.finditer(text):
        ln = text[: m.start()].count("\n")
        target, step = None, None
        for s in steps:
            if s["line"] < ln:
                target, step = s["target"], s["step"]
        edits.append({"line": ln + 1, "step": step, "target": target,
                      "old": m.group(1), "new": m.group(2)})
    return steps, edits


def norm_eol(s):
    return s.replace("\r\n", "\n")


def main(argv=None):
    # 仅在作为脚本执行时把 stdout 切到 UTF-8（Windows 控制台默认 GBK 会把 emoji 打印成
    # UnicodeEncodeError）；**不在 import 时执行**——否则 import 本模块会关闭调用方的
    # stdout（2026-09-12 实测 import 后 print 报 "I/O operation on closed file"）。
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="proposal-gen P2 G3: old_string 唯一性核验")
    ap.add_argument("proposal")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--strict", action="store_true",
                    help="忽略方案 status，强制核验（用于「怀疑 status 本身写错」的场合）")
    a = ap.parse_args(argv)

    steps, edits = parse(a.proposal)
    status = read_status(a.proposal)
    executed = is_executed(status)

    # 🔴 空块守卫（工作台账 #291）：有步骤头却一个 old_string 块都没解析到 ⇒ 门禁实际
    # 未验证任何锚点。不加此判据时会「静默报 0/0 且 rc=0」——整齐的假绿。
    # 判据刻意**只在 steps 非空时**触发：库内大量历史方案既无步骤头也无块（旧体例），
    # 若一并判负会造出一整片假 FAIL；有步骤头则意味着作者意图是「逐条编辑」，那就必须有条目。
    if steps and not edits:
        if a.json:
            print(json.dumps({"steps": len(steps), "edits": [], "ok": 0, "total": 0,
                              "guard": "NO_BLOCKS", "fail": [],
                              "hint": "有步骤头但 0 个 old_string 块；检查围栏是否独立成行"},
                             ensure_ascii=False, indent=1))
        else:
            print("步骤头 %d 个；old_string 块 0 个" % len(steps))
            print("🔴 门禁未验证任何锚点：解析到 %d 个「#### 步骤」头，但 **0 个 old_string 块**。"
                  % len(steps))
            print("   最常见成因 = 围栏未独立成行（把 ```old_string: 写在同一行）。本脚本要求的形态：")
            print("       ```")
            print("       old_string:   ← 必须独立成行")
            print("       <原文>")
            print("       new_string:")
            print("       <新文>")
            print("       ```")
        return 1

    results, bad = [], []
    for e in edits:
        rec = {"line": e["line"], "step": e["step"], "target": e["target"]}
        if not e["target"]:
            rec["status"] = "NO_TARGET"
            bad.append(rec)
        elif not os.path.isfile(resolve_target(e["target"])):
            rec["status"] = "FILE_MISSING"
            bad.append(rec)
        else:
            text = norm_eol(open(resolve_target(e["target"]), "rb").read().decode("utf-8"))
            n = text.count(norm_eol(e["old"]))
            rec["hits"] = n
            rec["status"] = "OK" if n == 1 else "HIT_%d" % n
            if n != 1:
                bad.append(rec)
        results.append(rec)

    # 🔴 已执行 ⇒ 跳过（#305）。注意：本分支**在解析面守卫之后**——守卫查的是「锚点当年有没有
    # 被验过」，与「是否已执行」无关，故已执行方案若踩守卫仍报 rc=1（见模块 docstring）。
    if executed and not a.strict:
        if a.json:
            print(json.dumps({"steps": len(steps), "edits": results,
                              "ok": len(edits) - len(bad), "total": len(edits),
                              "fail": bad, "mode": "skip-executed", "status": status,
                              "note": "方案 status=已执行 ⇒ 锚点预期已被消耗；本次未做唯一性"
                                      "核验。rc=0 表示跳过，非通过。"},
                             ensure_ascii=False, indent=1))
        else:
            print("🔵 SKIP（已执行）：方案 status = %s" % status)
            print("   锚点预期已在执行时被消耗 ⇒ 本次**未做**唯一性核验。"
                  "rc=0 = **跳过**，不是**通过**。")
            print("   怀疑 status 本身写错 → 加 --strict 强制核验。\n")
            print("步骤头 %d 个；old_string 块 %d 个" % (len(steps), len(edits)))
            for r in results:
                mark = "✅" if r["status"] == "OK" else "·"
                print("  %s %-6s %-58s %s" % (mark, r["step"] or "-",
                                              os.path.basename(r["target"] or "?"),
                                              r["status"]))
            n_ok = len(edits) - len(bad)
            print("\n跳过核验：锚点仍命中唯一 %d / %d；其余 %d 条已在执行时被消耗"
                  "（预期，非缺陷）。" % (n_ok, len(edits), len(bad)))
            if n_ok == len(edits) and edits:
                print("   ℹ️ 本条**零失配**——已执行≠锚点必被消耗（插入类编辑不消耗锚点），"
                      "故这个读数同样不构成任何核验结论。")
        return 0

    # ⚠️ 提示行只进人类可读通道：`--json` 下若打这行会污染 stdout 使 json.load 失败
    # （2026-10-01 实测）。JSON 模式下改由 `strict_note` 字段承载。
    if a.strict and executed and not a.json:
        print("⚠️ --strict：忽略 status（%s）强制核验——下述 ❌ 多为执行期已消耗，非缺陷。"
              % status)

    if a.json:
        out = {"steps": steps, "edits": results,
               "ok": len(edits) - len(bad), "total": len(edits),
               "fail": bad, "mode": "strict" if (a.strict and executed) else "verify",
               "status": status}
        if a.strict and executed:
            out["strict_note"] = ("status 表示已执行；--strict 强制核验，fail 中多为执行期"
                                  "已消耗的锚点，非缺陷。")
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("步骤头 %d 个；old_string 块 %d 个" % (len(steps), len(edits)))
        for r in results:
            mark = "✅" if r["status"] == "OK" else "❌"
            print("  %s %-6s %-58s %s" % (mark, r["step"] or "-",
                                          os.path.basename(r["target"] or "?"),
                                          r["status"]))
        print("\n命中唯一 %d / %d" % (len(edits) - len(bad), len(edits)))
        for r in bad:
            print("  ❌ 方案 L%d [%s] %s → %s" % (r["line"], r["step"], r["target"], r["status"]))

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
