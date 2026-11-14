# Phase 3.6 — DISPLAY2와 행정구역 검증

2026-11-13, 기준 커밋 ac8b129. Phase 3.5 기본·SDK APK의 SHA-256을 직전 보고서와 대조하고 동일한 파일을 보존했다. 3.6은 별도 파일과 테스트 DB를 쓴다. 로컬 차량 HTTP 포트는 18082, Chrome용 QR은 https://trippick.test:19445다.

## 공식 문의용 DISPLAY2 재현

별도 창의 공식 Pleos Connect v2.1.0 arm64 API 34 AVD, Vehicle 2.3.2, NaviHelper 3.0.5. 공식 콘솔이 쓰는 8096에 이전 AVD의 인증값으로 실행 중이던 호스트 브리지가 남아 있었다. 해당 브리지만 현재 AVD에 다시 연결한 뒤 Refresh에서 DISCONNECTED, 가상 화면 생성 뒤 CONNECTED를 확인했다. [공식 절차](https://document.pleos.ai/docs/pleos-only/app-test-guide/form-factor-test-guide)

1. AVD에서 FormFactorConsoleActivity 실행 → Connect-S 12.9″ Portrait 선택 → 가상 디스플레이 생성 → 앱 목록 실행 → DISPLAY2 목록의 TripPick 터치.
2. 현재 Activity의 표시 ID, WindowManager 프레임, UI Automator 루트, CarUxRestrictionsManagerService 등록 목록을 같은 시점에 비교한다.
3. 가상 디스플레이 제거 후 14.6″ Landscape로 반복한다. 장치 참고 해상도와 생성되는 테스트 창 해상도가 다르므로 콘솔이 표시하는 실제 생성값을 기록한다.

|항목|12.9인치 Portrait|14.6인치 Landscape|
|---|---|---|
|논리 display ID / 물리 슬롯|3 / 2|4 / 2|
|콘솔·Configuration|628×855 dp, 160 dpi, port|1360×948 dp, 200 dpi, land|
|실제 px, Window bounds, mAppBounds 및 UI 루트|[0,0]–[628,855]|[0,0]–[1700,1185]|
|WindowManager parent/display/frame|모두 628×855|모두 1700×1185|
|제한 안내 Text의 실제 bounds|[32,32]–[392,56]|[40,40]–[480,70]|

두 화면 모두 해당 display의 topResumedActivity는 kr.trippick.vehicle/kr.trippick.MainActivity였다. 설정상 앱 영역과 창 경계의 차이는 네 변 모두 0px였다. 이 값은 프레임 차이이고, 개별 IME·systemBars 타입에 대한 WindowInsets API 반환값은 계측하지 않았다.

**A — 앱 레이아웃.** 독립 실행의 Activity 창과 렌더링 루트는 전체 프리셋 크기를 차지했고 제한 문구는 양쪽 모두 영역 안에 있었다. Phase 3.5의 기존 작업 이동 캡처에서는 이전 작업 크기와 DISPLAY2 크기가 달라 검은 바탕과 잘림이 나타났다. 세로 측정의 WindowManager 목록에는 현행 전체 크기 프레임 외에 2560×1440 프레임도 있었다. 앱은 루트 fillMaxSize와 지도 Canvas의 실제 측정 크기를 사용한다. 기존 작업의 시스템 프레임보다 큰 영역을 앱에서 강제하지 않았다. 이동 창의 원인은 창 크기 불일치까지 확인했고 플랫폼 내부 원인은 미확인이다. [이동 창과 기본 화면 캡처](phase3_5-validation.md)

**B/C — 표시 장치별 안전 정보.** Park에서 두 독립 DISPLAY2 모두 주행 제한 안내만 표시했다. 같은 시점 car_service의 UX 대상 목록에는 display 0, DO false, UxR 0 한 줄만 있었다. 안전 로직은 해당 Activity의 차량 서비스에 listener를 등록하고 현재 제한을 조회한다. 제한이 없다는 공식 응답을 받아야 사진 조작이 가능하다. 이 이미지에서 나타나는 display별 서비스 제공 차이와 일치한다. 실차 전체에 일반화할 수 없다.

**D — 문의 항목.** FormFactorConsole이 생성한 DISPLAY2에 occupant zone과 UX 제한 구성을 제공하는 공식 방법이 있는지, 기존 작업을 이동하면 원래 크기 프레임이 남는 것이 의도된 동작인지 확인이 필요하다. 동일 안전 API를 쓰는 별도 공식 샘플과 실차는 비교하지 못했다. 독립 DISPLAY2의 사진·앨범·지도 조작은 미해결이다. 외부 문의는 발송하지 않았다.

## 좌표 판정과 행정구역

기존 광주청사 주소 지점은 원자료의 광주 외곽 링 밖, 전남 외곽 링 안, 전남의 광주 제외 홀 밖에 있다. 옛 자료에 대해 경도·위도를 같은 순서로 직접 판정해도 전남이었다. 2021년에 이미 구분되던 두 관할의 단순화된 형상 자체가 해당 지점을 잘못 포함했다. 통합 후의 12 판정과 역사적 오분류를 구분한다.

행정안전부 2026-07-01 시행 KIKcd_B 원문에서 1200000000과 생성일을 확인했다. 특별법 제7조에 따라 29와 46의 현재 표시 코드는 12다. 현재 전국 카탈로그는 16개 항목이다. 기존 두 도형을 합집합으로 가공했고, 기타 경계와 해안선은 geoBoundaries 2021년 자료를 사용한다. 현재 법정 관할과 2021년 기하 정밀도가 다르다. [행정안전부 변경내역](https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=127039) · [광주 공식 안내](https://news.gwangju.go.kr/gallery.es?act=view&bid=0009&cg_code=C02&list_no=5311&mid=a40200000000) · [지도 버전·라이선스](../assets/maps/SOURCE.md)

- assets/maps/catalog.json과 합집합 GeoJSON이 명칭, 코드 대응, 유효일과 도형을 제공한다. backend/app/services/regions.py가 좌표를 판정하고 journal API가 저장된 region_code를 현재 카탈로그로 투영한다. 응답의 stored_region_code는 DB에 이미 저장된 값을 보존한다. 원본 사진, 방문·장소 ID, 사진 연결과 앨범의 스키마 및 데이터는 수정하지 않는다.
- 모바일 SVG와 차량 Compose가 같은 API를 읽는다. 웹은 광주·전남·과거 정식 명칭 검색을 지원한다. 차량은 과거에 선택한 지역과 장소를 현재 지역으로 복원한다. 사진이 어느 옛 관할에서 촬영됐는지 현행 좌표만으로 역산하지 않는다.
- 경계선·꼭짓점, 둘 이상의 지역에 겹치는 내부, 영역 밖은 미확인으로 반환한다. 홀과 분리된 섬, 경계 양쪽의 점을 별도로 시험했다. 좌표계 변환이나 전국 실측 경계 교체는 하지 않았다.
- 청사 주소 8곳을 Esri World Geocoding Service의 WGS84 주소 매칭 점수 100으로 확인했다. 광주청사(내방로 111)·무안청사(오룡길 1)는 12, 대전시청(둔산로 100)은 30, 충남도청(충남대로 21)·천안시청(번영로 156)은 44, 충북도청(상당로 82)은 43, 서울시청(세종대로 110)은 11, 제주도청(문연로 6)은 50으로 통과했다. 이 좌표는 주소 지오코딩 결과다. 정부 청사 전자지도의 원본 측량·기준점과의 수치 일치는 별도 검증 대상이다. [Esri GeocodeServer](https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer) · [정부 민원행정기관 전자지도](https://business.juso.go.kr/jst/jstAddressDownload?menu=30)

후속 경계 교체 후보는 국토교통부 WFS lt_c_adsido_info다. 배포본의 기준일·실제 광주/전남 통합 반영·군위군 경계·좌표계·재배포 조건을 비교한 뒤 형상만 교체할 수 있다. 현재 자료로 필지·경계 인근의 법정 관할을 보증하지 않는다. [국토교통부 행정구역도](https://www.data.go.kr/data/15059008/openapi.do)

## 자동 검사와 배포 파일

기본·Pleos 설정에서 clean assembleDebug와 testDebugUnitTest를 각각 통과했다. 두 APK 모두 apksigner verify 통과. 최초 증분 빌드는 생성 디렉터리 안의 중복 DEX로 실패해 Gradle clean 후 다시 빌드했다. 기본 APK의 SHA-256은 206c80325a0cca9ff8fbb3dd375e7cb7d68c56ca3e9ac243c64e69a3b85fab66, SDK판은 9640dcf4a40ef1f34b8f5710dc90e39f7b8ff440f6d46830a4010f8ed62025b7이다.

- 백엔드 11건, 웹 2건과 배포 빌드, 현재 시·도 전체의 실제 Chrome SVG 선택·핀·필터 검사를 통과했다. 기존 코드 29·46으로 저장된 두 장소가 응답에서 12로 조회되고 같은 사진·방문 연결을 유지하는 회귀를 포함한다.
- 공식 AVD와 독립 Chrome 4개에서 참여 QR 판독, 사진 업로드, 같은 사용자 좋아요 취소·재등록, 강제 종료 후 상세 복원, 앨범 확정과 네 원본 다운로드, 충남 수동 장소의 모바일·차량 지도 열람을 통과했다. 광주·전남 별칭 검색도 같은 실행에서 확인했다.
- 자동 기록 시작 후 NaviHelper 연결과 listener release를 관측했다. 11월 14일 재실행에서는 연결 직후 실제 LOCATION과 DESTINATION 콜백을 두 번의 연결에서 각각 확인했다. 실제 도착이나 목적지 변경은 미관측이다.
- 민원행정기관 전자지도 공식 사이트에서 월별 원본 신청에 휴대폰 또는 간편 본인인증이 필요함을 확인했다. 청사 8곳의 회귀는 공개 주소 지오코딩 값 기준이다.

## 11월 14일 재검증

이전 만료 시험의 SQL 보호 조건이 실패한 원인은 재사용된 여행 제목 필드에 기존 접두사가 남은 것이었다. 새 여행을 생성할 때 입력 전체를 선택·삭제한 뒤 정확한 제목을 입력하는 테스트 도우미로 통일했다. 새 여행에서 앨범 확정 및 네 브라우저의 원본 다운로드를 다시 확인했다. 서버 DB에는 실제 LOCATION 후보와 MANUAL 시험 장소가 서로 다른 출처로 남았다.

반복 실행 중 앨범 다운로드 후 차량 지도 최초 조회가 한 번 실패했다. 당시 호스트 health와 regions는 각각 정상 응답했고 AVD dumpsys connectivity의 active default network는 none이었다. 기기·서버 중 어느 쪽에서 해당 요청이 끊겼는지는 이 로그만으로 확정할 수 없다. 이전 최종 APK 실행의 차량 지도·사진 열람 성공과 구분한다.
