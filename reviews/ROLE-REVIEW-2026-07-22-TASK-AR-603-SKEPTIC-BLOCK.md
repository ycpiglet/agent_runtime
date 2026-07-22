---
title: TASK-AR-603 Skeptic Adversarial Review - Unicode Token Boundary
date: 2026-07-22
signal: fail
task_id: TASK-AR-603
verified_head: 7c53fcfa56ae299321a9e23a383593011055e71c
verified_by: codex-task-ar-603-skeptic-20260722
role: skeptic
verdict: BLOCK
tags: [task-ar-603, skeptic, adversarial-review, task-id-contract, unicode-boundary]
---

# TASK-AR-603 Skeptic Adversarial Review - BLOCK

## Verdict

**BLOCK** at exact HEAD `7c53fcfa56ae299321a9e23a383593011055e71c`.

The shared token pattern rejects ASCII letters, digits, `_`, and `-` around a
canonical-looking ID, but it accepts the same ID when embedded in a larger
Unicode word. This violates the stated larger-token boundary contract and can
turn ordinary Korean prose into a blocking false task reference.

## Blocking Counterexample

The root and template copies of `TASK_ID_TOKEN_RE` both return a partial match
for every example below:

```text
éTASK-AR-1        -> TASK-AR-1
TASK-AR-1é        -> TASK-AR-1
작업TASK-AR-1     -> TASK-AR-1
TASK-AR-1작업     -> TASK-AR-1
αTASK-1β          -> TASK-1
```

The cause is the ASCII-only boundary class in both shared contract files:

```python
(?<![A-Za-z0-9_-]) ... (?![A-Za-z0-9_-])
```

Python treats the adjacent characters above as Unicode word/alphanumeric
characters, but this class does not. Root/template parity therefore preserves
the same defect on both surfaces.

## Consumer Impact Reproduction

An isolated temporary fixture containing this planning action was analyzed:

```markdown
| Next | 작업TASK-AR-999 후속 |
```

Observed result:

```text
conversation_findings [('block', 'missing-task-file',
  'references TASK-AR-999 but agents/lead_engineer/tasks/TASK-AR-999.md does not exist')]
taskset_body_order ['TASK-AR-999']
```

Expected under the larger-token contract: no task-ID token is extracted from
`작업TASK-AR-999`. The conversation audit must not emit a missing-task-file
block for it, and taskset body parsing must not add it to task order.

Reproduction matrix command:

```powershell
$env:PYTHONIOENCODING='utf-8'
@'
import importlib.util
from pathlib import Path

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

for name, path in (
    ('root', Path('scripts/task_id_contract.py')),
    ('template', Path('src/agent_runtime/templates/project/scripts/task_id_contract.py')),
):
    contract = load(name, path)
    for text in ('éTASK-AR-1', 'TASK-AR-1é', '작업TASK-AR-1',
                 'TASK-AR-1작업', 'αTASK-1β'):
        print(name, text, contract.TASK_ID_TOKEN_RE.findall(text))
'@ | python -
```

## Independent Regression Results

The declared checks all pass, showing that current coverage does not exercise
the blocking Unicode boundary case:

- Focused suite: `99 passed in 31.08s`
- `python scripts/task_identity.py check --check`: pass, findings 0
- `python scripts/conversation_work_audit.py --check`: pass, findings 0
- `python scripts/taskset_work_gate.py --check`: pass, findings 0
- `python scripts/work_item_classifier.py --check`: pass, findings 0
- `python scripts/regen_host_lock_if_needed.py --check`: pass, lock current

The broader adversarial matrix otherwise passed: seven valid values were
accepted, twelve invalid values including the no-AR timestamp form were
rejected, ten ASCII embedded-token cases were rejected, suffix case was
preserved, and ordinary punctuation-delimited tokens were extracted.

## Parity And Evidence Lineage

- `scripts/task_id_contract.py`, `scripts/taskset_dispatcher.py`, and
  `scripts/conversation_work_audit.py` are byte-identical to their template
  counterparts.
- Fix commit `9203a1b` is the direct parent of refreshed W4a evidence commit
  `5942633`; current HEAD `7c53fcf` is its documentation-only descendant.
- The refreshed task/unit W4a records contain successful 99-test and host-lock
  results. The prior independent W4b verifies `5942633` but does not cover the
  Unicode boundary counterexample.

## Required Correction

Use a Unicode-aware word boundary contract that still treats `_` and `-` as
token constituents, mirror it in the template, and add root/template consumer
tests proving Unicode-adjacent forms are rejected while punctuation-delimited
numeric and timestamp IDs continue to work. Refresh W4a and repeat independent
review at the corrected exact HEAD.
