---
type: rfc
id: RFC-2026-06-23-decision-first-console-IA
audience: owner
status: proposal
signal: decide
tags: [rfc, ui, console, information-architecture, cockpit, navigation, progressive-disclosure]
supersedes_context: HANDOFF-2026-06-15-ui-redesign-and-product-structure.md (sub-project #1)
---

# RFC — Decision-First Console IA

Proposal for the Owner to pick a direction. **Docs only — no code in this PR.**
Backs deferred sub-project **#1** from the 2026-06-15 UI handoff.

## Bottom Line

- The "67 nav items / 80-screen home" baseline measured on 2026-06-14 is **already
  partly addressed**: the console now ships a collapsible sidebar with 6 core links
  + a grouped **More** disclosure (WORK/AGENTS/COMMS/RECORDS/OPS, ~28 secondary
  views) and a home **cockpit** ("What needs you now" attention inbox + work-state
  panel). The redesign is therefore an **advance-from-baseline**, not a rebuild.
- Remaining gap is **decision focus and discipline**, not raw item count: the
  cockpit needs to be the load-bearing first screen (a typed attention inbox driving
  the operator's four questions), the nav needs a frozen rule so it cannot regrow,
  and detail must stay one click deep (progressive disclosure) rather than
  pre-rendered into the home scroll.
- **Recommendation: Option B (cockpit-led, nav frozen).** Make the cockpit the
  default route and the single source of "what needs me", enforce a nav budget,
  and reuse the existing pattern/token layer. Low structural risk, high decision
  payoff, no new vendor surface.

## Problem

The original audit (`HANDOFF-2026-06-15`, measured 2026-06-14): home ~72,279px
(~80 screens), ~25,452 DOM elements, 67 nav items, 13 font sizes, full-page
screenshot times out. Root cause was **information overload + no decision focus**,
not pixel alignment.

What is true **today** (current `ui_console_assets.py` baseline):

- **Nav is already pruned to a 6-item core** (Home, Work, Agents, Decisions,
  Records, Search) plus a `More` disclosure grouping ~28 secondary views into 5
  labelled groups. The 67-flat-tabs problem is structurally solved.
- **A cockpit exists**: `cockpit.title` = "What needs you now", an attention inbox
  with empty-state, an inbox-detail panel, and a work-state panel — but it is **one
  widget among several on a still-busy home**, not the unmistakable decision surface.
- **The four operator questions** (DESIGN.md: what needs attention / which task set
  owns this / what evidence / what next) are **answerable but not orchestrated** —
  the user still scans rather than being routed.

So the live problem is narrower and sharper than the 2026-06-14 snapshot: **the
cockpit is built but not yet load-bearing, and nothing prevents the nav from
regrowing back toward 67.**

## Proposed direction

**Make the cockpit the product.** The home route opens to a decision surface whose
job is to answer the four questions and hand off to detail on click. Everything
else is reachable but secondary.

### Information architecture

- **Tier 0 — Cockpit (default route).** A typed **attention inbox** is the spine:
  each item is a decision the operator can act on (owner gate awaiting approval,
  blocked chain, stale claim, at-risk taskset, unowned work, failed gate). Items
  carry kind + freshness + a primary action, ranked by urgency. Right rail =
  **work-state** (active taskset → wave → claims) so "what's happening now" is
  always visible. Reuses the existing `cockpit`/`work_state` panels — promote,
  don't rebuild.
- **Tier 1 — Core nav (≤7, frozen).** Home, Work, Agents, Decisions, Records,
  Search (current 6) + at most one more. This is a **budget**, not a snapshot:
  adding an 8th core link requires demoting another to `More`.
- **Tier 2 — More disclosure (grouped).** The 5 existing groups stay collapsed by
  default. Each group is a *destination index*, not a flat tab list.
- **Tier 3 — Detail (progressive disclosure).** Entity detail (taskset → task →
  unit, agent, message, event) opens **on click** into the existing detail panel,
  never pre-rendered into the home scroll. This is what kills the 80-screen home:
  detail is fetched, not flattened.
- **Hierarchy view** (initiative → taskset → task → unit) and **state-machine
  visibility** (waiting / active / done → drill) live under Work, surfaced into the
  cockpit only when an item *needs attention* (blocked, stale, gate-pending).

### Home cockpit + nav (ASCII sketch)

```
+----------------------------------------------------------------------------+
| [logo] Agent Runtime    [/ search]       polling*  EN/KO  D/L  Experience  |  header (command area)
+--------------+-------------------------------------------------------------+
| ACTIVE TASKSET|  WHAT NEEDS YOU NOW                          (cockpit)      |
|  AR-UI-V2     |  +------------------------------------------------------+   |
|  ####--  64%  |  | [GATE]  owner approval - release tag v0.9   [Review] |   |
|  4 active     |  | [BLOCK] TASK-AR-561 blocked-by AR-560       [Open]   |   |
| ------------- |  | [STALE] claim CLAIM-...-552 no heartbeat 3h [Reclaim]|   |
| [#] Home   *  |  | [RISK]  TASKSET-...-UPLIFT 2 units at risk  [Open]   |   |
| [=] Work      |  | [OPEN]  3 ready tasks, no claim            [Assign]  |   |
| [*] Agents    |  +------------------------------------------------------+   |
| [:)] Decisions|                                                             |
| [t] Records   |  WORK STATE                          | ATTENTION DETAIL    |
| [q] Search    |  active: TASKSET-AR-UI-V2            |  (selected inbox     |
| ------------- |  wave 3 . 4 claims . 1 review        |   item expands here  |
| [.] More >    |  - next: TASK-AR-565 (ready)         |   with evidence +    |
|   WORK        |  - state: 2 active . 1 waiting       |   the safe next      |
|   AGENTS      |                                      |   command)           |
|   COMMS       |  [ widgets: collapsed by default, opt-in ]                  |
|   RECORDS     |                                                             |
|   OPS         |                                                             |
+--------------+-------------------------------------------------------------+
```

Click any inbox row -> **Attention Detail** fills with the entity's evidence hooks
and the *one safe next command* (DESIGN.md: "click instead of ask", "every item
links to history"). Nothing on this screen requires scrolling 80 viewports.

## Scope / phases (rough sizing)

| Phase | Scope | Size |
| --- | --- | --- |
| P1 - Cockpit as default | Make cockpit the home route; rank the typed attention inbox; collapse widgets to opt-in. Reuses `renderCockpit`/`renderWorkState`. | S-M |
| P2 - Nav budget freeze | Codify the <=7 core rule + group taxonomy; add a lightweight check (gate or test) that fails if core nav exceeds budget. | S |
| P3 - Progressive detail | Ensure all entity detail opens via the detail panel on click, not pre-rendered; audit home for any flattened detail and lazy-load it. | M |
| P4 - Hierarchy + state drill | Initiative->taskset->task->unit view + waiting/active/done drill under Work, with cockpit cross-links for at-risk items. | M-L |

P1+P2 deliver the decision-focus win quickly; P3 reclaims the screen budget; P4 is
the deeper IA payoff and can follow.

## Risks / open questions

- **Inbox ranking is a product decision.** What counts as "needs you" and the
  priority order (gate > blocked > stale > risk > unowned?) is the Owner's call;
  the wrong ranking turns the cockpit into noise. Start with the order above, make
  it tunable.
- **Regression risk to a ~12k-LOC single-shell renderer.** The console is
  server-rendered HTML + vanilla JS in `ui_console_assets.py`; structural moves
  need the Playwright e2e foundation (TASK-AR-546, still candidate) to be safe.
- **Nav budget enforcement** could be felt as friction by future feature work — but
  that friction is the point (Owner: features were added to be pruned later).
- **Open:** does "Search" stay a core link or become `/`-palette-only (freeing a
  core slot)?

## Recommendation

Adopt **Option B: cockpit-led, nav frozen.** Greenlight **P1 + P2** first (small,
high-leverage, reuse-only). This makes the existing cockpit load-bearing and stops
nav regrowth; then P3/P4 deepen the IA. All work stays inside the accepted
token/pattern layer (DESIGN-SYSTEM.md) — no new vendor surface, no new visual
direction needed for this sub-project.
