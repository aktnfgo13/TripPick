import asyncio
from contextlib import closing

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..repositories.database import connect
from .access import actor

router = APIRouter(prefix="/api/v1/trips")


@router.websocket("/{trip}/events")
async def events(ws: WebSocket, trip: str):
    def revision():
        with closing(connect(ws.app.state.db_path)) as db:
            actor(ws, db, trip)
            return db.execute(
                "SELECT revision FROM trips WHERE id=?", (trip,)
            ).fetchone()[0]

    try:
        origin = ws.headers.get("origin")
        if origin and origin.split("://", 1)[-1] != ws.headers.get("host"):
            await ws.close(code=1008)
            return
        current = await asyncio.to_thread(revision)
        await ws.accept()
        while True:
            await ws.send_json({"revision": current})
            previous = current
            while previous == current:
                try:
                    await asyncio.wait_for(ws.receive_text(), timeout=1)
                except asyncio.TimeoutError:
                    pass
                current = await asyncio.to_thread(revision)
    except HTTPException:
        await ws.close(code=1008)
    except WebSocketDisconnect:
        pass
