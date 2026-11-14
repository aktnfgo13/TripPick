# 외부 공유 전 점검

- 관리하는 도메인의 신뢰 가능한 HTTPS 인증서와 지속 저장소를 준비한다. TRIPPICK_WEB_DIST는 Vue 배포 디렉터리, TRIPPICK_DATA_DIR는 SQLite와 사진의 지속 경로다. assets/maps까지 배포한다.
- 웹, /api/v1, /journal, WebSocket을 같은 공개 출처로 프록시하고 Host와 WebSocket 업그레이드를 전달한다. 업로드 용량과 요청 수 제한을 설정한다. TRIPPICK_DEV_HTTP와 TRIPPICK_ENABLE_MOCK_NAVIGATION은 운영에서 해제한다.
- apps/vehicle에서 실제 HTTPS 주소로 아래 명령을 실행한다. 로컬 프로필에만 isolatedDemo와 에뮬레이터 HTTP 주소를 사용한다.

```sh
./gradlew -PwithPleosSdk=true -PapiOrigin="https://$TRIPPICK_HOST" -PwebOrigin="https://$TRIPPICK_HOST" assembleDebug testDebugUnitTest
```

- 폰의 셀룰러 네트워크에서 QR과 표기 URL 일치, 참여, 업로드, 차량 반영, 좋아요, 원본 다운로드를 확인한다. 테스트 호스트·인증서 예외·브라우저 DNS 매핑 없이 확인한다.
- 공모전의 패키지명·서명 요건을 확인하고, 제출 키가 필요하면 주최 지침에 맞춰 별도 서명한다. apksigner verify --print-certs로 서명을, shasum -a 256으로 배포 및 설치 APK를 대조한다.
- 공유 대상은 소스, 검증 기록, APK와 공개용 캡처다. SQLite, 원본 여행 사진, 세션, QR 인증값, 복구 코드, keystore와 서버 개인 키는 제외한다.

공식 접수는 2026-11-15 23:59 KST까지다. 선정 제출물은 서명한 공식 양식과 함께 발송한다. Private 저장소를 제출하려면 11월 16일까지 공개 전환하고 23일까지 유지하거나 소스·APK 압축 파일 다운로드 주소를 제공한다. 공개 전환은 소유자가 결정한다.
