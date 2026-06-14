# Product Maturity & UI — Verification Case Catalog

A broad catalog of verification cases (typical / edge / adversarial / ambiguous /
access-controlled, per `agents/project/EVAL-POLICY.yml`) used to measure the
dimensions in `agents/project/PRODUCT-MATURITY-UI-RUBRIC.yml`. Each case has a
stable id `VC-<area>-<n>`, a type, the scenario, and the expected behavior. Cases
marked **[gap]** have no current automated coverage and become the verification
targets for the uplift tasks (TASK-AR-546..555).

Legend — type: `T`=typical, `E`=edge, `A`=adversarial, `M`=ambiguous, `X`=access-controlled.

## 1. Deadlock guardrails — claim_reaper

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-REAP-1 | T | active claim, lease `expires_at` in the future | left as `live`, never touched |
| VC-REAP-2 | T | active claim, lease expired beyond grace, non-orchestrator | reaped → `status=expired`, `recovered_from_status` set |
| VC-REAP-3 | E | lease expired exactly at `now` (boundary) | within-grace → `live` (not reaped) |
| VC-REAP-4 | E | lease expired at `now - grace` exactly | boundary inclusive → still `live` (`<=` deadline+grace) |
| VC-REAP-5 | E | `expires_at` present but `lease.expires_at` older | uses the furthest-future deadline; not falsely reaped |
| VC-REAP-6 | E | claim with no `expires_at` and no `lease` | skipped `no-lease-info`, never reaped |
| VC-REAP-7 | E | claim with malformed `expires_at` string | unparseable → treated as no-lease-info, skipped |
| VC-REAP-8 | A | orchestrator/release-orchestrator role with expired lease | skipped `orchestrator-claim` |
| VC-REAP-9 | A | `mode=orchestrator` or `worker_scope=orchestrator` | skipped (orchestrator detection beyond role) |
| VC-REAP-10 | E | already-`expired` claim re-swept | idempotent: not reaped again |
| VC-REAP-11 | E | terminal `released`/`completed`/`done` claim, expired | skipped `not-active` |
| VC-REAP-12 | E | mixed batch (live + 2 dead + orchestrator + terminal) | all processed; only the 2 dead reaped; others categorized |
| VC-REAP-13 | A | long-running LIVE worker that keeps heartbeating past 1h | never reaped (deadline keeps advancing) |
| VC-REAP-14 | E | dry-run on a dead claim | reported in `would_reap`; file untouched; no counters written |
| VC-REAP-15 | X | reaper run by a non-orchestrator session via SessionStart hook | recovers provably-dead only; honors `AGENT_RUNTIME_REAPER_AUTO_APPLY=0` |
| VC-REAP-16 | A | claim file becomes unreadable/corrupt mid-sweep | skipped silently; sweep completes the rest |
| VC-REAP-17 | E | `--grace-seconds 0` | reaps immediately past raw expiry (documented aggressive mode) |
| VC-REAP-18 | E | reaped status is in none of active/done sets | unit re-classifies to `pending` (re-dispatchable) **[covered: test]** |
| VC-REAP-19 | A | two reaper processes race on the same claim file | atomic write; no partial/corrupt JSON |
| VC-REAP-20 | M | claim active but `expires_at` missing while `lease.heartbeat_at` recent | ambiguous → skipped (cannot prove death) |

## 2. Deadlock guardrails — goal_supervisor

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-SUP-1 | T | last loop_stop reason = `max_iterations`, under cap | action `resume`; bumps per-goal counter |
| VC-SUP-2 | T | loop still running (no terminal event) | action `none` ("still running") |
| VC-SUP-3 | E | `loop_halt_max_failures` event | action `halt`; reason_code `max_failures`; never resumed |
| VC-SUP-4 | A | reason = emergency/orchestrator stop | not resumable; `halt` |
| VC-SUP-5 | E | restart_count == max_restarts | action `cap`; `restart_cap_reached` recorded |
| VC-SUP-6 | E | restart_count == max_restarts - 1 | last allowed resume |
| VC-SUP-7 | E | no agent_loop event file for today | action `none` |
| VC-SUP-8 | E | loop_start without a goal | action `none` (not a goal run) |
| VC-SUP-9 | E | multiple loop_start in one day | uses the most recent goal run |
| VC-SUP-10 | A | dry-run with resumable stop | decision computed; runner NOT invoked; no writes |
| VC-SUP-11 | E | resume command includes `--checkpoint-dirty` and the goal text | next round self-heals a dirty worktree |
| VC-SUP-12 | M | reason string unmapped/unknown | classified `unknown` → not resumable (conservative) |
| VC-SUP-13 | E | corrupt line in event log | skipped; latest valid terminal used |
| VC-SUP-14 | A | resume runner returns non-zero | `resumed` still recorded with rc; loop not crashed |

## 3. Deadlock guardrails — stop_events + agent_loop checkpoint

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-STOP-1 | T | record a recoverable stop | event appended; class `recoverable`; counters bumped |
| VC-STOP-2 | T | record an intentional stop | class `intentional` |
| VC-STOP-3 | E | explicit class override (`dirty_worktree_main`) | intentional even if base recoverable |
| VC-STOP-4 | E | counters file missing/corrupt | tolerated; treated as empty |
| VC-STOP-5 | E | `summary` aggregates by_class/by_action/by_reason/goal_restarts | tuning data correct |
| VC-CKPT-1 | T | dirty worktree on a feature branch, `--checkpoint-dirty` | WIP committed; loop continues |
| VC-CKPT-2 | A | dirty worktree on `main`/`master` | never auto-commits; records `dirty_worktree_main` |
| VC-CKPT-3 | E | detached HEAD, dirty | treated as protected; not auto-committed |
| VC-CKPT-4 | A | commit hook fails on checkpoint | checkpoint fails honestly; loop stops (no `--no-verify`) |
| VC-CKPT-5 | E | clean worktree with `--checkpoint-dirty` | no-op |
| VC-CKPT-6 | E | `--checkpoint-dirty` off (default) | existing dirty-stop behavior preserved **[covered: regression]** |

## 4. Claims / wave / taskset lifecycle

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-WAVE-1 | T | dispatch issues only the current wave | next wave waits for full cycle |
| VC-WAVE-2 | E | all current-wave tasks have active claims | `state=in_flight`; waits |
| VC-WAVE-3 | E | footprint overlap within a wave | conflicting unit deferred to a later wave |
| VC-WAVE-4 | A | two panes claim the same task_set_id without allow flag | second refused |
| VC-WAVE-5 | E | reaped claim's task re-dispatched | reuses existing worktree/branch; resumes work |
| VC-CLAIM-1 | A | claim worktree points at main checkout | refused (`must not point at main`) |
| VC-CLAIM-2 | A | release with verifier == worker identity | refused (cross-verification) |
| VC-CLAIM-3 | A | release without evidence ref (default) | refused unless `--allow-missing-evidence` |
| VC-CLAIM-4 | X | claim creation under drifted plan assumptions | refused unless `--skip-plan-check` (loud) |
| VC-CLAIM-5 | E | claim file untracked by git | parallel_worktree_gate blocks (commit-immediately) |

## 5. Governance gates

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-GOV-1 | T | owner_governance_gate on clean tree | exit 0 (approve) |
| VC-GOV-2 | E | new review not in reviews/INDEX.md | evidence_index_generator flags missing-review |
| VC-GOV-3 | E | new task without WORK-ITEM-CLASSIFICATION record | work_item_classifier flags missing-records |
| VC-GOV-4 | A | task frontmatter missing required field | work_schema_gate fails for that item |
| VC-GOV-5 | A | owner doc lacks a required section | owner_doc_format_gate fails |
| VC-GOV-6 | E | dependency cycle among units | dependency_cycle_gate fails |
| VC-GOV-7 | X | rbac-restricted write path | rbac_write_gate blocks |
| VC-GOV-8 | A | Stop hook with failing governance | emits `decision: block` (no false approve) |

## 6. Release / sync / update

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-REL-1 | T | publish_check on a complete tree | required files present |
| VC-REL-2 | E | version mismatch across pyproject/refs | preflight fails |
| VC-REL-3 | A | tag smoke install in a clean venv | importable; entry points work |
| VC-REL-4 | E | upstream tag newer than pinned ref | update-notify prints one notice (non-blocking) |
| VC-REL-5 | A | offline update check | exits 0 silently (cached) |
| VC-SYNC-1 | E | template file drifts from root copy | sync plan reports the diff/conflict |
| VC-SYNC-2 | A | sync over a user-modified file | conflict surfaced, not silently overwritten |

## 7. UI — board / navigation / search

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-UIB-1 | T | render board with N tasks across columns | columns/counts correct |
| VC-UIB-2 | E | board with 0 tasks | empty-state shown, no crash |
| VC-UIB-3 | A | task title with HTML/script payload | escaped; no injection (XSS-safe render) |
| VC-UIB-4 | E | drag-and-drop reorder (keyboard Ctrl+D path) | order persists; aria-live announces **[gap: no e2e]** |
| VC-UIB-5 | T | global search Ctrl+P across entities | matches tasks/tasksets/messages/events |
| VC-UIB-6 | E | search with empty/whitespace query | no results panel error |
| VC-UIB-7 | A | search query with regex/special chars | treated literally; no ReDoS |
| VC-UIB-8 | M | ambiguous search term matching many types | grouped, ranked results |
| VC-UIB-9 | E | navigate views then browser back/forward | **[gap]** no history routing — document/fix |

## 8. UI — forms / validation / commands

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-UIF-1 | T | submit a valid task-create form | success feedback |
| VC-UIF-2 | E | required field empty | inline error tied to the field **[gap: global-only]** |
| VC-UIF-3 | A | oversized/invalid input (10k char title) | rejected gracefully; no overflow |
| VC-UIF-4 | E | destructive action (delete) then undo | undo restores **[gap: no undo]** |
| VC-UIF-5 | A | proposal-only command boundary | UI cannot mutate SSoT directly; emits proposal |
| VC-UIF-6 | E | concurrent edit of the same entity | last-write surfaced; no silent clobber |
| VC-UIF-7 | M | partially-filled optional metadata | saved without forcing all fields |

## 9. UI — i18n / accessibility / theming

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-UII-1 | T | toggle ko/en | chrome strings switch; persists |
| VC-UII-2 | E | missing i18n key | falls back to key/default, no blank |
| VC-UII-3 | E | error message in non-en locale | **[gap]** currently hardcoded en |
| VC-UII-4 | E | date/number rendering by locale | **[gap]** ISO/raw only |
| VC-UIA-1 | T | tab through sidebar nav | focus order logical; aria-selected correct |
| VC-UIA-2 | E | skip-to-content link | **[gap]** add visible skip link |
| VC-UIA-3 | E | open modal, focus trap + return focus | **[gap]** no trap |
| VC-UIA-4 | A | screen-reader reads evidence list | **[gap]** div-not-table semantics |
| VC-UIA-5 | E | color contrast of tokens (WCAG AA) | **[gap]** audit ratios |
| VC-UIA-6 | T | prefers-reduced-motion respected | animations disabled (dual-gate) **[covered]** |
| VC-UIT-1 | T | dark/light theme no-flash bootstrap | correct theme before first paint |
| VC-UIT-2 | E | label/confetti colors use tokens, never raw hex | injection-safe **[covered]** |

## 10. UI — export / import / notifications / responsive

| id | type | scenario | expected |
| --- | --- | --- | --- |
| VC-UIE-1 | T | CSV export → import round-trip | lossless **[covered]** |
| VC-UIE-2 | A | CSV cell starting with `=`/`+`/`-`/`@` | formula-injection neutralized **[covered]** |
| VC-UIE-3 | E | import with duplicate rows | duplicates detected, not double-created |
| VC-UIE-4 | E | import malformed CSV | rejected with a clear error |
| VC-UIN-1 | T | @mention notification + reaction (whitelisted) | rendered; reaction within allowed set **[covered]** |
| VC-UIN-2 | A | reaction value outside the whitelist | rejected |
| VC-UIN-3 | E | notification when polling delayed | **[gap]** latency up to poll interval (SSE candidate) |
| VC-UIR-1 | E | viewport 375px (phone) | **[gap]** layout breaks — responsive task |
| VC-UIR-2 | E | viewport 768px (tablet) | **[gap]** sidebar collapse to hamburger |
| VC-UIR-3 | A | very long content in a narrow column | wraps/truncates; no horizontal scroll trap |

## Coverage rollup

- **Covered today (automated):** reaper/supervisor/stop/checkpoint core (Sections 1-3 mostly),
  CSV export/import + injection, microinteraction motion-gating, reaction whitelist, token-safe colors.
- **Gaps → uplift tasks:** UI e2e (VC-UIB-4/9, VC-UIF-*), a11y (VC-UIA-2..5), i18n depth
  (VC-UII-3/4), responsive (VC-UIR-*), real-time/SSE (VC-UIN-3), reaper concurrency
  (VC-REAP-13/19), observability export, multi-host claim safety, release automation.

See `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` for the scored
assessment and `reviews/MEETING-2026-06-14-product-maturity-uplift-taskset-registration.md`
for the task registration mapping these gaps to TASK-AR-546..555.
