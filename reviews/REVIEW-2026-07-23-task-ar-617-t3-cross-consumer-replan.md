---
title: TASK-AR-617 Cross-Consumer T3 Replan
date: 2026-07-23
signal: pass
score: 99
task_id: TASK-AR-617
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
review_type: w4b-rework-replan
trigger: independent-cross-consumer-blocker
blocked_head: ed914753
reviewed_by: codex-root
tags: [t3, w4b-rework, frontmatter, cross-consumer, data-integrity]
---

# TASK-AR-617 Cross-Consumer T3 Replan

## Bottom Line

The first W4b rework closed all Python `splitlines()` truncation boundaries,
but skeptic verification found a second blocker: marker-bearing scalars written
by `scripts/work.py` are decoded by `backlog_board` consumers while the
independent parsers in `org_model_gate` and `work_schema_gate` expose the marker
literally.

This leaks encoded text into attention views and dispatch worker context even
though the canonical file can be read correctly by the work CLI. The task is
not approvable until every operational consumer of free-form work metadata uses
the same decoder.

## Independent Evidence

- `attention_inbox` imports `org_model_gate.parse_frontmatter`; an encoded task
  title is displayed with the literal marker.
- `dispatch_gate` uses the same parser and forwards marker-bearing context,
  target files, and acceptance values into `org_orchestrator.build_order`.
- `work_schema_gate` has a separate scalar cleaner and validates the encoded
  representation rather than the original semantic value.
- ID/status-only parsers are unaffected because their canonical values never
  require unsafe-scalar encoding, but free-form operational consumers are in
  scope.

## Revised Compatibility Surface

- Keep `backlog_board.decode_encoded_work_scalar` as the single decoder.
- Make `org_model_gate.parse_frontmatter` call that decoder before its existing
  boolean/integer and quote coercion. This automatically aligns
  `attention_inbox`, `dispatch_gate`, `observability_export`, `org_read_api`,
  `unit_readiness_report`, and `work_efficiency` without duplicating logic.
- Make root/template `work_schema_gate` call the same decoder before existing
  scalar/list compatibility behavior.
- Add direct parser tests plus attention and dispatch end-to-end regressions.

## Boundaries

- Do not modify attention, dispatch, or orchestration production behavior; fix
  their shared metadata input parser.
- Do not centralize unrelated review/frontmatter parsers whose consumed fields
  are IDs, statuses, timestamps, or numeric metrics and cannot be marker
  encoded under canonical work generation.
- Do not weaken schema validation or marker fail-closed behavior.
- Preserve legacy non-marker quoted, flow-list, boolean, integer, and malformed
  input semantics.

## Revised Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q`
- `python scripts/work_schema_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`
- independent scalar/list probes through backlog, org-model, root work-schema,
  template work-schema, attention, and dispatch paths.

## T3 Decision

Expand the active task/unit/claim footprint only to the two shared operational
parsers, the template work-schema mirror, their focused tests, and the existing
host lock. Preserve both prior REWORK reports and require fresh W4a plus two
independent W4b rechecks after implementation.
