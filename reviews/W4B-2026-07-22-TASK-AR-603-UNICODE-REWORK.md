---
title: TASK-AR-603 Unicode Rework Independent W4b Verification
date: 2026-07-22
signal: pass
verdict: APPROVE
task_id: TASK-AR-603
verified_head: 73585da3ce9a9ab29d6d5def5090bd1212aa0a53
verified_by: codex-task-ar-603-independent-auditor-rework1
tags: [w4b, independent-verification, task-id-contract, unicode-boundary, github-299]
---

# TASK-AR-603 Unicode Rework Independent W4b Verification

## Verdict

**APPROVE** at exact HEAD
`73585da3ce9a9ab29d6d5def5090bd1212aa0a53`.

The prior W4b approval and subsequent skeptic BLOCK remain valid historical
evidence for their respective earlier HEADs. This rework review independently
confirms that the skeptic's Unicode larger-token counterexample is fixed while
the previously accepted numeric, timestamp, and suffix-case contract remains
unchanged.

## Validation Results

| Metric | Threshold | Measured result | Status |
| --- | --- | --- | --- |
| Declared focused suite | 101 tests pass | `101 passed in 31.31s` | pass |
| Root runtime gates | identity, conversation audit, taskset, classifier, and host lock all pass | 5/5 passed; zero findings; lock current | pass |
| Template/lock regression suite | all selected tests pass | 21/21 passed | pass |
| Root/template parity | shared contract and consumers remain equivalent | contract, dispatcher, and conversation audit are byte-identical | pass |
| Accepted value grammar | numeric and timestamp forms retain behavior | root and template each accepted 7/7 valid values and rejected 5/5 invalid values | pass |
| Timestamp suffix case | lowercase and uppercase preserved | root and template each preserved 2/2 variants | pass |
| Unicode larger-token boundary | accented Latin, Korean, and Greek adjacency rejected on both sides | root and template each rejected 7/7 Unicode cases, including all six required left/right cases | pass |
| Existing ASCII boundary | larger ASCII, underscore, and hyphen tokens remain rejected | root and template each rejected 7/7 cases | pass |
| Punctuation-delimited extraction | canonical tokens still extracted unchanged | root and template each returned the expected 4/4 tokens | pass |
| Failure-first provenance | both new regressions fail before the fix | commit `6f7c450`: 2 failed | pass |
| Refreshed W4a evidence | task and unit evidence contain 101 passes and a current lock | 2/2 evidence files passed; implementation `701a0f2` is the direct parent of evidence HEAD `73585da3` | pass |

## Commands And Evidence

```console
python -m pytest tests/test_task_identity.py tests/test_taskset_dispatcher.py tests/test_conversation_work_audit.py -q
# 101 passed in 31.31s

python scripts/task_identity.py check --check
# pass; findings=0

python scripts/conversation_work_audit.py --check
# pass; planning_records=19; findings=0 block=0 watch=0

python scripts/taskset_work_gate.py --check
# pass; findings=0

python scripts/work_item_classifier.py --check
# pass; findings=0

python scripts/regen_host_lock_if_needed.py --check
# OK; tests/fixtures/host/agent_runtime.lock.json is up to date

python -m pytest tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q
# 21 passed in 20.80s
```

An independent inline matrix loaded the root and template
`task_id_contract.py` files as separate modules. Both rejected task-ID matches
adjacent on the left and right to precomposed accented Latin (`é`), Korean,
and Greek word characters. The matrix also covered a Greek token embedded on
both sides, retained the seven prior ASCII/underscore/hyphen boundary cases,
accepted numeric `TASK-N`, numeric `TASK-AR-N`, lowercase/uppercase timestamp
forms, and preserved extracted token text exactly.

## Failure-First Reproduction

Commit `6f7c450` was exported to a disposable directory and only the two new
Unicode regressions were run against the pre-fix shared contract:

```console
python -m pytest \
  tests/test_conversation_work_audit.py::test_task_id_extractor_does_not_match_inside_unicode_words \
  tests/test_taskset_dispatcher.py::test_body_order_ignores_task_ids_embedded_in_unicode_words -q
# 2 failed in 1.07s
```

The conversation extractor returned all five embedded IDs, and taskset body
ordering returned both embedded IDs. This is the exact failure fixed by
`701a0f2`. The disposable export was removed after verification.

## W4a Lineage

The latest evidence files were independently parsed:

- `reviews/VERIFY-2026-07-22-unit-task-ar-603-001-20260722205011.json`
- `reviews/VERIFY-2026-07-22-task-ar-603-20260722205045.json`

Both record `status: passed`, two zero-returncode commands, `101 passed`, and a
current host lock. Git ancestry confirms implementation HEAD
`701a0f2829ce7e0176b656e47b65b72ca3676236` is the direct parent of final
evidence HEAD `73585da3ce9a9ab29d6d5def5090bd1212aa0a53`.

## Findings

- No unresolved correctness, regression, parity, scope, or evidence finding
  remains at the verified HEAD.
- The fix is limited to the shared root/template token boundary, its two
  failure-first consumer tests, regenerated host lock, and W4a records.
- The Unicode-aware `\w` boundary continues to include underscore, while the
  explicit `-` alternative preserves the prior hyphen-adjacency rejection.

## Residual Risks

- The boundary inherits Python `re` Unicode `\w` semantics rather than full
  Unicode text segmentation. The required accented Latin, Korean, Greek,
  ASCII, underscore, and hyphen matrices are covered; every Unicode category
  and grapheme composition is not exhaustively enumerated.
- This independent W4b ran the declared focused suite, targeted template and
  lock regressions, repository gates, and adversarial matrices rather than the
  entire package suite. Every modified runtime surface and reported failure
  path is directly covered.
