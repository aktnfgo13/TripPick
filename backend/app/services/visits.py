from datetime import timezone
from uuid import uuid4

from .regions import region_for


def record_visit(db, trip, body):
    timestamp = body.observedAt.astimezone(timezone.utc).isoformat()
    key = body.source + ":" + body.key
    existing = db.execute(
        "SELECT id,status FROM visits WHERE trip_id=? AND event_key=?", (trip, key)
    ).fetchone()
    if existing:
        if body.kind == "ARRIVED" and existing["status"] == "CANDIDATE":
            db.execute(
                "UPDATE visits SET status='ARRIVED',arrival_at=?,confidence=.9 WHERE id=?",
                (timestamp, existing["id"]),
            )
            db.execute("UPDATE trips SET revision=revision+1 WHERE id=?", (trip,))
        return {"id": existing["id"]}
    fingerprint = f"{body.name}:{body.latitude}:{body.longitude}"
    pid = str(uuid4())
    db.execute(
        """INSERT OR IGNORE INTO places(id,trip_id,id_key,name,latitude,longitude,region_code,district_code)
      VALUES(?,?,?,?,?,?,?,?)""",
        (
            pid,
            trip,
            fingerprint,
            body.name,
            body.latitude,
            body.longitude,
            region_for(body.latitude, body.longitude),
            body.districtCode,
        ),
    )
    pid = db.execute(
        "SELECT id FROM places WHERE trip_id=? AND id_key=?", (trip, fingerprint)
    ).fetchone()[0]
    vid = str(uuid4())
    db.execute(
        """INSERT INTO visits(id,trip_id,place_id,event_key,observed_at,arrival_at,source,confidence,status)
      VALUES(?,?,?,?,?,?,?,?,?)""",
        (
            vid,
            trip,
            pid,
            key,
            timestamp,
            timestamp if body.kind == "ARRIVED" else None,
            body.source,
            {"ARRIVED": 0.9, "CONFIRMED": 1, "CANDIDATE": 0.35}[body.kind],
            body.kind,
        ),
    )
    db.execute("UPDATE trips SET revision=revision+1 WHERE id=?", (trip,))
    return {"id": vid}
