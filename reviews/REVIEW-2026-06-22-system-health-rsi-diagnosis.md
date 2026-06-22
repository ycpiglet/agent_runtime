---
type: review
title: System-health / RSI diagnosis — collaboration, compound, role distribution, asset reuse
date: 2026-06-22
status: assessed
signal: watch
method: scripts/self_improvement_cycle.py assess + task-claim distribution + reviews cadence
---

# System-health / RSI diagnosis (2026-06-22)

Owner asked for a product-system check: multi-agent collaboration, the ralph
automation cycle, loop engineering, compound — and specifically whether
compound/review work is breaking down, whether the lead engineer carries
everything, and which agents/skills/hooks/APIs are under-exercised.

## Method (data, not vibes)
- `scripts/self_improvement_cycle.py assess --json` → maturity, collaboration, runtime assets.
- Task-claim distribution over `agents/runtime/task_claims/*.json` by `agent_role`.
- `reviews/` artifact cadence by type, this month.

## Findings

**Maturity: `improving`, score 70.** Largest deductions: monitored role gaps
(−15), lifecycle watch (−10), advisory-due (−3), low-reuse assets (−2). The
machinery is healthy and running; the gaps are about *distribution* and
*compounding*, not the loop itself.

1. **Role concentration is real (severe).** lead-engineer holds **85 of 112
   claims (76%)**. Everything else is a long tail: qa 8, interface-designer 5,
   design-system-steward 5, orchestrator 2, independent-auditor 2, then
   worker-engineer / scribe / reviewer / release-steward / doc-steward at 1 each.
   The monitored roles **council, progress-scout, skeptic have ZERO claims**
   (dormant) — these are exactly the review/verify/scout roles.
2. **Compound is the weak link; review is over-produced.** This month: **294
   REVIEW** vs **1 COMPOUND** vs 4 RETRO (+ 49 VERIFY, 12 SEMINAR). Reviews are
   generated copiously (W4b votes, per-task), but lessons are almost never
   compounded into the casebook / regression. The failure→regression loop runs
   only when a human triggers it.
3. **Low-reuse asset:** `capability.session_dashboard` (reuse 1, usage 3) is the
   single flagged low-reuse script of 35 assets (usage_total 303 — assets are
   otherwise healthy).
4. **Lifecycle watch debt (64):** legacy `reviews/VERIFY-*` records lack a
   freshness block, so staleness can't be evaluated — persistent watch noise.
5. **Automation layer is present and active:** agent_loop, wave_dispatcher,
   task_claim_dispatcher, taskset_dispatcher, org_orchestrator, planning_loop,
   claim_reaper, deadlock_watchdog, goal_supervisor, dispatch_gate (12 scripts).
   Claims, reviews, and verifies flow — the ralph/loop cycle itself works.

## Root-cause analysis

- **Why lead-engineer does everything:** the dispatch path
  (wave_dispatcher / task_claim_dispatcher / org_orchestrator) defaults work to
  the lead-engineer worker. The ORG-MODEL defines council/skeptic/progress-scout
  and review roles, but nothing *routes work to them* — they are *monitored*
  (gap-detected, −15 score) yet never *dispatched*. Review independence (W4b)
  pulls in qa/auditor as voters, which is why those are non-zero; pure
  review/skeptic/scout roles have no claim path at all.
- **Why compound lags review:** review is a cheap, auto-emitted artifact;
  compounding requires the deliberate `failure-to-regression` step (casebook +
  route). There is no cadence signal that says "you have N reviews and 0
  compounds — compound something," so it only happens by hand.
- **Why the low-reuse / lifecycle debt persists:** these are watch-only signals
  with no forcing function; they accumulate until a cleanup cycle.

## Remediation (routed)

- **Auto-detect the two headline problems (shipping now, advisory):**
  `scripts/role_concentration_gate.py` (flags a role > threshold share + dormant
  review roles) and `scripts/compound_cadence_gate.py` (flags review≫compound
  ratio). Source-repo advisory gates; see the system-health-guards PR. These turn
  invisible drift into a monitored watch signal.
- **Architectural rebalance (PROPOSAL — touches the autonomous dispatch, Owner
  tier):** route a fraction of work to the dormant review/skeptic/scout roles —
  e.g. dispatch a `skeptic`/`independent-auditor` claim on high-risk merges, a
  `progress-scout` sweep per wave, and a `council` deliberation at W6. Make the
  review→compound step a cadence obligation (compound at least 1 lesson per N
  reviews). Register as a taskset; do not auto-rewrite the dispatcher.
- **session_dashboard low-reuse:** decide exercise-vs-deprecate at the next
  cycle (route to the asset-lifecycle review).
- **Lifecycle watch debt (64):** batch-annotate legacy VERIFY records with a
  freshness block, or accept-watch explicitly.

## Companion work (this batch)
- autofolio fork-drift (`task.schema.json` vs upstream classifier) — separate fix/PR.
- self-eval #128 instrumentation — wires derivable deferred metrics.
- Non-hermetic ARCHIVE/BACKLOG test — accepted-watch (cosmetic date churn,
  already mitigated by explicit-pathspec commits).

## Bottom line
The multi-agent / ralph / loop machinery is **working and maturing (70,
improving)**. The two real weaknesses are **(1) work concentrates on
lead-engineer while review/skeptic/scout roles sit idle**, and **(2) the team
reviews far more than it compounds**. Both were previously invisible; they are
now made into monitored gate signals, with the deeper dispatch rebalance routed
as an Owner-tier proposal.
