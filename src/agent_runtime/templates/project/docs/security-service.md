# Security-service profile

This profile adds claim-time metadata enforcement for paths that can affect
secrets, authentication, data migrations, or production systems. The gate
classifies path names only; it never opens target files or records their
contents.

## Risk contract

| Risk class | Required unit metadata |
| --- | --- |
| Secrets | `risk_tier: high|critical`, `security_sensitive: true`, `approval_required: true`, `security`, and `## Security Controls` |
| Authentication | high/critical, security-sensitive, `security` plus `data_integrity`, and `## Security Controls` |
| Migration | high/critical, `data_integrity` plus `external_effect`, and `## Rollback` |
| Production external effect | high/critical, `approval_required: true`, `external_effect`, and `## External Effect Boundary` |

Managed conservative patterns live in
`agents/project/SECURITY-SERVICE-POLICY.json`. Every v2 `host.risk_paths`
entry is additionally treated as a production external-effect surface.

`scripts/task_claim_dispatcher.py create` runs the gate before persisting a
claim when `scripts/security_service_gate.py` is installed. Core-only hosts do
not ship the gate and incur no claim-time dependency. Owner governance
rechecks active claims to expose post-claim metadata drift.

The installed profile fails closed when a claim has no registered task/unit
identity, its unit path is not the one canonical repository-relative path
derived from those IDs, frontmatter identities disagree, a task/unit path is
missing or symlinked, an active claim record or target snapshot is malformed,
or an existing `agent_runtime.yml` is not a readable regular file that parses
safely. Explicit claim targets are added to—not substituted for—the unit's
registered `target_files`, so a narrow snapshot cannot hide a risky registered
path. An absent configuration file, or a valid v2 configuration that omits
`host.risk_paths`, is the canonical empty host overlay.

## Security Controls

- Keep the policy and `.allimbot.json` managed through Runtime sync.
- Put real credentials in the host's secret manager, never in task records,
  event data, `.env.example`, or doctor output.
- Require Owner approval before a claim covering a secret or production
  external-effect path can begin.
- Add project-specific production surfaces through `host.risk_paths`; do not
  weaken the shared managed defaults.

## Rollback

Remove `security-service` from the selected profiles and apply the normal
Runtime update plan. This removes the profile-only gate, policy, recipe,
helper, and guide while retaining the core lifecycle harness.

## External Effect Boundary

The gate authorizes claim creation only; it does not authorize deployment,
migration execution, credential access, event delivery, spool flushing, or
other production mutations. Those actions still require their own explicit
Owner-approved workflow.
