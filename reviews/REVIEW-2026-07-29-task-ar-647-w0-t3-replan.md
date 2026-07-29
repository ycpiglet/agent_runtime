---
title: TASK-AR-647 W0 T3 Replan
date: 2026-07-29
task_id: TASK-AR-647
unit_id: UNIT-TASK-AR-647-001
signal: pass
score: 96
priority: P0
tags: [task-ar-647, w0, t3-replan, allimbot, security-service, guardrail]
---

# TASK-AR-647 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-647-001` as one security-sensitive, cross-cutting
unit, but replace the original “compatible local spool fallback” plan with two
strict boundaries:

1. Agent Runtime owns event policy, bounded value validation, call-site
   semantics, profile closure, and fail-open handling.
2. Installed Allimbot owns the only durable spool and every network-delivery
   mechanism.

The unit also turns `security-service` from a notifier bundle into an
enforceable profile: a managed policy classifies secret, auth, migration, and
production-external-effect paths and blocks claim creation when the unit lacks
the required risk metadata or review sections.

Baseline is Agent Runtime `main@d0c31eba` and Allimbot
`origin/main@5a51ed4b6c42b0fea1ac97352209f47ff52f3b52`. Bean Wiki, Allimbot,
Autofolio, and other consumers remain read-only until their registered pilot
or migration tasks. No live event, credential access, spool flush, version
bump, tag, publish, release, or deployment is authorized here.

## T2 Drift

`plan_assumption_gate` reports 27 changed or newly present anchors. Every
finding is explained by completed TASK-AR-646: registration defaults, claim
routing, model resolution, provider/native dispatch telemetry, doctor output,
tests, guidance, and the generated host lock changed after this taskset's
previous snapshot.

The progress is legitimate, but W2 remains blocked because the T0 snapshot no
longer describes the dispatch surface. This review is the T3 replacement.
Re-record taskset anchors only after this review and the amended task/unit
records are present.

## Failure-First Evidence

The registered TASK-AR-647 suite is green:

```text
python -m pytest tests/test_allimbot.py tests/test_notify_routing.py \
  tests/test_owner_governance_consumer_host.py tests/test_doctor.py -q
58 passed
```

Those tests preserve the defect as expected behavior. They assert:

- `ALLIMBOT_URL`, `ALLIMBOT_TOKEN`, `ALLIMBOT_NTFY_TOPIC`, and
  `ALLIMBOT_PROVIDER`;
- direct `POST /trigger`;
- fallback delivery to `https://ntfy.sh`;
- free-form message/title payloads; and
- a GitHub Actions job that reads an ntfy topic secret.

A clean `core` projection has a second defect. The profile excludes
`scripts/allimbot.py`, but `agent_orchestrator.py` imports `allimbot`
unconditionally. With site packages disabled, the clean host fails before its
CLI can start:

```text
python -S <clean-core>/scripts/agent_orchestrator.py --help
ModuleNotFoundError: No module named 'allimbot'
```

Finally, the current `security-service` profile contains only
`scripts/allimbot.py` and a Windows-only `.cmd` stop helper. It contains no
policy, risk classifier, pre-claim check, Owner-gate integration, or doctor
coverage for secrets, auth, migration, or production external effects.

## Current Allimbot Contract

The local Allimbot checkout is on a user branch 20 commits behind
`origin/main`; it was not mutated. Canonical source was inspected from
`origin/main@5a51ed4b`, then verified in a detached temporary worktree:

```text
PYTHONPATH=src python -m pytest tests/test_integrations.py tests/test_client.py \
  tests/test_client_security.py tests/test_event_client_retry.py \
  tests/test_event.py -q
30 passed, 3 subtests passed
```

The current contract is:

- `ProjectIntegration.load()` requires `allimbot.project/v1`, at least one
  event policy, and list-valued metadata allowlists.
- `ProjectEmitter.emit()` rejects an unknown event or non-allowlisted metadata
  before building the event.
- `EventClient.emit()` performs only a local SQLite write and returns the event
  ID. It makes no network request.
- `EventClient.flush()` is the separate delivery boundary. It targets
  `/v1/events`, applies bounded retry/dead-letter behavior, and protects the
  authorization header across redirects.
- `EventClient.from_env()` uses `ALLIMBOT_ENDPOINT`,
  `ALLIMBOT_PROJECT_TOKEN`, `ALLIMBOT_SPOOL_PATH`, and a bounded HTTP timeout,
  or the locally stored account profile when appropriate.

Agent Runtime must never call `flush()`. “Uses `/v1/events`” means that Runtime
produces records for Allimbot's native worker; it does not implement or invoke
the HTTP delivery path itself.

## Exact Event Policy

The managed `.allimbot.json` mirrors Allimbot's current
`integrations/projects/agent-runtime.json`:

| Event | Allowed data |
| --- | --- |
| `attention.required` | `task_id`, `attention_kind`, `owner_role`, `state` |
| `task.state.changed` | `task_id`, `from_state`, `to_state`, `owner_role` |
| `release.gate.failed` | `gate`, `release`, `finding_count` |
| `turn.completed` | `task_id`, `result_state`, `duration_seconds` |

Allimbot validates keys, not the semantic safety of values or free-form
summary/body. Agent Runtime therefore adds the narrower producer policy:

- callers provide event type and structured data only;
- summary text comes from fixed Runtime templates;
- body is always empty;
- identifiers/states/roles/releases/gates are bounded, display-safe values;
- counts and durations are finite, non-negative numbers;
- session/turn correlation is bounded and optional;
- unknown fields, invalid values, or recipe drift raise a policy error before
  the optional dependency is constructed.

Prompts, arbitrary messages, exception text, tracebacks, tokens, endpoint
URLs, provider destinations, environment values, and account data are not
accepted by the producer API.

## Fail-Closed Versus Fail-Open

| Condition | Result |
| --- | --- |
| unknown event or metadata | fail closed: policy error |
| unsafe/unbounded value | fail closed: policy error |
| managed recipe differs from the pinned contract | fail closed: policy error |
| optional Allimbot package missing | fail open: structured `unavailable` |
| Allimbot config/keyring/spool unavailable | fail open: structured `unavailable` |
| local enqueue succeeds | structured `spooled` plus event ID |
| host operation calls an event site | event result never replaces host result |

There is no Runtime-owned JSONL/SQLite fallback. Such a fallback would duplicate
Allimbot's leases, retries, dead-letter rules, schema, state directory, and
security behavior and would inevitably drift.

The documented legacy `notify(message, title, provider)` API remains as a
one-release compatibility signal, but it does not forward any supplied text.
Owned Runtime callers move to the structured API. Compatibility removal or a
hard dependency can be decided only after pilot and release evidence.

## Call-Site Mapping

| Current boundary | Native event | Data policy |
| --- | --- | --- |
| Owner governance block | `attention.required` | fixed attention kind, owner role, blocked state |
| upstream Runtime update | `attention.required` | fixed update kind and available state |
| verified task completion/failure | `task.state.changed` | task ID, bounded prior/next state, role |
| Codex stop/turn boundary | `turn.completed` | task ID/result/duration when known |
| release gate failure | `release.gate.failed` | fixed gate/release/count only |

The template helper remains optional and is loaded lazily so `core` has no hard
dependency. The portable package hook replaces the Windows-only stop helper.
The GitHub Actions direct-ntfy job is removed; an ephemeral CI runner must not
bypass the durable producer boundary.

`notify_routing.py` remains a separate dormant UI/channel-recipe surface. This
unit does not merge its local webhook proposals into Allimbot, enable a
transport, or expose its secret-bearing local configuration.

## Security-Service Enforcement Contract

The profile adds a managed JSON policy and a gate script. `core` excludes both;
`security-service` includes them. The claim dispatcher invokes the gate only
when the profile script exists, preserving zero burden for a clean core host.
Owner governance rechecks active claims so post-claim record drift is visible.

The gate classifies unit `target_files` using managed conservative patterns
plus v2 `host.risk_paths`:

| Risk class | Required unit contract |
| --- | --- |
| secrets | `risk_tier: high|critical`, `security_sensitive: true`, `approval_required: true`, `security`, `## Security Controls` |
| auth | high/critical, security-sensitive, `security` + `data_integrity`, `## Security Controls` |
| migration | high/critical, `data_integrity` + `external_effect`, `## Rollback` |
| production external effect | high/critical, `approval_required: true`, `external_effect`, `## External Effect Boundary` |

Classification records paths and missing requirements, never file contents or
secret values. `host.risk_paths` are treated as production-external-effect
surfaces. Pattern coverage is intentionally conservative; the Allimbot pilot
must add its real auth, migration, and production-effect paths through the
host overlay rather than widening Runtime with product-specific paths.

TASK-AR-646 made `data_integrity` an effective routing signal, but
`schemas/task-unit.schema.json` still omits it. This unit aligns the root and
template schemas because migration/auth classification otherwise cannot
produce a schema-valid unit.

## Profile and Packaging Contract

`security-service` ships:

- managed `.allimbot.json`;
- a thin structured event helper;
- managed `SECURITY-SERVICE-POLICY.json`;
- the security gate; and
- service-profile operating guidance.

The package keeps no mandatory Allimbot dependency. The pilot may install the
trusted local Allimbot checkout into its isolated environment. Adding a public
optional dependency extra is deferred until its distribution source and
version availability are release-verified.

Because `.allimbot.json` is a dotfile, package-data enumeration and clean-wheel
tests must prove it survives older supported setuptools behavior.

Doctor reports only:

- selected profile;
- recipe/gate/policy presence and policy-match status;
- optional dependency availability as a boolean/status code;
- configured environment-variable names as booleans, never values;
- host risk-path count and covered risk classes; and
- stale legacy wiring warnings.

Doctor does not instantiate an emitter, open the spool, read credentials, call
keyring, or probe a network endpoint.

## Scope Amendment

Primary implementation surfaces:

- package event adapter, hook integration, update notice, and doctor;
- package security classifier/gate plus root/template command wrappers;
- root/template claim dispatcher integration;
- exact recipe, service policy, profile manifest, environment example, and
  profile guidance;
- template orchestrator/governance structured call sites;
- task-unit schema alignment;
- removal of direct CI/ntfy and Windows-only stop wiring;
- package-data and clean-profile/clean-wheel verification;
- focused tests and generated host lock refresh.

The Runtime asset registry remains orchestrator-owned during W3. If the new
gate is retained, W5/W6 must register it and regenerate its projections before
closeout.

## Verification

- focused event, security gate, claim dispatcher, doctor, hook, profile,
  governance, update-notify, and dormant-routing tests;
- `python scripts/runtime_asset_usage.py --check`;
- clean `core` host import/CLI smoke with no optional Allimbot;
- clean `core+security-service` host recipe/policy/gate smoke;
- wheel contents include `.allimbot.json` and every profile dependency;
- isolated use of Allimbot `origin/main@5a51ed4b` with a temporary
  `ALLIMBOT_SPOOL_PATH`, proving one local spool record and no network/flush;
- root/template parity where a script is intentionally mirrored;
- `python -m pytest -q`;
- independent W4b against the exact implementation head.

The initial verification typo referenced a nonexistent
`tests/test_security.py`; it was corrected immediately to
`tests/test_client_security.py`. It is command error evidence, not a product
defect.

## Out of Scope

- mutation of Bean Wiki, Allimbot, Autofolio, Tag Manual, or another consumer;
- reading, creating, rotating, or printing a production credential;
- `EventClient.flush()`, `/v1/events` HTTP, direct ntfy, webhook, email, or
  provider delivery;
- a second Runtime spool, retry worker, delivery worker, or channel router;
- live CI notification delivery;
- product-specific security patterns beyond host `risk_paths`;
- Allimbot account/provider/UI/server changes;
- broad `notify_routing.py` redesign;
- version bump, tag, publish, release, or deployment.

## W2 Decision

After this review and refreshed taskset snapshot merge to `main`, dispatch
exactly `UNIT-TASK-AR-647-001`. Keep `worker_standard` as the requested tier,
but its explicit `security`, `data_integrity`, `external_effect`, and
`cross_cutting` signals must visibly select `planner_high`. Claim-time security
validation must pass against the amended unit. Reserve W4b for an independent
agent instance, as required by the repository lifecycle.
