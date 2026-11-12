# 검증 순서
1. 기초 회귀: 빈 DB 시작 → 두 번째 시작 → 버전 보존, 사설 객체 저장/조회, HTTP 상태 및 저장소 장애, 웹 상태 분기·배포 빌드, Android debug APK·단위 테스트.
2. 여행 생성·소유권 재접속·QR 가입, 다른 여행 접근 거부, 중복 가입/투표, 업로드 재시도·중복·위장 MIME·HEIC·권한, 앨범 확정 충돌과 방문 위치 수동 정정.
3. iPhone Safari/Android Chrome에서 다중 업로드·실패 복구·좋아요·앨범 열람과 다운로드. 두 브라우저와 Pleos에서 같은 여행을 열고 사진·투표·최종 순서가 재연결/재시작 뒤 일치하는지 비교.
4. Pleos APK 설치·시작·종료·QR·사진 선택·복원, portrait/landscape·분할, 정차/주행/상태 불명 전환. NaviHelper 목적지·도착·위치를 전경/배경/종료 후 각각 기록. 권한 철회 시 앨범 열람 지속. 후속 검증은 구현된 단계에서만 실행한다.

Phase 2에서 실제 수행한 개별 테스트와 4개 브라우저 + 공식 AVD 통합 시험 결과는 phase2-validation.md에 기록한다. iPhone Safari·실차 검증, 방문 위치·분석은 후속 범위다.

Phase 3 회귀에는 tests/test_recovery.py, test_photo_pages.py, test_journal.py와 확장된 test_collaboration.py를 사용한다. 백엔드에서 세션 회전·오입력 잠금·동시 PUT/DELETE·동시 앨범 저장·WS 재접속, JPEG EXIF 위도/경도 및 UTC 변환, 인접한 충남·충북·대전 판정, DB 재시작·충돌·수동 연결을 확인한다. 전용 Pleos AVD에서 TRIPPICK_TEST_JOURNAL=1로 브라우저 4개와 차량의 공유 흐름을 실행한다. 시뮬레이션 fixture, 수동 지점, 실제 SDK 응답을 별도 기록한다. 생명주기·폼 팩터 및 실제 이벤트 검증 기록은 phase3-validation.md에 있다.
