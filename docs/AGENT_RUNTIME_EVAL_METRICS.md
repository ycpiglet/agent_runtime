# agent_runtime Self-Eval Metrics Framework (fixed + variable)

> **Purpose**: measure, **objectively and quantitatively**, whether a new
> agent_runtime version is actually *better* -- not just *different*. This is the
> fitness function that turns "self-improvement" into improvement rather than
> drift (agent_runtime#128).
>
> **Scope**: this is a consumer-agnostic methodology. A real consuming project's
> day-to-day work is the benchmark workload (dogfooding); this doc does not assume
> any particular consumer.

---

## 0. Principles

1. **Oracle = verified pass.** Not "did it look good" but "did it pass the tests
   and gates". A repo's own `pytest` plus its governance/quality gates are the
   ground truth (SWE-bench principle -- repo tests are the oracle).
2. **Fixed + variable, both.** Fixed-only means each new version is judged by an
   increasingly stale yardstick. Variable-only means every version overfits its
   own metrics and cannot be compared across versions. **Fixed = the spine
   (longitudinal comparison); variable = the limbs (does this version's new
   capability actually work).**
3. **Objective first, subjective only as support.** Things that cannot be
   quantified (e.g. "elegance") may be scored with a sampled rubric for color,
   but we never dress subjective judgement up as objective measurement.
4. **Small-N honesty.** Models vary run-to-run. Truly separating signal from
   noise needs many runs and is expensive. At small scale this is a **directional
   signal, not statistical proof** -- and we say so.

---

## 1. Fixed metrics (version-independent, longitudinal)

These stay meaningful no matter which version you are on: "is the work good and
cheap". Lock this set and measure it identically every version. The trend line
across versions is the spine of "is the platform actually getting better".

| Metric | Definition | Source | Available now |
|--------|------------|--------|---------------|
| `first_pass_rate` | Share of tasks that pass ALL gates (pytest, doc/quality gates, review) on the first attempt | Per-task CI + review logs | Proxy only (see below) |
| `rework_count` | Rework rounds (corrective follow-ups) per window | WORK-SCHEMA measurement / git proxy | Proxy (git) |
| `gate_failure_count` | Gate/verification failures per window | WORK-SCHEMA verification (`reviews/VERIFY-*.json`) | **Yes** (real source) |
| `reopened_count` | Times a task was reopened after closure | WORK-SCHEMA closure (`reopened_count` frontmatter) | **Yes** (real source) |
| `wall_clock_per_task` | Real time from task start to completion (`lead_time`) | WORK-SCHEMA `started_at`/`completed_at` | **Yes** (real source) |
| `tokens_per_task` | Tokens consumed per task | WORK-SCHEMA `actual_tokens` (closure) | **Yes** (real source) |
| `merge_conflict_count` | Merge conflicts during integration | git | Yes (merge-commit proxy) |
| `owner_interventions` | Owner decisions/corrections per task | Manual count | **NOT COLLECTED** (no source) |

### What `scripts/self_eval_metrics.py` computes today

The tool extracts two families for a version window (a commit range, default:
latest tag .. HEAD): the **git-derivable** metrics, and the **WORK-SCHEMA
record** metrics read from the repo's task/verification artifacts filtered to the
*same* window by record timestamp. Every metric is tagged `collected` or
`not_collected`; it never invents or estimates a value.

**Git-derived** (from the commit range `A..B`):

| JSON field | Maps to | How |
|------------|---------|-----|
| `commit_count` | window size | `git rev-list --no-merges --count A..B` |
| `feat_count` / `fix_count` | feature/fix volume | conventional-commit subjects |
| `merge_commit_count` | `merge_conflict_count` proxy | `git rev-list --merges --count A..B` |
| `rework_count` | `rework_count` | subject proxy (`revert`/`hotfix`/`fix:`) |
| `rework_ratio` | rework intensity | `rework_count / commit_count` (lower is better) |
| `first_pass_rate_proxy` | `first_pass_rate` | `1 - rework_ratio` (PROXY) |
| `days_since_from_tag` | window calendar span | timestamp of the base ref |

**WORK-SCHEMA-derived** (records whose timestamp falls in the window, where the
window bounds are the committer timestamps of the from/to refs):

| JSON field | Maps to | How |
|------------|---------|-----|
| `gate_failure_count` | `gate_failure_count` | `reviews/VERIFY-*.json` with `signal=fail`/`status=failed` and in-window `verified_at` |
| `reverification_count` | `rework`/`reopened` proxy | re-verification rounds (VERIFY attempts > 1 per work item) |
| `reopened_count` | `reopened_count` | WORK-SCHEMA closure `reopened_count` summed over in-window tasks |
| `measured_task_count` | denominator | tasks with `actual_hours`/`actual_tokens` populated |
| `actual_tokens_total` / `tokens_per_task` | `tokens_per_task` | WORK-SCHEMA measurement `actual_tokens` (sum, and per-task mean) |
| `actual_hours_total` / `hours_per_task` | effort | WORK-SCHEMA measurement `actual_hours` (sum, and per-task mean) |
| `wall_clock_hours_total` / `wall_clock_per_task` | `wall_clock_per_task` | `lead_time = completed_at - started_at` (sum, and per-task mean) |
| `owner_interventions` | `owner_interventions` | **`not_collected`** -- no source in repo records |

> **Honest framing.** `first_pass_rate_proxy` and `rework_count` are still *git
> subject proxies*, not the precise WORK-SCHEMA measurements; `reverification_count`
> is likewise a *proxy* for rework/reopen rounds derived from repeat verification
> attempts. The remaining WORK-SCHEMA fields (`gate_failure_count`,
> `reopened_count`, `actual_*`, `wall_clock_*`) read the **real** closure /
> measurement / verification source. Per-task means are emitted only when at
> least one in-window task actually carries the field -- otherwise the field is
> `not_collected` with `value: null` (never a fabricated zero-denominator value).
> `owner_interventions` has no source anywhere in the repo records and stays
> `not_collected`. We do not fake them.

---

## 2. Variable metrics (per-version, that version's new capability)

Whether the *new feature* of a version actually works. **When the capability
changes, this table changes.** Replace it per version; leave section 1 alone.

Example -- a hypothetical "parallel wave" version:

| Metric | Definition | Source |
|--------|------------|--------|
| `wave_parallelism` | Mean concurrent units per wave | wave dispatcher |
| `footprint_violation` | Units whose declared footprint differs from the actual `git diff` | post-hoc diff vs declaration |
| `wave_defer_rate` | Share of units deferred to a later wave due to footprint overlap | wave dispatcher |
| `parallel_speedup` | (estimated sequential time) / (actual wave wall-clock) | vs a sequential baseline |

> When the next version (e.g. a GUI, or RSI skill mutation) lands, **replace this
> table with that version's metrics**. The fixed table in section 1 does not move.

---

## 3. RSI fitness gate

Self-eval is the fitness function for Recursive Self-Improvement. A skill
self-modification (mutation) should be **adopted only if it passes an eval
improvement** -- otherwise "self-improvement" is just "self-change" with no
guarantee of direction.

- Compare version N vs N+1 on the **fixed** metrics (spine) and on N+1's
  **variable** metrics (does the new capability work).
- Account for run-to-run model variance with multiple runs before claiming an
  improvement; treat small-N results as directional.
- A mutation that regresses the fixed spine is rejected even if it improves a
  variable metric (no overfitting to the new toy).

---

## 4. Anti-patterns

- **Goodhart.** Optimizing the metric instead of the work (e.g. not splitting a
  task to keep `rework_count` low). Metrics are decision/feedback signals, not
  targets.
- **Eval theater.** Do not spend more on measuring than on the work. Prefer
  lightweight automatic capture; keep manual counting minimal.
- **False precision.** A proxy is a proxy. Label it, and prefer the
  instrumented metric once it exists.

---

## 5. Usage

```sh
# Latest tag .. HEAD, human-readable:
PYTHONPATH=src python scripts/self_eval_metrics.py

# Explicit version window, JSON for archiving / cross-version diffing:
# (--since/--until are aliases for --from/--to)
PYTHONPATH=src python scripts/self_eval_metrics.py --from v0.1.0 --to v0.2.0 --json

# Watch-only (always exits 0; never mutates state):
PYTHONPATH=src python scripts/self_eval_metrics.py --check
```

Boundaries: the tool is **watch-only** (no version bump, tag, push, publish, or
release), is a **source-repo tool** (not wired into `owner_governance_gate.py`,
no hardcoded consumer paths), and reuses the git helpers from
`scripts/release_cadence_trigger.py`.

---

## 5b. Host real-usage pipeline (`agent-runtime-host-eval/v1`)

Request 4 of agent_runtime#128: real-usage hosts (e.g. autofolio) supply
per-cycle metric snapshots so platform eval runs on real workload data, not
only on the platform's own records.

- **Drop location:** `agents/host/eval/*.json` — inside the host-owned
  namespace from `docs/host-context-read-location.md`, so templates never ship
  or overwrite it and absence is never an error. In the platform repo this is
  where host-relayed snapshots get committed (the same intake path as
  `HOST-FEEDBACK-QUEUE`); a host repo that copies the harness reads its own
  `agents/host/eval/` the same way.
- **File schema (one JSON per cycle):**

  ```json
  {
    "schema": "agent-runtime-host-eval/v1",
    "host": "autofolio",
    "cycle": "2026-07-pilot-wave-1",
    "fixed": {"gate_failure_count": 2, "rework_count": 1},
    "variable": {"wave_concurrency": 3, "footprint_violations": 0}
  }
  ```

  `schema`, `host`, and `cycle` are required. `fixed` uses the section-1
  vocabulary (subset OK); `variable` carries the host's per-version capability
  metrics (section-2 semantics, host-defined keys).
- **Ingestion:** `scripts/self_eval_harness.py` loads every matching file into
  the snapshot's `hosts` list (`--report`, `--write`, `--gate` all see them);
  the advisory gate prints one line per host cycle. Unreadable or
  foreign-schema files are listed loudly under `host_skipped` — never dropped
  silently.

---

## 6. What still needs instrumentation (deferred)

Section 1 lists eight fixed metrics. The git-derivable subset plus the
WORK-SCHEMA closure/measurement/verification fields that have a real repo source
are now automated. Newly wired from existing data (agent_runtime#128):

- **`gate_failure_count`** -- from `reviews/VERIFY-*.json` (`signal=fail`).
- **`reopened_count`** -- from WORK-SCHEMA closure `reopened_count` frontmatter.
- **`tokens_per_task` / `actual_*` / `wall_clock_per_task`** -- from WORK-SCHEMA
  measurement (`actual_tokens`/`actual_hours`) and `lead_time`
  (`completed_at - started_at`).
- **`reverification_count`** -- repeat-verification rounds as a rework/reopen
  *proxy*.

Still genuinely unsourced (remain `not_collected`):

1. **`owner_interventions`** -- no per-task owner-decision capture exists in any
   repo record.
2. **Per-task CI oracle** -- first-attempt FAILURE/SUCCESS per task to replace
   the `first_pass_rate` *proxy* with the true rate. (`gate_failure_count` and
   `reverification_count` now give a real-but-coarse signal in the meantime.)
3. **Live token metering** -- `tokens_per_task` reads the WORK-SCHEMA
   `actual_tokens` *closure* value (often `0`/unset on older tasks), not live
   session/workflow token accounting.

Until then those fields are reported as `not_collected`. Honest absence beats a
fabricated number.
