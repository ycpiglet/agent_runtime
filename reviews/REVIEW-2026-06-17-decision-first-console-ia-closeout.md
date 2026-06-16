# REVIEW: Decision-First Console IA Closeout

## Bottom Line

`TASKSET-AR-DECISION-FIRST-CONSOLE-IA` is complete. The final lane, `TASK-AR-569`, added browser-backed regression coverage for the decision-first home budget and was independently W4b-approved, released, merged, indexed, and cleaned.

## Scope Closed

- Completed `TASK-AR-569` on branch `codex/task-ar-569-e2e-dom-budget`.
- Added E2E regression coverage for initial DOM budget (`<= 1500`) and decision-shell budget before the detailed work surface.
- Added Playwright desktop/mobile coverage asserting the default home document stays within two viewports after cockpit/work-state data renders.
- Kept the detailed work surface closed on default `/` and opened it only through explicit route/sidebar navigation.
- Bounded cockpit and work-state hero card regions so loaded runtime data cannot expand the whole document past the screen budget.
- Preserved maturity signals in the same path: responsive CSS, skip-link/landmarks/ARIA, SSE, KO/EN i18n, and validation indicators.

## Evidence

- W4a review: `reviews/REVIEW-2026-06-16-task-ar-569-e2e-dom-budget.md`
- W4b evidence: `reviews/W4B-2026-06-17-TASK-AR-569.md`
- Claim: `agents/runtime/task_claims/CLAIM-20260616-232833-task-ar-569-8b7b.json`
- Status: `STATUS.md`
- Pointer: `agents/project/NEXT-SESSION-POINTER.yml`
- Board: `BACKLOG-BOARD.md`

## Verification

- `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 15 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.
- `PYTHONPATH=src python scripts/taskset_work_gate.py --check` -> pass.
- `PYTHONPATH=src python scripts/evidence_index_generator.py --check` -> pass.
- `python scripts/work.py status` -> active claims 0, one root worktree only.
- `git status --short` -> clean before this closure record.
- `git stash list` -> empty.
- `python scripts/dirty_intake.py --json` -> route clean, files empty, worktrees empty, stashes 0.

## Integration / Cleanup

- Merged implementation into `claude/decision-first-console-ia`.
- Removed `.worktrees/TASK-AR-569`.
- Deleted local branch `codex/task-ar-569-e2e-dom-budget`.
- Preserved six session baseline snapshots in `agents/runtime/session_baselines/` instead of dropping hook-created intake residue.
- Backlog board now reports `open_count: 0`, active workflows `0`, and `Decision Cockpit` as `7/7` done.

## Residual Risk

- Browser-height regression uses `pytest.importorskip("playwright.sync_api")`; environments without Playwright retain the DOM/maturity regression but skip the live browser-height assertion.
- Existing governance gates still report historical watch-only findings unrelated to this taskset, such as legacy verification freshness and attribution watch records.
