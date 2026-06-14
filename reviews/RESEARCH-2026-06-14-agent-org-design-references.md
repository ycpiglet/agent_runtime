# RESEARCH — Agent Org Design References (Karpathy · multi-agent architectures · persona diversity)

- **Date:** 2026-06-14
- **For:** `docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md`
- **Question:** How should a Director→Lead→Worker+Reviewer agent org be structured, how
  parallel/autonomous should it be, and how should persona/values diversity be used?

## Bottom Line

The research **validates** the chosen shape (4-role hierarchy + risk-based hybrid
dispatch) and adds three refinements: (1) software engineering is on the *"don't naively
parallelize"* side — parallelize only along genuine seams, serialize interdependent edits;
(2) persona/values diversity pays off **only** in deliberation/review, not execution, and
only if it is *real* (independent) — use blind-Delphi; (3) this is **not greenfield** —
the template already ships the org machinery (roles.yml, orchestrator, subagent
perspectives, seminar/council); operationalize and reconcile it. Token cost is the binding
constraint (multi-agent ≈ **15× tokens**).

## Strand 1 — Karpathy: autonomy & verification

- **LLM-OS** (Nov 2023): Director ≈ kernel/scheduler; context window = scarce RAM →
  *context engineering* (right info, not max-stuffing); disk (repo/claims/handoff) = memory
  because workers have "anterograde amnesia" — persist state, never assume recall.
- **Autonomy slider, default-low** — "build Iron Man suits, not robots" (Software 3.0,
  Jun 17 2025). Risk-based hybrid dispatch *is* the slider; slide right only as a task
  class earns reliability.
- **Generation–verification gap** (Jun 3 2025): review is the bottleneck → small,
  PR-sized, independently checkable units + fast/visual review.
- **Adversarial review + LLM Council** (Nov 22 2025): multiple models → *anonymized*
  ranking → "Chairman" synthesis, to fight self-preferencing.
- **March of nines** (Oct 17 2025): gate merges; human is the bottom line on load-bearing
  work. Over-autonomy wastes tokens; workers are gullible (sandbox/gate external writes).

## Strand 2 — Multi-agent architectures & "gstack"

- **gstack = Garry Tan's (YC) open-source Claude Code toolkit** — turns Claude Code into a
  "virtual engineering team you manage": 23+ personas (CEO/Eng-Manager/Staff-Eng
  reviewer/QA-Lead/Security…), slash-command skill routing (`/office-hours`,`/review`,
  `/qa`,`/ship`) along review gates (Think→Plan→Build→Review→Test→Ship→Reflect), parallel
  via Conductor (10–15 isolated Claude Code sessions). Human-mediated role-switching, not
  autonomous multi-agent. **Closest public analogue to this design; same Claude Code
  substrate.** The agent_runtime *template* (`roles.yml` + `agent_orchestrator.py` +
  `subagent_dispatch.py` + `agent_seminar.py`) is already a gstack-class system.
- **Patterns to adopt:** hierarchical orchestration with a *single decision-owning Lead*
  (MetaGPT, CrewAI-hierarchical, AutoGen manager, LangGraph supervisor, Anthropic
  orchestrator-workers); delegation as an *explicit typed handoff*; structured unit
  contracts (objective + output format + tools + **boundaries** + acceptance); Reviewer as
  a *mandatory gate* (evaluator-optimizer, executable verification, bounded retries ≤3);
  share full traces + compress context; cheap Workers / strong Lead.
- **Patterns to avoid:** parallel Workers editing shared/interdependent code without a
  serialization point (**#1 failure mode**); LLM auto speaker-selection as control flow;
  flat peer handoff with no validator; over-engineering; unbounded fan-out (15× cost).
- **The crux (Cognition, Jun 12 2025 vs Anthropic, Jun 13 2025):** Anthropic's multi-agent
  win was *research* (breadth-first, read-only, parallelizable). Cognition warns about
  *coding* (write-heavy, interdependent) — context fragmentation makes parallel workers
  adopt conflicting assumptions. **Our domain sits on Cognition's side → seam-aware
  parallelism, single-threaded for interdependent edits.**

## Strand 3 — Persona / values diversity

- **Helps, but only if real and only for deliberation.** Heterogeneity beats headcount
  (2 diverse ≈ 16 homogeneous; arXiv 2602.03794). Debate improves reasoning (Du 2023).
  Diversity-prediction theorem: diversity mechanically reduces collective error — **but**
  LLMs default to high correlation (mode collapse) and personas conform (lone dissenter
  flips **85%** of the time; "invisible groupthink"). A confident wrong/persuasive agent
  can drop group accuracy 10–40%.
- **Antidote = blind-Delphi** (already in repo `agent_seminar.py` / DIVERSITY-COUNCIL):
  independent first drafts before agents see each other; anonymized aggregation;
  adversarial skeptic; confidence-weighting; **measure** semantic spread; re-anchor each
  round.
- **Vary substance axes, not style:** risk tolerance · time-horizon · values/optimization
  target · domain lens · epistemic style. Starter archetypes: Skeptic, Pragmatist,
  Systems-Thinker, User-Advocate, Empiricist, First-Principles, Steward. **Avoid
  demographic personas** (bias). **Routine execution: single agent** — diversity there is
  noise + cost.

## Implications for the design

1. Execution = **seam-aware parallelism + phased autonomy** (footprint gate detects
   collisions; interdependent units serialized; single integrating Lead; full-trace
   sharing; autonomy slider starts low).
2. **Not greenfield:** operationalize + reconcile the template org machinery (roles.yml,
   orchestrator, subagent perspectives, seminar/council) into the repo and connect to the
   claim/wave execution + work-schema unit flow.
3. **Persona diversity = a separate deliberation/review layer** (extend council/seminar;
   optional LLM-Council; diversity measurement; capture guards) — never in routine
   execution.
4. **Cost discipline is binding** (15×): budget + concurrency caps, model-tier routing
   (cheap Workers / strong Lead), idempotent claims, stop conditions, est-vs-actual.

## Sources

Karpathy: [Intro to LLMs (Nov 2023)] · [Software 3.0 (Jun 17 2025)] · [Dwarkesh (Oct 17
2025)] · [LLM Council repo (Nov 22 2025)]. Architectures: [Anthropic — Building effective
agents (Dec 19 2024)] · [Anthropic — Multi-agent research system (Jun 13 2025)] ·
[Cognition — Don't build multi-agents (Jun 12 2025)] · MetaGPT (2308.00352) · ChatDev
(2307.07924) · CrewAI · AutoGen (2308.08155) · OpenAI Agents SDK/Swarm · LangGraph ·
[gstack (github.com/garrytan/gstack)]. Diversity: Du 2023 (2305.14325) · Agent Scaling via
Diversity (2602.03794) · Silicon Crowd (Science Advances 2024) · Verbalized Sampling
(2510.01171) · Persona Inconstancy (2405.03862) · Generative Agents (Park 2023).
