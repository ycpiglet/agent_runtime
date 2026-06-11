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
| `prevention_status` | note_only, proposal, fixture, gate, verified, or accepted_watch. |
| `recurrence_count` | Number of observed recurrences, with source refs. |
| `linked_regression_fixture` | Fixture path or explicit `none:<reason>`. |
| `affected_gate` | Gate, hook, wrapper, or manual flow affected by the case. |
| `task_proposal` | Existing task/proposal route or explicit `accepted_watch`. |

## Lookup Rules

- A repeated failure must be searchable by `symptom`, `trigger`, `owner_boundary`, and `affected_gate`.
- A case with `recurrence_count > 1` cannot stay `note_only` unless it has an explicit `accepted_watch` decision.
- A deterministic reproduction must route to a regression fixture, executable gate, or task proposal.
- Owner-only, external, destructive, release/version, prod-data, and cost-bearing boundaries remain proposal-only until Owner approval exists.

