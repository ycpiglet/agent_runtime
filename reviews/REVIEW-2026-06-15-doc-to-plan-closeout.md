# REVIEW — Doc-to-Plan: Closeout (TASKSET-AR-DOC-TO-PLAN)

- **Date:** 2026-06-15
- **Taskset:** TASKSET-AR-DOC-TO-PLAN

## Bottom Line

The taskset is closed: a document → registerable plan pipeline (MVP), the Paperclip
gap-adoption decision, and the actuals + multi-factor efficiency evaluation. Registration
stays Owner-gated (B-mode); no document auto-applies to the registry.

## Per-task closeout

| Task | Deliverable | Evidence |
| --- | --- | --- |
| 366 | Doc → plan pipeline (MVP): md/txt/html (stdlib) + lazy/graceful PDF/PPTX/DOCX → analyze (goals/features/constraints/milestones) → **B-mode** taskset+task proposal (Owner-gated, `work.py new`-shaped) | `scripts/doc_to_plan.py`; 5 tests; demo pitch → taskset proposal |
| 367 | Paperclip 4-axis adoption decision (budget hard-stop ADOPT; heartbeat = Phase-2 daemon; multi-tenancy DEFER→vault; plugins → declarative widgets) | `reviews/REVIEW-2026-06-15-paperclip-gap-adoption-decision.md` |
| 368 | Actual-metrics + multi-factor evaluation: efficiency (outcome/cost) + est-vs-actual variance, sortable by tokens/hours/variance/efficiency/team/priority/difficulty | `scripts/work_efficiency.py`; 3 tests |

## Acceptance

- 366: a sample pitch doc converts to an approvable taskset proposal (plan + task
  decomposition); on approval it registers consistently via `work.py new`. ✓ (MVP; binary
  deck parsers are optional lazy libs — graceful when absent.)
- 367: each of the 4 axes has a 채택/보류/수정 verdict + rationale + follow-up; deferrals → Idea Vault. ✓
- 368: completed items expose `actual_*`; board-style sorting by est-vs-actual variance and
  efficiency works. ✓ (efficiency engine; deep board-column integration is a follow-up.)

## Follow-ups (non-blocking, recorded)
- 366: add optional local parsers for PDF/PPTX/DOCX (pdfplumber/python-pptx/python-docx) behind the existing lazy hooks; richer analysis (LLM-assisted decomposition) as B-mode.
- 367 adopts: aggregate budget ledger + hard-stop gate; Phase-2 `DaemonBackend` heartbeat lifecycle.
- 368: wire efficiency/variance columns into BACKLOG-BOARD rendering + the console list.

## Verification
- Stdlib-only (PyYAML-free); tests pass under a PyYAML-blocked (CI-equivalent) run.
- Owner-gated registration preserved — `doc_to_plan` never writes the registry.
