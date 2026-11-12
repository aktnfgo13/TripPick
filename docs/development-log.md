2026-11-12 Phase 0: 빈 저장소 초기화, 환경 조사·공식 문서 대조·계약 검토. 도메인 API는 설계에만 존재한다.

## 2026-11-12 • Phase 1
- Python 3.14.6 / FastAPI. unittest discover로 2건 통과: 재시작 후 SQLite 초기화·저장 객체 재조회, DB 유실 시 503. TestClient의 httpx 사용 중단 예정 경고가 있었다.
- Node 24.19 / Vue 3.5.22. npm test 2건 통과, vue-tsc 및 Vite 7.1.11 배포 빌드 성공. 임시 포트에서 실제 Uvicorn 200, Vite HTML 200, Vite 프록시 경유 health 200 확인. 최초 IPv4 검사에서 Vite 기본 localhost 바인딩과 주소가 달라 명시적으로 127.0.0.1을 사용했다.
- 사용자 동의 후 작업용 Android API 34와 Build-Tools 34.0.0 설치. JDK 17.0.21 / Gradle 8.7 / AGP 8.5.2. 첫 빌드의 Java 8/Kotlin 17 타깃 충돌을 양쪽 17로 수정했다. assembleDebug와 testDebugUnitTest가 기본·Vehicle 2.3.2 포함 설정 모두 성공했다. 각 설정의 동일 시작 상태 단위 테스트 1건 통과. APK 둘 모두 디버그 서명을 검증했다.
- 실제 연동: 웹/HTTP/SQLite/파일 저장, 공식 Vehicle AAR의 빌드 의존성 해결 및 패키징. 차량 상태는 미연결 안내이며 주행·위치 이벤트를 합성하지 않는다. 사용자 여행 데이터, R2, Supabase, WebSocket, NaviHelper 호출은 후속 단계다.
- Pleos AVD, 화면 크기·분할·주행 제한·백그라운드 동작 및 모바일 실기기는 미실행. 다음 검증은 공식 이미지의 별도 약관 확인 후 APK 설치·기동, FormFactorConsole 검사다. 기본 환경 회귀 후 Phase 2를 별도 변경으로 시작한다.
