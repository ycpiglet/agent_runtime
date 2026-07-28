---
title: TASK-AR-646 W0 T3 Replan
date: 2026-07-29
signal: pass
score: 96
priority: P0
tags: [task-ar-646, w0, t3-replan, model-routing, subagents, telemetry, codex]
---

# TASK-AR-646 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-646-001` as one cross-cutting implementation unit,
but replace the original label-only routing scope with an execution-truth
contract.

The unit will:

1. default newly registered, precise routine units to `worker_low`;
2. resolve provider-neutral PM tiers into provider-specific models and
   reasoning effort without treating semantic labels as proof;
3. make equivalent tier mappings visibly ineffective;
4. require deterministic preflight evidence before delegating lookup-only work;
5. carry exact native Codex spawn arguments through the session bridge;
6. record the observed model, token availability, latency, and cost
   availability at the real provider/native completion boundaries;
7. exclude unresolved or equivalent routes from economic claims; and
8. expose the effective routing matrix and warnings through doctor.

The baseline is Agent Runtime `main` at `d93f581b`. Consumer repositories stay
read-only until their registered pilot tasks. No live billable provider call is
required for this unit.

## T2 Drift

`plan_assumption_gate` found 27 changed or newly present anchors. Every finding
comes from completed TASK-AR-645: task-linked compound records, host state
adapters, scribe projection, doctor/closure wiring, tests, fixtures, and closed
work records.

This is legitimate upstream progress, but W2 must remain blocked because the T0
snapshot predates those changes. This review is the T3 replacement. Re-record
the taskset anchors only after this review and the amended task/unit records are
committed.

## Failure-First Evidence

The registered suite is green:

```text
python -m pytest tests/test_model_routing.py \
  tests/test_role_routing.py \
  tests/test_role_routing_wiring.py \
  tests/test_provider_import_contract.py -q
61 passed
```

That suite does not exercise a provider call or a native subagent spawn. The
expanded template suite exposes the routing defect:

```text
python -m pytest \
  src/agent_runtime/templates/project/scripts/test_model_routing.py \
  src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py \
  src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py \
  src/agent_runtime/templates/project/scripts/test_auto_dispatch.py -q
75 passed, 2 failed
```

The relevant failure is
`test_routing_eval_requires_applied_provider_model`: a Low route selects the
semantic `haiku` tier, Codex actually remains `gpt-5.2-codex`, and the runtime
still writes an evaluation record as though routing applied. The second failure
is the pre-existing `auto_dispatch` write-back monkeypatch seam; it is unrelated
to model routing and remains outside this unit.

Additional failure evidence:

- all default `codex`/`codex-agent` haiku, sonnet, and opus entries resolve to
  the same `gpt-5.2-codex` model;
- `provider_env()` returns a non-empty mapping for those equivalent tiers, so
  both worker paths mistake configuration plumbing for an effective route;
- `subagent_dispatch.py` renders a prompt and emits a message/event but never
  invokes an agent;
- `codex_subagent_bridge.py` names the obsolete
  `multi_agent_v1.spawn_agent` tool and carries no model, reasoning, or observed
  usage contract;
- `agent_worker.py` and `auto_dispatch.py` are the actual packaged provider
  call sites, but they do not record local latency or distinguish a missing
  usage field from a measured zero;
- `eval_harness.py` calls token deltas `cost_delta` without proving that the
  route changed the invoked model or that billed cost is known;
- new work registration defaults to `worker_standard` and, when no explicit
  triggers are supplied, injects `ambiguity` and `data_integrity`; the latter
  is not recognized by `model_routing`, while the former makes routine
  low-cost execution impossible by default.

## Tag Manual and Autofolio Evidence

Tag Manual's `TASK-239-adaptive-model-routing.md` is the source of the current
haiku/sonnet/opus policy. Its status remains held because the required live
provider cost delta was never produced: the recorded baseline and actual
values remain `0/0`. The follow-up guards checked whether a provider mapping
was present, not whether the resolved model actually changed.

Tag Manual's `TASK-222-persistent-token-ledger.md` deliberately deferred a
shared persistent budget authority because concurrent writers and crash
windows would corrupt enforcement. This unit therefore adds append-only
observability, not a cross-process spending authority.

Autofolio copied the relevant runtime scripts byte-for-byte:

- `scripts/model_routing.py`
- `scripts/subagent_dispatch.py`

Its cycle gate correctly decides when reviewer/skeptic/auditor perspectives are
required, but it emits semantic `routing_tier` labels rather than native spawn
proof. Its `agents/lead_engineer/TOKEN-BUDGET.md` is a useful planning catalog,
yet the 30K-200K subagent figures are manual estimates with a wide error band.
They must never be presented as observed provider usage.

The reusable lesson is to preserve Autofolio's risk/collaboration policy while
moving model selection and usage truth into provider-aware execution evidence.

## Current Native Codex Contract

Current official Codex guidance establishes four relevant facts:

- subagent workflows consume more tokens than comparable single-agent runs;
- read-heavy exploration, triage, and summarization are the best starting
  points for parallel subagents;
- lighter subagent work should prefer the faster lower-cost
  `gpt-5.6-terra`, while demanding ambiguous multi-step work uses the stronger
  model family and higher reasoning effort;
- explicit spawn `model` and reasoning settings override configured/default
  values, and project-scoped custom agents may also set them.

The current session tool accepts explicit `model` and `reasoning_effort`
arguments. Repository Python still cannot invoke that tool. It can only build
an auditable packet for the parent session and record the result returned or
observed by the parent.

Source:
<https://learn.chatgpt.com/docs/agent-configuration/subagents>

## Routing Contract

### Provider-neutral policy

PM tiers remain the stable repository contract:

| PM tier | Intended work |
| --- | --- |
| `worker_low` | precise, bounded implementation and read-heavy exploration |
| `worker_standard` | broader routine implementation |
| `planner_high` | ambiguous, cross-cutting, security, or recovery planning |
| `reviewer_standard` | normal independent review |
| `reviewer_high` | critical/adversarial audit |

Haiku/sonnet/opus remain compatibility aliases for existing Claude-facing
records. They are not universal model names and are never evidence that a
Codex route applied.

New structured registrations default routine worker/task/unit tiers to
`worker_low`. Missing escalation triggers default to an empty list, not
fabricated ambiguity. Explicit `ambiguity`, `data_integrity`, `high_risk`,
`security`, `cross_cutting`, `external_effect`, or `repeated_failure` moves a
worker route to `planner_high`. Unknown triggers remain visible and make the
route unverified rather than silently proving savings.

### Provider resolution

Resolution returns a structured route:

- requested and selected PM tier;
- compatibility/provider tier;
- provider and execution surface;
- resolved model and model-source provenance;
- configured reasoning effort when supported;
- baseline model, equivalence group, and `model_changed`;
- route status (`effective`, `ineffective_equivalent`, `unsupported`, or
  `unverified`);
- economic-claim status.

The existing Claude defaults may remain compatibility data. Existing Codex API
defaults remain visible as an equivalent mapping until a host explicitly
configures distinct supported models.

For the native Codex session adapter, current documented/local tool capability
is represented as overridable adapter data:

| PM tier | Default native intent |
| --- | --- |
| `worker_low` | `gpt-5.6-terra`, low reasoning |
| `worker_standard` | `gpt-5.6-terra`, medium reasoning |
| `planner_high` | stronger Codex model, high reasoning |
| `reviewer_standard` | stronger Codex model, high reasoning |
| `reviewer_high` | stronger Codex model, highest supported configured reasoning |

The exact stronger model remains adapter/config driven. Availability is
`configured_unverified` until the native result is recorded; doctor must not
perform a live probe.

### Deterministic first

A `simple_lookup` signal is no longer permission to launch a cheaper model.
Before a lookup-only native/provider delegation is emitted, the dispatch
record must say:

- `not_required`;
- `attempted_insufficient`, with bounded evidence; or
- `completed_sufficient`, in which case no model dispatch is emitted.

An unresolved required preflight blocks `--emit-call`. This applies to the
generic subagent helper and the native Codex bridge. It does not create a new
tool executor.

## Native Dispatch Contract

Add a dedicated read-only `explorer` subagent role. Routine explorer and
precise implementer dispatches default to `worker_low`; strategist, reviewer,
auditor, and skeptic retain capability-appropriate defaults and can escalate
from task/unit signals.

The Codex bridge packet must use a provider-neutral execution capability name,
not a hard-coded historical tool identifier. It carries exact recommended
spawn arguments when resolved:

- prompt/task name;
- requested and selected PM tier;
- model and reasoning effort;
- dispatch/bridge correlation ID;
- escalation signals and reason;
- deterministic preflight status/evidence.

`record-reply` and council completion accept observed provider/model/reasoning,
token input/output, latency, and optional billed cost. Missing fields are
stored as `unverified`/`unavailable`, never copied from the request and never
coerced to zero.

## Provider and Evaluation Telemetry

Use existing append-only runtime event files as an observational dispatch
ledger. Do not add a shared mutable budget ledger.

Every dispatch/completion envelope records, where applicable:

- dispatch ID, task, role, provider, and execution surface;
- requested/selected tier, resolved/observed model, reasoning effort;
- escalation signals, routing reason, and deterministic preflight;
- route/equivalence/application status;
- token availability and positive input/output counts;
- measured local latency;
- billed-cost availability and currency;
- completion/error status.

Prompt bodies, transcripts, environment values, API keys, and arbitrary
provider responses are excluded.

`eval_harness` may report a token delta only when:

1. an actual model change was effective;
2. actual positive usage is known; and
3. a comparable baseline is present.

A monetary saving is verified only when both actual and baseline billed costs
are supplied in the same currency. Legacy estimates remain estimates.

## Doctor Contract

Doctor reads the host's model-routing module without making a provider call and
adds a machine-readable routing section. Equivalent mappings are warnings.
Distinct configured mappings are informative but still report availability as
unverified until execution evidence exists.

Doctor must never print credentials or unrelated environment values.

## Scope Amendment

Primary implementation surfaces:

- `scripts/model_routing.py` and the exact template mirror;
- root/template `scripts/work.py` registration defaults;
- root/template `scripts/task_claim_dispatcher.py` claim-time tier resolution;
- template `subagent_dispatch.py` and `codex_subagent_bridge.py`;
- template `agent_worker.py`, `auto_dispatch.py`, and `eval_harness.py`;
- `src/agent_runtime/doctor.py`;
- the Codex bootstrap and token-budget guidance;
- focused root and template tests, clean-host/template smoke, and the generated
  host lock fixture.

Claim records may persist planned routing metadata, but an actual model remains
unknown until a provider/native completion reports it. This unit does not infer
an actual model from a callsign, semantic tier, environment request, or parent
model.

## Verification

- `python -m pytest tests/test_model_routing.py tests/test_work_registration.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_provider_import_contract.py tests/test_template_smoke.py -q`
- template routing, dispatch, Codex bridge, provider-worker, auto-dispatch, and
  eval-harness tests, including failure-first equivalent-tier and unknown-usage
  cases
- root/template mirror checks for `model_routing.py`, `work.py`, and
  `task_claim_dispatcher.py`
- `python scripts/runtime_asset_usage.py --check`
- clean generated-host doctor JSON and routing-matrix smoke
- `python -m pytest -q`
- independent W4b against the exact implementation head

No verification step makes a live billable model call.

## Out of Scope

- Bean Wiki, Allimbot, or Autofolio mutation;
- a live provider availability or billing probe;
- provider pricing tables or synthetic dollar estimates;
- a cross-process persistent budget authority;
- a new agent executor or replacement orchestration framework;
- global user Codex configuration changes;
- the unrelated `auto_dispatch` write-back monkeypatch defect;
- broad provider model-catalog upgrades;
- version bump, tag, publish, release, or deployment.

## W2 Decision

After this review and the refreshed T3 snapshot merge to `main`, dispatch
exactly `UNIT-TASK-AR-646-001`. The unit keeps `worker_standard` as its
requested tier because it is cross-cutting; its explicit ambiguity and
data-integrity signals must visibly escalate the selected route. Reserve W4b
for a different agent instance.
