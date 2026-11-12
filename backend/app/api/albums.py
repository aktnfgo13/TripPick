from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..repositories.gallery import album_snapshot
from ..services.album_selection import AlbumConflict, save_album
from .access import actor, connection, fail

router = APIRouter(prefix="/api/v1/trips/{trip}/album")


class Selection(BaseModel):
    orderedPhotoIds: list[str] = Field(min_length=1, max_length=1000)
    coverPhotoId: str
    expectedRevision: int = Field(ge=0)


@router.get("")
def album(trip: str, req: Request, db=Depends(connection)):
    actor(req, db, trip)
    return album_snapshot(db, trip)


@router.put("")
def publish(trip: str, body: Selection, req: Request, db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    if actor(req, db, trip)["role"] != "owner":
        fail(403, "관리자 전용")
    try:
        return save_album(
            db, trip, body.orderedPhotoIds, body.coverPhotoId, body.expectedRevision
        )
    except AlbumConflict as error:
        fail(409, str(error))
    except ValueError as error:
        fail(422, str(error))
