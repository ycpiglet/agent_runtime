# RESEARCH-2026-06-11 — Interactive/Gamification Console Deep Research

- Bottom Line: 게임·인터랙티브 플랫폼의 검증된 패턴 5개 각도(공간 시각화, 게임화, 직접 조작, 외부 알림, 아이디어 수명주기)를 27개 출처·130개 주장으로 딥리서치했고, 채택분을 `TASKSET-AR-UI-LIVING-CONSOLE`(TASK-AR-360~365)로 등록한다. 핵심 판정: 게임화는 "사회적 연결 중심·처벌 금지·스트릭 압박 금지" 가드레일과 함께만 채택, 토큰=경험치는 낭비 유인이라 산식 수정, KakaoTalk 알림톡은 사업자 제약으로 보류(Idea Vault 보관).
- Signal: 검증 현황(2026-06-12 갱신, 4차 누적 실행) — 25개 중 **7건이 3-0 만장일치 확정**(원문 인용 확보, §6 참조), 18건은 반복된 세션 한도로 미검증 잔류. 미검증분도 1차 자료(SEC/학술지/공식 문서) 위주라 신뢰도는 양호하나 개별 수치는 사용 시 원문 재확인을 권한다. 재검증 재개: Workflow run `wf_6642dfc5-cb9` resume.
- Insight: 다섯 각도의 공통 결론 — "살아있는 느낌"은 그래픽이 아니라 **상태의 가시성**(이모지 글리프, 커서/선택 표시, 펄스)에서 나오고, 게임화의 효용은 점수가 아니라 **관계성**(relatedness)에서 나오며, 알림의 품질은 채널 수가 아니라 **집계 윈도우와 심각도 라우팅**에서 나온다.
- Decision: Owner 제안 전부를 수용하되 증거 기반 수정 3건 — ① 토큰 소비를 XP에 직접 가산하지 않고 "누적 경험"과 "효율"을 분리, ② 스트릭형 압박 메커니즘 도입 금지, ③ KakaoTalk 연동은 보류·Telegram/Discord 우선.

## 1. 각도별 핵심 발견 (출처 포함, 미검증 주장)

### A. 공간형 에이전트 시각화 (가상 오피스 / 2D 맵)

- **Smallville(Generative Agents, arXiv 2304.03442)이 정확한 선행 사례**: 25개 LLM 에이전트를 심즈풍 2D 스프라이트로 렌더링, 기능별 구역(카페·학교·집·상점), **아바타 위 이모지 글리프로 현재 행동을 무문자 전달**(📖📝 저널링, 💻📧 메일 확인). 공간 구조는 단순 트리(world→areas→objects) + 에이전트별 JSON(현재 위치·행동·상호작용 객체), 이동은 경로탐색 렌더링.
- Gather.town 공식 로드맵: AI 에이전트를 2D 공간 내 가시적 엔티티로 배치하는 항목과 **Webhook Objects**(외부 도구 이벤트에 반응하는 공간 내 객체 — 알림을 채팅이 아니라 "공간"에 표면화) 계획 — 둘 다 'Coming Later' 단계로 미출시. (gather.town/roadmap)
- Teamflow는 2024년 종료(kumospace 블로그) — 가상 오피스 단독 제품은 시장성이 약했다는 신호. **우리는 제품이 아니라 뷰 하나**이므로 리스크 구조가 다름.
- 적용: 최소 실행 가능 패턴 = 정적 회사 맵 + 팀별 방 + 에이전트 스프라이트 + 이모지 상태 글리프. 경로탐색 애니메이션은 후순위.

### B. 게임화 — 효과와 역효과의 실증

- **Habitica 현장 연구(ScienceDirect, 45명 2주)**: 전원이 역효과를 1회 이상 경험. 최빈 역효과 = **실제로 생산적인 기간에 앱 체크를 못 해서 처벌받는 것**. 보상 체계의 부적절성 인지가 동기 저하의 핵심 예측 변수.
- **메타분석(Springer, 35개 연구 2,500명)**: 게임화의 내재 동기 효과는 유의하지만 작음(g=0.257). 최대 효과는 **관계성**(g=1.776), 자율성(g=0.638) 순; 역량감은 미미. 실패 모드 2가지 = 피드백이 눈에 안 띔, 메커니즘이 선택권을 제약.
- **Duolingo SEC 공시(Q2 FY24)**: DAU의 20%가 365일+ 스트릭, 소셜 기능(Friend Quests/리더보드/Friend Streak)이 리텐션 동력 — 단 이것은 소비자 학습 앱 맥락.
- **GitHub 스트릭 제거 사례(isaacs/github#627)**: 잔디 스트릭이 주말 노동을 유발한다는 202개 코멘트 이슈 후 GitHub이 2016-05 스트릭 카운터를 프로필에서 제거. **개발 도구에서 스트릭 압박은 검증된 실패 패턴.**
- 적용 (가드레일): 처벌 메커니즘 금지, 스트릭/연속일 압박 금지, 보상은 완료·게이트 통과 같은 실질 성과에만, 피드백은 눈에 띄게, 끄기 쉽게. 사회적 메커니즘(에이전트 팀 단위 성취)이 점수보다 효과적.
- **토큰=XP 수정안**: 토큰 소비를 XP에 직접 가산하면 낭비를 보상한다(역 Goodhart). 분리 권고 — "누적 경험"(처리 task 수·게이트 통과·테스트 증가·리뷰 산출)으로 레벨을 올리고, "효율"(task당 토큰, 재작업률)은 별도 스탯으로 표시.
- 프로젝트 Lv/사업 단계: 누적 지표 가중합 → Lv.N(연속), 마일스톤 달성 → 단계 칭호(garage → seed → startup → scaleup → unicorn — 타이쿤 게임 문법). 산식은 TASK-AR-345에서 확정.

### C. 직접 조작 — hover/drag/presence

- Notion peek(2023-10 공식 발표): hover로 페이지 내용 미리보기 — task/에이전트 카드 hover 패턴의 직접 선행 사례.
- **Discord 접근성 DnD FAQ**: 드래그앤드롭을 1급 동사로 쓰되 **완전한 키보드 등가**(Ctrl+D로 들기 → 화살표 이동 → Space 드롭 → Esc 취소) 제공 — 회의실 드래그 설계의 접근성 기준.
- Figma 멀티플레이어(공식 블로그): 모든 참여자의 **커서+현재 선택**을 렌더해 "무엇을 만지고 있는지" 전달, 아바타 클릭 → 따라가기 모드 — "에이전트 따라가기(Agent Follow)"로 직역 가능.
- 적용: 회의실 = 드롭 존 패턴(Discord 음성채널 드래그와 동형). 에이전트 카드를 회의실에 드래그 → 주제/task 선택 → 라운드 토론 → MEETING 기록. 키보드 등가 필수.

### D. 외부 알림 연동

- **LangSmith 알림 모델(공식 문서)**: 이벤트당 알림이 아니라 **5/15분 집계 윈도우 + 임계값** 기반(런 수·비용·오류·피드백 점수·지연), 채널은 PagerDuty/웹훅 네이티브 + Slack/Teams/email은 **웹훅 레시피**로 — "범용 웹훅 + 레시피"가 업계 패턴.
- Devin Slack 연동, Claude Code hooks 문서: 에이전트 제품의 human-in-the-loop 알림은 기존 메신저에 위임하는 패턴.
- **KakaoTalk 알림톡(NHN Cloud 공식 API 가이드)**: 발신프로필 등록(사업자), 템플릿 사전 심사 필수 — 개인/소규모 프로젝트에는 진입장벽 높음. **보류 → Idea Vault** (부활 조건: 사업자 등록 또는 카카오 개인 채널 대안 확인).
- 적용: 웹훅 퍼스트(Discord/Telegram/email 레시피), 심각도 라우팅(block=즉시, watch=윈도우 집계, pass=데일리 다이제스트), 알림 센터(TASK-AR-338)와 일원화.

### E. 아이디어 수명주기 — Idea Vault (Owner 제안의 선행 사례)

- Linear 공식 문서: Archive(복원 가능) vs Delete(영구) 구분 — 폐기와 보관의 분리.
- Pivotal Tracker **Icebox**: "지금 안 하지만 버리지 않는" 작업의 전용 공간 — 명시적 1급 개념.
- **AWS ADR 프로세스 문서**: 결정 기록에 `superseded` 상태 — 과거 결정을 지우지 않고 대체 관계로 보존.
- **Readwise 공식 문서**: 저장한 하이라이트를 간격 반복으로 재노출(resurfacing) — "주기적으로 다시 꺼내보기"의 제품화된 사례.
- Google SRE 포스트모템 문화: 실패 기록을 비난 없이 보존·재학습 — 본 프로젝트 casebook과 동형.
- 적용: `agents/project/idea-vault/` 레지스트리 — 각 항목에 `shelved_reason`, `revisit_after`, `revival_criteria`, `origin_ref`. 주기 재발굴 루프(retro/planning scan에 통합)가 기한 도래분을 Owner 제안으로 재상정, 채택 시 프로세스 A/B 실험(한 변수씩, 측정 지표 선정)으로 검증. **Owner 통찰대로 이것은 UI 기능이 아니라 RSI 운영 원칙** — Evaluate→Propose→Verify→Merge 루프의 입력 소스가 된다. (운영 규칙: TASK-AR-360)

## 2. 채택/수정/보류 종합

| 판정 | 항목 |
| --- | --- |
| 채택 | 회의실 드래그 인(AR-361), hover peek + DnD 1급 동사 + 키보드 등가(AR-362), 이모지 상태 글리프·Agent Follow(AR-364/324 연계), 웹훅 퍼스트 알림 + 심각도/윈도우 라우팅(AR-365), Idea Vault + 재발굴 루프 + 프로세스 A/B(AR-360), 프로젝트 Lv/사업 단계/성장 시스템(AR-363), 2D 오피스 맵 최소 패턴(AR-364) |
| 증거 기반 수정 | 토큰=XP → 경험/효율 분리, 스트릭 금지, 처벌 금지, 게임화 전체 토글(TASK-AR-340 가드레일과 통합) |
| 보류 → Idea Vault | KakaoTalk 알림톡(사업자 제약), 경로탐색 이동 애니메이션(비용 대비 후순위), 에이전트 음성/TTS, 모바일 푸시 앱, Gather식 Webhook Objects(공간 내 알림 객체 — 맵 뷰 안착 후) |

## 3. 출처 (27개 중 핵심)

arxiv.org/pdf/2304.03442 (Generative Agents) · gather.town/roadmap · sciencedirect.com S1071581918305135 (Habitica 연구) · sec.gov Duolingo Q2 FY24 · springer 10.1007/s11423-023-10337-7 (메타분석) · github.com/isaacs/github/issues/627 · support.discord.com DnD 접근성 FAQ · figma.com/blog/multiplayer-editing-in-figma · x.com/NotionHQ peek · docs.langchain.com/langsmith/alerts · docs.devin.ai/integrations/slack · code.claude.com/docs hooks · docs.nhncloud.com 알림톡 API · linear.app/docs/delete-archive-issues · pivotaltracker.com workflow(icebox) · docs.aws.amazon.com ADR process · docs.readwise.io resurfacing · sre.google postmortem culture

## 6. 검증 확정 결과 (2026-06-12, 3-0 만장일치 + 원문 인용)

| # | 확정 주장 | 영향 |
| --- | --- | --- |
| 1 | 2D 스프라이트 아바타 + 머리 위 이모지 글리프(행동 추상화) + 클릭 시 자연어 상세 = 자율 에이전트 공간 시각화의 최소 패턴. 인용: "Each agent is represented by a simple sprite avatar... displayed as a set of emojis... accessed by clicking on the agent's avatar." (arXiv 2304.03442) | TASK-AR-364 설계 근거 확정 |
| 2 | 공간 모델 = 계층 트리(world→areas→objects), 에이전트는 관찰한 부분 그래프만 유지. (arXiv 2304.03442) | TASK-AR-364 데이터 구조 확정 |
| 3 | Gather 공식 로드맵에 "AI in Your Space"(에이전트를 공간 내 가시적·인터랙티브 엔티티로) 항목 존재 — 'Coming Later' 단계. (gather.town/roadmap) | 방향성 검증 + 선행 기회 |
| 4 | 해당 항목이 Gather 로드맵의 유일한 AI 항목이며 최원거리 단계 = 2026 중반 기준 출시된 공간형 AI 에이전트 제품은 없음. | 차별화 기회 확정 |
| 5 | 게임화 요소가 의도와 반대 행동(예: 미루기)을 유발하는 "역효과"가 Habitica에서 실증됨. (ScienceDirect S1071581918305135) | AR-363 가드레일 근거 |
| 6 | 45명 2주 현장 연구에서 전원이 역효과를 경험. (같은 연구) | AR-363 가드레일 근거 |
| 7 | 최빈 실패 모드 = 실제로 생산적인 시기에 체크를 못해 처벌받는 구조; 사용자들은 처벌 회피를 위해 task를 무기한 습관으로 재분류하는 식으로 시스템을 우회. (같은 연구) | "처벌 금지" 원칙 확정 |

- 미검증 잔류 18건: Duolingo 스트릭/소셜 수치(SEC), 게임화 메타분석 효과량(Springer), GitHub 스트릭 제거, Discord 키보드 DnD + 오픈소스 라이브러리, Figma 커서/아바타 패턴, LangSmith 알림 모델, Devin Slack 패턴, Claude Code hooks 등 — 출처는 모두 1차 자료.

- Action Board: TASK-AR-360~365 등록(본 문서가 분석 근거; 342~350 대역은 병행 세션의 PM-OPERATING-SYSTEM이 선점하여 재배치), Idea Vault 시드 파일 생성. 검증 확정 7건 반영(2026-06-12).
- Next: 잔여 18건 재검증은 사용량 리셋 후 Workflow resume(wf_6642dfc5-cb9)으로 누적 재개 가능.
