# DIAGNOSTIC — UI Design-System Maturity & Asset-ization Gap

- **Date:** 2026-06-18 (09:31 KST)
- **Scope:** `src/agent_runtime/ui_console.py` (the entire web console) + `docs/design/`
- **Question:** Is the UI being asset-ized (tokens + reusable components), or re-styled
  from scratch on every redesign/refactor?
- **Method:** static inspection of the single console file + design docs. Counts are from
  `grep`/`sed` over the file; line ranges are exact.

## Bottom Line

The console has a **documented design intent and a mature *color/theme* token layer**, but
**no reusable component layer and no spacing/typography/radius scale**. "Components" today
are CSS class clusters inside one ~5,100-line stylesheet, hand-wired per context. There is
**no mechanical gate** preventing ad-hoc styles. Net: **color is genuinely asset-ized;
everything else is effectively re-decided per surface** — so the Owner's suspicion ("매번
새로 만드는 것 아닌가") is correct for everything except color/theme.

**Maturity: 2.0 / 5** (color tokens 4/5 pull the average up; structure & component API ≈ 1/5.)

## Structural facts

The whole UI lives in **one 13,343-line Python file**, `ui_console.py`, as three template
strings:

| Region | Lines | Size | Notes |
|--------|-------|------|-------|
| `HTML` | 23–1058 | ~1,035 | one static document |
| `CSS`  | 1061–6208 | **~5,147 lines, ~1,129 rule blocks, 831 distinct class names** | one monolithic stylesheet |
| `JS`   | 6210–12898 | ~6,688 | all behavior, hand-wired |

There is **no separate CSS file, no component file, no token file**. `var(--…)` is used
**1,255 times** (good — tokens *are* consumed), `!important` only 8 times (good), inline
`style=` only 24 (good). The problem is not messy overrides — it is **missing
abstraction layers**.

## Scorecard (the 8 asset-ization categories)

| # | Category | Score | Evidence |
|---|----------|:---:|----------|
| 1 | **Color tokens** | 🟢 4/5 | ~90 semantic CSS vars; dual scope `:root` (light) / `[data-theme="dark"]`; `surface/ink/line/status` families + `*-soft`/`*-line` variants; TASK-AR-320 migrated literals→tokens; WCAG-aware. Genuinely tokenized & reused. |
| 2 | **Typography scale** | 🔴 0/5 | **No** `--font-size/--text/--leading/--weight` tokens. Sizes hardcoded & scattered: `12px`×99, `11px`×87, `13px`×62, `10px`×21, `14px`×16, plus px/rem/em mixed. No type scale. |
| 3 | **Spacing scale** | 🔴 0/5 | **No** `--space/--gap` tokens. **523** raw `padding/margin/gap` literal declarations. No 4/8px grid. |
| 4 | **Radius scale** | 🟡 2/5 | One `--radius` token reused 109× (good), but `999px`×36, `6px`×18, `8/4/3/2/12/10px` scattered alongside. No `sm/md/lg` scale. |
| 5 | **Shadow / elevation** | 🟡 3/5 | `--shadow`, `--shadow-pop`, `--focus` tokenized & reused. Two levels only, no formal elevation scale, but consistent. |
| 6 | **Button/Input/Card/Modal/Table API** | 🔴 1/5 | **No reusable component layer.** No `.btn` system: buttons = bare `button {}` (L1555) + a single `button.ghost` + per-context overrides (`.config-form button`, `.inbox-item-actions button`, `.task-card-actions button`, `.taskset-bulk-bar button.ghost`…). No render-function / JS-component with a stable prop API. Same story for Card/Modal/Table — class clusters, not components. |
| 7 | **Component variants** | 🔴 1/5 | Only ad-hoc modifiers (`.ghost`, `.pill`, `.tab`, `.action`, `.chip`). No systematic matrix (e.g. button primary/secondary/danger/ghost × sizes; input default/error/disabled/focus states as a defined set). |
| 8 | **Ad-hoc-style prohibition** | 🟡 2/5 | Intent exists: `DESIGN.md` says *"Components reference tokens only"* + a "Do not" list. **But no stylelint, no lint rule, no CI gate.** Nothing mechanically blocks the next page from hardcoding `font-size:13px; padding:11px`. Enforcement = author discipline only. |

## What exists vs. what doesn't

**Exists (real assets):**
- Accepted design guide `docs/design/agent-runtime/DESIGN.md` (status: accepted) — Linear-like
  operator-console direction, status-color semantics, "Do not" rules, amendment log
  (light-theme switch, TASK-AR-320 token implementation).
- Dual-theme **color token system** (TASK-AR-320) — the one fully asset-ized layer.
- Plans/specs: `docs/superpowers/plans/2026-06-11-agent-runtime-ui-design-system.md`,
  `…/ui-ux-v2-console.md`, `…/ui-design-implementation.md`; specs
  `…/2026-06-15-decision-first-console-ia-design.md`, `…/2026-06-17-llm-wiki-design.md`.
- ~70 benchmark brand references under `docs/design/*` (Linear, Stripe, Apple, Notion, …) —
  inspiration material, not consumed assets.

**Does not exist:**
- A component library you can *assemble* from (Button/Input/Card/Modal/Table with documented
  props/variants/states).
- Scale tokens for typography / spacing / radius — so each location re-picks literal values.
- A **pattern** layer (composed, repeatable units: e.g. "filterable list", "evidence card",
  "command bar", "empty/error/loading state").
- Any **mechanical gate** (lint/CI) that fails a build on raw color/px or new bespoke classes.
- A page/layer separation: page logic, layout, components, and tokens are all interleaved in
  one file, so a "page" cannot be kept to layout + data binding only.

## Why redesigns keep re-deriving the look

Because the only reusable layer is color, every new surface (a) re-chooses spacing/type/radius
literals by eye and (b) writes new CSS classes (831 and counting) instead of composing
existing components. With no gate, drift is invisible until someone audits. This is exactly
the "rebuild every time" pattern the Owner flagged. Color/theme is the proof that the team
*can* asset-ize — the gap is that it was only done once, for one layer.

## Recommended remediation (sequenced by ROI)

1. **Extract 3 scale tokens** next to the existing color tokens: `--text-*` (type scale),
   `--space-*` (4/8px grid), `--radius-sm/md/lg`; replace scattered literals. *Low risk,
   highest ROI — closes categories 2/3/4.*
2. **Define 5 component standards** (Button/Input/Card/Modal/Table) as a base class + a
   documented variant/state matrix; refactor existing usages onto them. *Closes 6/7.*
3. **Add a pattern layer** for repeatable composites (list/evidence/command-bar/state-views).
4. **Add a gate** — stylelint (no raw color/px, token-only) + CI check — to turn category 8
   from "intent" into "enforced". *Closes the recurrence.*
5. **(Optional) modularize** the 5,147-line CSS into tokens / base / components / patterns /
   layout; consider splitting `ui_console.py` along the same seams.
6. **Author `docs/design/DESIGN-SYSTEM.md`** as the single governance contract: the
   asset-ization taxonomy (token / ui-component / pattern / one-off), the "use existing
   first" rules, and the gate definition.

## Cross-refs

- Design intent: `docs/design/agent-runtime/DESIGN.md`
- Org-design precedent (role topology, gstack, blind-Delphi): `reviews/RESEARCH-2026-06-14-agent-org-design-references.md`
- Current designer role: `src/agent_runtime/templates/project/agents/uiux_designer/SKILL.md` (single generalist)
