import unittest

from app.services.regions import current_code, region_for, resolve


class RegionTest(unittest.TestCase):
    def test_public_offices(self):
        # Public street-address geocodes, WGS84. Source and address list in the validation report.
        for name, lat, lon, code in [
            ("광주청사", 35.160099, 126.851462, "12"),
            ("무안청사", 34.816986, 126.462707, "12"),
            ("대전시청", 36.350385, 127.384633, "30"),
            ("충남도청", 36.659071, 126.672972, "44"),
            ("충북도청", 36.636129, 127.491270, "43"),
            ("천안시청", 36.815718, 127.112921, "44"),
            ("서울시청", 37.566695, 126.978376, "11"),
            ("제주도청", 33.488411, 126.497584, "50"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(region_for(lat, lon), code)
        self.assertIsNone(region_for(0, 0))
        self.assertEqual(current_code("29"), current_code("46"))

    def test_edges_holes_islands_and_overlaps(self):
        def square(left, bottom, size):
            right, top = left + size, bottom + size
            return [
                [left, bottom],
                [right, bottom],
                [right, top],
                [left, top],
                [left, bottom],
            ]

        islands = {
            "properties": {"code": "a"},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[square(0, 0, 4), square(1, 1, 1)], [square(6, 0, 1)]],
            },
        }
        adjacent = {
            "properties": {"code": "b"},
            "geometry": {"type": "Polygon", "coordinates": [square(4, 0, 2)]},
        }
        features = [islands, adjacent]
        self.assertIsNone(resolve(1, 4, features))
        self.assertIsNone(resolve(1.5, 1, features))
        self.assertIsNone(resolve(1.5, 1.5, features))
        self.assertEqual(resolve(1, 3.999, features), "a")
        self.assertEqual(resolve(1, 4.001, features), "b")
        self.assertEqual(resolve(0.5, 6.5, features), "a")
        adjacent["geometry"]["coordinates"] = [square(3, 0, 2)]
        self.assertIsNone(resolve(0.5, 3.5, features))
