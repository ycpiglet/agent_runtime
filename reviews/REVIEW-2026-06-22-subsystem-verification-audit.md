---
type: review
title: Subsystem verification audit — deliberation, voting, A2A, testing, self-improvement
date: 2026-06-22
status: assessed
signal: watch
method: 4 evidence-based audits (ran tests + scripts, read artifacts) on origin/main v0.4.0
---

# Subsystem verification audit (2026-06-22)

Owner asked whether the product's own systems actually *work*: testing
(beta/edge/stress), meetings/seminars (opinion exchange), same-role multi-persona
communication, voting, skill self-improvement, asset/hook/API frequency-scoring
→ pruning of dead weight, cross-team exchange, and A2A/messaging. Four
evidence-based audits ran the tests/scripts and inspected runtime artifacts.

## What WORKS (verified, not declared)

- **Deliberation / opinion exchange — WORKING.** `meeting_room.py` 13/13 tests;
  60 MEETING-* + 16 SEMINAR-* artifacts with multi-round structure (participants
  / agenda / rounds / decision). Mutation boundary = proposal_only.
- **Same-role multi-personality — WORKING.** `persona_council.py` 4/4 tests:
  blind-Delphi over 7 personas (skeptic / pragmatist / systems-thinker /
  user-advocate / empiricist / first-principles / steward), `diversity_score`
  detects mode-collapse, `synthesize` flags capture-risk. Live COUNCIL-2026-06-14
  shows 5 personas × 4 candidates with real divergence (P0↔P3) preserved, not
  averaged away.
- **Voting — WORKING.** `subagent_council.py` 35/35 tests: majority /
  any-veto (skeptic+auditor veto) / weighted algorithms; emits a `consensus`
  message. `release_council_gate.py` enforces W4b independence — 4 required roles,
  distinct instance IDs (live RELEASE-DECISION-v0.2.0 vote record).
- **Testing core — STRONG.** Edge cases (116+ boundary/None/malformed
  assertions) and concurrency (Barrier/multiprocessing race tests pass) are
  strong; 47-gate owner-governance chain + a p95/p99 latency SLO gate
  (fail-on-warning on main).

## GAPS (dormant / detect-only / not wired)

1. **A2A messaging is dormant.** `a2a_message_router.py` is complete + tested
   (4/4) but `agents/runtime/a2a/messages.jsonl` doesn't exist; only a static
   2026-06-09 baseline (4 msgs). **Zero production calls to `emit_message()`** —
   the dispatcher/orchestrator never emit A2A on real work. Gates pass vacuously
   on the baseline. (Registered PoC-complete in TASK-AR-311; live wiring deferred
   to TASK-AR-518.)
2. **Cross-team + same-role-multi-instance comms don't happen at runtime.** 9
   teams / 21 roles are defined in ORG-MODEL; the baseline proves the schema
   routes cross-team, but there is **0 runtime cross-team traffic**. Same-role
   instances coordinate via file/worktree handoff, **not A2A** (not implemented).
3. **Asset-prune loop is detect-only.** Scoring works (`runtime_asset_usage` +
   `self_improvement_cycle assess`, 35 assets), but nothing transitions a
   low-reuse asset — `capability.session_dashboard` (reuse=1) has been flagged
   since 2026-06-17 and never demoted/deprecated. No skill self-improvement
   automation exists.
4. **beta_tester role is dormant.** Spec + advisory `beta_tester_due.py` exist,
   but zero activation — no automated exploration rounds, no BTC-* artifacts.
5. **Role concentration** (lead-engineer 76% of claims) and **compound
   under-cadence** (294 REVIEW : 1 COMPOUND) — diagnosed 2026-06-22, now guarded
   by `role_concentration_gate` / `compound_cadence_gate`.
6. **Testing gaps:** no property-based/fuzz (`hypothesis` unused), no E2E UI
   (Playwright), no multi-host/distributed claim-safety stress.

## Common root cause

The collaboration / messaging / asset infrastructure is **built and tested**,
but the **live autonomous dispatch loop does not exercise the distributed
paths**: it centralizes work on lead-engineer, never emits A2A, never routes to
review/skeptic/scout/beta roles, and never closes the asset-prune loop. The
deliberate, on-demand mechanisms (council, seminar, release vote) work *when
invoked*; the everyday loop is centralized and one-actor. This is an
**operationalization gap, not an infrastructure gap** — most of these were
landed as PoC/infra (TASK-AR-311 A2A PoC; ORG-MODEL roles; asset registry) with
the dispatch integration deferred and never closed.

## Remediation

**Shipped this cycle:**
- `role_concentration_gate` + `compound_cadence_gate` (advisory monitoring) — PR #197.
- `asset_lifecycle.py` — closes the asset detect→action gap with a safe,
  reversible `keep → observe` demotion for low-reuse assets (deprecate/remove
  stay Owner-gated) — see the asset-lifecycle PR.

**Routed as PROPOSALS (Owner-tier; operationalize the live loop — do not auto-rewrite the dispatcher):**
- **Wire A2A emission into dispatch** (claim/handoff/decision → `emit_message`),
  turning the dormant router live (the deferred TASK-AR-518 intent). This also
  enables cross-team + same-role-instance comms.
- **Route work to dormant roles** (skeptic/independent-auditor on high-risk
  merges; progress-scout per wave; council at W6) to break the lead-engineer
  monopoly.
- **Activate beta_tester** (scheduled exploration rounds → BTC-* → QA bugs).
- **Compound cadence obligation** (compound ≥1 lesson per N reviews).
- **Testing uplift** (property-based/fuzz; E2E UI; multi-host claim stress) —
  already on the maturity rubric (TASK-AR-546.. / v0.5 uplift).

**Accept-watch:** lifecycle watch debt (64 legacy VERIFY records without a
freshness block) — pre-date the schema; batch re-annotation is low-value churn.

## Bottom line
The deliberation/voting/persona/meeting machinery and the test/concurrency core
are genuinely WORKING with evidence. The real, consistent weakness is that the
**distributed-collaboration paths (A2A, cross-team, dormant roles, asset-prune,
beta) are built but not wired into the live loop** — so the system runs as a
centralized one-actor loop that *can* deliberate on demand but rarely does day to
day. Monitoring + one loop-closer shipped; the dispatch operationalization is
routed as Owner-tier proposals.
