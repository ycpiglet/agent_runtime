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

## COMPOUND-2026-06-10-002: Response contract enforcement gap

### Bottom Line
- The same response-format drift class recurred: status vocabulary and report shape were not applied in live chat.
- Compound logging was working as a record, but not as a prevention loop.
- The missing closure was an executable gate that fails when normative response rules still allow color-status contracts or omit the pre-answer checklist.

### 5W1H
| Field | Record |
|---|---|
| Who | Assistant/Codex response path; affected Owner-facing governance and status reports. |
| What | A user-facing reply used the wrong language/format path and did not preserve the established `pass/watch/block` status vocabulary and BRIEF/report shape. |
| When | 2026-06-10T17:00:08+09:00 investigation checkpoint. |
| Where | Chat response for `C:\Users\ycpig\agent_runtime`; normative surfaces: `REPORTING-FORMAT.md`, template `AGENTS.md`, scheduled prompt templates, governance gate scripts. |
| Why | The prior Compound entry said enforcement was needed, but the enforcement task had not been connected to `owner_governance_gate.py`, doctor, publish-check, or template sync. |
| How | Stale `G/Y/R` examples remained in normative templates, and direct conversation output had no mandatory pre-answer check for user language, BRIEF order, or status vocabulary. |

### Situation
- The repo already had `COMPOUND-2026-06-09-001` for BRIEF format drift.
- Memory and project guidance had also established `pass/watch/block + score` as the preferred status contract.
- The live issue therefore was not discovery; it was missing enforcement and contradictory template text.

### Cause
- Primary cause: Compound entries were treated as retrospective notes, not as work items that must close with executable prevention.
- Secondary cause: `REPORTING-FORMAT.md` contained both the newer `pass/watch/block` rule and older `G/Y/R` examples, so agents could follow either.
- Secondary cause: `owner_governance_gate.py` did not run a response-contract gate.
- Secondary cause: scheduled prompt and `AGENTS.md` templates could regenerate the old status vocabulary in future host installs.

### Recurrence Count
- Repo-local Compound count for this exact BRIEF/status drift class: 2 entries, including `COMPOUND-2026-06-09-001` and this entry.
- Cross-session memory indicates older BRIEF/reporting drift corrections also exist, so this is not a first or isolated failure.
- The accurate diagnosis is: Compound recorded recurrence, but did not yet force remediation closure.

### Forced Rule
- Any user-facing `status`, `report`, `brief`, `plan`, backlog, review, or summary answer must use the user's language unless explicitly requested otherwise.
- Default visible order: `Bottom Line -> Signal -> Insight -> Decision -> Action Board -> Next`.
- Status machine values: `pass/watch/block` + `score: 0-100`.
- Color names or color abbreviations are not valid status machine values in normative response contracts.
- If a Compound entry says "Needs enforcement", the next closure step must add or update an executable gate, not only another note.

### Preventive Action
- Add `scripts/response_contract_gate.py`.
- Run it from `scripts/owner_governance_gate.py`.
- Ship the gate in project templates and publish checks.
- Update normative template docs so stale color status examples fail before release.

### Status
- signal: pass
- score: 92
- Enforcement implemented and verified in working tree.

## COMPOUND-2026-06-10-003: Continuity pointer and repeated-request API gap

### Bottom Line
- The Owner repeated the same class of feedback: session continuity, language,
  BRIEF shape, status vocabulary, and repeated-request promotion were still not
  reliably applied.
- The root issue was structural: rules existed in long documents and memory,
  but there was no compact live work pointer plus executable continuity gate.
- The closure must therefore be a gate and pointer contract, not another
  prose-only reminder.

### 5W1H
| Field | Record |
|---|---|
| Who | Lead Engineer / agent response path; affected future memory-reset agents and host adopters. |
| What | Repeated Owner requests were not automatically promoted into function/API, scripts, hooks, gates, tasks, live work pointers, or Compound remediation. |
| When | 2026-06-10T17:38:07+09:00 |
| Where | `C:\Users\ycpig\agent_runtime`; surfaces: README, template AGENTS/CLAUDE, pointer, owner governance gate. |
| Why | The project had partial pointers (`STATUS.md`, backlog, task records, claims), but no single mandatory live work pointer contract and no continuity gate. |
| How | Agents could read long docs selectively, miss a standing preference, answer in the wrong language/format, and still pass existing gates. |

### Situation
- `COMPOUND-2026-06-09-001` and `COMPOUND-2026-06-10-002` already recorded BRIEF/status drift.
- The Owner then asked why repeated prompt requests were not converted into
  reusable functions/APIs and why Compound did not prevent recurrence.
- Existing docs were useful but too distributed for cold-start recovery.

### Cause
- Primary cause: no enforced live work pointer with current agent/team/pane,
  task, status, phase, progress, worktree, responsibility, verification, and
  next action.
- Secondary cause: repeated-request handling was policy text, not a checked
  contract.
- Secondary cause: Compound entries did not force executable prevention when
  feasible.
- Secondary cause: README was acting as a dense technical record instead of a
  friendly bilingual entry point that points humans and agents to deeper docs.

### Forced Rule
- Maintain `agents/project/NEXT-SESSION-POINTER.yml` and
  `agents/runtime/task_claims/*.json` as the first live work read target.
- README must stay bilingual (`한국어` and `English`) and point to deeper
  protocol docs.
- Template `AGENTS.md` and `CLAUDE.md` must define:
  - session continuity pointer maintenance;
  - `Evaluate -> Propose -> Verify -> Merge`;
  - golden set / failure / edge case preservation;
  - repeated request API promotion;
  - Owner-owned criteria and merge decisions;
  - mandatory Compound capture for repeated mistakes or criticism.
- Owner governance must run a continuity contract gate.

### Preventive Action
- Add `scripts/continuity_contract_gate.py`.
- Ship the gate in project templates.
- Add `agents/project/NEXT-SESSION-POINTER.yml`, active_work fields, and
  template pointer.
- Wire the gate into `owner_governance_gate.py`, doctor, publish-check, and
  publish-bundle.

### Status
- signal: pass
- score: 94
- Enforcement implemented in working tree and verified by full tests and release-facing gates.

## COMPOUND-2026-06-10-004: Task-set completion inferred from claims instead of canonical tasks

### Bottom Line
- `TASKSET-AR-QUALITY-LOOP` was reported as effectively complete before all canonical task files in that set were complete.
- Runtime claims were closed, but `agents/lead_engineer/tasks/TASK-AR-221.md` and `agents/lead_engineer/tasks/TASK-AR-243.md` still showed unfinished states.
- The fix is an executable task-set completion gate, not another manual reminder.

### 5W1H
| Field | Record |
|---|---|
| Who | Assistant/Codex task-set closeout path; affected Owner progress view for task set 1. |
| What | Completion was judged from active/released claims and UI task-set aggregation instead of the canonical task files for the whole task set. |
| When | 2026-06-10 task-set closeout cycle. |
| Where | `C:\Users\ycpig\agent_runtime`; surfaces: `agents/runtime/task_claims/`, `agents/lead_engineer/tasks/`, `agents/project/NEXT-SESSION-POINTER.yml`, task-set UI state. |
| Why | `taskset_work_gate.py` checked task-set IDs and board freshness, but had no mode to require a named task set to have all tasks completed and all claims fully released. |
| How | Closed claims for `TASK-AR-205` through `TASK-AR-208` and `TASK-AR-217` made the runtime view look done, while task-file scan still had `TASK-AR-221` as `in_progress` and `TASK-AR-243` as `planned`. |

### Situation
- The Owner asked for task set 1 to be progressed and finished.
- Task set 1 maps to `TASKSET-AR-QUALITY-LOOP`.
- The canonical set contains seven tasks: `TASK-AR-205`, `TASK-AR-206`, `TASK-AR-207`, `TASK-AR-208`, `TASK-AR-217`, `TASK-AR-221`, and `TASK-AR-243`.
- Runtime claims only represented the subset currently claimed by dispatcher runs.

### Cause
- Primary cause: completion audit used runtime claims as the main source of truth instead of task files plus claims.
- Secondary cause: `NEXT-SESSION-POINTER.yml` could mention multiple task sets even after one set was complete, confusing task-set progress interpretation.
- Secondary cause: no `--require-complete --task-set-id` gate existed for explicit Owner requests like "finish task set 1".

### Forced Rule
- For "finish task set N" requests, identify the task-set ID and enumerate all canonical task files with that `task_set_id`.
- Completion requires every canonical task in the set to be `completed` and every claim for the set to be non-active with `phase=taskset-completed` and `progress_pct=100`.
- Do not use UI aggregation alone as proof of completion because it is claim-derived and omits unclaimed planned/in-progress task files.

### Preventive Action
- Extend `scripts/taskset_work_gate.py` with `--task-set-id` and `--require-complete`.
- Add regression coverage so incomplete task files and stale released-claim metadata fail the gate.
- Use `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-QUALITY-LOOP --require-complete --check` before claiming task set 1 is complete.

### Status
- signal: pass
- score: 95
- Enforcement implemented in working tree; Quality Loop closeout uses the new named task-set completion gate.
