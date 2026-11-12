BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS places(
 id TEXT PRIMARY KEY,trip_id TEXT NOT NULL REFERENCES trips,id_key TEXT NOT NULL,
 name TEXT NOT NULL,latitude REAL,longitude REAL,region_code TEXT,district_code TEXT,
 category TEXT NOT NULL DEFAULT '장소', UNIQUE(trip_id,id_key),UNIQUE(trip_id,id)
);
CREATE TABLE IF NOT EXISTS visits(
 id TEXT PRIMARY KEY,trip_id TEXT NOT NULL REFERENCES trips,place_id TEXT NOT NULL,
 event_key TEXT NOT NULL,observed_at TEXT NOT NULL,arrival_at TEXT,departure_at TEXT,
 source TEXT NOT NULL,confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
 status TEXT NOT NULL CHECK(status IN ('CANDIDATE','ARRIVED','CONFIRMED','EXCLUDED')),
 UNIQUE(trip_id,event_key),UNIQUE(trip_id,id),
 FOREIGN KEY(trip_id,place_id) REFERENCES places(trip_id,id)
);
CREATE INDEX IF NOT EXISTS visits_time ON visits(trip_id,observed_at);
CREATE TABLE IF NOT EXISTS photo_place_links(
 trip_id TEXT NOT NULL,photo_id TEXT PRIMARY KEY,visit_id TEXT,status TEXT NOT NULL,
 FOREIGN KEY(trip_id,visit_id) REFERENCES visits(trip_id,id),
 FOREIGN KEY(trip_id,photo_id) REFERENCES photos(trip_id,id)
);
CREATE TABLE IF NOT EXISTS photo_metadata(photo_id TEXT PRIMARY KEY REFERENCES photos(id), taken_at TEXT,latitude REAL,longitude REAL);
INSERT OR IGNORE INTO schema_migrations(version) VALUES(4);
COMMIT;
