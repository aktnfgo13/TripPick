from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, UploadFile

from ..repositories.gallery import photos_page
from ..services.images import MAX_BYTES
from ..services.upload import QuotaExceeded, UploadConflict, save_photo
from .access import actor, changed, connection, fail

router = APIRouter(prefix="/api/v1/trips/{trip}/photos")


@router.post("", status_code=201)
def upload(
    trip: str,
    req: Request,
    file: UploadFile,
    idempotency_key: UUID = Header(),
    db=Depends(connection),
):
    who = actor(req, db, trip)
    if not who["member"] or who["vehicle"]:
        fail(403, "휴대폰 참여 세션 필요")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        fail(413, "최대 12 MiB")
    try:
        return save_photo(
            db,
            req.app.state.objects,
            trip,
            who["member"],
            data,
            file.content_type,
            idempotency_key,
        )
    except ValueError as error:
        fail(422, str(error))
    except UploadConflict as error:
        fail(409, str(error))
    except QuotaExceeded as error:
        fail(413, str(error))


@router.get("")
def photos(
    trip: str,
    req: Request,
    cursor: str = "",
    limit: int = Query(40, ge=1, le=100),
    db=Depends(connection),
):
    who = actor(req, db, trip)
    return photos_page(db, trip, who["member"], cursor, limit)


@router.get("/{photo}/{kind}")
def media(trip: str, photo: str, kind: str, req: Request, db=Depends(connection)):
    who = actor(req, db, trip)
    row = db.execute(
        "SELECT * FROM photos WHERE trip_id=? AND id=?", (trip, photo)
    ).fetchone()
    if not row or kind not in ("preview", "download"):
        fail(404, "사진 없음")
    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if kind == "download":
        included = db.execute(
            "SELECT 1 FROM album_items WHERE trip_id=? AND photo_id=?", (trip, photo)
        ).fetchone()
        if who["vehicle"] or not (
            included
            or who["role"] == "owner"
            or who["member"] == row["uploader_member_id"]
        ):
            fail(403, "원본 다운로드 권한 없음")
        ext = "jpg" if row["mime"] == "image/jpeg" else "png"
        headers["Content-Disposition"] = f'attachment; filename="{photo}.{ext}"'
    key = row["preview_key" if kind == "preview" else "object_key"]
    return Response(
        req.app.state.objects.read(UUID(key)),
        media_type="image/jpeg" if kind == "preview" else row["mime"],
        headers=headers,
    )


@router.api_route("/{photo}/vote", methods=["PUT", "DELETE"])
def vote(trip: str, photo: str, req: Request, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    who = actor(req, db, trip)
    if not who["member"]:
        fail(403, "참여자의 휴대폰에서 차량을 연결하세요.")
    if who["vehicle"] and req.headers.get("X-Expected-Member") != who["member"]:
        fail(409, "차량에 연결된 계정이 변경되었습니다. 다시 조회하세요.")
    if not db.execute(
        "SELECT 1 FROM photos WHERE trip_id=? AND id=?", (trip, photo)
    ).fetchone():
        fail(404, "사진 없음")
    if req.method == "PUT":
        modified = db.execute(
            "INSERT OR IGNORE INTO photo_votes VALUES(?,?,?)",
            (trip, photo, who["member"]),
        )
    else:
        modified = db.execute(
            "DELETE FROM photo_votes WHERE photo_id=? AND member_id=?",
            (photo, who["member"]),
        )
    if modified.rowcount:
        changed(db, trip)
    return dict(
        myVote=req.method == "PUT",
        voteCount=db.execute(
            "SELECT count(*) FROM photo_votes WHERE photo_id=?", (photo,)
        ).fetchone()[0],
    )
