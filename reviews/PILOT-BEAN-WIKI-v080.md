---
title: Bean Wiki v0.8 Agent Runtime Red Pilot
date: 2026-07-29
status: blocked
signal: fail
verdict: BLOCKED
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-001
runtime_baseline: 4ab35b89023f23c032fc574a12a8679f1ea57d33
host_baseline: 357eee4fd8c29c33a949adbe3a0ffa80c874bf42
fixture: tests/fixtures/pilots/bean-wiki/evidence.json
tags: [pilot, bean-wiki, adoption, compound, scribe, model-routing, red-pilot]
---

# Bean Wiki v0.8 Agent Runtime Red Pilot

## Bottom Line

**BLOCKED — do not release Agent Runtime v0.8 or begin the Allimbot pilot
against this build.**

The disposable Bean Wiki pilot proved that the common Runtime controls are
useful and can preserve the product-specific editorial harness, but it also
reproduced five release-blocking integration defects:

1. a taskset registered by `work.py new` cannot be dispatched;
2. a worker running inside its own clean linked worktree cannot claim it;
3. the installed example unit is classified as a real orphan task;
4. the state-sync gate ignores the configured host state adapter; and
5. a Runtime producer mutates a file that Runtime sync still owns as managed.

This is a successful **red-pilot observation**, not a successful adoption.
The offline fixture is expected to validate as truthful while its top-level
result remains `blocked`. The five P0s must be repaired and this exact pilot
must be replayed green before TASK-AR-649, TASK-AR-650, or the v0.8 release
lane proceeds.

## Safety and Baselines

| Boundary | Result |
| --- | --- |
| Agent Runtime baseline | `4ab35b89023f23c032fc574a12a8679f1ea57d33` |
| Bean Wiki baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean work surface | disposable clean linked worktree |
| Bean consumer commits | 0 |
| Bean origin pushes | 0 |
| Publish / deploy | 0 / 0 |
| Credential reads / network delivery | 0 / 0 |
| Content mutations | 0 |
| Unmapped pilot diffs | 0 |

The dirty primary Agent Runtime and Bean Wiki checkouts were not used as pilot
workspaces and were not modified. The consumer worktree was neither committed
nor pushed. Allimbot and Autofolio were inspected only at their pinned
baselines; no event was enqueued or delivered.

## Adoption Measurement

The actual `core+web-content` projection selected 243 files:

| Measurement | Count |
| --- | ---: |
| Selected template files | 243 |
| Default managed files | 237 |
| Seed files | 6 |
| `web-content` increment over `core` | 0 |
| Initial safe updates | 241 |
| Explicit host-owned exclusions | 2 |
| Initial conflicts | 0 |
| Files applied | 241 |
| Apply duration | 0.15 seconds |
| Immediate post-apply safe updates / conflicts | 0 / 0 |

The v2 lock was written only after the first reconcile settled. It records
schema `agent-runtime-lock/v2` and template digest
`sha256:c2679c1d7698112a11a4f7ada3d5ee18941853a9961f68b161c759549c7a03ef`.

The projection is not yet a credible lightweight `web-content` profile:
adding the profile changes no selected file. This is P1 profile-design work,
not a reason to weaken the five functional P0s.

`doctor` initially found that newly installed runtime directories needed to
be materialized before one help probe could run. `doctor --repair` created the
six required directories; the repeated doctor run then had zero blockers and
eight non-blocking warnings. This bootstrap rough edge should be retained as
P1 follow-up evidence.

## Host Preservation

All 16 declared Bean Wiki host assets were byte-identical before and after
adoption. The fixture contains the individual SHA-256 pairs for:

- `AGENTS.md`, `CLAUDE.md`, and `BACKLOG.md`;
- the editorial operations and editorial SSOT documents;
- the existing `.claude/agents/**` specialists and personas; and
- the existing `.claude/skills/**` article workflows.

The 125 files under `src/content/**` also remained byte-identical, with
aggregate manifest digest
`cb1ba979576e586dabb235c536b8db7675933782d96d12d7f7dd5cf5808fd1eb`.
Unexpected overwrite count was zero.

Bean's read-only gates passed:

```text
npm run check-content     pass; 98 articles, 12 English articles, 12 categories
npm run check:editorial   pass; 17 pre-existing editorial warnings
git diff -- src/content   pass; no diff
git diff --check          pass
```

`build:content` was intentionally not run because it writes
`src/content/articles/index.ts`, while the pilot stop boundary allowed content
reads only. The report does not convert a deliberately skipped mutating gate
into a pass.

## Three Claimed Tasks

| Task | Execution | Routing truth | Result |
| --- | --- | --- | --- |
| `TASK-AR-001` | deterministic adoption and negative fixture | requested/selected `worker_low`; resolved provider tier `haiku`; no observed model or provider usage | blocked by reproduced dispatch/claim defects |
| `TASK-AR-002` | one sequential editorial specialist subagent | requested/selected `worker_standard`; configured provider tier `sonnet`; orchestration requested `gpt-5.6-terra`; actual provider/model unobserved | task scope completed |
| `TASK-AR-003` | two deterministic local processes | requested/selected `worker_low`; resolved provider tier `haiku`; no model call observed | completed |

Every task has a canonical task/unit/claim trace and bounded output references.
The two completed claims were released. The first claim remains honestly
blocked rather than being relabeled as complete.

The editorial specialist rated the read-only `coffee-flavor-wheel.html`
article `REVISE`, 2.5/5. The review found missing or weak editorial-SSOT
coverage for length, section structure, references, quiz, glossary, and
versioned SCA/WCR checks. This was a harness test only; no article content was
edited.

Configured tiers are not execution observations. The Runtime did not expose a
verifiable provider model identifier, input/output token counts, or monetary
cost for these tasks. Consequently all token, cost, and savings claims remain
`unavailable`.

## Compound, Scribe, and Restart

The pilot exercised the common controls rather than merely installing their
files:

- An intentional negative unit fixture reproduced a missing `new:` target
  prefix failure. Compound stored signature
  `defect:worker-ready-unit-target-omits-new-prefix-and-po:8d3fd2fbaebb2789`;
  a later matching lookup returned the record.
- A first process persisted the task, claim, and checkpoint, then exited. A
  distinct second process recovered the same task and claim. The checkpoint
  digest was
  `e63f5da708054d7a350631151e53bf4f625a8dc1c815facae0b2fb252b861603`.
- Scribe produced a fresh, ready, non-blocking projection from an overdue
  source with 74 hot items. `BACKLOG.md` remained byte-identical at
  `c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591`.

These results support a shared Runtime kernel: registered work, claims,
Compound, Scribe, continuity, routing evidence, and verification should not be
rebuilt independently in each product. They do not support copying the whole
current projection unchanged into every repository.

## Release-Blocking Findings

### P0-1 — `registered-taskset-undispatchable`

`work.py new` persists the new taskset in
`agents/project/work-items/TASKSET-DEFINITIONS.json` and its generated plan,
while `taskset_dispatcher` reads the static Python
`backlog_board.TASK_SET_DEFINITIONS` or legacy initiative Markdown. The
successfully registered Bean taskset is therefore unknown to the dispatcher.

**Required repair:** make the canonical work registry the dispatcher's source,
retain an explicit compatibility fallback if needed, and add a
register-then-dispatch integration test.

### P0-2 — `linked-worktree-self-claim-refused`

`task_claim_dispatcher._claim_creation_errors` rejects a claim when the
declared worker worktree equals the invocation root. That condition does not
identify the protected primary checkout; it also rejects the intended clean
linked worktree. The pilot had to use orchestrator mode to continue.

**Required repair:** resolve the actual Git common directory and primary
worktree boundary, permit a clean registered linked worktree to claim itself,
and retain refusal for the protected primary checkout and ambiguous paths.

### P0-3 — `template-example-classified-as-orphan`

The managed template installs
`agents/lead_engineer/tasks/units/examples/UNIT-EXAMPLE-001.md`.
`work_item_classifier` treats it as canonical task `TASK-EXAMPLE`, producing
orphan findings in every adopted host.

**Required repair:** classify the examples namespace as non-canonical sample
material, or move it outside the canonical scanner roots. Add a clean
installed-host classifier test with zero example-derived work items.

### P0-4 — `host-state-runtime-taskset-collision`

`state_sync_gate` hardcodes that `BACKLOG.md` must mention the active Runtime
taskset and requires `STATUS.md`. This contradicts v2
`host.state_adapters`/generated projection ownership and would force Runtime
state into Bean Wiki's host-owned editorial backlog. The pilot correctly
preserved `BACKLOG.md`; the gate then emitted two blockers.

**Required repair:** resolve state paths and projection behavior from v2
configuration. A host-owned adapter source must be read-only, and a configured
generated projection must satisfy Runtime state synchronization without
requiring `STATUS.md`.

### P0-5 — `managed-file-mutated-by-runtime-producer`

After clean adoption, `work.py new` changed `owner-docs.yml`. Reconcile then
reported one conflict because sync/lock still classify that path as managed.
A normal Runtime command therefore creates a divergence from its own managed
template.

**Required repair:** assign generated/host-owned ownership to mutable registry
state, or separate immutable owner policy from generated registrations. Add an
adopt → register work → reconcile test that remains at zero conflicts.

## Pre-GA and Later Findings

P1 work:

- split a genuinely thin common kernel from optional collaboration, UI,
  release, and domain profiles; `web-content` currently adds zero files;
- execute `host.context` and `role_overlay` in session/dispatch context rather
  than only parsing and reporting them;
- make first-run directory materialization deterministic so a clean adoption
  does not require a surprise doctor repair; and
- expose trustworthy provider/model/usage observations if the product is to
  make model-economy claims.

No P2 finding is required to unblock this pilot. UI refinement remains part of
the broader v0.8 program, but it must not displace the five adoption P0s.

## Offline Acceptance

The sanitized fixture contains no article body, credential, or absolute
consumer path. Its validator checks:

- pinned baselines and reconcile arithmetic;
- host/content before-and-after preservation;
- bootstrap and three task/claim traces;
- routing observation truth and unsupported savings refusal;
- Compound retrieval, process restart, and Scribe preservation;
- zero external-effect counters; and
- the rule that a P0 result must remain blocked.

Registered commands:

```text
PYTHONPATH=src python scripts/pilot_acceptance.py --host bean-wiki --check
  pass; findings=0

PYTHONPATH=src python -m pytest tests/test_pilot_acceptance.py -q
  14 passed
```

Here `findings=0` means the evidence document is internally consistent; it
does not erase the seven pilot findings contained in that document.
The validator also pins the fixture's canonical semantic SHA-256 so an
otherwise unrecognized field mutation cannot silently pass.

## Decision and Next Gate

Keep `TASK-AR-648` open. Add a separately claimed remediation unit for the
five P0s, run focused and full Runtime verification, then repeat the Bean Wiki
pilot from a fresh pinned worktree. Green acceptance requires:

1. all five P0 reproducers to pass as regressions;
2. register → dispatch → linked-worktree claim to work without orchestrator
   bypass;
3. installed-host classification and state-sync blockers to be zero;
4. post-registration reconcile conflicts to be zero;
5. host/content preservation and all external-effect counters to remain zero;
   and
6. the offline fixture result to change from `blocked` only after observed
   evidence supports that change.

Only after that green replay may the process continue to the Allimbot pilot,
Autofolio compatibility validation, and v0.8 release candidate.
