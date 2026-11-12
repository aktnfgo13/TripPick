from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from .access import actor, changed, connection, fail, uid

router=APIRouter(prefix="/api/v1/trips/{trip}/album")
class Selection(BaseModel):
    orderedPhotoIds:list[str]=Field(min_length=1,max_length=1000)
    coverPhotoId:str
    expectedRevision:int=Field(ge=0)


@router.get("")
def album(trip:str,req:Request,db=Depends(connection)):
    actor(req,db,trip)
    record=db.execute("SELECT * FROM albums WHERE trip_id=?",(trip,)).fetchone()
    items=[r[0] for r in db.execute("SELECT photo_id FROM album_items WHERE trip_id=? ORDER BY position",(trip,))]
    return dict(albumId=record["id"] if record else None,revision=record["revision"] if record else 0,
                orderedPhotoIds=items,coverPhotoId=items[0] if items else None)


@router.put("")
def publish(trip:str,body:Selection,req:Request,db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    if actor(req,db,trip)["role"]!="owner": fail(403,"관리자 전용")
    existing=db.execute("SELECT id,revision FROM albums WHERE trip_id=?",(trip,)).fetchone()
    if (existing["revision"] if existing else 0)!=body.expectedRevision: fail(409,"앨범이 변경되었습니다. 다시 조회하세요.")
    ids=body.orderedPhotoIds
    if len(set(ids))!=len(ids) or body.coverPhotoId not in ids: fail(422,"선정 목록 또는 표지 오류")
    allowed={r[0] for r in db.execute("SELECT id FROM photos WHERE trip_id=?",(trip,))}
    if not set(ids)<=allowed: fail(422,"여행에 없는 사진")
    ids=[body.coverPhotoId]+[p for p in ids if p!=body.coverPhotoId]
    aid=existing["id"] if existing else uid()
    db.execute("INSERT INTO albums VALUES(?,?,1) ON CONFLICT(trip_id) DO UPDATE SET revision=revision+1",(aid,trip))
    db.execute("DELETE FROM album_items WHERE album_id=?",(aid,))
    db.executemany("INSERT INTO album_items VALUES(?,?,?,?)",[(trip,aid,p,i) for i,p in enumerate(ids)])
    db.execute("UPDATE trips SET state='PUBLISHED' WHERE id=?",(trip,))
    changed(db,trip)
    return {"albumId":aid,"revision":body.expectedRevision+1}
