# TripPick
Pleos 차량에서 여행을 만들고 참여자는 휴대폰 웹에서 사진을 올린다. 같은 참여자로 차량·휴대폰에서 투표하고 관리자가 확정한 앨범을 휴대폰에서 내려받을 수 있다. Phase 0·1 기준점은 Git 이력에 보존되어 있다.

## Phase 2 실행
1. 아래 모바일 웹 절차로 npm ci, npm run build를 실행한다. 서버 터미널에서 backend 디렉터리로 이동해 의존성을 설치한다.
2. 서버 시작 전에 `export TRIPPICK_WEB_DIST="$(cd ../apps/mobile-web/dist && pwd)"`를 설정하면 FastAPI가 모바일 배포 파일과 /api/v1을 한 출처에서 제공한다. DB와 파일은 TRIPPICK_DATA_DIR 아래에 보관한다. 서버 여러 개를 시작할 때는 동일한 절대 경로를 사용한다.
3. AVD 디버깅은 호스트의 127.0.0.1:8000으로 서버를 실행한다. 앱의 기본 apiOrigin은 http://10.0.2.2:8000 이다. 실물 휴대폰에는 직접 제어하는 HTTPS 개발 도메인을 준비한다. 해당 도메인의 TLS 역방향 프록시가 같은 FastAPI 포트로 HTTP와 WebSocket을 전달하고 원래 Host를 보존하도록 설정한다. 테스트 전용 접근 정책과 업로드 크기·요청 수 제한을 설정한다. 로컬 개발 시 쿠키 기본값은 Secure/HttpOnly/SameSite=Strict다.
4. 앱에서 쓸 모바일 HTTPS 주소를 아래 Gradle 명령의 YOUR-TEST-HOST에 넣고 APK를 설치한다. 공개 주소 없이 검증한 통합 테스트는 trippick.test를 테스트용 Chrome 안에서만 127.0.0.1로 매핑한다. 제공 APK의 QR은 이 로컬 테스트 주소를 사용한다.
5. 정차 상태에서 차량 화면의 **여행 생성** → 관리자 휴대폰으로 **소유권 QR** 스캔 → 다른 휴대폰으로 **참여 QR** 스캔 → 사진 업로드. 차량에서 **계정 연결** QR을 띄우고 이미 참여한 휴대폰에서 **연결 확인**을 누른다. 차량 화면에서 표시된 계정으로 좋아요를 입력한다. 관리자 계정으로 연결한 차량의 **최종 선정 → 앨범 확정** 또는 관리자 웹의 **앨범 편집**을 사용한다. 공유 앨범에서 원본을 다운로드한다.

## 서버
Python 3.14 기준. 저장소 루트에서 아래를 실행한다.
```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-test.txt
python -m unittest discover -s tests -v
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
기본 데이터는 backend/.local에 생성한다. 경로 변경은 시작 전 TRIPPICK_DATA_DIR 환경 변수로 지정한다. .env.example은 셸 설정 예시다. 환경 파일을 자동으로 읽지 않는다. GET /api/v1/health로 연결하고 /docs에서 실제 제공 API를 확인한다.

## 모바일 웹
별도 터미널에서 Node 24와 npm을 사용한다.
```sh
cd apps/mobile-web
npm ci
npm test
npm run build
npm run dev -- --host 127.0.0.1
```
브라우저에서 http://127.0.0.1:5173 을 연다. 서버 주소를 변경하려면 API_PROXY_TARGET을 설정한다. 배포용 dist를 제공하는 서버도 /api를 백엔드로 전달해야 한다.

## 차량
JDK 17, Android API 34와 Build-Tools 34.0.0을 준비하고 ANDROID_HOME을 설정한다.
```sh
cd apps/vehicle
./gradlew assembleDebug testDebugUnitTest
./gradlew -PwithPleosSdk=true -PwebOrigin=https://YOUR-TEST-HOST assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```
SDK 포함 설정은 공식 Maven의 Vehicle 라이브러리를 패키징한다. 실차·원격 서버는 -PapiOrigin=https://YOUR-TEST-HOST를 추가한다. APK는 app/build/outputs/apk/debug/app-debug.apk에 생성된다. 자동차 기능을 요구하며 주행 제한을 알 수 없거나 조작이 제한되면 갤러리와 QR을 숨긴다. Pleos 설치·주행 제한 검증 절차는 docs/sdk-validation.md에 있다.

## 계약 및 변경 이력
docs/requirements.md, architecture.md, database.md, api.md는 목표 상태와 현재 구현을 구분한다. 테스트 범위는 docs/test-plan.md, 실행 결과는 docs/development-log.md, 결정 근거는 docs/decisions에서 확인한다.

## 회귀 검증
일반 단위 테스트 외에 tests/integration/pleos_album.py가 실제 공식 AVD의 UI Automator, QR 화면 캡처, 별도 Chrome 컨텍스트 4개를 사용한다. 별도 테스트 DB, SDK 포함 설치 앱, adb, Chrome과 tests/integration/requirements.txt가 필요하다. 테스트는 새 여행만 만들며 기존 데이터는 지우지 않는다. 서버/도메인 설정과 실측 결과는 docs/phase2-validation.md를 참조한다.
