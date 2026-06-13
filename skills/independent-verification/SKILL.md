---
name: independent-verification
version: 1.0.0
description: Use when the user asks to verify work, review a claim before release, run W4a self-check or W4b independent approval, or asks why a release needs a verifier different from the worker (작업자 자기검증 금지).
triggers:
  - verify
  - W4b
  - 검증
  - review
dependencies:
  - scripts/task_claim_dispatcher.py
  - scripts/work.py
  - scripts/owner_governance_gate.py
registry_id: independent-verification
template_path: src/agent_runtime/templates/project/skills/independent-verification/SKILL.md
---

# Independent Verification

Codifies the Owner rule "작업자 자기검증 금지 -- 항상 다른 에이전트가 검증".
W4 is split: W4a (the worker runs verification commands and attaches evidence)
and W4b (a DIFFERENT agent instance/role reviews and approves). A claim can
only be released after a W4b sign-off whose identity differs from the worker.

## When To Use

- About to release a claim, close a work item, or merge implemented work.
- Owner asks to "검증", "review before merge", or who may approve a release.

## W4a -- Worker Self-Check (necessary, not sufficient)

The worker runs the work item's verification commands and records evidence:

```powershell
python scripts/work.py verify <UNIT-or-TASK-id>
python scripts/owner_governance_gate.py
python -m pytest tests -q
```

Self-check alone CANNOT release the claim. It produces the evidence the W4b
verifier reviews.

## W4b -- Independent Approval (release gate)

A distinct agent instance (a reviewer subagent, or a separate role pane such
as codex<->claude cross-review) reviews the diff and the W4a evidence, then
the release is recorded with the verifier's identity:

```powershell
python scripts/task_claim_dispatcher.py release `
    --claim-id <CLAIM-id> `
    --verified-by <verifier-agent_instance_id> `
    --verifier-role <e.g. qa-reviewer> `
    --verification-evidence <repo-relative evidence ref>
```

The gate refuses release when:
- `--verified-by` is missing, OR equals the claim's worker `agent_instance_id`
  (verifier must differ from worker);
- `--verifier-role` is missing;
- `--verification-evidence` is missing or the ref does not exist (evidence is
  required by default).

The released claim records `verified_by`, `verifier_role`, and
`verification_evidence`, and a `claim_released` pane event captures the
cross-verification.

## Safety Boundaries

- verifier != worker is a HARD gate -- never self-approve to release, close,
  or enter merge.
- `--allow-missing-evidence` is a loud transitional escape only; attach
  evidence and backfill `verification_evidence` as soon as possible.
- Minimum independence: an instance that does NOT share the worker's
  conversation context (subagent reviewer is acceptable); a separate role pane
  is stronger. Record the verifier identity in closeout/handoff.

## W0->W6 Touchpoints

- W4a: worker verification + evidence.
- W4b: independent approval = the release gate; this is where
  `task_claim_dispatcher.py release --verified-by` enforces the rule.
- W5/W6: only verified-released branches enter the merge queue and closeout.
