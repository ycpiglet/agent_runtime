---
title: TASK-AR-609 Skeptic and Adversarial W4b
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-609
verified_head: b0bbce9d8e544bb7a07ed39c23d16d1fa1f57308
implementation_sha: 5421f9b2987d8ae3b85aa042f6fbc9618bdb57bc
failure_first_sha: efbe574d635c91314901f6722a03de20edc356ba
original_rejected_head: 41f6b4d62547b360d432ded336d29e5ef1ced096
original_rejected_implementation_sha: 806a9db1605fa1009fd45c6c4ce797de6005dcde
original_failure_first_sha: 2ab14c8c2308887f3781b59b9cf876acb080feab
verified_by: codex-task-ar-609-skeptic-20260723
worker: codex-root-task-ar-609
role: skeptic
verdict: APPROVE
tags: [task-ar-609, skeptic, adversarial, classifier, initiative, normalization, identity]
---

# TASK-AR-609 Skeptic and Adversarial W4b

## Verdict

**REJECT** at exact W4a HEAD
`41f6b4d62547b360d432ded336d29e5ef1ced096`, implementation commit
`806a9db1605fa1009fd45c6c4ce797de6005dcde`.

The normal mixed-directory regression is fixed, the registered suite and
gates pass, and root/template behavior is identical. Approval is blocked
because whitespace-only canonical fields are selected before normalization.
They prevent the required `kind -> type` and `id -> work_id -> path stem`
fallbacks and can re-admit a taskset as a legacy initiative.

## Findings

### [P1] Whitespace-only `kind` suppresses `type` and can reintroduce duplication

The implementation computes:

```python
kind = str(meta.get("kind") or meta.get("type") or "").strip().lower()
```

The `or` choice happens before normalization. A quoted whitespace-only
frontmatter value is truthy when selected, then becomes empty only after
`.strip()`. The compatibility `type` is therefore never examined, and the
empty result enters the no-kind legacy path.

Both root and template parsers reproduced this counterexample:

```yaml
kind: "   "
type: taskset
id: INIT-TYPE-TASKSET
```

```text
expected: rejected from the initiative collection because normalized type is taskset
actual:   accepted as legacy initiative INIT-TYPE-TASKSET
```

This is the exact unsafe direction for GitHub issue 300: a taskset-shaped
record can again populate the initiative level when an empty canonical field
coexists with a non-empty compatibility type and an `INIT-` identity.

The inverse boundary also fails:

```yaml
kind: "   "
type: initiative
id: CUSTOM-TYPE-INIT
```

The normalized `type: initiative` should admit the record, but both copies
drop it because the empty selected kind is not `initiative` and the ID does
not qualify for legacy prefix inference.

Required rework: normalize the canonical kind candidate first, then fall back
to a separately normalized type only when the canonical candidate is empty.
Apply legacy `INIT-` inference only when both normalized candidates are empty.
Retain the existing rule that any non-empty canonical kind wins over a
conflicting type.

### [P1] Whitespace-only identity candidates suppress deterministic fallback

Identity uses the same select-before-normalize pattern:

```python
initiative_id = str(meta.get("id") or meta.get("work_id") or path.stem).strip()
```

Two direct fixture cases fail in both parser copies:

```yaml
kind: initiative
id: "   "
work_id: INIT-WORK-SPACE-ID
```

Expected `INIT-WORK-SPACE-ID`; actual result is no initiative record.

```yaml
kind: initiative
work_id: "   "
# filename: INIT-STEM-SPACE-WORK.md
```

Expected `INIT-STEM-SPACE-WORK`; actual result is no initiative record. The
later `if not initiative_id` guard only drops the selected empty result and
cannot recover the skipped fallback candidate.

Required rework: normalize `id`, `work_id`, and `path.stem` independently,
then select the first non-empty normalized value. Add empty-string and quoted
whitespace-only cases for every fallback edge in root and template tests.

## Adversarial Reproduction Matrix

The independent fixture passed each record through the real frontmatter parser
and `_initiative_records()` in both root and template modules.

| Boundary | Root | Template | Assessment |
| --- | --- | --- | --- |
| `kind=taskset`, conflicting `type=initiative` | pass | pass | canonical kind wins |
| `kind=initiative`, conflicting `type=taskset` | pass | pass | canonical kind wins |
| mixed-case kind with surrounding whitespace | pass | pass | normalized |
| absent kind, mixed-case type with surrounding whitespace | pass | pass | alias works |
| whitespace-only kind -> `type=initiative` | **fail** | **fail** | alias suppressed |
| whitespace-only kind -> `type=taskset`, `INIT-*` ID | **fail** | **fail** | unsafe legacy admission |
| non-empty `id` over `work_id` | pass | pass | ID wins |
| empty-string `id` -> `work_id` | pass | pass | fallback works |
| whitespace-only `id` -> `work_id` | **fail** | **fail** | record dropped |
| empty-string `work_id` -> filename stem | pass | pass | fallback works |
| whitespace-only `work_id` -> filename stem | **fail** | **fail** | record dropped |
| absent kind/type with `INIT-*` stem | pass | pass | legacy admitted |
| absent kind/type with non-`INIT-*` stem | pass | pass | legacy rejected |
| explicit/type-only taskset with `INIT-*` ID | pass | pass | rejected |

Across 15 cases, 11 pass and 4 fail in each implementation copy. The failures
are identical because parity is exact; parity does not make the behavior
correct.

## Passing Stability and Duplicate Boundaries

Legitimate initiatives retain their fields and ordering. A separate full
`collect()` fixture produced the same exact rows in root and template:

| ID | Title | Status | Number |
| --- | --- | --- | --- |
| `INIT-FIRST` | First Initiative | active | 1 |
| `INIT-SECOND` | Second Initiative | planned | 2 |
| `INIT-THIRD` | Third Initiative | complete | 3 |

The ordinary mixed-record case is repaired. AST-extracted
`_initiative_records()` from failure-first `2ab14c8c` admitted a
`kind: taskset` / `type: initiative` record as `TASKSET-DUP`; the implemented
function rejects it. The registered full-collection tests also prove the
normal taskset ID appears exactly once at the taskset level rather than being
duplicated as an initiative.

Root and template `_initiative_records()` have identical normalized AST with
SHA-256:

```text
a0d17a5fbe16d2daacc1d1628292bca7302ca91cddbb2652e13a3d68e3e90079
```

## Generated View and Scope Audit

The production generated JSON at `2ab14c8c` and `806a9db1` has identical key
sets: 438 records, no additions, no removals, and no changed initiative row.
Only the already-claimed TASK-AR-609 task and unit lifecycle statuses changed:

```text
task:TASK-AR-609                 planned -> in_progress
unit:UNIT-TASK-AR-609-001       worker_ready -> in_progress
```

Thus the generated classifier view has no initiative identity, title, parent,
path, order, or numbering churn caused by the filter. The timestamp-only
header changes are expected generation metadata.

The complete failure-first plus implementation delta changes exactly seven
files: the root/template classifier copies, their two focused test files, the
generated host lock, and the JSON/Markdown generated classification views.
There are no file additions, deletions, renames, storage-directory moves,
record relocations, dependency changes, or task/taskset numbering-policy
changes. Regenerating the two views is explicitly included by the T3 scope.

## Commands and W4a Evidence

```text
python -m pytest tests/test_work_item_classifier.py \
  tests/test_template_work_item_classifier.py -q
7 passed in 2.82s

python scripts/work_item_classifier.py --check
work-item-classifier: pass
findings=0

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --check 2ab14c8c..806a9db1
pass
```

The independent adversarial command used OS temporary directories, imported
both current classifier modules, passed each fixture through the real
frontmatter reader, AST-extracted the failure-first function, compared
legitimate ordering, and performed a semantic generated-view diff. It did not
write repository files.

Both W4a records parse correctly, identify worker
`codex-root-task-ar-609`, and contain the same three passing commands with zero
return codes and empty stderr:

- `reviews/VERIFY-2026-07-23-task-ar-609-20260723072306.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723072326.json`

## Measurable Validation

| Metric | Threshold | Measured value | Status |
| --- | --- | --- | --- |
| canonical kind conflict precedence | 2/2 pass per copy | 2/2 root, 2/2 template | pass |
| kind/type normalization and fallback | all pass | 2 failures per copy | **fail** |
| identity fallback order including empty values | all pass | 2 failures per copy | **fail** |
| no-kind legacy boundary | INIT admitted, non-INIT rejected | 2/2 per copy | pass |
| ordinary taskset duplicate removal | no initiative duplicate | removed | pass |
| legitimate initiative stability | exact title/status/order/number | 3/3 per copy | pass |
| root/template AST parity | identical | identical | pass |
| production generated semantic stability | no initiative churn | 0 initiative rows changed | pass |
| registered suite | all tests pass | 7/7 | pass |
| classifier check | zero findings | 0 | pass |
| generated host lock | no drift | current | pass |
| scope | no moves or numbering-policy changes | none | pass |

## Review Mutation Boundary

This skeptic review created only
`reviews/ROLE-REVIEW-2026-07-23-TASK-AR-609-SKEPTIC.md`. It did not modify
implementation files, tests, generated classification views, W4a evidence,
task/runtime metadata, or `reviews/INDEX.md`.

## Remediation Re-review

This section records the independent re-review of remediation implementation
`5421f9b2987d8ae3b85aa042f6fbc9618bdb57bc` at latest W4a HEAD
`b0bbce9d8e544bb7a07ed39c23d16d1fa1f57308`. The original REJECT narrative,
counterexamples, measurements, and exact SHAs above remain unchanged as audit
history. The frontmatter now identifies the final reviewed state and retains
the original rejected identities explicitly.

### Findings

No blocking finding was reproduced at the remediation SHA.

The implementation now normalizes each fallback candidate before deciding
whether to continue:

```python
initiative_id = str(meta.get("id") or "").strip()
if not initiative_id:
    initiative_id = str(meta.get("work_id") or "").strip()
if not initiative_id:
    initiative_id = path.stem.strip()

kind = str(meta.get("kind") or "").strip().lower()
if not kind:
    kind = str(meta.get("type") or "").strip().lower()
```

This directly closes both select-before-normalize blockers. A non-empty
canonical kind still wins over a conflicting type; only an empty normalized
kind reaches the compatibility alias. Legacy `INIT-` inference occurs only
after both normalized kind candidates are empty. Identity likewise selects the
first non-empty normalized value in the required `id -> work_id -> filename`
order.

### Counterexample Closure and Adversarial Matrix

The original minimum blockers now behave correctly in both root and template:

```yaml
kind: "   "
type: taskset
id: INIT-TYPE-TASKSET
```

Result: rejected from the initiative collection rather than admitted through
legacy inference.

```yaml
kind: initiative
id: "   "
work_id: INIT-WORK-SPACE-ID
```

Result: classified as `INIT-WORK-SPACE-ID`; the empty ID no longer suppresses
the work-ID fallback.

The full real-frontmatter fixture passed all 15 cases in each copy:

| Boundary family | Root | Template |
| --- | ---: | ---: |
| canonical `kind` wins over conflicting `type` | 2/2 | 2/2 |
| kind/type case and surrounding-whitespace normalization | 2/2 | 2/2 |
| whitespace-only kind falls through to initiative/taskset type | 2/2 | 2/2 |
| non-empty ID precedence and empty/whitespace ID fallback | 3/3 | 3/3 |
| empty/whitespace work ID falls through to filename | 2/2 | 2/2 |
| no-kind INIT legacy and non-INIT rejection | 2/2 | 2/2 |
| explicit/type-only taskset rejection | 2/2 | 2/2 |
| **Total** | **15/15** | **15/15** |

A separate full `collect()` fixture retained the exact legitimate initiative
title, status, ordering, and number sequence in both modules:

| ID | Title | Status | Number |
| --- | --- | --- | --- |
| `INIT-FIRST` | First Initiative | active | 1 |
| `INIT-SECOND` | Second Initiative | planned | 2 |
| `INIT-THIRD` | Third Initiative | complete | 3 |

### Failure-First Provenance

The new failure-first commit
`efbe574d635c91314901f6722a03de20edc356ba` changes only the two focused test
files. AST-extracting its pre-fix `_initiative_records()` reproduced both
failures:

- whitespace-kind/type-taskset was incorrectly present as
  `INIT-TYPE-TASKSET`; and
- whitespace ID failed to produce `INIT-WORK-SPACE-ID`.

The exact same fixture against `5421f9b2` rejects the taskset and emits the
work-ID initiative. The earlier `2ab14c8c` provenance and normal mixed-record
duplicate closure recorded above remain valid.

### Parity, Suite, Write/Check, Lock, and Scope

Root and template `_initiative_records()` have identical normalized AST with
SHA-256:

```text
fd799cc7eae073b60925f4b663e9a89a963415c4cc441e2cabe9496483927f34
```

Independent verification passed:

```text
python -m pytest tests/test_work_item_classifier.py \
  tests/test_template_work_item_classifier.py -q
7 passed in 3.20s

python scripts/work_item_classifier.py --root <worktree> \
  --json-out <temporary-json> --md-out <temporary-md> --write --check
work-item-classifier: pass
findings=0

python scripts/work_item_classifier.py --check
work-item-classifier: pass
findings=0

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

git diff --check efbe574d..5421f9b2
pass
```

The write/check outputs were deliberately directed to an OS temporary
directory, so the reviewer exercised the write path without changing the
repository-generated views.

The implementation delta changes exactly five files: the root/template
classifier copies, JSON/Markdown generated views, and generated host lock. The
failure-first commit owns the two test-file additions. There are no file moves,
storage changes, dependency changes, record relocation, or numbering-policy
changes.

### Production Semantic Churn

The production JSON payload at `efbe574d` and `5421f9b2` is byte-equivalent
after removing only `generated_at`. It retains all 438 records, findings 0,
and identical initiative/taskset/task/unit rows. The production Markdown is
also line-equivalent after removing its `generated_at` line.

Measured semantic churn is therefore exactly zero: no ID, kind/level, title,
status, parent, path, order, number, finding, or record-count change. The two
generated file changes are timestamp refreshes only.

### Fresh W4a Evidence

The latest task and unit evidence records parse correctly, identify worker
`codex-root-task-ar-609`, and each contain three passing commands with zero
return codes and empty stderr:

- `reviews/VERIFY-2026-07-23-task-ar-609-20260723073137.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723073144.json`

Each records 7 tests passing, classifier write/check findings 0, and a current
host lock. The superseded intermediate unit evidence does not affect the
latest task/unit pair.

### Final Validation Metrics

| Metric | Threshold | Measured value | Status |
| --- | --- | --- | --- |
| root adversarial normalization matrix | all pass | 15/15 | pass |
| template adversarial normalization matrix | all pass | 15/15 | pass |
| `efbe574d` failure-first causality | old fails, remediation passes | 2/2 | pass |
| legitimate initiative stability | exact title/status/order/number | 3/3 per copy | pass |
| root/template AST parity | identical | identical | pass |
| registered suite | all tests pass | 7/7 | pass |
| classifier temporary write/check | findings 0 | 0 | pass |
| production classifier check | findings 0 | 0 | pass |
| generated host lock | no drift | current | pass |
| production semantic churn | zero | 0 fields/rows | pass |
| scope | no moves or numbering/storage policy changes | none | pass |

### Final Verdict

**APPROVE** TASK-AR-609 at latest W4a HEAD
`b0bbce9d8e544bb7a07ed39c23d16d1fa1f57308`, remediation implementation
`5421f9b2987d8ae3b85aa042f6fbc9618bdb57bc`.

Both historical blockers are closed, canonical precedence and compatibility
fallback are deterministic after normalization, the ordinary mixed-record
duplicate fix remains intact, and all parity, regression, write/check, lock,
scope, and generated-view stability gates pass.

This remediation re-review modified only this skeptic report. It did not
modify implementation files, tests, generated classification views, W4a
evidence, task/runtime metadata, `reviews/INDEX.md`, or the separately present
W4b report.
