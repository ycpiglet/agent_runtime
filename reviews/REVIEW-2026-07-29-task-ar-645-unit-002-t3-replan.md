---
title: TASK-AR-645 UNIT-002 W0 T3 Replan
date: 2026-07-29
signal: pass
score: 97
priority: P0
tags: [task-ar-645, unit-002, w0, t3-replan, scribe, state-adapters, projection]
---

# TASK-AR-645 UNIT-002 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-645-002` from Agent Runtime `main`
`8cff865b42fd5c677c476cecb82cd96c6b583ca9`.

Unit 001 is independently verified, integrated, and closed. Its changes are
the complete cause of the T2 drift and do not invalidate Unit 002. Unit 002
must consume the new task-linked closure behavior instead of restoring the
former same-day evidence heuristic.

No consumer repository may be changed in this unit. Bean Wiki, Allimbot, and
Autofolio remain read-only shape inputs represented by synthetic test
fixtures.

## W0 and T2 Evidence

`python scripts/work.py status` reports zero active claims and zero divergent
in-flight task branches. The merged Unit 001 worktree and branch are gone.

The fresh T2 check correctly failed closed with 32 changed or newly present
anchors. Every finding is an expected Unit 001 result: compound storage,
claim-time lookup, linked closeout, ownership defaults, their tests, and the
closed Unit 001 records. There is no unrelated upstream or consumer drift.

The live Unit 002 failure remains:

```text
python scripts/scribe_due.py --quiet
[scribe_due] ok — 핫 항목 0개 (<= 12), 압축 불요
```

That result is false. Root `STATUS.md` has 1,688 lines, 217 Markdown headings,
and 751 list items, but the current implementation only counts bullets below
one exact Korean heading.

The registered verification command also fails before implementation because
`tests/test_scribe_due.py` is intentionally a new target:

```text
ERROR: file or directory not found: tests/test_scribe_due.py
```

The existing neighboring suite remains green:

```text
python -m pytest tests/test_config_v2.py tests/test_doctor.py \
  tests/test_session_continuity_hooks.py tests/test_closure_gate.py \
  tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
# 209 passed
```

## Read-Only Host Shapes

The current inputs still differ as planned:

| Shape | Lines | Headings | List items | Canonical input |
| --- | ---: | ---: | ---: | --- |
| Agent Runtime | 1,688 | 217 | 751 | `STATUS.md` |
| Bean Wiki | 123 | 14 | 74 | `BACKLOG.md` |
| Allimbot | 112 | 10 | 42 | `docs/PROJECT_STATUS.ko.md` |
| Autofolio | 1,460 | 5 | 272 | `agents/lead_engineer/STATUS.md` |

Core behavior must therefore depend on configured paths and structural
Markdown/JSON parsing, not repository names, Korean labels, or one document
layout.

## State Adapter Contract

Configuration v2 continues to accept scalar adapter entries:

```yaml
host:
  state_adapters:
    status: STATUS.md
    backlog: BACKLOG.md
  state_projection: agents/project/state/SCRIBE-PROJECTION.json
```

- Adapter labels are descriptive identifiers, not parser or product switches.
- Paths use the existing safe relative-path normalization.
- The canonical projection default is
  `agents/project/state/SCRIBE-PROJECTION.json`.
- A custom projection path must be safe, distinct from every source, and
  explicitly declared with `ownership.generated`.
- If adapters are configured, every configured source is evaluated. A missing
  configured source is a structured warning with an unknown count, never
  `ok` with count zero.
- Without configured adapters, compatibility chooses the first existing path
  from a bounded conventional set:
  `agents/lead_engineer/STATUS.md`, `STATUS.md`, `BACKLOG.md`,
  `docs/PROJECT_STATUS.md`, `docs/PROJECT_STATUS.ko.md`, and
  `PROJECT_STATUS.md`.
- No conventional source found is an explicit `unavailable` advisory.

## Generic Parsing and Selection

The package module `agent_runtime.state_projection` owns parsing, evaluation,
freshness, redaction, and atomic projection writes. The root and template
`scribe_due.py` files are equivalent CLI adapters over that package API.

Markdown parsing derives only:

- ATX headings and their level;
- unordered bullets;
- checked and unchecked task-list markers;
- the nearest bounded heading associated with an item.

Unchecked task-list items and ordinary bullets are hot; checked task-list
items are cold. If a source has no list items, bounded headings are the
fallback items. Selection is deterministic and source ordered, prioritizing
unchecked task-list items before ordinary bullets, with at most ten selected
items per projection.

JSON support is deliberately bounded to a top-level list or list-valued
`items`, `entries`, `tasks`, `work`, or `backlog` field. String entries are
accepted directly. Object entries may derive only `id`, `name`, `title`,
`summary`, and `status`; arbitrary keys or nested bodies are not copied.

## Projection and Privacy Contract

`agent-runtime-scribe-projection/v1` stores only:

- generated timestamp and projection path;
- adapter label and safe relative source path;
- SHA-256 source digest;
- total, hot, and selected counts;
- bounded selected headings/items and checklist state;
- structured finding codes.

Hard limits are eight sources, ten selected items per projection, 160
characters per heading, 240 characters per item, and 32 KiB serialized
output. Secret-like keys and values, credential-shaped tokens, environment
assignments, private-key markers, prompts, transcripts, and arbitrary source
bodies are omitted or replaced with `[REDACTED]`.

`--now` makes test output deterministic. Projection generation writes a
same-directory temporary file and uses atomic replacement. No operation edits
a configured source.

## CLI and Read-Only Consumers

The CLI contract is:

```text
python scripts/scribe_due.py --root . --json
python scripts/scribe_due.py --root . --write-projection --now <ISO-8601> --json
```

The default invocation is read-only. `--write-projection` is the only write
path and may write only the resolved projection file.

Doctor and SessionStart call the same evaluation API in read-only mode. They
report missing, due, overdue, stale, and fresh states without regenerating a
projection or touching source mtimes.

## Freshness and Closure Enforcement

The existing thresholds remain:

- `ok`: at most 12 hot items;
- `due`: 13 to 15 hot items;
- `overdue`: at least 16 hot items.

A projection is fresh only when every projected present source path and digest
matches the current configured/fallback source set. A fresh projection
satisfies bounded-context readiness even while a canonical source remains
large.

Missing optional/fallback sources and `due` state remain advisory. Substantial
closure blocks when any present source is overdue and its projection is
missing or stale. Work below the existing substantial-line threshold remains
advisory. This scribe obligation is additive to Unit 001's linked
review/compound gate; it must not weaken verification JSON or work linkage.

## Scope Amendment

Keep the registered implementation surfaces and add explicit synthetic
fixtures for Agent Runtime, Bean Wiki, Allimbot, Autofolio, and generic JSON.
The fixtures contain structure only and are not copied from live consumer
records.

This unit does not authorize:

- edits to any consumer repository or canonical host status/backlog;
- product-specific parser branches;
- prompt, transcript, environment, or secret persistence;
- implicit writes from doctor, SessionStart, or closure checks;
- Unit 001 rewrites, historical compound migration, TASK-AR-646 or later;
- version bump, tag, publish, release, deployment, or per-user setting change.

## W2 Decision

After this review, the amended Unit 002 record, evidence index, and refreshed
T3 snapshot merge to main, dispatch exactly `UNIT-TASK-AR-645-002` as
`worker_standard`. Claim creation must use normalized target paths and create
one isolated worktree. W4b must be a different agent instance and must test
malformed paths, sensitive-content redaction, digest staleness, atomic writes,
read-only doctor/session start, mini exemption, substantial blocking, and all
five synthetic source shapes.
