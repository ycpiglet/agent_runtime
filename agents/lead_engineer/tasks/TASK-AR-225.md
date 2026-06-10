---
id: TASK-AR-225
display_id: TASK-AR-225
task_uid: 046534c6-22d2-4aba-8ea0-26f4fbce2ec4
registered_at: 2026-06-09
created_at: 2026-06-09
started_at: 2026-06-09
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1800
task_set_id: TASKSET-AR-RELEASE-STEWARD
tags:
  - release-preflight
  - source-publication
  - sanitize
  - closeout
audit_log:
  - BACKLOG.md
  - STATUS.md
  - agents/lead_engineer/tasks/TASK-AR-224.md
  - agents/lead_engineer/tasks/TASK-AR-223.md
  - agents/project/MIGRATION-HOLD-ROUTING.yml
  - agents/project/RELEASE-GATE-TEMPLATE.yml
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md
created: 2026-06-09
---

## Goal

Close the `release-preflight findings=358` blocker discovered by `TASK-AR-224` executable proof before `v0.1.8` can move from hold to ready.

## Blocker Summary

- Source command:
  - `PYTHONPATH=src python -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --warning-summary-gate-strict-refs <refs> --check`
- Actual Python path used:
  - `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe`
- Result:
  - exit_code: 1
  - findings: 358

## Finding Groups

1. Host-only task files in publishable source
   - Symptom: `agents/lead_engineer/tasks/TASK-AR-201.md` through `TASK-AR-224.md` are flagged as `forbidden-path`.
   - Target: host governance records must not be published as clean package source unless explicitly classified as docs/templates.

2. Absolute local paths in migration docs
   - Symptom: `agents/project/MIGRATION-COMPAT-MAP.yml`, `agents/project/MIGRATION-HOLD-ROUTING.yml`, and template migration example contain local machine paths.
   - Target: publishable files use placeholders or repo-relative paths; host-only files are excluded.

3. Host history reference in template example
   - Symptom: `src/agent_runtime/templates/project/agents/project/MIGRATION-COMPAT-MAP.example.yml` contains product-specific history reference.
   - Target: template example must be generic.

4. Clean source selection mismatch
   - Symptom: many `unexpected-source-file` findings under `github-publish-plan`.
   - Target: release source must come from `publish-bundle` selected files only.

5. Host lock stale
   - Symptom: fixture host reports `agent_runtime.lock.json lock-out-of-date`.
   - Target: either refresh fixture lock or record as fixture-only blocker with owner/expiry.

## Work Items

- Decide which current root files are host-only versus package-public.
- Sanitize or exclude absolute local paths from publishable artifacts.
- Update generic template examples so they do not mention host history or local machine paths.
- Re-run release-preflight using fixture host and capture the reduced blocker count.
- Feed remaining blockers into `TASK-AR-223` closeout with `release_state=hold_for_data` or `block`.

## Completion Criteria

- `release-preflight` no longer reports host-only TASK/review files as package-public source, or those findings are intentionally routed through `hold_for_data` with owner/expiry.
- `MIGRATION-HOLD-ROUTING.yml` is either host-only or sanitized for publication.
- `MIGRATION-COMPAT-MAP.example.yml` contains no absolute local path and no product-specific history reference.
- fixture host lock status is resolved or explicitly waived with `approved_by`, `decision_date`, `expiry`, and `justification`.
- `TASK-AR-223` closeout has a clear release decision: `ready`, `hold_for_data`, or `block`.

## Cycle Log

- 2026-06-09: Created from `TASK-AR-224` executable proof after release-preflight returned `findings=358`.
- 2026-06-09: Sanitizer updated so top-level host `agents/` records are excluded from publishable source while nested project templates remain scanned.
- 2026-06-09: Generic migration template example sanitized to remove host-specific `tag_manual` source history and absolute local path.
- 2026-06-09: Targeted sanitizer test passed: `95 passed in 9.09s`.
- 2026-06-09: Root source preflight improved from `findings=358` to `findings=245`; remaining findings were clean-source-selection mismatch plus stale fixture host lock.
- 2026-06-09: Clean public source bundle generated with `publish-bundle --source . --dest .tmp/public-source --apply`; result `files=209`, `findings=0`, `applied=209`.
- 2026-06-09: Fixture host lock refreshed with `agent_runtime.cli lock --root tests/fixtures/host --write`; result `findings=0`.
- 2026-06-09: Release preflight passed using clean bundle source: `release-preflight --source .tmp/public-source --host-root tests/fixtures/host --check`; result `findings=0`.

## Closeout Decision

- Result: completed.
- Release path: clean publish bundle is the canonical release source. The repo root remains a working source that can contain host governance records; public release checks must use the generated bundle.
- Remaining release dependency: `TASK-AR-223`/`TASK-AR-221` still need closeout bundle evidence for query contract, overlay, migration evidence, reviewer/correction/A2A, and version decision fields.
