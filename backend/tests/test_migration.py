from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.repositories.database import BASELINE, initialize


class PhaseOneUpgrade(unittest.TestCase):
    def test_existing_storage_survives_upgrade_and_second_start(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "trippick.sqlite3"
            with closing(sqlite3.connect(path)) as db:
                db.executescript(BASELINE.read_text())
                timestamp = db.execute(
                    "SELECT applied_at FROM schema_migrations WHERE version=1"
                ).fetchone()
            original = root / "objects" / "f5bdac8d-9715-47e4-99f9-54ce54bd0950"
            original.parent.mkdir()
            original.write_bytes(b"phase one")
            initialize(path)
            initialize(path)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(
                    db.execute(
                        "SELECT applied_at FROM schema_migrations WHERE version=1"
                    ).fetchone(),
                    timestamp,
                )
                self.assertEqual(
                    db.execute(
                        "SELECT version FROM schema_migrations ORDER BY version"
                    ).fetchall(),
                    [(1,), (2,), (3,), (4,)],
                )
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(original.read_bytes(), b"phase one")
