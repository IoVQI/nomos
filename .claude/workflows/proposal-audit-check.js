export const meta = {
  name: 'proposal-audit-check',
  description: 'Audit a proposal across 7 dimensions (paths, counts, indices, logic, registration, destructiveness, reuse) before human review. Outputs structured findings JSON + Markdown report.',
  phases: [
    { title: 'Read', detail: 'Read proposal + related workflows per depth setting' },
    { title: 'Mech', detail: 'Phase 1.5 机械核验 verify_proposal_declarations.py（FM-30/31/33 集合断言）' },
    { title: 'Audit D1-D7', detail: 'pipeline() 7 parallel dimension audits, structured schema each' },
    { title: 'Synthesize', detail: 'Merge findings, classify AUTO_FIX/SEMI/MANUAL, write report' },
  ],
  cost: { agents: { min: 9, max: 10 }, mandatory: false,
          notes: 'Read 1 + Mech 1（Phase 1.5）+ pipeline 7 维度 + 程序内合成' },
};

// 🔴 仓库根 = Claude Code 的工作目录（cwd）。不写死绝对路径：本仓库在源机为
// .、第二台机为 .，硬编码会把不存在的路径注入 agent 提示，
// 使 Glob/Read/路径基准静默落空。下文 ${PROJECT_ROOT}/x 一律渲染为 ./x，相对 cwd 解析。
const PROJECT_ROOT = '.';
const WORKFLOW_REF = `${PROJECT_ROOT}/ai_system/workflows/proposal_audit_workflow.md`;

// ── Audit dimension rules (inlined from proposal_audit_workflow.md Phase 2-8, wf-1.0, 2026-07-28) ──
// ⚠️ 修改 MD 工作流 Phase 2-8 的审计规则时，同步更新下方常量。

const D1_RULES = `## D1 — 路径存在性审计
对方案中提取的每一个文件路径引用：
1. 解析为绝对路径（基准: 仓库根 = cwd）
2. 用 Glob 验证存在性（test -f / test -d 等价）
3. 若不存在 → 用 Glob 搜索同一父目录下的近似文件名
4. 若 Glob 命中 → 报告「疑似拼写错误：方案写 X，实际为 Y」
5. 若 Glob 无命中 → 报告「路径不存在: <path>」
已知路径陷阱（本骨架一律用**仓库相对路径**）：
- 绝对路径（`D:/…`、`C:/…`）⇒ 报错
- 顶层目录写错（真值 = 仓库根的实盘目录列表）
- 引用原项目已不存在的目录名（如 Journal、lab，以及早期 sandbox 下的 _parallel、_handoff、_scripts）`;

const D2_RULES = `## D2 — 计数一致性审计
对方案中提取的每一个数值声明，交叉验证真源：
- 活跃工作流数 → workflow_index.md §2 注册表**现场数行**（frontmatter 无计数键）
- 层计数 / 总计 → 🔴 已于 2026-08-31 退役为真值指针；若方案声明此类数字，报「引用了已退役的计数设施」
- 工作流版本号 → 🔴 frontmatter workflow_version 已于 2026-08-31 退役；不要求核对（版本串为冻结历史注解）
- 链模板版本号 → 🔴 frontmatter catalog_version 不存在；同上
- 项目版本号 → ai_system/version_registry.md §1
- 方案计数 → 🔴 frontmatter 计数键已退役；真值 = 现场数 proposals/_catalog.md §2 数据行
- 闸门可跑性 → 方案声明的每条终验命令，必须能在 ai_system/validation/ 实盘找到
- Skill 数量 → .claude/skills/*/SKILL.md 文件数
- 动态工作流数量 → .claude/workflows/*.js 文件数
- 变更文件清单行数是否等于声明的数量（🔴 集合版见 Phase 1.5 机械核验）`;

const D3_RULES = `## D3 — 索引完整性审计
对方案声明的每个新建设施，检查对应索引的注册情况：
- 新建 workflow .md → workflow_index.md §1 全景树 + §2 注册表行
- 新建 skill → .claude/skills/README.md「已注册」表
- 新建 dynamic workflow → .claude/workflows/README.md「已注册」表
- 新建方案文件 → proposals/index.md + proposals/_catalog.md
- 新建版本相关设施 → ai_system/version_registry.md §二
- 方案自身的注册 → 检查 proposals/index.md + _catalog.md 是否有对应条目`;

const D4_RULES = `## D4 — 逻辑自洽性审计
检查以下逻辑一致性：
1. 步骤依赖顺序 — 是否存在步骤引用后续步骤产物的逆序依赖？
2. 闸门一致性 — 同一条件在不同段落是否有不同描述/行为？
3. 摘要与步骤一致性 — 摘要声明（如「只读」）与实际步骤（Edit/Write/rm）是否冲突？
4. 前提条件可满足性 — Prerequisites 中声明的文件/工具/环境是否真实存在？
5. CLAUDE.md 冲突 — 方案假设是否与 CLAUDE.md 硬约束矛盾？
6. 图表-代码一致性 — ASCII 图/表格列数是否与描述匹配？`;

const D5_RULES = `## D5 — 注册完备性审计（仅 L2+）
对每个新建设施检查：
- 新建工作流：workflow_index.md §1 树条目 + §2 注册表行 + §4 维护触发器评估
- 新建 Skill：名称唯一性 + description 触发词覆盖 + .claude/skills/README.md
- 新建动态工作流：meta.name 唯一 + meta.phases 完整 + .claude/workflows/README.md
- 跨层影响：属于七层中的哪层？该层计数字段是否需要更新？
- version_registry.md：是否需要新增 §2 行？`;

const D6_RULES = `## D6 — 破坏性评估审计（仅 L2+）
对方案中每个被修改的现有文件：
1. 影响面查询（3 路 grep）：
   - grep -rl "filename" ai_system/workflows/  → 被哪些工作流引用
   - grep -rl "filename" ai_system/context/    → 被哪些上下文引用
   - grep -rl "filename" proposals/              → 被哪些方案/报告引用
2. 不可逆操作检测：是否有文件删除/git mv/工作流废弃？有无回滚方案？
3. 约定冲突：新增 frontmatter 字段/命名规则是否与现有文件冲突？
4. 可逆性：方案是否给出回滚路径，或建议先在可回滚的小范围内验证？`;

const D7_RULES = `## D7 — 已有设施复用度审计（仅 L2+）
对方案中每个新建设施：
1. 重复造轮子检测 — 比对已有 active 工作流（真值 = workflow_index.md §2 现场数行，勿硬编码）+ Skills + 动态工作流 + 验证脚本
2. 委托充分性 — Skill → 委托到已有工作流 .md？动态工作流 → 引用 .md？
4. 基础设施复用 — 是否利用了已有验证脚本（check_workflows / check_official_docs / verify_md_syntax / check_claude_md / verify_proposal_anchors / verify_proposal_declarations）？
5. 模式一致性 — 架构选型是否遵循 P0/P1/P2 标准？
   - P0 (md 加固): execution_mode: strict + 退出条件
   - P1 (动态工作流): 线性 Phase + 结构化输出 + 固定命令 + ≤15 agents + 无运行时交互
   - P2 (Skill): 高频调用 + 工具漂移 + allowed-tools 可锁定 + 参数化收益
6. 冗余声明检测 — 是否声称「新建」了已存在的设施？`;

// ── Parse args ──
const proposalPath = args?.proposalPath || null;
const depth = args?.depth || 'l2';
const validDepths = ['l1', 'l2', 'l3', 'l4'];
if (!validDepths.includes(depth)) {
  throw new Error(`Invalid depth: ${depth}. Must be one of: ${validDepths.join(', ')}`);
}
if (!proposalPath) {
  throw new Error('args.proposalPath is required. Pass the absolute path to the proposal file.');
}

const impact = args?.impact || 'i2'; // 🆕 wf-1.1: 影响广度轴
const validImpacts = ['i1', 'i2', 'i3'];
if (!validImpacts.includes(impact)) {
  throw new Error(`Invalid impact: ${impact}. Must be one of: ${validImpacts.join(', ')}`);
}
const isI2Plus = impact === 'i2' || impact === 'i3';
const isI3 = impact === 'i3';

const isL2Plus = depth === 'l2' || depth === 'l3' || depth === 'l4';
const isL3Plus = depth === 'l3' || depth === 'l4';
const isL4 = depth === 'l4';

// ── Phase 1: Read ──
phase('Read');

const readResult = await agent(
  `Read the proposal file at ${proposalPath} in full.\n\n` +
  `Extract and return:\n` +
  `1. All file path references (from frontmatter related[], Markdown links [text](path), code blocks, and inline paths)\n` +
  `2. All numeric claims (counts like "N active workflows", "M files modified", version numbers like wf-x.y)\n` +
  `3. All index facility references (workflow_index, official_docs/index.md, proposals/index.md, _catalog.md, README files)
` +
  `4. The logic chain: ordered list of steps/phases with their declared dependencies and gate conditions\n` +
  `5. All new facilities the proposal declares it will create (workflows, skills, dynamic workflows, scripts, directories)\n` +
  `6. All existing files the proposal declares it will modify\n` +
  `7. The full frontmatter (especially related[], status, tags)\n\n` +
  `Depth is ${depth}. For L2+: also read the frontmatter of each file listed in the proposal's related[] frontmatter field\n` +
  `For L3+: also read §1/§2 of any chain templates and upstream/downstream workflows referenced in the proposal\n` +
  `🆕 Impact breadth is ${impact}:\n` +
  `- I1: only extract files explicitly listed in the proposal's modified_files/related (current behavior)\n` +
  `- I2: For each file in modified_files, run grep -rl "<filename>" ai_system/workflows/ ai_system/context/ proposals/ to discover transitive references. Return discovered files as transitive_refs[{source_file, discovered_refs[]}]. 🆕 作用域隔离：① 仅记录「命中文件名 + 命中计数」，禁止读取命中文件正文；② proposals/ 扫描结果排除「本方案同日期目录 proposals/YYYY/MM/DD/ 下的其他兄弟方案 + 本方案自身」；③ transitive_refs 仅用于爆炸半径计数，正文内容不得混入本方案审计维度。\n` +
  `- I3: I2 + also check ai_system/version_registry.md for consumers of modified versioned facilities. 🆕 同样遵守 I2 的作用域隔离约束。
` +
  `For L4: also read the full body of all referenced workflow documents`,
  { label: 'read-proposal', phase: 'Read', schema: {
    type: 'object',
    properties: {
      proposal_stem: { type: 'string' },
      proposal_date: { type: 'string' },
      proposal_status: { type: 'string' },
      path_refs: { type: 'array', items: { type: 'object', properties: {
        raw: { type: 'string' }, location: { type: 'string' }, context: { type: 'string' }
      }, required: ['raw', 'location'] }},
      numeric_claims: { type: 'array', items: { type: 'object', properties: {
        claim: { type: 'string' }, value: { type: 'number' }, unit: { type: 'string' }, location: { type: 'string' }
      }, required: ['claim', 'value', 'location'] }},
      index_refs: { type: 'array', items: { type: 'object', properties: {
        facility: { type: 'string' }, location: { type: 'string' }
      }, required: ['facility', 'location'] }},
      logic_chain: { type: 'array', items: { type: 'object', properties: {
        step_id: { type: 'string' }, description: { type: 'string' }, dependencies: { type: 'array', items: { type: 'string' } },
        gates: { type: 'array', items: { type: 'string' } }
      }, required: ['step_id', 'description'] }},
      new_facilities: { type: 'array', items: { type: 'object', properties: {
        type: { type: 'string', enum: ['workflow', 'skill', 'dynamic_workflow', 'script', 'directory', 'chain_template', 'other'] },
        path: { type: 'string' }, description: { type: 'string' }
      }, required: ['type', 'path'] }},
      modified_files: { type: 'array', items: { type: 'string' } },
      related_files: { type: 'array', items: { type: 'string' } },
      related_frontmatters: { type: 'object' },
      transitive_refs: { type: 'array', items: { type: 'object', properties: {  // 🆕 I2+
        source_file: { type: 'string' }, discovered_refs: { type: 'array', items: { type: 'string' } }
      }}},
      chain_impacts: { type: 'array', items: { type: 'string' } }  // 🆕 I3 only
    }, required: ['proposal_stem', 'path_refs', 'numeric_claims', 'index_refs', 'logic_chain', 'new_facilities', 'modified_files']
  }}
);

if (!readResult) {
  log('🔴 Read phase failed — proposal file may not exist or be unreadable.');
  return { status: 'FAILED', reason: 'read_phase_failed' };
}

log(`Read complete: ${readResult.path_refs.length} path refs, ${readResult.numeric_claims.length} numeric claims, ${readResult.new_facilities.length} new facilities.`);

// ── Finding Schema (shared across all dimensions) ──
const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    dimension: { type: 'string', enum: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'] },
    findings: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['CRITICAL', 'WARNING', 'INFO'] },
      category: { type: 'string' },
      location: { type: 'string' },
      claim: { type: 'string' },
      actual: { type: 'string' },
      fix_classification: { type: 'string', enum: ['AUTO_FIX', 'SEMI', 'MANUAL'] },
      fix_suggestion: { type: 'string' }
    }, required: ['severity', 'category', 'location', 'claim', 'actual', 'fix_classification'] }},
    summary: { type: 'string' }
  }, required: ['dimension', 'findings', 'summary']
};

// ── Phase 1.5: Mech — 声明面一致性机械核验（FM-30/31/33）──
phase('Mech');

const MECH_SCRIPT = `${PROJECT_ROOT}/ai_system/scripts/reusable/verify_proposal_declarations.py`;
const mechResult = await agent(
  `Run this exact command and return its JSON output verbatim:\n` +
  `python "${MECH_SCRIPT}" "${proposalPath}" --json\n\n` +
  `Do not interpret or repair the output — return the JSON as-is. ` +
  `If the command fails to run (non-zero exit with a Python traceback), return ` +
  `{"error": "<last line of the traceback>"} instead.`,
  { label: 'mech-declarations', phase: 'Mech', schema: {
    type: 'object',
    properties: {
      ok: { type: 'number' }, total: { type: 'number' },
      nochange_section_present: { type: 'boolean' },
      targets: { type: 'array', items: { type: 'string' } },
      assertions: { type: 'array', items: { type: 'object', properties: {
        assertion: { type: 'string' }, violations: { type: 'array', items: { type: 'string' } }
      }, required: ['assertion'] } },
      error: { type: 'string' }
    }, required: []
  }}
);

// 机械 findings 映射到既有 D 维度（FM-33→D7 / FM-21→D2 / FM-30→D4），保持 FINDING_SCHEMA 契约
const MECH_DIM = { A1: 'D7', A2: 'D2', A3: 'D4' };
const mechFindings = [];
if (mechResult && mechResult.error) {
  mechFindings.push({ dimension: 'D1', severity: 'WARNING',
    category: 'mech-check-unavailable', location: 'Phase 1.5',
    claim: '声明面机械核验应可执行', actual: `脚本执行失败：${mechResult.error}`,
    fix_classification: 'MANUAL',
    fix_suggestion: '确认 verify_proposal_declarations.py 存在且可被 python 调用' });
} else if (mechResult && Array.isArray(mechResult.assertions)) {
  for (const a of mechResult.assertions) {
    if (!a.violations || a.violations.length === 0) continue;
    mechFindings.push({ dimension: MECH_DIM[(a.assertion || '').slice(0, 2)] || 'D4',
      severity: 'CRITICAL', category: 'declaration-surface-mismatch',
      location: '§2 / §3 / §6', claim: `${a.assertion} 应通过`,
      actual: `缺 ${a.violations.length} 项：${a.violations.join(', ')}`,
      fix_classification: 'MANUAL',
      fix_suggestion: '补全对应声明面（回滚行 / §2 变更总览行 / 移出「不改动」段）——口径须由撰写者决定，不做自动修复' });
  }
  // 无「不改动」段 ⇒ A3 空过：显式登记为 INFO，避免「3/3 通过」被误读为全覆盖
  if (mechResult.nochange_section_present === false) {
    mechFindings.push({ dimension: 'D4', severity: 'INFO',
      category: 'vacuous-assertion', location: 'Phase 1.5 / A3',
      claim: 'A3（FM-30）已核验', actual: '方案无「不改动」段 ⇒ A3 空过（vacuous pass），该维未实际覆盖',
      fix_classification: 'MANUAL',
      fix_suggestion: '无需修复；仅提示勿把「3/3 通过」读作三断言均有实质约束' });
  }
} else {
  // 非 error 也非 assertions：schema 空对象或输出畸变——必须显式报警，不能静默 0 findings
  mechFindings.push({ dimension: 'D1', severity: 'WARNING',
    category: 'mech-output-malformed', location: 'Phase 1.5',
    claim: '机械核验应返回 assertions 数组', actual: '返回既无 error 也无 assertions 的结果',
    fix_classification: 'MANUAL',
    fix_suggestion: '复核脚本输出契约（--json 应含 assertions 数组）' });
}
log(`Mech: ${mechFindings.length} 项声明面 finding`);

// ── Phase 2: Audit D1–D7 (pipeline — dimensions run in parallel) ───
phase('Audit D1-D7');

const dimensions = [
  {
    key: 'D1', label: 'paths',
    prompt: (ctx) =>
      `${D1_RULES}\n\n` +
      `Verify EVERY file path reference in the proposal:\n${JSON.stringify(ctx.path_refs, null, 2)}\n\n` +
      `For each FAIL: record the claimed path, actual state (not_found/typo/old_arch), and the correct path if found via Glob.\n\n` +
      `Also check the proposal's own self-references: does the proposal cite its own related[] files correctly?`,
    schema: FINDING_SCHEMA
  },
  {
    key: 'D2', label: 'counts',
    prompt: (ctx) =>
      `${D2_RULES}\n\n` +
      `Verify EVERY numeric claim in the proposal:\n${JSON.stringify(ctx.numeric_claims, null, 2)}\n\n` +
      `Also check: does the proposal say "N categories of problems" matching the actual table row count?`,
    schema: FINDING_SCHEMA
  },
  {
    key: 'D3', label: 'indices',
    prompt: (ctx) =>
      `${D3_RULES}\n\n` +
      `New facilities declared:\n${JSON.stringify(ctx.new_facilities, null, 2)}\n\n` +
      `Index facilities referenced:\n${JSON.stringify(ctx.index_refs, null, 2)}\n\n` +
      `Check registration for each new facility. Also check: is the proposal itself registered in proposals/index.md and proposals/_catalog.md?`,
    schema: FINDING_SCHEMA
  },
  {
    key: 'D4', label: 'logic',
    prompt: (ctx) =>
      `${D4_RULES}\n\n` +
      `The proposal's logic chain:\n${JSON.stringify(ctx.logic_chain, null, 2)}\n\n` +
      `Proposal status: ${readResult.proposal_status}. Proposal stem: ${readResult.proposal_stem}.`,
    schema: FINDING_SCHEMA
  }
];

// D5-D7 only for L2+
if (isL2Plus) {
  dimensions.push(
    {
      key: 'D5', label: 'registration',
      prompt: (ctx) =>
        `${D5_RULES}\n\n` +
        `New facilities declared:\n${JSON.stringify(ctx.new_facilities, null, 2)}\n\n` +
        `Check registration completeness for EACH. Check: do the proposal's registration claims cover all required locations?`,
      schema: FINDING_SCHEMA
    },
    {
      key: 'D6', label: 'destructiveness',
      prompt: (ctx) => {
        let prompt = `${D6_RULES}\n\n` +
          `Modified existing files:\n${JSON.stringify(ctx.modified_files, null, 2)}\n\n`;
        if (isI2Plus && ctx.transitive_refs && ctx.transitive_refs.length > 0) {
          prompt += `🆕 I${impact[1]} transitive references (pre-collected by Read phase — use directly, do NOT re-grep):\n` +
            `${JSON.stringify(ctx.transitive_refs, null, 2)}\n\n` +
            `For each transitive_refs entry: verify the discovered_refs are real files that would be affected. ` +
            `Cross-check: does the proposal's modified_files list cover all transitive impact files? ` +
            `If not → CRITICAL: the proposal underestimates its blast radius.\n\n`;
        }
        prompt += `New facilities:\n${JSON.stringify(ctx.new_facilities, null, 2)}\n\n` +
          `The rollback section of the proposal (if it exists) — NOTE: 回滚表对 §3 目标集的覆盖已由 Phase 1.5 机械核验（断言 A1），此处**只判断语义层**（回滚命令是否正确/可执行、口径是否合理），勿重复计数核对。Original instruction follows — verify it covers all new files.`;
        return prompt;
      },
      schema: FINDING_SCHEMA
    },
    {
      key: 'D7', label: 'reuse',
      prompt: (ctx) => {
        let prompt = `${D7_RULES}\n\n` +
          `New facilities the proposal wants to create:\n${JSON.stringify(ctx.new_facilities, null, 2)}\n\n`;
        if (isI2Plus && ctx.transitive_refs && ctx.transitive_refs.length > 0) {
          prompt += `🆕 I${impact[1]} transitive impact data (pre-collected by Read phase):\n` +
            `${JSON.stringify(ctx.transitive_refs, null, 2)}\n\n` +
            `Use this to verify D7 point 3 (chain template awareness): each modified file's transitive_refs reveals ` +
            `which workflows/chains/templates reference it. Flag any workflow in transitive_refs.discovered_refs ` +
            `whose name suggests it falls into a chain template trigger domain that the proposal doesn't declare.\n\n`;
        }
        if (isI3 && ctx.chain_impacts && ctx.chain_impacts.length > 0) {
          prompt += `🆕 I3 chain impact analysis (pre-collected by Read phase):\n` +
            `${JSON.stringify(ctx.chain_impacts, null, 2)}\n\n` +
            `These are the chain templates whose trigger domains are affected by this proposal. ` +
            `For each: verify the proposal declares the chain impact or provides a reason for not declaring it. ` +
            `If the proposal modifies a workflow that is a step in an affected chain → CRITICAL.\n\n`;
        }
        prompt += `Check all 6 points from the D7 rules above.`;
        return prompt;
      },
      schema: FINDING_SCHEMA
    }
  );
}

// Run all dimensions in pipeline — each completes independently, no barrier
const dimResults = await pipeline(
  dimensions,
  (dim) => agent(dim.prompt(readResult), { label: `audit:${dim.key}`, phase: 'Audit D1-D7', schema: dim.schema })
);

// ── Phase 3: Synthesize ──
phase('Synthesize');

// dimension 声明在 FINDING_SCHEMA 外层（agent 返回 {dimension, findings[]}），
// 故扁平化时须把外层 dimension 注入每条 finding——否则 findings_by_dimension 恒为 0。
// mechFindings 在 Phase 1.5 声明（同文件同作用域），此处并入以纳入分维统计。
const allFindings = dimResults.filter(Boolean).flatMap(r =>
  (r.findings || []).map(f => ({ ...f, dimension: f.dimension || r.dimension }))
).concat(mechFindings);
const criticals = allFindings.filter(f => f.severity === 'CRITICAL');
const warnings = allFindings.filter(f => f.severity === 'WARNING');
const infos = allFindings.filter(f => f.severity === 'INFO');
const autoFix = allFindings.filter(f => f.fix_classification === 'AUTO_FIX');
const semi = allFindings.filter(f => f.fix_classification === 'SEMI');
const manual = allFindings.filter(f => f.fix_classification === 'MANUAL');

log(`${allFindings.length} total findings: ${criticals.length}C / ${warnings.length}W / ${infos.length}I`);
log(`Fix classification: ${autoFix.length} AUTO_FIX / ${semi.length} SEMI / ${manual.length} MANUAL`);

const proposalStem = readResult.proposal_stem;
const proposalDate = readResult.proposal_date || args.batchDate || 'unknown-date';
const auditDir = `${PROJECT_ROOT}/proposals/_audit/${proposalDate}`;

const report = {
  proposal_path: proposalPath,
  proposal_stem: proposalStem,
  audit_depth: depth,
  audit_impact: impact,
  audit_date: args.batchDate || 'unknown',
  dimensions_executed: dimensions.map(d => d.key),
  summary: {
    total: allFindings.length,
    critical: criticals.length,
    warning: warnings.length,
    info: infos.length,
    auto_fix: autoFix.length,
    semi: semi.length,
    manual: manual.length
  },
  findings_by_dimension: {},
  all_findings: allFindings
};

// Group findings by dimension (use finding.dimension field — avoids IPC reference-identity bug)
for (const dimKey of dimensions.map(d => d.key)) {
  const dimFindings = allFindings.filter(f => f.dimension === dimKey);
  report.findings_by_dimension[dimKey] = {
    count: dimFindings.length,
    critical: dimFindings.filter(f => f.severity === 'CRITICAL').length,
    warning: dimFindings.filter(f => f.severity === 'WARNING').length,
    info: dimFindings.filter(f => f.severity === 'INFO').length
  };
}

// Write JSON report via agent (Workflow sandbox has no filesystem access)
const writeResult = await agent(
  `Write the following content to ${auditDir}/${proposalStem}_audit.json:\n\n` +
  `\`\`\`json\n${JSON.stringify(report, null, 2)}\n\`\`\`\n\n` +
  `First ensure the directory ${auditDir} exists (create it if needed). Then write the file.\n\n` +
  `Also write a human-readable Markdown audit report to ${auditDir}/${proposalStem}_audit.md with:\n` +
  `- Header: proposal name, audit date, depth, dimensions executed\n` +
  `- Summary section: total findings breakdown\n` +
  `- Per-dimension sections: each finding with severity, location, claim, actual, fix suggestion\n` +
  `- AUTO_FIX section: list all auto-fixable items\n` +
  `- Next steps: "Run /proposal-audit-fix to auto-fix ${autoFix.length} items, then manually review ${semi.length} SEMI + ${manual.length} MANUAL items."`,
  { label: 'write-report', phase: 'Synthesize' }
);

log(`Audit report written to ${auditDir}/${proposalStem}_audit.md + _audit.json`);

return {
  status: 'COMPLETED',
  proposal_stem: proposalStem,
  audit_dir: auditDir,
  summary: report.summary,
  auto_fix_count: autoFix.length,
  semi_count: semi.length,
  manual_count: manual.length
};
