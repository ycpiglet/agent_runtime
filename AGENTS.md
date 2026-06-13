# AGENTS.md

This repository-level file is the first human-facing behavior contract for
agents working directly in this checkout. The reusable host-project template
continues to live at `src/agent_runtime/templates/project/AGENTS.md`.

## Owner-Facing Language Contract

- 사용자와 직접 대화할 때는 별도 요청이 없는 한 무조건 한국어로 답한다.
- 사용자가 영어로 말해도 "영어로 답해줘"처럼 명시 요청하지 않으면 한국어로 답한다.
- 진행 업데이트, 상태 보고, 질문, 계획, 검토 요약, 최종 보고 모두 한국어가 기본값이다.
- 에이전트 간 메시지, 로그, machine-readable frontmatter, 코드 주석, 테스트명, evidence record는 필요하면 영어를 사용할 수 있다.

## Working Rules

- Keep task work scoped to the active request and existing task records.
- Verify before claiming completion.
- Preserve user changes and do not revert unrelated work.
- For full shared protocol details, mirror updates into
  `src/agent_runtime/templates/project/AGENTS.md` when the rule should apply to
  generated host projects.

## Live Checkout Layout vs Host Scaffold (Two-Layer Structure)

- This checkout intentionally keeps `agents/` flat with four lanes:
  `lead_engineer` (task records), `planning`, `project` (product/PM overlay),
  `runtime` (claims, pane events, session baselines). Roles such as `qa`,
  `doc-steward`, `independent-auditor`, `scribe`, `ceo`, `uiux` exist here as
  claim/gate **metadata** (`agent_role` in
  `agents/runtime/task_claims/*.json`, `required_roles` in
  `agents/project/MULTIPANE-PROCESS-POLICY.yml`), not as directories.
- The full per-role scaffold (role directories plus `agents/roles.yml`) is
  product surface for generated host projects and lives only under
  `src/agent_runtime/templates/project/agents/`. Do not recreate per-role
  directories in this checkout, and do not fork `roles.yml` into the live
  tree: `agents/project/PROJECT-CONTEXT.yml` lists it under
  `do_not_customize_for_project`, and a live copy would create a second
  source of truth.
- `doctor.py`, `agent_orchestrator.py`, and `agents/messages/**` expectations
  are host-runtime checks for installed projects, not gaps in this checkout.
- Decision record:
  `reviews/REVIEW-2026-06-12-agent-runtime-live-structure-two-layer-decision.md`.

## Project Management Decomposition Contract

- Non-trivial work must be decomposed as
  `initiative -> taskset -> task -> unit` before implementation begins. Use
  `project` only for the host/repository/product lane such as `agent_runtime`;
  use `initiative` for the taskset parent grouping the Owner wants planned or
  tracked.
- The backlog/board carries routing metadata; detailed execution context
  belongs in linked initiative, taskset, task, or unit spec files.
- A task is not worker-ready until a lower-cost implementation model can execute
  it from the record alone: context, target files, exact scope, out-of-scope
  boundaries, acceptance criteria, verification commands, and handoff format
  must be explicit.
- Human-facing numbers are assigned by the work-item classifier, not manually
  by planners. Use generated `Initiative N -> Taskset N.N -> Task N.N.N ->
  Unit N.N.N.N` labels for recognition; keep UUID/timestamp-backed file IDs for
  collision resistance.
- Milestone, horizon, team, owner, role, priority, and phase are metadata axes,
  not extra hierarchy levels. Routine recurring work and spike research may use
  their own record type instead of being forced into the goal tree.
- Planning or design discussion must be recorded in `reviews/` before closeout;
  do not leave hierarchy, numbering, or workflow decisions as chat-only state.
- Planning, research synthesis, architecture, risk classification, and task
  decomposition are assigned to higher-capability planner roles/models. Routine
  implementation units default to lower-cost worker models unless the unit is
  ambiguous, high-risk, cross-cutting, security-sensitive, or repeatedly failing.
- Agents should execute the smallest registered unit they can complete and
  verify. Do not let implementation agents expand scope into planning,
  reprioritization, or adjacent taskset work without a new planner-approved
  record.

## Standard Work Lifecycle (W0~W6) — Default For All Work

Owner rule: "이번 건만이 아니라 앞으로 모든 작업들이 그렇게 되길 원한다" — the
deferred-revalidation discipline (T0 snapshot at registration, T2 check at
dispatch) and the W0~W6 order below are the DEFAULT for every taskset, not an
opt-in. Decision record:
`reviews/MEETING-2026-06-12-parallel-work-lifecycle-rules.md`. No step may run
out of order.

- W0 Visibility (session start): run `python scripts/work.py status` to see
  active claims, git worktrees, and unmerged agent-branch divergence in one
  read-only view. Never enter a problem that already has an active claim.
- W1 Registration: search existing tasks/claims first (no duplicates), then
  register through `python scripts/work.py new --input <json>`. Registration
  automatically records the plan-assumption snapshot (T0) via
  `scripts/plan_assumption_gate.py` — anchors default to the design record,
  the registration/dispatch flow scripts (`scripts/work.py`,
  `scripts/task_claim_dispatcher.py`), and every `scripts/*.py` the taskset's
  tasks/units declare in `target_files`. `--no-plan-snapshot` is a discouraged
  opt-out; if used, record manually before dispatch.
- W2 Claim (claim-first): `python scripts/task_claim_dispatcher.py create`
  re-verifies the recorded assumptions (T2) BEFORE writing the claim; drift
  refuses the claim until a replan review re-records anchors (T3).
  `--skip-plan-check` is a loud transitional escape. The claim is created in
  the main checkout BEFORE any worktree work; footprint conflicts and
  duplicate task/taskset claims block. Never create a worktree without a
  claim.
- W3 Implement: work only inside the claimed worktree/branch; keep
  heartbeat/pane events current; no shared-SSoT writes (board, STATUS, INDEX,
  registries are orchestrator-only); adjacent problems found mid-work go to
  intake registration, never direct fixes.
- W4 Verify: W4a — the worker runs the recorded verification commands and
  writes the self-verification report; W4b — an INDEPENDENT agent instance
  verifies and releases the claim (`release` enforces verifier != worker and
  a verification evidence ref).
- W5 Cleanup: serial merge-queue integration, board/index regeneration, then
  worktree removal plus merged-branch cleanup — no zombie worktrees, no
  standing ahead(N).
- W6 Closeout: `work close` plus retro at wave boundaries; the next session
  starts again at W0.

T0/T2 wiring: T0 = snapshot at registration (`work.py new`); T1 =
informational `plan_assumption_gate --check` after merges; T2 = enforced at
dispatch (claim creation refuses on drift); T3 = the replan review re-runs
`record` to re-anchor the plan.
