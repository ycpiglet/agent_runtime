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

