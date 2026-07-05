---
type: design_spec
id: SPEC-decision-inbox-v1
topic: Decision Inbox v1 — turn the cockpit attention inbox into a legible, operable decision loop
audience: maintainers
status: draft
generated_at: 2026-06-27
references:
  - docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md
  - reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md
---

# Decision Inbox v1 — Design Spec

## Bottom Line (KO)
홈 코크핏의 attention 인박스(이미 존재)를 비전공자가 **읽고(이해) → 응답(의견·결정) → 결과를 보는(사이클)** 표면으로 격상한다. 신규 화면 없이 기존 `renderInboxDetailItem`/`/api/inbox`/`.ui_outbox` 패턴에 **추가만** 한다. 첫 이터레이션은 액션 3종(확인·의견·보류)만, 전부 proposal-only(파괴적 변경 없음).

## Problem
The console has 28+ views but no surface where a non-expert can actually *make a decision and see work move*. The home cockpit already derives a 6-group "what needs me now" attention inbox (`scripts/attention_inbox.py` → `/api/inbox`), rendered by `renderCockpit`/`openInboxDetail`/`renderInboxDetailItem` in `ui_console_assets.py`. But it is **read-only** and its phrasing is machine-ish (`status=blocked`, `no update 7d`, `approval_required`). A first-time operator can neither fully *understand* an item nor *respond* to it.

Council (4 diverse lenses) converged: build the decision loop on this inbox, but **legibility-first** and **scoped to a minimal real loop** (not 5 actions). Owner's own ordering: 파악(understand) → 의견(opine) → 전진(advance) → 평가(evaluate) → 사이클(loop).

## Goals (iteration 1)
1. **Legibility**: each inbox item reads as one plain-language sentence ("이 작업은 당신의 승인을 기다립니다 · 7일째 업데이트 없음"), not a row of terse system chips. Raw ID is shown but de-emphasised.
2. **Respond**: each item offers a minimal, honest, reversible response set — **확인/승인(acknowledge), 의견/질문(comment), 보류(hold)** — each writing an auditable proposal only.
3. **Loop visibility**: a compact "최근 결정(Decided)" log shows the operator their own responses accumulating, so the cycle is visible.

## Non-Goals (deferred to later iterations)
- Reprioritize / Block / Request-changes routing, and any **runtime executor** that consumes the proposals (proposals are recorded + surfaced; no auto-mutation this iteration — avoids "decision theater" by being honest in copy: "기록됨").
- **v2:** wire `decision.comment` → `task.comment` (real agent message inbox) for task-typed items; build the executor that consumes `.ui_outbox/decisions/`.
- New nav surfaces, task-detail "operate" panel, meeting-outcome→task binding.
- Any new image/illustration generation beyond reusing the existing empty-state.

## Design

### A. Data (no change to source)
`/api/inbox` already returns `{groups, counts, total}`; each item is `{group, id, title, why, age_days, severity, action}`. We add NO fields to `attention_inbox.py`. A `decided` set is tracked client-side for optimistic removal; the durable record is the proposal file.

### B. Legibility layer (front-end only)
- Extend `localizedInboxWhy`/`localizedInboxAction` (or add `inboxPlainSentence(item)`) to compose ONE sentence per item from `why`+`age`+`action`, in KO/EN via existing i18n (`i18nStrings`). No raw literals.
- `renderInboxDetailItem` (ui_console_assets.py:7280) renders: plain sentence (h3-level), a muted meta line (id · stage chip with color+label · "N분/일 전"), then the response bar.
- Stage chip uses existing status tokens (color + text label, never color-only — DESIGN.md rule).

### C. Respond bar (front-end + one command)
- Three buttons under each detail item: **확인 (acknowledge)**, **의견 (comment — reveals inline `<textarea>`)**, **보류 (hold)**. Keyboard accessible; tokens only.
- New JS `queueDecision(action, item, reason)` modeled on `queuePlanningDecision` (ui_console_assets.py:10792). NOTE: mirror that function's payload-wrapping shape exactly (it double-wraps as `{type, payload:{type, payload:{...}}}`) so the client stays consistent with existing command submission.
- **All three actions are uniform `decision.*` proposal types in v1** (red-team F2): `decision.acknowledge`, `decision.comment`, `decision.hold`. We do NOT branch to `task.comment` in v1 — `_comment_task` requires the target to be an on-disk task file, but inbox items include non-task ids (e.g. `runtime_anomalies` cross-host claims), so the branch would silently fail. Wiring `decision.comment` → real agent routing (`task.comment`) for task-typed items is an explicit **v2** promotion.
- Optimistic UI: on success, mark item `decided`, animate row slide-up+fade (150ms ease-out, reuse existing `prefers-reduced-motion` handling at ui_console_assets.py ~2715/6131/6395/6690), decrement the group count, append to the Decided log.

### D. Back end (additive, proposal-only)
- `ui_commands.py`: add `_decision_command()`. **Validation** structure is modeled on `_planning_decision_command` (lines 1015-1051) + the shared `_payload_errors` helper (line 413): validate `target` (item id) + `action`; `reason` optional for `acknowledge`, required for `hold` and `comment`. **Write path** is the `.ui_outbox/<kind>/` UI-proposal convention used by `_meeting_command`/`_taskset_lifecycle_command` (NOT planning's `agents/planning/decisions/` path — red-team F1): write ONE proposal to `.ui_outbox/decisions/<DECISION-id>.json` with `{id, target, group, action, reason, decided_by, decided_at, canonical_mutation_allowed: false}`. Confirm the exact outbox-queue helper name by reading `_meeting_command` before coding; reuse it verbatim.
- `ui_commands.py`: register the three new types in the command type set/dispatch (the same if-elif chain `submit_command` uses).
- `ui_console.py`: no new route — `POST /api/commands` (line 257) already forwards every type to `submit_command`.

### E. Decided log (front-end)
- A compact list under the inbox hero (or in the detail drawer footer) reading the session's optimistic decisions; on reload it can hydrate from a read-only `GET` of recent `.ui_outbox/decisions/` summaries (optional — if cheap; else session-only for v1, clearly labeled).

## Testing
- `tests/test_ui_console*.py`: POST `/api/commands` `{type:"decision.acknowledge", payload:{target:"TASK-AR-xxx", action:"acknowledge"}}` → returns queued status and writes exactly one file under `.ui_outbox/decisions/`. `decision.hold`/`decision.comment` without `reason` → `{errors:[...]}`. Missing `target` → errors. Assert the proposal record carries `canonical_mutation_allowed: false`.
- Front-end: extend microinteraction/console tests to assert the response bar renders for a detail item and that a `decided` item is removed optimistically.
- Gates: `python scripts/design_system_gate.py --all-ui` (no raw hex/px literals). i18n: there is NO standalone i18n gate script (red-team I3) — enforcement is manual: every new visible string MUST be added to BOTH `ko` and `en` keys of `i18nStrings` (ui_console_assets.py ~6970) and read via `t()`; before commit, grep new strings to confirm both-locale coverage (and run any existing i18n test under tests/ if present). nav-budget unchanged.

## Risks & Mitigations
1. **Scope creep into executors** → explicitly non-goal; proposals only; honest copy.
2. **Design-system gate rejects styling** → use `--space-*/--radius-*/--success/--warning` tokens; run `--all-ui` before commit.
3. **Stale inbox item (ghost)** → show "N분/일 전" staleness; proposal records intent, no mutation, so acting on a ghost is harmless and auditable.
4. **i18n literal gate** → every new visible string added to both KO/EN `i18nStrings`.

## Rollback
All changes are additive; reverting the diff restores the read-only inbox. No data migration.
