# 감시 대상 한국 기업 기준 및 초기 시드

## 목적

해외 언론에서 자주 등장할 가능성이 높은 한국 기업을 관리한다.

이 문서는 사람이 읽고 수정하는 기준 문서다. 구현 단계에서는 같은 구조를 YAML 설정으로 옮긴다.

## 기본 선정 원칙

1. 기본 모수는 공정위 기준 대기업집단 상위권 그룹이다.
2. 해외 언론 노출 빈도가 높은 비그룹 독립 기업은 추가한다.
3. 그룹 전체를 전부 넣지 않고, 해외 기사에 직접 등장할 가능성이 높은 대표 회사와 대표 브랜드를 우선 넣는다.
4. 계열사 수가 너무 많으면 "그룹 대표사 + 핵심 상장사"까지만 시작한다.

## 갱신 원칙

- 정기 갱신: 분기 1회
- 대규모 조정: 공정위 공시대상기업집단 지정 결과 발표 이후
- 수시 갱신: 사용자가 직접 추가/비활성화 가능

## 관리 단위

회사 하나를 아래 정보로 관리한다.

- canonical_name_ko
- canonical_name_en
- group_name
- aliases_en
- aliases_ko
- aliases_local
- primary_brands
- ticker
- active
- notes

## 별칭 관리 규칙

### 꼭 넣어야 하는 것

- 영문 정식명
- 한국어 표기
- 자주 쓰는 짧은 표기
- 대표 브랜드명
- 해외 기사에서 흔한 변형

### 주의할 것

- 너무 일반적인 단어만 있는 별칭은 금지한다.
- 예: `SK`, `LG`, `KT` 같은 짧은 문자열은 단독 매칭 시 오탐이 많다.
- 이런 경우에는 `SK hynix`, `LG Energy Solution`, `KT Corp` 같이 긴 별칭을 우선 쓴다.

## 초기 시드 구성 방식

- Tier A: 해외 언론 노출 빈도가 높고 글로벌 사업 비중이 큰 기업
- Tier B: 대형 그룹이지만 해외 일반 언론 노출 빈도는 상대적으로 낮은 기업
- Tier C: 추후 추가 후보

## Tier A 초기 시드

아래 목록은 운영 시작용 초안이다. 최종 확정 전에 공정위 최신 자료와 실제 해외 기사 빈도로 한 번 더 보정한다.

| 구분 | 대표 회사/그룹 | 핵심 추적 대상 예시 |
| --- | --- | --- |
| A | 삼성 | Samsung Electronics, Samsung SDI, Samsung Biologics, Samsung Heavy Industries |
| A | SK | SK hynix, SK Innovation, SK Telecom |
| A | 현대자동차그룹 | Hyundai Motor, Kia, Hyundai Mobis |
| A | LG | LG Electronics, LG Energy Solution, LG Chem, LG Display |
| A | 포스코 | POSCO Holdings, POSCO Future M |
| A | 한화 | Hanwha Aerospace, Hanwha Ocean, Hanwha Solutions |
| A | HD현대 | HD Hyundai, HD Hyundai Heavy Industries, HD Hyundai Electric |
| A | 롯데 | Lotte Group, Lotte Chemical |
| A | CJ | CJ CheilJedang, CJ ENM |
| A | 네이버 | NAVER |
| A | 카카오 | Kakao |
| A | HYBE | HYBE |
| A | 쿠팡 | Coupang |
| A | 셀트리온 | Celltrion |
| A | 대한항공/한진 | Korean Air, Hanjin KAL |

## Tier B 초기 시드

| 구분 | 대표 회사/그룹 | 핵심 추적 대상 예시 |
| --- | --- | --- |
| B | GS | GS, GS Caltex, GS E&C |
| B | 두산 | Doosan Enerbility, Doosan Bobcat |
| B | LS | LS Electric |
| B | 한국항공우주산업 | Korea Aerospace Industries |
| B | 아모레퍼시픽 | Amorepacific |
| B | 신세계 | Shinsegae, E-Mart |
| B | 효성 | Hyosung, Hyosung Heavy Industries |
| B | KT | KT Corp |
| B | KT&G | KT&G |
| B | 미래에셋 | Mirae Asset |
| B | 메리츠 | Meritz Financial |

## Tier C 추가 후보

- OCI
- 에코프로
- 고려아연
- 한진중공업 계열 재편 대상
- 게임/플랫폼 계열 추가 후보
- 방산/배터리/바이오 업종의 신규 부상 기업

## 구현 전 확정해야 할 정책

1. 그룹 단위만 볼지, 계열 상장사까지 분리할지
2. 쿠팡처럼 한국계이지만 해외 상장/해외 법인 중심 기업을 포함할지
3. 네이버, 카카오처럼 플랫폼 기업을 몇 개까지 별도 포함할지
4. 바이오/방산/배터리 업종의 독립 대형주를 어디까지 포함할지

## 이후 YAML로 옮길 때 예시 형태

```yaml
- canonical_name_ko: 삼성전자
  canonical_name_en: Samsung Electronics
  group_name: 삼성
  aliases_en:
    - Samsung Electronics
    - Samsung Elec
    - Samsung
  aliases_ko:
    - 삼성전자
    - 삼성
  primary_brands:
    - Galaxy
  ticker:
    - KRX:005930
  active: true
  notes: 글로벌 일반 뉴스와 산업 뉴스 모두에서 우선순위가 높음
```

## 참고 기준

- 공정위 2025년 공시대상기업집단 지정 결과: https://www.ftc.go.kr/www/selectBbsNttView.do?bordCd=3&key=12&nttSn=46053&searchCtgry=01%2C02
