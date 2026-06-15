# IDEA VAULT — 보류 아이디어 보존·재발굴 레지스트리

- Bottom Line: 기각·보류된 아이디어를 폐기하지 않고 부활 조건과 재검토 기한과 함께 보존한다. 주기 재발굴 루프가 기한 도래분을 Owner 제안으로 재상정하고, 채택 시 프로세스 A/B 실험으로 검증한다 (운영 규칙은 TASK-AR-360에서 확정).
- Signal: 선행 사례 — Pivotal Tracker Icebox, ADR `superseded`, Linear Archive vs Delete, Readwise resurfacing, Google SRE postmortem 보존 문화.
- Insight: RSI 루프의 입력 소스다 — 과거 결정을 잊지 않고 재평가하는 것이 자가 개선의 전제다.
- Decision: 항목 스키마 — `shelved_at`, `shelved_reason`, `origin_ref`(결정 기록), `revisit_after`(재검토 기한), `revival_criteria`(부활 조건), `status: shelved | revived | retired`.

## Entries

| id | idea | shelved_at | shelved_reason | origin_ref | revisit_after | revival_criteria | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IV-001 | Cycles/스프린트 | 2026-06-11 | milestone 체계와 개념 중복 | RESEARCH-2026-06-11-console-platform-feature-research §4 | 2026-09-01 | Roadmap(AR-325) 운영 후 주기 단위 필요 입증 | shelved |
| IV-002 | 워크플로(상태 집합) UI 편집 | 2026-06-11 | STATE-MACHINES.yml SSoT 원칙, 거버넌스 리스크 | 같은 문서 §2-B | 2026-09-01 | 상태머신 뷰어(AR-336) 사용 후 편집 수요 확인 | shelved |
| IV-003 | 위키 문서 UI 직접 편집 | 2026-06-11 | owner-doc 포맷 게이트와 충돌 위험 | 같은 문서 §2-C | 2026-09-01 | 포맷 게이트의 UI 내 통합 설계 완성 | shelved |
| IV-004 | 외부 캘린더 동기화(Google) | 2026-06-11 | 외부 서비스 연동 승인 경계 | 같은 문서 §2-D | 2026-10-01 | Owner의 외부 연동 승인 + 로컬 캘린더(AR-335) 안착 | shelved |
| IV-005 | 에이전트 인스턴스 스폰/중지 UI | 2026-06-11 | RBAC(AR-312)·C-mode 거버넌스 선행 필요 | 같은 문서 §2-F | 2026-10-01 | RBAC 게이트 가동 + C-mode 경계 결정 | shelved |
| IV-006 | 계정/멀티유저 + 커뮤니티 + 레벨 랭킹 | 2026-06-11 (확장 2026-06-12) | 로컬 단일 사용자 원칙(브리프 §15); 계정·서버·프라이버시 전제가 큼 | RESEARCH-2026-06-12-paperclip-and-doc-to-plan §4 | 2026-12-01 | 외부 공유/팀 사용 요구 발생; Paperclip Identity 모델(board user, agent API key, JWT)을 참조 설계로 사용 | shelved |
| IV-012 | 유저 간 리더보드 (저토큰·고성숙도 등 다요소 랭킹) | 2026-06-12 | IV-006(계정) 선행 필요; 다요소 지표는 AR-368이 먼저 구축 | 같은 문서 §4 | 2027-01-01 | IV-006 부활 + AR-368 실측 지표 안착 | shelved |
| IV-007 | KakaoTalk 알림톡 연동 | 2026-06-11 | 발신프로필(사업자)·템플릿 사전 심사 진입장벽 | RESEARCH-2026-06-11-interactive-gamification §1-D | 2026-10-01 | 사업자 등록 또는 개인 채널 대안 검증; 우선 Telegram/Discord(AR-365) | shelved |
| IV-008 | 오피스 맵 경로탐색 이동 애니메이션 | 2026-06-11 | 비용 대비 후순위 — 정적 맵+글리프가 먼저 | 같은 문서 §1-A | 2026-11-01 | 2D 맵(AR-364) 안착 + 성능 여유 확인 | shelved |
| IV-009 | 에이전트 음성/TTS 발화 | 2026-06-11 | 효용 미검증, 소음 리스크 | 같은 문서 §2 | 2026-12-01 | 회의실(AR-361) 사용 패턴에서 수요 확인 | shelved |
| IV-010 | 모바일 푸시 전용 앱 | 2026-06-11 | 웹훅→메신저 알림으로 충분 | 같은 문서 §1-D | 2026-12-01 | 메신저 알림(AR-365)의 한계 입증 | shelved |
| IV-011 | Gather식 Webhook Objects(공간 내 알림 객체) | 2026-06-11 | 맵 뷰 자체가 미구현 | 같은 문서 §1-A | 2026-11-01 | 2D 맵(AR-364) 출시 후 | shelved |
| IV-013 | 완전 멀티테넌시 데이터 격리 (vs 현 멀티호스트) | 2026-06-15 | 현 멀티호스트(AR-341/554) 충분; 완전 테넌트 격리는 별도 대형 보안 모델 (YAGNI) | REVIEW-2026-06-15-paperclip-gap-adoption-decision §axis3 | 2027-01-01 | 실제 멀티테넌트 요구 발생(외부/팀 공유) | shelved |
| IV-014 | out-of-process 플러그인 워커 (vs 선언적 위젯) | 2026-06-15 | 새 비신뢰 코드 실행 경계(샌드박스·권한범위·공급망 검토 필요); 선언적 위젯(AR-341)이 더 안전 | REVIEW-2026-06-15-paperclip-gap-adoption-decision §axis4 | 2027-01-01 | 마켓플레이스 수요 + 샌드박스 설계 완성 | shelved |

- Action Board: 재발굴 루프 규칙·주기는 TASK-AR-360에서 확정 (아래 운영 규칙). 신규 보류 결정은 반드시 본 레지스트리에 추가.
- Next: revisit_after 도래 항목을 retro/planning scan이 Owner 제안으로 재상정 (`scripts/planning_loop.py scan` → `idea-vault-revival-due` finding).

## Operating Rules (TASK-AR-360 확정)

레지스트리(위 표)가 SSoT다. 도구 `scripts/idea_vault.py`가 표를 읽고/갱신한다 (수동 표 편집도 허용 — 단 컬럼 8개·형식 유지).

### Entry Schema (표 컬럼 = 항목 스키마)

| 컬럼 | 의미 | 형식 |
| --- | --- | --- |
| `id` | 고유 식별자 | `IV-NNN` (3자리) |
| `idea` | 아이디어 요약 (summary) | 자유 텍스트 |
| `shelved_at` | 보류 일자 | `YYYY-MM-DD` |
| `shelved_reason` | 보류 사유 (rejected_reason) | 자유 텍스트 (비어 있으면 안 됨) |
| `origin_ref` | 결정 기록 출처 | 문서/리서치 참조 |
| `revisit_after` | 재검토 기한 | `YYYY-MM-DD` |
| `revival_criteria` | 부활 조건 | 자유 텍스트 (비어 있으면 안 됨) |
| `status` | 생애주기 상태 | `shelved` \| `revived` \| `re-deferred` \| `adopted` \| `retired` |

### Status 생애주기

- `shelved` — 활성 보류, `revisit_after` 도래 대기.
- `revived` — 재발굴 제안이 발행됨 (재평가/A·B 진행 중). `idea_vault.py revive <id>`가 설정.
- `re-deferred` — 재평가 후 새 `revisit_after`로 재보류. `idea_vault.py defer <id> --until <date>`가 설정.
- `adopted` — 정규 작업으로 승격 (결정 이력 보존; revive 불가).
- `retired` — 영구 폐기 (결정 이력 보존; revive 불가).

활성(active) 상태 = `shelved`, `re-deferred`. `due`/scan은 활성 항목 중 `revisit_after <= now`만 재상정한다.

### Commands (`scripts/idea_vault.py`)

- `list` — 전체 항목 출력.
- `due [--now YYYY-MM-DD]` — `revisit_after` 도래 활성 항목 출력. 읽기 전용, **항상 exit 0**.
- `revive <id>` — **제안 전용**. planning outbox에 B-mode owner 제안(`origin_type: idea_vault_revival`, `proposal_output: owner_decision`)을 발행하고 항목을 `revived`로 표시한다. **절대 task를 자동 생성하지 않는다.** `adopted`/`retired`(종결) 항목은 거부. 이미 `revived`인 항목에 재실행하면 동일 제안을 덮어써 멱등(idempotent)이다 (`revived`는 active가 아니므로 scan이 다시 재상정하지 않음).
- `defer <id> --until <date>` — `revisit_after`를 갱신하고 `re-deferred`로 표시. `adopted`/`retired`(종결) 항목은 거부 — 결정 이력은 영구 보존된다.
- `validate` — 레지스트리 스키마 검증 (id 형식·중복, status 허용값, 날짜 형식, 필수 컬럼).

### 재발굴 루프 연동

`scripts/planning_loop.py scan`이 `_scan_idea_vault`로 도래 항목을 `idea-vault-revival-due` finding(risk_tier `owner`, 비차단)으로 surface한다. 이 finding은 Owner 제안 경로로만 흐르며 canonical mutation을 일으키지 않는다 (scan status는 `pass` 유지 — high-risk가 아님).

### 신규 보류 게이트 (체크리스트)

새로 기각·보류하는 모든 아이디어는 task 종료/제안 거부 전에 본 레지스트리에 한 행을 추가해야 한다: `id`, `idea`, `shelved_at`, `shelved_reason`, `origin_ref`, `revisit_after`(기본 +3개월 권장), `revival_criteria`, `status: shelved`. 폐기 대신 보존이 RSI 원칙이다.

## A/B Experiment Protocol (부활 시 검증 규약)

부활 제안이 Owner 승인으로 채택될 때, 곧바로 정규 작업으로 굳히지 않고 **한 번에 한 변수**만 바꾸는 짧은 A/B 실험으로 검증한다 (Measured Improvement 원칙과 통합).

1. **One variable** — 이번 부활로 바꾸는 단일 변수를 명시 (예: "회의실 사용 시 TTS on/off"). 두 개 이상 변수는 분리해 별도 실험.
2. **Metric** — 채택/재보류를 가를 측정 지표 하나 (예: 토큰/작업, 회의 합의 도달 시간, Owner 개입 횟수). 사전에 baseline(A) 값을 기록.
3. **Period** — 짧은 고정 기간 (기본 1주 또는 N 사이클). 기간 종료 전 결론을 내지 않는다.
4. **Decision** — 기간 종료 시 A(현행) vs B(부활안) 지표를 비교: 개선이면 `adopted`(정규 작업 승격), 아니면 `re-deferred`(새 `revisit_after`와 함께 재보류) — 어느 쪽이든 결과는 레지스트리에 반영.

부활 제안 JSON은 `ab_experiment` 블록(`protocol`, `status`, `one_variable`, `metric`, `period`, `decision`)을 운반하며, 본 절(`#ab-experiment-protocol`)을 참조한다.

### 선행 사례 매핑 (Acceptance Criteria)

| 패턴 | 본 레지스트리 대응 |
| --- | --- |
| Pivotal Tracker Icebox | `status: shelved` 항목 (활성 보류, 미일정) |
| ADR `superseded` | `status: retired`/`adopted` (결정 이력 보존, revive 불가) |
| Linear Archive vs Delete | 표에서 행 삭제 금지 — 항상 status 전이로 보존 |
| Readwise resurfacing | `revisit_after` 도래 → scan이 주기 재상정 |
| Google SRE postmortem 보존 | 신규 보류 게이트 = 결정을 잊지 않고 기록 |
