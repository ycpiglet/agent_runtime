---
type: research
id: RESEARCH-2026-06-14-unified-decision-console
audience: owner
status: complete
tags: [research, ui, console, entity-graph, command-palette, decision-making]
---

# Unified Decision/Operations Console — Research Synthesis

Backs `TASKSET-AR-UNIFIED-DECISION-CONSOLE` (TASK-AR-539..545). Sourced from
multi-agent web research over primary product docs.

## The universal formula

Every "unified browser" reduces to two primitives: **(1) a typed entity graph**
(typed node + typed directional relations) and **(2) an IA of faceted index +
detail pages with pluggable tabs/cards**. Decision surfaces (palette, timeline,
saved views) layer on top.

## 1. Entity-graph catalogs (IDPs)

- **Backstage**: entities described in YAML with a 4-field envelope (`apiVersion`/`kind`/`metadata`/`spec`); well-known kinds (Component/API/Resource/System/Domain/Group/User/Location/Template); typed directional **relations** with auto-derived inverses (`ownedBy`/`ownerOf`, `partOf`/`hasPart`, `dependsOn`/`dependencyOf`); plugins attach to entity pages via `EntityCardBlueprint`/`EntityContentBlueprint` (cards/tabs). Relations derived from `spec` at ingestion.
- **Sourcegraph**: cross-repo code navigation (go-to-def, find-refs, hover) via precise (SCIP) + search-based tiers; every result is an entry point into the graph.
- **Glean**: enterprise knowledge graph (content + people + activity), 100+ connectors, permission-aware at index + query time.
- **Port/Cortex**: user-defined **blueprints** (Port) / JSON-schema custom entity types (Cortex) + relations + mirror/calculation/aggregation properties; standards modeled as Scorecard entities.
- **For us:** define an envelope (`kind`/`metadata`/`spec`/`relations`) over plan/review/issue/pr/git/branch/skill/council/seminar/initiative/taskset/task/unit/wave; derive relations from existing frontmatter/links; generate a catalog manifest the console reads (TASK-AR-539).

## 2. Command palette & universal search

- VS Code: one input, **prefix scoping** — `>` commands, `@` symbol-in-file, `#` workspace symbol, `:` go-to-line. Linear: Cmd-K context-aware menu acting on the focused entity, shows shortcuts. Raycast: Root Search across apps/files/extensions + **Action Panel** (Cmd-K within results: primary action on Enter, secondary list). Superhuman: forgiving fuzzy + synonyms ("archive" → Mark Done).
- **For us (TASK-AR-540):** Cmd-K over the catalog; prefix scoping `>`/`@`/`#`/`:`; blended cross-kind results; in-result quick actions; context-aware on focused entity.

## 3. Activity feeds, timelines & provenance

- GitHub: PR/issue **timeline event types** (`committed`, `reviewed`, `labeled`, `cross-referenced`, `connected`, `merged`, `closed`, `reopened`…) = who/what/when lineage; separate **audit log** (`category.operation`, owner-only, 180d). Linear: per-issue history with grouping/collapsing; health-stamped project/initiative updates. Datadog Audit Trail (100+ event types, filterable like logs). Grafana annotations overlay events on time-series.
- **For us (TASK-AR-542):** typed event stream per entity ingested from git/gh/claims/pane-events/council-verdicts; grouped global feed; separate filterable audit stream.

## 4. Faceted/saved views & rollups & needs-attention

- Linear: Custom Views (save/share/favorite/subscribe), filters with match counts, grouping → swimlanes (incl. by health). GitHub Projects: table/board/roadmap, custom fields, group-by, Insights charts. Jira: saved filters/JQL → dashboard gadgets (real-time propagation). Notion: relation+rollup (count/sum/%complete), linked databases (views local), synced blocks. Datadog: Monitor Quality + Case Management = needs-attention triage; dashboards as rollups.
- **For us (TASK-AR-543):** faceted saved views + match counts + grouping/swimlanes; hierarchy rollups (initiative→taskset→task) as counts+representatives; needs-attention inbox (blocked/stale/at-risk/unowned).

## 5. Cross-linking / knowledge discovery

- Notion relations+rollups (structured decision metrics). Obsidian backlinks/unlinked-mentions/graph/transclusion (page-level). Logseq/Roam block-level bidirectional links + block embeds (atomic provenance). Linear typed issue relations (Blocked-by/Blocks/Related/Duplicate). Height (now shut down): AI over a unified task+chat graph (auto-triage, live spec) — note human-in-the-loop "suggest" caveat.
- **For us (TASK-AR-541/545):** entity detail with relations both ways + backlinks; transclusion of linked excerpts; council/seminar verdict fields surfaced.

## IA synthesis (for this product)

- **Entity catalog** (539) is the spine. **Surfaces:** command palette (540), entity detail + backlinks (541), activity/provenance timeline + audit (542), faceted views + rollups + needs-attention (543), live SCM (544), governance docs (545). **Reads** generated manifests (catalog/board/reviews index from the store restructure); records stay canonical.

## Sources

Backstage docs (descriptor/system-model/well-known-relations/extension blueprints/TechDocs), Sourcegraph docs (code-navigation/queries/cross-repo), Glean docs (knowledge-graph/permissions), Port & Cortex docs (blueprints/scorecards/entity-types), VS Code/Linear/Raycast/Superhuman (palettes), GitHub (timeline event types/audit log/Projects), Linear (custom-views/history/updates), Datadog (audit trail/monitor quality/case management), Grafana (annotations), Notion (relations-rollups/linked-databases/synced-blocks), Obsidian/Logseq/Roam (backlinks/graph/embeds), Height (Wayback).
