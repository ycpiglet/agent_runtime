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
| `gate_failure_count` | Gate failures per task | WORK-SCHEMA / CI | Not from git alone |
| `reopened_count` | Times a task was reopened after closure | WORK-SCHEMA closure | Not from git alone |
| `wall_clock_per_task` | Real time from task start to merge | Timestamps | Not from git alone |
| `tokens_per_task` | Tokens consumed per task | Session/workflow usage | **NOT COLLECTED** (no instrumentation) |
| `merge_conflict_count` | Merge conflicts during integration | git | Yes (merge-commit proxy) |
| `owner_interventions` | Owner decisions/corrections per task | Manual count | Not from git alone |

### What `scripts/self_eval_metrics.py` computes today

The tool extracts the **git-derivable subset** for a version window (a commit
range, default: latest tag .. HEAD), emitting `--json` with each metric tagged
`collected` or `not_collected`. It never invents or estimates a value.

| JSON field | Maps to | How |
|------------|---------|-----|
| `commit_count` | window size | `git rev-list --no-merges --count A..B` |
| `feat_count` / `fix_count` | feature/fix volume | conventional-commit subjects |
| `merge_commit_count` | `merge_conflict_count` proxy | `git rev-list --merges --count A..B` |
| `rework_count` | `rework_count` | subject proxy (`revert`/`hotfix`/`fix:`) |
| `rework_ratio` | rework intensity | `rework_count / commit_count` (lower is better) |
| `first_pass_rate_proxy` | `first_pass_rate` | `1 - rework_ratio` (PROXY) |
| `days_since_from_tag` | window calendar span | timestamp of the base ref |
| `tokens_per_task` | `tokens_per_task` | **`not_collected`** -- no instrumentation yet |

> **Honest framing.** `first_pass_rate_proxy` and `rework_count` here are *git
> subject proxies*, not the precise WORK-SCHEMA measurements. The exact oracle is
> per-task CI status (FAILURE/SUCCESS on first attempt) plus the WORK-SCHEMA
> measurement/closure groups (`rework`, `gate_failure`, `reopened`, `actual_*`).
> Fields that require instrumentation the platform does not yet have are emitted
> as `status: not_collected` with `value: null`. We do not fake them.

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
PYTHONPATH=src python scripts/self_eval_metrics.py --from v0.1.0 --to v0.2.0 --json

# Watch-only (always exits 0; never mutates state):
PYTHONPATH=src python scripts/self_eval_metrics.py --check
```

Boundaries: the tool is **watch-only** (no version bump, tag, push, publish, or
release), is a **source-repo tool** (not wired into `owner_governance_gate.py`,
no hardcoded consumer paths), and reuses the git helpers from
`scripts/release_cadence_trigger.py`.

---

## 6. What still needs instrumentation (deferred)

Section 1 lists eight fixed metrics; only the git-derivable subset is automated
today. To complete the harness:

1. **`tokens_per_task`** -- session/workflow token accounting (none exists yet).
2. **Per-task CI oracle** -- first-attempt FAILURE/SUCCESS per task to replace
   the `first_pass_rate` *proxy* with the true rate.
3. **WORK-SCHEMA wiring** -- read `gate_failure`, `reopened`, `actual_*` from the
   measurement/closure groups instead of git subject heuristics.
4. **`wall_clock_per_task` / `owner_interventions`** -- timestamp and
   intervention capture.

Until then those fields are reported as `not_collected`. Honest absence beats a
fabricated number.
