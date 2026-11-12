# TripPick
차량과 휴대폰에서 함께 만드는 여행 앨범의 Phase 1 개발 기준점이다. 현재 실행 경로는 모바일 웹 → FastAPI 준비 상태 조회, SQLite 및 비공개 로컬 객체 저장소, 독립적인 차량 시작 화면이다.

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
./gradlew -PwithPleosSdk=true assembleDebug
```
두 번째 명령은 공식 Maven의 Vehicle SDK를 포함하는 선택 검증이다. APK는 app/build/outputs/apk/debug/app-debug.apk에 생성된다. 자동차 기능을 요구하며 시작 화면은 정적 연결 상태만 표시한다. Pleos 설치·주행 제한 검증 절차는 docs/sdk-validation.md에 있다.

## 계약 및 변경 이력
docs/requirements.md, architecture.md, database.md, api.md는 목표 상태와 현재 구현을 구분한다. 테스트 범위는 docs/test-plan.md, 실행 결과는 docs/development-log.md, 결정 근거는 docs/decisions에서 확인한다.
