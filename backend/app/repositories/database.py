from contextlib import closing
from pathlib import Path
import sqlite3

BASELINE = Path(__file__).resolve().parents[2] / "migrations/001_foundation.sql"


def initialize(path: Path) -> None:
    with closing(sqlite3.connect(path)) as db:
        db.executescript(BASELINE.read_text())


def ready(path: Path) -> bool:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute("SELECT 1 FROM schema_migrations WHERE version=1").fetchone() is not None
