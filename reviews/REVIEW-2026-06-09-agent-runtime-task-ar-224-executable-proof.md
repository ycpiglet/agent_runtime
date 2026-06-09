# REVIEW (2026-06-09) - TASK-AR-224 executable overlay packet + preflight proof

## Scope

- 대상 태스크: `TASK-AR-224`
- 목적: 문서상 overlay/gate 정합을 실제 실행 증거로 보강.
- 실행 환경: Windows PowerShell
- Python 경로: `C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe`

## Command Evidence

### 1. Bare python failure

Command:

```powershell
python "src/agent_runtime/templates/project/scripts/agent_context_packet.py" --role lead-engineer --format json
```

Result:

- exit_code: 1
- finding: `python` is not on PATH in this shell.
- decision: use verified Python310 path for this repo.

### 2. Executable context packet proof

Command:

```powershell
& "C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe" "src/agent_runtime/templates/project/scripts/agent_context_packet.py" --role lead-engineer --format json
```

Result:

- exit_code: 0
- role_id: `lead-engineer`
- audit_gate: `true`
- project_context included:
  - `agents/project/README.md`
  - `agents/project/SKILL-GOVERNANCE.md`
  - `agents/project/ROADMAP.md`
  - `agents/project/ORG.md`
  - `agents/project/TEAMS.md`
  - `agents/project/LINKS.md`
- warning:
  - `CONTEXT-SOURCES.yml: definition_policy.rule is missing; define policy first.`

Interpretation:

- PASS: context packet generation is executable and includes project overlay documents.
- HOLD: missing `definition_policy.rule` means the query/definition policy path is not release-ready.

### 3. Context packet check-only proof

Command:

```powershell
& "C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe" "src/agent_runtime/templates/project/scripts/agent_context_packet.py" --role lead-engineer --check-only
```

Result:

- exit_code: 0
- output: `OK: role 'lead-engineer' and task '(none)' resolve cleanly`

Interpretation:

- PASS: role registry and packet builder resolve without task input.
- LIMITATION: `TASK-AR-224` is not present inside the package template task folder, so this proof is role/overlay executable proof, not task-specific packet proof.

### 4. release-preflight with current root as host

Command:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe" -m agent_runtime.cli release-preflight --source . --host-root . --remote-url https://github.com/ycpiglet/agent_runtime.git --warning-summary-gate-strict-refs "refs/heads/main`nrefs/heads/release/`nrefs/tags/" --check
```

Result:

- exit_code: 1
- error: `agent_runtime.yml not found under C:\Users\ycpig\agent_runtime`

Interpretation:

- PASS as blocker evidence: repo root is a package source, not a configured host project.
- Route: use fixture host or configured host for preflight.

### 5. release-preflight with fixture host

Command:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\ycpig\AppData\Local\Programs\Python\Python310\python.exe" -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --warning-summary-gate-strict-refs "refs/heads/main`nrefs/heads/release/`nrefs/tags/" --check
```

Result:

- exit_code: 1
- findings: 358
- check summary:
  - sanitize: blocked, findings=29
  - warning-summary-gate-strict-refs: ok, findings=0
  - publish-check: ok, findings=0
  - publish-bundle: blocked, findings=29
  - local-tag-smoke-plan: blocked, findings=29
  - github-publish-plan: blocked, findings=270
  - host-update-plan: ok, findings=0
  - host-upstream-match: ok, findings=0
  - host-update-command: ok, findings=0
  - host-sync-check: ok, updates=172, conflicts=0
  - host-lock: blocked, findings=1

Representative blockers:

- `agents/lead_engineer/tasks/TASK-AR-201.md` through `TASK-AR-224.md`: forbidden-path, host/product/local path must not be published.
- `agents/project/MIGRATION-COMPAT-MAP.yml`: absolute-local-path.
- `agents/project/MIGRATION-HOLD-ROUTING.yml`: absolute-local-path.
- `src/agent_runtime/templates/project/agents/project/MIGRATION-COMPAT-MAP.example.yml`: absolute-local-path and host-history-reference.
- `agent_runtime.lock.json`: lock-out-of-date, run `agent_runtime lock --write`.

## Gate Decision

- `TASK-AR-224` has executable packet proof.
- `TASK-AR-224` has executable release-preflight proof.
- Release state remains `hold_for_data` and `block`; it is not `ready`.
- The next required work is not more documentation. It is source publication hygiene:
  - remove or exclude host-local task/review files from clean public source
  - remove absolute local paths from publishable migration docs
  - decide whether `MIGRATION-HOLD-ROUTING.yml` is host-only or sanitized package data
  - refresh host lock if using the fixture host as proof input

## Follow-Up

1. Update `TASK-AR-224` cycle log.
2. Route the 358 findings into `TASK-AR-223` closeout as blocker evidence.
3. Start a follow-up task for source publication hygiene before marking v0.1.8 ready.
