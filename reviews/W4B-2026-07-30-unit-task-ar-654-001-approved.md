# UNIT-TASK-AR-654-001 Independent W4b Review — Approved

- verdict: `APPROVED`
- verified_at: `2026-07-30T10:12:00+09:00`
- verified_by: `qa-20260730-094300-task-ar-654-w4b`
- verifier_role: `qa-reviewer`
- claim_id: `CLAIM-20260730-092200-task-ar-654-host-gates`
- branch: `codex/unit-task-ar-654-001-host-required-gates`
- implementation_commit: `898adcdc`
- final_behavior_commit: `bd3bd0bc`
- reviewed_head: `9cc3fadf`
- worker_evidence: `reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730101015.json`
- prior_reviews:
  - `reviews/W4B-2026-07-30-unit-task-ar-654-001-rework.md`
  - `reviews/W4B-2026-07-30-unit-task-ar-654-001-rework2.md`

## Decision

W4b approves `UNIT-TASK-AR-654-001` at reviewed HEAD `9cc3fadf`.

The host-owned merge-gate policy is bound at enqueue, revalidated from the
effective integration ref before mutation, and appended after worker-supplied
narrow verification. Worker branches cannot weaken the policy or its declared
control files. Required-gate failures and launch failures fail closed without
merging or reaching PR handoff.

The two prior rework rounds are fully resolved. No blocking implementation,
compatibility, template-parity, Bean Wiki policy, lifecycle, or footprint
finding remains.

## Independent Revalidation

### Gate-integrity and failure behavior

- A worker change that weakens a protected gate implementation is rejected
  before verification or merge.
- A protected gate rename is diffed with NUL delimiters and `--no-renames`, so
  the protected source deletion remains visible and is rejected.
- A missing required-gate executable produces a terminal failed queue entry,
  actionable feedback, and no traceback.
- An invalid UTF-8 policy fails enqueue with return code 2 and does not create
  queue state.
- Worker deletion or modification of the base-owned policy cannot change the
  effective required gates.

### Compatibility and dry-run behavior

- An absent policy preserves the legacy entry shape and processing behavior.
- An empty `gates` list canonicalizes away `protected_paths` enforcement and
  preserves legacy processing.
- Dry-run resolves the read-only equivalent of local processing for missing,
  behind, ahead, and diverged integration branches.
- Behind-base policy drift and diverged refs fail consistently in dry-run and
  real processing; dry-run leaves queue state, branches, refs, and the current
  checkout unchanged.
- An ahead local integration branch retains its existing commits and accepts a
  compatible worker merge.

Six independent temporary bare-origin/clone scenarios passed:

```text
PASS empty-policy legacy
PASS missing integration
PASS ahead integration
PASS behind integration
PASS diverged integration
PASS protected rename
PASS all 6 independent compatibility/adversarial cases
```

The seven focused regression cases for empty-policy compatibility, protected
gate mutation, protected rename, missing executable, invalid UTF-8, custom
integration policy, and behind-base dry-run also passed individually.

## Final-HEAD Verification

The independent verifier reran the recorded verification commands against
HEAD `9cc3fadf`:

```text
python -m pytest tests/test_merge_queue.py -q
# PASS: 40 passed in 16.55s

cmp scripts/merge_queue.py \
  src/agent_runtime/templates/project/scripts/merge_queue.py
# PASS

cmp skills/merge-integrator/SKILL.md \
  src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
# PASS

python scripts/regen_host_lock_if_needed.py --check
# PASS: fixture lock is up to date
```

The broader generated-host compatibility suite also passed:

```text
python -m pytest \
  tests/test_template_smoke.py \
  tests/test_regen_host_lock_if_needed.py \
  tests/test_lock_merge_driver.py \
  tests/test_runtime_asset_usage.py -q
# PASS: 38 passed in 15.20s
```

Total independently rerun Python regressions: `78 passed`.

`python scripts/evidence_index_generator.py --check` also passed before this
review was added. The index is regenerated as part of this W4b evidence write.

History normalization is clean: every commit in `origin/main..9cc3fadf` uses
`68498184+ycpiglet@users.noreply.github.com` for both author and committer.
The rewritten implementation and final behavior trees are byte-equivalent to
the previously reviewed round-3 content.

## Bean Wiki Host Policy

Runtime normalization succeeds for Bean Wiki's
`agents/host/MERGE-GATES.json`:

```text
schema=agent-runtime-merge-gates/v1
digest=8d8d601000364110f7af9755451d27bbacbae6f8c1762bbefecd45a106c99975
gate_ids=design-contract,design-visual
protected_count=13
```

Bean Wiki's validator and configured protected closure agree exactly:

```text
required_count=13
actual_count=13
missing=
extra=
validation_errors=0
```

Both configured product commands passed independently:

```text
npm run design:check
# PASS: generated tokens, 9 design-contract tests, contract checker,
#       7 palette tests, and palette checker

npm run design:visual
# PASS: production build and 12 Playwright visual cases
```

The visual run's untracked `test-results/.last-run.json` artifact was removed
after verification; the Bean Wiki integration worktree was clean afterward.

## Footprint and Lifecycle

At reviewed HEAD, the enforced integration-base check passed:

```text
python scripts/footprint_conflict_gate.py \
  --postverify \
  --task-id TASK-AR-654 \
  --base origin/main \
  --enforce-undeclared

task_id=TASK-AR-654
declared=30 actual=36 undeclared=0
```

The lifecycle declaration covers the task-registration projections, unit and
claim records, W4a/W4b evidence, review index, pane event, and A2A release
projection. No TASK-AR-648 protected surface or undeclared implementation path
was changed.

## Release Gate

Independent approval is granted. Claim release must use:

```text
verified_by=qa-20260730-094300-task-ar-654-w4b
verifier_role=qa-reviewer
verification_evidence=reviews/W4B-2026-07-30-unit-task-ar-654-001-approved.md
```

Release result: `released` at `2026-07-30T10:12:31+09:00`.

The dispatcher updated these governed projections:

```text
agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.json
agents/runtime/pane_events/pane-events.jsonl
agents/runtime/a2a/messages.jsonl
```

The claim now records this independent verifier, role, and evidence path.
Pane events gained the release event plus two additive review-pass dispatches;
the A2A stream gained the review, decision, and correction chain.

Active closeout role routing also generated two additive review claims, each
with its claim, handoff, and log record:

```text
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-independent-auditor-closeout.json
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-independent-auditor-closeout.handoff.md
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-independent-auditor-closeout.log.md
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-skeptic-closeout.json
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-skeptic-closeout.handoff.md
agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-654-skeptic-closeout.log.md
```

The integrator added these six additive records to the declared lifecycle
footprint and released both overlay claims at
`2026-07-30T10:14:27+09:00`, using this independent approval as evidence.
The overlay release path does not recursively create more review claims.
No generated claim was deleted or bypassed.
