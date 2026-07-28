# Compound Log (Legacy Read-only Fallback)

이 파일은 기존 설치의 과거 기록을 검색하기 위한 읽기 전용 호환 경로다. 새 반복
실패·재발 패턴은 이 단일 파일에 추가하지 않고
`agents/project/knowledge/compounds/records/COMPOUND-*.json`에
`python scripts/compound_record.py create ...`로 기록한다. 생성된
`agents/project/knowledge/compounds/INDEX.json`은 직접 편집하지 않는다.

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

<!-- Legacy records may remain below. Do not append new records here. -->
