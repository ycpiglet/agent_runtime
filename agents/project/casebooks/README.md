# Casebooks

## Purpose

Casebooks are searchable collections of failures, compound issues, repeated
review findings, and regression patterns. They turn scattered notes into
fixtures, gates, or task proposals.

## Catalogs

| Catalog | Purpose |
| --- | --- |
| `failure-and-compound-casebook.md` | Owner-visible registry for repeated failures, compound entries, and prevention status. |

## Case Fields

| Field | Meaning |
| --- | --- |
| `case_id` | Stable case identifier. |
| `dedupe_key` | Recurrence key used by evidence inbox and proposal engine. |
| `symptom` | Observable problem. |
| `trigger` | User action, command, gate, or workflow that exposed it. |
| `source_refs` | Compound, review, retro, eval, or conversation records. |
| `reproduction` | Command or reason a deterministic reproduction is unavailable. |
| `owner_boundary` | Local, Owner-only, external, destructive, release, version, prod-data, or cost-bearing. |
| `affected_gate` | Gate, test, hook, or workflow that should catch recurrence. |
| `recurrence_count` | Number of known occurrences or `unknown` when historical count is incomplete. |
| `linked_regression_fixture` | Fixture, test, or explicit `none` / `not_yet`. |
| `prevention_status` | note_only, proposal, fixture, gate, verified, or accepted_watch. |
| `needs_enforcement` | yes/no flag; yes must route to a task proposal or accepted_watch state. |

## Routing Rules

- `needs_enforcement: yes` cannot remain a note without a linked task proposal
  or an explicit `accepted_watch` decision.
- Casebooks index `agents/lead_engineer/compound_log.md` as a historical source,
  not as the final query surface.
- Owner-only, release, version, external, destructive, prod-data, and
  cost-bearing cases remain proposal-only until the Owner decision is explicit.

