from hashlib import sha256
from uuid import uuid4

from ..integrations.objects import ObjectStore
from .images import thumbnail
from .matching import classify_upload
import logging


class UploadConflict(Exception):
    pass


class QuotaExceeded(Exception):
    pass


def save_photo(db, store: ObjectStore, trip, member, data, mime, idempotency_key):
    checksum = sha256(data).hexdigest()
    preview = thumbnail(data, mime)
    db.execute("BEGIN IMMEDIATE")
    existing = db.execute(
        "SELECT id,sha256 FROM photos WHERE trip_id=? AND uploader_member_id=? AND request_key=?",
        (trip, member, str(idempotency_key)),
    ).fetchone()
    if existing:
        if existing["sha256"] != checksum:
            raise UploadConflict("같은 요청 키로 다른 이미지 전송")
        return {"photoId": existing["id"]}
    if (
        db.execute("SELECT state FROM trips WHERE id=?", (trip,)).fetchone()[0]
        != "ACTIVE"
    ):
        raise UploadConflict("진행 중인 여행에서 업로드하세요.")
    usage = db.execute(
        "SELECT coalesce(sum(size_bytes),0) FROM photos WHERE trip_id=?", (trip,)
    ).fetchone()[0]
    if usage + len(data) > 512 * 1024 * 1024:
        raise QuotaExceeded("여행 저장 한도 초과")
    keys = []
    try:
        for blob in (data, preview):
            keys.append(store.put(blob))
        photo = str(uuid4())
        db.execute(
            """INSERT INTO photos(id,trip_id,uploader_member_id,object_key,preview_key,mime,size_bytes,sha256,request_key)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                photo,
                trip,
                member,
                *map(str, keys),
                mime,
                len(data),
                checksum,
                str(idempotency_key),
            ),
        )
        db.execute("SAVEPOINT photo_classification")
        try:
            classify_upload(db,trip,photo,data)
        except Exception:
            db.execute("ROLLBACK TO photo_classification")
            logging.getLogger(__name__).warning("Optional photo classification unavailable")
        finally:
            db.execute("RELEASE photo_classification")
        db.execute("UPDATE trips SET revision=revision+1 WHERE id=?", (trip,))
        db.commit()
    except Exception:
        for key in keys:
            store.discard(key)
        raise
    return {"photoId": photo}
