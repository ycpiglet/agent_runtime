---
type: release-publication
id: RELEASE-PUBLICATION-v0.1.8
audience: owner, agents, maintainers
status: released
priority: P1
tags:
  - release
  - autonomy-policy
  - executive-brief
  - github-publication
release: v0.1.8
published_at: 2026-06-09T10:34:02Z
owner_required: false
approval_route: agent_release_council
---

# RELEASE-PUBLICATION-v0.1.8

## Bottom Line
- `v0.1.8` was released through the autonomous branch -> commit -> PR -> CI -> merge -> tag path.
- Owner approval was not required because the release council classified this as noncritical policy/runtime hardening.

## Signal
- PR: https://github.com/ycpiglet/agent_runtime/pull/3
- Merge commit: `54a04a58b9f53c845fee281aea70a9e7ffee955a`
- Tag: `v0.1.8` -> `54a04a58b9f53c845fee281aea70a9e7ffee955a`
- CI: GitHub Actions run `27200245237`, Python `3.10`, `3.11`, `3.12` all passed.
- External install smoke: `pip install git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8`, imported `agent_runtime.__version__ == 0.1.8`.

## Action
- Use `v0.1.8` as the current public release tag.
- For host projects, update `agent_runtime.yml` to `ref: v0.1.8`, then run sync/lock through the normal runtime update flow.

## Insight
- The release path exposed real automation gaps in public CI: clean bundle helper inclusion, strict-ref artifact paths, host preflight remote alignment, Windows path escape handling, and message-claim concurrency.
- Those gaps are now covered by CI and release-preflight evidence rather than manual approval.

## Decision
- Released.
- Future routine patch/minor releases should use the same agent-council path and ask Owner only for critical boundaries.

## Footer
- Evidence files: `agents/project/release/RELEASE-DECISION-v0.1.8.yml`, `agents/project/release/RELEASE-EXECUTION-v0.1.8.yml`, `reviews/REVIEW-2026-06-09-agent-runtime-v018-automation-policy-release.md`.

## Post-merge verification
- Main push CI: GitHub Actions run `27200314376`, conclusion `success`, head `54a04a58b9f53c845fee281aea70a9e7ffee955a`.
