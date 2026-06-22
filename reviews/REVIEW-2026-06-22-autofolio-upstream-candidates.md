---
type: review
title: autofolio → agent_runtime upstream-candidate assessment
date: 2026-06-22
status: assessed
signal: pass
related: [issue #128, issue #185, PR #187, docs/AGENT_RUNTIME_INTEGRATION.md]
---

# autofolio → agent_runtime upstream-candidate assessment

autofolio consumes agent_runtime pinned at **v0.3.1** (3-layer model: framework ①
/ host-overlay ② / seam ③). Established upstreaming precedent: **#185 → #187**
generalized the gates so autofolio dropped two forks in v0.3.1. This review is the
"check" half of the Owner request ("반영할만한지 체크 + 병합"); each code merge is
routed as a scoped follow-up task per the evidence→proposal contract
(`agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`).

## Recent autofolio change themes (~2026-06-05 → 06-22)

- Upstream sync cadence: v0.2.0→v0.3.0→v0.3.1 in ~1 week (tight).
- Product UI overhaul (Next.js + FastAPI, #73–#94) — host overlay, not upstream.
- Trading-domain safety/ops (KRX holiday block, SQLite WAL+FK, log rotation,
  safety-mode tests) — host-only.
- Platform dogfooding: a self-eval metrics pilot using autofolio as the workload.
- Host-built governance tooling facing the framework.

## Upstream candidates (recommended order)

| # | Candidate (autofolio path) | Rationale | Worth | Route |
|---|---|---|---|---|
| 1 | **Self-eval metrics framework** — `docs/AGENT_RUNTIME_EVAL_METRICS.md` + pilot BRIEF | Directly answers the OPEN upstream ask **#128** (cross-version self-eval). Generic: every consumer wants to know if a version got better/cheaper. | **High** | Task proposal under #128; merge the methodology doc first, then add `tokens_per_task` instrumentation upstream lacks. |
| 2 | **Downstream bug intake** — `scripts/report_upstream_bug.py` + AGENTS.md §18 convention | The exact consumer→maintainer feedback loop any pinned-dependency consumer needs (classify → BRIEF issue + patch PR → SessionStart WARN if unreported). | **High** | Task proposal; MUST parameterize remote URL / package name (currently hardcodes agent_runtime). |
| 3 | **`scripts/doc_steward_due.py`** | Read-only doc-governance advisory, sibling to upstream `scribe_due.py`; moving it framework-side lets autofolio drop another seam. | **Medium** | Task proposal; verify the role-taxonomy scan is consumer-generic before adopting. |
| 4 | **UUIDv4 task-identity core** (from `scripts/task_identity.py`) | Collision-proof IDs for concurrent registration — generally useful; only autofolio's `IDENTITY_REQUIRED_TASK_NUMBER=70` grandfather is host-specific. | **Medium** | Task proposal; upstream the core with the threshold made configurable. |

## Host-only (do NOT upstream)
`app/**` trading domain, product UI, and overlay/data files (`AGENTS.md`,
`agents/roles.yml`, `schemas/task.schema.json`, `NEXT-SESSION-POINTER.yml`,
research notes). Correctly forked via the `unmanaged` seam list.

## Risks
- Tight sync cadence; #101 recorded 10 conflicts from untracked drift at the
  v0.3.0 sync (mitigated by issue-first tracking, §6 MANDATORY).
- `AGENTS.md` is a high-churn seam (§15–§19 overlay shrinks as upstream absorbs
  each section — push §18/§19 upstream to shrink it).
- No duplicate/conflicting host patches detected; the two gate forks that *did*
  duplicate upstream logic were retired once #187 landed.

## Recommendation
Adopt #1 and #2 next (both answer concrete consumer needs and have an open issue
or a stated convention); #3 and #4 are cleanups. Each is a follow-up taskset
(generalize + tests + root/template parity + lock regen), not a blind file copy —
mirroring how #185 became #187. Owner approval gates the actual merges.
