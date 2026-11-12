from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest import TestCase
from uuid import uuid4

from app.main import create_app
from app.repositories.database import connect
from fastapi.testclient import TestClient


class GalleryPages(TestCase):
    def test_500_metadata_rows(self):
        with (
            TemporaryDirectory() as root,
            TestClient(create_app(Path(root)), base_url="https://testserver") as client,
        ):
            trip = client.post("/api/v1/trips", json={"title": "부하 시험"}).json()
            member = client.post(
                "/api/v1/join", json={"nickname": "owner", "token": trip["claimToken"]}
            ).json()["memberId"]
            ids = sorted(str(uuid4()) for _ in range(500))
            with closing(connect(Path(root) / "trippick.sqlite3")) as db, db:
                db.executemany(
                    "INSERT INTO photos(id,trip_id,uploader_member_id,object_key,preview_key,mime,size_bytes,sha256,request_key) VALUES(?,?,?,?,?,?,?,?,?)",
                    [
                        (i, trip["tripId"], member, i, i, "image/png", 200, i, i)
                        for i in ids
                    ],
                )
            cursor = ""
            seen = []
            pages = 0
            size = 0
            start = perf_counter()
            while True:
                r = client.get(
                    "/api/v1/trips/" + trip["tripId"] + "/photos",
                    params={"cursor": cursor},
                )
                r.raise_for_status()
                page = r.json()
                size += len(r.content)
                pages += 1
                seen.extend(p["id"] for p in page["items"])
                cursor = page["nextCursor"]
                if not cursor:
                    break
            self.assertEqual(seen, ids)
            self.assertEqual(pages, 13)
            print(
                f"500 metadata rows: {pages} pages, {size} bytes, {(perf_counter() - start) * 1000:.1f} ms"
            )
