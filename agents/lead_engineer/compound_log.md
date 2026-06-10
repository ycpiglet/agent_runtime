# Compound Log

## COMPOUND-2026-06-09-001: Backlog BRIEF format drift recurrence

### Bottom Line
- The backlog response drifted away from the established decision-oriented BRIEF format.
- This was a recurrence, not a first occurrence.
- Existing rules were documented, but the live chat response path did not enforce them before answering.

### 5W1H
| Field | Record |
|---|---|
| Who | Assistant/Codex response path; affected user/Owner decision flow. |
| What | `백로그 띄워줘` was answered as a compressed list instead of the expected `Bottom Line -> Signal -> Insight -> Decision` decision board. |
| When | 2026-06-09, immediately after v0.1.8 reporting-format and README follow-up work. |
| Where | Chat response for `C:\Users\ycpig\agent_runtime`; related repo surfaces: `STATUS.md`, `BACKLOG.md`, `REPORTING-FORMAT.md`. |
| Why | The rule existed in documentation and memory, but there was no pre-answer runtime checklist/gate for conversational backlog rendering. The assistant optimized for brevity and accidentally treated the request as a plain summary. |
| How | The response used ad hoc `P0/P1` grouping and omitted required decision-support sections: `Bottom Line`, `Signal`, `Insight`, `Decision`, evidence/status interpretation, and clear recommendation. |

### Situation
- The user had repeatedly requested decision-friendly backlog output.
- Prior rules already identified canonical BRIEF and backlog board expectations.
- v0.1.8 added Executive BRIEF v2, but that implementation reinforced document/report artifacts more than direct chat output.
- The immediate preceding work updated README and backlog records, then the next `백로그 띄워줘` response still bypassed the canonical format.

### Cause
- Primary cause: live response rendering was not connected to the same enforcement path as repo artifacts.
- Secondary cause: "concise" was over-weighted against "decision-oriented".
- Secondary cause: the assistant did not reopen or apply `REPORTING-FORMAT.md` before answering a formatting-sensitive backlog request.
- Secondary cause: no explicit local rule existed that `백로그 띄워줘` means "render a decision board using BRIEF sections", not "summarize the backlog".

### Impact
- Decision quality degraded because the response hid priority rationale, current signals, insight, and recommended decision.
- Trust degraded because the same drift class had already been corrected before.
- The issue exposed a gap between policy text and actual response behavior.

### Recurrence Pattern
- Symptom: backlog/report output becomes shorter but less useful for decisions.
- Trigger: user asks for a simple surface command such as `백로그 띄워줘`.
- Failure mode: assistant treats the command as a plain list request and omits canonical sections.
- Root gap: no pre-answer format assertion for conversational outputs.

### Forced Rule
- For any user request matching backlog/report/status/plan/review/summary output, default to Executive BRIEF unless the user explicitly asks for raw/plain/minimal output.
- Required visible order:
  1. `Bottom Line`
  2. `Signal`
  3. `Insight`
  4. `Decision`
  5. `Priority` or `Action Board`
  6. `Next`
- Keep bullets concise, but do not remove decision context.
- If giving a short answer, preserve at least `Bottom Line`, `Decision`, and `Next`.

### Preventive Action
- Add a backlog follow-up to create a machine/readable response-format gate for generated plan/report/backlog artifacts.
- Add a prompt-level self-check: before answering `백로그`, ask internally, "Does this help the user decide?"
- Keep `REPORTING-FORMAT.md` as the canonical source for user-facing backlog/report outputs.

### Status
- Recorded.
- Needs enforcement task: response-format gate and backlog rendering contract.
