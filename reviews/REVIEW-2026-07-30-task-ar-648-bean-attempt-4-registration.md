---
title: TASK-AR-648 Bean Wiki Attempt-4 Registration
date: 2026-07-30
status: active
signal: pass
score: 99
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-011
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
tags: [planning-record, bean-wiki, adoption, green-replay, ownership, editorial-ops]
---

# TASK-AR-648 Bean Wiki Attempt-4 Registration

## Bottom Line

Register one fresh Bean Wiki replay only after the consumer-continuity
ownership repair passed canonical W4a, fresh independent W4b, and canonical
verification. Preserve attempt 3 as failure evidence; do not repair or resume
it.

## Fixed Inputs

| Boundary | Fixed value |
| --- | --- |
| Runtime product | `dd279cd5613578c87ed6c4c24b37325084449d82` |
| Runtime product tree | `ea843b6ca5661f04179376df92a11f4416217ab1` |
| Product template tree | `fb7a9ad3dca93b9734467e2e9b5201ba2c1527a9` |
| Runtime lifecycle close | `5e44d7f6764865c87c818260e2b841e74c7b3d29` |
| Runtime W4b | `APPROVE`, 99/100, no P0/P1 |
| Runtime complete suite | `2692 passed, 3 skipped` |
| Bean baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean existing checkouts | primary and attempts 0-3 read-only |
| New path | `.pilot-worktrees/bean-wiki-task-ar-648-green-4` |
| New branch | `codex/task-ar-648-agent-runtime-green-pilot-4` |
| Profile | `core+web-content` |
| Consumer SCM | default `working_tree`; consumer commits remain zero |

The Runtime lifecycle commits after the product change governance evidence
only. Product, template, and pilot-validator surfaces have zero delta from the
exact approved product.

## Editorial and Routing Contract

| Trace | Requested tier | Permitted execution |
| --- | --- | --- |
| adoption and preservation | `worker_low` | deterministic local commands |
| article review | `worker_standard` | one selective read-only editorial specialist |
| restart and Scribe | `worker_low` | deterministic distinct local processes |

The editorial trace follows `bean-wiki-editorial-ops`. It reads the Bean
editorial SSOT, configured review skill, personas, topic plan, and target
article, then writes one bounded review artifact. It cannot edit
`src/content/**` or a generated index. Configured tiers are not evidence of an
observed provider model, tokens, cost, or savings.

## Evidence Contract

1. Snapshot exact Runtime and Bean identities before creating attempt 4.
2. Record template root, product/template trees, upstream ref, and semantic
   digest at each adoption stage.
3. Preserve and compare all declared host assets, BACKLOG.md, the target
   article, and every `src/content/**` file.
4. Prove standby and active-claim continuity plus complete installed Owner
   governance without editing Bean README/AGENTS/CLAUDE.
5. Complete exactly three task/unit/claim traces with truthful routing fields.
6. Require an exact task-linked Compound retrieval, cross-process restart,
   fresh Scribe projection, and integer-zero external effects.
7. Sanitize the observed fixture and obtain exact-product W4a plus independent
   W4b before Allimbot.

## Boundary

No Bean primary or prior-attempt mutation, content or host-document edit,
consumer commit, dependency installation, provider-live call, Allimbot action,
release, version, tag, package, push, publish, deploy, credential access, or
network delivery is authorized.

## Next

T3-anchor UNIT-011, require readiness and canonical plan selection, create a
default working-tree Runtime claim, and only then create the two fresh pinned
worktrees.
