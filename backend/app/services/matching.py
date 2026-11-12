from datetime import datetime, timezone
from io import BytesIO
from math import asin, cos, isfinite, radians, sin, sqrt

from PIL import Image


def extracted(data):
    with Image.open(BytesIO(data)) as img:
        exif = img.getexif()
        tags = exif.get_ifd(34665)
        gps = exif.get_ifd(34853)
    stamp = None
    if tags.get(36867) and tags.get(36881):
        stamp = (
            datetime.strptime(tags[36867] + tags[36881], "%Y:%m:%d %H:%M:%S%z")
            .astimezone(timezone.utc)
            .isoformat()
        )

    def coord(key, ref, negative):
        deg, minute, sec = map(float, gps[key])
        return (deg + minute / 60 + sec / 3600) * (-1 if gps[ref] == negative else 1)

    if all(k in gps for k in (1, 2, 3, 4)):
        lat, lon = coord(2, 1, "S"), coord(4, 3, "W")
        if isfinite(lat) and isfinite(lon) and abs(lat) <= 90 and abs(lon) <= 180:
            return stamp, lat, lon
    return stamp, None, None


def meters(a, b, c, d):
    h = (
        sin(radians(c - a) / 2) ** 2
        + cos(radians(a)) * cos(radians(c)) * sin(radians(d - b) / 2) ** 2
    )
    return 12742000 * asin(sqrt(min(1, h)))


def match(db, trip, photo, stamp, lat, lon):
    candidates = []
    for r in db.execute(
        """SELECT v.id,v.observed_at,v.arrival_at,v.departure_at,p.latitude,p.longitude FROM visits v JOIN places p ON p.id=v.place_id
        WHERE v.trip_id=? AND v.status!='EXCLUDED'""",
        (trip,),
    ):
        time_delta = None
        if stamp:
            shot = datetime.fromisoformat(stamp)
            start = datetime.fromisoformat(r["arrival_at"] or r["observed_at"])
            end = (
                datetime.fromisoformat(r["departure_at"])
                if r["departure_at"]
                else start
            )
            time_delta = max(
                0, (start - shot).total_seconds(), (shot - end).total_seconds()
            )
        distance = (
            meters(lat, lon, r["latitude"], r["longitude"])
            if lat is not None and r["latitude"] is not None
            else None
        )
        if time_delta is not None and time_delta > 7200:
            continue
        if distance is not None and distance > 500:
            continue
        if distance is not None or (time_delta is not None and time_delta <= 1800):
            candidates.append(r["id"])
    if len(candidates) == 1:
        db.execute(
            "INSERT OR IGNORE INTO photo_place_links VALUES(?,?,?,'CANDIDATE')",
            (trip, photo, candidates[0]),
        )


def classify_upload(db, trip, photo, data):
    stamp, lat, lon = extracted(data)
    db.execute("INSERT INTO photo_metadata VALUES(?,?,?,?)", (photo, stamp, lat, lon))
    match(db, trip, photo, stamp, lat, lon)
