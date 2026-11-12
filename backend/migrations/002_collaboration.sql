BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS trips (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'DRAFT'
 CHECK(state IN ('DRAFT','ACTIVE','REVIEW','PUBLISHED')), revision INTEGER NOT NULL DEFAULT 0,
 invite_hash TEXT UNIQUE NOT NULL, claim_hash TEXT UNIQUE, invite_until INTEGER NOT NULL,
 owner_user_id TEXT REFERENCES users(id), created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, nickname TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS trip_members(
 id TEXT PRIMARY KEY, trip_id TEXT NOT NULL REFERENCES trips, user_id TEXT NOT NULL REFERENCES users,
 role TEXT NOT NULL CHECK(role IN ('owner','member')), session_hash TEXT UNIQUE NOT NULL, expires INTEGER NOT NULL,
 UNIQUE(trip_id,user_id), UNIQUE(trip_id,id)
);
CREATE TABLE IF NOT EXISTS vehicle_sessions(
 id TEXT PRIMARY KEY, trip_id TEXT NOT NULL REFERENCES trips, token_hash TEXT UNIQUE NOT NULL,
 actor_member_id TEXT, expires INTEGER NOT NULL, pair_hash TEXT UNIQUE, pair_until INTEGER,
 FOREIGN KEY(trip_id,actor_member_id) REFERENCES trip_members(trip_id,id)
);
CREATE TABLE IF NOT EXISTS photos(
 id TEXT PRIMARY KEY, trip_id TEXT NOT NULL REFERENCES trips, uploader_member_id TEXT NOT NULL,
 object_key TEXT NOT NULL UNIQUE, preview_key TEXT NOT NULL UNIQUE, mime TEXT NOT NULL,
 size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, request_key TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(trip_id,id),
 UNIQUE(trip_id,uploader_member_id,request_key), FOREIGN KEY(trip_id,uploader_member_id) REFERENCES trip_members(trip_id,id)
);
CREATE INDEX IF NOT EXISTS photos_trip ON photos(trip_id,id);
CREATE TABLE IF NOT EXISTS photo_votes(
 trip_id TEXT NOT NULL, photo_id TEXT NOT NULL, member_id TEXT NOT NULL, PRIMARY KEY(photo_id,member_id),
 FOREIGN KEY(trip_id,photo_id) REFERENCES photos(trip_id,id), FOREIGN KEY(trip_id,member_id) REFERENCES trip_members(trip_id,id)
);
CREATE TABLE IF NOT EXISTS albums(id TEXT PRIMARY KEY,trip_id TEXT UNIQUE NOT NULL REFERENCES trips,
 revision INTEGER NOT NULL, UNIQUE(trip_id,id));
CREATE TABLE IF NOT EXISTS album_items(trip_id TEXT NOT NULL, album_id TEXT NOT NULL, photo_id TEXT NOT NULL,
 position INTEGER NOT NULL, PRIMARY KEY(album_id,photo_id), UNIQUE(album_id,position),
 FOREIGN KEY(trip_id,album_id) REFERENCES albums(trip_id,id), FOREIGN KEY(trip_id,photo_id) REFERENCES photos(trip_id,id));
INSERT OR IGNORE INTO schema_migrations(version) VALUES(2);
COMMIT;
