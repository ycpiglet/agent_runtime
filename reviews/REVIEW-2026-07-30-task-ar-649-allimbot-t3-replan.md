---
title: TASK-AR-649 Allimbot Pilot T3 Replan
date: 2026-07-30
task_id: TASK-AR-649
unit_id: UNIT-TASK-AR-649-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: approved
signal: pass
score: 98
priority: P0
tags: [allimbot, t3-replan, security-service, native-events, isolation]
---

# TASK-AR-649 Allimbot Pilot T3 Replan

## Bottom Line

Proceed only from exact Runtime product
`4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` and clean Allimbot commit
`5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd`. Bean Wiki is independently
green. The live Allimbot primary is dirty with unrelated Owner work and is a
read-only observation, never the pilot target.

## Revalidated Evidence

- Runtime product tree:
  `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Runtime template tree:
  `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f`
- Runtime packaged-scripts tree:
  `62311b7847f66206a2a33e4bd497750bf074384f`
- Runtime exact-product suite: `2739 passed, 3 skipped`
- Bean attempt 6: W4a and independent W4b approve, P0 0 / P1 0 / P2 3
- Allimbot commit/tree:
  `5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd` /
  `b50199a13b534f9e7a89b301a645f39759b89dc1`
- Live-primary dirty paths: `console/app/console/page.js`,
  `console/auth.js`
- Primary status and tracked-diff digests:
  `19f6706dc44e5f3d2484715723fc2c2414218f8ec5949872c8a4ddd3f5a956a8`,
  `c90de2ff8397144a33a708f8c551162f6578cea9efcb4af30256cf1246902a69`
- `core+security-service`: 251 selected files; only `.env.example` and
  `.gitattributes` currently collide with tracked host files.

## Dispatch Decision

Keep `UNIT-TASK-AR-649-001`, but replace its stale generic scope with this
exact-product, exact-host, isolation-bound replay. Before the first consumer
write:

1. refresh taskset plan assumptions without bypass;
2. pass Unit readiness with zero findings;
3. prove canonical selection resolves TASK-AR-649 / UNIT-TASK-AR-649-001;
4. create a default working-tree Runtime claim without changing Runtime HEAD;
5. create a new detached product, target, and same-commit control;
6. capture all physical isolation baselines.

## Harness Decision

Use `core+security-service` as a shared Runtime projection plus a small
Allimbot overlay:

- host-owned: `.env.example`, `.gitattributes`, security/release/status docs,
  integration recipe, and all existing product paths;
- generated: Scribe projection and local pilot evidence;
- risk overlay: auth, Supabase migrations, deploy workflows, and Vercel
  configuration;
- state adapter: `docs/PROJECT_STATUS.ko.md`.

Exactly three traces are allowed:

1. deterministic adoption verification at `worker_low`;
2. one Critical read-only auth review with canonical high-risk metadata and
   exactly one independent reviewer;
3. deterministic native-event local spool recovery, intentional unsafe-event
   rejection, Compound retrieval, two-process restart, and Scribe at
   `worker_low`.

## Event Boundary

Runtime may call only `ProjectEmitter.emit()` into a disposable SQLite spool.
The pilot supplies non-secret local configuration so Allimbot does not consult
hosted credentials. It never calls `flush`, starts a worker, reaches a provider,
or reports delivery. The persisted event must have an empty body and the exact
managed allowlist; a secret-like negative input must be rejected before enqueue.

## Promotion Rule

Allimbot is Runtime-green only if adoption, Critical routing/review, local event
durability, Compound/restart/Scribe, host tests, causal isolation, exact
acceptance, W4a, and fresh independent W4b pass with no Runtime P0/P1. A
separate product-security review verdict remains distinct from harness
acceptance.

## Stop Boundary

Stop on assumption drift, wrong selection, primary/control/product write,
tracked product mutation, unreviewed Critical work, policy fail-open, secret
leak, credential read, install, flush, network delivery, provider-live call,
migration, deploy, consumer commit, contract ambiguity, or any release surface.
