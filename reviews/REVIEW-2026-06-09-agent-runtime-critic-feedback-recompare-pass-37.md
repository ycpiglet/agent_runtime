# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-37.md

## Bottom Line

`PASS-37`에서는 다중 메시지 처리의 지연 분포와 스타베이션(미응답) 위험을 계측 가능한 형태로 검증했다.

`test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`를 통해 여러 메시지를 대상으로 stale claim 복구/재획득 경합 하에서:
- 모든 메시지가 `answered`로 수렴하는지
- 성공/실패 레이스에서 지연 분포가 한계 내인지
- 메시지별 중복 응답이 없는지
- 일부 경쟁자는 성공하지 못해 실패 카운트가 존재하는지
를 동시에 검증했다.

## Signal

| 항목 | PASS-36 상태 | PASS-37 상태 | 근거 |
|---|---|---|---|
| 다중 메시지 경합의 처리 지연 계측 | ✅ 통과 | ✅ 확장 통과 | `winner` 측정 지연 분포를 신규 테스트로 정량 확인 |
| 스타베이션 방지(미응답 메시지) | ✅ 점검 대상 | ✅ 강화 | 경합 하에서도 모든 메시지 상태가 `answered`로 수렴 |
| 응답 유일성 | ✅ 통과 | ✅ 강화 | 메시지당 중복 reply 1개 검증 추가 |
| 템플릿 self-contained 및 공개 게이트 | ✅ 유지 | ✅ 유지 | 전체 `tests`, `sanitize`, `publish` 게이트 clean 상태 유지 |

## Insight

- R2 리스크 추적을 `single winner` 검사에서 한 단계 넘어 `latency + starvation` 관측으로 확장해, 처리량·지연 편차가 큰 노드군에서도 병목이 없는지 볼 수 있게 했다.
- 동일 메시지에 여러 worker가 동시에 진입해도 `answered` 결과는 메시지별 1개로 정착되고, 경쟁 실패(worker 실패)는 정상적인 분산 경쟁 노이즈로 수용되어 실제 장애 패턴과 부합한다.
- 결과적으로 기존 `claim/답변` 경로가 동시성 경합에서 “성공 유실 없이 회수되는지”와 “급격한 지연 폭주”를 동시에 감시할 수 있는 테스트 기반이 추가되었다.

## Decision

- `PASS-37`로 병렬 stale recovery 시나리오의 정량 지표(지연 분포, 미응답 없음, 1:1 응답 매핑)를 강화했다.
- 다음 사이클(`PASS-38`)은 이 지표를 고정 임계치 문서화(`p95/p99`, 허용 실패율)하고, 테스트 실패 시 로깅을 남기는 방식으로 운영 모니터링 성격까지 연결한다.

## Evidence (pass-37)

- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/test_template_message_queue.py -q`
  - `23 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests -q`
  - `150 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli sanitize --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-check --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source-pass37 --check`
  - `findings=0`

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-36.md`
- `tests/test_template_message_queue.py`
