# REVIEW-2026-06-08-agent-runtime-after-pass-1

## Purpose

This is a post-pass comparison against `REVIEW-2026-06-08-agent-runtime-baseline.md`.

It records what changed immediately in the template layer and what remains open.

## Baseline Summary (Before this pass)

- `PYTHONPATH=src pytest tests -q` passed (package-layer checks).
- `sanitize --check`, `publish-check --check`, `publish-bundle --check` had no package-level regressions.
- Runtime template execution was not self-contained (`orchestrator_safety_gate.py`, `pipeline.py`, `schemas/task.schema.json`, and role docs had gaps).
- ToolRunner command policy still broad (`python`/`py` path and mutable git commands reachable).
- Message claiming/race safety had no atomic lease primitive.
- Provider dependency contract not separated by extras.

## What was implemented in this pass

### 1) Template self-sufficiency restored
- Added `src/agent_runtime/templates/project/scripts/orchestrator_safety_gate.py`
- Added `src/agent_runtime/templates/project/scripts/pipeline.py`
- Added `src/agent_runtime/templates/project/schemas/task.schema.json`
- Added `src/agent_runtime/templates/project/agents/independent_auditor/AUDIT-GATE.md`
- Added `src/agent_runtime/templates/project/agents/independent_auditor/SAFETY-GATE.md`
- Added `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

### 2) Template smoke sanity in a clean host
- Created clean fixture host and ran:
  - `agent_runtime sync --root <host> --apply`
  - `agent_orchestrator.py --help`
  - `agent_worker.py --help`
  - `auto_runner.py --help`
  - `check_messages.py` (with required `agents/messages/*` folders)
- Result: command entrypoints execute without import/runtime errors.

### 3) Public-package checks back to clean
- Sanitize/product-publish gate checks were re-run and now return no findings.

## Evidence snapshot (current)

- `PYTHONPATH=src python -m pytest tests -q` → **94 passed**
- `python -m agent_runtime.cli sanitize --root . --check` → **findings=0**
- `python -m agent_runtime.cli publish-check --root . --check` → **findings=0**
- `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check` → **findings=0**
- `sync` dry run/`apply` on clean host: **156 template updates created** (including scripts + docs + schema)

## Compare this pass vs baseline

| Category | Baseline | After pass |
|---|---|---|
| Self-contained template runtime | major gap | **closed for import/schema path failures** |
| CI package checks (`sanitize`, `publish-check`, `publish-bundle`) | clean | **clean** |
| Runtime smoke for host template (sync + script entrypoints) | not covered | **covered; entrypoints execute** |
| ToolRunner command sandbox | open | **unchanged (still open)** |
| Message claim race safety | open | **unchanged (still open)** |
| Provider extras/lazy import | open | **unchanged (still open)** |

## What is still weak / needs next pass

- Harden `providers/agent_tools.py` command policy (block `python -c`, mutable git, pip/module install paths, etc.).
- Add atomic claim/lease queue for parallel workers.
- Implement optional dependency/extra contract and lazy provider loading.
- Add template-level and package-level regression tests for these two risk areas.
