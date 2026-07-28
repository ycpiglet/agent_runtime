---
title: TASK-AR-640 W0 T3 Replan
date: 2026-07-28
signal: pass
score: 97
priority: P0
tags: [task-ar-640, w0, t3-replan, config-v2, autofolio]
---

# TASK-AR-640 W0 T3 Replan

## Bottom Line

Continue with `UNIT-TASK-AR-640-001` after replacing the stale taskset
assumption set. The five drifting anchors are expected outputs of the completed
TASK-AR-639 lifecycle-reconciliation work, not a changed Owner objective.

This unit establishes a backward-compatible, typed configuration contract and
machine-readable doctor projection. It does not change sync/lock ownership
behavior, install profile manifests, execute adapters, or mutate a host.

## T3 Revalidation

| Check | Result | Decision |
| --- | --- | --- |
| `UNIT-TASK-AR-639-002.md` | expected drift | UNIT-002 closed and TASK-AR-639 is complete |
| `agents/project/WORK-SCHEMA.yml` | expected drift | TASK-AR-639 registered lifecycle recovery fields |
| `scripts/state_sync_gate.py` | expected drift | lifecycle tuple reconciliation shipped |
| `scripts/task_claim_dispatcher.py` | expected drift | claim bootstrap and release truth shipped |
| `scripts/work_schema_gate.py` | expected drift | new fields are now schema-consumed |
| Owner objective | unchanged | one reusable runtime with composable host overlays, not per-project forks |
| Autofolio evidence | current | v0.6 uses the correct framework/overlay/seam model but carries 21 unmanaged entries |
| Current parser | insufficient | only project/upstream/sync/unmanaged are represented |
| Current host context | convention only | fixed path is documented but runtime does not consume it |
| Current doctor | insufficient | human-only config summary; no effective configuration JSON |

## Configuration Contract

### Source schemas

- A config without `schema` is source schema
  `agent-runtime-config/v1`. Its current required fields and behavior remain
  unchanged.
- A v2 config declares `schema: agent-runtime-config/v2`. Any other explicit
  schema is a blocker.
- Both schemas normalize into one immutable `AgentRuntimeConfig`. The
  projection records `source_schema` and `effective_schema`.
- v1 `sync.unmanaged` remains accepted and maps to effective `host_owned`
  ownership while `unmanaged_paths` stays available to existing sync/lock
  consumers. A v1 host is projected as `full-runtime`; that is descriptive and
  must not alter its existing full-template behavior.

### Profiles and capabilities

The registered profile order is `core`, `web-content`, `security-service`.

- v2 defaults to `profiles: [core]`.
- `core` is always present in effective profiles.
- `web-content` and `security-service` are additive.
- `full-runtime` is an exclusive alias that expands to all three profiles.
  Combining the alias with another profile is invalid.
- Repeated entries are deduplicated and the effective projection uses registry
  order, never source or set iteration order.
- Unknown profile or capability identifiers block.

The initial capability registry is deliberately semantic rather than a file
manifest:

| Profile | Effective capabilities |
| --- | --- |
| `core` | `lifecycle`, `continuity`, `verification`, `compound`, `scribe`, `model-routing` |
| `web-content` | core plus `web-content` |
| `security-service` | core plus `security-service` |
| `full-runtime` | union of all registered profiles |

An optional top-level `capabilities` list can add registered capability IDs.
TASK-AR-642/643 will bind effective capabilities to owned file manifests and
enforce dependency closure. Selection here does not claim that a later profile
implementation has shipped.

### Ownership

V2 accepts lists under:

```yaml
ownership:
  managed:
    - scripts/example.py
  seed_once:
    - agents/project/NEXT-SESSION-POINTER.yml
  host_owned:
    - AGENTS.md
  generated:
    - BACKLOG-BOARD.md
```

Paths are normalized repo-relative POSIX paths. Empty paths, absolute paths,
backslashes, `.`/`..` traversal, `.git/**`, `agent_runtime.yml`, and
`agent_runtime.lock.json` are invalid. Exact duplicates in one mode are
deduplicated. A path classified in different modes, including a mixed-mode
ancestor/descendant overlap, is a blocker. `agents/host/**` may only be
`host_owned`.

This unit reports the effective ownership table. TASK-AR-642 owns matching,
reconcile, safe apply, seed transition, generated-producer behavior, and
lock/sync semantics.

### Host context and adapters

The canonical optional context path is
`agents/host/HOST-CONTEXT.yml`. If `host.context` is present, it must name that
exact path. Missing context is informational, not an error; an invalid present
file blocks.

The runtime consumes and projects the current `host-context/v1` keys:
`purpose`, `domain`, `safety_constraints`, `role_mapping`, and `read_more`.
Host-relative paths receive the same path-safety validation.

V2 can also declare:

```yaml
host:
  context: agents/host/HOST-CONTEXT.yml
  role_overlay: agents/host/ROLE-OVERLAY.yml
  risk_paths:
    - app/production/
  state_adapters:
    status: STATUS.md
    backlog: BACKLOG.md
```

`role_overlay`, `risk_paths`, and `state_adapters` are typed, normalized, and
visible in the effective projection. This unit does not execute or enforce
them; TASK-AR-645 owns scribe adapter execution and TASK-AR-647 owns
security/external-effect enforcement.

### Doctor JSON

`agent_runtime doctor --json` emits a deterministic object with:

- `schema: agent-runtime-doctor/v1`
- `root`
- `config` containing source/effective schema, source path, project, upstream,
  sync compatibility fields, effective profiles/capabilities/ownership, and
  host context/overlay/risk/state-adapter data
- sorted `findings`
- `summary` counts

Invalid configuration must still emit valid JSON with the available schema
and path plus the blocker finding. Human doctor output and `--check` exit
semantics remain compatible. `--repair --json` includes repair actions in the
same JSON document rather than printing a second non-JSON stream.

## Scope Amendments

Add these files to the unit target:

- `src/agent_runtime/cli.py` for the public `doctor --json` flag
- `tests/test_config_v2.py` for focused parser/normalization/validation tests

Keep these boundaries:

- no new YAML dependency; implement only the documented bounded shapes,
  including quoted scalars, scalar lists/mappings, comments, and the documented
  folded host-context scalars
- no sync, lock, install, profile-manifest, or host mutation changes
- no product-specific default path
- no migration of Bean Wiki, Allimbot, or Autofolio in this unit

## Verification

- `python -m pytest tests/test_config_v2.py tests/test_doctor.py tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py -q`
- `python -m pytest tests/test_project_context_overlay.py -q`
- focused v1 sync/lock regression proving `unmanaged_paths` is byte-compatible
- independent W4b by a different worker instance

## Decision

Record new taskset assumptions against this review and the TASK-AR-640
implementation surfaces, then dispatch UNIT-001 without
`--skip-plan-check`.
