대한민국 시·도 17곳의 경계는 geoBoundaries gbOpen KOR ADM1(KOR-ADM1-68945753, 2021년 기준), 원자료 Natural Earth 1:10m, Public Domain이다. geoBoundaries 배포물은 CC BY 4.0. 원본 형상은 유지하고 표시용 한국어 이름과 현행 시·도 코드 속성을 추가했다. 측량·필지 판정용 정밀도는 제공하지 않는다. 2021년 이후 경계 변경(예: 군위군 대구 편입)은 반영되지 않는다.
[메타데이터](https://www.geoboundaries.org/api/current/gbOpen/KOR/ADM1/) · [고정 원본](https://github.com/wmgeolab/geoBoundaries/blob/9469f09/releaseData/gbOpen/KOR/ADM1/geoBoundaries-KOR-ADM1.geojson) · [라이선스](https://creativecommons.org/licenses/by/4.0/)

2026-11-12 회귀 검사에서 각 시·도 내부의 공개 지점 17곳을 선택하고 SVG hit test와 지역 코드가 일치함을 확인했다. 광주시청 인근의 별도 점은 이 단순화된 자료에서 전남으로 판정됐다. 2023년 7월 1일 군위군이 경북에서 대구로 편입된 사실도 현행 경계와의 차이다. [대구광역시의회 정책연구보고서](https://council.daegu.go.kr/attach/bbs/policy/ab1d67791a2dee7056a026263d27ccf9.pdf)

경계를 교체할 때 properties.code는 기존 장소 테이블의 region_code와 호환돼야 한다. 기존 장소를 조회하거나 지도를 다시 그릴 때 좌표로 재분류하지 않는다. 신규·폐지 코드가 있으면 과거 코드의 표시 매핑과 신규 장소 판정 규칙을 먼저 마련한다. 기존 행의 일괄 재분류는 별도 이관 작업으로 관리한다.
