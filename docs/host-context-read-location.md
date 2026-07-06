# Host-Context Read-Location Convention

Status: adopted (doc-only scope per COUNCIL-2026-06-14, candidate 531 —
"read-location = doc-only; substrate `unmanaged_paths` exists").
Origin: issue #121 item 2 — hosts had no fixed place to put purpose, domain,
safety constraints, or role mapping that the framework would read, so they
either edited managed template files (sync conflicts) or scattered context in
files nothing reads.

## The convention

**`agents/host/` is the host-owned context namespace.**

- Templates MUST NOT ship any file under `agents/host/` (reserved; enforced by
  `tests/test_host_context_read_location.py`). Because nothing there is
  managed, `agent_runtime sync` / the lock digest never touch it — no
  `sync.unmanaged` entry is needed for files in this directory.
- The entry point is **`agents/host/HOST-CONTEXT.yml`**. Suggested keys:

  ```yaml
  schema: host-context/v1
  purpose: >-        # why this host exists, in one paragraph
  domain: >-         # the business/technical domain the agents operate in
  safety_constraints:
    - ...            # host-level inviolables (e.g. never place live orders)
  role_mapping:
    lead_engineer: ...   # host-side owner/team for each framework role
  read_more:
    - agents/host/...    # any further host-owned context documents
  ```

- Additional host context (playbooks, glossaries, domain notes) lives under
  `agents/host/` next to the entry point and is linked via `read_more`.

## Who reads it

- **Agents (today):** session-start instructions should treat
  `agents/host/HOST-CONTEXT.yml` as the fixed place to look for host purpose,
  domain, safety constraints, and role mapping — the point of the convention
  is that its *location* never needs discovering per host.
- **Framework (future):** components that want host context (planning loop,
  deliberation, dashboards) read this path. The file is optional; absence
  means "no host context provided" and MUST NOT be an error.
- **Wired today:** `scripts/self_eval_harness.py` reads host-supplied eval
  snapshots from `agents/host/eval/*.json`
  (`agent-runtime-host-eval/v1`; see `docs/AGENT_RUNTIME_EVAL_METRICS.md` §5b).

## Overriding managed files is a different problem

This convention is for *additive* host context. To locally diverge from a
file the templates DO manage, declare it under `sync.unmanaged` in
`agent_runtime.yml` — that excludes it from the sync plan and the lock digest
(see `src/agent_runtime/config.py` / `lock.py`). Do not put overrides in
`agents/host/`.
