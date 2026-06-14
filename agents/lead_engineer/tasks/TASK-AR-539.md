---
id: TASK-AR-539
display_id: TASK-AR-539
task_uid: caa68fb5-1275-4aa8-aee6-a6cafa792944
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
started_at: 2026-06-14T12:05:00+09:00
updated_at: 2026-06-14T12:15:00+09:00
completed_at: 2026-06-14T12:15:00+09:00
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-UNIFIED-DECISION-CONSOLE
tags:
  - console
  - entity-model
  - catalog
  - foundation
---

# TASK-AR-539 - Unified artifact entity model + catalog manifest

## Goal

- Make every meaningful artifact the product operates/archives a first-class, browsable entity in ONE typed graph — the Backstage "software catalog" pattern (typed node envelope + typed directional relations) — so the console can surface plan/review/issue/pr/git-log/branch/skill/council/seminar/initiative/taskset/task/unit/wave/state/history uniformly. This is the foundation every other console task builds on.

## Scope

- Define an entity envelope (`kind`, `metadata` {id/title/tags/links/owner}, `spec`, `relations`) covering all artifact kinds above.
- Define typed directional relations (e.g. `derivedFrom`/`hasArtifact`, `dependsOn`, `decidedBy`, `references`/`referencedBy`, `partOf`/`hasPart`, `ownedBy`) — many derived from existing frontmatter/links at ingestion (Backstage-style).
- Generate a catalog manifest (JSON) the console reads (manifest-first; coordinate with TASK-AR-537); ingest from existing stores (tasks, reviews index, claims, git, gh, skills registry).

## Acceptance Criteria

- A catalog manifest enumerates entities of every listed kind with stable ids + typed relations.
- Relations are derivable/queryable (forward + inverse) and traceable back to source files.
- The model is extensible (new kind = config, not a rewrite).

## Dependency / Footprint

- depends_on: TASK-AR-535 (canonical IDs), soft TASK-AR-537 (read-index).
- target_files: `scripts/entity_catalog.py` (new), catalog manifest JSON (new), console catalog model. Foundation for 540-545.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (Backstage kind/metadata/spec + well-known relations; Port blueprints; Glean knowledge graph; Cortex JSON-schema custom types).

## Completion Evidence

- `scripts/entity_catalog.py` + `tests/test_entity_catalog.py`: a Backstage-style typed entity graph. Uniform envelope `{kind, id, title, metadata, relations}`; typed directional relations (`partOf` from the classification parent graph, `addresses` from host feedback -> tasks, `references` from review filenames -> tasks). `--check`/`--write`.
- Generated `agents/project/work-items/ENTITY-CATALOG.json`: **693 entities across 11 kinds** (task 219, taskset 32, initiative 8, unit 13, host_feedback 7, plus review/council/seminar/meeting/research/verification 414). Manifest-first (TASK-AR-537): reads the generated classification + queue + review filenames, not raw re-scan.
- This is the foundation the console tasks (TASK-AR-540..545) read instead of re-deriving the graph.

## Verification Results

- W4a: 4 catalog tests pass; `--check` findings=0; `--write` emits the manifest; governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-539.md`.
