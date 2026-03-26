# 교역국 우선순위 및 국가별 소스 후보

## 목적

해외 언론 모니터링 국가와 국가별 우선 소스를 관리한다.

핵심은 "많은 나라"가 아니라 "교역 중요도가 높고, 안정적으로 수집 가능한 나라"다.

## 국가 선정 원칙

1. 공식 교역 통계를 기준으로 우선순위를 정한다.
2. 다만 운영 초기에는 사용자가 명시한 6개국을 고정 포함한다.
3. 국가 추가/제외는 분기 1회만 반영해 목록이 자주 흔들리지 않게 한다.
4. 통계상 권역(EU)과 실제 언론 운영 단위(독일, 영국)는 분리해서 관리한다.

## 공식 기준

- 한국무역협회 K-stat 월별/연간 통계
- 산업통상자원부 월별 수출입 동향 보도자료

초기 우선 국가는 아래와 같이 둔다.

| 우선순위 | 국가 | 상태 | 비고 |
| --- | --- | --- | --- |
| P1 | 미국 | 운영 시작 포함 | 사용자 요청 고정 |
| P1 | 중국 | 운영 시작 포함 | 사용자 요청 고정 |
| P1 | 일본 | 운영 시작 포함 | 사용자 요청 고정 |
| P1 | 베트남 | 운영 시작 포함 | 사용자 요청 고정 |
| P2 | 독일 | 운영 시작 포함 | EU 대표국 성격 |
| P2 | 영국 | 운영 시작 포함 | 금융/비즈니스 기사 비중 고려 |
| P2 | 프랑스 | 운영 확장 포함 | 르몽드, France 24로 유럽 기업/정책 기사 보강 |
| P2 | 유럽권 공통 | 운영 확장 포함 | Euronews, POLITICO Europe로 범유럽 정책/산업 기사 보강 |

## 향후 추가 후보 국가

- 대만
- 홍콩
- 인도
- 싱가포르
- 인도네시아
- 멕시코

## 국가 유지/제외 규칙

- 신규 추가: 공식 통계 기준 우선순위 상위권 + 안정적 소스 1개 이상 확보 시
- 제외: 2개 분기 연속 우선순위 하락 + 수집 효용 낮음이 확인될 때
- 예외 유지: 사용자가 중요하다고 지정한 국가는 순위와 별개로 유지 가능

## 소스 선정 원칙

1. 공개 RSS 또는 구조가 단순한 섹션 페이지가 있어야 한다.
2. 기사 원문 URL과 발행 시각이 안정적으로 제공되어야 한다.
3. 로그인/유료벽 의존도가 너무 높지 않아야 한다.
4. 국가를 대표하는 대형 매체거나, 경제/기업 기사 비중이 충분해야 한다.
5. 초기에는 국가별 1~2개 소스만 채택한다.

## 국가별 초기 후보 소스

### 미국

- 1차 후보: NYT Business, NPR Business, MarketWatch
- 2차 후보: NYT Technology, Fox Business Markets, Fox Business Technology, U.S. DOJ Press Releases
- 보조 수단: Google News US 검색 결과에서 허용 도메인만 통과

메모:

- 미국은 소스는 많지만 사이트 구조가 자주 바뀌는 곳도 많다.
- 초기에는 직접 피드가 확인되는 소스 위주로 제한하는 편이 안전하다.
- DOJ 보도자료는 일반 기업 뉴스보다 빈도는 낮지만, 제재, 반독점, 수출통제, 형사수사 이슈를 빠르게 포착하는 데 유용하다.

### 중국

- 1차 후보: China Daily BizChina, China Daily World
- 2차 후보: China Daily China, Global Times English

메모:

- 영문판 소스를 우선 사용하면 초기 구현 난도가 낮다.
- 필요하면 이후 중국어 키워드 별칭을 추가한다.

### 일본

- 1차 후보: Nikkei Asia RSS
- 2차 후보: NHK 계열 뉴스 피드 또는 비즈니스 섹션

메모:

- 일본은 영문 기사와 일본어 기사 간 표현 차이가 있어 별칭 사전이 중요하다.

### 베트남

- 1차 후보: VietnamPlus English RSS
- 2차 후보: VnExpress International RSS

메모:

- 베트남은 영문판이 있어 MVP에 적합하다.

### 독일

- 1차 후보: Deutsche Welle RSS
- 2차 후보: tagesschau Wirtschaft RSS

메모:

- 독일은 영문과 독문 소스를 병행할 수 있다.
- 기업 기사 비중은 DW보다 tagesschau Wirtschaft가 높을 수 있다.

### 영국

- 1차 후보: BBC News Business RSS, FT Companies RSS
- 2차 후보: The Guardian Business, World, Technology RSS

메모:

- 영국은 글로벌 기업 기사량이 많아 우선순위가 높다.

### 프랑스

- 1차 후보: Le Monde Economie RSS, France 24 Business / Tech RSS
- 2차 후보: Le Monde International RSS, France 24 Europe RSS

메모:

- 프랑스는 유럽 산업정책, 배터리, 자동차, 규제 기사에서 한국 기업 노출이 상대적으로 잦다.
- 르몽드는 프랑스어지만 구조가 안정적이고, France 24는 영문 유럽 기사 보강에 유리하다.

### 유럽권 공통

- 1차 후보: Euronews Business RSS, POLITICO Europe RSS

메모:

- 범유럽 매체는 국가 코드와 별도로 `EU` 묶음으로 관리한다.
- 개별 교역국과 달리 규제, 배터리, 자동차, 통상 정책 기사를 빨리 포착하는 데 강하다.
- Reuters, Telex처럼 영향력은 크지만 공식 피드 안정성이 떨어지는 매체는 후순위로 둔다.

## Google News를 보조 수단으로만 쓰는 이유

- 장점: 국가별 기사 발굴 범위가 넓다.
- 단점: 원문 출처가 다양해 도메인 관리가 없으면 품질이 흔들린다.

따라서 기본 원칙은 아래와 같다.

1. 직접 소스 수집이 우선
2. Google News는 누락 보완용
3. Google News 결과도 허용 도메인 목록에 있는 기사만 채택

## 구현 시 필요한 메타데이터

국가별로 아래 정보를 함께 둔다.

- country_code
- country_name_ko
- country_name_en
- priority
- languages
- allowed_domains
- excluded_domains
- primary_sources
- fallback_sources
- active

## 이후 YAML로 옮길 때 예시 형태

```yaml
- country_code: US
  country_name_ko: 미국
  country_name_en: United States
  priority: P1
  languages:
    - en
  allowed_domains:
    - cnbc.com
  excluded_domains:
    - yna.co.kr
    - chosun.com
    - joongang.co.kr
  primary_sources:
    - name: CNBC
      type: rss_or_feed
      status: candidate
  fallback_sources:
    - name: Google News US
      type: search_feed
      status: fallback_only
  active: true
```

## 참고 링크

- 한국무역협회 K-stat: https://stat.kita.net/stat/kts/ktsMain.screen
- 산업통상자원부 2025년 6월 및 상반기 수출입 동향: https://www.motie.go.kr/kor/article/ATCL3f49a5a8c/170672/view
- China Daily RSS: https://www.chinadaily.com.cn/test/node_1058381.htm
- Nikkei Asia RSS: https://info.asia.nikkei.com/rss
- VietnamPlus English RSS: https://en.vietnamplus.vn/rss.html
- VnExpress International RSS: https://e.vnexpress.net/rss
- Deutsche Welle RSS 안내: https://corporate.dw.com/de/rss-feeds/a-68615875
- tagesschau RSS 안내: https://www.tagesschau.de/infoservices/rssfeeds
- The Guardian RSS 안내: https://www.theguardian.com/help/feeds
- BBC News RSS 안내: https://feeds.bbci.co.uk/news/10628494
- U.S. DOJ Press Releases: https://www.justice.gov/news/press-releases
- U.S. DOJ RSS: https://www.justice.gov/news/rss?m=1&type=press_release
- Le Monde RSS: https://www.lemonde.fr/rss/
- France 24 RSS 예시: https://www.france24.com/en/business-tech/rss
- Euronews RSS: https://www.euronews.com/rss
- POLITICO Europe RSS: https://www.politico.eu/feed/
