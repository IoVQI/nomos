# Contributing / 贡献指南

感谢你愿意改进 Nomos。本项目是**文档与治理骨架**，变更的可维护性比变更的数量更重要。

Thanks for improving Nomos. This is a **documentation and governance skeleton**; maintainability
matters more than the number of changes.

---

## 中文

### 开始之前

1. 先读 [`CLAUDE.md`](CLAUDE.md) 与 [`project/standards/`](project/standards/index.md)。
2. 涉及架构增量的变更，先走提案：`proposals/YYYY/MM/DD/`，状态为「待确认」时不得执行。
3. 并行工作时，先在 `coordination/claims/` 声明写入域；每个文件任何时刻只有一个写者。

### 提交规范

- 提交信息格式：`type(scope): 中文摘要`，≤ 72 字符。
- `type`：`docs` / `fix` / `feat` / `refactor` / `chore`。
- 一次提交只做一件事；不要混入无关格式化。
- 不要提交：凭据、真实地址、个人路径、日志、缓存、构建产物。

### 校验闸门

```bash
pip install pre-commit pyyaml
pre-commit install
pre-commit run --all-files
python ai_system/validation/check_workflows.py --quiet
```

PR 必须通过 CI。判断层文件（`project/standards/`）不要求也不应配脚本。

### 新增工作流

按 [`ai_system/workflows/workflow_creation_workflow.md`](ai_system/workflows/workflow_creation_workflow.md)
创建文件，并同步 `workflow_index.md`；随后运行注册表校验。

### 发布

发布由维护者从私有开发仓通过白名单构建生成，发布仓不接受直接修改。
安全问题请见 [`SECURITY.md`](SECURITY.md)。

---

## English

### Before you start

1. Read [`CLAUDE.md`](CLAUDE.md) and [`project/standards/`](project/standards/index.md).
2. Architectural changes require a proposal under `proposals/YYYY/MM/DD/`. A proposal marked
   "pending" must not be executed.
3. When working in parallel, declare your write domain under `coordination/claims/`.
   Each file has exactly one writer at any time.

### Commit conventions

- Commit subject: `type(scope): summary`, at most 72 characters.
- `type`: `docs` / `fix` / `feat` / `refactor` / `chore`.
- One logical change per commit; avoid unrelated reformatting.
- Never commit credentials, real addresses, personal paths, logs, caches, or build artifacts.

### Gates

```bash
pip install pre-commit pyyaml
pre-commit install
pre-commit run --all-files
python ai_system/validation/check_workflows.py --quiet
```

Pull requests must pass CI. Judgment-layer files (`project/standards/`) are intentionally unscripted.

### Adding a workflow

Follow [`ai_system/workflows/workflow_creation_workflow.md`](ai_system/workflows/workflow_creation_workflow.md),
register it in `workflow_index.md`, then run the registry check.

### Releases

Releases are produced by the maintainer from a private development repository through a
whitelist build. The public release repository does not accept direct edits.
For security issues, see [`SECURITY.md`](SECURITY.md).
