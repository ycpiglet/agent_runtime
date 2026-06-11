# AGENTS.md

Shared operating protocol for Codex, Claude, Gemini, Cursor, and other agents
working in this repository.

This file is the repository-level source of truth. Tool-specific files such as
`CLAUDE.md`, `GEMINI.md`, and `CURSOR.md` may add local guidance, but when they
conflict, follow this file and the latest records under `agents/lead_engineer/`.

## 0. Core Rules

1. Read the same starting context before doing non-trivial work.
2. Do not start implementation without an explicit user request or an approved
   `CYCLE` / `TASK` record.
3. Do not create duplicate work. Search existing tasks and backlog first.
4. Keep changes small, scoped, and verifiable.
5. A task is not complete until the result and verification are recorded.
6. Do not guess timestamps. Use `python scripts/now.py`.
7. Never commit secrets, credentials, private runtime state, or local tool data.
8. Owner-facing chat responses must be Korean by default. Use another language
   only when the Owner explicitly asks for it. Agent-to-agent notes, code
   comments, machine fields, and evidence records may use English when that is
   clearer or more parseable.

## 1. Start Protocol

Before non-trivial work, read:

1. `agents/project/NEXT-SESSION-POINTER.yml`
2. `AGENTS.md`
3. `README.md`
4. `agents/project/PROJECT-CONTEXT.yml` if present
5. `AGENT_RUNTIME.md`
6. `agents/lead_engineer/STATUS.md`
7. `agents/lead_engineer/AUDIT-LOG.md`
8. `agents/roles.yml`
9. Tool-specific guidance, if relevant
10. Your role file: `agents/{role}/SKILL.md`
11. `agents/lead_engineer/tasks/BACKLOG.md`
12. The latest relevant `CYCLE`, `REVIEW`, and `TASK` files

Create an internal context snapshot:

```text
latest cycle:
current request:
related task:
role:
owner:
scope:
out of scope:
done when:
verification:
```

Only print the snapshot when it would clarify ambiguity or risk.

## 1.5 Live Work Pointer

`agents/project/NEXT-SESSION-POINTER.yml` is the compact live work pointer for
the whole runtime, not only a next-session note. Together with
`agents/runtime/task_claims/*.json`, it must identify which agent, team, and
pane is working on which task, current status, phase, progress_pct, worktree,
branch, claim, handoff, pointers, required rules, and next verification steps.

Update it while work is happening and before closure whenever non-trivial state
changes:

1. active task, role, team, pane, owner, or responsibility changes;
2. a decision or blocker changes the next action;
3. status, phase, progress_pct, or verification status changes;
4. a repeated request becomes a rule, function/API, script, hook, gate, or task;
5. Compound captures a repeated mistake or criticism.

If the pointer and longer records disagree, treat the pointer as a resume hint,
then verify against the canonical task, status, backlog, and audit records.

## 2. Source Of Truth

| Topic | Source |
|-------|--------|
| Project overview and setup | `README.md` |
| Host project context | `agents/project/PROJECT-CONTEXT.yml` and `agents/project/*.md` |
| Shared agent protocol | `AGENTS.md` |
| Current operating status | `agents/lead_engineer/STATUS.md` |
| Decisions and operating changes | `agents/lead_engineer/AUDIT-LOG.md` |
| Role registry | `agents/roles.yml` |
| Open work board | `agents/lead_engineer/tasks/BACKLOG.md` |
| Task registry | `agents/lead_engineer/tasks/INDEX.md` |
| Individual tasks | `agents/lead_engineer/tasks/TASK-*.md` |
| Reports | `agents/lead_engineer/reports/` |
| Runtime model | `AGENT_RUNTIME.md` |

Do not hard-code the current cycle number in tool-specific documents. Determine
the latest cycle from the files in `agents/lead_engineer/`.

## 3. Project Context Overlay

Reusable runtime skills stay generic. Host-specific product identity, MVP
scope, vision, roadmap, organization, and external references live under
`agents/project/`.

When adapting this runtime to a new project:

1. Copy `agents/project/PROJECT-CONTEXT.example.yml` to
   `agents/project/PROJECT-CONTEXT.yml`.
2. Fill product-specific files such as `VISION.md`, `ROADMAP.md`, `ORG.md`,
   `TEAMS.md`, and `LINKS.md`.
3. Reference those files from TASK records and context packets.
4. Do not edit `agents/*/SKILL.md` or `scripts/*` to encode project-specific
   product behavior.

If a role needs project-specific nuance, add a host-owned note under
`agents/project/` and link it from the task. Promote it upstream only when it is
generic across projects.

## 4. Roles

| Role | Responsibility |
|------|----------------|
| Owner | Human final authority for irreversible, external, destructive, or high-risk changes |
| CEO | Autonomous coordinator for routine goals, scope, priority, cost, and risk |
| Managing Partner | Independent cost, direction, and role-balance review |
| Lead Engineer | Plan, task definition, assignment, review, and closure records |
| Independent Auditor | Evidence, completion, cost, and self-review audit |
| Doc Steward | Documentation freshness, integrity, stale references, and missing artifacts |
| Scribe | Cleanup, compression, normalization, and archive notes after canonical state is set |
| Research Agent | Evidence notes from official docs, standards, or external examples |
| Timeline Agent | Chronology reconstruction across tasks, meetings, audits, and messages |
| Requirements Interviewer | Clarifies ambiguous requests before plan or implementation |
| Secretary | Personal desk summary, reminders, agenda prep, and non-governance assistance |
| Backend Engineer | Server, data, auth, and API surfaces for the host project |
| UI/UX Designer | Frontend, accessibility, responsive behavior, and user workflows |
| CI/CD Engineer | Git, PR, release, deployment, and environment workflows |
| QA | Tests, regression checks, bug reports, and quality gates |
| Beta Tester | User-perspective exploration and scenario reports |

One task has one accountable owner. Collaborators may contribute, but the owner
closes the record.

## 5. Work Selection

When a request arrives:

1. Check whether an existing `TASK`, bug, or test case already covers it.
2. If yes, continue that record instead of creating a duplicate.
3. If it is inside the current cycle, work under that cycle.
4. If it is a direct user request outside the current cycle, keep it small and
   record it.
5. If the request changes architecture, workflow, public release, secrets, data,
   or irreversible state, escalate before mutation.

Allowed task states:

- `대기`
- `진행 중`
- `완료`
- `보류`

## 5.4 Project Management Decomposition

Non-trivial work uses this hierarchy:

```text
project -> taskset -> task -> unit
```

The backlog/board is a routing index, not the full task specification. Keep
only metadata there: ids, status, priority, owner, model tier, difficulty,
task_set_id, project_id, and evidence pointers. Put detailed work instructions
in linked project, taskset, task, or unit spec files.

A worker-ready unit must include:

1. context and source links;
2. exact target files or components;
3. in-scope and out-of-scope boundaries;
4. step-by-step execution notes when needed;
5. acceptance criteria;
6. verification commands;
7. handoff/report format.

Planning, research synthesis, architecture, risk classification, and
decomposition belong to higher-capability planner roles/models. Routine
implementation units should be assigned to lower-cost worker models when the
unit is precise, reversible, and verifiable. Escalate the model tier when the
unit is ambiguous, high-risk, cross-cutting, security-sensitive, or repeatedly
failing.

Implementation agents execute the smallest registered unit. They must not
expand into reprioritization, adjacent tasksets, or new planning unless a
planner-approved record says so.

## 5.5 Task Set Dispatch

Task sets are the default unit for parallel panes. A "pane" may be a terminal
pane, a separate terminal tab, or another worktree-backed agent session. The
important boundary is not the UI container; it is the tuple
`task_set_id + task_id + claim_id + worktree_path + branch + pane_id`.

When the Owner says `taskset-xxx 진행해줘`, `taskset-xxx 시작`, or an equivalent
request:

1. Resolve the alias and inspect the lane:
   `python scripts/taskset_dispatcher.py plan <taskset-alias> --json`.
2. Claim the task set before editing:
   `python scripts/taskset_dispatcher.py start <taskset-alias> --json`.
3. Work only in the returned `worktree_path` and `branch`.
4. Keep one active claim per `task_set_id` unless the claim explicitly records
   `allow_parallel_task_set: true` and the reason is documented.
5. Keep the claim and live pointer updated with `phase`, `progress_pct`,
   `step_index`, `step_total`, and `status_text`.
6. Before handoff or closure, run:
   `python scripts/taskset_work_gate.py --check` and
   `python scripts/parallel_worktree_gate.py --check`.

Use human-friendly task-set display names in reports, for example
`Quality Sentinel`, `Progress Scout`, `Console Operator`, or `Repo Custodian`.
System identifiers remain stable machine fields; display names help humans read
the board like RPG-style party/status labels.

## 6. Reversibility Gate

Use reversibility and blast radius to decide whether to act or ask.

| Level | Rule |
|-------|------|
| R1 | Reversible and in scope: act, verify, record |
| R2 | Reversible but slightly ambiguous or cross-scope: act, flag assumptions and undo path |
| R3 | Irreversible, destructive, external, secret-bearing, production-data, or high-risk: ask Owner |

### Autonomous Delivery Lane

Branch, commit, PR, and merge work should be automated by default when the
repository has deterministic gates and the change is not critical.

| Step | Default | Required evidence |
|------|---------|-------------------|
| Branch | Agent may create a scoped task branch | task id, scope, rollback path |
| Commit | Agent may commit scoped changes | focused check result and changed-file summary |
| PR | Agent may open/update PR | review summary, test evidence, risk label |
| Merge | Agent may merge when configured gates pass | green checks, no critical findings, merge log |

Owner approval is not required for routine branch/commit/PR/merge execution
when all of these are true:

1. the change is scoped to an approved task or direct user request;
2. no secret, production data, billing, legal, destructive, or public release
   boundary is crossed;
3. required checks pass or a documented waiver is approved by the accountable
   non-Owner role named in the task;
4. the merge target and branch protection rules permit automation;
5. rollback is possible through normal VCS history.

Examples that require Owner approval:

- file or directory deletion
- recursive move or delete
- force push, rollback, hard reset, or checkout that discards work
- production deployment or external publication
- secret access or rotation
- production data writes
- disabling safety checks
- critical security, legal, billing, data-loss, or irreversible release changes

If the execution platform asks for permission, do not bypass it. Present the
smallest safe command scope.

## 7. File Edits

1. Check the worktree before edits.
2. Preserve user changes.
3. Edit only files tied to the current task.
4. Keep generated, local, runtime, and secret files out of public release.
5. Use structured parsers or existing scripts where available.
6. If behavior changes, update the relevant docs and verification records.
7. If a rule is repeated by the Owner, prefer a function/API, script, hook, gate,
   or test over another prose-only instruction.

## 8. Records

New task records should include:

```yaml
---
type: task
id: TASK-NNN
status: 대기
owner: Lead Engineer
assignees: [Lead Engineer]
priority: Medium
difficulty: 중
est_hours: 1
est_tokens: 10000
tags: [automation]
trigger_meeting: 자가발생
audit_log: AUDIT-YYYY-MM-DD-NNN
created: YYYY-MM-DD
created_at: YYYY-MM-DDTHH:MM:SS+09:00
---
```

Completion records must state:

- original request
- actual work performed
- result
- changed files
- verification commands and outcomes
- remaining issues or handoff notes
- whether `agents/project/NEXT-SESSION-POINTER.yml` was updated or did not need
  an update
- whether repeated criticism required Compound capture

## 8.5 Measured Improvement Loop

Use this loop for process, prompt, workflow, quality, and agent-behavior
improvements:

1. Evaluate: define a measurable score, golden set, failure cases, and edge
   cases before changing behavior.
2. Propose: suggest one change that should improve the score.
3. Verify: rerun the same evaluation and record whether the score improved.
4. Merge: keep the change only when it is valuable, meaningful, and safe.

Keep one variable per verified change. If multiple variants are useful, run
them as separate proposals or parallel experiments and keep only the verified
winners. The problem-posing/proposer role and grader role should be separate
when stakes justify the overhead.

Owner defines what "better" means and owns final merge decisions. Agents may
recommend criteria and present evidence, but they do not redefine success to fit
their own proposal.

## 8.6 Repeated Request API And Compound Capture

Repeated Owner requests are signal, not noise. If the same request, criticism,
or failure class appears twice:

1. create or propose a Repeated Request API: function/API, script, hook, gate,
   checklist item, template, or explicit task that prevents manual repetition;
2. add or update tests when the behavior can be checked automatically;
3. record the recurrence in `agents/lead_engineer/compound_log.md` when it is a
   repeated mistake, drift, or governance failure;
4. close the Compound item with an executable prevention step when feasible.

Long documents are not sufficient prevention. A rule is considered durable only
when a future agent can find it quickly from the pointer and, where practical,
an executable gate can fail when it is violated.

## 9. Reporting

Final task reports use the human-centered, machine-readable Executive BRIEF
format. Keep it concise, visually scannable, and action-oriented.

### Owner-Facing Language Contract

- 사용자와 직접 대화할 때는 별도 요청이 없는 한 무조건 한국어로 답한다.
- Owner-facing 보고, 상태 업데이트, 질문, 계획, 검토 요약은 한국어가 기본값이다.
- 에이전트 간 메시지, 로그, machine-readable frontmatter, 코드 주석, 테스트명,
  evidence record는 필요하면 영어를 사용할 수 있다.
- 사용자가 영어로 말해도 "영어로 답해줘"처럼 명시 요청하지 않으면 한국어로 답한다.
- 이 규칙은 짧은 진행 업데이트와 최종 보고 모두에 적용한다.

```yaml
---
type: brief
id: BRIEF-YYYY-MM-DD-NNN
audience: owner|ceo|agent-team
signal: pass|watch|block
score: 0-100
priority: Critical|High|Medium|Low
tags: [release, automation]
actions: [approve, review, no-action]
evidence:
  - path/or/url
---
```

```text
Bottom Line: <one-line outcome and decision>.

## Signal
| Item | State | Evidence |
|------|-------|----------|
| Work | pass/watch/block + score | <evidence> |

## Insight
1. <short interpretation>

## Decision
1. <decision needed, or "없음">

## Next
| Step | Owner | Trigger |
|------|-------|---------|
| <action> | <role> | <condition> |
```

Use `pass`, `watch`, and `block` with `score: 0-100` for state. Do not use color labels or emoji as machine values.

## 10. Time

Use these commands for timestamps:

```powershell
python scripts/now.py
python scripts/now.py --utc
python scripts/now.py --date
```

If Python is unavailable, mark time as `unknown` rather than guessing.

## 11. Git

Default flow is automated unless a critical boundary is detected:

1. Create a task branch.
2. Make small scoped commits.
3. Run focused checks.
4. Open or update a PR.
5. Dispatch review agents or CI checks.
6. Merge through the configured gate when checks pass.
7. Record branch, commit, PR, merge, and evidence links.

Do not push directly to `main` unless this repository explicitly allows it.
Do not ask Owner for routine branch/commit/PR/merge approval when the
Autonomous Delivery Lane conditions are met.

## 11.5 Release Council

Routine patch/minor releases may be decided by an agent release council instead
of Owner approval when all release gates pass and no critical boundary exists.

Required council roles:

1. Lead Engineer: scope and version readiness.
2. QA: validation evidence.
3. Independent Auditor: risk and evidence integrity.
4. Doc Steward: changelog, reports, and handoff quality.

Owner approval is required only for critical releases:

1. major version or breaking change;
2. secret, credential, production data, billing, or legal impact;
3. failed, missing, or waived critical gate;
4. external publication to a new or untrusted target;
5. destructive rollback, force push, or irreversible operation;
6. explicit user or organization policy requiring Owner sign-off.

## 12. Agent Runtime Sync

This repository may consume reusable automation through `agent_runtime`.
Host projects pin the upstream in `agent_runtime.yml` and update through:

```powershell
agent_runtime update-plan --root . --check
agent_runtime update --root . --check
agent_runtime update --root . --diff
agent_runtime update --root . --apply
agent_runtime lock --root . --write
```

The update path must preserve host edits and only apply managed template files.

## 13. Validation

Before closure, run the narrowest useful checks first, then the repository gate:

```powershell
python scripts/check_agent_docs.py
```

If a check cannot run, report exactly why and what remains unverified.

## 14. Downstream Bug Intake

Host projects that consume this runtime report bugs through a structured evidence
process. Maintainers should respond to issues labelled `downstream-report`.

### What a good bug report includes

Every downstream bug report must follow the 6W1H structure:

| Field | Content |
|-------|---------|
| Who | Component / caller that triggered the error |
| What | Error type and message (verbatim) |
| When | agent_runtime version, upgrade path |
| Where | File:line in agent_runtime source |
| Why | Root cause analysis (design gap / missing doc / regression) |
| How | Reproduction steps and minimal code snippet |

### Intake checklist for maintainers

1. Confirm reproduction in a clean install.
2. Apply labels: `bug` + severity (`critical`/`high`/`medium`/`low`) + `downstream-report`.
3. Link to the host EVIDENCE file if provided.
4. Prioritize `high` and above within one release cycle.
5. Add a CHANGELOG entry and update `MIGRATION-COMPAT-MAP.example.yml` when
   fixing a public API change (function signature rename, removed export, etc.).

### Known standing issues from downstream

- **Windows cp949 encoding**: `sync --diff` fails on Windows cp949 consoles
  when template files contain non-ASCII characters. Workaround: set
  `PYTHONIOENCODING=utf-8`. Tracked in issue #6.
- **`build_sync_plan` signature**: the function internally calls `load_config`;
  callers must NOT pass an `AgentRuntimeConfig` as `template_root`. Tracked
  in issue #5. Add a type guard or clear error message.
