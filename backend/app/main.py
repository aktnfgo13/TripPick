import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from fastapi.staticfiles import StaticFiles
from .api import albums, events, photos, trips
from .api.request_policy import RequestPolicy
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

    api = FastAPI(title="TripPick", version="0.2.0", lifespan=lifespan)
    api.state.db_path = db_path
    api.state.secure_cookie = os.getenv("TRIPPICK_DEV_HTTP") != "1"
    api.add_middleware(RequestPolicy)
    for feature in (trips, photos, albums, events):
        api.include_router(feature.router)

    @api.get("/api/v1/health")
    def health() -> dict[str, str]:
        try:
            if objects.is_dir() and os.access(objects, os.W_OK) and database.ready(db_path):
                return {"status": "ok"}
        except sqlite3.Error:
            pass
        raise HTTPException(503, "storage unavailable")

    web_dir = os.getenv("TRIPPICK_WEB_DIST")
    if web_dir:
        api.mount("/", StaticFiles(directory=web_dir, html=True), name="mobile")
    return api


app = create_app(Path(os.getenv("TRIPPICK_DATA_DIR", ".local")))
