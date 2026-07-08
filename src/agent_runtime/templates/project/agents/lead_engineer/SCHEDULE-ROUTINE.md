# Schedule Routine

저빈도 scheduled 작업의 등록·실행·점검 절차를 한 곳에 모은다. 스케줄 레지스트리는
OS 독립이고, **실행 트리거만 OS별로 다르다**: Windows는 Task Scheduler,
Linux/macOS는 세션 내 로컬 데몬(또는 실제 cron/launchd)을 쓴다.

관련 스크립트/문서:

- 레지스트리 CRUD: `scripts/schedule.py` → `agents/lead_engineer/SCHEDULE.yml`
- Windows OS 트리거: `scripts/schedule_task.py` (schtasks) + `scripts/run_schedule_task.cmd`
- 크로스플랫폼 로컬 데몬: `scripts/local_schedule_daemon.py` → `schedule_runs/`
- 실행기: `scripts/auto_runner.py --from-schedule --run`
- LLM scheduled 프롬프트 템플릿: `docs/agent_bootstrap/scheduled_prompts.md`

## 원칙

- 대기 중 로컬 데몬은 LLM을 호출하지 않는다. LLM scheduled task는 실행 시점에만 사용량을 쓴다.
- 스케줄은 새 작업을 만들지 않는다. 후보는 "제안"으로만 남기고 TASK 생성은 Owner 지시가 있을 때만.
- 파괴적 작업·`auto_runner --execute`·deploy·secret·prod DB·삭제/롤백은 스케줄 경로에서 하지 않는다.
- source of truth: `agents/lead_engineer/tasks/BACKLOG.md`, `schedule_runs/latest.md`,
  `agents/lead_engineer/STATUS.md`, `agents/lead_engineer/AUDIT-LOG.md`.

## 레지스트리 (모든 OS 공통)

```bash
python scripts/schedule.py list
python scripts/schedule.py add    --id daily-digest --cron "0 8 * * *" --selector digest --mode notify
python scripts/schedule.py enable  daily-digest
python scripts/schedule.py disable daily-digest
python scripts/schedule.py remove  daily-digest
```

`cron`은 5필드(`분 시 일 월 요일`) 표준이며 로컬 데몬의 `is_due`가 직접 파싱한다
(요일은 cron 규약 Sun=0/7). `mode: notify`는 알림만, 실행은 실행기가 담당한다.

## Windows — Task Scheduler

```powershell
python scripts/schedule_task.py status         # 등록/다음 실행/마지막 결과
python scripts/schedule_task.py register 07:53  # schtasks 에 OS 작업 등록(/F=덮어씀)
```

OS 작업은 `run_schedule_task.cmd` 래퍼를 호출하고, 래퍼가
`scripts/auto_runner.py --from-schedule --run` 을 돌려 로그를 `schedule_runs/last_task.log`
에 남긴다. `LastTaskResult=255` 이거나 현재 세션에서 OS task가 보이지 않으면 아래
로컬 데몬 폴백으로 전환한다.

## Linux / macOS — 로컬 스케줄 데몬

OS 스케줄러에 의존하지 않는다. `local_schedule_daemon.py`가 세션 안에서 cron을 직접
평가하므로 별도 설치 없이 어느 OS에서나 동작한다. Windows에서도 Task Scheduler
폴백으로 동일하게 쓸 수 있다.

```bash
python scripts/local_schedule_daemon.py status                    # 하트비트: last tick / last runs
python scripts/local_schedule_daemon.py tick --force              # 즉시 R1 smoke: enabled notify 전부 1회
python scripts/local_schedule_daemon.py watch --interval 60 --run-now  # 상시 루프(현재 세션)
python scripts/local_schedule_daemon.py stop                      # schedule_runs/local_daemon.stop 로 정지 요청
python scripts/local_schedule_daemon.py clear-stop
```

산출물은 모두 `schedule_runs/` 아래에 있다: 하트비트 상태 `local_daemon.state.json`,
로그 `local_daemon.log`, 정지 신호 `local_daemon.stop`. `watch`는 그 세션이 살아있는
동안만 유효하므로, 로그아웃 후에도 유지하려면 아래 OS 네이티브 스케줄로 감싼다.

### 세션 밖 상시 실행 (선택)

`watch` 대신 OS 네이티브 스케줄러가 `tick`을 주기 호출하도록 감쌀 수 있다.

Linux (cron) — 매분 due 검사:

```cron
* * * * * cd /path/to/repo && python scripts/local_schedule_daemon.py tick >> schedule_runs/cron.log 2>&1
```

macOS (launchd) — `~/Library/LaunchAgents/` 에 plist를 두고 `StartInterval` 60초로
`scripts/local_schedule_daemon.py tick` 을 호출한다. `RunAtLoad`는 취향에 따라.

두 경우 모두 데몬 자체는 무상태 tick이므로, 중복 실행은 분(minute) 키 dedup으로 방지된다.

## 점검 순서

1. `python scripts/schedule.py list` — 레지스트리와 enabled 상태 확인.
2. Windows면 `schedule_task.py status`, 아니면 `local_schedule_daemon.py status` — 트리거 살아있는지.
3. `schedule_runs/latest.md` / `local_daemon.log` — 최근 발화 결과 확인.
4. 이상 시 `tick --force`로 즉시 R1 smoke, 로그로 원인 격리.
