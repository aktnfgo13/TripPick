import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from app.main import create_app


class FoundationTest(unittest.TestCase):
    def test_restart(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            first = create_app(path)
            with TestClient(first) as client:
                self.assertEqual(client.get("/api/v1/health").json(), {"status": "ok"})
                key = first.state.objects.put(b"persist")
            second = create_app(path)
            with TestClient(second) as client:
                self.assertEqual(client.get("/api/v1/health").status_code, 200)
                self.assertEqual(second.state.objects.read(key), b"persist")

    def test_missing_database(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            with TestClient(create_app(path)) as client:
                (path / "trippick.sqlite3").unlink()
                self.assertEqual(client.get("/api/v1/health").status_code, 503)
                self.assertFalse((path / "trippick.sqlite3").exists())
