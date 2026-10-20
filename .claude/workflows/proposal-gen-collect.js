export const meta = {
  name: 'proposal-gen-collect',
  description: 'P0 fact collection for proposal generation: deterministically collect PATH/COUNT/EDIT/REG/BLAST/CHAIN/REUSE ground-truth facts (value + source pairs) for the proposal-gen skill. Mirrors proposal-audit-check Read phase.',
  phases: [
    { title: 'Collect A-D', detail: 'parallel() 4 independent collection blocks (paths, counts, edit points, index/blast/chain/reuse), each with structured schema' },
    { title: 'Synthesize', detail: 'Programmatic in-script merge into one fact sheet, returned for SKILL.md P1 as the closed-set input' },
  ],
  cost: { agents: { min: 4, max: 4 }, mandatory: false,
          notes: 'parallel 4 块 + 程序内合成，固定 4' },
};

// 🔴 仓库根 = Claude Code 的工作目录（cwd）。不写死绝对路径：本仓库在源机为
// .、第二台机为 .，硬编码会把不存在的路径注入 agent 提示，
// 使 Glob/Read/路径基准静默落空。下文 ${PROJECT_ROOT}/x 一律渲染为 ./x，相对 cwd 解析。
const PROJECT_ROOT = '.';

// ── Parse args (script top level, no phase — mirrors proposal-audit-check.js) ──
const topic = args?.topic || '';
const relatedFiles = Array.isArray(args?.related_files) ? args.related_files : [];
const site = args?.site || 'general';
const validSites = ['general', 'G_newdir', 'literature_ingestion', 'chain_tier_b'];
if (!validSites.includes(site)) {
  throw new Error(`Invalid site: ${site}. Must be one of: ${validSites.join(', ')}`);
}

// ── Per-block schemas (structured output enforcement = 证据纪律的机械保障) ──
const PATHS_SCHEMA = {
  type: 'object',
  properties: {
    paths: { type: 'array', items: { type: 'object', properties: {
      path: { type: 'string' }, resolved: { type: 'string' },
      exists: { type: 'boolean' }, fix: { type: 'string' },
      relative_depth: { type: 'string' }, note: { type: 'string' }
    }, required: ['path', 'exists'] }},
    summary: { type: 'string' }
  }, required: ['paths', 'summary']
};

const COUNTS_SCHEMA = {
  type: 'object',
  properties: {
    counts: { type: 'array', items: { type: 'object', properties: {
      claim_type: { type: 'string' }, verified_value: { type: 'string' },
      source: { type: 'string' }, decision_bearing: { type: 'boolean' },
      rederived_conclusion: { type: 'string' }
    }, required: ['claim_type', 'verified_value', 'source'] }},
    summary: { type: 'string' }
  }, required: ['counts', 'summary']
};

const EDITS_SCHEMA = {
  type: 'object',
  properties: {
    edits: { type: 'array', items: { type: 'object', properties: {
      file: { type: 'string' }, anchor_quote: { type: 'string' },
      current_version: { type: 'string' }, structure_type: { type: 'string' },
      facility_exists: { type: 'boolean' }
    }, required: ['file', 'anchor_quote'] }},
    summary: { type: 'string' }
  }, required: ['edits', 'summary']
};

const REG_SCHEMA = {
  type: 'object',
  properties: {
    journal_catalog_entries: { type: 'string' },
    blast: { type: 'array', items: { type: 'object', properties: {
      file: { type: 'string' }, hit_count: { type: 'number' }, refs: { type: 'array', items: { type: 'string' } }
    }, required: ['file', 'hit_count'] }},
    chains: { type: 'array', items: { type: 'object', properties: {
      chain_id: { type: 'string' }, impact: { type: 'string' }
    }, required: ['chain_id'] }},
    reuse: { type: 'array', items: { type: 'object', properties: {
      facility: { type: 'string' }, exists: { type: 'boolean' }, covers: { type: 'string' }
    }, required: ['facility', 'exists'] }},
    summary: { type: 'string' }
  }, required: ['blast', 'reuse', 'summary']
};

// ── Phase: Collect A-D (parallel barrier — 4 independent blocks, Synthesize needs all) ──
phase('Collect A-D');

const [pathsResult, countsResult, editsResult, regResult] = await parallel([
  () => agent(
    `You are a PATH fact collector for proposal generation (D1 路径存在性).\n\n` +
    `Project root: the repo root (cwd). Proposal will land at proposals/YYYY/MM/DD/ (4-segment depth).\n\n` +
    `Candidate related files / paths to verify:\n${JSON.stringify(relatedFiles, null, 2)}\n\n` +
    `For EVERY path in related_files and every path you infer from the topic "${topic}":\n` +
    `1. Resolve to absolute path relative to the repo root (cwd) and verify existence with Glob/test.\n` +
    `2. For relative links that the proposal will contain, resolve from the proposal's landing location: ` +
    `   from proposals/YYYY/MM/DD/ back to the repo root is 4 levels (..→YYYY/MM, ../..→YYYY, ../../..→proposals/, ../../../..→repo root). Count the levels explicitly for every relative link and confirm the target exists.
` +
    `3. Flag any ABSOLUTE path (D:/…, C:/…) and any reference to a directory that does not exist in this repo.
` +
    `4. Verify any proposal output path uses YYYY/MM/DD depth and filename DD matches parent dir.
` +
    `5. Distinguish artifact-TYPE names (e.g. deep_reading/*.md — per-paper, only under project/references/.../<paper>/) from literal top-level paths.\n` +
    `6. Resolve script/command paths to on-disk location (e.g. check_workflows.py and verify_md_syntax.py at ai_system/validation/).

` +
    `Output each path fact with: path, resolved, exists, fix (corrected path if broken), relative_depth (if a relative link), note. ` +
    `Value+source pairs only — never write "verified" without the concrete value.`,
    { label: 'collect:A-paths', phase: 'Collect A-D', schema: PATHS_SCHEMA }
  ),
  () => agent(
    `You are a COUNT fact collector for proposal generation (D2 计数一致性).\n\n` +
    `Project root: the repo root (cwd). Topic: "${topic}". Site: ${site}.\n\n` +
    `Collect ground-truth values for every numeric claim type a proposal for this topic might make, using the claim-type → truth-source mapping:\n` +
    `- 活跃工作流数 → ${PROJECT_ROOT}/ai_system/workflows/workflow_index.md frontmatter + §2\n` +
    `- 七层层计数/总数 → workflow_index.md §1 (各层相加必须 = 总数)\n` +
    `- 工作流版本号 → 对应 .md frontmatter workflow_version (逐字复制含格式)\n` +
    `- 项目版本号 → ai_system/version_registry.md
` +
    `- 项目版本号 → ai_system/version_registry.md\n` +
    `- proposals/catalog 计数 → frontmatter 计数键已于 2026-08-31 退役（不存在）——改为现场数 proposals/_catalog.md §2 数据行\n` +
    `- 目录/文件存量 → Glob the actual directory and wc (NEVER from memory — FM-07)\n` +
    `- Skill / 动态工作流数量 → .claude/skills/*/SKILL.md and .claude/workflows/*.js actual file counts\n\n` +
    `For each count: claim_type, verified_value (the concrete number/version), source (absolute path + location).\n` +
    `If a count supports an exclusion/deferral decision, set decision_bearing=true and in rederived_conclusion re-derive whether the exclusion still holds with the corrected value (FM-08).`,
    { label: 'collect:B-counts', phase: 'Collect A-D', schema: COUNTS_SCHEMA }
  ),
  () => agent(
    `You are an EDIT-POINT fact collector for proposal generation (D4 编辑点结构).\n\n` +
    `Project root: the repo root (cwd). Topic: "${topic}". Candidate related files:\n${JSON.stringify(relatedFiles, null, 2)}\n\n` +
    `For each file the proposal will EDIT (from related_files or inferred from topic):\n` +
    `1. READ the file's actual content — quote the real anchor text verbatim (the old_string the proposal will use). ` +
    `   NEVER write an edit anchor from a remembered or assumed structure (FM-20: writing "add a row to the Metadata table" for a file that is actually YAML frontmatter).\n` +
    `2. Record the file's current version field (workflow_version / kb_version / template_version) from its frontmatter verbatim.\n` +
    `3. Record the structure type where the anchor lives (table / YAML frontmatter / list / prose).\n` +
    `4. If the proposal claims to CREATE a facility, verify it does not already exist (FM-40) — set facility_exists accordingly.\n\n` +
    `Output each edit fact with: file, anchor_quote (verbatim), current_version, structure_type, facility_exists.`,
    { label: 'collect:C-edits', phase: 'Collect A-D', schema: EDITS_SCHEMA }
  ),
  () => agent(
    `You are an INDEX / BLAST / CHAIN / REUSE fact collector for proposal generation (D3/D5/D7).\n\n` +
    `Project root: the repo root (cwd). Topic: "${topic}". Site: ${site}. Candidate related files:\n${JSON.stringify(relatedFiles, null, 2)}\n\n` +
    `Collect:\n` +
    `1. REG: proposals/_catalog.md §2 表首行（最新方案）+ 数据行实盘数。🔴 frontmatter total_entries/latest_entry 与 proposals/index.md frontmatter catalog_proposals_entries 已于 2026-08-31 退役——不存在，勿采集、勿要求 bump。\n` +
    `2. BLAST: for each related/modified file, run the 3-way grep sweep: grep -rl "<filename>" ai_system/workflows/ ai_system/context/ proposals/ and report the ACTUAL hit counts + top refs (FM-27: don't hand-pick a subset). 🆕 作用域隔离：仅记录命中文件名 + 计数，不读取命中文件正文；proposals/ 结果排除本方案同日期目录下的其他兄弟方案 + 本方案自身。\n` +
    `3. SCOPE: which other files reference the modified paths? Report the actual grep hit counts (not a hand-picked subset).
` +
    `4. REUSE: list existing validation scripts (include ai_system/scripts/reusable/verify_proposal_anchors.py and ai_system/scripts/reusable/verify_proposal_declarations.py) (ai_system/validation/check_workflows.py, ai_system/validation/check_official_docs.py, ai_system/validation/verify_md_syntax.py, ai_system/validation/check_claude_md.py), existing Skills (.claude/skills/*/SKILL.md), existing dynamic workflows (.claude/workflows/*.js) — note which already cover what the proposal might build (FM-36/37/41).\n\n` +
    `Value+source pairs only — never write "verified" without the concrete value.`,
    { label: 'collect:D-reg', phase: 'Collect A-D', schema: REG_SCHEMA }
  ),
]);

// ── Phase: Synthesize (programmatic in-script merge — no file write, no extra agent) ──
phase('Synthesize');

const factSheet = {
  topic,
  site,
  generated: 'fact-sheet',
  paths: (pathsResult?.paths || []).map(p => ({
    path: p.path, resolved: p.resolved || '', exists: !!p.exists,
    fix: p.fix || '', relative_depth: p.relative_depth || '', note: p.note || ''
  })),
  counts: (countsResult?.counts || []).map(c => ({
    claim_type: c.claim_type, verified_value: c.verified_value,
    source: c.source, decision_bearing: !!c.decision_bearing,
    rederived_conclusion: c.rederived_conclusion || ''
  })),
  edits: (editsResult?.edits || []).map(e => ({
    file: e.file, anchor_quote: e.anchor_quote,
    current_version: e.current_version || '', structure_type: e.structure_type || '',
    facility_exists: !!e.facility_exists
  })),
  reg: {
    journal_catalog_entries: regResult?.journal_catalog_entries || ''
  },
  blast: (regResult?.blast || []).map(b => ({
    file: b.file, hit_count: b.hit_count, refs: (b.refs || []).slice(0, 10)
  })),
  chains: (regResult?.chains || []).map(c => ({ chain_id: c.chain_id, impact: c.impact || '' })),
  reuse: (regResult?.reuse || []).map(r => ({
    facility: r.facility, exists: !!r.exists, covers: r.covers || ''
  }))
};

log(`Fact sheet: ${factSheet.paths.length} paths, ${factSheet.counts.length} counts, ${factSheet.edits.length} edits, ${factSheet.blast.length} blast entries, ${factSheet.chains.length} chain impacts, ${factSheet.reuse.length} reuse entries.`);

return {
  status: 'COMPLETED',
  fact_sheet: factSheet,
};
