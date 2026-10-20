#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""方案 §3 编辑点确定性执行器（reusable）。

用途
----
读取方案 md 的 §3 编辑表，把每条 `old_string → new_string` 应用到对应目标文件。
格式与 `verify_proposal_anchors.py` 完全一致（`#### 步骤 X#：…` 标题行带反引号路径 + 围栏
`old_string:` / `new_string:`）。

🔴 解析器与校验器共用同一份
---------------------------
`parse()` 由 `verify_proposal_anchors.py` 提供，本脚本 **import 复用，不重写**。
同族事故（2026-09-14 实测）：`archive/apply_proposal_edits.py` 自带一份解析，在方案格式演进
（步骤号 `[A-F]\d+` → `[A-F0-9]+`；路径反斜杠 → 正/反斜杠均可）中**分叉**，对现行格式
直接抛 `UnboundLocalError: cannot access local variable 'cur_step'`。
**执行器与校验器各写一份解析 = 迟早分叉。**

三条纪律（缺一不可）
--------------------
1. **逐条断言命中恰好 1 次**（非 0 非多）。任一失配 → **立即中止且不写盘**
   —— 全部编辑在内存完成，**全部通过后**才统一写盘。
2. **按目标文件原行尾回写**：先 `\r\n → \n` 归一再匹配，回写时还原行尾。判定优先级：
   ① 命中区含 `\r\n` → CRLF；② 命中区含裸 `\n` → LF；
   ③ **命中区不含任何换行（单行锚点）→ 回落到目标文件的「主导行尾」**。
   🔴 ③ 是 2026-09-14 首次真实执行时才补上的：原实现只有 ①②，而**单行锚点必然落到 ②**，
   于是往 CRLF 目标文件的**多行 `new_string`** 里注入裸 LF ⇒ 工作树转混合行尾
   （实测 `_scripts/index.md` 119 CRLF/0 裸 LF → 119/2、`SKILL.md` 245/0 → 245/5）。
   本仓库 `.md`/`.py` 均 `text eol=lf`，git 归一化会吃掉该差异（实测三变体 blob 哈希相同
   `96b0278e`）⇒ 提交内容不受影响 —— 但那是**仓库属性的兜底，不是本脚本行为正确**。
   历史教训：首跑未归一 ⇒ 4 个多行锚点全挂，而单行锚点不受影响，故障呈「**部分通过**」的迷惑形态。
3. **方案外附加编辑**用 `--extra <target> <old-file> <new-file>` 传入（可重复），
   与主编辑同批校验、同批写盘 —— 执行期常需补 `import` 之类的小编辑。

用法
----
    python sandbox/_scripts/reusable/apply_proposal_edits.py <proposal.md> [--dry-run] [--json]
    python sandbox/_scripts/reusable/apply_proposal_edits.py <proposal.md> \
        --extra <target> <old.txt> <new.txt> [--extra ...]

退出码：全部应用成功 → 0；任一失配/写入失败 → 1（且**不写盘**）。
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
_ANCHORS = os.path.join(_HERE, 'verify_proposal_anchors.py')


def _load_anchors():
    """import 复用校验器的模块（含 parse 与 norm_eol），不重写解析。"""
    spec = importlib.util.spec_from_file_location('_vpa', _ANCHORS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def detect_file_eol(raw):
    r"""目标文件的「主导行尾」→ '\r\n' 或 '\n'（CRLF 行数 > 裸 LF 行数 ⇒ CRLF）。"""
    crlf = raw.count(b'\r\n')
    lf = raw.count(b'\n')
    return '\r\n' if crlf > lf - crlf else '\n'


def apply_one(text, old_n, new_n, label, file_eol='\n'):
    r"""在 text 中把 old_n（LF 归一形态）替换为 new_n，还原命中区**原行尾**。断言唯一。

    行尾判定：命中区含 CRLF → CRLF；含裸 LF → LF；**单行锚点（不含换行）→ file_eol**
    （目标文件主导行尾）。单行锚点若不回落，会恒判 LF 并把裸 LF 注入 CRLF 文件。

    返回 (新文本, 备注)。失配时抛 AssertionError（调用方统一中止，不写盘）。
    """
    pat = re.compile(re.escape(old_n).replace('\\\n', r'\r?\n'))
    hits = pat.findall(text)
    if len(hits) != 1:
        raise AssertionError('%s: 命中 %d 次（要求恰好 1）' % (label, len(hits)))
    matched = hits[0]
    if '\r\n' in matched:
        eol, src = '\r\n', '命中区'
    elif '\n' in matched:
        eol, src = '\n', '命中区'
    else:
        eol, src = file_eol, '单行回落'
    repl = new_n.replace('\n', eol) if eol == '\r\n' else new_n
    return pat.sub(lambda m: repl, text, count=1), 'eol=%s(%s)' % (
        'CRLF' if eol == '\r\n' else 'LF', src)


def main(argv=None):
    ap = argparse.ArgumentParser(description='方案 §3 编辑点确定性执行器')
    ap.add_argument('proposal')
    ap.add_argument('--extra', nargs=3, action='append', metavar=('TARGET', 'OLD_FILE', 'NEW_FILE'),
                    help='方案外附加编辑（可重复）：目标文件 + 旧文本文件 + 新文本文件')
    ap.add_argument('--dry-run', action='store_true', help='只校验不写盘')
    ap.add_argument('--json', action='store_true', help='输出 JSON 摘要')
    a = ap.parse_args(argv)

    V = _load_anchors()
    steps, edits = V.parse(a.proposal)

    # 🔴 零值守卫（2026-09-17）：无任何编辑点时**不得**报告成功。
    # 原行为：edits 为空 ⇒ 循环不执行 ⇒ results=[] ⇒ 写盘分支遍历空字典不写任何文件
    # ⇒ 打印「已写入 0 处编辑」⇒ return 0。即**解析失败与「方案确实没编辑点」在退出码上同形**，
    # 外层只看 exit code 会判成功（同族：verify_proposal_anchors 的「步骤头 0 个」真空通过）。
    if not edits and not a.extra:
        print('❌ 方案 %s：解析出 0 个 old_string 块（步骤头 %d 个）——§3 格式可能不合规。'
              % (os.path.basename(a.proposal), len(steps)))
        print('   要求：步骤头为 `#### 步骤 N：…`（4 个 # + 全角冒号），'
              '编辑块为**裸三反引号**围栏 + 独立成行的 `old_string:` / `new_string:`。')
        print('   —— 已中止，**未写盘**（零值守卫）')
        return 1

    # 目标文件一次性读入（内存）；eols 存各文件**主导行尾**，供单行锚点回落
    texts, eols = {}, {}
    for e in edits:
        p = e['target']
        if p not in texts:
            raw = open(p, 'rb').read()
            texts[p] = raw.decode('utf-8')
            eols[p] = detect_file_eol(raw)

    results = []
    try:
        for e in edits:
            p, step = e['target'], e['step']
            texts[p], note = apply_one(texts[p], V.norm_eol(e['old']), V.norm_eol(e['new']),
                                       '步骤 %s → %s' % (step, os.path.basename(p)), eols[p])
            results.append({'step': step, 'target': p, 'status': 'OK', 'note': note})
        for k, (tgt, of, nf) in enumerate(a.extra or [], 1):
            if tgt not in texts:
                raw = open(tgt, 'rb').read()
                texts[tgt] = raw.decode('utf-8')
                eols[tgt] = detect_file_eol(raw)
            old_t = open(of, encoding='utf-8').read()
            new_t = open(nf, encoding='utf-8').read()
            texts[tgt], note = apply_one(texts[tgt], V.norm_eol(old_t), V.norm_eol(new_t),
                                         'extra %d → %s' % (k, os.path.basename(tgt)), eols[tgt])
            results.append({'step': 'extra-%d' % k, 'target': tgt, 'status': 'OK', 'note': note})
    except AssertionError as exc:
        print('❌ %s' % exc)
        print('   —— 已中止，**未写盘**')
        return 1

    if not a.dry_run:
        for p, t in texts.items():
            with open(p, 'wb') as f:
                f.write(t.encode('utf-8'))

    if a.json:
        print(json.dumps({'proposal': a.proposal, 'applied': len(results),
                          'dry_run': a.dry_run, 'results': results},
                         ensure_ascii=False, indent=1))
    else:
        print('方案 %s：步骤头 %d 个 / old_string 块 %d 个 / 附加 %d 个' %
              (os.path.basename(a.proposal), len(steps), len(edits), len(a.extra or [])))
        for r in results:
            print('  ✅ %-8s %-46s %s' % (r['step'], os.path.basename(r['target']), r['note']))
        print('  %s %d 处编辑' % ('[dry-run] 校验通过，未写盘：' if a.dry_run else '已写入', len(results)))
    return 0


if __name__ == '__main__':
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
