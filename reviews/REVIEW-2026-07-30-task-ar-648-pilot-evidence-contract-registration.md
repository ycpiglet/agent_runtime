---
title: TASK-AR-648 Pilot Evidence Contract Repair Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-015
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, pilot-acceptance, isolation, evidence-portability, fail-closed]
---

# TASK-AR-648 Pilot Evidence Contract Repair Registration

## Bottom Line

Register one Runtime-only unit for the two independently confirmed UNIT-014
P1s. The repair must make multiple immutable pilot executions selectable
without turning contracts into policy overrides, and must make public
isolation evidence portable without pretending that sanitized aliases are
physical checkout paths.

Bean attempt 5 is frozen. Attempt 6, Allimbot, and all release surfaces remain
blocked until the repair passes W4a and fresh independent W4b.

## Contract Split

| Layer | Owner | May vary by pilot? |
| --- | --- | --- |
| Generic preservation, routing-truth, identity, restart/Scribe, P0, and zero-effect rules | Executable Runtime validator | No |
| Exact result, baselines, counts, tasks, findings, verification, and evidence semantic digest | Versioned pilot contract | Yes, through reviewed immutable records |
| Physical root disjointness and write containment | Local raw isolation gate | No |
| Public checkout identity, snapshots, attribution, raw digest, and raw decision | Sanitized projection | Yes, deterministically derived only after raw validation |

An unknown, duplicate, malformed, cross-host, or drifting record blocks.
Contracts cannot suppress a generic finding.

## Fixed Evidence

- Historical red semantic SHA-256:
  `e8a6119f3c6cef815c352600188f57c48e669e9d650b3e4e1b67f751a1d8582e`
- Attempt-5 green semantic SHA-256:
  `8a56c8e5a89bfb5bbd7c6224be70f1ec69e41c339dcfe5b0c542b0b26361c39f`
- Attempt-5 raw isolation byte SHA-256:
  `761b236f6ad9f1fd99cb88e688ffefb75422e0e177e5fc8422b1738fbcfd52b1`
- Registration baseline:
  `25ef558d602fda4685b40af39a57f3be4a3c2dab`

The red and green acceptance fixtures are inputs, not implementation scratch
files. Their semantic payloads must remain unchanged.

## Required Adversarial Coverage

- unknown host and unknown pilot
- cross-host pilot reuse
- duplicate `(host, pilot_id)` pair
- malformed schema, counts, digest, task, finding, verification, and effect
  contract fields
- semantic fixture mutation and unrecognized payload fields
- false model/usage/savings observations
- nonzero and boolean external-effect values
- missing or invalid raw digest and raw-decision binding
- duplicate or unknown checkout ID
- observed write mapped to a non-target checkout
- absolute path in a sanitized projection
- snapshot or attribution mutation after projection

## Exclusions

No consumer write, package install, provider call, release mutation, or remote
action is authorized by this registration.
