# HANDOFF — UI Redesign & Product-Structure Change (for next session)

- **Date:** 2026-06-15
- **Purpose:** Carry the UI/UX + product-structure redesign discussion to a future
  session for design + modification work. (This session delivered the *agent-org &
  delegation* sub-project; UI is deferred per Owner.)
- **Owner directive (2026-06-15):** "UI 이슈, 재설계 및 프로덕트 구조 변경 대화기록
  나누고 다음 세션에서 다시 설계하고 수정 작업하도록 설정."

## Context: the 4-way decomposition

The Owner's concerns split into 4 independent sub-projects. **#2 is underway; #1/#3/#4
are deferred to next session.**

1. **Decision-first console IA** *(deferred)* — home cockpit (attention inbox), nav
   prune (67→~5-9), progressive disclosure (essentials → click for detail),
   initiative/taskset/task/unit hierarchy views, state-machine visibility
   (waiting/active/done → drill-down).
2. **Agent org & delegation model** *(DONE this session: spec + research + taskset
   TASKSET-AR-AGENT-ORG-DELEGATION, Unit 1 implemented)* — see
   `docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md`.
3. **Visual identity** *(deferred)* — design tokens / type scale (replace 309
   hardcoded font-sizes), **2.5D game-piece/Pokémon/Mario-style agent characters**
   (Office Map), **insight-driven graph** (replace the radial 0-edge node-link with
   critical-path / blocked-chain / swimlane).
4. **i18n** *(deferred, small)* — EN schema/docs + KO UI localization (Owner leaned
   this way; fold into #1).

## UI/UX audit (measured 2026-06-14 — the evidence base for #1/#3)

Home page alone: **72,279px ≈ 80 screens**, **25,452 DOM elements**, **4,382 card/blocks**,
**67 nav items**, 39 headings, **13 font sizes / 11 text colors**, full-page screenshot
**times out**. Source: `src/agent_runtime/ui_console.py` is a **single ~479KB file** with
inline HTML/CSS/JS, only ~20 CSS vars vs **309 hardcoded `font-size:`**.

Called-out areas:
- **Agents tab** = "No active sessions" + filter scaffolding (no engaging agent view).
- **Office Map** = right idea (rooms + avatars) but 52 agents crammed in Dev Room as tiny
  initial-badges; not the desired cute 2.5D characters.
- **Dependencies graph** = radial node-link, 226 nodes in a circle but **0 dependency
  edges shown**; no insight (no critical path / blockers / bottlenecks).

Honest note: at 1440px desktop, top-level **alignment/overflow is fine** — the real
problems are **information overload + no decision focus + typography inconsistency +
monolithic UI architecture**, not pixel alignment.

## Direction agreed (research-backed)

- **Decision-first, progressive disclosure**: show essentials, reveal detail on
  interaction. Cut the feature surface aggressively (Owner: features were added
  intentionally to prune later — now is the time).
- **Persona diversity** (research `reviews/RESEARCH-2026-06-14-agent-org-design-references.md`)
  belongs in the **deliberation/review** layer (blind-Delphi), not routine UI; vary
  substance axes; measure diversity. Relevant to #3 character personalities too
  (functional/epistemic, not demographic).
- **Architecture**: extract UI from the 479KB monolith into templates/components + a
  design-token stylesheet so iteration + pruning are feasible. This likely should be the
  first move of #1/#3.

## Next-session entry points

- Resume UI: brainstorm sub-project **#1 (Decision-first IA)** first (offer the visual
  companion — it's visual-heavy), then **#3 (visual identity + characters + insight graph)**.
- Continue agent-org: implement remaining units **TASK-AR-558..562** (each gets its own
  plan via writing-plans). `docs/superpowers/plans/2026-06-15-agent-org-delegation-unit1-role-registry.md`
  is the pattern.
- Artifacts: spec/research/plan under `docs/superpowers/` + `reviews/RESEARCH-2026-06-14-*`.
