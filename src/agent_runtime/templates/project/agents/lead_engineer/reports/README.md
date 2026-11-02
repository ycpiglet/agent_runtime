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

새 Owner/CEO 작업 보고의 기본 프로필은 `report_layout: compact-v1`이다.
보관 시 위 식별·출처 필드를 유지하고 `signal: pass|watch|block`을 추가한다.
`score`는 선택이며 실제 원본 수치와 `score_source`가 있을 때만 쓴다.
생성기 출력의 최소 frontmatter만으로 보관 필수 필드가 채워졌다고 보지 않는다.
`save_report.py --body-file`에는 생성기의 compact 문서 전체를 전달한다.
검증 후 프로필·상태·원본 점수 필드를 보관 메타데이터에 한 번만 합친다.
알 수 없는 프로필·중복 필드·잘못된 compact 본문은 저장 전에 거부한다.

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

- `compact-v1` 본문은 H1 제목과 `> **한 줄 결론**`으로 시작한다.
  `현재 상태` → `다음 행동` → `한도와 미확인` → `검증 근거` 순서를 지킨다.
  첫 층의 미확인·미실행·한도·승인 경계는 항상 보인다. 상세 한도는
  [REPORTING-FORMAT.md](../REPORTING-FORMAT.md) §새 Owner 작업 보고 기본값 참조.
- 기존 프로필의 `Owner`/`CEO`/`mixed` 보고만 `Bottom Line:`으로 시작한다.
  compact-v1에서는 6개 절·표·Insight/Decision·점수를 강제하지 않는다.
  과거 보고를 일괄 변환하거나 증빙·보관 색인을 제거하지 않는다.
- 장식용 이모지 금지 — 상태 표시는 O/X/체크박스 또는 G/Y/R 텍스트 라벨 사용
  (REPORTING-FORMAT.md §이모지정책).
