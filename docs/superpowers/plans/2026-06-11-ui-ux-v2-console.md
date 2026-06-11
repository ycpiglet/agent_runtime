---
title: Agent Runtime UI/UX V2 Plan (Owner Console)
status: proposed
date: 2026-06-11
task_set_id: TASKSET-AR-UI-UX-V2
owner_request: 2026-06-11 Owner UI/UX 기획 지시
---

# Agent Runtime UI/UX V2 Plan

- Bottom Line: 현재 콘솔은 "9개 탭 + Linear풍 다크 스타일링"까지 도달했다. V2는 ① Notion형 라이트 테마 기본 + 다크 토글, ② 사이드바 정보 구조, ③ 전 리스트 공통 정렬/필터/그룹/밀도 토글, ④ taskset 중심 작업 뷰, ⑤ 조직도/Vision/Roadmap, ⑥ SSE 기반 실시간 RPG 프레즌스 + rqt 라이브 그래프, ⑦ Slack형 채널 + meeting/seminar 명령, ⑧ taskset 경계 실행 가드를 추가해 "읽는 대시보드"를 "운영 컨트롤룸"으로 승격한다.
- Signal: 선행 작업(TASKSET-AR-UI-DESIGN-SYSTEM/IMPLEMENTATION)은 main에 반영 완료 — 단 범위가 CSS/시각 계층에 한정돼 있었다(DESIGN.md "DOM and API contracts must stay stable"). 기능적 UX는 본 계획이 첫 등록이다.
- Insight: 데이터는 이미 충분하다. `/api/state`가 tasks/task_sets/agents/messages/events/evidence/map/roadmap/planning을 모두 노출하므로 V2는 백엔드 신규 개발보다 **프런트 정보 구조와 실시간 레이어** 문제다.
- Decision: 테마 기본값을 다크 → 라이트(Notion형)로 전환하고 기존 다크 토큰은 Dark Mode로 보존한다 (DESIGN.md 결정 일부 개정).

## 1. 선행 작업 정리 (무엇이 반영됐고 무엇이 없나)

| 항목 | 상태 |
| --- | --- |
| Linear풍 다크 토큰, 카드 시각 계층(backlog/agent/command/audit/surface), 반응형/접근성 폴리시 | 반영됨 (AR-278~284, main) |
| 9탭 단일 페이지(Backlog/Agents/Messages/Events/Evidence/Planner/Map/Sources/Writes) | 반영됨 (기존 구조) |
| 사이드바 IA, 라이트 테마, 정렬/필터/그룹, 밀도 토글, taskset 그룹 뷰, 조직도, Vision/Roadmap, 실시간(SSE), 라이브 그래프, 채널/회의 | **미구현 — 본 계획 범위** |

## 2. 디자인 방향

### 2.1 테마 시스템 (Owner 결정 반영)

- 기본 테마: **Light (Notion형)** — 따뜻한 화이트 캔버스, 잉크 계열 텍스트, 낮은 채도 상태색, 종이 같은 문서감.
- Dark Mode: 기존 DESIGN.md Linear 토큰(`--canvas:#010102` 계열)을 그대로 다크 테마로 보존. 헤더 토글 + OS 선호 자동 감지.
- 구현 원칙: 모든 색을 시맨틱 토큰(`--canvas/--panel/--ink/--muted/--line/--primary/--success/--warning/--danger`)으로 이원화. 컴포넌트는 토큰만 참조.

라이트 토큰 초안:

```css
--canvas:#ffffff; --panel:#f7f7f5; --panel-strong:#f1f1ef;
--ink:#37352f; --muted:#787774; --subtle:#9b9a97;
--line:#e9e9e7; --line-strong:#d3d1cb;
--primary:#2e6fdb; --success:#0f7b55; --warning:#cb7509; --danger:#e03e3e;
```

### 2.2 정보 구조: 사이드바 (권고: 채택)

9개 수평 탭은 이미 포화 상태이고 V2 뷰 추가(조직도/Roadmap/채널)를 수용할 수 없다. Notion/Linear/Slack 공통 패턴인 **접이식 좌측 사이드바 + 그룹 섹션**으로 전환한다. Agent/Map을 사이드탭으로 빼자는 Owner 의견에 동의하며, 전체 뷰를 다음과 같이 그룹화한다:

```text
⌂ Home                      ← 대시보드 (현재 goal, 진행중 taskset, 주의 필요 항목)
WORK
  ▸ Tasksets                ← taskset 중심 뷰 (기본 진입점)
  ▸ Board                   ← 칸반 (기존 Backlog)
  ▸ Roadmap                 ← Vision / Objective / Milestone / Release
AGENTS
  ▸ Team                    ← 조직도 + 에이전트 카드 (RPG 프레즌스)
  ▸ Live Map                ← rqt형 라이브 그래프 (기존 Map 승격)
COMMS
  ▸ Channels                ← Slack형 메시지 (기존 Messages 승격)
  ▸ Meetings                ← 회의/세미나 소집 및 기록
RECORDS
  ▸ Events / Evidence / Sources
OPS
  ▸ Planner / Writes / Settings(테마·밀도·새로고침 주기)
```

- 사이드바는 접으면 아이콘 레일로 축소(Notion식), 현재 활성 taskset이 사이드바에 진행률과 함께 고정 노출.
- URL 해시 라우팅(`#/tasksets/TASKSET-AR-…`)으로 딥링크/뒤로가기 지원.

### 2.3 공통 인터랙션 패턴 (Notion/Linear 벤치마크)

| 패턴 | 출처 | 적용 |
| --- | --- | --- |
| 정렬/필터/그룹 바 | Notion DB, Linear | 모든 리스트 뷰 상단 공통 컴포넌트. 필터: 상태/우선순위/담당 에이전트/taskset/태그/날짜. 그룹: taskset(기본)·상태·담당. 정렬: 우선순위·갱신시각·진행률. 조건은 URL+localStorage에 저장 |
| 밀도 토글 (간략히/자세히) | Notion, Gmail | `compact / cozy / detail` 3단. compact=한 줄 행, detail=카드+메타+증거 링크 |
| 상세 패널 | Linear(우측 패널), Notion(페이지) | 행 클릭 → 우측 드로어. 탭: Overview / Activity / Messages / Evidence |
| 커맨드 팔레트 | Linear/Raycast | `Ctrl+K`: 뷰 이동, task 생성, 필터 적용, 에이전트 호출, meeting 소집 |
| 키보드 우선 | Linear | `j/k` 이동, `Enter` 상세, `s` 상태 변경, `a` 담당 지정 |
| 저장된 뷰 | Notion/Linear | 필터+정렬+그룹 조합을 명명 저장 ("진행중 P0", "리뷰 대기") |
| 빵부스러기/백링크 | Notion | task ↔ taskset ↔ evidence ↔ review 문서 상호 링크 |

## 3. 뷰별 기획

### 3.1 Tasksets (기본 진입 뷰)

- taskset 카드: 이름·코드네임(Feedback Analyst 등)·목적·**진행률 bar(done/total)**·상태 분포 미니 차트·담당 에이전트 아바타 스택·최근 활동 시각.
- 카드 확장 → 소속 task 리스트(공통 리스트 컴포넌트, 상태별 그룹).
- task 행: `상태칩(plan/work/review/blocked/done) · ID · 제목 · 담당 에이전트 · 진행률% · 우선순위 · 갱신시각`. 상태 어휘는 런타임 상태(planned/ready/in_progress/review/blocked/completed)에 라벨 매핑.
- **Owner task 주입**: taskset 상세에서 "+ Add task" → `task.create` 명령(기존 Writes 경로 재사용) + 큐 위치 지정(맨 앞/특정 task 다음). 진행 중 흐름에 안전하게 삽입.
- 아카이브 taskset은 기본 접힘.

### 3.2 Board (칸반)

- 컬럼: Plan / Ready / Work / Review / Blocked / Done.
- 스윔레인 = taskset (토글 가능). 드래그 = 상태 변경(`task.update` 명령 경유, 직접 파일 변경 금지 원칙 유지).

### 3.3 Roadmap (Vision/Milestone)

- 데이터: `agents/project/VISION.md`, `ROADMAP.md`, 릴리스 계획(BACKLOG.md 버전 섹션), taskset 메타.
- 3계층 뷰: Vision(문서 카드) → Milestone/Release 타임라인(가로 바, 날짜·done 여부) → 연결된 taskset 진행률.
- Linear의 Projects/Milestones 모델 차용: milestone에 taskset을 연결하고 합산 진행률 표시.

### 3.4 Team (조직도 + RPG 프레즌스)

- 데이터: `agents/project/TEAMS.md`, `ORG.md`, `agents/roles.yml`, task_claims, pane_events.
- 상단: **조직도 트리**(Owner → lead-engineer → planning/qa/risk/release/ui-runtime/eval/rsi-lab …). 역할 노드에 활성 인스턴스 수 뱃지.
- 하단: 에이전트 카드 그리드 — 아바타(역할 아이콘), online/idle/working/reviewing/in_meeting/offline 상태(컬러 링 + 미세 펄스 애니메이션), 현재 task, 진행률, 마지막 발언. **"살아있는 길드 멤버" 감각은 과한 그래픽이 아니라 상태 전이 애니메이션·하트비트 점멸·활동 피드로 구현.**
- 클릭 → Agent Focus(현재 task, 최근 메시지/이벤트, 상태 전이 이력).

### 3.5 Live Map (rqt형 그래프)

- 노드: Owner·에이전트 인스턴스·활성 taskset·게이트. 엣지: 메시지 흐름·task 할당·리뷰 요청·차단 관계.
- SSE 이벤트 수신 시 해당 엣지 하이라이트 펄스(메시지가 "흘러가는" 시각화). 노드 상태색 = 에이전트 상태.
- 1단계는 기존 Map 데이터의 정적 그래프 + 주기 갱신, 2단계에서 SSE 라이브.

### 3.6 Channels (Slack/Discord형)

- 채널 = taskset별 자동 채널 + `#general` + `#governance`. 스레드 = task 단위.
- 메시지에 발신 에이전트 아바타·역할색. 에이전트 간 대화가 실시간으로 흘러내려오는 피드.
- **Owner 개입**: 입력창에서 특정 에이전트/채널에 지시 전송(`runtime.message` 명령). `/meeting <주제> @역할들`, `/seminar <주제>` 슬래시 명령 → 런타임 meeting/seminar 이벤트 생성, Meetings 뷰와 reviews/MEETING-·SEMINAR- 기록 연동.

### 3.7 Home (대시보드)

- 현재 goal/실행 상태, 활성 taskset 진행률, 주의 필요(blocked/error/승인 대기), 최근 이벤트 5건, 오늘의 완료(Daily Brief).

## 4. 런타임 연동 기능 (UI 밖 정책 포함)

1. **Taskset 경계 실행 가드**: 특정 taskset 실행을 지시하면 해당 taskset의 task가 모두 끝났을 때 **정지하고 Owner에게 보고**해야 한다. 현재는 완료 후 taskset 외 작업으로 이탈하는 사례가 있음(Owner 관찰). 구현 방향: `taskset_dispatcher`에 active taskset scope 기록 → stop hook/governance gate가 "scope 외 신규 작업 착수"를 block, 완료 시 `taskset.completed` 이벤트 + 정지. UI는 완료 배너와 "다음 taskset 제안(승인 대기)"을 표시.
2. **Owner task 주입**: 3.1의 task.create + 큐 위치. 실행 중 에이전트는 다음 task 선택 시점에 주입분을 인지.
3. **Meeting/Seminar 명령**: `meeting.start`/`seminar.start` 명령 타입 추가 → 지정 역할들이 합의 라운드 수행, 결과는 reviews/ 기록 + Meetings 뷰 노출.
4. **실시간 레이어**: `/api/events` SSE 스트림(TASK-AR-317과 동일 기반). 폴링 폴백 유지.

## 5. 기술 스택 결정 포인트 (Owner 선택 필요)

| 옵션 | 장점 | 단점 |
| --- | --- | --- |
| A. 현행 유지(파이썬 단일 파일 + vanilla JS) 점진 확장 | 의존성 0, 배포 단순(현 cli 그대로) | ui_console.py가 이미 1,700줄+, V2 뷰 추가 시 유지보수 한계 |
| B. `frontend/` React+Vite+TS 분리, 기존 `/api/*` 소비 (브리프 §10 권고안) | 컴포넌트화·라우팅·그래프 라이브러리(React Flow) 자연스러움 | 빌드 체인 도입, 템플릿 배포 경로 결정 필요 |

권고: **Phase A(테마/IA/리스트 패턴)는 현행 구조에서 진행**해 즉시 가치를 내고, Phase C(그래프/실시간/채널) 진입 전에 B 전환을 결정한다.

## 6. 단계별 로드맵

| Phase | 내용 | 등록 task |
| --- | --- | --- |
| A. Foundation | 라이트 테마+토글, 사이드바 IA, 공통 정렬/필터/그룹+밀도 토글 | TASK-AR-320, 321, 322 |
| B. Work Model | Tasksets 뷰+task 주입, Roadmap/Vision/Milestone, 조직도+Team | TASK-AR-323, 324, 325 |
| C. Live | SSE 프레즌스+활동 피드, rqt 라이브 그래프 (TASK-AR-317 기반) | TASK-AR-326 |
| D. Comms | 채널/스레드, meeting/seminar 명령 | TASK-AR-327 |
| E. Guard | taskset 경계 실행 가드 + 완료 정지 | TASK-AR-328 |

## 7. 성공 기준

- Owner가 CLI에 상태를 묻지 않고: 진행중 task·상태·담당·%를 5초 내 파악, taskset 단위로 묶어 보고, 임의 task를 흐름에 삽입하고, 에이전트 대화를 실시간으로 관전하며, 회의를 소집할 수 있다.
- 특정 taskset 실행 지시 시 완료 후 정지가 보장된다 (scope 이탈 0건).
- 라이트/다크 전환이 전 뷰에서 토큰만으로 동작한다.
