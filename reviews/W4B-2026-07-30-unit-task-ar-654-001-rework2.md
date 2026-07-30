# UNIT-TASK-AR-654-001 Independent W4b Review — Round 2

- verdict: `REWORK`
- verified_at: `2026-07-30T09:58:00+09:00`
- verified_by: `qa-20260730-094300-task-ar-654-w4b`
- verifier_role: `qa-reviewer`
- claim_id: `CLAIM-20260730-092200-task-ar-654-host-gates`
- branch: `codex/unit-task-ar-654-001-host-required-gates`
- implementation_commit: `fc5df6e7`
- correction_commit: `0af60f59`
- reviewed_head: `c94a9fa6`
- worker_evidence: `reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730095331.json`
- prior_review: `reviews/W4B-2026-07-30-unit-task-ar-654-001-rework.md`

## Decision

The four round-1 blockers requested for direct revalidation are corrected:
protected gate implementations fail closed, missing executables produce a
terminal failed entry and feedback, invalid UTF-8 is actionable, and the
custom integration-branch dry-run agrees with real processing.

W4b nevertheless remains `REWORK` because two additional compatibility/parity
counterexamples and one generated-host regression remain. The claim must not
be released at reviewed HEAD `c94a9fa6`.

## Round-1 Blocker Revalidation

### Protected gate implementation mutation — resolved

The same adversarial branch changed a base `gate.py` from exit `3` to exit `0`
and added a product rollback. With `gate.py` in `protected_paths`, processing
now produced:

```text
enqueue_rc=0
process_rc=1
entry.status=failed
reason=required-gate-protected-path-modified: ... gate.py
main_unchanged=True
product_merged=False
gate_restored=True
```

### Missing executable — resolved

```text
enqueue_rc=0
process_rc=1
traceback=False
entry.status=failed
reason=required-gate-launch-failed:missing: ...
feedback_exists=True
feedback_has_reason=True
main_unchanged=True
worker_file_absent=True
```

### Invalid UTF-8 policy — resolved

```text
enqueue_rc=2
traceback=False
queue_exists=False
message=agents/host/MERGE-GATES.json: unreadable (...)
```

### Custom integration-branch dry-run — resolved for the reported case

With `origin/main` carrying `base-policy` and existing local `staging`
carrying `staging-policy`, dry-run and real processing now agree:

```text
dry_run_rc=2
real_process_rc=2
reason=required-gate policy drift
dry_run_queue_unchanged=True
```

## Remaining Blocking Findings

### B1 — Empty gate list can still change legacy behavior

The plan and merge-integrator skill promise that absence **or an empty gate
list** preserves legacy behavior. The normalized policy retains
`protected_paths` even when `gates` is empty, and processing enforces those
paths despite having no bound required gates.

Independent reproduction:

1. Base policy:
   `{"schema":"agent-runtime-merge-gates/v1","protected_paths":["foo.txt"],"gates":[]}`
2. Worker performs a normal change to `foo.txt`.
3. Enqueue creates the legacy entry shape with no policy digest.
4. Process marks it failed for modifying a protected path.

Observed result:

```text
enqueue_rc=0
entry_has_binding=False
process_rc=1
entry.status=failed
reason=required-gate-protected-path-modified: ... foo.txt
```

Required correction: apply protected-path integrity only when the normalized
policy has nonempty gates, or canonicalize/reject `protected_paths` for an
empty policy. Add a regression proving an empty gate list retains the legacy
entry and processing behavior.

### B2 — Dry-run is stale when the local integration branch is behind base

Dry-run selects any existing local integration branch as `policy_ref`.
Real processing first fast-forwards that branch to `args.base`. When local
`main` is behind an already-known `origin/main`, the two operations therefore
inspect different policies.

Observed result:

```text
local main at enqueue=base-policy
origin/main before dry-run=updated-policy
dry_run_rc=0
dry_run_required=[base-policy]
real_process_rc=2
real_process=required-gate policy drift
```

Required correction: resolve the read-only equivalent of the actual
fast-forward:

- use `args.base` when the local integration branch is an ancestor of base;
- use the integration branch when it contains base;
- report divergence when neither is an ancestor;
- preserve the existing fallback to base when the branch does not exist.

### B3 — The packaged skill introduces a missing template dependency

The new merge-integrator example names `scripts/design-contract.mjs`, which is
not shipped in the generated host template. The runtime asset scanner treats
that literal as a dependency and blocks a clean generated host.

Exact compatibility command:

```text
python -m pytest tests/test_template_smoke.py tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_runtime_asset_usage.py -q
```

Observed result:

```text
1 failed, 37 passed
block dependency-missing scripts/design-contract.mjs:
referenced by skills/merge-integrator/SKILL.md is absent from template
```

Required correction: use an actually shipped template path in the example or
word the host-specific placeholder so it is not registered as a concrete
runtime dependency. Regenerate the host lock and rerun this suite.

## Bean Wiki Policy Audit

Runtime normalization succeeds for:

`/home/keti-itp-01/ycpiglet/.integration-worktrees/bean-wiki-design-gates-20260730/agents/host/MERGE-GATES.json`

```text
schema=agent-runtime-merge-gates/v1
digest=8d8d601000364110f7af9755451d27bbacbae6f8c1762bbefecd45a106c99975
gate_ids=[design-contract, design-visual]
protected_count=13
```

The Bean validator's required control-file set and the configured Runtime
policy are exact:

```text
validatorErrors=[]
requiredCount=13
configuredCount=13
missing=[]
extra=[]
```

The protected closure covers:

- policy, CODEOWNERS, and GitHub CI workflow;
- `package.json` and `package-lock.json`;
- Playwright configuration, visual spec, and approved screenshots;
- design-token generator, contract checker, and shared validation library;
- palette checker and both contract/palette test files.

Mutable palette, CSS, components, pages, and content remain subjects under
test rather than gate-control implementations. Bean policy compatibility and
control-file coverage pass this W4b round.

Commands used:

```text
python -c 'import json; from pathlib import Path; from scripts import merge_queue as mq; p=Path("/home/keti-itp-01/ycpiglet/.integration-worktrees/bean-wiki-design-gates-20260730/agents/host/MERGE-GATES.json"); policy=mq.normalize_merge_gate_policy(json.loads(p.read_text(encoding="utf-8"))); print(json.dumps({"schema":policy["schema"],"digest":mq.merge_gate_policy_digest(policy),"gate_ids":[g["id"] for g in policy["gates"]],"protected_count":len(policy["protected_paths"]),"protected_paths":policy["protected_paths"]},indent=2))'

node --input-type=module -e 'import {readFileSync} from "node:fs"; import {REQUIRED_PROTECTED_PATHS,validateMergeGatePolicy} from "./scripts/lib/design-tokens.mjs"; const policy=JSON.parse(readFileSync("agents/host/MERGE-GATES.json","utf8")); const configured=new Set(policy.protected_paths); const missing=REQUIRED_PROTECTED_PATHS.filter((path)=>!configured.has(path)); const extra=policy.protected_paths.filter((path)=>!REQUIRED_PROTECTED_PATHS.includes(path)); console.log(JSON.stringify({validatorErrors:validateMergeGatePolicy(policy).errors,requiredCount:REQUIRED_PROTECTED_PATHS.length,configuredCount:configured.size,missing,extra},null,2)); if(missing.length||validateMergeGatePolicy(policy).errors.length) process.exit(1)'
```

## Recorded Verification

```text
python -m pytest tests/test_merge_queue.py -q
# PASS: 37 passed in 13.79s

cmp scripts/merge_queue.py src/agent_runtime/templates/project/scripts/merge_queue.py
# PASS

cmp skills/merge-integrator/SKILL.md src/agent_runtime/templates/project/skills/merge-integrator/SKILL.md
# PASS

python scripts/regen_host_lock_if_needed.py --check
# PASS: fixture lock is up to date
```

The four adversarial cases were executed independently through temporary bare
origin/clone repositories using the same `runpy.run_path("tests/test_merge_queue.py")`
harness recorded verbatim in the prior review. Round 2 added the empty-policy
and behind-base dry-run counterexamples described above.

## Footprint and Lifecycle

The functional correction remains within the seven declared implementation
targets. Correction commit `0af60f59` also absorbs the prior requested W4b
evidence and regenerates its review index:

```text
reviews/W4B-2026-07-30-unit-task-ar-654-001-rework.md
reviews/INDEX.md
```

Worker re-verification commit `c94a9fa6` adds or changes:

```text
agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
reviews/INDEX.md
reviews/VERIFY-2026-07-30-unit-task-ar-654-001-20260730095331.json
```

These are lifecycle/evidence writes outside the declared implementation
footprint. They are expected in W4/W4b but must be included in the final
lifecycle projection or a documented lifecycle exemption.

The two pre-existing claim handoff/log `stop_condition` lines still contain
trailing whitespace. No implementation diff has a whitespace error.

## Release Gate

W4b approval is not granted for HEAD `c94a9fa6`. No claim release, bypass,
implementation edit, commit, push, or merge was performed.
