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

- Action Board: 재발굴 루프 규칙·주기는 TASK-AR-360에서 구현. 신규 보류 결정은 반드시 본 레지스트리에 추가.
- Next: revisit_after 도래 항목을 retro/planning scan이 Owner 제안으로 재상정.
