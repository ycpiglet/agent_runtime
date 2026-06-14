---
id: TASK-AR-531
display_id: TASK-AR-531
task_uid: 270755af-d866-4b1c-9dc1-8c729f9aee7f
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5500
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - host-fit
  - packaging
  - candidate
---

# TASK-AR-531 - Host-fit gap closures (deep-adoption friction)

## Goal

- Close the host-fit gaps that block deep adoption of agent_runtime as a reusable platform, surfaced by autofolio's v0.2.0 dogfooding. (GH #121 §3)

## Scope

1. **Wheel packaging of dotfiles** — `templates/project/` dot-files (`.gitattributes`, `.githooks/`, `.github/`, `.codex/`) are excluded from the built wheel (setuptools default), so `pip install` + `sync` never delivers the wiring even though the referenced scripts ship. Fix via `MANIFEST.in` / `force-include`, or make sync compare against a source manifest. (Cross-check against AR-511 .gitattributes work to avoid duplication.)
2. **Host-context read-location** — no fixed convention for where a host puts purpose/domain/safety-constraints/role-mapping so the framework reads it; hosts either edit templates (conflict) or scatter into files the framework ignores. Define a fixed *unmanaged* read-location convention.
3. **work_cli / scaffolder** — adopting v1 work items (WORK-SCHEMA) requires hand-filling 12 mandatory fields + 4 layers; an item-creation CLI is missing.
4. **Status vocabulary localization** — v1 status is an English enum (planned/blocked/...); hosts localize (Korean), forcing a dual validation regime. Add status alias/localization support.

## Acceptance Criteria — candidate

- Adoption + per-gap sequencing is decided by the TASK-AR-527 deliberation (votes = priority signal); this file pre-registers the four gaps so none is lost.

## Acceptance Criteria

- Each adopted gap has a concrete fix with evidence; deferred gaps carry a recorded reason.
- Wheel fix is verified by inspecting built wheel contents (dotfiles present).

## Evidence Targets

- `MANIFEST.in` / packaging config; status alias map; scaffolder CLI; read-location convention doc.
- Host counterpart: autofolio `docs/agent_runtime_feedback.md` (§1, §7), `docs/AGENT_RUNTIME_RELATIONSHIP.md`.
- Source: GH ycpiglet/agent_runtime#121.

## Deliberation Verdict (2026-06-14)

- ACCEPT (split) — `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.
- **#1 wheel-dotfile packaging — P1, do now.** CONFIRMED live blocker by empirical wheel build: 0 of 4 template dotfiles (`.gitattributes`, `.githooks/`, `.github/`, `.codex/`) ship (setuptools silently drops dot-prefixed paths under the `templates/project/**/*` glob; no MANIFEST.in). Fix via explicit dot-path enumeration or `MANIFEST.in` + `include-package-data`; gate on a built-wheel content assertion so a future build can't silently drop them again. Reuse AR-511, do not re-author.
- **#4 status localization — P3**, alias-additive (English enum stays canonical; Korean maps onto it).
- **#2 host-context read-location — doc-only** (substrate `unmanaged_paths` from `sync.unmanaged:` already exists in config.py).
- **#3 work_cli scaffolder — REJECTED.** `scripts/work.py` already is the scaffolder (`new`/`register` + required-field validation). Do not fund.
