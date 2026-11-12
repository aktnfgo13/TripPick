from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from ..services.regions import BOUNDARIES
from ..services.visits import record_visit
from .access import actor, changed, connection, fail

router = APIRouter(prefix="/api/v1")


class Event(BaseModel):
    key: str = Field(min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=160)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    source: Literal["NAVIGATION", "LOCATION", "MANUAL", "MOCK"]
    kind: Literal["CANDIDATE", "ARRIVED", "CONFIRMED"]
    observedAt: datetime
    category: str = Field("장소", min_length=1, max_length=40)
    districtCode: str | None = Field(None, pattern=r"^\d{5}$")

    @model_validator(mode="after")
    def valid(self):
        if (self.latitude is None) != (
            self.longitude is None
        ) or self.observedAt.tzinfo is None:
            raise ValueError("좌표 쌍과 시간대가 필요합니다.")
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("장소명이 필요합니다.")
        return self


class Edit(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=160)
    departureAt: datetime | None = None
    status: Literal["CONFIRMED", "EXCLUDED"]


class Link(BaseModel):
    visitId: str | None


@router.get("/regions")
def boundaries():
    return FileResponse(BOUNDARIES, media_type="application/geo+json")


@router.get("/trips/{trip}/journal")
def journal(trip: str, req: Request, db=Depends(connection)):
    actor(req, db, trip)
    entries = [
        dict(r)
        for r in db.execute(
            """SELECT v.*,p.name,p.latitude,p.longitude,p.region_code,p.district_code,p.category
        FROM visits v JOIN places p ON p.id=v.place_id WHERE v.trip_id=? ORDER BY v.observed_at DESC,v.id""",
            (trip,),
        )
    ]
    links = [
        dict(r)
        for r in db.execute(
            "SELECT photo_id,visit_id,status FROM photo_place_links WHERE trip_id=?",
            (trip,),
        )
    ]
    return {"visits": entries, "links": links}


@router.post("/trips/{trip}/visits")
def record(trip: str, body: Event, req: Request, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    who = actor(req, db, trip)
    if body.source == "MOCK" and not req.app.state.mock_navigation:
        fail(403, "모의 기록 비활성화")
    manual = body.source == "MANUAL"
    if manual and who["role"] != "owner" or not manual and not who["vehicle"]:
        fail(403, "기록 권한 없음")
    if not manual and body.kind == "CONFIRMED":
        fail(422, "사용자 확인 필요")
    if (
        not manual
        and db.execute("SELECT state FROM trips WHERE id=?", (trip,)).fetchone()[0]
        != "ACTIVE"
    ):
        fail(409, "진행 중인 여행만 기록합니다.")
    return record_visit(db, trip, body)


@router.patch("/trips/{trip}/visits/{visit}")
def edit(trip: str, visit: str, body: Edit, req: Request, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    if actor(req, db, trip)["role"] != "owner":
        fail(403, "관리자 전용")
    row = db.execute(
        "SELECT place_id,coalesce(arrival_at,observed_at) FROM visits WHERE id=? AND trip_id=?",
        (visit, trip),
    ).fetchone()
    if not row:
        fail(404, "방문 없음")
    if body.departureAt:
        if body.departureAt.tzinfo is None or body.departureAt < datetime.fromisoformat(
            row[1]
        ):
            fail(422, "출발은 방문 이후의 시간이어야 합니다.")
        db.execute(
            "UPDATE visits SET departure_at=? WHERE id=?",
            (body.departureAt.astimezone(timezone.utc).isoformat(), visit),
        )
    if body.name:
        db.execute("UPDATE places SET name=? WHERE id=?", (body.name, row[0]))
    db.execute(
        "UPDATE visits SET status=?,confidence=1 WHERE id=?", (body.status, visit)
    )
    changed(db, trip)
    return {"id": visit}


@router.put("/trips/{trip}/photos/{photo}/place")
def link(trip: str, photo: str, body: Link, req: Request, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    who = actor(req, db, trip)
    row = db.execute(
        "SELECT uploader_member_id FROM photos WHERE trip_id=? AND id=?", (trip, photo)
    ).fetchone()
    if not row:
        fail(404, "사진 없음")
    if who["role"] != "owner" and who["member"] != row[0]:
        fail(403, "편집 권한 없음")
    if (
        body.visitId
        and not db.execute(
            "SELECT 1 FROM visits WHERE id=? AND trip_id=? AND status!='EXCLUDED'",
            (body.visitId, trip),
        ).fetchone()
    ):
        fail(422, "방문 확인 필요")
    db.execute(
        "INSERT OR REPLACE INTO photo_place_links VALUES(?,?,?,?)",
        (trip, photo, body.visitId, "CONFIRMED" if body.visitId else "UNLINKED"),
    )
    changed(db, trip)
    return {"visitId": body.visitId}
