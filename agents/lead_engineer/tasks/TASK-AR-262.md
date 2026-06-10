---
id: TASK-AR-262
title: Broad pytest collection hygiene and verification tier split
status: completed
priority: P1
importance: High
difficulty: M
est_hours: 4
est_tokens: 1600
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: qa
owner: qa
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [pytest, verification, template-tests, repo-health]
audit_log: [pyproject.toml, tests]
---

## Goal

Separate root verification from generated-project template verification so broad tests become usable completion evidence.

## Completion Criteria

- Root-focused pytest collection does not accidentally collect template-project tests requiring generated-project context.
- Template tests have an explicit command and `PYTHONPATH` contract.
- A review artifact records the prior broad-suite failures and the new verification tiers.
- Focused root tests remain runnable without long template timeouts.

## Execution Notes

- Do not claim full-suite green until a fresh full-suite command completes.
- Preserve template tests; do not delete them to make root pytest pass.

## Result

- Added `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = [".", "src"]`.
- Added `tests/test_pytest_collection_contract.py`.
- Verified default collection excludes template tests.
- Added `reviews/REVIEW-2026-06-10-agent-runtime-pytest-hygiene.md`.
