import hmac
import time
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from .access import actor, changed, connection, digest, fail, ticket

router = APIRouter(prefix="/api/v1/trips/{trip}/recovery")

class Proof(BaseModel):
    code: str = Field(min_length=1,max_length=128)

def enabled(req):
    if not req.app.state.recovery_enabled:
        fail(404, "이 환경에서는 복구 기능을 사용할 수 없습니다.")

@router.post("/issue")
def issue(trip:str,req:Request,response:Response,db=Depends(connection)):
    enabled(req)
    db.execute("BEGIN IMMEDIATE")
    who=actor(req,db,trip)
    if who["vehicle"] or who["role"]!="owner":
        fail(403,"관리자 휴대폰에서 발급하세요.")
    code=ticket()
    db.execute("INSERT OR REPLACE INTO owner_recovery(trip_id,code_hash) VALUES(?,?)",(trip,digest(code)))
    response.headers["Cache-Control"]="no-store"
    return {"code":code,"tripId":trip}

@router.post("")
def recover(trip:str,body:Proof,req:Request,response:Response,db=Depends(connection)):
    enabled(req)
    db.execute("BEGIN IMMEDIATE")
    row=db.execute("SELECT * FROM owner_recovery WHERE trip_id=?",(trip,)).fetchone()
    now=int(time.time())
    if not row: fail(403,"복구 정보를 확인하세요.")
    active=now-row["window_start"]<900
    if active and row["failures"]>=5: fail(429,"15분 후 다시 시도하세요.")
    if not hmac.compare_digest(digest(body.code.strip()),row["code_hash"]):
        db.execute("UPDATE owner_recovery SET failures=?,window_start=? WHERE trip_id=?",
                   (row["failures"]+1 if active else 1,row["window_start"] if active else now,trip))
        db.commit()
        fail(403,"복구 정보를 확인하세요.")
    token=ticket()
    db.execute("UPDATE trip_members SET session_hash=?,expires=? WHERE trip_id=? AND role='owner'",(digest(token),now+30*86400,trip))
    db.execute("DELETE FROM owner_recovery WHERE trip_id=?",(trip,))
    db.execute("UPDATE vehicle_sessions SET actor_member_id=NULL,pair_hash=NULL WHERE trip_id=?",(trip,))
    changed(db,trip)
    response.set_cookie("tp_"+trip,token,httponly=True,secure=req.app.state.secure_cookie,samesite="strict",max_age=30*86400,path="/api/v1")
    return {"tripId":trip}
