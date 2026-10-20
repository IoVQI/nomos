export const meta = {
  name: 'proposal-audit-fix',
  description: 'Auto-fix AUTO_FIX findings from a proposal-audit-check report. Only fixes AUTO_FIX items (paths, counts, indices) — SEMI and MANUAL items are left for human decision.',
  phases: [
    { title: 'Classify', detail: 'Parse audit JSON, extract AUTO_FIX items only' },
    { title: 'AutoFix', detail: 'pipeline() apply each AUTO_FIX fix to the proposal file or index files' },
    { title: 'Verify', detail: 'Re-run proposal-audit-check --depth l1, confirm 0 CRITICAL' },
  ],
  cost: { agents: { min: 3, max: 12 }, mandatory: false,
          notes: 'Classify 1 + AutoFix pipeline(依 AUTO_FIX 项数) + Verify 1' },
};

// 原 `const PROJECT_ROOT = '.'` 已删除：本文件从未引用它（死常量），
// 且硬编码绝对路径会在第二台机（仓库不在 D:）误导读者。本脚本全部路径来自 args。

// ── Parse args ──
const auditReportPath = args?.auditReportPath || null;
if (!auditReportPath) {
  throw new Error('args.auditReportPath is required. Pass the path to the _audit.json file from proposal-audit-check.');
}

// ── Phase 1: Classify ──
phase('Classify');

const classifyResult = await agent(
  `Read the audit report JSON at ${auditReportPath}.\n\n` +
  `Extract ALL findings where fix_classification === "AUTO_FIX".\n` +
  `For each, extract: dimension, category, location, claim, actual, fix_suggestion, target_file, old_string, new_string.\n\n` +
  `Group AUTO_FIX items by target_file so we can batch edits to the same file.\n\n` +
  `Also read the proposal file (path in the report's proposal_path field) to get current content for editing.`,
  { label: 'classify', phase: 'Classify', schema: {
    type: 'object',
    properties: {
      auto_fix_items: { type: 'array', items: { type: 'object', properties: {
        dimension: { type: 'string' },
        category: { type: 'string' },
        location: { type: 'string' },
        claim: { type: 'string' },
        actual: { type: 'string' },
        fix_suggestion: { type: 'string' },
        target_file: { type: 'string' },
        old_string: { type: 'string' },
        new_string: { type: 'string' }
      }, required: ['dimension', 'category', 'location', 'target_file', 'old_string', 'new_string'] }},
      by_target_file: { type: 'object' },
      total_auto_fix: { type: 'number' }
    }, required: ['auto_fix_items', 'total_auto_fix']
  }}
);

if (!classifyResult || classifyResult.total_auto_fix === 0) {
  log('No AUTO_FIX items found — nothing to fix.');
  return { status: 'COMPLETED', fixed: 0 };
}

const autoFixItems = classifyResult.auto_fix_items || [];
log(`${autoFixItems.length} AUTO_FIX items to process across ${Object.keys(classifyResult.by_target_file || {}).length} target files.`);

// ── Phase 2: AutoFix ──
phase('AutoFix');

const targetFiles = Object.keys(classifyResult.by_target_file || {});
if (targetFiles.length === 0) {
  const fixResults = await pipeline(
    autoFixItems,
    (item) => agent(
      `Apply this AUTO_FIX to ${item.target_file}:\n\n` +
      `Location: ${item.location}\nProblem: ${item.claim} → should be ${item.actual}\nFix: ${item.fix_suggestion}\n\n` +
      `OLD STRING:\n\`\`\`\n${item.old_string}\n\`\`\`\nNEW STRING:\n\`\`\`\n${item.new_string}\n\`\`\`\n\n` +
      `Use the Edit tool with old_string and new_string. First Read the target file to verify old_string matches.`,
      { label: `fix:${item.dimension}:${item.category}`, phase: 'AutoFix' }
    )
  );
  const succeeded = fixResults.filter(Boolean).length;
  log(`Applied ${succeeded}/${autoFixItems.length} fixes.`);
} else {
  const fixResults = await pipeline(
    targetFiles,
    (targetFile) => agent(
      `Apply ALL AUTO_FIX edits to ${targetFile}.\n\n` +
      `Items to fix in this file:\n${JSON.stringify(classifyResult.by_target_file[targetFile], null, 2)}\n\n` +
      `For each: Read file, verify old_string, Edit to replace with new_string. Return count of applied/skipped fixes.`,
      { label: `fix-file:${targetFile.replace(/^.*\//, '')}`, phase: 'AutoFix', schema: {
        type: 'object', properties: {
          file: { type: 'string' }, applied: { type: 'number' }, skipped: { type: 'number' },
          skipped_reasons: { type: 'array', items: { type: 'string' } }
        }, required: ['file', 'applied', 'skipped']
      }}
    )
  );
  const totalApplied = fixResults.filter(Boolean).reduce((sum, r) => sum + (r.applied || 0), 0);
  log(`Applied ${totalApplied} fixes across ${targetFiles.length} files.`);
}

// ── Phase 3: Verify ──
phase('Verify');

const proposalPath = args?.proposalPath || null;
if (proposalPath) {
  const verifyResult = await agent(
    `Quick L1 re-audit on ${proposalPath}. Check: D1 path existence, D2 count consistency, D3 index completeness.\n` +
    `Return { all_clear, remaining_critical, remaining_warning, remaining_issues[] }.\n` +
    `"all_clear" = 0 CRITICAL findings remain.`,
    { label: 'verify', phase: 'Verify', schema: {
      type: 'object', properties: {
        all_clear: { type: 'boolean' }, remaining_critical: { type: 'number' },
        remaining_warning: { type: 'number' }, remaining_issues: { type: 'array', items: { type: 'string' } }
      }, required: ['all_clear', 'remaining_critical']
    }}
  );
  if (verifyResult && verifyResult.all_clear) {
    log('✅ Verification passed — 0 CRITICAL findings remain.');
  } else {
    log(`⚠️ ${verifyResult?.remaining_critical || '?'} CRITICAL findings remain. Manual review needed.`);
  }
}

log('🔴 CHAIN_COMPLETE');
return { status: 'COMPLETED', fixed: autoFixItems.length, proposal_path: proposalPath };
