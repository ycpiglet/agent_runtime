# CALL: TASK-AR-205 Offline Eval Follow-up

## Summary

Offline eval has moved from conceptual requirement to executable gate. The current result is `block`, and that is the correct release signal.

## Notes

- The 90% threshold is only meaningful if the goldset includes policy-required case diversity.
- Missing query contract metadata prevents interpretation of failures.
- The correction loop should treat missing goldset metadata as a correction proposal owned by Lead Engineer/Data Steward.

## Next Action

Expand `overlay-routing-v1.jsonl` and `gov-metadata-v1.jsonl`, then rerun the gate before live reviewer lane is treated as release-ready.
