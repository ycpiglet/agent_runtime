# TASK-AR-569 W4a Review - E2E + DOM Budget Regression

## Bottom Line

TASK-AR-569 is ready for independent W4b verification.

## Scope

- Added a server-backed E2E regression for the decision-first home budget.
- Counted initial served HTML elements and enforced the `<= 1500` DOM budget.
- Counted the decision shell before the work surface and enforced a compact `<= 320` element budget.
- Added Playwright desktop/mobile viewport coverage that asserts the default home document stays within two screens after the browser loads the shell and available hero data.
- Kept detailed board/work views behind explicit route/sidebar navigation and bounded the attention/work-state hero card regions so loaded runtime data cannot expand the default home document.
- Asserted progressive disclosure through exactly one active view plus CSS-hidden inactive views.
- Re-asserted maturity behavior preservation in the same E2E path: responsive CSS, accessibility landmarks/ARIA, SSE, KO/EN i18n, and validation signals.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 15 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.
- `git diff --check` -> passed.

## Risk

- Playwright is imported with `pytest.importorskip`; environments without Playwright still keep the DOM/maturity regression, while this checkout currently exercises the browser-height assertion.
