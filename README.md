# Agent Runtime (agent_runtime)

Agent Runtime is a reusable automation core for repository agent workflows.
The primary distribution name, import package, config files, and CLI command
are `agent_runtime`.

Legacy `ralph` / `ralph_automation` aliases remain for one release so existing
host projects can migrate safely. Remove them after the replacement release is
published and host projects have moved to `agent_runtime`.

Public release boundary:

- Primary public tag: `https://github.com/ycpiglet/agent_runtime` `v0.1.5`
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
- package-data templates under `src/agent_runtime/templates/project/`
- package-local `tests/`
- GitHub Actions workflow under `.github/workflows/test.yml`
- no product files, host state, or local runtime state exported by default

## Quick Host Install

In a project that wants to use Agent Runtime, create a virtual environment,
install the package from the public GitHub tag, add `agent_runtime.yml`, then
run the non-mutating checks before applying templates.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.5"

@'
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.5
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
'@ | Set-Content -Encoding utf8 agent_runtime.yml

.\.venv\Scripts\agent_runtime update-plan --check
.\.venv\Scripts\agent_runtime update --check
.\.venv\Scripts\agent_runtime update --diff
.\.venv\Scripts\agent_runtime update --apply
```

macOS/Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.5"

cat > agent_runtime.yml <<'YAML'
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.5
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
YAML

agent_runtime update-plan --check
agent_runtime update --check
agent_runtime update --diff
agent_runtime update --apply
```

Use `--check` first for a safe status report, `--diff` to inspect exact file
changes, and `--apply` only when the diff is acceptable.

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
PYTHONPATH=src python -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/ycpiglet/agent_runtime.git --check
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
  ref: v0.1.5
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
as `v0.1.5` are accepted for normal distribution; a 40-character commit SHA is
stricter if the host must be protected from force-moved tags.
