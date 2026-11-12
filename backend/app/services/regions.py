import json
from functools import cache
from pathlib import Path

BOUNDARIES = Path(__file__).resolve().parents[3] / "assets/maps/korea.geojson"


@cache
def regions():
    return json.loads(BOUNDARIES.read_text())["features"]


def inside_ring(x, y, ring):
    inside = False
    for (a, b), (c, d) in zip(ring, ring[1:]):
        if (b > y) != (d > y) and x < (c - a) * (y - b) / (d - b) + a:
            inside = not inside
    return inside


def region_for(latitude, longitude):
    if latitude is None or longitude is None:
        return None
    for feature in regions():
        geometry = feature["geometry"]
        polygons = (
            geometry["coordinates"]
            if geometry["type"] == "MultiPolygon"
            else [geometry["coordinates"]]
        )
        for outer, *holes in polygons:
            if inside_ring(longitude, latitude, outer) and not any(
                inside_ring(longitude, latitude, h) for h in holes
            ):
                return feature["properties"]["code"]
    return None
