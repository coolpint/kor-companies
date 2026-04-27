# kor-companies plan

## 최초 기획 의도

이 프로젝트는 해외 언론 RSS와 보조 뉴스 소스를 수집해 한국 주요 기업 관련 기사를 선별하고, 결과를 텔레그램과 GitHub 리포트로 남기는 모니터링 시스템이다. 목표는 모든 기사의 장기 아카이빙이 아니라, 하루 2회 주요 해외 보도 흐름을 안정적으로 포착하는 것이다.

## 유지해야 할 방향

- 운영 기준은 GitHub Actions 중심으로 둔다.
- 로컬 머신은 개발, 점검, 수동 검증에 사용한다.
- 상태 보존은 `data/state/state.json`과 `reports/`의 커밋 이력을 기준으로 한다.
- 안정적인 RSS/Atom/RDF 소스를 우선하고, Google News는 품질 편차가 있어 보조 수집으로 다룬다.
- 외부 API와 발송 채널은 GitHub Secrets 또는 로컬 환경 변수로만 주입한다.

## 현재 상태

- 원격 저장소: `https://github.com/coolpint/kor-companies`
- 로컬 경로: `/Users/sanghoon/codes/kor-companies`
- 기본 브랜치: `main`
- 실행 진입점: `python3 -m src.main`
- 테스트 명령: `python3 -m unittest discover -s tests -v`
- 운영 문서: `README.md`, `docs/monitoring-plan.md`, `docs/machine-handover.md`
- 최신 모니터링 리포트: `reports/latest.md`
- 최신 주간 점검 리포트: `reports/health/latest-weekly.md`

## 2026-04-27 인수인계 작업 기록

- `/Users/sanghoon/codes/kor-companies`가 비어 있고 Git 저장소가 아닌 상태임을 확인했다.
- `https://github.com/coolpint/kor-companies.git`을 현재 경로에 클론했다.
- 저장소는 `main` 브랜치에서 `origin/main`을 추적하고 있으며, 최신 커밋은 `a4f95b1 Document machine handover dependencies`다.
- README와 `docs/machine-handover.md`를 확인해 이 프로젝트가 로컬 스케줄러가 아니라 GitHub Actions 중심으로 운영된다는 점을 확인했다.
- 전체 테스트 `python3 -m unittest discover -s tests -v`를 실행했고 34개 테스트가 모두 통과했다.
- 사용자의 작업 규칙을 이어가기 위해 `AGENTS.md`, `constitution.md`, `docs/agents/constitution-agent.md`, `docs/agents/review-agent.md`를 추가했다.
- 문서 추가 후 전체 테스트를 다시 실행했고 34개 테스트가 모두 통과했다.
- review agent 기준으로 확인한 결과, 이번 변경은 문서 추가만 포함하며 코드 실행 경로, 상태 파일, 리포트 산출물은 변경하지 않았다.
- 로컬 커밋 `Document local working protocol`로 작업 규칙과 계획 문서를 저장했다.
- `git push origin main`은 GitHub HTTPS 인증 부재로 실패했다. `gh` CLI도 현재 머신에서 `bad CPU type in executable`로 실행되지 않았다.
- GitHub 커넥터로 원격 기본 브랜치에 파일을 개별 생성하려는 방식은, 로컬 커밋과 다른 경로로 `main`을 부분 변경하면 이력 divergence가 생길 수 있어 안전 심사에서 거부되었다.
- 이후 원격 `origin/main`의 현재 커밋을 부모로 삼아 5개 파일을 하나의 tree/commit으로 만든 뒤 `main`을 fast-forward시키는 방식으로 해결하기로 했다.

## 다음 작업 후보

- GitHub Actions 최근 실행 상태와 Secrets 설정 여부를 GitHub에서 확인한다.
- 로컬 수동 실행이 필요하면 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GOOGLE_TRANSLATE_API_KEY`를 환경 변수로 설정한 뒤 실행한다.
- 소스 실패가 반복되는 매체를 `reports/latest.md`와 주간 점검 리포트 기준으로 검토한다.
- Google News 보조 수집을 다시 켤지 여부는 품질과 중복률을 확인한 뒤 결정한다.

## 변경 기록

- 2026-04-27: 머신 인수인계 상태를 정리하고, 계획/판단/리뷰 문서 체계를 추가했다.
- 2026-04-27: 로컬 커밋까지 완료했으며, Git 인증 문제로 일반 push는 실패했다. 이후 원격은 GitHub 커넥터의 tree/commit/ref 업데이트 방식으로 같은 변경 묶음을 반영하기로 했다.
