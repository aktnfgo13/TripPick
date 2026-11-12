# Pleos 검증 • 2026-11-12
macOS 27.0.1 arm64, Git 2.54, Python 3.14.6. 최초 PATH에 JDK, Gradle, npm, adb, Go가 없고 Android Studio, 기본 Android SDK 및 AVD 디렉터리도 없었다.
[시작 가이드](https://document.pleos.ai/docs/pleos-only/getting-started)는 API 34와 minSdk 28+, Vehicle 2.3.1 예시를 제시한다. [한국어 릴리스](https://document.pleos.ai/docs/pleos-only/release-note/sdk-release-note)는 Vehicle 2.3.2, NaviHelper 3.0.5, FusedLocation 1.1.3을 표기한다. 버전 공개와 개별 앱의 접근 권한은 별도로 확인한다. FusedLocation은 필수 의존성에서 제외한다.
[Playground](https://developers.pleos.ai/playground)에서 [프로젝트 및 SDK 권한 신청](https://document.pleos.ai/docs/pleos-only/create-my-project) 후 [설치 가이드](https://document.pleos.ai/docs/connect/guide/getting-started/application-development/setup-connect-sdk-emulator)의 시스템 이미지로 AVD를 구성한다. [에뮬레이터 릴리스](https://document.pleos.ai/docs/pleos-only/release-note/emulator-release-note)와 실제 설치 버전을 함께 기록한다.
[NaviHelper 이벤트](https://document.pleos.ai/api-reference/connect-sdk-pleos/NaviHelper/event-listeners)는 목적지 조회·변경·도착 및 현재 위치 응답을 정의한다. 내비 구현·권한별 전달, 백그라운드·프로세스 종료 중 수신은 미검증이다. 3.0.5 좌표 생성자 순서는 위도, 경도다. [개발 가이드](https://document.pleos.ai/docs/pleos-only/vehicle-app-developer-guide/intro)와 [샘플](https://document.pleos.ai/docs/pleos-only/tutorial/vehicle-sdk-sample-app)을 기준으로 연결·해제를 검증한 뒤 도입한다.
[화면 모델](https://document.pleos.ai/docs/pleos-only/vehicle-app-planning-guide/app-structure-screen-model)에 따라 회전·분할을 허용한다. [주행 제한](https://document.pleos.ai/docs/pleos-only/vehicle-app-developer-guide/driving-restriction-development-guide)에 따라 DO를 선언하지 않는다. 이후 CarUxRestrictionsManager의 초기 상태·변경·서비스 단절 시 조작 차단을 확인한다. 현재 차량 화면은 조작 없는 안내 화면이다.
[폼 팩터 테스트](https://document.pleos.ai/docs/pleos-only/app-test-guide/form-factor-test-guide)는 별도 창의 Pleos AVD, Go 1.22+, adb, 포트 8095/8096이 필요하다. [등록 태그](https://document.pleos.ai/docs/pleos-only/app-registration-guide/app-tagging-guide) 및 카테고리 심사는 배포 전 확인한다. 차량 서비스 권한·실행 검증 결과가 없어 SDK 연동 및 배포 적합성은 미확정이다.
Mac 공식 이미지 저장소 XML 조회 성공. API 34 arm64, Emulator v2.1.0, 압축 4,669,762,816바이트, 별도 42dot SDK 약관을 확인했다. 이미지는 설치하지 않았다. 공식 Maven의 Vehicle 2.3.2 POM은 HTTP 200으로 확인했다.

## Phase 1.5 실측
사용자가 42dot 약관에 동의한 뒤 공식 arm64 v2.1.0 시스템 이미지와 호스트 Emulator를 설치했다. SDK 도구를 표준 cmdline-tools/latest 위치로 배치한 뒤 기기 프로필 ID Pleos_Connect_v2_0로 TripPick_Pleos AVD를 생성했다. RAM 4096 MiB, host GPU, 별도 창 cold boot 14.2초. 부팅 중 ColorBuffer 경고가 있었으나 UI 트리와 스크린샷 생성에 성공했다.
기존 기본 APK와 Vehicle 2.3.2 포함 APK 각각 adb install -r 성공, am start -S -W Status ok (714ms / 437ms), 둘 모두 TripPick 및 차량 서비스 미연결 텍스트를 확인했다. 이 두 바이너리는 SDK 초기화를 호출하지 않는다.

Phase 3-A: 공식 Maven NaviHelper 3.0.5 AAR와 navi-data 3.0.4 확인. NAVI_ROUTE 및 AAR의 service query 병합. Vehicle 2.3.2 유지. API 34 공식 AVD 설치·cold launch 535ms. SDK 실제 로그 onConnected → DESTINATION → LOCATION(각 조회 응답). 콜백 전달은 유효한 목적지·도착 여행의 증명이 아니다. 변경·도착 이벤트는 이 검사에서 관측되지 않았다. 앱 onStop 시 리스너 제거·release, 재진입 시 재연결한다.

## Phase 3 생명주기 관측
사용자가 ACTIVE 여행에서 기록을 켠 뒤 Virtual Console의 주행 제한 화면과 주차 복귀를 확인했다. 주행 전환 구간과 HOME 직후 3초 동안 새 이벤트는 관측되지 않았다. 강제 종료 후 프로세스가 없었고 AVD 재부팅 직후에도 앱은 자동 실행되지 않았다. 사용자가 다시 실행하면 진행 중 여행·기록 설정을 복원하고 NaviHelper가 연결됐다. 주행 내내 위치가 연속 수집되는지, 목적지 변경 및 실제 도착이 전달되는지는 확인하지 못했다.
