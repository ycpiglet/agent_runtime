# REVIEW: v0.1.8 Local Smoke Plan Readiness

## Bottom Line

v0.1.8 local tag smoke is plan-ready, but not executed. This is a non-mutating readiness check only.

## Signal

- Command: `python -m agent_runtime.publish_tag_smoke --source . --repo-dir .tmp/local-tag-smoke-plan-v018-repo --install-dir .tmp/local-tag-smoke-plan-v018-install --tag v0.1.8 --check`
- Result: `findings=0`
- Planned install spec: `git+file:///C:/Users/ycpig/agent_runtime/.tmp/local-tag-smoke-plan-v018-repo@v0.1.8`
- Release execution gate: `ready_pending_owner_approval`, `findings=0`

## Insight

The local smoke path is structurally ready, but executing it would create a local temp git tag and install target. That remains gated behind owner approval or an explicit release execution instruction.

## Decision

- Record local smoke plan readiness as evidence.
- Do not run `publish_tag_smoke --apply` before owner approval.
- Keep package version at `0.1.6` and release route at `ready_pending_owner_approval`.

## Verification Result

- Release execution gate after smoke-plan record: `status=pass`, `route=ready_pending_owner_approval`, `target=v0.1.8`, `package=0.1.6`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-local-smoke-plan --check`: `files=209`, `findings=0`.
