---
type: brief
id: REVIEW-2026-06-11-toolrunner-policy-closeout
audience: owner
signal: pass
score: 94
priority: High
tags: [toolrunner, security, command-policy, tests]
actions: [archive, no-action]
evidence:
  - IMPLEMENTATION_PLAN.md
  - src/agent_runtime/templates/project/scripts/providers/agent_tools.py
  - scripts/backlog_board.py
  - tests/test_template_agent_tools.py
---

Bottom Line: TASK-AR-313은 pass다. ToolRunner는 profile-scoped allowlist verifier로 동작하며, 이번 변경은 research/owner/pytest 우회 부정 테스트를 추가해 Phase 3 acceptance를 닫았다.

## Signal

| Item | State | Evidence |
|------|-------|----------|
| Default command profile | pass | `ToolRunner(..., command_profile="ci")` default |
| Mutable git blocking | pass | tests cover `git commit`, `checkout`, `restore`, `stash`, research mutable git denial |
| Python execution blocking | pass | tests cover `python -c`, stdin, pip install, unknown interpreters, path escapes |
| Profile-specific policy | pass | tests cover owner allowlist, owner path escape denial, research help-only commands and mutation denial |
| Board hygiene | pass | `scripts/backlog_board.py` avoids duplicate predecessor display replacement in generated board text |
| Verification | pass | `pytest tests/test_template_agent_tools.py -q`, `pytest tests -q` |

## Insight

1. Phase 3's code surface was already mostly implemented; the remaining risk was under-specified negative coverage by profile.
2. Keeping owner permissions explicit and path-bounded preserves repair workflows without reopening arbitrary shell execution.
3. Research profile remains non-mutating: it can inspect and run help-only exploration commands, but cannot write git state or install packages.

## Decision

1. No Owner decision is required for TASK-AR-313 closure.
2. Future ToolRunner expansion should add a named profile and a negative test before adding any new command form.

## Action Board

| Action | Owner | State |
|--------|-------|-------|
| Confirm Phase 3 implementation | Lead Engineer | pass |
| Add missing profile-negative tests | Lead Engineer | pass |
| Run focused and full pytest | QA | pass |

## Next

| Step | Owner | Trigger |
|------|-------|---------|
| Continue Vision Integrator taskset | dispatcher | next planned task |

## Verification

- `pytest tests/test_template_agent_tools.py -q` -> `19 passed`.
- `python -m py_compile src/agent_runtime/templates/project/scripts/providers/agent_tools.py` -> pass.
- `pytest tests -q` -> `390 passed in 372.82s`.
- `python -m py_compile scripts/backlog_board.py` -> pass.
- `pytest tests/test_backlog_board_tasksets.py tests/test_template_agent_tools.py -q` -> `22 passed`.
- `python scripts/owner_governance_gate.py` -> exit 0.
