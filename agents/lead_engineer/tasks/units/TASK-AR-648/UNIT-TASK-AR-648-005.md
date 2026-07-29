---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-005
work_uid: 7199137f-8678-45bf-b695-103b8d91a43b
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-005
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-29T20:28:29+09:00
updated_at: 2026-07-29T21:03:30+09:00
started_at: 2026-07-29T20:34:38+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan.md
created_by: codex-root-v080-planner
summary: Seal explicit claim commits to one immutable private-index tree before ref update
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-203438-task-ar-648-648005.json
escalation_triggers:
  - data_integrity
  - security
  - repeated_failure
context: Independent UNIT-004 W4b proved that the child-only transaction marker authorizes claim paths but not the final Git tree. The canonical gate can approve one indexed claim blob, after which a later hook command can replace and stage another blob before Git constructs the commit. This unit replaces that path transaction with a final-content transaction without touching consumer pilots.
inputs:
  - reviews/W4B-2026-07-29-unit-task-ar-648-004.md
  - reviews/W4A-2026-07-29-unit-task-ar-648-004.md
  - reviews/REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan.md
  - agent-runtime@76212dc0c1898c35542cf2838039b5ee88af360f
target_files:
  - scripts/claim_guard.py
  - src/agent_runtime/templates/project/scripts/claim_guard.py
  - tests/test_claim_guard.py
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_task_claim_dispatcher.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - tests/fixtures/host/agent_runtime.lock.json
  - new:reviews/W4A-2026-07-29-unit-task-ar-648-005.md
  - new:reviews/W4B-2026-07-29-unit-task-ar-648-005.md
  - reviews/REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan.md
  - reviews/INDEX.md
scope: Replace only the explicit claim-artifact SCM transaction. Build a private index from the starting HEAD, seal the exact JSON/handoff/log blobs and immutable tree object, run repository commit checks against that private index, revalidate the sealed tree and working blobs after all pre-commit work, create a commit from the immutable tree, and advance the symbolic branch with compare-and-swap. Keep ordinary working-tree claim persistence and overlay behavior unchanged. Do not create a Bean or Allimbot worktree in this unit.
acceptance:
  - The transaction marker binds the exact repository, starting HEAD, private index, sealed tree object, and every authorized artifact path and blob object ID.
  - The private index starts from HEAD and includes only the exact claim JSON, handoff, and log changes; unrelated staged or unstaged work is excluded from the commit.
  - Repository pre-commit checks run against the private index, and the transaction aborts before ref update if any hook changes, adds, removes, or re-stages an authorized artifact or otherwise changes the sealed tree.
  - A hook that changes and stages the claim JSON after the canonical gate reproducer cannot advance HEAD; marker/private-index files are removed and the ordinary gate reports authorized-commit-not-persisted.
  - Handoff-only and log-only mutation or omission fail closed.
  - The final commit tree exactly equals the pre-hook sealed tree, and symbolic HEAD advances by one compare-and-swap update only when the starting HEAD still matches.
  - Detached HEAD, concurrent ref movement, hook failure, malformed/stale/dead-owner/wrong-root/wrong-index/wrong-path/wrong-HEAD/wrong-tree/wrong-blob markers all fail without advancing the claim transaction.
  - Existing unrelated staged, partially staged, unstaged, and untracked user changes retain their exact real-index and working-tree state across both success and failure.
  - On success the three artifacts are clean against HEAD, the claim survives reset plus clean, and the ordinary post-transaction gate has zero block findings.
  - Root/template parity, host lock, focused/full tests, owner governance, and public sanitizer pass at one exact product SHA.
  - A fresh independent W4b approves the exact product SHA before any consumer pilot unit is registered or claimed.
verification:
  - python -m pytest tests/test_claim_guard.py tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py -q
  - python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py -q
  - python scripts/regen_host_lock_if_needed.py --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report the independent red reproducer, sealed marker/tree schema, exact private-index lifecycle, hook execution semantics, success and every fail-closed boundary, real-index preservation hashes, exact product SHA, W4a evidence, and independent W4b verdict.
stop_condition: Stop on a path-only authorization, normal git-commit TOCTOU, post-hoc rollback as the primary integrity control, mutation of unrelated real-index state, hook bypass, detached-HEAD ref write, non-CAS branch update, marker/private-index leak, weakened ordinary claim gate, evidence rewrite, new P0, consumer worktree creation, publish, deploy, push, credential access, or network delivery.
defect_signatures:
  - defect:claim-commit-final-tree-toctou:f39b32eb331a6963
verified_at: 2026-07-29T21:03:30+09:00
verified_by: codex-root-task-ar-648-005
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729210330.json
---

# UNIT-TASK-AR-648-005 - Seal Explicit Claim Commit Trees

## Context

UNIT-004 correctly repaired overlay production and made the explicit commit
exception narrow, but its W4b showed that the exception still described an
approved path at one instant rather than the immutable tree that reaches Git
history. Moving the gate later or adding only a blob field leaves a race with
another index writer.

## Inputs

- `reviews/W4B-2026-07-29-unit-task-ar-648-004.md`
- `reviews/W4A-2026-07-29-unit-task-ar-648-004.md`
- `reviews/REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan.md`
- Agent Runtime product SHA
  `76212dc0c1898c35542cf2838039b5ee88af360f`

## Target Files

- Root/template `claim_guard.py` and `parallel_worktree_gate.py`
- Focused claim-guard, gate, and dispatcher tests
- Root/template parallel worktree protocol
- Derived host lock and W4a/W4b evidence

## Scope

Replace only the explicit claim-artifact SCM transaction. Ordinary
working-tree persistence, overlay routing, consumer adoption, provider
telemetry, and UI behavior are out of scope.

## Transaction Contract

1. Stage the requested artifacts in the real index as today so a failed
   transaction remains visibly recoverable, while preserving all unrelated
   entries.
2. Create a mode-`0600` private index under Git's private runtime directory,
   load the starting `HEAD`, and add only the requested claim artifacts.
3. Record the exact artifact blob IDs and sealed `write-tree` object in a
   child-only, private-record-backed marker.
4. Run the repository's commit checks with `GIT_INDEX_FILE` pointing to the
   private index.
5. After every pre-commit action returns, require the private index tree and
   target working blobs to equal the seal.
6. Create the commit from the already immutable tree object and advance only
   the current symbolic branch using `update-ref <new> <old>`.
7. Clean the marker and private index on every exit. On failure, leave the
   ordinary staged claim state visible so the canonical gate blocks.

## Steps

1. Add deterministic red tests for post-gate JSON, handoff, and log
   substitution and for preservation of unrelated real-index state.
2. Upgrade the marker to bind the private index, artifact blob IDs, starting
   HEAD, and sealed tree.
3. Execute commit checks against the private index and revalidate its complete
   tree plus target working blobs after hook return.
4. Create a commit from the sealed tree and update the symbolic branch with a
   compare-and-swap old value.
5. Add detached-HEAD, ref-race, hook-failure, identity/OID mismatch, cleanup,
   and reset-plus-clean regressions.
6. Mirror root/template assets, regenerate the host lock, and run focused plus
   full W4a.
7. Obtain a fresh independent W4b before registering any consumer replay.

## Acceptance Criteria

- The exact marker, artifact, tree, hook, ref, cleanup, and user-index
  invariants in frontmatter all pass.
- The W4b post-gate substitution cannot advance HEAD.
- Existing overlay and ordinary post-failure claim behavior remains intact.

## Verification

- `python -m pytest tests/test_claim_guard.py tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py -q`
- `python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/owner_governance_gate.py`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check`
- `python -m pytest -q`

## Handoff

Report red/green reproductions, marker and private-index schema, hook
semantics, real-index preservation hashes, exact product SHA, W4a evidence,
and independent W4b verdict.

## Deliberate Exclusions

- Marker OIDs plus hook reordering alone are not called race-free.
- A bad normal commit followed by rollback is not used as the integrity
  boundary.
- Bean Wiki and Allimbot remain outside this unit.

## Stop Boundary

No consumer worktree, release, publish, deploy, push, credential read, network
delivery, ambient marker bypass, mutation of unrelated staged work, or
non-atomic ref update.