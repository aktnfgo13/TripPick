# 시연 후보 검증

공식 Pleos 기본 화면에서 여행 생성, 3종 QR의 표시 URL과 실제 QR 해독값 비교, 독립 Chrome 세션 네 개의 업로드, 양방향 투표와 취소, 앱 재시작과 상세 복원, 관리자 앨범 확정 및 원본 4개 바이트 일치를 검증했다. 전국 → 충남 → 장소 → 연결 사진도 확인했다. 별도 시도에서 수동 참여 코드 조회, 무효 코드 안내, Drive 조작 제한 및 Park 복귀를 확인했다.

[생성](submission/create.png) · [초대 QR (자격정보 가림)](submission/qr-redacted.png) · [휴대폰 참여](submission/mobile-join.png) · [휴대폰 사진](submission/mobile-gallery.png) · [차량 사진](submission/gallery.png) · [앨범](submission/album.png) · [전국](submission/national.png) · [지역](submission/region.png)

검증 환경은 별도 앱 ID의 SDK debug, 로컬 HTTPS, 데스크톱 Chrome 모바일 뷰포트다. 백엔드 11건, 웹 2건과 빌드, Android JUnit 5건 통과. 시연 APK와 AVD에서 추출한 APK의 SHA-256은 cee4e8b24614ac90a1022dd52fd073516d8938aaf90ee39a05f40b61b475ac22다.
