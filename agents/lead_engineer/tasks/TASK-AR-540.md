---
id: TASK-AR-540
display_id: TASK-AR-540
task_uid: eb29ba54-c724-451c-a4ec-53dcca89fb12
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
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
