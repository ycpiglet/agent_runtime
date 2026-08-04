---
title: TASK-AR-653 Semantic Delta and Exact Identity Final Independent W4b
date: 2026-07-31
created_at: 2026-07-31T02:46:37+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: 059bc5fb87109eb5095960b28c30a8431e71c821
repair_parent: 059bc5fb87109eb5095960b28c30a8431e71c821
reviewed_commit: 30fdf025ee3d15f88678934c827a287916f64e04
reviewed_tree: c868d2fea06e952b699bce6223885b04a22137d2
w4a_admin_head: f3a162f9c30f41aecd6bce8e96ee6950daefcffe
w4a_admin_tree: 83dcb94fc5f9e805de252c143f2716e50fabe9bc
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..30fdf025ee3d15f88678934c827a287916f64e04
repair_range: 059bc5fb87109eb5095960b28c30a8431e71c821..30fdf025ee3d15f88678934c827a287916f64e04
verifier_agent_instance_id: qa-20260731-ar653-semantic-delta-exact-identity-final-w4b
verified_by: qa-20260731-ar653-semantic-delta-exact-identity-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_semantic_delta_exact_identity_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
independence_status: independent
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
tags: [w4b, scribe, semantic-delta, markdown, json, exact-identity, independent-verification, revise]
---

# TASK-AR-653 Semantic Delta and Exact Identity Final Independent W4b

## Independent Verdict

`REVISE — P0: 0, P1: 2, P2: 0.`

The candidate closes the prior identity-normalization bypass and the registered
suite is green. It also retains the earlier Git audit-view, exact owner
`no_touch`, host-lock, package, and three-way mirror protections.

Two stronger fail-open source-delta paths remain:

1. Markdown blank-line changes are discarded before matching even when a blank
   line changes the CommonMark node structure of protected content; and
2. state-source JSON is parsed without duplicate-member rejection, so an
   arbitrary duplicate collection or a non-exact duplicate-field summary can
   be present in the raw canonical source while record and replay both approve
   it.

Both independent public-API reproductions produce
`verified_reduction`, `hot_count=11`, and `readiness=ready`. P0 and P1 must both
be zero for approval, so this report is not a release credential.

## Exact State, Evidence, and Independence

| Identity | Exact value |
| --- | --- |
| Complete implementation base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Latest blocking evidence / repair parent | `059bc5fb87109eb5095960b28c30a8431e71c821` |
| Reviewed implementation | `30fdf025ee3d15f88678934c827a287916f64e04` |
| Reviewed implementation tree | `c868d2fea06e952b699bce6223885b04a22137d2` |
| W4a/admin HEAD | `f3a162f9c30f41aecd6bce8e96ee6950daefcffe` |
| W4a/admin tree | `83dcb94fc5f9e805de252c143f2716e50fabe9bc` |
| Verifier | `qa-20260731-ar653-semantic-delta-exact-identity-final-w4b` |
| Verifier task | `/root/task_ar_653_semantic_delta_exact_identity_final_w4b` |
| Worker | `le-20260730-234934-kst-ar653004` |

This verifier is a distinct agent instance with independent conversation
context and did not share the worker identity or conclusions. The repository
contract, complete `independent-verification` skill, lifecycle references,
unit record, prior W4a/W4b repair chain, exact implementation diff, and machine
evidence were read before testing. Both requested ranges were reviewed:

- `ae998f7b3b96def7347be7317e3cadda6078150f..30fdf025ee3d15f88678934c827a287916f64e04`
- `059bc5fb87109eb5095960b28c30a8431e71c821..30fdf025ee3d15f88678934c827a287916f64e04`

Candidate-to-admin changes are only the unit/index/W4a/machine-evidence
artifacts; no implementation changes occur after the candidate. The worktree
and index were clean before this report.

Evidence integrity matched the supplied bindings:

| Evidence | SHA-256 |
| --- | --- |
| Prior blocking W4b | `6ac964ab539bb57c913bf2ccbfdbe3d8919607602d49a479a015a6e5701a2525` |
| Fresh W4a | `487848faf61db5bc4936a3dc86969611018dbec13c0cc975c4a13f7f54b8d75e` |
| Machine verification | `6f8de50c8d3a11f375dc8836173835e6727e3d75d17ae3f88cf3923323079fbe` |

## P1-1 — Blank-Line Elision Changes Protected Markdown Semantics

`_validate_cleanup_delta()` removes every blank line from both Markdown
versions before `_matches_bound_cleanup_rewrite()` runs. The matcher therefore
cannot distinguish formatting-only blank changes from blank changes that
create, terminate, or alter Markdown blocks.

### Independent Setext reproduction

An offline temporary Git repository used a baseline with 16 hot list rows:

```markdown
Protected heading
---
- item 0
...
- item 15
```

The cleanup plan bound the six oldest candidate rows. The after-source deleted
five of those candidates and inserted one blank line between the two protected
nonblank rows:

```markdown
Protected heading

---
- item 5
...
- item 15
```

No protected nonblank byte changed. Nevertheless, a CommonMark parser reports
the protected prefix changing from a Setext heading to a paragraph followed by
a thematic break. The public receipt flow accepted it:

```json
{
  "record_status": "verified_reduction",
  "replay_status": "verified_reduction",
  "hot_count": 11,
  "readiness": "ready",
  "before_semantic_block": "heading",
  "after_semantic_blocks": ["paragraph", "thematic_break"]
}
```

### Independent raw-HTML reproduction

A second baseline placed a protected paragraph and the same 16 list rows after
an opening `<div>` HTML block separated by a blank line. Removing that blank
line while deleting five bound candidates caused CommonMark to absorb the
protected paragraph and list into the raw HTML block. The baseline had parsed
paragraph/list nodes; the after-source had neither. Record and immediate replay
again both returned `verified_reduction` and `ready`.

This is the same root cause across Setext and raw-HTML block boundaries. It
also shows why globally declaring blank lines outside the semantic model is not
safe for Markdown.

### Required repair

- Preserve and validate blank-line placement wherever it can affect Markdown
  block structure.
- Either compare a bounded structural Markdown representation or allow blank
  changes only inside a proven candidate replacement span with unchanged
  protected-node context.
- Apply the same check at receipt creation and replay.
- Add negative regressions for Setext heading creation/destruction, raw HTML
  block termination, list looseness/continuation boundaries, and blank changes
  adjacent to fenced/comment/heading boundaries.
- Retain positive deletion-only and exact bounded-summary paths.

## P1-2 — Duplicate JSON Members Bypass Outer Structure and Exact Summary Form

`parse_json()` and `_json_cleanup_view()` use ordinary `json.loads()`. Python
silently keeps the last value for a repeated object member. The delta matcher
therefore validates only the collapsed object, not the raw canonical JSON text.
This is inconsistent with the fail-closed, duplicate-aware parser already used
for owner-decision evidence.

### Arbitrary duplicate collection reproduction

The baseline was a normal object containing 16 open entries in `items` and an
unchanged outer `version` field. The after-source contained two `items`
members:

```json
{
  "items": [{"id": "TASK-INSERTED-OUTSIDE-PLAN", "status": "open"}],
  "items": [
    {"id": "item-5", "status": "open"}
  ],
  "version": 1
}
```

The second collection contained the full `item-5` through `item-15` sequence.
The raw canonical source therefore contained an arbitrary, unplanned entry and
a changed outer member structure, but last-value parsing hid it from validation.
Observed public-flow result:

```json
{
  "record": "verified_reduction",
  "replay": "verified_reduction",
  "hot": 11,
  "readiness": "ready",
  "raw_contains_arbitrary_entry": true
}
```

Different JSON consumers are known to handle duplicate names differently, so
the receipt does not establish one stable collection identity.

### Non-exact summary reproduction

A separate after-source used the otherwise valid bounded summary but repeated
`candidate_count`:

```json
{
  "kind": "scribe_cleanup_summary",
  "status": "completed",
  "candidate_count": 999,
  "candidate_count": 5,
  "cleanup_plan_digest": "<BOUND_PLAN_DIGEST>"
}
```

The raw summary violates the declared exact form. Last-value parsing collapses
it to the expected count, and both record and replay still returned
`verified_reduction`, `hot=11`, and `ready`.

### Required repair

- Parse every state-source JSON object with recursive duplicate-member
  detection and reject any repeated member name before planning, recording, or
  replaying a receipt.
- Use the same duplicate-aware representation in `parse_json()` and
  `_json_cleanup_view()`.
- Add record/replay negatives for duplicate outer collection members,
  duplicate entry fields, and duplicate fields in cleanup-summary objects.
- Preserve compatible object-key reordering and whitespace-only serialization
  changes when member names are unique; continue to reject collection entry
  reordering, arbitrary insertions, collection identity changes, and outer
  value changes.

## Closed Families and Compatibility Evidence

The two findings above do not invalidate the protections that independently
passed:

- HTML-comment, fenced-code, heading, ordinary list-structure, protected-row
  deletion, candidate movement, continuation re-parenting, arbitrary
  replacement, wrong summary count/digest, and replay-rebinding regressions
  passed in the registered suite.
- Valid Markdown deletion, structurally empty heading deletion, valid JSON
  deletion, and exact bounded Markdown/JSON summaries remained valid.
- Exact raw TASK/UNIT/owner identity regressions passed for ASCII and Unicode
  padding, decoded controls, placeholder/non-string values, conflicting record
  identities, and legacy receipt replay.
- Exact owner `no_touch` retained byte-equivalent before/after source bindings;
  rewrite, increase, and rebound replay cases failed closed.
- Git replacement refs and graft state failed closed at record and replay.
  Inspection also confirmed that inherited `GIT_*` variables are removed and
  audit subprocesses receive `GIT_NO_REPLACE_OBJECTS=1`,
  `GIT_NO_LAZY_FETCH=1`, `GIT_OPTIONAL_LOCKS=0`, and
  `GIT_TERMINAL_PROMPT=0`.
- JSON entry order and outer collection identity remain position-bound when
  member names are unique.

## Bounded Resources, Mirrors, Host Lock, Package, and Footprint

The rewrite matcher remains bounded by the declared source and plan contract:

- each source read is capped at `2 MiB`;
- the cleanup plan is capped at 10 candidates;
- the matcher rejects an after-row count larger than the before-row count;
- its state alternatives arise only from those at-most-10 deletable candidates;
  and
- traversal is linear in bounded source rows with constant plan-bounded
  alternatives rather than an unbounded quadratic diff.

The three portable state-projection copies are byte-identical with SHA-256:

`00a4f3050d787a918560c821e86a5f57fca52ceac8d7909d6693f289545b117c`

The host lock check passed and the fixture SHA-256 is:

`69d92f142eab4b04749bf3f3e240a426d066e492a5f79dde36a9d33436cb819e`

Static package-data coverage plus the wheel packaging guard passed
(`2 passed`), and the managed packaged projection path exists in the template.
The mirror gate reports 84 expected/common paths, 81 identical, 3 intentional,
and 0 findings.

The repair range changes exactly six declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/agents/scribe/SKILL.md`
- `tests/test_scribe_due.py`
- `tests/fixtures/host/agent_runtime.lock.json`

The complete range contains the earlier declared implementation/test changes
plus unit/index/review/verification lifecycle evidence. No undeclared
implementation path was found. `git diff --check` passed for both requested
ranges.

## Independent Command Ledger

| Command or probe | Result |
| --- | --- |
| Registered unit pytest command with bytecode/cache disabled | `177 passed in 46.50s` |
| `python scripts/template_mirror_gate.py --check` | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Focused Git-audit and exact-identity matrix | `31 passed, 72 deselected in 2.84s` |
| Wheel package-data guard | `2 passed in 0.10s` |
| `python scripts/regen_host_lock_if_needed.py --check` | up to date |
| Three-way projection `cmp` / SHA-256 | byte-identical / `00a4f305...` |
| Both requested `git diff --check` ranges | pass |
| Setext blank-line public record/replay probe | incorrectly accepted as ready |
| Raw-HTML blank-line public record/replay probe | incorrectly accepted as ready |
| Duplicate JSON collection public record/replay probe | incorrectly accepted as ready |
| Duplicate summary-field public record/replay probe | incorrectly accepted as ready |
| Worktree before report | clean |

Registered command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_scribe_due.py tests/test_closure_gate.py \
  tests/test_session_continuity_hooks.py tests/test_doctor.py \
  tests/test_template_smoke.py -q -p no:cacheprovider
```

No network, credential, provider, broker, order, database migration,
notification, consumer-repository mutation, version, tag, package publication,
push, deployment, merge, release, or claim mutation occurred.

## Claim Disposition

Claim `CLAIM-20260730-234934-task-ar-653-ar653004` may **not** be released.
It must remain `claimed`, must not enter the merge queue, and must not advance
to W5. A repair needs focused RED/GREEN regressions, a fresh W4a bound to its
exact commit/tree, and another distinct independent W4b with P0=0 and P1=0.

This report is the verifier's only repository change.
