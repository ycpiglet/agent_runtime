# TASK-AR-653 Independent Verification

- verdict: `PASS`
- verified_at: `2026-07-30T08:12:56+09:00`
- reverified_at: `2026-07-30T08:26:41+09:00`
- verified_by: `qa-20260730-080600-task-ar-653`
- verifier_role: `qa-reviewer`
- claim_id: `CLAIM-20260730-075500-task-ar-653-merge-queue-safety`
- branch: `codex/unit-task-ar-653-001-wave`
- implementation_commit: `31f8976a`
- correction_commits:
  - `cb4e594b`
  - `542cae75`
- reviewed_head: `462986ac`
- worker_evidence: `reviews/VERIFY-2026-07-30-unit-task-ar-653-001-20260730082201.json`

## Decision

W4b passes for reviewed HEAD `462986ac`. The correction closes all four
previous blockers without touching the reserved TASK-AR-648/TASK-AR-652
implementation scopes. The claim may proceed to release and serial W5
integration after this evidence is preserved by the orchestrator.

## Blocker Revalidation

### B1 — Cross-linked queue union: resolved

Queue and feedback paths now resolve to the primary checkout while the lock
remains under the shared Git common directory. Two enqueue processes invoked
from different linked roots retained both entries in one physical queue.

Independent adversarial result:

```text
returncodes 0 0 0
same_lock True
same_queue True
union ['feat/from-main', 'feat/from-linked']
linked_list_union True
linked_local_queue_exists False
```

A linked-root failure-path run also produced the feedback file in the primary
checkout, left no linked-local feedback copy, marked the shared entry
`failed`, and restored the linked integrator branch.

### B2 — Failed predecessor with unrelated work: resolved

The dynamic dependency check now skips blocked dependents with `continue`
instead of terminating the batch. The failed predecessor and dependent
remained isolated while the unrelated entry merged.

Independent adversarial result:

```text
returncode 1
dependency_skip True
statuses [('TASK-BAD', 'failed'), ('TASK-DEP', 'pending'), ('TASK-INDEP', 'merged')]
independent_merged True
dependent_absent True
```

### B3 — PR dependency semantics: resolved

`pr-handoff` is no longer a dependency-success status. A dependency-bearing
PR-mode batch fails before queue or branch mutation, and a predecessor whose
plain push failed remains `pr-handoff` but cannot satisfy a later dependent.

Dependency-bearing PR-mode result:

```text
returncode 2
fail_closed_message True
queue_unchanged True
main_unchanged True
statuses [('TASK-DEP', 'pending'), ('TASK-PRED', 'pending')]
```

Failed-push predecessor result:

```text
handoff_returncode 0
push_failed_message True
predecessor_status pr-handoff
dependent_returncode 2
unmet_pr_handoff True
main_unchanged True
dependent_absent True
```

### B4 — Host lock freshness: resolved

`tests/fixtures/host/agent_runtime.lock.json` was regenerated in the dedicated
derived-artifact commit `542cae75`. The lock checker and both lock-related
test modules pass.

```text
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

## Scope and Parity

- `cb4e594b` changes exactly the registered implementation/test/documentation
  five-file scope.
- `542cae75` changes only the required generated host lock.
- `462986ac` changes only the unit verification projection, review index, and
  refreshed worker-evidence record.
- Root/template merge-queue scripts are byte-identical.
- Root/template merge-integrator skills are byte-identical.
- No workflow, dispatcher, release, deployment, TASK-AR-648, or TASK-AR-652
  implementation file changed in the correction commits.
- No conflict markers or whitespace errors were found.

## Commands Run

```text
python -m pytest tests/test_merge_queue.py -q
# 22 passed

python scripts/regen_host_lock_if_needed.py --check
# passed

python -m py_compile scripts/merge_queue.py \
  src/agent_runtime/templates/project/scripts/merge_queue.py
# passed

cmp scripts/merge_queue.py \
  src/agent_runtime/templates/project/scripts/merge_queue.py
# passed

cmp skills/merge-integrator/SKILL.md \
  src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
# passed

git diff --check origin/main...HEAD
# passed

python -m pytest tests/test_merge_queue.py tests/test_template_smoke.py \
  tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py -q
# 54 passed
```

Four temporary-repository adversarial harnesses independently exercised:

1. primary + linked-root concurrent enqueue union and linked-root list;
2. linked-root failure feedback and worktree restoration;
3. failed predecessor + dependent + unrelated independent continuation;
4. dependency-bearing PR-mode and failed-push `pr-handoff` rejection.

Their observed outputs are recorded above.

## Non-Blocking Watch

- POSIX locking is directly exercised; the Windows `msvcrt.locking` branch is
  not run by the repository's Ubuntu-only CI matrix.
- The correction now rejects non-finite lock timeout values and falls back to
  the bounded default.
- A predecessor completed through PR handoff cannot later satisfy a newly
  declared dependency because there is intentionally no unverifiable
  handoff-to-merged transition. This is conservative fail-closed behavior;
  dependency-bearing waves must use local serial mode until an explicit
  remote-merge confirmation command is designed.

## Release Gate

W4b approval is granted for HEAD `462986ac`. The verifier did not modify code,
commit this evidence, or execute `task_claim_dispatcher.py release`.
