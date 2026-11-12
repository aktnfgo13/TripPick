# 관계형 계약 (Phase 2 이후 마이그레이션 명세)
각 행의 id는 UUID, created_at은 UTC. PostgreSQL은 uuid/timestamptz, SQLite는 정규화한 UUID·RFC3339 UTC TEXT. 아래 참조는 FK이며 !는 유일 키다. 여행 소속 자식은 (trip_id,id) 유일 키와 복합 FK로 다른 여행 간 연결을 막는다.

|테이블|필수 데이터와 무결성|
|---|---|
|users|id, nickname, auth_subject! (익명은 NULL)|
|trips|id, owner_user_id→users (미인증 초안만 NULL), title, start_date, end_date≥start_date, state, revision|
|trip_members|id, trip_id→trips, user_id→users, role(owner/member/viewer), (trip_id,user_id)!|
|vehicle_sessions|id, trip_id, actor_member_id→trip_members nullable, token_hash!, expires_at, revoked_at|
|places|id, region_code, name, lat, lon, provider, external_id, (provider,external_id)!|
|visits|id, trip_id, place_id→places nullable, occurred_at, source, confidence [0,1], review_state, source_event_key, (trip_id,source_event_key)!|
|photos|id, trip_id, uploader_member_id, object_key!, preview_key, mime, size_bytes, sha256, taken_at, private_lat/lon, request_key, (trip_id,uploader_member_id,request_key)!|
|photo_place_links|id, trip_id, photo_id→photos, place_id→places, visit_id→visits nullable, source, confidence, review_state, (photo_id,place_id)!|
|photo_analysis|id, photo_id→photos, analyzer_version, status, sharpness, phash, similarity_group, (photo_id,analyzer_version)!|
|photo_votes|id, trip_id, photo_id, member_id, (photo_id,member_id)!|
|albums|id, trip_id!, owner_user_id, cover_item_id nullable, revision, published_at|
|album_items|id, trip_id, album_id, photo_id, position, (album_id,photo_id)!, (album_id,position)!|
|share_links|id, album_id, token_hash!, scope, expires_at, revoked_at|
|processing_jobs|id, photo_id, kind, version, state, attempts, lease_until, retry_at, (photo_id,kind,version)!|

표지는 같은 앨범 항목만 참조한다. 방문은 사진 없이 생성 가능하다. 투표 행과 앨범 항목은 독립적으로 수정한다. 장소 연결 변경은 원본 키를 바꾸지 않는다. 인덱스는 visits(trip_id,occurred_at), photos(trip_id,taken_at,id), places(region_code), processing_jobs(state,retry_at)에 둔다. 투표 유일 인덱스는 사진별 집계에도 사용한다.
Phase 1은 버전 1 기초 마이그레이션만 적용한다. 다음 버전부터 도메인 테이블을 도입한다. 기존 버전 SQL을 고치지 않고 순차 적용하며 백업 복제본에서 업그레이드·복원을 시험한다.

## Phase 2 적용 상태
002_collaboration.sql은 users, trips, trip_members, vehicle_sessions, photos, photo_votes, albums, album_items를 추가한다. 이전 001과 로컬 객체 UUID는 그대로 사용한다. 실제 열 이름과 CHECK/UNIQUE/FK는 버전 SQL이 기준이다. 식별자는 서버 발급 UUID, 만료는 UTC epoch 초, 생성 시각은 SQLite UTC다. 차량·멤버·초대 토큰은 해시로 조회한다. trip_members의 role과 trips.owner_user_id는 claim 트랜잭션에서 함께 변경한다. 사진과 멤버·앨범 항목은 같은 여행의 복합 FK로 묶인다. 앨범 첫 항목이 표지이며 원본은 독립 객체다. 사진 촬영 GPS, 방문·분석·작업 큐·공개 공유 링크는 장기 계약에 남겨둔다.
