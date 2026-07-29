# Pilot Acceptance Contracts

Consumer-pilot acceptance has two layers:

1. executable safety invariants that every pilot must satisfy; and
2. an immutable contract containing the observations for one exact run.

Contracts are selected by the exact `(host, pilot_id)` pair. A host default or
"latest run" fallback is intentionally not supported.

## Contract registry

Contracts use schema `agent-runtime-pilot-contract/v1` and live as individual
JSON files under `tests/fixtures/pilots/contracts/`. The loader rejects the
entire registry when it finds:

- an unknown schema, malformed field, unsafe path, or invalid digest;
- two files for the same host and pilot ID;
- one pilot ID reused by different hosts;
- a contract that omits a core external-effect guard; or
- an empty, missing, or symlinked registry.

Each record pins the evidence semantic SHA-256, result, Git baselines, adoption
and content counts, reconcile conflicts, exact task/unit/claim identities,
finding priorities, verification counters, required external effects, and
optional supporting-artifact bindings. These are observations, not policy.

## Executable invariants

The contract cannot disable checks for:

- host-asset and content preservation;
- bootstrap, task, unit, and claim identity;
- routing and provider-usage truthfulness;
- Compound retrieval, process restart, and Scribe freshness;
- integer-zero external effects;
- P0 findings blocking the run; or
- safe relative evidence and artifact paths.

Every external-effect key recorded by evidence is checked, even when it is not
listed by the selected contract. Every contract must retain the core guards:
`publish`, `deploy`, `origin_push`, `host_commit`, `credential_read`,
`network_delivery`, and `content_mutation`.

## Artifact bindings

A `pilot_isolation` binding points to a public v2 sanitized isolation
projection. Acceptance checks:

- the projection's semantic SHA-256;
- the byte SHA-256 of the validated private raw v1 proof recorded by the
  projection;
- the v2 portable schema; and
- a fresh zero-block isolation-gate decision.

Changing either the projection or its raw-proof identity therefore invalidates
the run contract.

## Validate a run

```text
python scripts/pilot_acceptance.py \
  --host bean-wiki \
  --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json \
  --check --json
```

Successful JSON includes the selected identity, for example
`bean-wiki:bean-wiki-v080-green-attempt-5`.

## Register another host or run

1. Produce sanitized, replayable evidence with a globally unique `pilot_id`.
2. Run all shared gates before deriving immutable observed values.
3. Add one strict contract file for the exact host and pilot ID.
4. Add positive replay plus unknown, mutation, and malformed-contract tests.
5. Run acceptance through the public CLI; do not add a host fallback.

Historical contracts remain in the registry so a later green run does not
rewrite or reinterpret earlier blocked evidence.
