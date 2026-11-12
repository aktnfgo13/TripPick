# Phase 0 설계와 Phase 2 API 계약
구현된 공개 진단 경로 GET /api/v1/health → 200 {"status":"ok"} 또는 503 {"detail":"storage unavailable"}. 경로·비밀값은 응답에 담지 않는다.

다음 표는 최초 설계다. 아래의 Phase 2 실제 계약을 함께 참조한다. 경로 앞에 /api/v1을 붙인다. T는 /trips/{tripId}. UUID 식별자, RFC3339 UTC 시각, 목록은 {items,nextCursor}. 오류는 {detail,code}, 인증 401, 권한 403, 없는 리소스 404, 버전·상태 충돌 409, 형식 422, 크기 413. 인증 주체를 본문에서 받지 않는다.

|동작|입력 → 응답|접근|
|---|---|---|
|POST /trips|title,startDate,endDate, Idempotency-Key → 201 tripId,claimToken|임시 차량 세션|
|POST T/claim|일회용 claimToken → 200 trip,role|인증한 휴대폰 계정|
|POST T/invites, POST /join|만료 시각 → inviteToken / token,nickname → 멤버 세션|관리자 발급, 초대 소지자 가입|
|PATCH T|state,title,expectedRevision → 갱신 trip|관리자|
|PUT T/vehicle-session/actor|차량 페어링과 휴대폰 확인 증명 → actorMemberId,expiresAt|해당 멤버|
|POST T/photos|multipart 파일 하나, Idempotency-Key → 201 photoId,status|참여자, 다중 선택은 파일별 전송|
|GET T/photos|cursor → id,previewUrl,analysisStatus,voteCount,myVote 목록|멤버|
|PUT 또는 DELETE T/photos/{id}/vote|빈 본문 → 200 voteCount,myVote|본인 또는 본인에게 연결된 차량|
|PUT T/album|orderedPhotoIds,coverPhotoId,expectedRevision,publish → albumId,revision|관리자|
|GET T/album, GET T/album/download|앨범과 순서 / ZIP 스트림|허가된 열람자|
|GET T/photos/{id}/download|짧게 만료되는 URL|원본 다운로드 권한 확인|
|POST T/album/shares, DELETE T/album/shares/{id}|scope,ttl → URL / 204|관리자|
|GET /shared/{token}|공개용 앨범·EXIF 제거 미리보기|유효 링크 소지자|
|PATCH T/visits/{id}|placeId,revision → 확인된 방문|관리자|

업로드는 magic bytes·실제 디코딩·픽셀 수·크기·여행 할당량을 검사한다. 같은 요청 키와 동일 내용의 재시도는 기존 결과, 다른 내용은 409. 저장 중단 시 임시 객체만 정리한다. 투표 PUT/DELETE 반복은 멱등이다. 앨범 확정과 여행 상태 전이는 한 트랜잭션이다. WebSocket /api/v1/trips/{id}/events는 멤버 인증 후 {type,resourceId,revision}을 통지한다. 재접속·순번 누락 시 REST로 원본을 다시 읽는다. 차량 만료·연결 해제 시 재인증한다.

## Phase 2 실제 API
공통 접두사는 /api/v1이다. T는 /trips/{trip}이다. JSON 오류 본문은 FastAPI의 detail이며 입력 검증 오류는 배열일 수 있다. 서버 실행 후 /docs 또는 /openapi.json이 HTTP 입력 스키마를 제공한다. 회원 쿠키는 여행별 tp_{trip}, 차량은 Authorization: Bearer 헤더를 사용한다.

|경로|성공 응답과 접근|
|---|---|
|POST /trips {title}|201 {tripId,inviteToken,claimToken,vehicleToken}. 로컬 MVP의 최초 생성 경로|
|POST /invite {token}|200 {id,title}. QR 유효성·제목만 제공|
|POST /join {token,nickname}|200 {tripId,memberId} 및 회원 쿠키. claim은 한 번만 소진|
|GET T|id,title,state,revision,members,photoCount,memberId,role. 차량·멤버|
|PATCH T {state}|관리자가 ACTIVE ↔ REVIEW 전환|
|POST T/pair-code → PUT T/vehicle-session/actor {token}|차량이 단기 코드 발급, 휴대폰 회원이 확인|
|POST T/photos|회원 multipart file + UUID Idempotency-Key. 201 {photoId}, 동일 키·다른 내용 409, 용량 413, 부적절한 이미지 422|
|GET T/photos?cursor=&limit=40|{items,nextCursor}. 최대 100개. id,uploaderId,uploader,voteCount,myVote(0/1)|
|GET T/photos/{id}/preview|차량 또는 멤버에게 EXIF 없는 640px 이하 JPEG|
|PUT/DELETE T/photos/{id}/vote|멤버 또는 연결 차량. 차량은 X-Expected-Member 필수. {voteCount,myVote}|
|GET/PUT T/album|GET {albumId,orderedPhotoIds,coverPhotoId,revision}. PUT은 관리자만 orderedPhotoIds,coverPhotoId,expectedRevision 제출. 성공 {albumId,revision} 및 PUBLISHED. 오래된 revision은 409|
|GET T/photos/{id}/download|원본 파일. 업로더·관리자 또는 해당 여행 확정 앨범의 멤버. 차량은 원본 접근 차단|
|WebSocket T/events|동일 출처의 멤버 쿠키 인증. 커밋 revision 통지. 단절 시 REST 재조회|

별도 계정 인증 시스템을 도입하기 전까지 claim과 join은 같은 라우트에서 다른 종류의 토큰을 소비한다. QR 발급·서버 조회 실패를 사용자에게 표시한다. 초대 회전·외부 공개 링크·전체 ZIP, 날짜 편집 및 여행 생성 요청 자체의 멱등 키는 최초 계약의 후속 항목이다.
