# REVIEW: TASK-AR-225 Source Publication Hygiene

## Bottom Line

`TASK-AR-225` is closed for the release-source blocker. The release preflight now passes with `findings=0` when run against the generated public source bundle.

## Signal

- Initial executable proof from `TASK-AR-224`: `release-preflight --source . --host-root tests/fixtures/host ... --check` returned `findings=358`.
- Sanitizer change: top-level host `agents/` records are skipped from publishable source checks; nested template files under `src/agent_runtime/templates/project/agents/` remain in scope.
- Template hygiene change: `MIGRATION-COMPAT-MAP.example.yml` no longer contains a host-specific `tag_manual` source reference or absolute local path.
- Targeted test: `PYTHONPATH=src python -m pytest tests/test_inventory_sync_sanitize.py -k "sanitize" -q`; result `95 passed in 9.09s`.
- Intermediate preflight after sanitizer/template fix: `findings=245`.
- Public bundle creation: `publish-bundle --source . --dest .tmp/public-source --apply`; result `files=209`, `findings=0`, `applied=209`.
- Fixture lock refresh: `agent_runtime.cli lock --root tests/fixtures/host --write`; result `findings=0`.
- Final preflight: `release-preflight --source .tmp/public-source --host-root tests/fixtures/host ... --check`; result `findings=0`.

## Insight

- `source=.` is not a valid public-release source because the working tree intentionally contains host governance records, task history, and local review artifacts.
- The valid release path is `publish-bundle` first, then `release-preflight` over that clean bundle.
- Host lock drift is a real release-gate signal and should remain blocking unless refreshed or explicitly waived.

## Decision

- Treat `publish-bundle -> release-preflight(clean bundle) -> host lock check` as the release artifact SOP.
- Do not publish from repo root directly.
- Feed the passing preflight evidence into `TASK-AR-223` closeout and `TASK-AR-221` integrated gate rehearsal.
