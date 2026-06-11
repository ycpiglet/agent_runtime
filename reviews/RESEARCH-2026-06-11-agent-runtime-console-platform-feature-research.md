# RESEARCH-2026-06-11 — Console Platform Feature Research (시중 플랫폼 전수 분석)

- Bottom Line: Notion/Linear/Jira/Asana/ClickUp/Monday/Slack/Discord/Miro/Motion/Obsidian/Sentry/Grafana의 기능을 11개 카테고리로 전수 분석해 agent_runtime 콘솔 적용 후보 60여 개를 도출했고, 그중 33개를 13개 태스크(TASK-AR-329~341)로 압축해 `TASKSET-AR-UI-PLATFORM-EXTENSIONS`로 등록한다.
- Signal: V2(TASK-AR-320~328)가 "보는/지시하는 컨트롤룸"이라면 본 확장은 "관리·확장·운영 플랫폼"으로의 승격이다. 기존 등록(317 승인 워크플로, 318 리플레이)과 중복 없이 보완한다.
- Insight: 시중 플랫폼 기능의 80%는 본질이 5가지다 — ① 구조 편집(CRUD·이동·벌크), ② 속성/자동화, ③ 콘텐츠 인입·반출(파일/검색/import·export), ④ 시간축(캘린더/타임라인/알림), ⑤ 시각화·게임화. agent_runtime은 여기에 고유 축인 ⑥ 에이전트 운영(팀 배정·비용·게이트)을 더해야 차별화된다.
- Decision: 전부 등록하되 우선순위는 P1(구조 편집·검색·첨부) → P2(캘린더·자동화·대시보드) → P3(게임화·확장 포인트) 순. 구현 시점은 V2 Phase A~C와 인터리브 가능.

## 1. 벤치마크 대상과 핵심 강점

| 플랫폼 | 가져올 핵심 |
| --- | --- |
| Notion | DB 뷰(테이블/보드/캘린더/갤러리), 속성 시스템, 페이지 위키+백링크, import/export, 첨부, 템플릿 |
| Linear | 키보드 우선, 트리아지, Cycles, Projects/Milestones, 자동화(auto-archive, SLA), 의존성, 워크플로 상태 커스텀 |
| Jira | 워크플로 엔진(상태머신 편집), 벌크 편집, JQL형 고급 필터, 권한 스킴 |
| Asana / ClickUp / Monday | 타임라인(Gantt), 워크로드/용량 뷰, 자동화 레시피("when status→done then …"), 커스텀 필드, 반복 작업 |
| Slack / Discord | 채널·스레드·멘션·핀·리액션, 알림 정책(mute/keyword), 검색 연산자 |
| Miro / FigJam | 무한 캔버스 그래프, 노드 직접 배치, 미니맵 |
| Motion / Notion Calendar | 일정 자동 배치, 회의·작업 통합 캘린더, 리마인더 |
| Obsidian | 로컬 파일 기반 지식 그래프(본 프로젝트의 reviews/ 구조와 동형), 그래프 뷰 |
| Sentry / Grafana | 운영 대시보드(추이 차트), 알림 임계값, 이슈 트리아지 흐름 |
| 온라인 RPG (Owner 비전) | 프레즌스, XP/레벨, 퀘스트 보드 은유, 완료 셀레브레이션 |

## 2. 카테고리별 기능 분석 → 적용 판정

판정: ✅ 등록(태스크), 🔁 기존 등록과 중복(참조), ⏸ 보류(사유).

### A. 구조 편집 — Taskset/Task 라이프사이클 (Owner 예시 요구)

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| UI에서 taskset 생성/이름변경/보관 | Linear Projects, Notion DB | ✅ AR-329 |
| task를 taskset 간 드래그 이동/소속 변경 | Linear, Jira | ✅ AR-329 |
| 멀티선택 + 벌크 편집(상태/우선순위/담당 일괄) | Jira, Linear | ✅ AR-329 |
| 실행 취소(undo) 토스트 | Linear, Gmail | ✅ AR-329 |
| task/taskset 템플릿 (반복 패턴 1클릭 생성) | Notion, Asana | ✅ AR-329 |
| 서브태스크 계층 | 전부 | ✅ AR-330 |
| 의존성(blocks/blocked-by) + 의존 그래프 | Linear, Jira | ✅ AR-330 |
| 타임라인(Gantt) 뷰 | Asana, ClickUp, Monday | ✅ AR-330 |
| Cycles/스프린트 | Linear | ⏸ 보류 — 릴리스/milestone(AR-325)로 충분, 중복 개념 |

### B. 속성/워크플로 자동화

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| 커스텀 속성(필드) — 텍스트/선택/숫자/날짜 | Notion, ClickUp | ✅ AR-331 (frontmatter 확장으로 자연 구현) |
| 라벨/태그 관리 UI | 전부 | ✅ AR-331 |
| 자동화 규칙 "when X then Y" (상태→done 시 보드 재생성, blocked 3일 경과 시 에스컬레이션 등) | Monday, ClickUp, Linear | ✅ AR-331 — 단 실행은 기존 게이트/훅 체계 경유, UI는 규칙 편집기만 |
| 워크플로(상태 집합) 커스텀 편집 | Jira | ⏸ 보류 — STATE-MACHINES.yml이 SSoT, UI 편집은 거버넌스 리스크. 뷰어만(AR-336) |
| SLA/트리아지 큐 | Linear Triage | ✅ AR-331에 포함 (미분류/지연 task 자동 큐) |

### C. 콘텐츠 — 파일/문서/검색/입출력 (Owner 예시 요구)

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| 파일 첨부 업로드(이미지·문서, 드래그드롭, 스크린샷 붙여넣기) | Notion, Slack, Jira | ✅ AR-332 — evidence 디렉토리 연동, task/메시지에 첨부 |
| 첨부 다운로드/미리보기(이미지 라이트박스, md 렌더) | Notion | ✅ AR-332 |
| 내보내기: taskset/보드 → Markdown/CSV/JSON, 전체 백업 번들 | Notion, Jira | ✅ AR-333 |
| 가져오기: md/CSV → task 일괄 등록 | Notion, Trello | ✅ AR-333 |
| 전역 풀텍스트 검색(task/문서/메시지/이벤트/리뷰) + 빠른 열기(Ctrl+P) | Notion, Slack 연산자 | ✅ AR-334 |
| 위키 페이지 편집(UI에서 reviews/ 문서 직접 편집) | Notion, Confluence | ⏸ 보류 — owner-doc 포맷 게이트와 충돌 위험, 읽기+링크 우선. 후속 검토 |
| 문서 버전 이력 | Notion | 🔁 git이 이미 SSoT — UI는 커밋 링크 표면화(AR-334 검색 결과에 포함) |

### D. 시간축 — 캘린더/스케줄링 (Owner 예시 요구)

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| 캘린더 뷰(마일스톤·회의·완료 이력·예약 실행) | Notion Calendar, Asana | ✅ AR-335 |
| 예약 실행(cron) — taskset 디스패치 예약, 반복 작업 | Motion, ClickUp | ✅ AR-335 |
| 리마인더/마감일 경고 | 전부 | ✅ AR-335 (알림 센터 AR-338과 연동) |
| 외부 캘린더 동기화(Google) | Notion Calendar | ⏸ 보류 — 외부 서비스 연동은 Owner 승인 경계 밖, 로컬 우선 |

### E. 시각화/관측 (Owner 예시: 상태머신)

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| 상태머신 인터랙티브 뷰어(STATE-MACHINES.yml 그래프 + 개별 task 현재 상태 하이라이트) | Jira workflow viewer, XState viz | ✅ AR-336 |
| 운영 대시보드: 토큰/비용 추이, eval 점수, 게이트 pass/watch/block 보드, 번다운/속도 | Grafana, Sentry, Linear Insights | ✅ AR-339 |
| 워크로드 히트맵(에이전트별 부하) | Asana Workload | ✅ AR-337 |
| 리플레이/타임 스크러버 | — | 🔁 TASK-AR-318 기등록 |
| 라이브 그래프 | rqt, Miro | 🔁 TASK-AR-326 기등록 |

### F. 에이전트 운영 (본 프로젝트 고유, Owner 예시: 팀별 할당)

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| taskset → 팀/역할 배정(assignee를 개인이 아닌 팀으로), 팀 용량 뷰 | Jira 컴포넌트, Asana 팀 | ✅ AR-337 |
| 에이전트 인스턴스 스폰/중지 UI("채용") | 고유 | ⏸ 보류 — C-mode 경계와 연관, 거버넌스 결정 선행 (TASK-AR-312 RBAC 이후) |
| 승인 큐(파괴적 작업 대기열) | 고유+brief §13.4 | 🔁 TASK-AR-317 Planner 승인 워크플로 기등록 |
| task당 토큰/비용 예산 표시 | 고유 | ✅ AR-339에 포함 |

### G. 커뮤니케이션 보강

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| @멘션(에이전트/역할), 핀, 리액션 | Slack | ✅ AR-338에 포함 (채널 자체는 AR-327) |
| 알림 센터(인앱) + mute/키워드 규칙 + 데일리 브리프 | Slack, Linear Inbox | ✅ AR-338 |

### H. UX 폴리시/게임화/확장성

| 기능 | 출처 | 판정 |
| --- | --- | --- |
| 마이크로인터랙션: 상태 전이 애니메이션, 드래그 물리감, 스켈레톤 로딩, 낙관적 업데이트 | Linear, Notion | ✅ AR-340 |
| taskset 완료 셀레브레이션(컨페티), 에이전트 XP/레벨/스트릭, 퀘스트 보드 모드 | RPG, Asana 유니콘 | ✅ AR-340 — 토글 가능(진지 모드 기본) |
| 사운드 이펙트(완료음 등, 기본 off) | Discord | ✅ AR-340 |
| 온보딩 투어/빈 상태(empty state)/컨텍스트 도움말 | 전부 | ✅ AR-340 |
| 멀티 프로젝트 워크스페이스 스위처(autofolio 등 호스트 프로젝트 전환) | Notion 워크스페이스, Slack 워크스페이스 | ✅ AR-341 — sync/템플릿 체계가 이미 멀티 호스트 전제 |
| 위젯/확장 포인트(대시보드 카드 플러그인), 단축키 커스텀 | Notion 위젯, Raycast | ✅ AR-341 |
| i18n (KR/EN) | 전부 | ✅ AR-341 |
| 멀티유저/인증 | 전부 | ⏸ 보류 — brief §15 "로컬 단일 사용자 우선" 원칙 유지 |

## 3. 등록 태스크 요약 (TASKSET-AR-UI-PLATFORM-EXTENSIONS)

| Task | 제목 | P |
| --- | --- | --- |
| AR-329 | Taskset 라이프사이클 UI (생성/보관/이동/벌크/undo/템플릿) | P1 |
| AR-330 | 서브태스크·의존성 모델 + 타임라인(Gantt)·의존 그래프 | P1 |
| AR-331 | 커스텀 속성·라벨 + 자동화 규칙 편집기 + 트리아지 큐 | P2 |
| AR-332 | 파일 첨부 (업로드/다운로드/미리보기, evidence 연동) | P1 |
| AR-333 | 가져오기/내보내기 (md/CSV/JSON, 백업 번들) | P2 |
| AR-334 | 전역 검색 + 빠른 열기 (커밋 링크 표면화 포함) | P1 |
| AR-335 | 캘린더/스케줄링 (예약 디스패치, 반복, 리마인더) | P2 |
| AR-336 | 상태머신 인터랙티브 뷰어 | P2 |
| AR-337 | 팀/역할 배정 모델 + 워크로드 히트맵 | P1 |
| AR-338 | 알림 센터 + 멘션/핀/리액션 + 데일리 브리프 | P2 |
| AR-339 | 운영 대시보드 (토큰/비용·eval·게이트·번다운) | P2 |
| AR-340 | 마이크로인터랙션/게임화 폴리시 (토글형) | P3 |
| AR-341 | 워크스페이스 스위처 + 위젯 확장 포인트 + i18n | P3 |

## 4. 보류 항목 (재검토 조건 포함)

- Cycles/스프린트: milestone 체계와 중복 — Roadmap(AR-325) 운영 후 필요 시.
- 워크플로 UI 편집: STATE-MACHINES.yml SSoT 원칙 — 뷰어(AR-336) 사용 경험 후.
- 위키 직접 편집: owner-doc 포맷 게이트와의 통합 설계 후.
- 외부 캘린더/서비스 동기화: 외부 연동 Owner 승인 경계.
- 에이전트 스폰 UI: RBAC(AR-312)와 C-mode 거버넌스 선행.
- 멀티유저/인증: 로컬 단일 사용자 원칙 유지 중.

## 5. 우선순위 운영 제안

V2 Phase A(테마/IA/리스트)와 P1 확장(329, 330, 332, 334, 337)을 인터리브하면 "관리 가능한 콘솔"이 가장 빨리 완성된다. 게임화(340)는 마지막 — 구조 없는 이펙트는 소음이다.
