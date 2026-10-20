# Nomos

**A governance skeleton for long-horizon human–AI collaboration** — treating workflow
definitions, validation gates, cross-session context, and proposal approval as
first-class infrastructure rather than after-the-fact documentation.

> 一套长期人机协作的治理骨架。 [中文](README.md)

This repository contains **no research content**. It provides structure, protocols, and
gates: fill the reserved slots with your own material, or delete what you do not need.

---

## Why it exists

The real failure mode of long-term work with AI is not an occasional wrong answer — it is
**the slow erosion of constraints**:

- agreements from last time are no longer remembered;
- a process is written down but nobody follows it;
- a rule exists, but nothing enforces it;
- sessions share no memory, so handoffs are improvised — and every retelling is a copy,
  and copies drift.

Nomos treats these as engineering problems: **turn agreements into files, attach gates to
files, and put gates in CI.** Judgment-layer guidance is explicitly marked as
"intentionally unscripted" rather than pretending to be mechanically verifiable.

---

## Research support: making the research process reproducible and transferable

Nomos **does not replace** your research tools — it does not search literature, run numerical
models, or draw figures. It governs the **discipline layer** of research: what each stage should
produce, where evidence lives, and how far a conclusion may be stated.

| Research stage | Facility | What it solves |
|---|---|---|
| Topic selection & scoping | [`project/standards/01`](project/standards/01_研究选题逻辑.md) + `Skill: proposal-gen` | Six-stage route: field survey → reproduction → candidate questions → systematic validation → pilot → problem statement; drop weak directions through real reproduction |
| Project execution | [`project/standards/02`](project/standards/02_课题推进.md) | Eight-stage frame: freeze the question → lock the baseline → minimal validation → full experiments → deep analysis → write in parallel → submission iterations |
| Literature work | `Skill: literature-review` | Four-part review body (background → synthesis → critique → references); A/B/C evidence grading against fabricated paraphrase; GB/T 7714 citations |
| Reproduction & figures | [`project/standards/03`](project/standards/03_复现绘图规范.md) | Input contracts, compute/plot separation, standard figure sets, unified style, default display windows |
| Experiment execution & records | [`project/standards/09`](project/standards/09_实验执行与记录准则.md) + [`coordination/`](coordination/README.md) | Six record questions (source of truth / protocol / scale / timing / artifacts / status), timing conventions, reproducibility criteria |
| Analysis & narrative | [`project/standards/04`](project/standards/04_研究故事线.md) | Nine-node storyline, evidence chain, conclusion boundaries, leverage of negative results |
| Reporting | [`project/standards/07`](project/standards/07_科研汇报展示准则.md) | Narrative arc, provenance marks, layout fidelity, and consistency of derived artifacts for decks / slides / PDFs |
| Credibility & boundaries | [`project/standards/10`](project/standards/10_研究可信度与边界陈述准则.md) | Self-referential baselines, no anchoring, no masking; boundary sentences name the mechanism instead of "there is uncertainty" |
| Proposals & changes | [`proposals/`](proposals/README.md) + `Skill: proposal-audit` | Design before execution; seven-dimension audit (paths / counts / indexes / logic / registration / destructive changes / reuse) |
| Cross-session & handoff | [`ai_system/context/`](ai_system/context/README.md) + `coordination/` | Context-recovery templates; parallel write-domain claims and serial handoff protocol |

A typical research line:

```text
topic → reproduce → pilot → records → analysis → storyline → reporting → submission
  01        01       01       09        02         04          07          02
```

**What it gives you**: after changing machines, sessions, or returning months later, you can still
answer *where the evidence for a conclusion is, how it was produced, and which conditions were not
validated*. **What it does not do**: judge scientific value or guarantee correctness — those stay in
the judgment layer and remain the researcher's responsibility.

---

## Repository layout

```text
nomos/
├── CLAUDE.md            ★ AI session conventions (loaded every session) — also the best tour
├── README.md              Chinese README
├── README.en.md           This file
├── VERSION                Single source of truth for the version
├── CHANGELOG.md           Keep a Changelog
├── .claude/               Claude Code facilities
│   ├── commands/          Slash commands (session close-out)
│   ├── skills/            Skill definitions: workflows exposed as callable entry points
│   ├── workflows/         JS dynamic workflows: deterministic multi-agent orchestration
│   └── settings.json      Permission allow / deny (hard-blocks irreversible git operations)
├── .github/workflows/     CI
├── ai_system/             AI engineering governance system
│   ├── index.md           Navigation entry
│   ├── workflows/         Workflow definitions + registry + usage guide
│   ├── context/           Cross-session context recovery (templates ship with the release)
│   ├── rules/             Coding / debugging rules
│   ├── prompts/           Prompt templates
│   ├── scripts/           Helper scripts (including reusable/)
│   ├── official_docs/     Optional local mirror of upstream docs (not distributed)
│   └── validation/        Validation gates
├── project/               Project-level living docs + intentionally empty directories
│   ├── index.md
│   ├── standards/         Research standards 01–10 (topic, execution, reproduction, narrative, reporting, credibility)
│   ├── ops/               Operations knowledge pattern (placeholders only; values stay local)
│   └── <empty dirs>       References / knowledge bases / lab / meeting notes, for your material
├── proposals/             Proposal workspace + audit reports
├── coordination/          Multi-session coordination (parallel claims + serial handoffs)
├── records/               Optional ledger (notes / reports / session summaries)
└── sandbox/               Sandbox (experiments / drafts / third-party ingestion)
```

### Intentionally empty directories

`project/references/`, `project/derivation_kb/`, `project/data_kb/`, `project/domain_kb/`,
`project/lab/`, `project/meeting_notes/`, and `project/research/` are deliberately empty.
They reserve path conventions for your own material; each contains a `README.md` explaining
its purpose. Delete any directory you do not need.

> The names (`derivation_kb`, `lab`, …) come from the skeleton's source project. They are
> placeholders — rename them freely, as long as you update the references.

---

## Quick start

```bash
# 1) Install git hooks (gates run automatically on commit)
pip install pre-commit pyyaml
pre-commit install

# 2) Run every gate manually
pre-commit run --all-files

# 3) Validate the workflow registry alone
python ai_system/validation/check_workflows.py --quiet
```

**Reading order**:

1. This file
2. [`CLAUDE.md`](CLAUDE.md) — full conventions, auto-loaded by AI sessions
3. [`ai_system/index.md`](ai_system/index.md) — governance system navigation
4. [`project/standards/index.md`](project/standards/index.md) — judgment-layer standards
5. [`coordination/claims/README.md`](coordination/claims/README.md) — multi-session rules
   (**read before editing shared files**)

---

## How the AI system works: three layers

| Layer | Location | Nature | When to use |
|---|---|---|---|
| **Workflow definition** | `ai_system/workflows/*.md` | Protocol: steps, gates, criteria | To understand *how* something should be done |
| **Skill** | `.claude/skills/*/SKILL.md` | Entry point: declares allowed tools, wraps a workflow as a command | To *initiate* an operation |
| **Dynamic workflow** | `.claude/workflows/*.js` | Execution: deterministic multi-agent orchestration (fan-out / verify / aggregate) | When a task needs parallel fan-out and convergence |

**Gates** (`ai_system/validation/*.py`) are the only mechanical criteria. They run in two
places: `.pre-commit-config.yaml` (local, on commit) and `.github/workflows/ci.yml` (remote,
on a clean clone). If documentation and scripts disagree, **the script wins**.

---

## Multi-session coordination

Sessions share no memory; **the filesystem is the only medium**.

| Directory | Scenario |
|---|---|
| [`coordination/claims/`](coordination/claims/README.md) | **Parallel**: declare your write domain in `claims/<slug>.md` as the first step |
| [`coordination/handoff/`](coordination/handoff/README.md) | **Serial**: handoff prompts, written for a human to paste into the next session |

The core rule: **every file has exactly one writer at any moment.**

---

## Provenance

This skeleton was distilled from an earlier research project: **only governance facilities and
infrastructure were kept; no history, data, literature, or third-party content is included.**
The public repository history is a release ledger, not a development history.

Path names retained in the empty directories come from the source project and are placeholders.

---

## License

[MIT](LICENSE)
