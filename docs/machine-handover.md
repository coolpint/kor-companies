# 로컬 의존성 점검과 머신 이관 가이드

## 한줄 결론

이 프로젝트는 로컬 머신에 강하게 묶여 있지 않다. 실행 로직은 표준 라이브러리 기반 Python 코드이고, 정기 실행은 GitHub Actions가 담당한다. 다만 운영을 계속하려면 GitHub Actions, GitHub Secrets, Telegram, Google Translate API, 저장소 안의 상태 파일을 함께 유지해야 한다.

## 점검 결과

### 로컬 머신 의존성이 없는 부분

- 코드에 사용자별 절대경로 하드코딩이 없다.
- `launchd`, `cron`, `systemd` 같은 로컬 스케줄러에 의존하지 않는다.
- Docker, 데이터베이스, 브라우저 자동화, 별도 패키지 매니저에 의존하지 않는다.
- 애플리케이션 자체는 표준 라이브러리만 사용한다.
- 기본 경로가 모두 상대경로라서 저장소 루트에서 실행하면 다른 머신에서도 같은 구조로 동작한다.

### 실제로 운영에 필요한 외부 의존성

- GitHub 저장소
  - GitHub Actions가 켜져 있어야 한다.
  - 워크플로가 `main` 브랜치에 결과를 다시 커밋하므로 저장소 쓰기 권한이 필요하다.
- GitHub Secrets
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `TELEGRAM_MESSAGE_THREAD_ID` 선택
  - `GOOGLE_TRANSLATE_API_KEY`
- 외부 서비스
  - Telegram Bot API
  - Google Cloud Translation Basic v2 API
  - 각국 언론 RSS와 기사 본문 URL
- 네트워크
  - GitHub Actions 러너나 로컬 머신에서 외부 HTTPS에 접근 가능해야 한다.

### 저장소 안에서 이어지는 상태

이 프로젝트는 아래 파일을 실행 상태의 일부로 취급한다.

- `data/state/state.json`
- `reports/latest.md`
- `reports/latest.json`
- `reports/archive/...`
- `reports/health/latest-weekly.md`
- `reports/health/latest-weekly.json`
- `reports/health/archive/...`

이 파일들이 계속 커밋되기 때문에, 새 머신에서 이어받을 때는 저장소 최신 `main`을 기준으로 시작해야 한다. 특히 `data/state/state.json`이 없거나 오래되면 이미 본 기사를 다시 신규로 판단할 수 있다.

## 코드 기준 운영 전제

### 런타임

- 권장 Python: `3.11+`
- GitHub Actions는 현재 `Python 3.11`로 실행한다.
- `zoneinfo`를 사용하므로 일반적인 macOS, Ubuntu, GitHub-hosted runner에서는 문제 없다.
- 매우 최소한의 Linux 환경에서는 `tzdata`가 빠져 있으면 시간대 처리에 문제가 생길 수 있다.

### 실행 위치

- 저장소 루트에서 실행하는 것을 전제로 한다.
- 기본 경로:
  - 설정: `config/`
  - 상태 파일: `data/state/state.json`
  - 출력: `reports/`

### 원격 실행 방식

- `.github/workflows/monitor.yml`
  - 매일 `08:00 KST`, `18:00 KST` 실행
  - 실행 후 `reports/`와 `data/state/state.json`을 커밋
- `.github/workflows/healthcheck.yml`
  - 매주 금요일 `15:51 KST` 실행
  - 실행 후 `reports/health/`를 커밋

## 다른 머신으로 옮길 때 체크리스트

### 1. 저장소 기준 상태 확인

- 최신 `main` 브랜치를 가져온다.
- `data/state/state.json`과 `reports/`가 최신인지 확인한다.
- GitHub Actions가 최근까지 정상 실행 중인지 확인한다.

### 2. 새 머신 로컬 실행 환경 준비

- Python `3.11+` 설치
- 저장소 루트에서 아래 검증 실행

```bash
python3 -m unittest discover -s tests -v
```

### 3. 로컬 수동 실행용 환경 변수 준비

원격 운영은 GitHub Secrets를 쓰지만, 로컬에서 직접 검증하려면 셸 환경 변수로 넣어야 한다.

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export TELEGRAM_MESSAGE_THREAD_ID="..."   # 선택
export GOOGLE_TRANSLATE_API_KEY="..."
```

### 4. 수동 검증 실행

```bash
python3 -m src.main --since-hours 36 --max-items-per-feed 80
python3 -m src.weekly_healthcheck
```

### 5. GitHub 쪽 점검

- 저장소 Secrets가 모두 설정돼 있는지 확인
- Actions 권한이 `contents: write`로 동작 가능한지 확인
- 기본 브랜치가 `main`인지 확인
- 워크플로 비활성화 상태가 아닌지 확인

## 이관 시 가장 흔한 실수

### 상태 파일 없이 시작

`data/state/state.json`을 비우거나 누락하면 과거 기사도 신규 기사처럼 다시 텔레그램으로 발송될 수 있다.

### 로컬과 GitHub Actions를 동시에 운영

같은 시간대에 로컬 수동 실행과 GitHub Actions 정기 실행이 겹치면, 상태 파일 커밋 충돌이나 중복 발송이 생길 수 있다. 운영 기준은 GitHub Actions 하나로 두고, 로컬은 점검용으로만 쓰는 편이 안전하다.

### Secrets는 옮기지 않고 코드만 복제

코드는 실행돼도 번역과 텔레그램 발송이 빠진 상태가 된다. 이 프로젝트는 코드보다 Secrets와 외부 API 키가 더 중요한 운영 자산이다.

### 다른 브랜치에서만 수정

현재 워크플로는 `main` 브랜치 기준으로 결과 파일을 다시 커밋한다. 기본 브랜치나 운영 브랜치를 바꿀 경우 워크플로도 함께 수정해야 한다.

## 권장 운영 방식

### 가장 안전한 방식

- 정기 실행: GitHub Actions
- 수동 점검: 로컬 머신
- 상태 보존: Git에 커밋된 `data/state/state.json`과 `reports/`

### 다른 머신에서 이어받는 방식

- 새 머신은 저장소를 클론하고 테스트와 수동 실행만 검증한다.
- 실제 정기 운영은 기존처럼 GitHub Actions가 계속 담당하게 둔다.
- 완전 이관이 필요하다면 저장소 Secrets와 Actions 설정까지 함께 옮긴다.

## 빠른 판정표

| 항목 | 로컬 머신 의존성 | 설명 |
| --- | --- | --- |
| Python 실행 | 약함 | Python 3.11+만 있으면 된다. |
| 파일 경로 | 없음 | 상대경로만 사용한다. |
| 로컬 스케줄러 | 없음 | GitHub Actions가 담당한다. |
| 텔레그램 발송 | 있음 | Bot token, chat id가 필요하다. |
| 번역 | 있음 | Google Translate API key가 필요하다. |
| 상태 보존 | 있음 | `data/state/state.json`을 유지해야 한다. |
| 주간 점검 | 없음 | 로컬이 아니라 GitHub Actions에서 돈다. |
| OS 종류 | 약함 | macOS/Ubuntu 수준이면 무난하고, 일부 최소 Linux는 `tzdata` 확인이 필요하다. |

