---
title: Bean Wiki Attempt-2 Portable Continuity Independent Review
date: 2026-07-29
status: failed
signal: block
score: 45
verdict: REQUEST_CHANGES
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-006
verified_by: p0-integrated-review-continuity-block
verifier_role: independent-auditor
tags: [w4b, bean-wiki, portability, continuity, p0]
---

# Bean Wiki Attempt-2 Portable Continuity Independent Review

## Bottom Line

**REQUEST_CHANGES — P0 confirmed.** Selected-core adoption can create a valid
default working-tree claim and then make its own mandatory parallel-worktree
gate block because neither installed profile content nor adoption diagnostics
supplies either required STATUS candidate. This is a portable bootstrap
contradiction, not a Bean-specific content failure.

## Read-only Evidence

Frozen attempt:
`/home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-2`
at `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`.

```text
STATUS.md: absent
agents/lead_engineer/STATUS.md: absent
agents/project/NEXT-SESSION-POINTER.yml: present
```

`agents/host/pilot/evidence/adoption-verification-green-2.json` records the
claimed-state failure: `priority=P0`,
`code=portable-active-claim-status-seed-missing`,
`gate=scripts/parallel_worktree_gate.py --check`, `gate_exit=1`,
`block_count=1`, and both STATUS candidates missing.

The current frozen claim is already `status: blocked`; accordingly, a later
read-only `python scripts/parallel_worktree_gate.py --check` returns `0` with
watches. Only active statuses invoke `_continuity_findings`, so this does not
invalidate the captured claimed-state failure.

Runtime source confirms the contradiction:

- `parallel_worktree_gate.py:76–79` recognizes only `STATUS.md` and
  `agents/lead_engineer/STATUS.md`.
- `_continuity_findings` (lines 402–425) blocks active claims when both are
  absent, even if handoff/log files exist.
- The core host lock installs `agents/project/NEXT-SESSION-POINTER.yml` as
  `seed_once`, but neither STATUS candidate.
- The installed pointer has canonical schema but says `active_claims: []` and
  points `pointers.status` at the missing lead-engineer STATUS file.

## Recommendation

Do not silently accept any pointer. Prefer a narrow canonical-pointer
alternative:

1. Preserve current STATUS validation whenever either STATUS file exists.
2. Only when both are absent, accept `agents/project/NEXT-SESSION-POINTER.yml`
   if its canonical schema names the exact active claim in `active_claims` and
   its task/task-set identity matches that claim.
3. Require existing declared handoff/log paths plus non-empty resumable pointer
   state and next actions.
4. Fail closed for malformed/stale/mismatched pointer or missing sidecars.

This uses core's actual continuity artifact and proves one-to-one resumability.
A generic STATUS seed is a weaker fallback: a marker-only file can be stale and
adds a broad pseudo-SSoT. If selected, adoption and doctor must install and
diagnose a claim-derived seed atomically, never a static placeholder.

## Freeze and Replay

Keep attempt-2 frozen. Repair the Runtime portable contract, add core adoption
and negative pointer-identity regressions, independently W4b the repair, then
replay from a new worktree at the original Bean baseline. Allimbot and all
downstream consumer rollout remain blocked.

## Decision

P0; no release or consumer replay. The minimal safe remediation is the strict
canonical-pointer fallback, not unconditional STATUS seeding or mere pointer
presence.
