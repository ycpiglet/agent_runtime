# REVIEW-2026-06-13 subtask + dependency model, timeline, dependency graph (TASK-AR-330)

## Bottom Line

Task frontmatter now carries a formal subtask + dependency model
(`parent_id`, `blocks`, `blocked_by`). A single read-only derivation in
`ui_state.py` turns that model into one canonical edge set that feeds three
views consistently - the board, a new ClickUp/Asana-style horizontal-bar
Timeline, and a dependency graph that reuses the Live Map's SVG node/edge
primitives. A new owner-governance gate (`dependency_cycle_gate.py`) warns when
the `blocks`/`blocked_by` graph contains a cycle.

## Problem

Subtasks and dependencies were prose-only. There was no machine-readable
hierarchy/dependency model, no timeline, no dependency graph, and nothing that
flagged an unsatisfiable circular dependency (A waits on B waits on ... waits on
A). Acceptance required dependencies to show consistently across
board/timeline/graph and a gate to warn on cycles.

## Design

- **Frontmatter model.** `load_tasks` now extracts `parent_id` (subtask
  hierarchy) plus `blocks` / `blocked_by` (directed dependencies). Both list and
  inline-scalar shapes are tolerated and deduped (`_string_list`).
- **Single source of truth.** `_normalize_dependency_edges` folds `blocks`
  ("this -> X") and `blocked_by` ("X -> this") into one deduped
  *blocker -> blocked* edge set. `build_dependency_graph` and `build_timeline`
  both consume it, and so does the gate, so a dependency renders identically in
  every view and the gate warns on exactly the cycle the UI shows.
- **Graph shares Live Map shape (AR-326).** Dependency-graph nodes use the same
  `id/kind/label` node shape and the same client-side SVG ring layout +
  node/edge rendering primitives as the Live Map, rather than a parallel
  renderer.
- **Cycle detection.** `detect_dependency_cycles` is a pure DFS (grey/black
  coloring) over the canonical edges, returning canonicalized cycle chains. It
  returns `[]` for an empty edge set, which is the key no-op property.
- **Gate.** `scripts/dependency_cycle_gate.py --check` scans task frontmatter,
  runs the same detection, prints `findings=N`, and exits 1 only when a cycle
  exists. It is OFF/no-op-safe: with zero `blocks`/`blocked_by` declarations (the
  current repo state) it exits 0 with `findings=0`, so wiring it into
  `owner_governance_gate.py` does NOT change the clean-repo stop-hook `approve`
  decision (`tests/test_stop_hook_owner_governance.py`).
- **Chain parity.** The gate ships byte-identical in
  `src/agent_runtime/templates/project/scripts/` and is wired into BOTH the root
  and template `owner_governance_gate.py` chains in the same relative position
  (after `footprint_conflict_gate`), satisfying
  `tests/test_owner_governance_chain_parity.py`.

## UI

- New WORK-group sidebar links **Timeline** (`work/timeline`,
  `#view-timeline`) and **Dependencies** (`work/dependencies`, `#view-deps`).
  No horizontal tabs.
- Timeline: per-taskset lanes with horizontal status-colored bars, a dependency
  arrow list, and a cycle-warning banner.
- Dependency graph: SVG graph with `dependency` (solid) and `parent` (dashed)
  edges; cycle nodes/edges are highlighted and the same warning banner appears.
- All new CSS colors flow through `var(--token)` (e.g. `--success-line`,
  `--warning-soft`, `--danger`, `--blue`, `--subtle`); no raw hex/rgba outside
  the token blocks (`test_ui_console_*_css_uses_tokens_not_raw_hex`). All
  rendered dynamic fields are `escapeHtml`-ed, and the JS stays ASCII-only so
  the Windows `node --check` stdin (cp949) guard keeps passing.

## Verification

- `tests/test_ui_state.py`, `tests/test_ui_console.py`,
  `tests/test_dependency_cycle_gate.py`,
  `tests/test_owner_governance_chain_parity.py`, and
  `tests/test_stop_hook_owner_governance.py` all pass.
- `node --check` on the generated `app.js` exits 0.
- `owner_governance_gate.py` runs the new gate at `findings=0`.

## Decision

Promote subtask/dependency relationships from prose to an executable model +
gate + consistent visualization. The cycle gate is advisory-but-blocking only
when a real cycle exists, and inert otherwise, so it adds safety without
regressing any clean-repo flow.
