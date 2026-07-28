---
title: TASK-AR-643 UNIT-001 Independent W4b Approval
date: 2026-07-29
status: approved
signal: pass
score: 96
verdict: APPROVE
task_id: TASK-AR-643
unit_id: UNIT-TASK-AR-643-001
verified_head: 832fe97e30f8a4d1f4331417e39ff90e11fb0a35
verified_by: /root/w4b_task_ar_640_001
verifier_role: independent-verifier
worker_instance: le-20260728-234228-kst-643001
tags: [w4b, independent-verification, profile-manifest, dependency-closure, clean-host]
---

# TASK-AR-643 UNIT-001 Independent W4b Approval

## Verdict

**APPROVE — 96/100.** The independently audited implementation head is
`832fe97e30f8a4d1f4331417e39ff90e11fb0a35`. The unit delivers one fail-closed
template profile projection and closes the advertised generic lifecycle
dependencies without shipping Agent Runtime product release procedures to core.

## Independent Verification

```text
python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py \
  tests/test_wheel_dotfiles_packaging.py tests/test_adoption.py \
  tests/test_inventory_sync_sanitize.py -q
# 144 passed in 14.65s

python -m pytest tests/test_template_smoke.py::test_clean_host_runs_work_session_report_and_dependency_lifecycle \
  tests/test_allimbot.py tests/test_runtime_asset_usage.py \
  tests/test_wheel_dotfiles_packaging.py -q
# 23 passed in 1.88s

python scripts/runtime_asset_usage.py --check
python scripts/verify_wheel_dotfiles.py --check
python scripts/footprint_conflict_gate.py --postverify --task-id TASK-AR-643 \
  --base 677a4f23 --enforce-undeclared
# pass; before W4b evidence projection: declared=20 actual=25 undeclared=0

python -m pytest -q
# 2333 passed, 3 skipped, 4 pre-existing UI escape warnings in 110.71s
```

## Adversarial Evidence

- In temporary installed hosts, all four requested projections agreed across
  `selected_paths`, sync actions, adoption actions, v2 lock ownership, and the
  installed dependency gate: core `240`, core+web-content `240`,
  core+security-service `242`, full runtime `242` selected files.
- Core and web hosts omitted root `scripts/test_*.py`, `allimbot.py`, and the
  Allimbot stop wrapper; security and full hosts included exactly the two
  Allimbot helpers. Core `.codex/hooks.json` has no Allimbot stop hook.
- Missing, malformed, wrong-schema manifests and unknown manifest/config
  profiles all raised fail-closed blockers. Deleting selected
  `scripts/save_report.py` from an installed core host produced
  `dependency-missing-installed`; inserting an Allimbot reference into the
  selected core release skill produced `dependency-cross-profile`.
- `work.py`, `session_baseline.py`, `dirty_intake.py`, `backlog_board.py`, and
  `task_identity.py` are exact root/template mirrors. Static local-import
  closure for their imported helper modules is wholly inside core, and the
  clean host completed sync, Git init, initiative/taskset/task/unit
  registration, status, verify, close, session baseline, dirty intake,
  save-report, five-column report index, report views, and installed gate.
- The built-wheel check inspected archive contents for the manifest, dotfiles,
  lifecycle helpers, runtime-asset gate, and selected skills. The release
  conductor contains only generic proposal/verification guidance; no
  Autofolio, Allimbot, Bean Wiki, Tag Manual, or Agent Runtime release path is
  advertised by the core release skill.
- The report smoke now examines both `check_agent_docs.py` stdout and stderr,
  so a report-specific validator diagnostic can no longer be masked by stream
  selection.

## Scope and Repair

The verifier found no P0/P1 profile, lock, adoption, wheel, or core-release
leak. It made one bounded test repair in `832fe97e`: combine the docs checker
stdout and stderr before asserting the generated report has no diagnostic.
No consumer repository, claim release, push, merge, version, tag, publish, or
release operation was performed.

## Residual Non-Blocking Debt

The deliberately minimal clean-host fixture is not globally
`check_agent_docs.py` clean: its run returns 1 for five pre-existing legacy
scaffold baseline records and three legacy `TASK-\\d+` checker assumptions
triggered by the current `work.py` `TASK-AR-990` lifecycle sample. The saved
report itself adds zero diagnostics on either stream, and report schema/index/
views all pass. Aligning the legacy checker and bootstrap baseline is a
separate host-documentation compatibility task, not a reason to ship product
release assets into core.
