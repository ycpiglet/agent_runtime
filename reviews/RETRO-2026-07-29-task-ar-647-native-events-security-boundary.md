---
id: RETRO-2026-07-29-task-ar-647-native-events-security-boundary
title: TASK-AR-647 native-events and security-boundary retrospective
kind: retrospective
status: completed
signal: pass-with-compound
date: 2026-07-29
task_id: TASK-AR-647
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
---

# TASK-AR-647 Native-Events and Security-Boundary Retrospective

## Outcome

TASK-AR-647 replaced Agent Runtime's free-form/direct notification path with a
strict four-event producer boundary and delegated durable enqueue exclusively
to Allimbot's installed `ProjectEmitter`. It also made the
`security-service` profile enforce declared risk metadata before claim
persistence for secret, authentication, migration, and production
external-effect paths.

The final product SHA
`1154b3374f340c50375d1f1916eb0d72d0d1fba4` passed the registered focused
suite at 391 tests, the full suite at 2,548 passed with 3 skipped and 4
pre-existing UI warnings, clean profile and wheel checks, sanitizer and lock
checks, and an isolated pinned-Allimbot spool proof with zero network,
credential, flush, or worker calls. Independent W4b approved 99/100. PR
[#381](https://github.com/ycpiglet/agent_runtime/pull/381) passed Python
3.10, 3.11, and 3.12 and merged as
`66219ba9e321779afc3c6297b9bbf6e936bd1650`; the exact merged SHA passed the
same three-version main workflow.

No production credential or provider destination was read. No spool was
flushed, no live event was delivered, no consumer repository was mutated, and
no version, tag, package publication, deployment, or product release occurred.

## What Worked

- The task pinned the real Allimbot contract at
  `origin/main@5a51ed4b6c42b0fea1ac97352209f47ff52f3b52`, archived that exact source
  into temporary isolation, and proved one local spool record without
  installing a second sender or exercising delivery.
- Policy rejection and environmental unavailability stayed different:
  unknown events, fields, values, recipes, and risky claim metadata fail
  closed, while a missing optional dependency, configuration, or writable
  spool returns a bounded unavailable result without breaking the host action.
- `core` remained dependency-closed without Allimbot; the five managed
  event/security assets are additive only in `core+security-service`.
- Every independent verifier used a distinct instance and attacked adjacent
  states rather than only rerunning the worker's examples. The final review
  bound its verdict to exact product, evidence, and lifecycle SHAs.
- W5 preserved the dirty main checkout and its stash by integrating from
  isolated worktrees and exact remote commits.

## Friction and Corrections

The first W4a evidence was green, but seven independent-review rounds exposed
one recurring defect family across several surfaces:

1. caller-controlled provider-, URL-, prompt-, exception-, role-, correlation-,
   and event-ID-shaped values crossed a boundary that was intended to be
   structured and bounded;
2. missing, substituted, symlinked, narrowed, or unstable unit/gate snapshots
   could erase the canonical registered footprint or the selected profile's
   required gate;
3. malformed host configuration and YAML-like scalar forms were normalized
   into values that could satisfy authorization metadata;
4. a plain-text section search accepted headings hidden inside non-rendered
   Markdown HTML blocks.

Each local fix closed the exact reported example, but fresh adversarial probes
found an adjacent representation of the same trust-boundary mismatch. The
final implementation therefore moved from permissive normalization and
line-matching to exact typed metadata, canonical identity binding, a single
bounded stable regular-file snapshot, installed-gate proof, unioned registered
and claim-snapshot targets, and rendered-semantics-aware Markdown state.

Two lifecycle corrections were also necessary: the registered footprint
initially omitted a directly affected atomic-write test, and descriptive smoke
bullets were initially eligible to be parsed as shell commands. Both records
were corrected before final verification while preserving earlier evidence.

## Durable Rules

1. Authorization and security gates must validate the grammar and semantics
   actually consumed by the downstream renderer or interpreter; substring or
   line-pattern presence is not authorization evidence.
2. Security-relevant frontmatter must use exact types, exact canonical
   identities, duplicate rejection, and fail-closed unsupported syntax. Do not
   normalize malformed values into valid policy inputs.
3. Claim-time decisions must bind one bounded, stable, regular,
   non-symlinked snapshot and union it with the immutable registered
   footprint. A supplied snapshot may add evidence but may not erase risk.
4. A selected profile's required gate must be proven installed and imported
   from the exact worktree/package under test. Missing or substituted gate code
   is a refusal, not a reason to skip.
5. High-risk W4b must probe adjacent representations and negative states after
   each remediation. Replaying only the reported exploit systematically
   underestimates parser and trust-boundary risk.
6. Consumer pilots must preserve this external-effect boundary: enqueue-only
   evidence may use temporary local state, but flush, worker execution,
   production credentials, and live delivery remain outside the pilot.

## Evidence

- W4a:
  `reviews/W4A-2026-07-29-unit-task-ar-647-001-r8.md`
- Independent W4b:
  `reviews/W4B-2026-07-29-unit-task-ar-647-001-r8.md`
- Canonical task verification:
  `reviews/VERIFY-2026-07-29-task-ar-647-20260729140829.json`
- Canonical unit verification:
  `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729140550.json`
- Implementation PR workflow: `30425564243`
- Merged-main workflow: `30425788283`

The main workflow's Node.js action-runtime deprecation messages and
`PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE` warning-summary
annotation were non-blocking annotations; every matrix job completed
successfully.
