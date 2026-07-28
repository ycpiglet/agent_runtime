# Configuration v2

Configuration v2 adds a machine-readable host overlay contract without
changing existing sync or lock behavior. There is no YAML package dependency:
only scalar mappings, scalar lists, quoted scalars, comments, and documented
folded context scalars are supported.

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

## Effective configuration report

`agent_runtime doctor --root . --json` emits
`agent-runtime-doctor/v1`. Its `config` object contains normalized source and
effective schema, compatibility sync fields, profile/capability selections,
ownership, and host context. It remains valid JSON if config is invalid; then
`config.valid` is false and `findings` contains the blocker. `--repair --json`
includes `repair_actions` in the same document.
