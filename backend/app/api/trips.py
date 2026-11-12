import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, StringConstraints

from .access import actor, changed, connection, digest, fail, ticket, uid

router = APIRouter(prefix="/api/v1")
Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]


class NewTrip(BaseModel):
    title: Name


class Join(BaseModel):
    token: str
    nickname: Name


class Code(BaseModel):
    token: str


class Transition(BaseModel):
    state: Literal["ACTIVE", "REVIEW"]


@router.post("/trips", status_code=201)
def create(body: NewTrip, db=Depends(connection)):
    trip, invite, claim, vehicle = uid(), ticket(), ticket(), ticket()
    until = int(time.time()) + 7 * 86400
    db.execute(
        "INSERT INTO trips(id,title,invite_hash,claim_hash,invite_until) VALUES(?,?,?,?,?)",
        (trip, body.title, digest(invite), digest(claim), until),
    )
    db.execute(
        "INSERT INTO vehicle_sessions(id,trip_id,token_hash,expires) VALUES(?,?,?,?)",
        (uid(), trip, digest(vehicle), until),
    )
    return dict(tripId=trip, inviteToken=invite, claimToken=claim, vehicleToken=vehicle)


def invitation(db, token):
    trip = db.execute(
        "SELECT * FROM trips WHERE (invite_hash=? OR claim_hash=?) AND invite_until>?",
        (digest(token), digest(token), time.time()),
    ).fetchone()
    if not trip:
        fail(404, "만료되었거나 유효하지 않은 초대입니다.")
    return trip


@router.post("/invite")
def preview(body: Code, db=Depends(connection)):
    trip = invitation(db, body.token)
    return dict(id=trip["id"], title=trip["title"])


@router.post("/join")
def join(body: Join, req: Request, response: Response, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    trip = invitation(db, body.token)
    tid = trip["id"]
    owner = trip["claim_hash"] == digest(body.token)
    current = db.execute(
        "SELECT * FROM trip_members WHERE trip_id=? AND session_hash=? AND expires>?",
        (tid, digest(req.cookies.get("tp_" + tid, "")), time.time()),
    ).fetchone()
    if current:
        member, user = current["id"], current["user_id"]
    else:
        user, member, session = uid(), uid(), ticket()
        db.execute("INSERT INTO users VALUES(?,?)", (user, body.nickname))
        db.execute(
            "INSERT INTO trip_members VALUES(?,?,?,?,?,?)",
            (
                member,
                tid,
                user,
                "member",
                digest(session),
                int(time.time()) + 30 * 86400,
            ),
        )
        response.set_cookie(
            "tp_" + tid,
            session,
            httponly=True,
            secure=req.app.state.secure_cookie,
            samesite="strict",
            max_age=30 * 86400,
            path="/api/v1",
        )
    if owner:
        db.execute(
            "UPDATE trips SET owner_user_id=?,claim_hash=NULL,state='ACTIVE' WHERE id=?",
            (user, tid),
        )
        db.execute("UPDATE trip_members SET role='owner' WHERE id=?", (member,))
    changed(db, tid)
    return dict(tripId=tid, memberId=member)


@router.get("/trips/{trip}")
def summary(trip: str, req: Request, db=Depends(connection)):
    who = actor(req, db, trip)
    info = dict(
        db.execute(
            "SELECT id,title,state,revision FROM trips WHERE id=?", (trip,)
        ).fetchone()
    )
    members = db.execute(
        "SELECT m.id,u.nickname,m.role FROM trip_members m JOIN users u ON u.id=m.user_id WHERE m.trip_id=?",
        (trip,),
    )
    return dict(
        **info,
        members=[dict(m) for m in members],
        memberId=who["member"],
        role=who["role"],
        photoCount=db.execute(
            "SELECT count(*) FROM photos WHERE trip_id=?", (trip,)
        ).fetchone()[0],
    )


@router.post("/trips/{trip}/pair-code")
def pair_code(trip: str, req: Request, db=Depends(connection)):
    who = actor(req, db, trip)
    if not who["vehicle"]:
        fail(403, "차량 전용")
    token = ticket()
    db.execute(
        "UPDATE vehicle_sessions SET pair_hash=?,pair_until=? WHERE id=?",
        (digest(token), int(time.time()) + 120, who["vehicle"]),
    )
    return dict(token=token)


@router.put("/trips/{trip}/vehicle-session/actor")
def pair(trip: str, body: Code, req: Request, db=Depends(connection)):
    who = actor(req, db, trip)
    if who["vehicle"]:
        fail(403, "휴대폰 확인 필요")
    updated = db.execute(
        "UPDATE vehicle_sessions SET actor_member_id=?,pair_hash=NULL WHERE trip_id=? AND pair_hash=? AND pair_until>? AND expires>?",
        (who["member"], trip, digest(body.token), time.time(), time.time()),
    )
    if not updated.rowcount:
        fail(409, "연결 코드가 만료되었습니다.")
    changed(db, trip)
    return {"memberId": who["member"]}


@router.patch("/trips/{trip}")
def transition(trip: str, body: Transition, req: Request, db=Depends(connection)):
    if actor(req, db, trip)["role"] != "owner":
        fail(403, "관리자 전용")
    previous = {"ACTIVE": "REVIEW", "REVIEW": "ACTIVE"}[body.state]
    if not db.execute(
        "UPDATE trips SET state=?,revision=revision+1 WHERE id=? AND state=?",
        (body.state, trip, previous),
    ).rowcount:
        fail(409, "상태 전환 불가")
    return {"state": body.state}
