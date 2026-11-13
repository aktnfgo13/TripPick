import json
from functools import cache
from pathlib import Path

MAPS = Path(__file__).resolve().parents[3] / "assets/maps"


@cache
def catalog():
    return json.loads((MAPS / "catalog.json").read_text())


@cache
def successors():
    return {
        old: change["code"]
        for change in catalog()["changes"]
        for old in change["predecessors"]
    }


def current_code(code):
    return successors().get(code, code)


@cache
def regions():
    features = json.loads((MAPS / "korea.geojson").read_text())["features"]
    active = [f for f in features if f["properties"]["code"] not in successors()]
    for change in catalog()["changes"]:
        active.append(
            {
                "type": "Feature",
                "properties": {k: v for k, v in change.items() if k != "geometry"},
                "geometry": json.loads((MAPS / change["geometry"]).read_text()),
            }
        )
    return active


def ring_position(x, y, ring):
    """Return 1 inside, -1 outside, 0 on an edge (including vertices)."""
    inside = False
    for (a, b), (c, d) in zip(ring, ring[1:]):
        cross = (x - a) * (d - b) - (y - b) * (c - a)
        if (
            min(a, c) <= x <= max(a, c)
            and min(b, d) <= y <= max(b, d)
            and abs(cross) <= 1e-12
        ):
            return 0
        if (b > y) != (d > y) and x < (c - a) * (y - b) / (d - b) + a:
            inside = not inside
    return 1 if inside else -1


def resolve(latitude, longitude, features):
    matches = set()
    for feature in features:
        geometry = feature["geometry"]
        polygons = (
            geometry["coordinates"]
            if geometry["type"] == "MultiPolygon"
            else [geometry["coordinates"]]
        )
        for outer, *holes in polygons:
            side = ring_position(longitude, latitude, outer)
            if side == 0:
                return None
            if side < 0:
                continue
            inner = [ring_position(longitude, latitude, h) for h in holes]
            if 0 in inner:
                return None
            if 1 not in inner:
                matches.add(feature["properties"]["code"])
    return next(iter(matches)) if len(matches) == 1 else None


def region_for(latitude, longitude):
    if latitude is None or longitude is None:
        return None
    return resolve(latitude, longitude, regions())
