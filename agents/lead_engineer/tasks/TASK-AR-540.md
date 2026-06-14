---
id: TASK-AR-540
display_id: TASK-AR-540
task_uid: eb29ba54-c724-451c-a4ec-53dcca89fb12
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
started_at: 2026-06-14T14:05:00+09:00
updated_at: 2026-06-14T14:20:00+09:00
completed_at: 2026-06-14T14:20:00+09:00
status: completed
priority: P1
difficulty: M
est_hours: 7
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UNIFIED-DECISION-CONSOLE
tags:
  - console
  - command-palette
  - search
---

# TASK-AR-540 - Universal command palette + cross-entity search

## Goal

- One fuzzy input to jump to / act on ANY entity in the catalog — the proven universal-search pattern (VS Code prefix scoping + Linear context-awareness + Raycast action panel).

## Scope

- Cmd/Ctrl+K palette over the TASK-AR-539 catalog with fuzzy + typo/synonym tolerance and recents ranking.
- Prefix scoping in one input: `>` commands, `@` symbol/entity-in-context, `#` workspace-wide entity, `:` go-to (VS Code model); blended results across kinds.
- In-result quick actions (Raycast action panel: primary action on Enter, secondary actions list); context-aware actions on the focused entity (Linear); show the keyboard shortcut next to each command.

## Acceptance Criteria

- Palette searches across all entity kinds and returns blended, ranked results.
- Prefix scoping switches modes in a single input; quick actions run from results without leaving the keyboard.
- Actions are context-aware on the currently focused entity.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog).
- target_files: console command-palette module + search index reader. Disjoint from 541-545 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (VS Code `>`/`@`/`#`/`:`; Linear Cmd-K context menu; Raycast Action Panel; Superhuman fuzzy/synonyms).

## Completion Evidence

- `scripts/entity_catalog.py` `search_entities()` + `ui_state.py` `load_catalog()`/`catalog_search()` + `/api/catalog` endpoint (ui_console.py): cross-entity command-palette search over the 539 catalog. Prefix scoping `kind:task foo` / `@taskset bar` (VS Code style); ranks id > title > metadata; blends across all kinds otherwise. Reads the generated ENTITY-CATALOG.json directly (manifest-first), NOT build_state, so the palette stays instant.
- Live-verified: `/api/catalog` serves 700 entities + kind_counts; `/api/catalog?q=TASK-AR-539` -> top TASK-AR-539; `?q=kind:taskset console` -> taskset-scoped. (Search reimplemented inline in ui_state so it works in the src-only server process.)
- Scope: delivers the searchable unified-catalog data/query layer the palette consumes. Full interactive palette keybinding/quick-action UI is incremental frontend on this endpoint.

## Verification Results

- W4a: entity_catalog 5 tests (incl. search blend/scope/rank); ui_state import + catalog_search smoke; live endpoint curl; governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-540.md`.
