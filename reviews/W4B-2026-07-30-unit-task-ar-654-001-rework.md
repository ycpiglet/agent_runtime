# UNIT-TASK-AR-654-001 Independent W4b Review

- verdict: `REWORK`
- verified_at: `2026-07-30T09:46:32+09:00`
- verified_by: `qa-20260730-094300-task-ar-654-w4b`
- verifier_role: `qa-reviewer`
- claim_id: `CLAIM-20260730-092200-task-ar-654-host-gates`
- branch: `codex/unit-task-ar-654-001-host-required-gates`
- implementation_commit: `898adcdc`
- reviewed_head: `90eac129`
- worker_evidence: `reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730094218.json`

## Decision

W4b requires rework. The recorded verification suite is green and the
implementation commit stays inside its declared seven-file footprint, but the
new enforcement boundary can still be bypassed by changing the command
implementation on the worker branch. A separate launch-error path also leaves
the queue entry stuck without actionable feedback. The claim must remain
unreleased until both blockers are corrected and independently rechecked.

## Blocking Findings

### B1 — A worker can weaken the required gate implementation and still merge

The policy text and command string are read from the integration base, but the
command runs against executables, package scripts, configuration, and tests
from worker `HEAD`. The queue protects only
`agents/host/MERGE-GATES.json`. It does not protect the files that give the
required command its behavior.

Independent adversarial reproduction:

1. Base policy command: `python gate.py`.
2. Base `gate.py` exits `3`.
3. Worker branch changes `gate.py` to exit `0` and adds `product.txt`.
4. The queue runs the worker's weakened gate and merges both files.

Observed result:

```text
enqueue_rc=0
process_rc=0
required gate: contract: python gate.py
status=merged
product_merged=True
gate_now=raise SystemExit(0)
```

This affects the Bean Wiki vertical slice directly. Its base-owned commands
are `npm run design:check` and `npm run design:visual`, while the worker branch
can currently change `package.json`, the Node gate scripts, Playwright config,
visual test, or baselines. Those paths trigger the gate but are not immutable;
triggering a worker-controlled command does not prove the original gate still
exists. Bean Wiki's CODEOWNERS file explicitly says required Code Owner
approval is disabled, so it is not an independent blocking boundary.

Required correction: extend the base-owned policy with enforced
`protected_paths` / `trusted_paths` integrity, or execute a trusted
base-materialized runner with equivalent integrity. The Bean policy must bind
the launchers and verification definitions needed by each command. Any
owner-approved change to those paths needs a separate, explicit policy/baseline
update lane rather than silently weakening its own W5 check.

### B2 — A missing gate executable wedges the queue without feedback

`_run_argv()` lets `OSError` / `FileNotFoundError` escape. `process_entry()`
only translates `CommandTimedOut`. A missing required executable therefore
prints a traceback, leaves the entry in `testing`, and writes no feedback.

Observed result:

```text
enqueue_rc=0
process_rc=1
exception=FileNotFoundError
entry.status=testing
entry.failure_reason=""
feedback_exists=False
head=main
main_has_worker_file=False
```

The integration branch remains unchanged, but this violates the registered
acceptance that required-gate failures produce actionable feedback and a
terminal failed entry. Treat command launch failures as required-gate failures,
restore the worktree, mark the entry `failed`, and include the gate ID and
sanitized launch error in feedback.

## Additional Correctness Findings

### M1 — Dry-run is not faithful for a custom local integration branch

Dry-run always reads policy and computes diffs from `args.base`. Real local
processing reads policy from `ctx.rebase_target`, which is the custom
integration branch.

With `origin/main` carrying `base-policy` and local `staging` carrying
`staging-policy`, the same entry produced:

```text
dry_run_rc=0
dry_run_required=[base-policy]
real_process_rc=2
real_process=required-gate policy drift
```

Dry-run should resolve the same effective rebase target as real processing
without mutating the checkout.

### M2 — Invalid UTF-8 policy content escapes as a traceback

`load_merge_gate_policy()` catches `OSError` but not `UnicodeError`. Invalid
bytes leave queue state untouched, but produce an uncaught
`UnicodeDecodeError` instead of the normal actionable merge-queue error.

Observed result:

```text
enqueue_rc=1
exception=UnicodeDecodeError
queue_exists=False
```

Catch decoding errors and report the policy as unreadable/invalid.

## Bean Policy Compatibility

The Bean policy at
`agents/host/MERGE-GATES.json` is syntactically compatible with the Runtime
schema:

- schema is `agent-runtime-merge-gates/v1`;
- gate IDs `design-contract` and `design-visual` satisfy the Runtime ID rule;
- commands contain no unsupported placeholders;
- repository-relative include/exclude patterns normalize successfully;
- `src/app/api/**` is excluded from the visual gate as intended.

The schema-level compatibility does not resolve B1 because command behavior
still comes from worker-controlled files.

## Recorded Verification Commands

```text
python -m pytest tests/test_merge_queue.py -q
# PASS: 32 passed in 14.85s

cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
# PASS

cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
# PASS

python scripts/regen_host_lock_if_needed.py --check
# PASS: fixture lock is up to date
```

Additional compatibility checks:

```text
python -m pytest tests/test_template_smoke.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_runtime_asset_usage.py -q
# PASS: 38 passed in 15.45s

python -m py_compile scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
# PASS

git diff --check 6c648f0a...898adcdc
# PASS
```

Adversarial commands run:

```text
python -c 'import runpy,tempfile,json; from pathlib import Path; ns=runpy.run_path("tests/test_merge_queue.py"); td=tempfile.TemporaryDirectory(); work=ns["_make_repos"](Path(td.name)); ns["_write_policy"](work,[{"id":"missing","command":"definitely-no-such-gate-executable"}]); ns["_make_branch"](work,"feat/missing-gate","src/missing.txt"); e=ns["_run_mq"](work,"enqueue","--branch","feat/missing-gate","--task-id","TASK-MISSING","--verify",ns["PASS_VERIFY"]); p=ns["_run_mq"](work,"process","--all","--regen-cmd",ns["REGEN_CMD"]); q=ns["_queue"](work); print(json.dumps({"enqueue_rc":e.returncode,"process_rc":p.returncode,"stdout":p.stdout,"stderr_tail":p.stderr[-1200:],"entry":q["entries"][0],"head":ns["_git"](work,"rev-parse","--abbrev-ref","HEAD"),"main_has_file":(work/"src/missing.txt").exists(),"feedback_exists":(work/"agents/runtime/merge_queue/feedback-feat-missing-gate.md").exists()},indent=2))'

python -c 'import runpy,tempfile,json; from pathlib import Path; ns=runpy.run_path("tests/test_merge_queue.py"); td=tempfile.TemporaryDirectory(); work=ns["_make_repos"](Path(td.name)); p=work/ns["merge_queue_module"].MERGE_GATES_REL; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b"\xff\xfe"); r=ns["_run_mq"](work,"enqueue","--branch","feat/x","--task-id","TASK-X"); print(json.dumps({"rc":r.returncode,"stdout":r.stdout,"stderr_tail":r.stderr[-1000:],"queue_exists":(work/ns["QUEUE_REL"]).exists()},indent=2))'

python -c 'import runpy,tempfile,json; from pathlib import Path; ns=runpy.run_path("tests/test_merge_queue.py"); td=tempfile.TemporaryDirectory(); work=ns["_make_repos"](Path(td.name)); ns["_write_policy"](work,[{"id":"base-policy","command":ns["PASS_VERIFY"]}]); ns["_make_branch"](work,"feat/work","work.txt"); ns["_git"](work,"checkout","-b","staging","main"); ns["_write_policy"](work,[{"id":"staging-policy","command":ns["PASS_VERIFY"]}],commit=False); ns["_git"](work,"add",ns["merge_queue_module"].MERGE_GATES_REL); ns["_git"](work,"commit","-m","staging policy"); ns["_git"](work,"checkout","main"); e=ns["_run_mq"](work,"enqueue","--branch","feat/work","--task-id","TASK-WORK","--verify",ns["PASS_VERIFY"]); d=ns["_run_mq"](work,"process","--all","--dry-run","--integration-branch","staging"); p=ns["_run_mq"](work,"process","--all","--integration-branch","staging"); print(json.dumps({"enqueue_rc":e.returncode,"dry_rc":d.returncode,"dry_stdout":d.stdout,"process_rc":p.returncode,"process_stdout":p.stdout},indent=2))'

python -c 'import runpy,tempfile,json; from pathlib import Path; ns=runpy.run_path("tests/test_merge_queue.py"); td=tempfile.TemporaryDirectory(); work=ns["_make_repos"](Path(td.name)); gate=work/"gate.py"; gate.write_text("raise SystemExit(3)\n",encoding="utf-8"); ns["_git"](work,"add","gate.py"); ns["_git"](work,"commit","-m","add failing base gate"); ns["_git"](work,"push"); ns["_write_policy"](work,[{"id":"contract","command":"python gate.py","include_paths":["**"]}]); ns["_git"](work,"checkout","-b","feat/weaken-gate","main"); gate.write_text("raise SystemExit(0)\n",encoding="utf-8"); (work/"product.txt").write_text("rollback\n",encoding="utf-8"); ns["_git"](work,"add","gate.py","product.txt"); ns["_git"](work,"commit","-m","weaken required gate"); ns["_git"](work,"checkout","main"); e=ns["_run_mq"](work,"enqueue","--branch","feat/weaken-gate","--task-id","TASK-BYPASS","--verify",ns["PASS_VERIFY"]); p=ns["_run_mq"](work,"process","--all","--regen-cmd",ns["REGEN_CMD"]); print(json.dumps({"enqueue_rc":e.returncode,"process_rc":p.returncode,"stdout":p.stdout,"status":ns["_queue"](work)["entries"][0]["status"],"product_merged":(work/"product.txt").exists(),"gate_now":(work/"gate.py").read_text()},indent=2))'
```

## Footprint and Lifecycle Audit

Implementation commit `898adcdc` changes exactly the seven declared target
files. The enforced postverify probe reports:

```text
declared=7 actual=7 undeclared=0
```

W4a commit `90eac129` additionally changes three lifecycle/evidence files not
listed in the claim footprint:

```text
agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
reviews/INDEX.md
reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730094218.json
```

These are normal verification projections, but the current strict footprint
gate reports them as three undeclared files. They should be explicitly covered
by a lifecycle exemption or declared footprint before final release.

The full branch also contains two pre-implementation claim lifecycle lines
with trailing whitespace:

```text
agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.handoff.md:16
agents/runtime/task_claims/CLAIM-20260730-092200-task-ar-654-host-gates.log.md:15
```

No implementation file has a whitespace error.

## Release Gate

W4b approval is not granted for HEAD `90eac129`. The independent verifier did
not release the claim, commit, push, merge, or modify implementation files.
