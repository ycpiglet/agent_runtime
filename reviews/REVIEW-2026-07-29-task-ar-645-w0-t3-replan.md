---
title: TASK-AR-645 W0 T3 Replan
date: 2026-07-29
signal: pass
score: 96
priority: P0
tags: [task-ar-645, w0, t3-replan, compound, scribe, knowledge, host-adapters]
---

# TASK-AR-645 W0 T3 Replan

## Bottom Line

Proceed with the two registered units in sequence. The registered problem is
still present, but the original targets and tests are too narrow:

1. `UNIT-TASK-AR-645-001` will create task-linked, per-record compound storage,
   deterministic defect signatures, claim-time lookup, linked closeout
   validation, and safe ownership defaults.
2. `UNIT-TASK-AR-645-002` will consume host-configured state adapters, generate
   a bounded scribe projection, surface it at doctor/session start, and enforce
   freshness only for substantial closeout.

The baseline is Agent Runtime `main` at `d41da008`. Consumer repositories remain
read-only research inputs until their separately registered pilot tasks.

## T2 Drift

`plan_assumption_gate` found 24 changed or newly present anchors. They are
expected consequences of completed TASK-AR-644: portable hook commands,
packaged lifecycle scripts, doctor changes, compact/restart tests, and the
closed TASK-AR-644 records. Dispatch must still stop because the recorded T0
snapshot points to the prior task's design and implementation surfaces.

This review is the T3 replacement. It narrows the next dispatch to
`UNIT-TASK-AR-645-001` and re-anchors the taskset only after the updated task
and both unit records are committed.

## Failure-First Evidence

The expanded current baseline passes:

```text
python -m pytest tests/test_compound_cadence_gate.py \
  tests/test_compound_cadence_obligation.py \
  tests/test_closure_gate.py \
  tests/test_doc_steward_due.py \
  tests/test_config_v2.py \
  tests/test_doctor.py -q
95 passed
```

That green result does not cover the required behavior:

| Surface | Current behavior | Defect |
| --- | --- | --- |
| Closure | any same-day compound, review, or retro approves substantial work | an unrelated record can satisfy the current task |
| Cadence | counts `reviews/COMPOUND-*` filenames globally | no task/signature obligation or per-record store |
| Claim dispatch | validates taskset assumptions and footprint only | no prior-error lookup before claim persistence |
| KEDB | template-only parser reads one `compound_log.md` | shared-file growth and write conflicts remain |
| Work close | execution evidence is JSON-only | Markdown review records must be manually separated and are not link-validated |
| Ownership | legacy `compound_log.md` defaults to managed | live host learning can conflict with template updates |
| Scribe | counts bullets below exactly `## 현재 한 줄 요약` | language/path/shape coupling produces false `ok` |
| Config | stores scalar `host.state_adapters` | no runtime consumer or generated projection exists |

The live false negative is direct:

```text
python scripts/scribe_due.py --quiet
[scribe_due] ok — 핫 항목 0개 (<= 12), 압축 불요
```

Agent Runtime's root `STATUS.md` is 1,688 lines. The script returns zero only
because that file does not use the one hard-coded Korean heading.

## Autofolio Precedent

Autofolio validates the framework/overlay/seam model:

- reusable Agent Runtime assets remain upstream-managed;
- product identity and operating records remain host-owned;
- only explicit seams are unmanaged and reconciled during updates;
- W0~W6, claim-first worktrees, independent W4b, and generated indexes are
  already real operating contracts.

It also demonstrates why TASK-AR-645 is necessary:

- `agents/lead_engineer/STATUS.md` is 1,460 lines;
- `agents/lead_engineer/compound_log.md` is 5,235 lines;
- the compound log is a permanent unmanaged data seam;
- its scribe checker still depends on the exact Korean heading.

The lesson is not to copy Autofolio's monolith into every host. Preserve its
successful framework/overlay boundary and replace the data seam with
task-linked records plus generated projections.

## Consumer Adapter Facts

The pilot inputs are intentionally different:

| Host | Canonical input observed at W0 | Shape |
| --- | --- | --- |
| Agent Runtime | `STATUS.md` | newest-first dated Markdown sections |
| Autofolio | `agents/lead_engineer/STATUS.md` | long host-owned Markdown status |
| Bean Wiki | `BACKLOG.md` | sprint headings plus emoji/checklist bullets |
| Allimbot | `docs/PROJECT_STATUS.ko.md` | conclusion/status headings plus bullets |

The registered phrase “Allimbot PROJECT_STATUS” was incomplete. The exact
current path includes both `docs/` and `.ko.md`. Core must not hard-code any of
these product names or Korean headings.

## Per-Record Compound Contract

The canonical new store is:

```text
agents/project/knowledge/compounds/
  records/COMPOUND-<timestamp>-<slug>-<digest>.json
  INDEX.json
```

Each `agent-runtime-compound-record/v1` JSON record contains:

- a collision-resistant record ID and creation time;
- one or more linked work IDs;
- one or more normalized defect signatures;
- recurrence count and status;
- bounded title, summary, cause, and prevention;
- source, prevention, and verification references.

Signature normalization is deterministic and bounded. The same explicit
signature input must resolve to the same canonical value; malformed, empty,
absolute-path, secret-like, or oversized inputs fail closed.

Creation writes one new record atomically and never appends to a shared record.
`INDEX.json` is a deterministic generated projection rebuilt from validated
records. Concurrent workers may create separate records; the serial
orchestrator regenerates the index.

The legacy `agents/lead_engineer/compound_log.md` remains a read-only search
fallback for existing hosts. This task does not bulk-migrate or rewrite it.

## Work Linkage and Retrieval

Register optional work-item fields:

- `defect_signatures`
- `compound_refs`
- `review_refs`

Claim creation reads the selected unit and task signatures, searches the
validated compound store before writing the claim, emits bounded matches, and
records match references on the claim. Search failure is visible and
fail-closed for malformed canonical records; the absence of a match is valid.

The readiness gate's `new:` target marker is planning syntax, not a repository
path. Claim dispatch must strip that prefix before footprint conflict and
post-verification checks. Until unit 001 implements the normalization, its W2
claim command must pass the real target paths explicitly.

The compatibility `kedb_search.py` gains work-ID/signature queries and a
legacy fallback. Operators may also run `compound_record.py search` after a
failure without persisting raw command output or transcripts.

## Closeout Contract

Execution verification and learning/review evidence remain distinct:

- `evidence_refs` must continue to point to passed verification JSON;
- `review_refs` point to linked review Markdown;
- `compound_refs` point to validated compound JSON.

`work close` and the substantial-work closure gate validate that referenced
review/compound records link to the current work ID or a defect signature
declared by that work. An unrelated same-day filename is never enough.

When a prior record matches a current defect signature, substantial closeout
requires a current linked compound record showing whether prevention was
reused, strengthened, or found insufficient. This turns repeat learning into
an executable obligation without forcing compound creation for every mini
task.

## Ownership Contract

Default effective ownership is:

| Path | Ownership | Reason |
| --- | --- | --- |
| `agents/lead_engineer/compound_log.md` | `seed_once` | legacy placeholder becomes host data after first install |
| `agents/project/knowledge/compounds/records/**` | `host_owned` | canonical live learning records |
| `agents/project/knowledge/compounds/INDEX.json` | `generated` | deterministic producer-owned projection |
| `agents/project/state/SCRIBE-PROJECTION.json` | `generated` | bounded derived state |
| configured state-adapter sources | host-owned or outside the template | runtime must never overwrite them |

Adoption, sync, and lock tests must prove these modes. Existing hosts retain
their monolithic data without a conflict or overwrite.

## Scribe Adapter and Projection Contract

Config v2 keeps the existing scalar `host.state_adapters` mapping:

```yaml
host:
  state_adapters:
    status: STATUS.md
    backlog: BACKLOG.md
    project_status: docs/PROJECT_STATUS.ko.md
  state_projection: agents/project/state/SCRIBE-PROJECTION.json
```

Adapter labels are descriptive only. Parser selection comes from a bounded
supported shape:

- Markdown headings, bullets, and checklists;
- JSON lists or documented list-valued object fields.

When no v2 config is present, a bounded conventional candidate set preserves
compatibility. Missing configured sources are explicit warnings, never a
fabricated zero-entry `ok`.

The `agent-runtime-scribe-projection/v1` output contains only source-relative
paths, content digests, counts, selected headings/items, timestamps, and
findings. It is capped by source count, item count, item length, and total
serialized size. It never stores prompt text, transcripts, arbitrary source
body, environment values, or secrets.

A source over the hot threshold requires a fresh projection. A matching source
digest proves freshness, so a large canonical host file may remain untouched
while agents consume the bounded projection. Doctor and `SessionStart` only
read/report it.

## Enforcement Boundary

- Mini work below the existing substantial-line threshold remains lightweight.
- Missing optional state remains a visible advisory.
- Substantial closeout blocks only when configured/present state is overdue
  and its projection is missing or stale.
- Projection generation is an explicit scribe/orchestrator action, never an
  implicit doctor or session-start write.

## Scope Amendment

The original two units remain valid, with necessary shared surfaces added:

- package modules for compound records and state projection;
- root/template compound, closure, claim, work, scribe, and session-start
  scripts;
- work-schema fields and ownership resolution;
- config/doctor documentation and runtime asset registries;
- focused claim, closeout, adoption/sync/lock, clean-host, sanitizer, and
  packaging tests.

This is not authorization for Bean Wiki, Allimbot, Autofolio, Tag Manual, or
any other consumer mutation; historical compound migration; product-specific
status logic; prompt/transcript persistence; per-user settings changes;
TASK-AR-646 or later; version bump; tag; publish; release; or deployment.

## Verification

- focused compound create/check/index/search and concurrent-record tests;
- claim refusal/surface tests before persistence;
- linked versus unrelated review/compound closeout fixtures;
- legacy-monolith read-only fallback;
- Agent Runtime, Autofolio, Bean Wiki, and Allimbot-shaped synthetic adapter
  fixtures;
- projection freshness, missing/stale, bounded-size, and sensitive-content
  exclusion tests;
- mini versus substantial closure behavior;
- adoption/sync/lock ownership and built-wheel template execution;
- `python scripts/runtime_asset_usage.py --check`;
- `python scripts/verify_wheel_dotfiles.py --check`;
- `python -m agent_runtime.cli sanitize --root . --check`;
- full `python -m pytest -q`;
- independent W4b against each exact implementation head.

## W2 Decision

After this review, the updated task/unit records, evidence index, and refreshed
T3 assumption snapshot merge, dispatch only `UNIT-TASK-AR-645-001` to a
`worker_standard` claim. Unit 002 starts from a new W0/T2 check after unit 001
is independently verified and integrated. W4b must use a different agent
instance and adversarially test unrelated evidence, malformed records,
concurrent creation, legacy fallback, ownership modes, and pre-persistence
claim lookup.
