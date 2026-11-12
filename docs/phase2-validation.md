# Phase 1.5·2 검증 기록 • 2026-11-12

## 실제 환경과 결과
macOS arm64, JDK 17, Gradle 8.7, API 34, 공식 Pleos Connect v2.1.0 arm64 AVD에서 실행했다. Android Studio 대신 SDK CLI와 독립 Emulator 창을 사용했다. 기존 Phase 1 기본 APK와 SDK 포함 APK 모두 설치·cold launch·UI 텍스트 확인에 성공했다. Phase 2는 기본 및 Vehicle 2.3.2 포함 debug 빌드, 각 설정의 JVM 단위 테스트 1건, 양쪽 APK 서명 검사를 통과했다. 최종 통합 테스트는 SDK 포함 APK를 사용했다.

- SDK 초기화 호출, Android 서비스 바인딩, 실제 CarInfo capability 콜백(available=true)을 각각 확인했다. VIN 자체를 요청하지 않았다. 초기 전체 capability 호출은 권한 오류였고, 공식 읽기 권한을 디버그 SDK 설정에 선언한 개별 capability 조회로 검증했다. 주행 제한은 SDK probe와 독립적으로 android.car의 CarUxRestrictionsManager에서 읽는다. android.car를 필수 공유 라이브러리로 선언하면 공식 이미지에서 INSTALL_FAILED_MISSING_SHARED_LIBRARY가 발생해 optional 선언으로 수정했다.
- 공식 Virtual Console 8088에서 실제 브라우저 heartbeat가 있어야 입력을 받았다. 단순 HTTP 제어 시 emulator_inactive, 브라우저 활성화 후 Drive·움직임 적용 성공. 최종 테스트에서 콘솔 속도 32km/h일 때 차량 UI 트리에 제한 안내만 표시됐다. 속도는 자극을 확인하는 테스트 값이며 앱은 공식 제한 상태만 사용한다. 이후 속도 0과 Park로 복구했다.
- FormFactorConsoleActivity 기동 성공. 공식 Host Display Bridge가 AVD의 gRPC 서비스에 연결됐다. 1440×2560 세로, 2560×1440 가로 DISPLAY2 생성·삭제에 성공했고 각 논리 디스플레이에 앱의 topResumedActivity를 확인했다. 재생성하면 Android 논리 ID가 바뀐다. 모든 해상도의 시각 품질과 터치 영역을 수동 검수한 결과는 없다.
- Python unittest 5건 통과. Phase 1 DB 001 → 002 업그레이드, 재초기화·기존 객체 보존, DB 누락, 초대/소유권 재사용 거부, 교차 여행 차단, 이미지 검증·재전송, 동시 중복 투표·취소, 계정 일치 검사, 앨범 권한·revision 충돌, 서버 재시작, WebSocket·만료·Origin 검사를 포함한다. TestClient의 httpx에 대한 라이브러리 사용 중단 예정 경고가 있다.
- Vue 상태 단위 테스트 2건, vue-tsc와 Vite 프로덕션 빌드 통과. 브라우저 통합 검사에서 FastAPI 스레드풀이 요청별 SQLite 연결을 다른 스레드에서 종료하는 오류를 발견해 수정했다. 같은 탭에 다른 QR을 열 때 fragment 전환도 처리했다.
- 실제 차량 UI에서 생성한 여행의 QR을 화면 픽셀에서 판독했다. Chrome의 독립된 쿠키 저장소 4개가 관리자 1명·일반 회원 3명으로 참여하고 각자 사진 1장을 업로드했다. 한 번의 전송을 의도적으로 차단한 뒤 재시도 버튼으로 복구했다. 모든 브라우저에 사진 4장이 표시됐다.
- 회원 휴대폰에서 계정 연결 QR을 확인하고 차량 상세 화면에서 해당 회원의 투표를 취소·재등록했다. 휴대폰의 표가 각각 0·1로 변경됐다. 앱 강제 종료·재실행 후 같은 상세 사진을 복원했다. 차량에서 좋아요 후보를 확정하고 네 브라우저 모두 동일 앨범에서 파일을 내려받아 PNG로 열었다. 차량에서 공유 앨범을 다시 열어 확정된 사진 1장을 확인했다.
- AVD ↔ 호스트 HTTP, Chrome ↔ 로컬 HTTPS를 같은 DB에 연결했다. 로컬 테스트 주소는 사용자가 선택했다. 실물 휴대폰·실차·공개 HTTPS 배포 결과는 없다.

## 재현
README의 기본 서버와 웹 빌드를 준비한다. 테스트 전용 디렉터리에 DB를 두고 TRIPPICK_DATA_DIR와 TRIPPICK_WEB_DIST에 절대 경로를 지정한다. 같은 설정으로 127.0.0.1:8000과 127.0.0.1:18443을 실행한다. 후자는 uvicorn의 --ssl-keyfile, --ssl-certfile로 테스트 인증서를 지정한다. 테스트 전용 Chrome은 TRIPPICK_TEST_LOOPBACK=1일 때만 trippick.test를 루프백에 매핑하고 임시 인증서를 허용한다. 일반 사용자 브라우저나 앱의 TLS 검사는 변경하지 않는다.

    ./gradlew -PwithPleosSdk=true -PwebOrigin=https://trippick.test:18443 assembleDebug
    adb -e install -r app/build/outputs/apk/debug/app-debug.apk
    adb -e shell am start -n kr.trippick.vehicle/kr.trippick.MainActivity

저장소 루트에서 전용 가상환경으로 실행한다. Chrome이 설치돼 있어야 하며 정차 상태의 테스트 AVD 한 대가 필요하다.

    python -m pip install -r tests/integration/requirements.txt
    TRIPPICK_TEST_LOOPBACK=1 python tests/integration/pleos_album.py

실제 전화기는 별도 DNS와 신뢰되는 HTTPS 인증서가 있는 개발 서버를 사용한다. Vite dev 서버를 공개하지 않고 배포용 dist와 /api를 동일한 TLS 프록시 뒤에 둔다. 프록시에서 원래 Host 및 WebSocket 업그레이드를 전달한다. 공개 터널은 이번 검증에서 열지 않았다.

## 코드 리뷰 및 남은 한계
차량 SDK·이미지 처리·미리보기·세션 복원을 분리했다. 참여자별 멱등 키, 트랜잭션과 복합 FK, 앨범 revision 및 차량 쓰기 시 예상 계정 확인이 재시도·동시 요청의 결과를 보호한다. 사진 원본과 미리보기는 비공개이며 앨범 수정으로 원본을 삭제하지 않는다.
현재 앱은 메타데이터 페이지들을 모두 순회한다. 사진 수가 큰 여행에서는 revision이 바뀐 경우에만 페이지를 갱신하고 뷰포트 기준으로 필요한 페이지를 가져오는 방식으로 개선할 수 있다. SQLite와 객체 파일 사이의 프로세스 강제 종료는 고아 파일을 남길 수 있어 대규모 운영 전 정합성 점검 작업이 필요하다. 긴 여행의 초대·차량 재발급, 쿠키를 잃은 소유자 복구, 공개 환경의 차량 등록 및 생성 요청 제한은 후속 설계 대상이다. HEIC는 현재 Pillow 환경에서 디코더가 등록되지 않아 JPEG·PNG만 수락한다.
