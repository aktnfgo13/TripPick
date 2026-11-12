"""Read models shared by the album and photo HTTP endpoints."""


def photos_page(db, trip, member, cursor, limit):
    rows = db.execute(
        """SELECT p.id,p.uploader_member_id uploaderId,u.nickname uploader,
      (SELECT count(*) FROM photo_votes WHERE photo_id=p.id) voteCount,
      EXISTS(SELECT 1 FROM photo_votes WHERE photo_id=p.id AND member_id=?) myVote
      FROM photos p JOIN trip_members m ON m.id=p.uploader_member_id JOIN users u ON u.id=m.user_id
      WHERE p.trip_id=? AND p.id>? ORDER BY p.id LIMIT ?""",
        (member, trip, cursor, limit + 1),
    ).fetchall()
    return dict(
        items=[dict(r) for r in rows[:limit]],
        nextCursor=rows[limit - 1]["id"] if len(rows) > limit else None,
    )


def album_snapshot(db, trip):
    record = db.execute(
        "SELECT id, revision FROM albums WHERE trip_id=?", (trip,)
    ).fetchone()
    items = [
        r[0]
        for r in db.execute(
            "SELECT photo_id FROM album_items WHERE trip_id=? ORDER BY position",
            (trip,),
        )
    ]
    return dict(
        albumId=record["id"] if record else None,
        revision=record["revision"] if record else 0,
        orderedPhotoIds=items,
        coverPhotoId=items[0] if items else None,
    )
