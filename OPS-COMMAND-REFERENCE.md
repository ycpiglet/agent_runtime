---
type: owner_brief
id: OPS-COMMAND-REFERENCE
audience: owner
status: pass
signal: pass
score: 90
priority: P1
tags: [ops, ergonomics, commands, skills, gates, 500-series, how-to-use]
updated_at: 2026-06-13T14:34:57+09:00
---

# Ops Command Reference

The single "how do I use this" surface for the 500-series + ops-ergonomics
assets. Every new command, skill, gate, tool, and hook maps here to: purpose,
exact invocation, automation class (auto / on-demand / Owner-gated), and the
W0-W6 lifecycle stage it serves.

## Bottom Line

- Summary: the 500-series shipped parallel-wave dispatch, a merge queue, SCM
  hygiene, in-flight overlay, work-item analytics, attribution + verification
  freshness enforcement, release cadence detection, and a session-start
  dashboard. This reference is the one place that says how to invoke each one.
- Status: tools, gates, and `work.py` subcommands are live and invocable today.
  The SessionStart dashboard hook (`session_dashboard.py`, TASK-AR-523) and the
  five trigger-skills (TASK-AR-524) land from sibling tasks merging around the
  same time; their registry entries reference post-merge paths.
- Boundary: every gate is non-mutating; `merge_queue process`, `scm_steward
  clean`, release tag/publish, and host `update --apply` stay Owner-gated.

## Signal

signal: pass

| Asset class | Count | Automation | Invocation surface |
| --- | --- | --- | --- |
| Session dashboard | 1 | auto (SessionStart) | `.codex/hooks.json` hook |
| `work.py` subcommands | 6 | on-demand | `python scripts/work.py <cmd>` |
| Ops tools | 4 | on-demand / Owner-gated | `python scripts/<tool>.py` |
| Update notify | 1 | auto (SessionStart) | `update-notify` hook |
| New gates | 7 | auto (gate chain) | `python scripts/<gate>.py --check` |
| Plan assumption gate | 1 | auto (gate chain) | `python scripts/plan_assumption_gate.py --check` |
| New skills | 6 | trigger-based | trigger phrase -> Skill tool |
| Existing skills | 1 | trigger-based | trigger phrase -> Skill tool |

## Command Reference

### Session start (auto, W0)

| Command | Purpose | How to invoke | Class | Stage |
| --- | --- | --- | --- | --- |
| `session_dashboard` | Aggregate active claims/worktrees, inflight overlay summary, update-notify, and SCM steward report into one read-only panel at session start | `python scripts/session_dashboard.py` (auto via `.codex/hooks.json` SessionStart; always exit 0, cached) | auto | W0 |
| `update-notify` | Compare upstream latest release tag vs pinned `agent_runtime.yml` ref; print one non-blocking notice when a newer release exists | `python -m agent_runtime.cli update-notify` (auto via SessionStart `update_notify_hook.cmd`); manual: `--no-cache --verbose` | auto | W0 |

### Work-item analytics — `work.py` (on-demand, W0-W6)

| Command | Purpose | How to invoke | Class | Stage |
| --- | --- | --- | --- | --- |
| `work status` | Show status of an initiative/taskset/task/unit work item | `python scripts/work.py status <id>` | on-demand | W0-W6 |
| `work stats` | Aggregate v1 Work Item metadata across the backlog without mutating files | `python scripts/work.py stats` | on-demand | W0/W5 |
| `work view` | Save, list, and run reusable stats queries (Work Explorer) | `python scripts/work.py view save|list|run <name>` | on-demand | W0/W5 |
| `work new` | Create work records from structured JSON input (alias: `register`) | `python scripts/work.py new --input <json>` | on-demand | W0 |
| `work verify` | Run a work item's verification commands and write evidence | `python scripts/work.py verify <id>` | on-demand | W4 |
| `work close` | Close a work item after passed verification evidence | `python scripts/work.py close <id>` | Owner-gated | W5 |

### Ops tools (on-demand, W2-W5)

| Command | Purpose | How to invoke | Class | Stage |
| --- | --- | --- | --- | --- |
| `wave_dispatcher` | Plan/dispatch parallel waves of task units from a taskset; issue claim+worktree per wave | `python scripts/wave_dispatcher.py --taskset <id> --plan` then `--dispatch` (`--status` for progress) | on-demand | W2 |
| `merge_queue` | Serialize branch integration: enqueue branches, then process them against the base | `python scripts/merge_queue.py enqueue --branch <b> --task-id <id>`; `list`; `process --dry-run` (mutating `process` Owner-gated) | on-demand / Owner-gated | W5 |
| `scm_steward` | Detect and (after approval) clean SCM debt: zombie worktrees, stale branches/claims/stashes, aging PRs/issues | `python scripts/scm_steward.py report` (read-only); `clean` and `pr-open` Owner-gated | on-demand / Owner-gated | W5/W6 |
| `inflight_overlay` | Show divergence between active branches and base to surface in-flight collision risk | `python scripts/inflight_overlay.py --summary` (or `--json`) | on-demand | W2/W5 |

### Gates (auto, gate chain — W1-W5)

| Gate | Purpose | How to invoke | Class | Stage |
| --- | --- | --- | --- | --- |
| `footprint_conflict_gate` | Verify active claims have non-overlapping write footprints (pairwise) | `python scripts/footprint_conflict_gate.py --check` | auto | W2 |
| `worktree_lifecycle_gate` | Enforce worktree lifecycle hygiene (creation, claim binding, cleanup) | `python scripts/worktree_lifecycle_gate.py --check` (report) / `--clean` (cleanup) | auto | W2/W6 |
| `attribution_gate` | Enforce correct authorship/Co-Authored-By attribution on changes | `python scripts/attribution_gate.py --check` | auto | W5 |
| `verification_freshness_gate` | Block stale verification evidence; require fresh W4 proof before close | `python scripts/verification_freshness_gate.py --check` | auto | W4 |
| `release_cadence` (trigger) | Watch-only release-timing detector; proposes a version bump when change since last tag crosses thresholds (always exit 0) | `python scripts/release_cadence_trigger.py --check` | auto | W5 |
| `conversation_work_audit` | Audit that planning conversations recorded in `reviews/` map to durable work records | `python scripts/conversation_work_audit.py --check` | auto | W0/W1 |
| `work_schema_gate` | Validate the Work Item metadata schema SSoT | `python scripts/work_schema_gate.py --check` | auto | W1 |
| `plan_assumption_gate` | Verify recorded plan anchors/assumptions before implementation proceeds | `python scripts/plan_assumption_gate.py --check` | auto | W1 |

### Skills (trigger-based, W2-W6)

| Skill | Purpose | How to invoke (trigger) | Class | Stage |
| --- | --- | --- | --- | --- |
| `wave-conductor` | Drive `wave_dispatcher` parallel-wave planning and dispatch | trigger: "wave", "parallel wave", "dispatch wave" -> Skill tool | trigger-based | W2 |
| `merge-integrator` | Drive `merge_queue` enqueue/process integration flow | trigger: "merge queue", "integrate branch" -> Skill tool | trigger-based | W5 |
| `independent-verification` | Run the W4a/W4b independent verification protocol | trigger: "independent verification", "W4a", "W4b" -> Skill tool | trigger-based | W4 |
| `work-analytics` | Drive `work.py` stats/view/status and the Work Explorer | trigger: "work stats", "work analytics", "work explorer" -> Skill tool | trigger-based | W0/W5 |
| `release-conductor` | Drive release cadence + v2 release flow | trigger: "release", "cadence", "release flow" -> Skill tool | trigger-based | W5 |
| `taskset-dispatch` | Work a `TASKSET-AR-*` lane via the taskset dispatcher | trigger: "taskset", "TASKSET-AR", "진행" -> Skill tool | trigger-based | W1/W2 |
| `scm-steward` | Periodic repo-hygiene loop (worktrees, branches, stashes, claims, PRs) | trigger: "scm", "hygiene", "형상관리" -> Skill tool | trigger-based | W5/W6 |
| `grill` | Discovery interview -> blueprint + vision for a program/asset (planning-strategy entry) | trigger: "grill", "blueprint", "vision", "discovery interview" -> Skill tool | trigger-based | W1 |
| `enable` | Build the enablement pack from a grill blueprint | trigger: "enable", "enablement pack" -> Skill tool | trigger-based | W1 |
| `scaffold` | Scaffold an asset/program structure from an approved blueprint | trigger: "scaffold" -> Skill tool | trigger-based | W1 |
| `rsi-planning-loop` | Drive the recursive self-improvement planning loop | trigger: "rsi", "self-improvement planning", "rsi loop" -> Skill tool | trigger-based | W1 |
| `failure-to-regression` | Turn a gate/verify failure into a fixture/gate/regression task | trigger: "failure to regression", "regression from failure" -> Skill tool | trigger-based | W4/W6 |
| `session-closeout` | Run the W6 session closeout (retro, regeneration, handoff) | trigger: "session closeout", "closeout", "마무리" -> Skill tool | trigger-based | W6 |

## Decision

- Keep this reference as the canonical "how do I use this" surface for the
  500-series + ops-ergonomics assets; update it whenever a new ops command,
  gate, tool, or skill is registered in `RUNTIME-ASSET-REGISTRY.json`.
- Owner-gated boundaries are fixed: `merge_queue process`, `scm_steward clean`,
  `work close`, and any release tag/publish or `update --apply` require Owner
  approval; everything else is read-only or on-demand.

## Action Board

| Action | Owner | Status |
| --- | --- | --- |
| Register 500-series + ops assets in RUNTIME-ASSET-REGISTRY.json | lead_engineer | Done |
| Publish OPS-COMMAND-REFERENCE.md and register it in owner-docs.yml | lead_engineer | Done |
| Land `session_dashboard.py` (TASK-AR-523) so the dashboard hook path resolves | sibling task | Next |
| Land the 5 trigger-skills (TASK-AR-524) so skill paths resolve | sibling task | Next |
| Confirm `runtime_asset_usage --check` is block=0 after AR-523/524 merge | lead_engineer | Next |

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Cross-task path dependency: `session_dashboard.py` (AR-523) and 5 skills (AR-524) are not in this worktree base | `runtime_asset_usage --check` transiently blocks on 6 entries (12 missing-path findings) until siblings merge | Registry entries reference the canonical post-merge paths; expected transient block clears once AR-523/524 land; tracked on the Action Board |
| Mutating ops commands run without approval | Unintended merges/cleanup/releases | `process`/`clean`/`close`/release stay Owner-gated and dry-run-first |
| Reference drifts from registry | Stale "how do I use this" surface | Update this doc alongside any new RUNTIME-ASSET-REGISTRY.json entry |

## Next Steps

1. Merge TASK-AR-523 (`session_dashboard.py`) and TASK-AR-524 (5 skills) so all
   registered asset paths resolve.
2. Re-run `python scripts/runtime_asset_usage.py --check` and confirm block=0.
3. Re-run `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`
   and the full gate chain to confirm this reference and the registry pass.
