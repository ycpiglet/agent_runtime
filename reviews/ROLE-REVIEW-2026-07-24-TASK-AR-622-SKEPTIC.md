---
title: TASK-AR-622 Skeptic and Adversarial Review
date: 2026-07-24
status: hold
signal: fail
score: 80
verdict: BLOCK
task_id: TASK-AR-622
unit_id: UNIT-TASK-AR-622-001
reviewed_head: a1fbacceb4fb605d2436c4a19444c34c5e07cc09
verified_by: /root/task_ar_611_auditor
worker: /root/task-ar-622
role: skeptic
tags:
  - task-ar-622
  - skeptic
  - frontmatter
  - data-integrity
  - fail-closed
---

# TASK-AR-622 Skeptic and Adversarial Review

## Gate

This review evaluates exact HEAD
`a1fbacceb4fb605d2436c4a19444c34c5e07cc09` for independent W4b release. The
reviewed worktree was initially clean at that HEAD. When concurrent blocker
rework later changed the shared worktree, the exact commit was exported with
`git archive` and all final adversarial commands were run from the isolated
archive. No later uncommitted or committed fix is included in this verdict.

The required gate is:

1. detect raw legacy hash-bearing scalars without bypass;
2. avoid false positives for quoted values, genuine comments, supported flow
   values, Markdown body hashes, and delimiter-less legacy headers;
3. make `verify` and `close` fail before commands or any file write;
4. preserve the existing versioned scalar encoding and exact round trips.

## Readiness decision

**BLOCK — 80/100.**

The canonical two-space examples, false-positive boundaries, and encoded
scalar compatibility pass. The gate remains fail-open for raw values whose
pre-comment portion becomes empty and for valid YAML list indentation other
than exactly two spaces. Both `verify` and `close` were independently shown to
proceed, rewrite the record, and permanently remove the missed hash-bearing
item.

## Blocking finding

### B1 — raw-list and empty-value forms bypass the detector and are rewritten away

At the reviewed HEAD, list detection is restricted to:

```python
if uncommented.startswith("  - ") and current_list:
```

and it records a finding only when the post-comment item remains nonempty:

```python
if uncommented != raw.rstrip() and item and ...
```

The top-level empty-value path likewise treats `key: #274` as a new empty list
instead of an unsafe scalar.

The following exact raw cases all returned no findings:

```yaml
context: #274
```

```yaml
acceptance:
  - #275
```

```yaml
acceptance:
    - Preserve issue #274 before verification.
```

Measured pure-function results:

```text
empty top-level value: findings=[]; parsed={"context": []}
empty two-space item:  findings=[]; parsed={"acceptance": []}
four-space item:       findings=[]; parsed={"acceptance": []}
```

Four-space indentation is valid YAML for a sequence nested under a mapping key.
It is also realistic legacy/human-authored frontmatter. The lightweight parser
does not retain that item, so allowing the lifecycle rewrite converts the
already dangerous parse into permanent loss.

#### End-to-end verify bypass

An isolated raw unit used a four-space unsafe acceptance item and an explicit
verification command that created a sentinel file:

```text
detector findings=[]
work verify returncode=0
verification command ran=true
unit bytes changed=true
raw "Preserve issue #274" survives=false
evidence written=true
```

`work verify` reported `passed`, wrote verification evidence, and rewrote the
frontmatter without the raw item. This directly violates the required
fail-before-command and fail-before-write boundary.

#### End-to-end close bypass

An otherwise close-ready isolated unit used the same four-space unsafe item:

```text
detector findings=[]
work close returncode=0
status=closed
unit bytes changed=true
raw "Preserve issue #274" survives=false
```

Closeout metadata was written and the original item disappeared. This directly
violates the required fail-before-close-rewrite boundary.

The focused tests cover a nonempty, exactly two-space list item and therefore
do not exercise either empty-after-comment or alternate-valid-indentation
forms.

## Passed adversarial checks

### False-positive and boundary behavior

The detector correctly returned no findings for:

- a double-quoted hash value followed by a genuine YAML comment;
- a single-quoted hash value followed by a genuine YAML comment;
- a complete simple flow list followed by a comment;
- a complete flow mapping containing a quoted hash followed by a comment;
- quoted and simple flow-style list items followed by comments;
- full-line frontmatter comments;
- hashes after the closing `---`;
- Markdown body hashes;
- body hashes after a `##` boundary in delimiter-less legacy records;
- an existing versioned encoded scalar followed by a comment.

It correctly found:

- a top-level plain `context: Preserve issue #274`;
- `origin_ref: github:#274` without whitespace before the hash;
- a nonempty, exactly two-space plain list item;
- an incomplete simple flow value truncated by a hash;
- a delimiter-less legacy header containing an unsafe plain scalar;
- multiple unsafe top-level/list values with correct key and line attribution.

Thus normal quoted comments, simple supported flow values, body text, and the
delimiter-less header boundary do not create the blocker. The blocker is the
incomplete fail-closed coverage described in B1.

### Write-before-failure for detected cases

For supported detected forms, independent full CLI checks passed:

```text
verify: rc=1, unsafe finding=true, complete tree byte-identical=true,
        verification side effect=false
close:  rc=1, unsafe finding=true, complete tree byte-identical=true
```

Pre-existing unit bytes, evidence, `reviews/INDEX.md`, and
`BACKLOG-BOARD.md` sentinels were unchanged. The loader placement before parse
and lifecycle writes is correct once the detector actually returns a finding.

### Scalar encoding compatibility

The existing `\u001eagent-runtime-work-scalar-v1:` encoding round-tripped
exactly across two serialize/parse cycles for:

- hash-bearing text with both quote types;
- bracket-looking text;
- leading/trailing whitespace;
- list values containing hashes;
- boolean-like and numeric-like strings;
- newline and control-separator values.

Both detector passes returned no findings, and both parsed dictionaries exactly
equaled the source metadata. A pre-existing encoded hash value with a genuine
trailing comment also decoded exactly. No encoding compatibility blocker was
found.

## Additional adversarial observations

- A malformed nested flow form such as `[[safe] #274]` is considered
  delimited after truncation because only the first and last characters are
  checked. It then parses to a different list. This strengthens the need for a
  structural rather than superficial flow boundary, although B1 alone is
  sufficient to block.
- A valid flow list containing a quoted comma is accepted but the lightweight
  flow parser splits on every comma. That is a pre-existing broader flow-parser
  limitation rather than the exact unquoted-hash acceptance criterion, but the
  implementation review should avoid implying full YAML-flow compatibility.
- No reviewed migration is attempted, which is correct. The implementation
  does not guess discarded suffix content or bulk-rewrite historical records.

## Commands and results

- Exact-HEAD archive:
  `git archive --format=tar a1fbacceb4fb605d2436c4a19444c34c5e07cc09`
- Exact archived focused suite:
  `py -3.10 -m pytest tests/test_work_registration.py
  tests/test_work_verify.py tests/test_work_close.py -q`
  → **25 passed in 16.45s**
- W4a evidence
  `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051.json`
  records the same 25 focused tests and Owner governance passing.
- Pure detector matrix: quoted/comment/flow/body/delimiter-less expected cases
  passed; empty-value and four-space list bypasses reproduced.
- Full isolated CLI A/B: detected two-space cases were byte-identical refusals;
  four-space cases passed and rewrote data in both verify and close.

The green focused suite is insufficient because it does not contain the
blocking counterexamples.

## Blockers

1. Detect and refuse an unsafe scalar when comment stripping leaves an empty
   top-level value or empty list item.
2. Recognize list items with any supported YAML indentation, or fail closed on
   unsupported indented frontmatter syntax before lifecycle rewrite.
3. Add full `verify` and `close` regressions proving the above forms produce no
   command execution and no file mutation.

## Warnings and residual risks

- Flow completeness is currently inferred only from matching first/last
  delimiters; malformed nesting can evade the scanner.
- The custom flow-list parser is not a complete YAML parser. Documentation
  should state the supported subset or the raw safety gate should reject forms
  it cannot round-trip losslessly.
- The active claim and worktree are expected W4 state and must not be released
  on this blocked HEAD.

## Required next actions

1. Implement B1 coverage without weakening the verified quoted-comment,
   simple-flow, body, and delimiter-less boundaries.
2. Run the new counterexamples through full CLI verify/close tests with
   complete-tree byte snapshots and command-side-effect sentinels.
3. Rerun the 25 focused tests plus Owner governance and write fresh W4a evidence
   at a new exact HEAD.
4. Request a fresh independent exact-HEAD W4b review before claim release.

## Final verdict

**Quoted/comment boundaries: PASS. Detected-case pre-write refusal: PASS.
Scalar encoding compatibility: PASS. Raw detector completeness: FAIL.
TASK-AR-622 at `a1fbacce`: BLOCK.**
