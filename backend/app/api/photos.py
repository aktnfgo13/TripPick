from hashlib import sha256
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Request, Response, UploadFile, Query
from .access import actor, changed, connection, fail, uid
from ..services.images import MAX_BYTES, thumbnail

router=APIRouter(prefix="/api/v1/trips/{trip}/photos")


@router.post("",status_code=201)
def upload(trip:str, req:Request, file:UploadFile, idempotency_key:UUID=Header(), db=Depends(connection)):
    who=actor(req,db,trip)
    if not who["member"] or who["vehicle"]: fail(403,"휴대폰 참여 세션 필요")
    data=file.file.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES: fail(413,"최대 12 MiB")
    checksum=sha256(data).hexdigest()
    try:
        preview=thumbnail(data,file.content_type)
    except ValueError as error:
        fail(422,str(error))
    db.execute("BEGIN IMMEDIATE")
    existing=db.execute("SELECT id,sha256 FROM photos WHERE trip_id=? AND uploader_member_id=? AND request_key=?",
                        (trip,who["member"],str(idempotency_key))).fetchone()
    if existing:
        if existing["sha256"]!=checksum: fail(409,"같은 요청 키로 다른 이미지 전송")
        return {"photoId":existing["id"]}
    if db.execute("SELECT state FROM trips WHERE id=?",(trip,)).fetchone()[0]!="ACTIVE": fail(409,"진행 중인 여행에서 업로드하세요.")
    usage=db.execute("SELECT coalesce(sum(size_bytes),0) FROM photos WHERE trip_id=?",(trip,)).fetchone()[0]
    if usage+len(data)>512*1024*1024: fail(413,"여행 저장 한도 초과")
    store=req.app.state.objects
    keys=[]
    try:
        for blob in (data,preview):
            keys.append(store.put(blob))
        photo=uid()
        db.execute("""INSERT INTO photos(id,trip_id,uploader_member_id,object_key,preview_key,mime,size_bytes,sha256,request_key)
            VALUES(?,?,?,?,?,?,?,?,?)""",(photo,trip,who["member"],*map(str,keys),file.content_type,len(data),checksum,str(idempotency_key)))
        changed(db,trip)
        db.commit()
    except Exception:
        for key in keys: store.discard(key)
        raise
    return {"photoId":photo}


@router.get("")
def photos(trip:str, req:Request,cursor:str="",limit:int=Query(40,ge=1,le=100),db=Depends(connection)):
    who=actor(req,db,trip)
    rows=db.execute("""SELECT p.id,p.uploader_member_id uploaderId,u.nickname uploader,
      (SELECT count(*) FROM photo_votes WHERE photo_id=p.id) voteCount,
      EXISTS(SELECT 1 FROM photo_votes WHERE photo_id=p.id AND member_id=?) myVote
      FROM photos p JOIN trip_members m ON m.id=p.uploader_member_id JOIN users u ON u.id=m.user_id
      WHERE p.trip_id=? AND p.id>? ORDER BY p.id LIMIT ?""",(who["member"],trip,cursor,limit+1)).fetchall()
    return dict(items=[dict(r) for r in rows[:limit]],nextCursor=rows[limit-1]["id"] if len(rows)>limit else None)


@router.get("/{photo}/{kind}")
def media(trip:str,photo:str,kind:str,req:Request,db=Depends(connection)):
    who=actor(req,db,trip)
    row=db.execute("SELECT * FROM photos WHERE trip_id=? AND id=?",(trip,photo)).fetchone()
    if not row or kind not in ("preview","download"): fail(404,"사진 없음")
    headers={"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}
    if kind=="download":
        included=db.execute("SELECT 1 FROM album_items WHERE trip_id=? AND photo_id=?",(trip,photo)).fetchone()
        if who["vehicle"] or not (included or who["role"]=="owner" or who["member"]==row["uploader_member_id"]):
            fail(403,"원본 다운로드 권한 없음")
        ext="jpg" if row["mime"]=="image/jpeg" else "png"
        headers["Content-Disposition"]=f'attachment; filename="{photo}.{ext}"'
    key=row["preview_key" if kind=="preview" else "object_key"]
    return Response(req.app.state.objects.read(UUID(key)),media_type="image/jpeg" if kind=="preview" else row["mime"],headers=headers)


@router.api_route("/{photo}/vote",methods=["PUT","DELETE"])
def vote(trip:str,photo:str,req:Request,db=Depends(connection)):
    db.execute("BEGIN IMMEDIATE")
    who=actor(req,db,trip)
    if not who["member"]: fail(403,"참여자의 휴대폰에서 차량을 연결하세요.")
    if not db.execute("SELECT 1 FROM photos WHERE trip_id=? AND id=?",(trip,photo)).fetchone(): fail(404,"사진 없음")
    if req.method=="PUT":
        modified=db.execute("INSERT OR IGNORE INTO photo_votes VALUES(?,?,?)",(trip,photo,who["member"]))
    else:
        modified=db.execute("DELETE FROM photo_votes WHERE photo_id=? AND member_id=?",(photo,who["member"]))
    if modified.rowcount: changed(db,trip)
    return dict(myVote=req.method=="PUT",voteCount=db.execute("SELECT count(*) FROM photo_votes WHERE photo_id=?",(photo,)).fetchone()[0])
