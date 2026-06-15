# Decision-First Console IA — Design

- **Date:** 2026-06-15
- **Status:** approved (Owner, 2026-06-15)
- **Owner:** uiux (UI/UX) + lead-engineer
- **Sub-project:** UI redesign #1 of the 4-way decomposition (see `reviews/HANDOFF-2026-06-15-ui-redesign-and-product-structure.md`). #2 agent-org delegation is done; #3 visual identity and #4 i18n follow.
- **Basis:** UI/UX audit 2026-06-14 (home = 72,279px ≈ 80 screens, 25,452 DOM elements, 4,382 blocks, 67 nav items, full-page screenshot times out; not decision-supporting).

## Bottom Line

The console shows *data*, not *decisions*. This sub-project makes the home a **decision-first cockpit** whose hero is an **Attention Inbox** ("what needs me now"), prunes the 67-item nav to a core 7, and applies **progressive disclosure** (essentials on screen, detail on interaction) — turning an 80-screen dump into a 1–2 screen cockpit. Done **incrementally** on the current monolith (Approach A), preserving the just-landed maturity behaviors (responsive, a11y, SSE, i18n, validation). No new data is invented — every inbox signal is derived from existing gates/records.

## Problem

- Home renders ~everything inline (80 screens / 25K elements / 4,382 blocks); no information hierarchy or decision focus; renders heavily (screenshot timeout).
- 67 nav destinations overwhelm; the Owner intentionally over-added features to prune later — now is the prune.
- The Owner's core value ("의사결정·운용 최적화 UI") is unmet: there is no "what needs my attention / what to decide next" surface.

## Goals

1. **Attention Inbox hero**: surface only what needs a human decision/intervention now, grouped by urgency, derived from real signals; click → detail + action; empty inbox = "nothing to handle" (a good state).
2. **Nav prune**: 67 → a core of ~7, with the rest behind a collapsed `More`.
3. **Progressive disclosure**: cockpit shows counts/summaries; detail opens on click/hover in a panel — not inline.
4. **Preserve maturity**: keep responsive (`@media`), a11y (skip-link/landmarks/aria), SSE (`/api/stream`), i18n, and form validation through the restructure.
5. **i18n surface**: EN data/schema stays; the UI offers a KO/EN toggle (folds in sub-project #4).
6. **Incremental (Approach A)**: keep the `ui_console.py` monolith; add the cockpit + prune + a derived inbox read. (Component/token extraction = sub-project #3, a follow-on.)

## Non-Goals (deferred)

- Visual identity overhaul: design tokens / 309-font-size cleanup, 2.5D agent characters, insight-graph redesign → **sub-project #3**.
- Full UI extraction from the 479KB monolith into components/templates → #3.
- Deep i18n resource externalization → #4.
- New backend/runtime data — the inbox consumes existing records only.

## Design

### A. Attention Inbox (home hero)
A derived read (`ui_state.attention_inbox(root)`, stdlib, no new storage) aggregates real signals into ranked groups:

| Group | Source (existing) |
| --- | --- |
| Approval pending | `dispatch_gate` owner-gate decisions · `approval_required` items · open PRs (gh, when available) |
| Blocked | work-items `status: blocked` · unresolved `blocked_by` |
| Stale | `verification_freshness_gate` findings · items not updated > N days |
| Gate failures | recent `owner_governance_gate` failures · `closure_gate` misses |
| Cost anomalies | `work_efficiency` actual > est · `budget_cap` breaches |
| Runtime anomalies | `multi_host_claim_gate` conflicts · `claim_reaper` expired · orphan claims |

- **Item (card) contract**: `{group, id, title, why, age, severity, action}` — compact card shows title + why + age; severity orders within a group; `action` names the next step (approve / dispatch / resolve / review).
- **Empty state**: each group with 0 items collapses; a fully-empty inbox shows "처리할 것 없음 / Nothing needs you" (explicitly a healthy state, not a blank).
- Served via a new `/api/inbox` endpoint + an inbox view in the cockpit; reuses the existing `ui_state` cache + SSE for live refresh.

### B. Nav prune (67 → core 7)
Core: **Home** (inbox) · **Work** (initiative/taskset/unit) · **Agents** (org + activity) · **Decisions** (council/review/PR) · **Records** (evidence/events) · **Search** · **More** (the remaining 60+ collapsed, discoverable but not competing). The current 67 routes keep working (no dead links) — they move under `More`/their section, not deleted.

### C. Secondary views (tab/drill — not home-inline)
- **Work**: the initiative→taskset→unit state board (waiting/active/done counts + drill-down) — the second hero; consumes `org_read_api.work_state`.
- **Agents**: org tree + live agents (`org_read_api.org_tree`); 2.5D characters are #3.
- **Decisions**: council/seminar/review/PR surface.

### D. Progressive disclosure
Cockpit = counts + top-N summaries. Detail opens in a side panel/drawer on click (keyboard-accessible, focus-managed). No section renders its full content inline on the home. Target: home ≤ 2 screens, DOM elements ≤ ~1,500.

### E. i18n
A UI language toggle (KO/EN) over the existing i18n layer; data/schema stay EN. Inbox `title`/`why`/group labels are localizable; values (ids, statuses) are not translated.

### F. Architecture (incremental)
- New: `ui_state.attention_inbox(root)` (derived read, stdlib, PyYAML-free) + `/api/inbox` route in `ui_console.py` + a cockpit home view + nav-prune (group the 67 links under sections + `More`).
- Reuse: the `_STATE_CACHE` + SSE warm path; `org_read_api` for work-state/org; existing gates as signal sources.
- Preserve: `/app.css` `@media`, skip-link/landmarks, `/api/stream`, i18n, validation (regression-tested).
- The monolith stays; extraction is #3.

## Build sequence (Stage-B taskset units)
1. `attention_inbox` derived read + signal adapters (stdlib) + tests.
2. `/api/inbox` endpoint + cockpit home view (replaces the 80-screen home) + empty-state.
3. Nav prune: core-7 + `More` grouping (no dead routes) + tests.
4. Progressive-disclosure detail panel (counts → drawer) + a11y focus management.
5. Work state board as the secondary hero (reuse `org_read_api.work_state`) + drill-down.
6. i18n KO/EN UI toggle over existing layer.
7. E2E + regression: home ≤ 2 screens / DOM budget; maturity behaviors preserved.

## Risks
- **Monolith edits** (479KB) are fragile → small, test-guarded changes; preserve the token-CSS + a11y/SSE/responsive (regression suite is the guard).
- **Signal accuracy**: the inbox must derive from real gates only (no fabricated items); false-empty or false-alarm both erode trust → unit-test each adapter against fixtures.
- **Don't regress maturity** (#546–551): keep the E2E feature assertions green.
- **Scope creep into #3**: resist visual/character/graph work here; this is IA + decision focus only.
