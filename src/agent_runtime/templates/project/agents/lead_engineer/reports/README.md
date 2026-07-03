# Reports Archive (BRIEF / PLAN)

BRIEF/PLAN 응답의 자동 보관 디렉토리. 대화 출력으로 끝내지 않고 이 디렉토리에
`BRIEF-YYYY-MM-DD-NNN.md` / `PLAN-YYYY-MM-DD-NNN.md`로 누적 저장한다.
운영 규칙은 [../REPORTING-FORMAT.md](../REPORTING-FORMAT.md) §자동 보관, 무결성 검사는
`python scripts/check_agent_docs.py`가 수행한다.

## 파일 규칙

- 파일명: `{BRIEF|PLAN}-YYYY-MM-DD-NNN.md` (NNN은 같은 kind+날짜 안에서 3자리 시퀀스, 중복 금지)
- 파일명 stem == frontmatter `id`
- 모든 리포트는 [INDEX.md](INDEX.md)에 시간 역순으로 양방향 등재한다
  (파일만 있고 INDEX에 없거나, INDEX에만 있고 파일이 없으면 검사 실패).
- `VIEW-*.md`는 자동 생성 파생 뷰로 frontmatter 검사 대상이 아니다.

## Frontmatter 스키마

필수 키: `type`, `id`, `kind`, `date`, `recorded_at`, `audience`, `scale`, `title`,
`author`, `insights_count`, `decisions_count`.

| 키 | 허용값/형식 |
|---|---|
| `type` | `report` (고정) |
| `id` | `{BRIEF\|PLAN}-YYYY-MM-DD-NNN` |
| `kind` | `BRIEF` 또는 `PLAN` (`id`의 kind와 일치) |
| `date` | `YYYY-MM-DD` (`id`의 날짜와 일치) |
| `recorded_at` | ISO 8601 또는 `unknown` |
| `audience` | `Owner` / `CEO` / `agent` / `mixed` |
| `scale` | `mini` / `standard` / `full` |
| `insights_count`, `decisions_count` | 정수 |

## 본문 규칙

- `Owner`/`CEO`/`mixed` 대상 리포트는 본문이 `Bottom Line:`으로 시작해야 한다
  (Executive Layer 마커, REPORTING-FORMAT.md §보고 2-layer).
- 장식용 이모지 금지 — 상태 표시는 O/X/체크박스 또는 G/Y/R 텍스트 라벨 사용
  (REPORTING-FORMAT.md §이모지정책).
