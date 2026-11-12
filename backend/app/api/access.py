import hashlib
import secrets
import time
from uuid import uuid4

from fastapi import HTTPException, Request

from ..repositories.database import connect


def uid():
    return str(uuid4())


def ticket():
    return secrets.token_urlsafe(32)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def connection(req: Request):
    db = connect(req.app.state.db_path)
    try:
        with db:
            yield db
    finally:
        db.close()


def fail(code, message):
    raise HTTPException(code, message)


def actor(req, db, trip):
    bearer = req.headers.get("authorization", "").removeprefix("Bearer ")
    if bearer:
        row = db.execute(
            """SELECT v.id vehicle,m.id member,m.role FROM vehicle_sessions v
          LEFT JOIN trip_members m ON m.id=v.actor_member_id WHERE v.trip_id=? AND v.token_hash=? AND v.expires>?""",
            (trip, digest(bearer), time.time()),
        ).fetchone()
    else:
        row = db.execute(
            """SELECT NULL vehicle,id member,role FROM trip_members
          WHERE trip_id=? AND session_hash=? AND expires>?""",
            (trip, digest(req.cookies.get("tp_" + trip, "")), time.time()),
        ).fetchone()
    if not row:
        fail(401, "세션이 없거나 만료되었습니다.")
    return row


def changed(db, trip):
    db.execute("UPDATE trips SET revision=revision+1 WHERE id=?", (trip,))
