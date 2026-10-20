r"""Workflows/ directory consistency checker.

Validates the ai_system/workflows/ directory against project conventions:
  G1 — Frontmatter validity: every .md must have valid YAML frontmatter with
        required fields (project_version, last_updated, language, purpose).
        🔴 2026-09-22：**必须是真解析器认得的 YAML**，不只是「regex 能切出键值」——
        见 gate1 内的说明（原伪解析器剥引号但不处理转义，使含裸 LaTeX 命令
        `\c*` `\author` 的 changelog 判为合法）。
  G2 — last_updated non-empty: all active workflow files must have a populated
        last_updated field.
  G5 — Cross-reference integrity: all files referenced in workflow_index.md
        must exist on disk, and all disk files must appear in the index.
  G6 — Deprecation consistency: files marked deprecated in §3 must also be
        marked consistently in §1 and §2.
  G7 — Delegation target validity (--strict): workflow_alignment_audit.md §4
        delegation targets must not reference deprecated workflows.
  # G3 (index-磁盘注册数对账) / G4 (版本注册表分桶计数) / G8 (审计卡片新鲜度) /
  # G9 (.js meta.cost) 均已退役：G8 于 2026-08-18，G3/G4/G9 于 2026-08-31——均为纯计数/门禁设施。

Usage
-----
    python ai_system/validation/check_workflows.py
    python ai_system/validation/check_workflows.py --strict
    python ai_system/validation/check_workflows.py --quiet
"""

import sys
import os
import re

# PyYAML 用于 G1 的**严格** frontmatter 校验。它是 `lab/pyproject.toml`
# `[project.optional-dependencies].dev` 的声明依赖，CI 走 `pip install -e ".[dev]"`。
# 但本脚本也以 `language: system` 被 pre-commit 调用（用开发者本机解释器），
# 故软导入：缺失时 G1 降级为 WARN **并显式说出跳过了什么**（不静默）。
try:
    import yaml
except ImportError:                                          # pragma: no cover
    yaml = None
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
_WORKFLOW_DIR = os.path.join(_PROJECT_ROOT, 'ai_system', 'workflows')
_INDEX_FILE = os.path.join(_WORKFLOW_DIR, 'workflow_index.md')
_GUIDE_FILE = os.path.join(_WORKFLOW_DIR, 'workflow_usage_guide.md')
_AUDIT_FILE = os.path.join(_WORKFLOW_DIR, 'workflow_alignment_audit.md')
_AUDIT_INDEX = os.path.join(_PROJECT_ROOT, 'ai_system', 'audit', 'workflows', 'index.md')

# Files in workflows/ that are NOT workflow definitions（非工作流定义文件，无 G1 必需字段约束）。
_NON_WORKFLOW_FILES = {
    'workflow_index.md',
    'workflow_usage_guide.md',
    'chain_template_catalog.md',
}

# External .md files referenced by workflow_index.md that are NOT in
# ai_system/workflows/ — they live in other project directories.
_KNOWN_EXTERNAL_REFS = {
    'documentation_rules.md',      # ai_system/context/ (optional context file)
    '_extracted_text.md',          # references/ (document extraction output)
    '_translation_cn.md',          # references/ (translation output)
    '_transcript.md',              # project/meeting_notes/ (transcription output)
    '_source.md',                  # sandbox/external/ (third-party repo ingestion metadata)
    '_references/references.md',   # sandbox/external/ (third-party repo index)
    'SANDBOX_CONTEXT.md',          # sandbox/ (project-level sandbox context)
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_utf8(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _write_utf8(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def _parse_frontmatter(text):
    """Return (dict, raw_string) or (None, None) if no valid frontmatter."""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None, None
    raw = m.group(1)
    # Minimal YAML parser: extract key: value pairs (single-line, quoted or unquoted)
    fm = {}
    for line in raw.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        kv = re.match(r'^(\w[\w_-]*)\s*:\s*(.*)', line)
        if kv:
            key = kv.group(1)
            val = kv.group(2).strip()
            # Remove surrounding quotes
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            fm[key] = val
    return fm, raw


def _get_workflow_files():
    """Return list of (Path, frontmatter_dict) for workflow definition files."""
    results = []
    for f in sorted(Path(_WORKFLOW_DIR).glob('*.md')):
        if f.name in _NON_WORKFLOW_FILES:
            continue
        text = _read_utf8(str(f))
        fm, _ = _parse_frontmatter(text)
        results.append((f, fm, text))
    return results


def _parse_deprecated_set(index_text):
    """Parse §3 废弃记录 table to get set of deprecated filenames."""
    deprecated = set()
    in_section = False
    for line in index_text.split('\n'):
        if line.strip().startswith('## 3. 废弃记录'):
            in_section = True
            continue
        if in_section and line.strip().startswith('## '):
            break
        if in_section:
            # Match table rows: | `filename.md` | date | replacement |
            m = re.match(r'\|\s*`([^`]+\.md)`\s*\|', line)
            if m and not m.group(1).startswith('工作流'):
                deprecated.add(m.group(1))
    return deprecated


def _parse_completed_set(index_text):
    """Parse 已完成工作流 line to get completed filenames."""
    completed = set()
    m = re.search(r'已完成工作流[：:]\s*(.+)', index_text)
    if m:
        # Extract filenames from the rest of the text
        for fn in re.finditer(r'`([^`]+\.md)`', m.group(1)):
            completed.add(fn.group(1))
    return completed


def _parse_index_file_refs(index_text):
    """Return set of .md filenames referenced in §1 tree and §2 tables."""
    refs = set()
    # Match `filename.md` patterns (with optional backtick)
    for m in re.finditer(r'`([^`]+\.md)`', index_text):
        refs.add(m.group(1))
    return refs


# ---------------------------------------------------------------------------
# G1 — Frontmatter Validity
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ['project_version', 'last_updated', 'language', 'purpose']

_FM_BLOCK_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
_warned_no_yaml = False


def gate1_frontmatter_validity(workflow_data):
    """Each .md must have valid YAML frontmatter with required fields.

    🔴 2026-09-22：增**真解析器**校验。此处原先只靠 `_parse_frontmatter()`——
    一个 regex 伪解析器：它按行取 `key: value`、**剥掉首尾引号但不处理转义**，
    因此「regex 切得出键值」被当成了「frontmatter 合法」。实证该盲区：
    `workflow_index.md` 与 `research_presentation_pdf_workflow.md` 的 `changelog`
    含裸 LaTeX 命令（`\\c*` `\\q*` `\\author` `\\graphicspath`），真 YAML 解析器报
    `found unknown escape character`，而 G1 一路 PASS —— 80 个定义文件中 2 个非合法
    YAML 而闸门全绿。与同日修的工作台账 #264（`verify_md_syntax --all` 的作用域）同族：
    **闸门宣称的域 ≠ 实际覆盖的域**；那次按「台账命名而无 id ⇒ FAIL」收窄 M0 同理。
    注：`_parse_frontmatter` 仍保留用于**取字段**（其它闸门依赖其扁平字符串），
    本处只增不改。
    """
    global _warned_no_yaml
    errors = []
    if yaml is None and not _warned_no_yaml:
        _warned_no_yaml = True
        print("⚠️  G1: PyYAML 未安装——**严格 YAML 校验已跳过**（只做键值存在性检查）。"
              "装回（`pip install -e \".[dev]\"`）后再跑，否则本门禁覆盖不完整。",
              file=sys.stderr)
    for fpath, fm, text in workflow_data:
        rel = os.path.relpath(str(fpath), _PROJECT_ROOT)
        if fm is None:
            errors.append(f"G1: Missing or malformed frontmatter in {rel}")
            continue
        if not fm:
            errors.append(f"G1: Empty frontmatter in {rel}")
            continue
        if yaml is not None:
            m = _FM_BLOCK_RE.match(text or '')
            if m:
                try:
                    yaml.safe_load(m.group(1))
                except yaml.YAMLError as exc:
                    detail = ' '.join(str(exc).split())[:160]
                    errors.append(
                        f"G1: Invalid YAML frontmatter in {rel} — {detail}"
                    )
        for field in REQUIRED_FIELDS:
            val = fm.get(field, '')
            if not val or val.strip() == '':
                errors.append(
                    f"G1: Missing/empty required field '{field}' in {rel}"
                )
    return errors


# ---------------------------------------------------------------------------
# G2 — last_updated Non-Empty (active files only)
# ---------------------------------------------------------------------------

def gate2_last_updated_nonempty(workflow_data, deprecated, completed):
    """All non-deprecated/non-completed files must have non-empty last_updated."""
    errors = []
    for fpath, fm, text in workflow_data:
        name = fpath.name
        if name in deprecated or name in completed:
            continue
        if fm is None:
            continue  # G1 will catch
        lu = fm.get('last_updated', '')
        if not lu or lu.strip() == '':
            rel = os.path.relpath(str(fpath), _PROJECT_ROOT)
            errors.append(f"G2: Empty last_updated in active file {rel}")
    return errors


# ---------------------------------------------------------------------------
# G5 — Cross-Reference Integrity
# ---------------------------------------------------------------------------

def gate5_cross_reference_integrity(workflow_data, index_text):
    """All workflow files on disk must be referenced in index;
    all index references that look like workflow files must exist on disk."""
    errors = []

    index_refs = _parse_index_file_refs(index_text)

    # Build disk names set: only files actually in workflows/ directory
    disk_names = set()
    for fpath, fm, text in workflow_data:
        disk_names.add(fpath.name)
    disk_names.add('workflow_index.md')
    disk_names.add('workflow_usage_guide.md')

    # Files on disk but not referenced in index (exclude non-workflow files)
    for name in sorted(disk_names):
        if name in _NON_WORKFLOW_FILES:
            continue
        if name not in index_refs:
            errors.append(
                f"G5: '{name}' exists on disk but not referenced in "
                f"workflow_index.md"
            )

    # Index refs that should be in workflows/ but are missing.
    # The index IS the authoritative registry of what files should exist.
    # Flag every missing .md reference not explicitly excluded.
    for ref in sorted(index_refs):
        if ref in disk_names:
            continue  # exists on disk — OK
        if ref in _NON_WORKFLOW_FILES:
            continue  # intentionally not a workflow-definition file
        if ref in _KNOWN_EXTERNAL_REFS:
            continue  # intentionally lives outside workflows/
        # Ref is in the index but missing from disk — registry violation
        errors.append(
            f"G5: Index references '{ref}' but file not found in "
            f"workflows/"
        )

    return errors


# ---------------------------------------------------------------------------
# G6 — Deprecation Consistency
# ---------------------------------------------------------------------------

def gate6_deprecation_consistency(workflow_data, index_text, deprecated):
    """Files in §3 as deprecated must also be marked so in §1 and §2."""
    errors = []

    # All deprecated files must appear in index text with ⚠️ marker
    for name in sorted(deprecated):
        # Check §1 (tree) — look for ⚠️ marker near the filename (same line only)
        pattern = re.compile(
            r'`' + re.escape(name) + r'`[^\n]*?(?:⚠️|已废弃)'
        )
        if not pattern.search(index_text):
            errors.append(
                f"G6: '{name}' is in §3 废弃记录 but not marked ⚠️/已废弃 in §1 or §2"
            )

    # All files marked ⚠️ in §1 or §2 should also be in §3
    # Find all ⚠️ marked filenames (within same line only — no cross-line matching)
    deprecated_in_body = set()
    for m in re.finditer(r'`([^`]+\.md)`[^\n]*?(?:⚠️|已废弃)', index_text):
        deprecated_in_body.add(m.group(1))

    for name in sorted(deprecated_in_body):
        if name not in deprecated:
            errors.append(
                f"G6: '{name}' is marked ⚠️/已废弃 in §1/§2 "
                f"but not listed in §3 废弃记录"
            )

    return errors


# ---------------------------------------------------------------------------
# G7 — Delegation Target Validity (--strict only)
# ---------------------------------------------------------------------------

def gate7_delegation_validity(deprecated, completed):
    """workflow_alignment_audit.md §4 must not delegate to deprecated workflows."""
    errors = []
    if not os.path.exists(_AUDIT_FILE):
        errors.append("G7: workflow_alignment_audit.md not found")
        return errors

    audit_text = _read_utf8(_AUDIT_FILE)
    # Find §4 delegation section
    # Match patterns like: → `filename.md`
    for m in re.finditer(r'→\s*`([^`]+\.md)`', audit_text):
        target = m.group(1)
        if target in deprecated:
            # Check if the same line marks it as deprecated
            line_start = audit_text.rfind('\n', 0, m.start()) + 1
            line_end = audit_text.find('\n', m.end())
            if line_end == -1:
                line_end = len(audit_text)
            context_line = audit_text[line_start:line_end]
            if re.search(r'⚠️|已废弃|deprecated', context_line):
                continue  # Already annotated — not an error
            errors.append(
                f"G7: workflow_alignment_audit.md §4 delegates to deprecated "
                f"workflow '{target}'"
            )

    return errors


# ---------------------------------------------------------------------------
# G8 — Audit Card Freshness (--strict only)
# ---------------------------------------------------------------------------

def _parse_audit_index_rows(audit_text):
    """Parse per-layer and governance tables from audit index.
    Returns (workflow_rows, governance_rows) where each row is
    {name, latest_audit, findings, health, card_link}.
    """
    wf_rows = []
    gov_rows = []
    in_gov = False
    in_table = False
    collecting = True
    for line in audit_text.split('\n'):
        # Detect governance section
        if 'Governance' in line and line.strip().startswith('##'):
            in_gov = True
            in_table = False
            continue
        if in_gov and line.strip().startswith('##') and 'Governance' not in line:
            in_gov = False
            in_table = False
        # 🆕 边界收束：批次日志/统计面板节后彻底停止收集
        # （仅设 in_table=False 不够：批次日志分隔行 `|------|` 会重新触发表开始检测，
        #   导致批次日志数据行如 `| 2026-08-14 | full | 56 |...` 被误解析为 wf_row）
        if line.strip().startswith('## 审计批次日志') or line.strip().startswith('## 统计面板'):
            collecting = False
            in_table = False
            continue
        if not collecting:
            continue
        # Detect table start
        if '|' in line and ('---|' in line or '-+-' in line):
            in_table = True
            continue
        if in_table and line.startswith('|'):
            # Parse: | `name` | version | health | findings | date |（.js Phase 4 层表序）
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5:
                name = parts[1].strip('`')
                date = parts[5].strip() if len(parts) > 5 else ''
                entry = {
                    'name': name,
                    'latest_audit': date,
                }
                if in_gov:
                    gov_rows.append(entry)
                else:
                    wf_rows.append(entry)
        if in_table and not line.startswith('|'):
            in_table = False
    return wf_rows, gov_rows


def _parse_audit_index_frontmatter(audit_text):
    """Extract frontmatter stats from audit index."""
    fm, _ = _parse_frontmatter(audit_text)
    if not fm:
        return {}
    result = {}
    for key in ('last_full_audit', 'last_incremental_audit',
                'total_active_workflows', 'total_governance_files',
                'total_healthy', 'total_attention', 'total_stale',
                'total_broken', 'total_not_audited'):
        val = fm.get(key, '')
        if val:
            try:
                result[key] = int(val)
            except ValueError:
                result[key] = val
    return result


def gate8_audit_card_freshness(workflow_data, deprecated, completed):
    """Check per-workflow audit cards are fresh vs workflow last_updated."""
    errors = []

    if not os.path.exists(_AUDIT_INDEX):
        errors.append("G8: Audit index not found at ai_system/audit/workflows/index.md")
        return errors

    audit_text = _read_utf8(_AUDIT_INDEX)
    wf_rows, gov_rows = _parse_audit_index_rows(audit_text)
    fm_stats = _parse_audit_index_frontmatter(audit_text)

    # Build set of active workflow names
    active_names = set()
    wf_last_updated = {}
    for fpath, fm, text in workflow_data:
        name = fpath.name
        if name in deprecated or name in completed:
            continue
        if fm is None:
            continue
        active_names.add(name)
        lu = fm.get('last_updated', '')
        wf_last_updated[name] = lu

    # Check 1: Each active workflow has an audit index row
    audited_names = {r['name'] for r in wf_rows}
    for name in sorted(active_names):
        if name not in audited_names:
            errors.append(
                f"G8: Active workflow '{name}' has no row in audit index"
            )

    # Check 2: Governance files (3) have rows
    expected_gov = {'workflow_index.md', 'workflow_usage_guide.md',
                    'chain_template_catalog.md'}
    audited_gov = {r['name'] for r in gov_rows}
    for name in sorted(expected_gov):
        if name not in audited_gov:
            errors.append(
                f"G8: Governance file '{name}' has no row in audit index governance section"
            )

    # Check 3: For audited workflows, latest_audit >= last_updated
    for row in wf_rows:
        name = row['name']
        if name in wf_last_updated and wf_last_updated[name]:
            lu = wf_last_updated[name]
            la = row.get('latest_audit', '')
            if la and la < lu:
                errors.append(
                    f"G8: '{name}' audit card stale — last_audited={la} < "
                    f"last_updated={lu}"
                )

    # Check 4: Frontmatter stats match actual row counts
    actual_wf = len([r for r in wf_rows if r['name'] not in deprecated and r['name'] not in completed])
    actual_gov = len(gov_rows)
    claimed_wf = fm_stats.get('total_active_workflows')
    claimed_gov = fm_stats.get('total_governance_files')
    if claimed_wf is not None and actual_wf != claimed_wf:
        errors.append(
            f"G8: Audit index claims {claimed_wf} workflows, "
            f"but has {actual_wf} rows"
        )
    if claimed_gov is not None and actual_gov != claimed_gov:
        errors.append(
            f"G8: Audit index claims {claimed_gov} governance files, "
            f"but has {actual_gov} rows"
        )

    return errors


# ---------------------------------------------------------------------------
# G9 — Dynamic workflow meta.cost validity (G_wf_confirm data source)
# ---------------------------------------------------------------------------

def gate9_meta_cost_validity():
    """G9 — Validate meta.cost in .claude/workflows/*.js.

    Every dynamic workflow must declare a cost profile in its meta block:
      cost: { agents: { min, max }, mandatory, gate?, notes }
    Requirements: cost present; agents.min/max present; mandatory present;
                  max >= min >= 1. 缺失/结构错 → FAIL（阻断，防 G_wf_confirm 静默失效）。
    """
    _JS_DIR = os.path.join(_PROJECT_ROOT, '.claude', 'workflows')
    errors = []
    if not os.path.isdir(_JS_DIR):
        return errors
    js_files = sorted(
        f for f in os.listdir(_JS_DIR)
        if f.endswith('.js') and not f.startswith('.') and not f.startswith('_')
    )
    for fname in js_files:
        rel = os.path.join('.claude', 'workflows', fname)
        fpath = os.path.join(_JS_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                src = fh.read()
        except OSError as exc:
            errors.append(f"G9: {rel} — 无法读取: {exc}")
            continue
        meta_m = re.search(r'export\s+const\s+meta\s*=\s*\{', src)
        if not meta_m:
            errors.append(f"G9: {rel} — 缺 export const meta 块")
            continue
        region = src[meta_m.start():meta_m.start() + 2000]
        cost_m = re.search(r'\bcost\s*:\s*\{', region)
        if not cost_m:
            errors.append(
                f"G9: {rel} — meta.cost 缺失（G_wf_confirm 数据源，见 CLAUDE.md「动态工作流触发确认阀门」段）"
            )
            continue
        cost_region = region[cost_m.start():cost_m.start() + 500]
        a_min = re.search(r'\bmin\s*:\s*(\d+)', cost_region)
        a_max = re.search(r'\bmax\s*:\s*(\d+)', cost_region)
        mandatory = re.search(r'\bmandatory\s*:\s*(true|false)', cost_region)
        if not (a_min and a_max and mandatory):
            errors.append(f"G9: {rel} — meta.cost 结构不完整（需 agents:{min,max} + mandatory）")
            continue
        v_min, v_max = int(a_min.group(1)), int(a_max.group(1))
        if v_min < 1:
            errors.append(f"G9: {rel} — agents.min={v_min} 应 ≥ 1")
        if v_max < v_min:
            errors.append(f"G9: {rel} — agents.max={v_max} < agents.min={v_min}")
        if v_max < 1:
            errors.append(f"G9: {rel} — agents.max={v_max} 应 ≥ 1")
    return errors


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Validate ai_system/workflows/ consistency'
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Enable G7 (delegation target validity)'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Only print FAIL lines'
    )
    args = parser.parse_args()

    # Load data
    if not os.path.isdir(_WORKFLOW_DIR):
        print(f"ERROR: workflow directory not found: {_WORKFLOW_DIR}")
        sys.exit(2)

    workflow_data = _get_workflow_files()
    index_text = _read_utf8(_INDEX_FILE)

    deprecated = _parse_deprecated_set(index_text)
    completed = _parse_completed_set(index_text)

    # Strip frontmatter for G6 — changelog can cause false positive matches
    # (e.g. "_extracted_text.md" on the same long line as "废弃")
    index_body = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', index_text, flags=re.DOTALL)

    # 🔴 RETIRED 2026-08-31: G3 (索引-磁盘注册数对账) / G4 (版本注册表分桶计数+auto-fix) /
    # G9 (.js meta.cost 校验，G_wf_confirm 数据源) 是纯计数/门禁设施，瘦身退役。
    # 保留格式/一致性校验 G1/G2/G5/G6/G7。
    # 2026-09-10: G3/G4 的函数体、版本解析器与 --fix 参数一并删除——其解析目标
    # version_registry.md §2 分桶行已移除，永久无法解析，留作死代码只会误导读文档的人。
    gates = [
        ('G1', gate1_frontmatter_validity(workflow_data)),
        ('G2', gate2_last_updated_nonempty(workflow_data, deprecated, completed)),
        ('G5', gate5_cross_reference_integrity(workflow_data, index_text)),
        ('G6', gate6_deprecation_consistency(workflow_data, index_body, deprecated)),
    ]
    if args.strict:
        gates.append(('G7', gate7_delegation_validity(deprecated, completed)))
        # G8 (audit card freshness) 已退役 (2026-08-18) —— per_workflow_audit 卡片体系废弃，保留会随时间必然 FAIL

    # Run and report
    all_errors = []
    for gate_name, errors in gates:
        if errors:
            status = 'FAIL'
            all_errors.extend(errors)
        else:
            status = 'PASS'
        if not args.quiet or errors:
            print(f"{gate_name}: {status}")
            for e in errors:
                print(f"  [FAIL] {e}")

    total = len(all_errors)
    if total > 0:
        summary_gate = "FAIL"
    else:
        summary_gate = "PASS"

    if not args.quiet or total > 0:
        print(f"\nSummary: {summary_gate} ({total} error(s))")

    sys.exit(1 if total > 0 else 0)


if __name__ == '__main__':
    main()
