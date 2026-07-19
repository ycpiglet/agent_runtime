---
type: review
id: REVIEW-2026-07-19-AUTO-MERGE-READBACK
status: approved
created_at: 2026-07-19T10:34:25+09:00
owner: Lead Engineer
source_issue: https://github.com/ycpiglet/agent_runtime/issues/291
---

# Auto-merge execution read-back design

## Decision

`auto_merge.py --execute` must read the remote PR back and report success only
when `state=MERGED` and `mergedAt` is present.

## Scope

- Patch the host template `scripts/auto_merge.py`.
- Add deterministic package-level regressions for Draft rejection and
  remote-merge/local-cleanup divergence.
- Preserve dry-run policy, R3 classification, and the code-size cap.

## Out of scope

- Branch protection, review policy, workflows, or automatic Draft-to-Ready changes.
- Host-specific product behavior.

## Acceptance

1. Draft GraphQL rejection returns failure and never prints merge success.
2. Nonzero local cleanup is accepted only after remote MERGED read-back.
3. Existing R3 surface tests and template parity remain green.

## Rollback

Revert the scoped template/test commit.
