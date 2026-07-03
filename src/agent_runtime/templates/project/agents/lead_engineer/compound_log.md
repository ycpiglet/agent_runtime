# Compound Log

반복 실패·재발 패턴을 누적하는 학습 로그. 같은 실수/비판이 재발하면 산문 리마인더로
끝내지 않고 여기 `COMPOUND-*` 항목으로 기록하고, 가능하면 실행 가능한 방지책
(게이트/훅/체크리스트/스크립트)으로 승격한다 (AGENTS.md §Measured Improvement).

## 항목 형식

```markdown
## COMPOUND-YYYY-MM-DD-NNN: <제목>

### Bottom Line
- 무엇이 재발했고, 왜 규칙만으로 못 막았는지 한두 줄.

### 5W1H
| Field | Record |
|---|---|
| Who / What / When / Where / Why / How | ... |

### Cause
- 근본 원인과 부차 원인.

### Prevention
- 도입한 실행 가능한 방지책 (게이트/훅/테스트/스크립트 경로).
```

<!-- 아래에 최신 항목을 위로 누적한다. -->
