# kor-companies

해외 언론 RSS를 수집해 한국 주요 기업 언급 기사를 골라내고 텔레그램으로 보내는 모니터링 앱이다.

## 목표

- 하루 2회 원격에서 실행
- 로컬 장비가 꺼져 있어도 계속 동작
- 결과는 텔레그램으로 전달하고 GitHub에도 남긴다
- 상태는 저장소 안에 기록해 다음 실행에 재사용

## 현재 구조

- `config/companies.json`: 감시 대상 기업과 별칭
- `config/countries.json`: 국가 우선순위와 언어 정보
- `config/sources.json`: RSS 소스 목록
- `config/google_news.json`: Google News 보조 수집 설정과 제외 규칙
- `src/`: 모니터링 앱
- `data/state/state.json`: 중복 제거용 상태 저장
- `reports/`: 최신 리포트와 아카이브
- `.github/workflows/monitor.yml`: GitHub Actions 스케줄 실행
- `.github/workflows/healthcheck.yml`: 매주 점검 실행 및 텔레그램 알림

## 실행

```bash
python3 -m src.main
```

옵션 예시:

```bash
python3 -m src.main --since-hours 48 --max-items-per-feed 100
```

## 원격 실행 방식

GitHub Actions가 UTC 기준 `09:00`, `23:00`에 실행된다.

- `23:00 UTC` = 다음날 `08:00 KST`
- `09:00 UTC` = 당일 `18:00 KST`

워크플로는 실행 후 아래 파일을 갱신하고 같은 저장소에 다시 커밋한다.

- `reports/latest.md`
- `reports/latest.json`
- `reports/archive/...`
- `data/state/state.json`

결과는 텔레그램으로 즉시 전송하고, 동시에 GitHub에도 남긴다.

필요한 GitHub Secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_MESSAGE_THREAD_ID` (선택)
- `GOOGLE_TRANSLATE_API_KEY` (비영문 기사 제목/회사 관련 요약을 한국어로 번역하기 위해 필수)

번역은 Google Cloud Translation Basic(v2) API를 사용한다. 앱은 기사 전체를 번역하지 않고, 제목과 회사 관련 문장만 번역해 비용을 줄인다.

## 직접 RSS 수집 범위

- 기본값은 Google News 없이 직접 RSS/Atom/RDF 피드만 사용한다.
- 현재 활성 직접 RSS는 73개이며, 미국·중국·일본·베트남·독일·영국·프랑스·유럽권 공통 외에 캐나다·호주·인도·싱가포르·홍콩·대만·네덜란드·태국·멕시코·카타르권 소스를 포함한다.
- 소스는 `config/sources.json`에서 켜고 끌 수 있다. 안정성이 떨어지는 후보는 `enabled: false`로 남겨둔다.

## Google News 보조 수집

- Google News RSS는 저품질/소비자성 소스가 많이 섞여 기본값으로는 비활성화한다.
- 필요할 때만 `config/google_news.json`의 `enabled`를 `true`로 바꿔 보조 수집을 켠다.
- 활성화하면 `US / JP / GB / DE / FR / VN` 6개 리전에서 회사명을 배치 쿼리로 묶어 검색한다.
- Google News 항목은 한국 매체, PR 배포망, 회사 자체 보도자료, 기존 정식 RSS와 중복되는 원 매체를 제외한다.
- Google News 링크는 직접 기사 URL이 아니어서 본문 추출은 건너뛰고 제목 중심 보조 요약으로 처리한다.
- 제외 규칙과 국가별 설정은 `config/google_news.json`에서 수정할 수 있다.

## 주간 점검

GitHub Actions가 매주 금요일 `15:51 KST`에 지난 7일 로그를 점검한다.

- 예정된 `08:00 / 18:00 KST` 실행 슬롯이 모두 채워졌는지 확인
- 최근 24시간 내 실행 기록이 있는지 확인
- 대규모 소스 실패가 있었는지 확인
- 결과는 `정상 작동중`이어도 텔레그램으로 전송

주간 점검 결과는 아래 파일에도 저장된다.

- `reports/health/latest-weekly.md`
- `reports/health/latest-weekly.json`
- `reports/health/archive/...`

## 검증

표준 라이브러리만 사용하도록 작성했다.

```bash
python3 -m unittest discover -s tests -v
```

## 한계

- 현재는 RSS/Atom/RDF 피드만 사용한다.
- Google News 보조 수집은 품질 편차가 커서 기본 비활성화했다. 다시 켜면 발견 범위는 넓어지지만 직접 RSS를 제공하는 정식 매체보다 요약 정보가 제한적일 수 있다.
- 기사 본문 HTML에서 회사 관련 문장을 보조적으로 추출하지만, 사이트 구조가 크게 다르면 문맥 추출 품질이 떨어질 수 있다.
- 중국 소스는 공개 RSS 안정성이 낮아 일부 후보를 비활성 상태로 두었다.
