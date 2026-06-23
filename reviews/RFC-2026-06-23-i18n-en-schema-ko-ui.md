---
type: rfc
id: RFC-2026-06-23-i18n-en-schema-ko-ui
audience: owner
status: proposal
signal: decide
tags: [rfc, i18n, localization, ko, en, schema, string-extraction]
supersedes_context: HANDOFF-2026-06-15-ui-redesign-and-product-structure.md (sub-project #4)
---

# RFC — i18n: EN Canonical Schema + KO UI Localization

Proposal for the Owner to pick a direction. **Docs only — no code in this PR.**
Backs deferred sub-project **#4** from the 2026-06-15 UI handoff.

## Bottom Line

- The i18n **foundation already exists** (`TASK-AR-341`): a Python-side string
  table (`ui_state.I18N_STRINGS`, ~74 keys, `{ "ko": ..., "en": ... }`), served as
  JSON via `/api/i18n`, applied client-side by `t()` / `applyTranslations()` over
  `[data-i18n]` (+ aria-label/title variants), with a `ko`-default language toggle
  persisted in `localStorage`. The architectural decision (**EN schema, KO UI,
  default KO**) is effectively already made and shipped at small scale.
- The open work is **coverage and discipline**, not architecture: most UI strings
  are still inline English, error/toast copy is hardcoded EN
  (`RESEARCH-2026-06-14-product-maturity` scored i18n 3/5 for exactly this),
  there is no locale-aware date/number formatting, and there is no gate stopping
  new untranslated strings from landing.
- **Recommendation: Option A (extend the shipped table + add an extraction gate).**
  Keep the existing EN-canonical / KO-UI model, expand the string table to cover
  the operator-facing surface, add locale formatting, and add a lightweight check
  that fails when new user-facing UI strings bypass the table. Do **not** adopt a
  heavyweight i18n framework — the stdlib server + ASCII-only app.js constraint
  favors the current JSON approach.

## Problem

The Owner leaned toward **EN canonical schema/docs + KO UI localization**, folded
into the IA work. Current reality:

- **Already working:** `ui_state.DEFAULT_LANGUAGE = "ko"`, `I18N_LANGUAGES =
  ("ko", "en")`, ~74 keyed strings (nav groups, view titles, buttons, cockpit/
  work-state hero strings, workspace switcher). `app.js` keeps **ASCII-only** by
  design — KO values live Python-side and arrive as JSON, so the served script
  never carries non-ASCII (a deliberate, sound constraint).
- **Gaps (from `RESEARCH-2026-06-14-product-maturity-ui-assessment`, i18n = 3/5):**
  - Error / toast / validation copy is **hardcoded English** in the renderer.
  - **No locale formatting** — dates, numbers, relative times render one way.
  - Coverage is partial: only ~74 keys vs. a 30+ view surface; most labels are
    still inline literals.
  - **No guard** — nothing prevents the next feature from adding an untranslated
    inline string, so coverage will silently regress.

So this is the **smallest** of the three sub-projects (the handoff already called it
"small") and the most mechanical: the schema decision is made; the work is
extraction, coverage, formatting, and a gate.

## Proposed direction

Keep the shipped model and make it complete and self-defending.

### i18n architecture (extend, don't replace)

- **EN is the canonical schema.** Keys, frontmatter, docs, API identifiers, log
  lines, and machine-readable records stay **English-only** (they are contracts,
  not UI). KO is a *presentation* locale layered on top — never in data.
- **String table stays Python-side, served as JSON.** Preserve the ASCII-only
  app.js invariant: all human-facing UI text resolves through `t(key)` against
  `I18N_STRINGS`; the browser only ever sees `[data-i18n]` keys + a JSON values
  payload. This is the existing `/api/i18n` contract — extend its table, don't
  re-plumb.
- **Three string classes (explicit boundary):**

  | Class | Example | Localized? |
  | --- | --- | --- |
  | UI chrome / operator copy | nav, buttons, cockpit, toasts, errors, validation | **Yes — KO + EN** |
  | Runtime data identifiers | task ids, statuses, role names, event types | **No — EN canonical** |
  | Author content | review/plan/spec markdown, agent output | **No — passthrough** |

- **Add locale-aware formatting.** A small `formatDate` / `formatNumber` /
  `formatRelative` helper keyed on `currentLanguage` (KO vs EN date order, relative
  time strings). No new dependency — vanilla `Intl` is sufficient.
- **Add an extraction gate.** A check (sibling to `design_system_gate`) that flags
  new user-facing string literals in renderers that are not routed through `t()` /
  `data-i18n`, so coverage cannot silently regress. This is the discipline piece.

### KO locale + what stays EN

- **KO UI:** every operator-facing string — nav, view titles, buttons, cockpit
  inbox kinds + actions, work-state labels, toasts, error/validation copy,
  empty-states.
- **Stays EN (canonical):** entity ids (`TASK-AR-…`), state-machine state names,
  role keys, event-type names, gate names, file paths, commands, and all
  `reviews/` / `docs/` records (these are the schema and audit trail).

## Scope / phases (rough sizing)

| Phase | Scope | Size |
| --- | --- | --- |
| P1 - String extraction sweep | Move remaining inline operator strings into `I18N_STRINGS` with KO+EN; cover cockpit/work-state/error/toast/empty-state copy. | M |
| P2 - Locale formatting | `Intl`-based date/number/relative-time helpers keyed on `currentLanguage`; apply at render sites. | S |
| P3 - Extraction gate | Lightweight gate/test flagging new un-keyed user-facing literals in renderers; wire into the UI gate chain. | S |
| P4 - KO copy pass | A reviewer/owner pass on KO phrasing for tone + consistency across the expanded table. | S |

This is the cheapest sub-project; P1+P3 are the load-bearing pair (coverage +
no-regression).

## Risks / open questions

- **ASCII-only app.js must hold.** Any KO literal that leaks into the served JS
  breaks the invariant; the extraction gate must also catch non-ASCII in app.js.
- **Coverage is a moving target.** Without P3 (the gate), every new feature
  re-opens the gap; the gate is what makes this durable rather than a one-time
  sweep.
- **Translation quality.** Machine-drafted KO needs a human pass (P4) — error and
  governance copy especially must read naturally to the Owner.
- **Open:** should KO date/number formatting follow the OS locale or the explicit
  language toggle? (Recommend the toggle, for predictability.)
- **Open:** are any `reviews/`/`docs/` summaries wanted in KO, or strictly the live
  UI? (Recommend UI-only; keep records EN-canonical for audit.)

## Recommendation

Adopt **Option A: extend the shipped EN-schema / KO-UI table + add an extraction
gate.** Greenlight **P1 + P3** together — coverage without the gate regresses, the
gate without coverage is empty. P2 (formatting) and P4 (KO copy pass) follow
cheaply. No new framework, no change to the `/api/i18n` contract or the ASCII-only
app.js invariant. This is the lowest-risk, lowest-cost of the three RFCs and a
natural companion to the cockpit work in RFC #1 (the cockpit's new strings should be
keyed from day one).
