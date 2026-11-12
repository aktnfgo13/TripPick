from uuid import uuid4


class AlbumConflict(Exception):
    pass


def save_album(db, trip, ids, cover, revision):
    existing = db.execute(
        "SELECT id,revision FROM albums WHERE trip_id=?", (trip,)
    ).fetchone()
    if (existing["revision"] if existing else 0) != revision:
        raise AlbumConflict("앨범이 변경되었습니다. 다시 조회하세요.")
    if len(set(ids)) != len(ids) or cover not in ids:
        raise ValueError("선정 목록 또는 표지 오류")
    allowed = {
        r[0] for r in db.execute("SELECT id FROM photos WHERE trip_id=?", (trip,))
    }
    if not set(ids) <= allowed:
        raise ValueError("여행에 없는 사진")
    ids = [cover] + [p for p in ids if p != cover]
    aid = existing["id"] if existing else str(uuid4())
    db.execute(
        "INSERT INTO albums VALUES(?,?,1) ON CONFLICT(trip_id) DO UPDATE SET revision=revision+1",
        (aid, trip),
    )
    db.execute("DELETE FROM album_items WHERE album_id=?", (aid,))
    db.executemany(
        "INSERT INTO album_items VALUES(?,?,?,?)",
        [(trip, aid, p, i) for i, p in enumerate(ids)],
    )
    db.execute("UPDATE trips SET state='PUBLISHED' WHERE id=?", (trip,))
    db.execute("UPDATE trips SET revision=revision+1 WHERE id=?", (trip,))
    return {"albumId": aid, "revision": revision + 1}
