# REVIEW-2026-06-10 agent runtime collaboration governance redesign

## Bottom Line

Collaboration governance is now promoted from advisory/template-only guidance into an Owner-facing runtime gate. Waived gaps are explicit, expiring, and measurable; unwaived role, artifact, capability, and lifecycle failures are machine-checkable.

## Definitions

`waiver` means an explicit exception record with subject, reason, approving authority, expiry, mitigation, and required follow-up. It does not mean "ignore the issue"; it means "allow this known gap temporarily while keeping it visible."

`runtime promotion` means a rule is no longer only written in documentation or template assets. It exists in root project policy, executable gate code, Owner gate wiring, and tests/templates so active work and future projects are checked the same way.

## Evidence added

- Root policy: `agents/project/COLLABORATION-GOVERNANCE.json`
- Template policy: `src/agent_runtime/templates/project/agents/project/COLLABORATION-GOVERNANCE.json`
- Waiver record: `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json`
- Root gate: `scripts/collaboration_governance_gate.py`
- Template gate: `src/agent_runtime/templates/project/scripts/collaboration_governance_gate.py`
- Owner gate wiring: `scripts/owner_governance_gate.py`
- Template Owner gate wiring: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- Gate tests: `tests/test_collaboration_governance_gate.py`

## What is now measurable

- Role coverage across task claims, including minimum required roles.
- Review artifact coverage by canonical prefixes: `REVIEW`, `MEETING`, `CALL`, `SEMINAR`, `RESEARCH`, `RETRO`.
- Root runtime capability presence for Ralph, retro, scribe, doc-steward, and compound coordination.
- Waiver count and expiry state.
- Lifecycle drift signals including future heartbeats, incomplete released-claim metadata, and missing active worktrees.

## Current gaps acknowledged by waiver

- `artifact:RETRO` has no root review artifact evidence by filename prefix.
- `role-usage:scribe` has insufficient claim evidence.
- `root-capability:ralph` is not promoted to a root executable capability path yet.
- `root-capability:retro` is not promoted to a root executable capability path yet.
- `root-capability:scribe` is not promoted to a root executable capability path yet.
- `root-capability:doc-steward` is not promoted to a root executable capability path yet.

## Weaknesses found

- Usage accounting existed only indirectly through task claims and artifacts; there was no single policy object declaring minimum expected role and artifact coverage.
- Template capabilities existed for some collaboration functions, but root runtime evidence was incomplete.
- Lifecycle quality issues such as future heartbeats and missing active worktrees were not surfaced by an Owner-facing collaboration gate.
- Low-frequency or excluded-agent detection was not enforced as a structured policy; it was audit prose.
- Waivers were not modeled as first-class governance records, so temporary exceptions could be confused with completion.

## Enforcement model

The new gate classifies findings as:

- `block`: unwaived required role, artifact, policy, or capability gap.
- `watch`: measurable lifecycle or utilization drift that should stay visible but should not stop safe local progress yet.
- `waived`: a block finding covered by an unexpired explicit waiver.

Owner gate now runs `scripts/collaboration_governance_gate.py --check`, so unwaived collaboration-governance failures become part of the standard release/hook gate path.

## Verification evidence

Focused plan verification passed:

```text
$env:PYTHONPATH='src'; pytest tests/test_collaboration_governance_gate.py tests/test_continuity_contract_gate.py tests/test_response_contract_gate.py
12 passed in 9.17s
```

Focused gate verification passed:

```text
$env:PYTHONPATH='src'; python scripts/collaboration_governance_gate.py --root . --check
collaboration-governance-gate: pass
block=0
watch=10
waived=6
```

Owner gate verification passed after wiring:

```text
$env:PYTHONPATH='src'; python scripts/owner_governance_gate.py
status=pass
```

Broad-suite verification is not closed:

```text
$env:PYTHONPATH='src'; pytest
collection failed with 7 import errors

$env:PYTHONPATH='.;src'; pytest
collection failed with 4 template-project import errors

$env:PYTHONPATH='.;src;src/agent_runtime/templates/project'; pytest
timed out after 180s with multiple template-project failures in progress

$env:PYTHONPATH='.;src'; pytest tests
timed out after 180s after collecting 321 root tests
```

The broad-suite result is recorded as residual repo-health work, not as a blocker for the collaboration governance gate because the focused tests and Owner gate covering this change passed.

## Follow-up required

- Replace waived root-capability gaps by promoting Ralph, retro, scribe, and doc-steward scripts into the root runtime.
- Add actual `RETRO-*` review artifacts when retrospectives are completed.
- Add claim/log evidence for scribe participation instead of relying on waiver.
- Triage active lifecycle watch signals before claiming all panes are cycle-complete.
