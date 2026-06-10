---
type: governance_ops_report
id: GOVERNANCE-OPS-REPORT-2026-06-10
audience: owner
status: watch
signal: watch
score: 90
priority: P0
tags: [governance, usage-metrics, lifecycle, waiver, state-sync]
generated_at: 2026-06-10T23:47:10+09:00
---

# Governance Operations Report

## Bottom Line
- Summary: governance operations signal is `watch`.
- Scope: collaboration governance, runtime asset usage/reuse, and active state sync.
- Boundary: broad full-suite runtime remains separate under `TASK-AR-262`; this report uses focused gates.

## Signal

| Gate | Block | Watch | Waived | Detail |
| --- | ---: | ---: | ---: | --- |
| collaboration-governance | 0 | 5 | 1 |  |
| runtime-asset-usage | 0 | 0 | 0 | assets=14 usage_total=85 |
| state-sync | 0 | 0 | 0 |  |

## Insight
- Asset kinds: `{"gate": 4, "hook": 2, "script": 6, "skill": 1, "trigger": 1}`.
- Lifecycle decisions: `{"keep": 13, "observe": 1}`.
- Low-reuse candidates: `gate.owner_governance, report.governance_ops, hook.taskset_prompt`.
- Remaining collaboration waiver is meaningful only if it points to real missing role evidence, not missing scripts.

## Decision
- Decision: keep runtime asset usage measurement in Owner governance.
- Decision: keep `role-usage:scribe` visible until real scribe claim/log evidence exists.
- Decision: default pytest collection is root tests only; template tests require explicit suite execution.

## Action Board

| Action | Owner | State | Evidence |
| --- | --- | --- | --- |
| Remove remaining scribe waiver after real claim/log evidence | lead-engineer | watch | `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json` |
| Review monitored low-frequency roles | lead-engineer | watch | `scripts/collaboration_governance_gate.py --check` |
| Keep runtime asset registry current when adding skills/hooks/triggers | agent-runtime-core | pass | `agents/project/RUNTIME-ASSET-REGISTRY.json` |
| Keep state sync gate in Owner governance | lead-engineer | pass | `scripts/state_sync_gate.py --check` |

## Asset Lifecycle Table

| Asset | Kind | Lifecycle | Usage | Reuse | Decision |
| --- | --- | --- | ---: | ---: | --- |
| `gate.owner_governance` | gate | keep | 2 | 1 | review |
| `gate.collaboration_governance` | gate | keep | 12 | 2 | keep |
| `gate.runtime_asset_usage` | gate | keep | 7 | 2 | keep |
| `gate.state_sync` | gate | keep | 5 | 2 | keep |
| `report.governance_ops` | script | keep | 3 | 1 | review |
| `hook.taskset_prompt` | hook | keep | 2 | 1 | review |
| `hook.stop_owner_governance` | hook | keep | 6 | 2 | keep |
| `trigger.planning` | trigger | observe | 9 | 2 | keep |
| `capability.ralph_loop` | script | keep | 2 | 2 | keep |
| `capability.agent_retro` | script | keep | 11 | 2 | keep |
| `capability.retro_forward` | script | keep | 7 | 2 | keep |
| `capability.scribe_due` | script | keep | 10 | 2 | keep |
| `capability.doc_steward_due` | script | keep | 5 | 2 | keep |
| `skill.taskset_dispatch` | skill | keep | 4 | 2 | keep |

## Next
- Add real scribe claim/log evidence in the next reporting cycle.
- Promote recurring low-frequency role watches into tasks if they persist.
- Run `python scripts/owner_governance_gate.py` before claiming governance closure.
