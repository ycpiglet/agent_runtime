---
title: Allimbot Agent Runtime v0.8 Green Pilot — Attempt 1
date: 2026-07-30
task_id: TASK-AR-649
unit_id: UNIT-TASK-AR-649-001
pilot_id: allimbot-v080-green-attempt-1
signal: pass
runtime_verdict: APPROVE
product_security_verdict: REVISE
runtime_finding_counts: {P0: 0, P1: 0, P2: 6}
product_finding_counts: {P0: 0, P1: 1, P2: 1}
---

# Allimbot Agent Runtime v0.8 Green Pilot — Attempt 1

## Bottom line

The Runtime pilot passes. Exact Runtime product `4929415d` adopted
`core+security-service` into a clean disposable Allimbot checkout, completed
three independently approved local traces, preserved every pre-existing
tracked product byte, and produced no external effect.

This is not an Allimbot product-security approval. The independent auth review
found one product P1: a broad GitHub OAuth bearer token is copied into the
browser-visible session. That issue was intentionally not edited in this
read-only pilot.

## Exact boundary

| Surface | Exact baseline | Result |
| --- | --- | --- |
| Runtime product | `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` | detached checkout clean |
| Runtime product tree | `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f` | pinned |
| Runtime template tree | `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f` | pinned |
| Runtime template scripts tree | `62311b7847f66206a2a33e4bd497750bf074384f` | pinned |
| Allimbot target/control | `5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd` | HEAD unchanged |
| Allimbot live primary | same commit, pre-existing dirty state | observation-only and unchanged |
| Consumer commits/pushes | none authorized | `0 / 0` |

Only the disposable target was an observed write checkout. The frozen control,
live Allimbot primary, Bean attempt 6 and control, Bean primary, Autofolio
primary, and detached Runtime product all matched their before snapshots.

## Adoption result

- Profiles: `core`, `security-service`
- Selected template files: `251`
- Ownership: `242 managed`, `7 seed_once`, `2 host_owned`
- Initial plan: `249 safe`, `2 excluded`, `0 conflicts`
- Safe apply: `249 applied`
- Immediate, post-registration, and final reconcile:
  `0 safe`, `249 preserved`, `2 excluded`, `0 conflicts`
- Lock: `agent-runtime-lock/v2`, package `0.7.0`, current and passing
- Doctor: `0 blockers`, `8 warnings`, `5 infos`
- Security-service gate: `9 classifications`, `0 findings`

The host-owned exclusions were `.env.example` and `.gitattributes`.
All 12 declared host assets, 26 auth/security files, and all 276 tracked
Allimbot files retained their exact baseline digests. The complete tracked
manifest remained
`9de6a8dd96f406540e39fec941507b5a8940001d42cf9e06c90a39150d8d1791`.

## Three bounded traces

### TASK-AR-301 — ordinary adoption

- Requested and selected tier: `worker_low`
- Resolved policy alias: `haiku`
- Actual provider/model, usage, cost, and savings: unavailable
- Result: completed and independently approved
- All adoption, continuity, isolation, and preservation checks passed

### TASK-AR-302 — selective Critical security review

- Requested tier: `worker_standard`
- Selected tier: `planner_high`, due to security, data-integrity,
  external-effect, and cross-cutting triggers
- Resolved policy alias: `opus`
- Actual provider/model, usage, cost, and savings: unavailable
- Exactly one independent reviewer wrote exactly one bounded review artifact
- Runtime verdict: `APPROVE — P0 0 / P1 0 / P2 1`
- Allimbot product verdict: `REVISE — P0 0 / P1 1 / P2 1`

The product P1 is in `console/auth.js`: GitHub `repo` scope is requested, the
provider access token is copied through the JWT, and `session.accessToken`
exposes it to the browser session. Move repository access fully server-side,
remove the browser session token, and narrow the OAuth scope before broader
use. The product P2 is the documented deployment-wide
`ALLIMBOT_SECRETS_KEY`; public multi-user launch still needs KMS/envelope
separation.

### TASK-AR-303 — local event and restart recovery

- Requested and selected tier: `worker_low`
- One allowlisted `task.state.changed` event entered only a private SQLite
  spool; one unsafe event was rejected before enqueue
- Final spool count: `1`; flushes, workers, and network calls: `0`
- Distinct writer and reader processes recovered the same task and claim
- One task-linked Compound record was retrieved first at score `180`
- Scribe projection was fresh and ready; the configured host status source
  stayed byte-identical
- Result: completed and independently approved

## Isolation and strict acceptance

- Raw physical-isolation SHA-256:
  `c812105c2849593ca4142ccb88de1471b2235167a44c6b9e6ca45b565bf660be`
- Raw isolation: `0 blockers / 0 watches`
- Portable isolation semantic SHA-256:
  `6434415de42ef0e53f2e0e4367df3aa5da4626b9ac05d3ab7b982e3b85fa4e5c`
- Exact evidence semantic SHA-256:
  `5e5a5b904cb9572c3ec101fe3721754fa5fa7a045ffcb8c04309bab81b569bdf`
- Strict contract:
  `allimbot:allimbot-v080-green-attempt-1`, `0 findings`
- Historical Bean attempt-6 strict contract: unchanged and passing

## Verification

| Check | Result |
| --- | --- |
| Allimbot Python suite | `388 passed, 1 skipped, 121 subtests passed` |
| Runtime pilot/isolation/Allimbot/security tests | `162 passed` |
| Runtime claim/state/continuity/Owner/adoption/config tests | `285 passed` |
| state sync, continuity, RBAC, taskset, security-service, Owner governance | pass, no blocker |
| template mirror | `84 expected`, `81 identical`, `3 intentional`, `0 findings` |
| Runtime asset usage | `0 blockers / 0 watches` |
| public sanitization | `0 findings` |

The Allimbot web suite was not run: the clean target had no installed
JavaScript dependencies, and dependency installation was prohibited. The first
plain Python test command also lacked `PYTHONPATH=src` and failed during import
collection; the corrected no-install command produced the passing result above.

## Runtime findings and next-release work

The pilot has no Runtime P0/P1 defect, but it exposed six Runtime P2 gaps that
should be treated as high-priority release work because they recur across
hosts:

1. Taskset registration has no canonical sequence/dependency semantics.
   Scoring selected TASK-AR-303 ahead of the mandatory Critical TASK-AR-302
   until local metadata was repaired.
2. Releasing a taskset-created claim does not terminalize its phase and
   progress. The completion gate required a deterministic manual projection to
   `taskset-completed / 100%`.
3. TASK-level descriptive verification bullets were executed as shell
   commands. The failed canonical record was preserved, then the task was
   repaired with the same eight executable commands already used by its unit.
4. The no-install security-service runner needs the pinned Runtime source on
   `PYTHONPATH`; an installed-package consumer smoke is still missing.
5. Routing records policy aliases, not observed provider/model usage. Doctor
   also shows tier equivalence groups, so token/cost savings cannot currently
   be proved.
6. The status Scribe adapter classified 42 ordinary prose bullets as hot
   items. Freshness works, but prioritization needs host-aware item semantics.
The missing dependency-preserving web-test path is an additional consumer
verification P2.

One additional diagnostic was intentionally not counted as a pilot finding:
broad collaboration governance requires CALL/MEETING/RESEARCH/RETRO/SEMINAR
artifacts even though this host selected only core plus security-service.
Capability-aware gate applicability should be addressed, but the gate was
outside this profile's acceptance surface.

## Priority order before an RC

1. Encode canonical taskset dependencies/order and add a regression where a
   mandatory Critical task cannot be skipped by cost scoring.
2. Make claim release/task completion/taskset projection an atomic supported
   lifecycle operation; remove manual JSON repair from the green path.
3. Make Work registration reject or preserve descriptive verification as
   non-executable text; only explicit command fields may reach `work verify`.
4. Add installed-wheel clean-host smokes for `core`, `web-content`, and
   `security-service`, including the security gate and JS-suite
   available/unavailable distinction.
5. Add actual model/provider/token/cost observation and make collapsed tier
   mappings loud; do not claim savings from aliases.
6. Add configurable Scribe classifiers and capability-aware governance.
7. Rehearse Autofolio v0.6-to-v0.8 migration, then assemble the RC with exact
   tag-install and browser smoke. Tag, push, publish, deploy, and release remain
   Owner-gated.

## External-effect ledger

Publish, deploy, origin push, host commit, consumer commit, credential read,
network delivery, package install, provider-live call, content/product
mutation, migration, and spool flush were all integer zero.
