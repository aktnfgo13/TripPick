import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .integrations.objects import LocalObjects
from .repositories import database


def create_app(data_dir: Path) -> FastAPI:
    root = data_dir.resolve()
    db_path = root / "trippick.sqlite3"
    objects = root / "objects"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        app.state.objects = LocalObjects(objects)
        database.initialize(db_path)
        yield

    api = FastAPI(title="TripPick", version="0.1.0", lifespan=lifespan)

    @api.get("/api/v1/health")
    def health() -> dict[str, str]:
        try:
            if objects.is_dir() and os.access(objects, os.W_OK) and database.ready(db_path):
                return {"status": "ok"}
        except sqlite3.Error:
            pass
        raise HTTPException(503, "storage unavailable")

    return api


app = create_app(Path(os.getenv("TRIPPICK_DATA_DIR", ".local")))
