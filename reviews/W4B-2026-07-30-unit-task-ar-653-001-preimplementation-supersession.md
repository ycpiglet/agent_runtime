---
title: W4b Administrative Preimplementation Supersession - TASK-AR-653
date: 2026-07-30
created_at: 2026-07-30T22:57:09+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-225027-task-ar-653-ar653001
status: supersede
signal: block
verdict: SUPERSEDE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: 4fd24097dcce0fbeb79471ccfdc192c70d46ac80
reviewed_base_tree: a4ae4d5ddb6d4f18839b940c7a204c0fc62d71a9
reviewed_commit: 4fd24097dcce0fbeb79471ccfdc192c70d46ac80
worker_unique_commit_count: 0
verifier_agent_instance_id: qa-20260730-ar653-preimplementation-supersession
verified_by: qa-20260730-ar653-preimplementation-supersession
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_claim_supersession_audit
worker_identity: le-20260730-225027-kst-ar653001
independence_status: independent
implementation_reviewed: false
w4b_acceptance: false
administrative_release_evidence_only: true
claim_disposition: remain_claimed_pending_orchestrator_supersession
tags: [w4b, administrative-audit, preimplementation, claim-supersession, independent-verification, block]
---

# W4b Administrative Preimplementation Supersession

## Independent verdict

`SUPERSEDE — P0: 0, P1: 1, P2: 0`

Claim `CLAIM-20260730-225027-task-ar-653-ar653001` should be released only
to replace it with a corrected claim. The worker worktree is clean, contains
no worker modification or unique commit, and was created from main commit
`4fd24097dcce0fbeb79471ccfdc192c70d46ac80`. However, the registered
14-file target footprint omits both required byte-identical portable mirrors:

- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`

That omission is one administrative P1 because implementation under the
current claim cannot atomically maintain the canonical implementation and all
portable copies within its registered file authority.

Verifier `qa-20260730-ar653-preimplementation-supersession`, role
`qa-reviewer`, is distinct from worker
`le-20260730-225027-kst-ar653001`. The independent-verification procedure was
used only to attest the clean preimplementation state and the reason the claim
must be superseded.

> **NON-ACCEPTANCE BOUNDARY:** This report is administrative claim-release
> evidence only. It is not an implementation review, is not W4b implementation
> acceptance, does not approve any TASK-AR-653 code, and must never be cited or
> interpreted as implementation/W4b acceptance.

No claim was released or edited during this audit.

## Exact evidence

### 1. Clean worker worktree and zero unique commits

Executed in
`.worktrees/TASK-AR-653`:

```text
$ git status --short --branch
## codex/unit-task-ar-653-001-wave

$ git rev-parse HEAD
4fd24097dcce0fbeb79471ccfdc192c70d46ac80

$ git branch --show-current
codex/unit-task-ar-653-001-wave

$ git rev-list --count main..HEAD
0

$ git rev-list --count HEAD..main
0

$ git diff --quiet main...HEAD; printf '%s\n' "$?"
0

$ git status --porcelain=v2 --untracked-files=all
[no output]
```

The empty porcelain output proves there are no tracked modifications,
staged changes, or untracked files in the worker worktree. The symmetric
zero commit counts and empty three-dot diff prove there are no unique worker
commits or content changes relative to main.

### 2. Claim/worktree creation base

The control clone main reflog, claim record, branch reflog, and merge base form
one ordered provenance chain:

```text
$ git reflog show --date=iso-strict --format='%H%x09%gd%x09%gs' main | head -n 1
4fd24097dcce0fbeb79471ccfdc192c70d46ac80	main@{2026-07-30T22:50:13+09:00}	commit: docs(runtime): make TASK-AR-653 dispatchable

$ python - <<'PY'
import json
from pathlib import Path
d = json.loads(Path(
    "agents/runtime/task_claims/"
    "CLAIM-20260730-225027-task-ar-653-ar653001.json"
).read_text())
print(d["claimed_at"])
print(d["branch"])
print(d["worktree_path"])
PY
2026-07-30T22:50:27+09:00
codex/unit-task-ar-653-001-wave
.worktrees/TASK-AR-653

$ git reflog show --date=iso-strict --format='%H%x09%gd%x09%gs' codex/unit-task-ar-653-001-wave
4fd24097dcce0fbeb79471ccfdc192c70d46ac80	codex/unit-task-ar-653-001-wave@{2026-07-30T22:50:34+09:00}	branch: Created from HEAD

$ git merge-base main HEAD
4fd24097dcce0fbeb79471ccfdc192c70d46ac80
```

Main reached `4fd24097dcce0fbeb79471ccfdc192c70d46ac80` at
22:50:13 KST; the claim was recorded at 22:50:27; and its registered worker
branch was created from that HEAD at 22:50:34. Both refs and their merge base
remain exactly that commit. The claim/worktree therefore originated from main
commit `4fd24097dcce0fbeb79471ccfdc192c70d46ac80`.

### 3. Registered footprint omission and mirror identity

The claim JSON and canonical unit frontmatter contain the same 14 target
files. An exact membership check returned:

```text
claim_target_file_count=14
unit_target_file_count=14
claim_unit_target_lists_equal=True
scripts/agent_runtime/state_projection.py: claim=False, unit=False, tracked=True
src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py: claim=False, unit=False, tracked=True
```

Both omitted files exist in the reviewed baseline and are byte-identical:

```text
$ sha256sum scripts/agent_runtime/state_projection.py \
    src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py
c3cc5adcce631bf46952aa848dafacec7d451bb32fbc08f4ae80adc112ad401f  scripts/agent_runtime/state_projection.py
c3cc5adcce631bf46952aa848dafacec7d451bb32fbc08f4ae80adc112ad401f  src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py

$ cmp -s scripts/agent_runtime/state_projection.py \
    src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py; printf '%s\n' "$?"
0
```

The current equality is a baseline fact, not permission to omit the paths.
Because TASK-AR-653 changes state-projection semantics, the replacement claim
must register both portable mirrors so parity can be preserved and verified.

## Finding

### P1 — Portable state-projection mirrors are outside claim authority

The registered footprint includes
`src/agent_runtime/state_projection.py` but excludes both portable
`scripts/agent_runtime/state_projection.py` copies listed above. Continuing
under this claim would either leave distributable surfaces stale or require
out-of-claim edits. Supersede the untouched claim, register both missing
paths, and start implementation only under the corrected claim.

## Disposition

- Leave the present claim untouched for the orchestrator to release.
- Use this report solely as administrative evidence for that release and
  replacement.
- Preserve the clean worker branch until the orchestrator completes the
  supersession.
- Require fresh worker W4a and independent implementation W4b after actual
  TASK-AR-653 work; this report cannot satisfy either requirement.
