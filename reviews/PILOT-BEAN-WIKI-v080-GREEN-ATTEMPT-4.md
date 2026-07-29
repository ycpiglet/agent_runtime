---
title: Bean Wiki v0.8 Green Pilot Attempt 4
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-011
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: blocked
signal: block
score: 84
priority: P1
tags: [pilot, bean-wiki, green-replay, attempt-4, adoption, template-parity, evidence]
---

# Bean Wiki v0.8 Green Pilot Attempt 4

## Bottom Line

Attempt 4 is blocked at the final taskset completion gate. Exact product
`dd279cd5613578c87ed6c4c24b37325084449d82` safely installed
`core+web-content`; all three bounded Bean traces completed and received
independent local approval with no Runtime/task P0 or P1. The final installed
`taskset_work_gate.py`, however, treats its own ISO-second `generated_at`
value as semantic drift. A board becomes stale merely because the next render
occurs in another second.

The defect is isolated to root/template parity: the Runtime root script already
contains the TASK-AR-623 ISO timestamp repair and TASK-AR-630 attention-line
mask, but the packaged project-template copy does not. Bean correctly received
the packaged copy. The consumer must not be patched as a workaround.

The live Bean primary checkout also changed its tracked-diff digest during the
pilot while retaining the same HEAD, status paths, and status digest. No pilot
operation targeted that checkout, but the literal UNIT-011 byte-identity
acceptance cannot be asserted. Future pilot contracts must protect frozen
evidence while allowing unrelated owner work in a live primary checkout.

## Signal

`BLOCK / P1`; P0 none.

| Finding | Scope | Priority | Effect |
| --- | --- | ---: | --- |
| Packaged taskset freshness regex omits ISO-second timestamps | Runtime product/template | P1 | Deterministic consumer completion cannot pass after wall-clock time advances |
| Live primary checkout used as a byte-immutable global oracle | Pilot isolation contract | P1 | Concurrent owner edits invalidate an otherwise isolated consumer proof |
| No general terminal taskset projection command | Runtime lifecycle ergonomics | P2 | Released claims required serial normalization to `taskset-completed`/100 |
| Severity domains are not explicit | Runtime review schema | P2 | Article-publication P0/P1 could be confused with Runtime/task P0/P1 |
| Specialist model label says “actual” for an orchestration request | Runtime review template | P2 | Canonical claim remains truthful, but report terminology is imprecise |
| Installed `work.py now` calls absent `now.value` | Runtime template | P2 | Convenience command fails; direct time API and lifecycle commands still work |
| Two optional Owner-gate scripts are absent | Profile coverage | P2 | Owner gate reports explicit skips; required installed gates still ran |

## Fixed Provenance

| Field | Observed value |
| --- | --- |
| Runtime product | `dd279cd5613578c87ed6c4c24b37325084449d82` |
| Runtime product tree | `ea843b6ca5661f04179376df92a11f4416217ab1` |
| Runtime template tree | `fb7a9ad3dca93b9734467e2e9b5201ba2c1527a9` |
| Runtime lifecycle baseline | `5e44d7f6764865c87c818260e2b841e74c7b3d29` |
| Template semantic digest | `sha256:0cb7e1bdfbd1bfaa5ae1e58b2e374d80326e13532c97a56545d8b2274f15e730` |
| Bean baseline/current HEAD | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean branch | `codex/task-ar-648-agent-runtime-green-pilot-4` |
| Consumer commit count | `0` |

The detached product worktree remained clean and fixed at the exact product.

## Adoption and Preservation

| Check | Result |
| --- | --- |
| Selected files | 246 (`core+web-content`) |
| Effective ownership | 239 managed, 5 seed-once, 2 host-owned excluded |
| Initial reconcile | 244 safe updates, 2 excluded, 0 conflicts |
| Immediate reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Lock | v2, 246 files, exact ref/digest, passed |
| Doctor | 1 expected empty-directory blocker repaired; 0 blockers, 8 warnings |
| Standby/active no-STATUS continuity | passed |
| State sync / RBAC / parallel / installed Owner governance | passed before closeout |
| Managed `AGENT_RUNTIME.md` | host/template SHA-256 both `d62e1ac808d27fbd3b63555aa2aaff8de4bd5af1d92c8cd6ba606be71cb6bcf8` |
| 16 declared host assets | manifest unchanged at `d09b7a36a2e329a1ca47110f53dbcb8ae6303de6b72bdfe8e278cd09aea94107` |
| Complete `src/content` | 125 files; manifest unchanged at `2d45cb99dbcd1e3fe86ad0ebf9d31646580a0720d3496c27c952e829e2ba07cb` |
| Target article | unchanged at `a4c431e1ad5eb77d260c37e19b2ceb3637b43f2c606a2b87b81e99857354f4d6` |
| Generated article index | unchanged at `0f635c697d019744a8a9abfbc357723261537a088308d05692ea87a0edc476b0` |
| Bean local content/editorial checks | passed; 17 non-blocking legacy length warnings |
| External effects | publish/deploy/push/commit/credential/network/install/content mutation all integer zero |

No final post-registration reconcile or sanitized green-fixture promotion was
accepted after the P1 stop condition fired.

## Three Bounded Traces

| Task | Route | Independent result |
| --- | --- | --- |
| `TASK-AR-201` adoption | requested/selected `worker_low`; provider tier `haiku`; deterministic local; observed model/usage unavailable | APPROVE, P0 0, P1 0, P2 2 |
| `TASK-AR-203` Compound/restart/Scribe | requested/selected `worker_low`; provider tier `haiku`; distinct PIDs `715468`/`715779` | APPROVE, P0 0, P1 0, P2 1 |
| `TASK-AR-202` editorial review | requested/selected `worker_standard`; provider tier `sonnet`; native subagent configured with `gpt-5.6-terra`; provider observation unavailable | APPROVE for trace, Runtime/task P0 0, P1 0, P2 2 |

The editorial specialist correctly returned `REVISE` for the separate
`bean_content_publication` domain (P0 2, P1 3, P2 1). Those findings block
publishing the article; they do not retroactively fail the requested read-only
diagnostic trace. No content remediation was authorized or performed.

The Compound search retrieved the exact TASK-AR-203 record first with score
180 and no unrelated match. The restart checkpoint and `latest.json` were
byte-identical at
`06711ffa74e7554375ba83409119ea47ca0985f5d1578deb288484cec51ae49f`.
Scribe refreshed only its configured projection; `BACKLOG.md` remained
`c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591`.

## Final Failure Reproduction

After all three tasks and claims were terminal, the serial owner normalized
the three released claims to `phase=taskset-completed` and
`progress_pct=100`, regenerated the board and classifier, and obtained:

```text
state-sync-gate: pass
continuity-contract-gate: pass
taskset-work-gate: fail
- BACKLOG-BOARD.md: stale:content-mismatch
```

The only semantic diff between the just-written board and a later render was:

```diff
-generated_at: 2026-07-30T03:23:06+09:00
+generated_at: 2026-07-30T03:23:22+09:00
```

Root/template/installed hashes prove the packaging gap:

| Surface | SHA-256 |
| --- | --- |
| Runtime root `scripts/taskset_work_gate.py` | `3a7589270b576a97f90e3121891ad08f510f6ed4bf352438bf0754a90143c22e` |
| Packaged template copy | `fe840225c2fe9e6a11769d370f3f9920f532bd95fcc20a59a75449ff226652e6` |
| Bean installed copy | `fe840225c2fe9e6a11769d370f3f9920f532bd95fcc20a59a75449ff226652e6` |

The existing root unit test uses a synthetic date-only value, so it passes
without exercising the packaged script's real ISO-second output. There is no
root/template byte-parity regression for this gate.

As a same-state control, the Runtime root gate was then invoked against the
frozen Bean attempt-4 root with the same taskset and `--require-complete`. It
passed with zero findings. The installed template gate still failed. This
rules out Bean task/claim/board semantics and isolates the failure to the
packaged executable bytes.

## Primary and Frozen Checkout Audit

Allimbot remained exactly at HEAD
`5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd`, status digest
`97585bc46387fde8ee01b51518bfe5ffeb3084f3b6f7b085cf555059f83eded6`,
and tracked-diff digest
`c90de2ff8397144a33a708f8c551162f6578cea9efcb4af30256cf1246902a69`.
The original red pilot and frozen attempts 1–3 retained their initial HEAD,
status, and tracked-diff digests.

The live Bean primary retained HEAD
`808309a7b41b80b901e79a1fa6ad546871187ab9`, 166 status entries, and status
digest
`b59aff092434a6a003a836275d3b5135b744e64aa64028b27f0f05ca5d878664`,
but its tracked-diff digest changed from the pre-run
`65a25c028a52d8da39dc7d595d4e7add3ee64cac70c1a531ee12a47e3d6ec995`
to
`b2199aefc8965e1c6f8041eb53c7bb23530924581f9c79d5bec4cc1cf63c56a4`.
This is consistent with concurrent edits to already-dirty paths, not with the
pilot's isolated attempt-4 write surface. Nevertheless, UNIT-011 required
byte identity and therefore cannot pass.

## Decision

Freeze attempt 4. Do not patch its installed gate, mutate Bean host/content
files, promote a green fixture, create an Allimbot pilot worktree, or begin
release work.

Open a separate Runtime repair unit that:

1. restores the already-correct root taskset freshness behavior to the
   packaged template;
2. adds a packaged-script parity regression plus an ISO-second delayed-render
   regression;
3. audits other root/template executable mirrors for drift and introduces a
   scalable parity guard rather than one-file memory;
4. provides or documents one canonical taskset terminal-projection operation;
5. scopes pilot invariants to the disposable worktree and frozen evidence,
   while recording rather than blocking on unrelated live-primary edits.

Only an exact repaired product with W4a and independent W4b may start a fifth
fresh Bean replay. Allimbot remains blocked until that replay independently
passes.
