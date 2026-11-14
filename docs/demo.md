# TripPick 시연

1. 공식 Pleos AVD의 기본 화면에서 Park 상태와 조작 허용을 확인한다. 여행 제목을 입력하고 **여행 생성**을 누른다.
2. 관리자 한 명이 **소유권 QR**을 스캔하고 닉네임을 입력한다. 동행자는 **참여 QR**을 사용한다. 카메라 인식이 어려우면 일반 참여 QR 아래의 홈페이지를 열고 참여 코드를 붙여 넣는다. 관리자 QR·복구 코드는 개인적으로 보관한다.
3. 휴대폰에서 JPEG 또는 PNG를 선택하고 완료 표시를 기다린다. 실패한 항목의 **재시도**를 누르면 같은 업로드 키를 재사용한다. 차량의 **계정 연결** QR을 이미 참여한 휴대폰에서 확인하면 두 기기가 같은 이름으로 투표한다.
4. **전체 사진**의 좋아요를 고르고 관리자 차량에서 **최종 선정 → 앨범 확정**을 누른다. 참여자는 휴대폰의 **공유 앨범 → 원본 다운로드**를 사용한다.
5. **여행 지도**에서 시·도를 선택하고 방문 장소를 눌러 연결 사진을 연다. 자동 기록이 어려운 환경에서는 관리자 웹에서 방문 장소를 직접 등록할 수 있다.

## 로컬 재현

저장소 루트 기준으로 README의 Python·Node·JDK·SDK 준비를 따른다. 테스트 DB는 기존 여행과 별도 디렉터리를 지정한다. 같은 DB와 objects를 사용하는 FastAPI 인스턴스에 차량 API와 모바일 웹이 연결되어야 한다.

- 이번 시연 APK는 앱 ID kr.trippick.vehicle.demo, 차량 HTTP 10.0.2.2:18083, 모바일 HTTPS trippick.test:19446을 사용한다.
- backend에서 TRIPPICK_DATA_DIR와 TRIPPICK_WEB_DIST를 절대 경로로 설정하고 uvicorn app.main:app --host 127.0.0.1 --port 18083을 실행한다. 동일 설정에서 테스트 인증서를 가진 HTTPS 리스너를 19446에 준비한다. 인증서 개인 키는 공유 파일에 포함하지 않는다.
- 공식 Pleos Connect Emulator 2.1.0을 부팅하고 adb install -r로 시연 APK를 설치한다. tests/integration/pleos_album.py에는 TRIPPICK_TEST_PACKAGE=kr.trippick.vehicle.demo, TRIPPICK_TEST_LOOPBACK=1, TRIPPICK_TEST_JOURNAL=1을 지정한다. 테스트 Chrome이 trippick.test를 loopback에 매핑한다.
- 폼 팩터 검사는 공식 Host Display Bridge와 FormFactorConsole로 별도 창에서 실행한다. 사용 허용 상태가 확인돼야 사진을 조작할 수 있다. [공식 가이드](https://document.pleos.ai/docs/pleos-only/app-test-guide/form-factor-test-guide)
