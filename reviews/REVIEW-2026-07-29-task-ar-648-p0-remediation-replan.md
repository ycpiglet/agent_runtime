---
title: TASK-AR-648 Bean Pilot P0 Remediation Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-002
signal: pass
score: 96
priority: P0
tags: [task-ar-648, t3-replan, bean-wiki, remediation, green-replay]
---

# TASK-AR-648 Bean Pilot P0 Remediation Replan

## Bottom Line

The red pilot is complete and valid. Do not rerun it unchanged and do not
start Allimbot or release work yet. Repair the five independently verified
P0 defects in Agent Runtime, prove each with a focused regression, and then
repeat Bean Wiki adoption from a fresh pinned worktree.

This is a remediation amendment to
`reviews/REVIEW-2026-07-29-task-ar-648-w0-t3-replan.md`. The original report
and fixture remain the immutable red baseline. A green replay must be stored
as a distinct result and must not erase the evidence that caused these
repairs.

## Integrated Baseline

| Surface | Exact baseline | State |
| --- | --- | --- |
| Agent Runtime | `main@ec08a3d8c2a6613f508f1d9fd3f2f67693b4a92b` | PR #384 merged; exact-main Python 3.10/3.11/3.12 CI passed |
| Bean Wiki | `origin/main@357eee4fd8c29c33a949adbe3a0ffa80c874bf42` | clean disposable replay only |
| Red evidence | `reviews/PILOT-BEAN-WIKI-v080.md` | independently approved, P0 count 5 |
| Red fixture | `tests/fixtures/pilots/bean-wiki/evidence.json` | semantic digest pinned and tamper-tested |

Dirty primary checkouts remain excluded. The implementation branch and the
fresh Bean replay must both start from clean, explicit baselines.

## Repair Matrix

| P0 | Root cause | Narrow repair | Required negative guard |
| --- | --- | --- | --- |
| registered-taskset-undispatchable | `work.py new` writes `TASKSET-DEFINITIONS.json`; dispatch reads static Python or legacy Markdown | make the JSON registry the canonical dispatch source; keep compatibility fallback explicit | malformed/duplicate registry rows fail closed; legacy alias behavior remains |
| linked-worktree-self-claim-refused | equality with invocation root is treated as proof of primary checkout | derive Git common dir and actual primary worktree; allow a clean linked worktree to claim itself | primary checkout, missing marker, unrelated path, and ambiguous Git result remain blocked |
| template-example-classified-as-orphan | canonical scanner includes `units/examples/UNIT-EXAMPLE-001.md` | exclude the examples namespace from canonical units in source and template | a real canonical orphan outside examples still reports a finding |
| host-state-runtime-taskset-collision | state sync hardcodes `BACKLOG.md` and `STATUS.md` | honor v2 adapters and generated projection; keep configured sources read-only | missing/stale projection and invalid config block; legacy unconfigured behavior remains |
| managed-file-mutated-by-runtime-producer | `owner-docs.yml` is managed even though `work.py new` appends registrations | classify it as `seed_once` mutable registry state and keep the initial schema seed | package still seeds it once; later host mutation is preserved and does not disappear from lock evidence |

## Why One Unit

The code changes are separable, but their release claim is not. The consumer
only becomes usable when registration, dispatch, claim, classification,
state, and reconcile all succeed in the same adopted worktree. One claimed
unit keeps the green replay attributable to one exact repair head and avoids
five partial branches each claiming adoption success.

Implementation may still use selective reviewers or bounded subagents per
seam. They must share no files, report exact diffs, and never merge or push
independently. Final W4b reviews the integrated head.

## Source and Template Parity

The following executable pairs are product surfaces, not generated copies to
be updated later:

- `scripts/taskset_dispatcher.py` and its packaged-template copy;
- `scripts/task_claim_dispatcher.py` and its packaged-template copy;
- `scripts/work_item_classifier.py` and its packaged-template copy; and
- `scripts/state_sync_gate.py` and its packaged-template copy.

Tests must execute installed-host behavior, not only repository-root imports.
Any intentional source/template difference must be explained and bounded;
silent drift is a blocker.

## State Contract

For a v2 host with explicit `host.state_adapters`:

1. adapter files are host-owned or seed-once sources and are read-only;
2. `host.state_projection` is generated Runtime state;
3. state sync validates canonical tasks, claims, pointer identity, Runtime's
   generated board, adapter availability, and projection freshness;
4. it does not require Runtime task IDs inside host-owned editorial state; and
5. it does not invent `STATUS.md` when the host did not configure it.

For a v1 or unconfigured host, the current legacy surfaces remain the
compatibility contract. This amendment does not silently remove their checks.

## Ownership Contract

`owner-docs.yml` is a schema seed plus a Runtime-producer-updated registry.
`seed_once` matches that lifecycle:

- adoption installs the empty canonical schema when the host has no file;
- an existing host file is preserved;
- `work.py new` may append a review path;
- the v2 lock records the seed classification; and
- later reconcile preserves the mutation instead of reporting it as a managed
  template conflict.

Changing all owner documentation to generated or host-owned is broader than
the observed defect and is not authorized here.

## Green Replay

After focused and full tests pass, create a new Bean worktree rather than
reusing the red-pilot directory. Repeat:

1. baseline and host-asset hashing;
2. v2 config/context/role overlay bootstrap;
3. pre-adoption doctor, plan, reconcile, safe apply, and lock;
4. `work.py new` registration followed by taskset plan;
5. linked-worktree self-claim without orchestrator bypass;
6. classifier check with no example-derived records;
7. Scribe projection write and state-sync check without host backlog mutation;
8. post-registration reconcile with zero conflicts;
9. Bean content/editorial checks allowed by the non-mutating boundary; and
10. sanitized evidence validation and adversarial tamper tests.

The replay may reuse the same read-only article and deterministic process
scenarios, but every trace must carry the new Runtime head and new replay
identity. No result may be copied forward merely because the red pilot once
observed it.

## Acceptance Gate

Release-blocking acceptance requires all of the following:

- five focused reproducer tests pass;
- focused package/template tests pass;
- the full suite passes;
- fresh replay P0 count is zero;
- unexpected overwrite and reconcile conflict counts are zero;
- preserved host/content digests match;
- publish, deploy, push, commit, credential, and network counters are zero;
- model/token/cost fields remain observationally honest;
- independent W4b approves the exact integrated repair head; and
- PR plus exact-main CI pass.

If the replay finds another P0, stop and append a new remediation unit. Do not
proceed to Allimbot or `TASK-AR-651`.

## Deferred P1 Work

This unit deliberately does not:

- thin the 243-file core projection;
- make `web-content` contribute a specialized asset;
- execute host context or role overlay in dispatch/session context;
- redesign first-run directory materialization; or
- add provider token/cost telemetry.

Those are real findings, but mixing them into the release-blocking repair
would make the safety proof harder to audit.

## Verification

```text
python -m pytest tests/test_taskset_dispatcher.py tests/test_work_registration.py \
  tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py \
  tests/test_state_sync_gate.py -q
python -m pytest tests/test_adoption.py tests/test_config_v2.py \
  tests/test_inventory_sync_sanitize.py -q
python -m pytest tests/test_template_smoke.py tests/test_pilot_acceptance.py -q
python scripts/pilot_acceptance.py --host bean-wiki --check
python scripts/owner_governance_gate.py
PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
python -m pytest -q
```

## Stop Boundary

Stop before live publication, deployment, origin push, Bean commit,
credential access, event delivery, article mutation, dirty primary-checkout
mutation, force push, version/tag/package release, weakened fail-closed guard,
or unsupported green/model/cost claim.
