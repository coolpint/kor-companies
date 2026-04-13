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
| P2 | 캐나다 | 운영 확장 포함 | 북미 규제/시장 기사 보강 |
| P2 | 호주 | 운영 확장 포함 | 자원, 배터리, 공급망 기사 보강 |
| P2 | 인도 | 운영 확장 포함 | IT, 전자, 자동차, 투자 기사 보강 |
| P2 | 싱가포르 | 운영 확장 포함 | 동남아 허브 매체 보강 |
| P2 | 홍콩 | 운영 확장 포함 | SCMP로 중국/아시아 기업 기사 보강 |
| P2 | 대만 | 운영 확장 포함 | 반도체/공급망 기사 보강 |
| P3 | 네덜란드 | 운영 확장 포함 | EU 산업/반도체 공급망 보강 |
| P3 | 태국 | 운영 확장 포함 | 동남아 제조/자동차 기사 보강 |
| P3 | 멕시코 | 운영 확장 포함 | 북미 제조/투자 기사 보강 |
| P3 | 카타르 | 운영 확장 포함 | Al Jazeera로 중동/글로벌 기사 보강 |

## 향후 추가 후보 국가

- 인도네시아
- 말레이시아
- 사우디아라비아
- UAE

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
- 2차 후보: NYT Technology, Fox Business Markets, Fox Business Technology, CNBC Top/World/Technology, ABC News Business/International, U.S. DOJ Press Releases, U.S. SEC Press Releases, The Verge
- 보조 수단: Google News US 검색 결과에서 허용 도메인만 통과

메모:

- 미국은 소스는 많지만 사이트 구조가 자주 바뀌는 곳도 많다.
- 초기에는 직접 피드가 확인되는 소스 위주로 제한하는 편이 안전하다.
- DOJ 보도자료는 일반 기업 뉴스보다 빈도는 낮지만, 제재, 반독점, 수출통제, 형사수사 이슈를 빠르게 포착하는 데 유용하다.
- SEC 보도자료는 삼성전자, 하이닉스, 쿠팡 같은 미국 자본시장 연계 기업 이슈를 보강하는 데 도움이 된다.
- The Verge는 일반 경제지보다 전자, 플랫폼, 게임, AI 관련 한국 기업 노출이 잦다.

### 중국

- 1차 후보: China Daily BizChina, China Daily World
- 2차 후보: China Daily China, Global Times English

메모:

- 영문판 소스를 우선 사용하면 초기 구현 난도가 낮다.
- 필요하면 이후 중국어 키워드 별칭을 추가한다.

### 일본

- 1차 후보: Nikkei Asia RSS
- 2차 후보: NHK 계열 뉴스 피드 또는 비즈니스 섹션, Japan Today RSS

메모:

- 일본은 영문 기사와 일본어 기사 간 표현 차이가 있어 별칭 사전이 중요하다.
- Japan Today는 영문 일반 뉴스 피드지만 일본 내 기업·정책 이슈 보강에 유용하다.

### 베트남

- 1차 후보: VietnamPlus English RSS
- 2차 후보: VnExpress International RSS

메모:

- 베트남은 영문판이 있어 MVP에 적합하다.

### 독일

- 1차 후보: Deutsche Welle RSS
- 2차 후보: tagesschau Wirtschaft RSS, DER SPIEGEL International RSS

메모:

- 독일은 영문과 독문 소스를 병행할 수 있다.
- 기업 기사 비중은 DW보다 tagesschau Wirtschaft가 높을 수 있다.
- SPIEGEL 영문판은 유럽 내 산업정책과 지정학 맥락을 빠르게 잡는 데 유리하다.

### 영국

- 1차 후보: BBC News Business RSS, FT Companies RSS
- 2차 후보: The Guardian Business, World, Technology RSS, The Independent Business RSS

메모:

- 영국은 글로벌 기업 기사량이 많아 우선순위가 높다.
- The Independent는 신뢰도는 BBC/FT보다 낮지만 기사량 보강용 보조 소스로는 쓸 만하다.

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

### 캐나다

- 1차 후보: The Globe and Mail Business, The Globe and Mail World
- 2차 후보: Global News Money, Global News World
- 비활성 후보: CBC Business, CBC World

메모:

- CBC RSS는 후보 검증에서는 열렸지만 실제 수집에서 타임아웃이 발생해 기본 비활성화한다.

### 호주

- 1차 후보: ABC Australia Top Stories, ABC Australia Business

메모:

- 호주는 자원, 배터리 원료, 공급망 기사에서 한국 기업과 연결될 가능성이 있다.

### 인도

- 1차 후보: BusinessLine Companies, BusinessLine Economy
- 2차 후보: The Economic Times Industry, The Economic Times Tech

메모:

- 인도는 전자, 자동차, IT 서비스, 스타트업/플랫폼 투자 기사에서 한국 기업 노출 가능성이 높다.

### 싱가포르

- 1차 후보: CNA Business, CNA Asia, CNA World
- 2차 후보: The Straits Times Business, The Straits Times World

메모:

- 싱가포르는 동남아권 허브 성격이 강해 지역 비즈니스/정책 기사 보강에 유리하다.

### 홍콩

- 1차 후보: South China Morning Post Business, Tech, World

메모:

- SCMP는 중국·홍콩·아시아 공급망과 기술 기사 보강용으로 사용한다.

### 대만

- 1차 후보: Taipei Times RSS

메모:

- 반도체/공급망 관련 기사 보강용이다. 세부 비즈니스 RSS는 안정 URL 확인 후 추가한다.

### 네덜란드

- 1차 후보: DutchNews.nl, NL Times

메모:

- ASML 등 반도체 공급망과 EU 산업정책 이슈를 보강한다.

### 태국

- 1차 후보: Bangkok Post Business, Bangkok Post World

메모:

- 자동차/전자 제조 및 동남아 투자 기사 보강용이다.

### 멕시코

- 1차 후보: Mexico News Daily

메모:

- 북미 제조, 자동차, 공급망 투자 이슈 보강용이다.

### 카타르/중동

- 1차 후보: Al Jazeera RSS

메모:

- 국가 단위보다는 중동/글로벌 주요 이슈 보강용으로 사용한다.

## Google News를 기본 비활성 보조 수단으로 두는 이유

- 장점: 국가별 기사 발굴 범위가 넓다.
- 단점: 원문 출처가 다양하고 저품질/소비자성 소스가 많아 도메인 관리만으로 품질을 안정화하기 어렵다.

따라서 기본 원칙은 아래와 같다.

1. 직접 소스 수집이 우선
2. Google News는 기본 비활성화
3. 필요할 때만 일시적으로 켜고 결과를 검증
4. Google News 결과도 한국 매체, PR 배포망, 저품질 투자매체를 제외

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
- U.S. SEC Press Releases RSS: https://www.sec.gov/news/pressreleases.rss
- The Verge RSS: https://www.theverge.com/rss/index.xml
- Japan Today RSS: https://japantoday.com/feed
- DER SPIEGEL International RSS: https://www.spiegel.de/international/index.rss
- The Independent Business RSS: https://www.independent.co.uk/topic/business/rss
- Le Monde RSS: https://www.lemonde.fr/rss/
- France 24 RSS 예시: https://www.france24.com/en/business-tech/rss
- Euronews RSS: https://www.euronews.com/rss
- POLITICO Europe RSS: https://www.politico.eu/feed/
- CNBC RSS 예시: https://www.cnbc.com/id/100003114/device/rss/rss.html
- ABC News RSS 예시: https://abcnews.go.com/abcnews/businessheadlines
- The Globe and Mail RSS 예시: https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/
- Global News RSS 예시: https://globalnews.ca/money/feed/
- ABC Australia RSS 예시: https://www.abc.net.au/news/feed/51120/rss.xml
- Economic Times RSS 예시: https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms
- BusinessLine RSS 예시: https://www.thehindubusinessline.com/companies/?service=rss
- CNA RSS 예시: https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936
- Straits Times RSS 예시: https://www.straitstimes.com/news/business/rss.xml
- SCMP RSS 예시: https://www.scmp.com/rss/2/feed
- Taipei Times RSS: https://www.taipeitimes.com/xml/index.rss
- DutchNews RSS: https://www.dutchnews.nl/feed/
- NL Times RSS: https://nltimes.nl/rss
- Bangkok Post RSS 예시: https://www.bangkokpost.com/rss/data/business.xml
- Mexico News Daily RSS: https://mexiconewsdaily.com/feed/
- Al Jazeera RSS: https://www.aljazeera.com/xml/rss/all.xml
