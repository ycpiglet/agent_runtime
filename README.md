# Agent Runtime (agent_runtime)

Agent Runtime is a reusable automation core for repository agent workflows.
The primary distribution name, import package, config files, and CLI command
are `agent_runtime`.

## Host? Start Here

If you are installing Agent Runtime into a host project such as Autofolio, do
not clone this repository and copy files by hand. Treat this repository as the
upstream runtime, pin a release tag, then let `agent_runtime update`/`sync`
install the managed templates.

Recommended first path:

1. Install from the current public tag: `git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8`.
2. Create `agent_runtime.yml` with the same `remote_url` and `ref`.
3. Run `agent_runtime update --check`, then `--diff`, then `--apply`.
4. Put host identity under `agents/project/` overlays, not inside managed runtime files.
5. Run the host smoke checks listed below before tuning roles or reports.

Keep this split:

| Layer | Owner | Edit rule |
|---|---|---|
| Runtime templates | `agent_runtime` | Update through pinned release tags. |
| Host context | host project | Store under `agents/project/` overlays. |
| Host seams | host project | Use `sync.unmanaged` only when a managed file must diverge. |

Legacy `ralph` / `ralph_automation` aliases remain for one release so existing
host projects can migrate safely. Remove them after the replacement release is
published and host projects have moved to `agent_runtime`.

Public release boundary:

- Primary public tag: `https://github.com/ycpiglet/agent_runtime` `v0.1.8`
- Legacy compatibility tag: `https://github.com/ycpiglet/ralph-automation` `v0.1.4`

Current scope is GitHub source and host sync distribution:

- importable `agent_runtime` package
- `agent_runtime inventory --check`
- `agent_runtime export --check|--diff|--apply`
- `agent_runtime sync --check|--diff|--apply`
- `agent_runtime sanitize --root . --check`
- `agent_runtime publish-check --root . --check`
- `agent_runtime publish-bundle --source . --dest <dir> --check|--apply`
- `agent_runtime publish-tag-smoke --source . --repo-dir <dir> --install-dir <dir> --check|--apply`
- `agent_runtime publish-github-plan --source . --remote-url <github-url> --install-dir <dir> --check`
- `agent_runtime publish-github-status --remote-url <github-url> --check`
- `agent_runtime publish-github-execute --source <clean-source> --remote-url <github-url> --install-dir <dir> [--work-dir <dir>] [--execute]`
- `agent_runtime update-plan --root <host> --install-dir <dir> --check`
- `agent_runtime update --root <host> --install-dir <dir> --check|--diff|--apply`
- `agent_runtime release-preflight --source . --host-root <host> --remote-url <github-url> --check`
- `agent_runtime release-preflight --source . --host-root <host> --remote-url <github-url> --warning-summary-gate-strict-refs <strict_refs> --check`
- package-data templates under `src/agent_runtime/templates/project/`
- package-local `tests/`
- GitHub Actions workflow under `.github/workflows/test.yml`
- no product files, host state, or local runtime state exported by default

### Latency policy hooks (message queue PASS-39+)

Queue latency metrics for `tests/test_template_message_queue.py` are optionally exported
and evaluated by policy:

- `PASS_39_LATENCY_METRICS_PATH`: JSON or JSONL output path for one or more latency
  metric records.
- `PASS_39_MAX_P95_MS`, `PASS_39_MAX_P99_MS`, `PASS_39_MAX_FAILURE_RATIO`: numeric
  threshold overrides used by `test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`.
- `PASS_39_LATENCY_POLICY`: one of `warning-only` (default) or `fail-on-warning`.
- `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`: optional integer limit for allowed warning
  entries per policy evaluation.
- `PASS_39_LATENCY_METRICS_RUN_ID`: optional stable id written into each record.

`warning-only` mode keeps warnings visible without failing the assertion path, while
`fail-on-warning` enforces a hard gate when warning records exist.

CI 운영에서는 기본 게이트를 `warning-only`로 유지하고, 현재 워크플로우에서는
`main` 브랜치 푸시에 한해 Python `3.10`, `3.11`, `3.12` 실행기로 `fail-on-warning` 게이트를
추가로 실행합니다. 또한 매주 월요일 02:00 UTC의 `schedule` 실행에서는 Python
`3.10`, `3.11`, `3.12`에서 `fail-on-warning`을 실행하되,
`main`은 `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT=0`,
`schedule`은 `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT=1`을 사용합니다.
경로는 `event-py<python-version>-strict-countN.jsonl` 형태로 정책/허용치별 분리 저장하고, warning-only는 `event-py<python-version>.jsonl`으로 남깁니다.
CI 실행마다 `PASS_39_LATENCY_METRICS_RUN_ID`를 `run-<github_run_id>-...` 패턴으로 주입해
아티팩트 추적 재현성을 보장합니다.

### warning-summary strict-ref policy inputs (manual/reusable workflows)

`test` workflow supports `workflow_call` / `workflow_dispatch` input:

- input name: `warning_summary_gate_strict_refs`
- default lines:
  - `refs/heads/main`
  - `refs/heads/release/`
  - `refs/tags/`

재현 실행 예시:

```bash
gh workflow run test.yml \
  --repo <OWNER>/<REPO> \
  --ref <branch-or-tag> \
  --field warning_summary_gate_strict_refs=$'refs/heads/main\nrefs/heads/release/\nrefs/tags/'
```

수동 실행에서는 요약 로그/summary에 다음이 남아야 추적 가능합니다:

- source (`workflow_dispatch_input` 또는 fallback source)
- 정규화된 strict-ref 라인 목록
- `require-send-targets` 판정 (`0`/`1`)
- `warning-summary-strict-ref-policy.json`(workflow artifact) 내 동일 값

CI summary는 동일한 판정을 재사용하므로, policy 재현 시점과 실제 적용이 일치해야 합니다.

CI에서 `PASS-93` 항목은 추가로 `Validate warning-summary strict-ref policy artifact consistency` 스텝에서
artifact( .tmp/warning-summary-strict-ref-policy.json )와 resolve step 출력의 일치 여부를
자동 검증합니다. 추가로 수동 점검이 필요하면 다음처럼 확인할 수 있습니다:

```bash
python - <<'PY'
import json
path = ".tmp/warning-summary-strict-ref-policy.json"
decision = json.load(open(path, encoding="utf-8"))
print(decision)
PY
```

PASS-95 보조 재현 스크립트:

```bash
python scripts/warning_summary_strict_ref_policy.py \
  --mode validate \
  --artifact .tmp/warning-summary-strict-ref-policy.json \
  --github-event-name manual \
  --github-ref refs/heads/main \
  --run-id 1234 \
  --job-attempt 1 \
  --matrix-python-version 3.12 \
  --strict-refs-source workflow_dispatch_input \
  --strict-refs $'refs/heads/main\nrefs/heads/release/\nrefs/tags/' \
  --require-send-targets 1
```

## Quick Host Install

In a project that wants to use Agent Runtime, create a virtual environment,
install the package from the public GitHub tag, add `agent_runtime.yml`, then
run the non-mutating checks before applying templates.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8"

@'
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.8
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
'@ | Set-Content -Encoding utf8 agent_runtime.yml

.\.venv\Scripts\agent_runtime update-plan --check
.\.venv\Scripts\agent_runtime update --check
.\.venv\Scripts\agent_runtime update --diff
.\.venv\Scripts\agent_runtime update --apply
Copy-Item agents\project\PROJECT-CONTEXT.example.yml agents\project\PROJECT-CONTEXT.yml
```

macOS/Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8"

cat > agent_runtime.yml <<'YAML'
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.8
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
YAML

agent_runtime update-plan --check
agent_runtime update --check
agent_runtime update --diff
agent_runtime update --apply
cp agents/project/PROJECT-CONTEXT.example.yml agents/project/PROJECT-CONTEXT.yml
```

Use `--check` first for a safe status report, `--diff` to inspect exact file
changes, and `--apply` only when the diff is acceptable.

Recommended host smoke after first apply:

```bash
agent_runtime update --check
python scripts/check_agent_docs.py
python -m pytest tests -q
```

Host projects should scope their own tests under `tests/`. Framework self-tests
remain upstream CI responsibility unless the host intentionally vendors or
modifies template internals.

## Host Project Context

Agent Runtime is meant to act like a reusable agent development team. Keep the
team's shared runtime behavior upstream-managed, and put each host project's
product identity under `agents/project/`.

Use `agents/project/PROJECT-CONTEXT.yml` to map:

- project vision, purpose, user, and MVP success metric
- roadmap phase and release policy
- organization, decision owner, and escalation rule
- agent teams and the documents each team must read
- links to briefs, specs, tickets, product docs, and external references

`scripts/agent_context_packet.py` automatically includes existing
`agents/project/` context files in every role packet. This lets different host
projects tune vision, roadmap, organization, and team topology without editing
managed files such as `agents/*/SKILL.md`, `agents/roles.yml`, or `scripts/*`.

Recommended host-owned overlay files:

| File | Purpose |
|---|---|
| `PROJECT-CONTEXT.yml` | Vision, product purpose, target users, MVP success metric, domain constraints. |
| `ROADMAP.md` | Current phase, milestones, release policy, near-term work. |
| `ORG.md` | Decision owner, escalation path, accountability map. |
| `LINKS.md` | Canonical specs, tickets, docs, external references. |
| `TEAMS.md` | Host-specific team topology and role mapping. |
| `CONTEXT-SOURCES.example.yml` | Source tier, owner, freshness, lineage, access level examples. |
| `DATASET-CATALOG.example.yml` | SSoT-style dataset inventory and trust ranking examples. |
| `AUTONOMY-POLICY.example.yml` | Branch/commit/PR/merge and release-council defaults. |
| `EVAL-POLICY.example.yml` | Offline/live validation defaults and evidence expectations. |

### Autofolio integration lessons tracked in issue #1

Autofolio's host integration report identified three high-value adoption
lessons. The current disposition is:

| Input | Current handling |
|---|---|
| Host context injection was unclear. | Use `agents/project/PROJECT-CONTEXT.yml` and neighboring overlay files as the fixed read location for project identity. Runtime context packets include these files when present. |
| Sync was too binary for unavoidable host seams. | Current safe behavior remains fail-closed conflicts. Use overlays first; use `sync.unmanaged` only for intentional host-owned seams. Managed-region and skip-conflict ergonomics remain follow-up design work. |
| Fresh host install was not green enough. | `v0.1.8` ships the missing schema, handoff/token-budget links, safety gate, pipeline module, and clean-bundle CI coverage. Hosts should still run the smoke commands above. |

When a host needs custom agents or role exposure for another runtime such as
Claude Code, keep `agents/<role>/SKILL.md` as the durable project-readable
source and add adapter/generated files separately. Do not edit upstream-managed
role skills just to inject host product context.

For local development on this source tree, use an editable install instead:

```powershell
python -m pip install -e <local-agent-runtime-path>
```

## Export Behavior

`agent_runtime export` stages reusable host automation into installable package
templates.

- `--check` reports missing template files, conflicts, and unsafe content.
- `--diff` renders unified diffs for staged templates.
- `--apply` copies missing safe candidates only.
- It never exports `public/`, `supabase/`, `.env`, task/report history,
  runtime messages, or local tool settings.
- Existing divergent templates are conflicts and are not overwritten.

## Sync Behavior

`agent_runtime sync` reads safe templates from package data under
`agent_runtime/templates/project`.

- Missing host files are reported as `create` updates.
- Existing managed host files are reported as `update` only when their current
  content still matches the previous `agent_runtime.lock.json` per-file hash.
- `--diff` renders unified diffs.
- `--apply` creates missing safe templates and updates unchanged managed files.
- Existing divergent host files are conflicts and are not overwritten.

## Conflict Meaning

A `conflict` is a sync safety stop, not a Git merge conflict. It means the host
project has edited a managed file since the previous `agent_runtime.lock.json` baseline,
so Agent Runtime refuses to overwrite it automatically.

When conflicts appear:

1. Run `agent_runtime update --diff`.
2. Inspect each host-diverged file.
3. Manually merge the upstream template change if it is useful.
4. Re-run `agent_runtime update --check`.
5. Write a fresh lock only after the host files intentionally match the chosen
   state.

This keeps product-specific edits, local operating rules, and private host
state from being replaced by generic upstream templates.

## Tool Command Guardrails (Template Runtime)

Template workers expose a constrained command tool (`ToolRunner`) used by provider
bridges.

- `ci` (default): read-only verification commands only.
- `research`: `ci` baseline + non-mutating helper script help commands.
- `owner`: `research` + extra maintenance commands (`git add`, `git restore`)
  with explicit in-repo path checks.

Allowed examples:

- `git status`, `git diff`, `python scripts/check_agent_docs.py`, `python -m pytest -q`
- `python scripts/agent_worker.py --help`, `python scripts/auto_runner.py --help` (research)
- `git add path/to/file` (owner only)

Blocked by default:

- `python -c ...`
- `python -m pip ...`
- mutable git commands (`git commit`, `git checkout`, `git push`, `git stash`, ...)
- shell composition tokens (`&&`, `||`, `|`, `;`, `>`/`<`, `` ` ``, `$(`)

If a command is denied, the runtime message includes the active profile and the
profile allowlist summary for deterministic review.

## Publish Check

Run this before creating a public GitHub repo or tag:

```powershell
PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check
PYTHONPATH=src python -m agent_runtime.cli publish-tag-smoke --source . --repo-dir .tmp/tag-repo --install-dir .tmp/tag-install --check
PYTHONPATH=src python -m agent_runtime.cli publish-github-plan --source . --remote-url https://github.com/ycpiglet/agent_runtime.git --install-dir .tmp/github-install --check
PYTHONPATH=src python -m agent_runtime.cli publish-github-status --remote-url https://github.com/ycpiglet/agent_runtime.git --check
PYTHONPATH=src python -m agent_runtime.cli publish-github-status --remote-url https://github.com/ycpiglet/agent_runtime.git --branch main --require-workflow --wait-workflow --check
PYTHONPATH=src python -m agent_runtime.cli publish-github-status --remote-url https://github.com/ycpiglet/agent_runtime.git --branch main --require-workflow --wait-workflow --workflow-head-sha <commit-sha> --check
PYTHONPATH=src python -m agent_runtime.cli publish-github-execute --source .tmp/public-source --remote-url https://github.com/ycpiglet/agent_runtime.git --install-dir .tmp/public-source/.tmp/github-install
PYTHONPATH=src python -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/ycpiglet/agent_runtime.git --warning-summary-gate-strict-refs $'refs/heads/main\nrefs/heads/release/\nrefs/tags/' --check
PYTHONPATH=src python -m pytest tests -q
```

`publish-check` verifies the package has CI, package-data templates, sanitizer
CI coverage, and no unignored legacy top-level template tree.

`sanitize` scans publishable source content for forbidden paths, local absolute
paths, and secret-like content. Generated local work directories such as
`.tmp/`, `build/`, `dist/`, `.pytest_cache/`, and `*.egg-info/` are ignored so a
local smoke run does not make the source package fail its own preflight.

`publish-bundle` selects only the files that should become the public GitHub
source tree: `.github/`, `src/`, `tests/`, `.gitignore`, `pyproject.toml`, and
`README.md`. It refuses to overwrite a non-empty destination.

`publish-tag-smoke` creates a clean local git repo, tags it, installs from
`git+file://...@tag`, and verifies installed sync templates. Use `--apply` for
the full local rehearsal.

`publish-github-plan` is non-mutating. It prints the exact external commands for
the Owner-approved boundary: first build the public bundle worktree, initialize
and commit/tag the local release, then verify or create the public GitHub
repository with `gh repo view` / `gh repo create --public`, push `main`, push
the release tag, install from `git+https://...@tag`, verify installed sync
templates, and run the workflow-required publish status check. The final manual
status command resolves the release SHA with a Python subprocess call instead
of shell command substitution, reducing PowerShell/Bash quoting drift for paths
with spaces. It blocks unignored files outside the `publish-bundle` public
source contract so `git add .` cannot accidentally publish host-only leftovers.
Placeholder owners such as `OWNER` are publish findings; replace `example` with
the real GitHub owner before treating the plan as release evidence.

`publish-github-status` is read-only. It checks local `gh` authentication and
repository availability so the external publish boundary can fail early before
repo creation, push, or tag commands are attempted. Existing repositories must
be public; a private repo is a publish finding, not a successful target. Add
`--require-workflow` after a push to require the configured workflow
(`--workflow-name`, default `test`) to be completed with a successful
conclusion. Add `--wait-workflow` for the real post-push gate; it polls until
the latest run succeeds or the timeout is reached. Add `--workflow-head-sha` to
ensure the run belongs to the release commit, not an older successful run on
the same branch.

`publish-github-execute` renders the exact Owner-approved execution sequence by
default. It only runs public GitHub mutation commands when `--execute` is
provided. The first executed step is `gh auth status`; if auth fails, repo
creation, git commit, push, tag, and install verification are not attempted.
Use a clean bundle from `publish-bundle` as `--source` for the real external
publish. When execution proceeds, the clean source is copied into a throwaway
git worktree under `<source>/.tmp/github-worktree` by default, and all
`git init/add/commit/tag` steps run there before repo create/push, instead of
mutating the original clean source. Use `--work-dir` only for an empty directory under the source
`.tmp/` tree. The repo ensure step is fail-closed: it accepts an existing public
repo, creates a public repo only when `gh repo view` reports not found, and
blocks private repos or other lookup failures. After pushing and verifying the GitHub tag install, execution runs
`publish-github-status --require-workflow --wait-workflow --check` so a failed,
missing, timed-out, or never-green GitHub Actions run keeps the publish
incomplete. During real execution it resolves the release worktree `HEAD` and
passes it as `--workflow-head-sha`, so a previous successful workflow run cannot
stand in for the commit just published.

## Host Update Plan

Host projects pin the upstream dependency in `agent_runtime.yml`:

```yaml
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.8
```

If the package is installed in the active environment, run:

```powershell
agent_runtime update-plan --root <host> --check
agent_runtime update --root <host> --check
agent_runtime update --root <host> --diff
agent_runtime update --root <host> --apply
```

When `--install-dir` is omitted, `agent_runtime` stages the pinned upstream
package in `<root>/.tmp/agent_runtime-upstream`.

`update-plan` is non-mutating. It prints the install command for the pinned
GitHub ref and the follow-up `sync --check`, `sync --diff`, `sync --apply`
commands, followed by `lock --write` to record the installed version and
template digest. The digest ignores install-time `__pycache__` files and
normalizes text line endings, so source and installed package checks compare the
same template content across platforms. `update-plan --check` uses the same
trust checks as executable update: `upstream.package` must be
`agent_runtime`, the remote must be GitHub, the ref must be a SemVer-like
release tag or 40-character SHA, and the install dir must be empty under
`.tmp/` or `.agent_runtime/` (`.ralph/` is accepted for one release).

`update` executes the same flow instead of only printing it. It installs the
pinned upstream into a staging directory, verifies the installed package has
sync templates, and then runs installed-target sync commands. `--check` and
`--diff` write only to the staging install directory; `--apply` runs
`sync --apply`, verifies with a post-apply `sync --check`, and then writes the
host `agent_runtime.lock.json`. Executable update rejects unsafe install targets: use an
empty directory under the host `.tmp/` or `.agent_runtime/` tree.

The lock file records both an aggregate template digest and per-file
`managed_files` hashes. That lets future sync runs automatically update files
that still match the previous upstream while blocking files that were edited in
the host project.

`release-preflight` is the single non-mutating pre-publication plan check. It
aggregates sanitize, publish-check, bundle plan, local tag smoke plan, GitHub
publish plan, host update plan, host upstream match, executable host update
command shape, host sync conflict detection, and host lock freshness into one
report. It does not replace `publish-tag-smoke --apply` or the real
`publish-github-execute --execute` / workflow status evidence. Release tags such
as `v0.1.6` are accepted for normal distribution; a 40-character commit SHA is
stricter if the host must be protected from force-moved tags.

