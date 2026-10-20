#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""proposal 声明面一致性机械核验 —— FM-21 / FM-30 / FM-33 的机械护栏。

以 §3 编辑目标集为**真值**，独立核验各「声明面」是否与之自洽：
  A1 (FM-33)  §6 回滚表路径集 R ⊇ §3 目标集 T
  A2 (FM-21)  §2 变更总览 + 元信息表 提及的文件集 D ⊇ T
  A3 (FM-30)  「不改动」声明集 U ∩ T = ∅

只做**单方向**断言（⊇ / ∩=∅），不做反向相等——声明的文件数可因分节口径不同而
合法地多于 T（如自注册文件单列），反向相等会把护栏变成噪声。

🔴 覆盖边界（实测标定，2026-09-14）：本脚本只覆盖**声明面之间的集合包含关系**。
不覆盖：跨节计数一致性、步骤引用可达性、影响面/爆炸半径完备性、检查项自反性。
即它把「声明与编辑面脱节」做成机械的，不是把审计做成机械的。

与 verify_proposal_anchors.py 的分工：后者核 §3 锚点**唯一性**（FM-20），本脚本核
**声明面集合一致性**（FM-30/31/33）。本脚本 import 复用其 parse()，不重写解析。

用法：python ai_system/scripts/reusable/verify_proposal_declarations.py <proposal.md> [--json]
退出码：全部通过 → 0；任一断言失败 → 1。
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# 位置鲁棒：脚本可能被复制到 tmp/（dry-run）后运行，不能只认自己的目录。
# 2026-09-14 dry-run 实证：仅用 _HERE 时放到 tmp/ 即 FileNotFoundError。
_ANCHOR_CANDIDATES = [
    os.path.join(_HERE, "verify_proposal_anchors.py"),
    os.path.join(_HERE, "..", "reusable", "verify_proposal_anchors.py"),
]

# 「不改动」段标题关键词（用于 A3）；仅匹配 `## …` 级标题
NOCHANGE_HEAD = "不改动"

# 仓库顶层目录：用于把「绝对路径」与「仓库相对路径」归一到同一形式。
# 🔴 本骨架已改全相对路径；此表须与**实际的顶层目录**一致，否则路径归一不到同一形式，
# A1/A2 会对含该目标的方案整齐地报「全部缺失」（不报错，只给假阳性）。
# 增删顶层目录时**同批更新此表**。
# 🔴 2026-10-05：6 个空壳目录（references / derivation_kb / data_kb / domain_kb /
#    lab / meeting_notes）下沉至 `project/` 下 ⇒ **删除**其条目。归一仍正确：
#    新路径 `project/xxx/...` 命中 `project` 条目。留条目有害——`_norm` 按本表**顺序**
#    取首个命中，残留项若排在 `project` 之前会把 `project/references/x.md` 误归一成
#    `references/x.md`，A1/A2 随即对含该路径的方案整齐报缺失。
_TOP_DIRS = (".claude", ".github", "ai_system", "project", "proposals", "coordination")

#: 路径 token 的扩展名白名单，由 `PATH_TOKEN_RE` 的两条相对路径分支共用。
_EXTS = r"(?:md|json|py|js|yml|yaml|toml|txt|tex|sty|hpp|cpp|h|cc|bat|sh)"

PATH_TOKEN_RE = re.compile(
    # 扩展名白名单：2026-09-15 补 tex|sty（用户授权）；2026-09-20 补 hpp|cpp|h|cc|bat|sh。
    # 原白名单无 tex ⇒ §3 目标含 .tex 的方案恒过不了 A1/A2——声明面正则表达不出该路径，
    # 故障形态是「整齐的假 FAIL」而非报错。实证：presentations 四事项目录重构方案的 2 个
    # tex 目标在 A1/A2 恒报缺失，最小复现确认旧正则不匹配、新正则匹配。
    # 🔴 同型二次复发（2026-09-20）：D10 修复方案改 C++（.hpp/.cpp），A1/A2 恒报
    # 「缺 solver.hpp / tov_c_api.cpp」而两者**确实**已写进 §2 与 §6 —— 又是「正则表达不出
    # 该路径」。判据：`standards/06 §3.1`「闸门的阻断面不得超出提交者控制面」。
    # 对拍（改前/改后跑 09-20/09-19/09-14 三份既有方案）：均 3/3 不变 ⇒ 无回归。
    # 🔴 同型三次复发（2026-10-05）：**仓库根级文件**（`./CLAUDE.md` / `./README.md`）。原
    #    正则两条分支都要求路径含 `/` ⇒ 根文件恒解析不出，A1/A2 对「§3 目标落在根文件」的
    #    方案整齐报缺失。补 `\./<name>.<ext>` 分支；**刻意只收显式 `./` 前缀**，使散文里的
    #    裸文件名（`index.md` 一类）不进候选——与 `check_claude_md.py`「含 `/` 才判定」同口径。
    #    对拍（改前/改后实测）：`./CLAUDE.md` F→T；裸 `CLAUDE.md`/`index.md`/`settings.json`
    #    保持 F；`a/b/c.py`、`D:/x/y.md` 等既有形态全部不变 ⇒ 无回归、无新噪声。
    r"`([A-Za-z]:[\\/][^`\s]+"
    r"|\.?[A-Za-z_][\w.\-]*/[\w./+\-]+\." + _EXTS +
    r"|\./[A-Za-z_][\w.\-]*\." + _EXTS + r")`"
)


def _load_anchors():
    for cand in _ANCHOR_CANDIDATES:
        p = os.path.normpath(cand)
        if os.path.isfile(p):
            spec = importlib.util.spec_from_file_location("_vpa", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError(
        "verify_proposal_anchors.py 未找到；已尝试：%s" % _ANCHOR_CANDIDATES)


def _norm(p):
    """归一到「仓库内相对路径」，使 §3 的绝对路径与声明面的相对路径可比。

     2026-09-14 dry-run 实证：不归一时 T（步骤标题里的绝对路径）与
    D（正文反引号里的相对路径）**永不相交** ⇒ A2 对**任何**方案都报「全部缺失」。
    这是最危险的一类缺陷——不报错，只给出整齐的假阳性。
    """
    p = p.replace("\\", "/")
    for d in _TOP_DIRS:
        i = p.find("/" + d + "/")
        if i >= 0:
            return p[i + 1:]
        if p.startswith(d + "/"):
            return p
    # 🔴 2026-09-29（工作台账 #292）：只剥「./」前缀，**不是** `lstrip("./")`。
    # `lstrip` 按字符集剥，会把 `.github/…` 的前导点一并吃掉 ⇒ 得 `github/…`，
    # 与 §3 侧归一结果（`.github/…`）永不相交。同族先例见 PATH_TOKEN_RE 注释
    # （.tex / .hpp：正则表达不出该路径 ⇒ 整齐的假 FAIL）。
    while p.startswith("./"):
        p = p[2:]
    return p


def _sections(text):
    """按顶层 `## ` 标题切段 → {标题: 正文}。"""
    out, cur, buf = {}, None, []
    for line in text.split("\n"):
        if line.startswith("## "):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = line[3:].strip(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def check(proposal_path):
    vpa = _load_anchors()
    text = open(proposal_path, encoding="utf-8").read().replace("\r\n", "\n")
    steps, edits = vpa.parse(proposal_path)

    # T = §3 全部目标，**含无 old_string 块的新建文件步骤**——否则新建文件不进断言范围
    # （2026-09-14 dry-run 实证：只取 edits 会漏掉新建文件步骤）。
    T = {_norm(x["target"]) for x in (steps + edits) if x.get("target")}
    secs = _sections(text)

    def paths_in(*keys):
        acc = set()
        for name, body in secs.items():
            if any(k in name for k in keys):
                acc |= {_norm(m) for m in PATH_TOKEN_RE.findall(body)}
        return acc

    R = paths_in("§6")
    D = paths_in("§2", "元信息")
    U = paths_in(NOCHANGE_HEAD)

    res = [("A1 FM-33 回滚表 ⊇ §3 目标", sorted(T - R)),
           ("A2 FM-21 声明面 ⊇ §3 目标", sorted(T - D)),
           ("A3 FM-30 不改动 ∩ §3 目标", sorted(U & T))]
    bad = [{"assertion": n, "violations": v} for n, v in res if v]
    return {"proposal": os.path.abspath(proposal_path), "targets": sorted(T),
            "nochange_section_present": bool(U),
            "assertions": [{"assertion": n, "violations": v} for n, v in res],
            "ok": len(res) - len(bad), "total": len(res), "fail": bad}


def main(argv=None):
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="proposal 声明面一致性机械核验（FM-30/31/33）")
    ap.add_argument("proposal")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    r = check(a.proposal)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("§3 编辑目标集 %d 个" % len(r["targets"]))
        for x in r["assertions"]:
            mark = "✅" if not x["violations"] else "❌"
            detail = ("缺 %d 项：%s" % (len(x["violations"]), ", ".join(x["violations"]))
                      if x["violations"] else "通过")
            print("  %s %-28s %s" % (mark, x["assertion"], detail))
        if not r["nochange_section_present"]:
            print("  ⚠️ 未检出「不改动」段 ⇒ A3 空过（vacuous pass），不代表已核验")
        print("\n声明面断言 %d / %d 通过" % (r["ok"], r["total"]))
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
