---
id: TASK-AR-541
display_id: TASK-AR-541
task_uid: 086d2ce1-9cd3-42c4-ba96-12a45a9f2be2
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
  - entity-detail
  - backlinks
---

# TASK-AR-541 - Entity detail pages + cross-links/backlinks

## Goal

- Make any entity a rich detail surface with pluggable tabs/cards (Backstage `EntityContentBlueprint`/`EntityCardBlueprint`) and "what references this" backlinks (Obsidian/Notion), so a decision-maker can drill from any artifact into its full context.

## Scope

- Per-entity detail page: Overview + pluggable tabs/cards by kind (e.g. a task shows claims/units/PR/verdicts; a review shows decisions/links).
- Relations rendered both ways: forward (`dependsOn`, `partOf`) and inverse backlinks (`referencedBy`, "linked mentions"); surface unlinked mentions where cheap.
- Linked-excerpt transclusion (show the referenced block/section inline) for decision synthesis.

## Acceptance Criteria

- Each entity kind renders an Overview + relevant tabs/cards from the catalog.
- Backlinks list every entity that references the current one (derived, not hand-maintained).
- Cross-links navigate without leaving the console.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog + relations).
- target_files: console entity-detail module + card/tab registry. Disjoint from 540/542-545 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (Backstage entity tabs/cards; Notion relations+rollups; Obsidian backlinks/unlinked mentions/transclusion; Logseq/Roam block-level provenance).
