---
title: Autofolio v0.8 Migration Pilot - Red Attempt 1
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
status: failed
signal: red
severity: P1
runtime_product: 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2
host_commit: ca88433cf155fd03d616584fda7ed4aa3d33fd71
tags: [autofolio, migration, exact-product, downstream-contract, red]
---

# Autofolio v0.8 Migration Pilot - Red Attempt 1

## Decision

Do not promote Runtime product
`4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` as the Autofolio migration
candidate. The exact-host replay found four Runtime safety contracts that the
candidate does not preserve and an unresolved tracked-hook compatibility
boundary. The live Autofolio primary, frozen control, and detached Runtime
product were not modified.

The attempt stopped before lock migration, consumer commit, or RC work. This
is an expected causal-isolation failure: the disposable target exposed a
candidate defect without changing protected product behavior.

## Exact Inputs

- Runtime product / tree:
  `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` /
  `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Runtime template / scripts trees:
  `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f` /
  `62311b7847f66206a2a33e4bd497750bf074384f`
- Autofolio commit / tree:
  `ca88433cf155fd03d616584fda7ed4aa3d33fd71` /
  `c51490efb2249f532c78b03025a3d0c78cca68e7`
- Initial protected tracked paths / digest:
  `1804` /
  `30a13b834e4c3bf0f824018fe3c994f72d6300f747f8b27907b873233b97f994`
- Exact v0.6 unmanaged count: `20`
- Staging v2 reconcile: `59 safe_updates`, `0 conflicts`,
  `170 preserved`, `22 excluded`

Python module provenance was checked explicitly before every authoritative
Runtime command. An initial read-only command resolved an unrelated editable
checkout, so its output was discarded. The accepted command used the detached
product's `src` through an explicit `PYTHONPATH`, and its reported
`template_root` matched that product checkout.

## Twenty Legacy Seam Dispositions

The attempt classified every v0.6 unmanaged path. These are attempted
dispositions, not a green migration result.

### Reclaimable as managed in this candidate

1. `scripts/agent_orchestrator.py` - exact candidate replacement retained
   atomic writes, added authoritative terminal outcomes, and passed syntax,
   help, and dry-run spawn smoke.
2. `agents/project/WORK-SCHEMA.yml` - exact candidate replacement is a field
   superset and passed `work_schema_gate.py --check`.

### Preserve as seed-once host state

3. `CLAUDE.md`
4. `agents/project/NEXT-SESSION-POINTER.yml`
5. `.codex/hooks.json`
6. `agents/lead_engineer/tasks/units/examples/UNIT-EXAMPLE-001.md`
7. `agents/lead_engineer/compound_log.md`

The hook file remains a blocking compatibility seam: the candidate requires
the portable hook dispatcher while Autofolio also preserves a host-owned
Owner-authority prompt hook and legacy cross-platform contract.

### Preserve as host-owned context or operating data

8. `AGENTS.md`
9. `agents/roles.yml`
10. `schemas/task.schema.json`
11. `agents/lead_engineer/REPORTING-FORMAT.md`
12. `agents/project/SKILL-GOVERNANCE.md`
13. `agents/research_agent/notes/EVIDENCE-2026-06-03-001-requirement-elicitation.md`
14. `scripts/task_identity.py`
15. `agents/lead_engineer/reports/INDEX.md`
16. `agents/lead_engineer/reports/README.md`

### Preserve temporarily because candidate replacement regresses safety

17. `scripts/owner_governance_gate.py`
18. `scripts/parallel_worktree_gate.py`
19. `scripts/taskset_dispatcher.py`
20. `scripts/wave_dispatcher.py`

Seven additional v0.6 lock conflicts were explicitly classified
`host_owned`: `.env.example`, `scripts/auto_merge.py`,
`scripts/generate_views.py`, `scripts/session_dashboard.py`,
`scripts/session_resume_check.py`, `scripts/status_alias.py`, and
`scripts/task_claim_dispatcher.py`.

## Exact Regression Evidence

Each candidate file was copied alone into the disposable target, tested
against Autofolio's existing no-install host contract, and then restored from
the byte-for-byte backup when it failed.

| Candidate replacement | Result | Safety contract lost |
|---|---:|---|
| `owner_governance_gate.py` | 11 failed, 2 passed | protected untracked files must not be opened; partial tracking, staged deletion, and git-probe failure must fail closed |
| `parallel_worktree_gate.py` | 1 failed, 8 passed | missing continuity state must identify both supported candidate paths |
| `taskset_dispatcher.py` | 19 failed, 66 passed | blocked/not-ready/localized states and readiness failures must refuse before claim, subprocess, or mutation with structured diagnostics |
| `wave_dispatcher.py` | 35 failed, 24 passed | duplicate IDs, unresolved dependencies, mixed-batch readiness/footprints, and malformed claims must fail before claim, subprocess, git, or mutation |
| all four preserved host seams | 166 passed | preserved baseline remains green |

Private raw evidence hashes:

- Owner governance JUnit:
  `6cf6de4db79d79426d9c9c149d7d1728584535322ae543814a2ed8c51920b1bf`
- Parallel continuity JUnit:
  `414612145926c7030cb91e5b74001d5c214c96d8fb4e853d267da58501a1c607`
- Taskset dispatcher JUnit:
  `497a1f898b88cea29fbdbe7e13297d9ea307a899537347d424d4068efefcad10`
- Wave dispatcher JUnit:
  `dbc1f62216768f150acd1aa0c74450743841d0dc0fba1a6965884caf4a12a3c8`
- Preserved-seam JUnit:
  `12cd29cb5477a7265a8b7c44247bc61d0c1d2d00517af82bad36cdb2b6f81c63`

## Doctor Result

After safe sync and before lock migration, exact-product doctor reported
`14 blockers`, `2 infos`, and `8 warnings`:

- six missing portable hook modes;
- three missing Windows hook commands;
- three stale legacy hook commands;
- one continuity diagnostic failure while the host safety seam is preserved;
- one expected out-of-date v1 lock.

Doctor evidence digest:
`f16e5bcd7fef1fe23b9e98d6565350b4ad6c3228d94025a22f145da593078df3`.

## Required Runtime Repair

Before another Autofolio migration attempt:

1. combine the portable Owner gate with Autofolio's git-index/HEAD,
   never-open-untracked, and fail-closed probe contract;
2. preserve status/pointer continuity compatibility without weakening the
   newer canonical pointer checks;
3. promote taskset and wave pre-mutation refusal contracts into both Runtime
   source and packaged template mirrors;
4. define a portable hook-extension compatibility contract so canonical
   lifecycle dispatch and the host Owner-authority hook coexist without
   duplicate legacy dispatch; and
5. add Autofolio-derived regression fixtures to Runtime before pinning a new
   product commit.

Attempt 2 must start from a new clean target and same-commit frozen control.
It must not continue from this partially synchronized disposable target.
