---
id: REVIEW-2026-06-09-backlog-board-restoration-owner-format-gate
type: review
audience: owner
status: completed
signal: pass
score: 100
priority: P0
category: governance
owner: lead-engineer
agent: codex
date: 2026-06-09
tags: [backlog, owner-brief, action-board, format-gate, reporting]
references:
  - BACKLOG-BOARD.md
  - BACKLOG.md
  - STATUS.md
  - scripts/backlog_board.py
  - scripts/owner_doc_format_gate.py
  - src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md
  - src/agent_runtime/templates/project/agents/project/SKILL-GOVERNANCE.md
---

# Backlog Board Restoration and Owner Format Gate

## Bottom Line

- Summary: restored prior backlog decision-board style with clearer `Action / Ask / Review / Later / Done` lanes.
- Status: completed.
- Gate: `BACKLOG-BOARD.md` passes Owner document format gate.

## Signal

- Issue: prior backlog output drifted from decision-oriented Owner brief into a flatter task list.
- Cause: style rules were prose-only; generator and gate did not enforce `Bottom Line / Signal / Insight / Decision`.
- Data gap: nonstandard TASK frontmatter caused task omission risk.

## Insight

- Former model: `ACT / REVIEW / ASK / DEFER` decision board.
- Restored model: `Action / Review / Ask / Later / Done` for clearer Owner reading.
- Added fields: difficulty, cost hours, cost tokens, value, importance, team, agent, score, decision, summary.
- Parser fix: accepts standard YAML, header-like metadata, and missing closing frontmatter delimiter.

## Decision

- Decision: use `BACKLOG-BOARD.md` as Owner-facing backlog view.
- Rule: preserve `Bottom Line / Signal / Insight / Decision` before tables.
- Rule: all Owner-facing backlog/review/report docs need concise bullets, metadata, tags, actions, risks, next steps.
- Rule: generated boards must pass `scripts/owner_doc_format_gate.py` before sharing.

## Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Generate all-task backlog board | lead-engineer | codex | `BACKLOG-BOARD.md`, `tasks=25` |
| Done | Restore decision-board sections | lead-engineer | codex | `Bottom Line / Signal / Insight / Decision` |
| Done | Add Owner doc format gate | lead-engineer | codex | `scripts/owner_doc_format_gate.py` |
| Done | Add template enforcement | agent-runtime-core | codex | `REPORTING-FORMAT.md`, `SKILL-GOVERNANCE.md` |

## Risks / Blockers

- Risk: old task files may keep malformed metadata.
- Risk: future manual report edits may bypass generated format.
- Blocker: none for current board generation.

## Next Steps

- Run `python scripts/backlog_board.py --write` after task metadata changes.
- Run `python scripts/owner_doc_format_gate.py BACKLOG-BOARD.md` before Owner sharing.
- Promote repeated inferred fields into explicit task frontmatter.

## Tags / References

- tags: backlog, decision-board, owner-brief, action-board, format-gate
- references: `BACKLOG-BOARD.md`, `scripts/backlog_board.py`, `scripts/owner_doc_format_gate.py`

## Enforcement Update - Hook / CI / Release Gate

### Bottom Line

- Summary: Owner document format gate now runs in hook, CI, and release-preflight paths.
- Status: completed.
- Release proof: clean bundle preflight passed with `findings=0`.

### Signal

- Hook: `.githooks/pre-commit` runs `scripts/owner_doc_format_gate.py --manifest owner-docs.yml`.
- CI: `.github/workflows/test.yml` runs the same manifest gate.
- Release: `release-preflight` includes `owner-doc-format` as a blocking check.
- Source truth: `owner-docs.yml` is the shared manifest.

### Insight

- Cause addressed: prose-only reporting rules are no longer enough to pass release.
- Enforcement path: local hook catches early; CI catches PR/push drift; release-preflight blocks final drift.
- Template path: new projects receive `owner-docs.yml`, `.githooks/pre-commit`, and `.github/workflows/owner-doc-format.yml`.

### Decision

- Decision: Owner-facing docs listed in `owner-docs.yml` must pass the executable format contract.
- Decision: clean bundle release is the authoritative release-preflight path.
- Decision: `.codex/` hook config is intentionally not added because public sanitizer forbids `.codex/` paths.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add local hook gate | lead-engineer | codex | `.githooks/pre-commit` |
| Done | Add CI gate | cicd-engineer | codex | `.github/workflows/test.yml` |
| Done | Add release-preflight gate | agent-runtime-core | codex | `owner-doc-format` check |
| Done | Add manifest SSoT | doc-steward | codex | `owner-docs.yml` |
| Done | Add template propagation | agent-runtime-core | codex | `src/agent_runtime/templates/project/.github/workflows/owner-doc-format.yml` |
| Done | Refresh fixture lock | cicd-engineer | codex | `tests/fixtures/host/agent_runtime.lock.json` |

### Risks / Blockers

- Risk: docs not listed in `owner-docs.yml` are not yet hard-gated.
- Risk: legacy docs may need gradual migration before adding them to the manifest.
- Blocker: none for clean-bundle release path.

### Next Steps

- Add additional Owner-facing reports to `owner-docs.yml` after each report is migrated to the executive brief format.
- Keep hook/CI/release gate aligned by using the manifest only, not ad hoc path lists.

### Tags / References

- tags: owner-doc-format, hook, ci, release-preflight, manifest, executive-brief
- references: `.githooks/pre-commit`, `.github/workflows/test.yml`, `owner-docs.yml`, `src/agent_runtime/release_preflight.py`


## Enforcement Update - Hooks and State Machines

### Bottom Line

- Summary: `.codex/hooks.json`, Git hook, CI, release-preflight now share Owner governance enforcement.
- Signal: pass.
- Score: 100.
- Release proof: clean bundle preflight passed with `findings=0`.

### Signal

| Layer | State | Signal | Score | Evidence |
| --- | --- | --- | --- | --- |
| Codex hook config | enforced | pass | 100 | `.codex/hooks.json` |
| Git hook | enforced | pass | 100 | `.githooks/pre-commit`, `core.hooksPath=.githooks` |
| CI | enforced | pass | 100 | `.github/workflows/test.yml` |
| Release gate | enforced | pass | 100 | `owner-doc-format`, `state-machines` checks |
| State SSoT | enforced | pass | 100 | `agents/project/STATE-MACHINES.yml` |

### Insight

- Hook config and hook are connected only when the runner reads that config.
- Git hook required repo-local `core.hooksPath`; now configured.
- `.codex/hooks.json` is included as a sanitized public-safe exception limited to that one file.
- State labels are now `pass/watch/block`; score carries severity and sorting power.

### Decision

- Decision: use `scripts/owner_governance_gate.py` as the shared hook/CI/release governance entrypoint.
- Decision: use `agents/project/STATE-MACHINES.yml` as the canonical state-machine SSoT.
- Decision: new state dimensions include cycle, task, agent job, gate, review, release, owner decision, hook enforcement, CI, document, and shared health signal.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add Codex hook config | cicd-engineer | codex | `.codex/hooks.json` |
| Done | Enforce Git hook | cicd-engineer | codex | `.githooks/pre-commit`, `git config core.hooksPath .githooks` |
| Done | Add state-machine SSoT | agent-runtime-core | codex | `agents/project/STATE-MACHINES.yml` |
| Done | Add schema and example | doc-steward | codex | `schemas/state-machines.schema.json`, `STATE-MACHINES.example.yml` |
| Done | Add release-preflight check | agent-runtime-core | codex | `state-machines` preflight check |
| Done | Add template propagation | agent-runtime-core | codex | template `.codex`, `.githooks`, schema, example, scripts |

### Risks / Blockers

- Risk: Codex hook behavior depends on the runtime honoring `.codex/hooks.json`.
- Risk: Git hooks can still be bypassed with `--no-verify`; CI and release-preflight remain the non-bypass repo gates.
- Blocker: none for clean-bundle release path.

### Next Steps

- Add any newly migrated Owner-facing report to `owner-docs.yml`.
- When adding a new lifecycle domain, extend `STATE-MACHINES.yml` first, then code/docs.

### Tags / References

- tags: hooks, codex, git-hooks, state-machine, pass-watch-block, release-preflight
- references: `.codex/hooks.json`, `.githooks/pre-commit`, `agents/project/STATE-MACHINES.yml`, `scripts/owner_governance_gate.py`
