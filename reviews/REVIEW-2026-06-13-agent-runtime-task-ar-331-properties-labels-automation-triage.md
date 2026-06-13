---
id: REVIEW-2026-06-13-agent-runtime-task-ar-331-properties-labels-automation-triage
type: review
date: 2026-06-13
task: TASK-AR-331
signal: pass
score: 93
owner: lead-engineer
tags: [review, ui-console, custom-properties, labels, automation, triage, gate]
evidence:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_commands.py
  - src/agent_runtime/ui_console.py
  - scripts/automation_rules_gate.py
  - src/agent_runtime/templates/project/scripts/automation_rules_gate.py
  - scripts/owner_governance_gate.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - tests/test_ui_extensions.py
  - tests/test_automation_rules_gate.py
---

# TASK-AR-331 Custom Properties / Labels / Automation Rules / Triage Review

## Bottom Line

- Summary: `TASK-AR-331` adds Notion-style custom properties, Monday/Linear-style
  labels, Monday/ClickUp "when X then Y" automation rules, and a Linear-style
  triage queue to the V2 console - all within the established read-only state +
  proposal-only command boundaries.
- Output: four new resources (`custom_properties`, `labels`, `automation_rules`,
  `triage`), four new CRUD command families (property/label/automation), four new
  sidebar views, and a new gate (`automation_rules_gate.py`) wired into the
  owner-governance chain (root + template, chain-parity).
- Next: a runtime executor should consume the `.ui_outbox/{properties,labels,automation}`
  proposals into the canonical `agents/project/ui/**` + `agents/project/automation/rules/**`
  files, and run the automation gate with `--apply` on the gate tick.

## Signal

| Signal | Status | Evidence |
|---|---|---|
| Custom properties parse/display/filter | pass | `load_custom_properties`, `enrich_tasks_with_custom_properties`, `filter_tasks_by_custom_properties` |
| Label CRUD + usage count | pass | `build_labels` joins definitions with COMPUTED task-tag usage counts |
| Automation rule CRUD + active/inactive | pass | `load_automation_rules`; `automation.toggle` proposal flips `active` |
| Rules saved as declarative files + gate execution | pass | `agents/project/automation/rules/*.json` executed by `automation_rules_gate.py` in the chain |
| Triage collection (unclassified/overdue/long-blocked) | pass | `build_triage` (computed-only, done tasks excluded) |
| Proposal-only command path | pass | all CRUD writes go to `.ui_outbox/**`; no console-side canonical write |
| Tokenized label colors | pass | `_label_color_token` maps any input to a fixed palette; CSS resolves `var(--token)` only |
| Gate off-by-default safe | pass | 0 rules => pass, 0 executed; stop-hook approve path unaffected |

## Insight

### Boundary design

- **Read vs. write.** Definitions live in declarative files
  (`agents/project/ui/custom-properties.json`, `agents/project/ui/labels.json`,
  `agents/project/automation/rules/*.json`). `ui_state` only READS them and joins
  computed facts (label usage counts from task tags, triage reasons from task
  status/dates). The console never writes a canonical file: every property/label/
  rule mutation is a proposal under `.ui_outbox/{properties,labels,automation}`,
  consumed later by a runtime executor (mirroring the existing meeting/planning
  proposal pattern).

- **CRUD vs. execution.** The UI does rule CRUD + the active/inactive toggle
  only. Rule EXECUTION is owned by `scripts/automation_rules_gate.py`, which runs
  inside `owner_governance_gate.py`. This keeps a single execution point and
  reuses the gate-chain trust model rather than letting the console act.

### Tokenization (label colors never become raw CSS)

User-supplied label colors are a classic CSS-injection vector. Both
`ui_state._label_color_token` and `ui_commands._label_color_token` normalize ANY
input (including `"red; background:url(evil)"` or `"javascript:alert(1)"`) to one
of ten fixed semantic tokens that already exist in BOTH theme blocks. The JS only
ever emits `data-color="<token>"`, and the CSS resolves each token via
`var(--token)`. Net effect: the global tokenization guard stays green and no raw
or user CSS can reach the DOM.

### Off-by-default safety

The automation gate is the riskiest addition because it joins the
owner-governance chain that the stop hook depends on. It is no-op-safe by
construction: no rules directory => pass with `rules_total=0`; inactive rules
skipped; invalid rules reported as `watch` findings (never `block`); `--check`
only fails on `block` findings, which the gate never emits for "rules exist".
Side effects (`board_regen`, event log append) require `--apply`, which the chain
does not pass. Verified `scripts/owner_governance_gate.py` returns 0 and
`tests/test_stop_hook_owner_governance.py` still approves with `findings=0`.

## Decision

- Decision: persist automation rules as one declarative JSON file per rule so the
  gate can load/execute them independently and the UI toggle is a single-field
  proposal.
- Decision: model label colors as a fixed token palette (not free-form) so the
  feature can never widen the CSS attack surface or break the tokenization gate.
- Decision: keep rule execution in the gate chain (`--apply` opt-in) rather than
  in the console, preserving the read-only/proposal-only console contract.

## Verification

- `pytest tests/test_ui_console.py tests/test_ui_state.py tests/test_ui_commands.py tests/test_ui_extensions.py tests/test_automation_rules_gate.py tests/test_owner_governance_chain_parity.py tests/test_stop_hook_owner_governance.py` -> all pass.
- `node --check` on served `/app.js` -> exit 0.
- Tokenization guard logic over served `/app.css` -> 0 raw-color violations.
- `python scripts/owner_governance_gate.py` -> 0 (automation gate passes in-chain).
