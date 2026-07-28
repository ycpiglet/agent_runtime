# Configuration v2

Configuration v2 adds a machine-readable host overlay contract without
changing existing sync or lock behavior. There is no YAML package dependency:
only scalar mappings, scalar lists, quoted scalars, comments, and documented
folded context scalars are supported.

An unquoted `#` preceded by whitespace starts a comment; apostrophes in an
unquoted scalar are literal. Quoted mode starts only when the first non-space
character is a quote, preserving `#` inside the quoted value; an opened quote
must be closed before an optional trailing comment.

```yaml
schema: agent-runtime-config/v2
project: example
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.8.0
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
profiles:
  - web-content
capabilities:
  - compound
ownership:
  host_owned:
    - AGENTS.md
host:
  context: agents/host/HOST-CONTEXT.yml
  role_overlay: agents/host/ROLE-OVERLAY.yml
  risk_paths:
    - app/production
  state_adapters:
    status: STATUS.md
    backlog: BACKLOG.md
  state_projection: agents/project/state/SCRIBE-PROJECTION.json
```

## Compatibility

| Source | Effective projection | Existing behavior |
| --- | --- | --- |
| config without `schema` | `source_schema: agent-runtime-config/v1`, full-runtime profiles | unchanged; documented v1 keys only |
| `sync.unmanaged` | `host_owned` ownership | `unmanaged_paths` remains byte-compatible for sync/lock |
| `agent-runtime-config/v2` | selected profiles/capabilities and ownership table | diagnostic only in UNIT-640 |

Schema omission is the only v1 signal. An explicit v1 schema (or any unknown
schema) blocks. V2-only declarations cannot be added to a schema-less file,
and `sync.unmanaged` is v1-only: v2 hosts declare `ownership.host_owned`.
Unknown keys in the supported root and nested mappings block rather than being
silently ignored.

Profiles are registry ordered: `core`, `web-content`, `security-service`.
`core` is always enabled; `full-runtime` expands to all three and cannot be
combined with another profile. Unknown profile or capability identifiers block.

Ownership modes are `managed`, `seed_once`, `host_owned`, and `generated`.
Paths must be safe relative POSIX paths. Mixed-mode duplicate or
ancestor/descendant overlaps block. `agents/host/**` is always host-owned.
Windows drive paths, absolute paths, backslashes, empty/internal-double-slash,
dot traversal, `.git`, and runtime config/lock paths block. A trailing slash
in a risk path is normalized to its canonical path.
This release does not apply declarations; sync/lock semantics come later.

`agents/host/HOST-CONTEXT.yml` is optional. When present it must declare
`schema: host-context/v1`, and its purpose, domain, safety constraints, role
mapping, and read-more links appear in `agent_runtime doctor --json`.
`host.context`, if set, must be the canonical context path.

## Scribe state adapters and projection

`host.state_adapters` accepts at most eight descriptive identifiers mapped to
safe relative Markdown or JSON paths. Identifiers describe sources; they do
not select a product-specific parser. If adapters are omitted, Scribe uses the
first existing conventional state path from
`agents/lead_engineer/STATUS.md`, `STATUS.md`, `BACKLOG.md`,
`docs/PROJECT_STATUS.md`, `docs/PROJECT_STATUS.ko.md`, and
`PROJECT_STATUS.md`. A missing configured source or unavailable fallback is
reported explicitly and is never counted as zero.

Conventional state paths default to `host_owned`. Any other configured source
must be declared under `ownership.host_owned` or `ownership.seed_once`; live
host state can never become a permanently managed or generated template
asset.

The default generated projection is
`agents/project/state/SCRIBE-PROJECTION.json`. A custom
`host.state_projection` must be distinct from every source and must also be
listed exactly under `ownership.generated`. Canonical status and backlog files
remain host-owned; the runtime never edits them.

```yaml
ownership:
  generated:
    - .agent-runtime/state/scribe.json
host:
  state_adapters:
    status: STATUS.md
  state_projection: .agent-runtime/state/scribe.json
```

`python scripts/scribe_due.py --root . --json` is read-only.
`--write-projection` is the sole projection write path and uses an atomic
same-directory replacement. The projection holds only source paths and
SHA-256 digests, counts, bounded derived headings/items, checklist state,
timestamps, and finding codes. It is limited to eight sources, ten selected
items, and 32 KiB; credentials, environment assignments, prompt/transcript
content, private-key markers, and arbitrary JSON fields are omitted or
redacted.

Each source is `ok` at 12 or fewer hot items, `due` at 13–15, and `overdue`
at 16 or more. A projection is fresh only while all current source paths and
digests match. Doctor and SessionStart evaluate this state without writing.
Substantial closeout blocks only for a present overdue source whose projection
is missing or stale; due, unavailable optional sources, and mini work remain
advisory.

## Effective configuration report

`agent_runtime doctor --root . --json` emits
`agent-runtime-doctor/v1`. Its `config` object contains normalized source and
effective schema, compatibility sync fields, profile/capability selections,
ownership, and host context. It remains valid JSON if config is invalid; then
`config.valid` is false and `findings` contains the blocker. `--repair --json`
includes `repair_actions` in the same document. The host block also includes
the effective `state_projection`, and valid hosts receive a read-only `scribe`
evaluation with source and projection freshness findings.
