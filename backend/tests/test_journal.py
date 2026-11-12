from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.main import create_app
from app.repositories.database import connect
from app.services.matching import match
from app.services.regions import region_for, regions
from fastapi.testclient import TestClient


class Journal(TestCase):
    def test_real_exif_order_and_offset(self):
        from io import BytesIO

        from app.services.matching import extracted
        from PIL import Image

        e = Image.Exif()
        e[34853] = {1: "N", 2: (36, 48, 0), 3: "E", 4: (127, 9, 0)}
        e[34665] = {36867: "2026:11:12 10:00:00", 36881: "+09:00"}
        data = BytesIO()
        Image.new("RGB", (2, 2)).save(data, "JPEG", exif=e)
        self.assertEqual(
            extracted(data.getvalue()), ("2026-11-12T01:00:00+00:00", 36.8, 127.15)
        )

    def test_shared_regions_and_conflicting_metadata(self):
        self.assertEqual(len(regions()), 17)
        self.assertEqual(region_for(36.35, 127.38), "30")
        self.assertEqual(region_for(36.8, 127.15), "44")
        self.assertEqual(region_for(36.64, 127.49), "43")
        with TemporaryDirectory() as root:
            with TestClient(create_app(Path(root)), base_url="https://testserver") as c:
                t = c.post("/api/v1/trips", json={"title": "multi"}).json()
                id = t["tripId"]
                path = "/api/v1/trips/" + id
                m = c.post(
                    "/api/v1/join", json={"token": t["claimToken"], "nickname": "owner"}
                ).json()
                source = {"Authorization": "Bearer " + t["vehicleToken"]}
                event = dict(
                    key="test-only",
                    name="충남 장소",
                    latitude=36.8,
                    longitude=127.15,
                    source="NAVIGATION",
                    kind="CANDIDATE",
                    observedAt="2026-11-12T01:00:00Z",
                )
                self.assertEqual(
                    c.post(
                        path + "/visits",
                        json={**event, "source": "MOCK"},
                        headers=source,
                    ).status_code,
                    403,
                )
                c.app.state.mock_navigation = True
                event["source"] = "MOCK"
                v = c.post(path + "/visits", json=event, headers=source).json()["id"]
                self.assertEqual(
                    c.post(path + "/visits", json=event, headers=source).json()["id"], v
                )
                c.post(
                    path + "/visits", json={**event, "kind": "ARRIVED"}, headers=source
                ).raise_for_status()
                c.post(
                    path + "/visits",
                    json={
                        **event,
                        "key": "manual",
                        "source": "MANUAL",
                        "kind": "CONFIRMED",
                        "name": "대전 장소",
                        "latitude": 36.35,
                        "longitude": 127.38,
                    },
                ).raise_for_status()
                journal = c.get(path + "/journal").json()
                self.assertEqual(
                    {r["region_code"] for r in journal["visits"]}, {"44", "30"}
                )
                self.assertEqual(journal["links"], [])
                with closing(connect(Path(root) / "trippick.sqlite3")) as db, db:
                    db.execute(
                        "INSERT INTO photos(id,trip_id,uploader_member_id,object_key,preview_key,mime,size_bytes,sha256,request_key) VALUES('p',?,?,'o','t','image/png',42,'h','key')",
                        (id, m["memberId"]),
                    )
                    match(db, id, "p", event["observedAt"], 37.5, 127.0)
                    self.assertEqual(
                        db.execute("SELECT count(*) FROM photo_place_links").fetchone()[
                            0
                        ],
                        0,
                    )
                    match(db, id, "p", event["observedAt"], 36.8, 127.15)
                self.assertEqual(
                    c.get(path + "/journal").json()["links"][0]["status"], "CANDIDATE"
                )
                c.put(path + "/photos/p/place", json={"visitId": v}).raise_for_status()
                c.put(
                    path + "/photos/p/place", json={"visitId": None}
                ).raise_for_status()
                c.patch(
                    path + "/visits/" + v, json={"name": "수정", "status": "EXCLUDED"}
                ).raise_for_status()
            with TestClient(create_app(Path(root))) as restored:
                result = restored.get(path + "/journal", headers=source).json()
                self.assertEqual(len(result["visits"]), 2)
                self.assertEqual(result["links"][0]["status"], "UNLINKED")
