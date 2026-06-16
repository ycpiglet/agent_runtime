# TASK-AR-568 W4a Review - i18n KO/EN UI Toggle

## Bottom Line

TASK-AR-568 is ready for independent W4b verification.

## Scope

- Added KO/EN string resources for the decision-first cockpit, inbox group/action/why labels, and the work-state secondary hero.
- Added `data-i18n`, `data-i18n-aria-label`, and `data-i18n-title` anchors for the static UI text touched by the language toggle.
- Kept `/api/inbox` and `/api/work-state` schema/data values in English; only browser display labels are localized.
- Added dynamic render helpers for inbox title/why/action display and work-state bucket labels.
- Re-rendered cockpit and work-state surfaces when the language select changes.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 12 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_state.py -q` -> 103 passed.
- `PYTHONPATH=src python -m pytest tests/test_attention_inbox.py -q` -> 6 passed.

## Risk

- Unknown inbox `why` or `action` strings intentionally remain raw so the UI does not misrepresent data outside the known mapping contract.
- The work-state hero localization is display-only and preserves task ids, taskset ids, and bucket source values outside the visible label.
