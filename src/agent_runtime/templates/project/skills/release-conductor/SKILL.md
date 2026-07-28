---
name: release-conductor
version: 1.1.0
description: Prepare a release proposal and run generic verification; never tags, publishes, or encodes a host product release process.
triggers: [release, 배포, version]
dependencies:
  - scripts/owner_governance_gate.py
registry_id: release-conductor
template_path: skills/release-conductor/SKILL.md
---

# Release Conductor

Use this skill to make a release **proposal**, not to perform a release. Run
the host's normal test command and `python scripts/owner_governance_gate.py`.
Record the version, evidence, risks, and rollback plan with
`python scripts/save_report.py plan ...` in a host-owned report.

Tagging, publishing, release councils, credentials, downstream notification,
and product-specific cadence are deliberately outside Agent Runtime core. A
host may add those procedures in its own documentation after explicit Owner
approval.
