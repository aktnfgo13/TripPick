"""Expire only a newly created fixture in the dedicated local test DB."""

import os
import signal
import sqlite3
import subprocess
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from playwright.sync_api import sync_playwright
from pleos_album import fill_trip_title, find, qr, tap, tree


def check_reconnect(trip):
    # Only pause the explicitly nominated loopback-only test API; HTTPS stays up.
    pid = int(os.environ["TRIPPICK_TEST_API_PID"])
    command = subprocess.check_output(
        ["ps", "-p", str(pid), "-o", "command="], text=True
    )
    listeners = subprocess.check_output(
        ["lsof", "-nP", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN", "-Fn"], text=True
    ).splitlines()
    port = int(os.getenv("TRIPPICK_TEST_API_PORT", "18081"))
    assert f"uvicorn app.main:app --port {port}" in command
    assert [line for line in listeners if line.startswith("n")] == [
        f"n127.0.0.1:{port}"
    ]
    claim = parse_qs(urlsplit(qr("소유권 QR")).fragment)["invite"][0]
    try:
        os.kill(pid, signal.SIGSTOP)
        tap("새로고침")
        find("서버에 연결하지 못했습니다.", exact=False)
        with sync_playwright() as pw:
            client = pw.request.new_context(
                base_url="https://127.0.0.1:"
                + str(int(os.getenv("TRIPPICK_TEST_TLS_PORT", "19444"))),
                ignore_https_errors=True,
            )
            response = client.post(
                "/api/v1/join", data={"token": claim, "nickname": "NetworkOwner"}
            )
            assert response.ok, response.status
            client.dispose()
    finally:
        os.kill(pid, signal.SIGCONT)
    tap("새로고침")
    find("NetworkOwner", exact=False)
    find("여행 ID " + trip)
    print(
        "Vehicle network failure, retry and synchronization of a missed membership change passed.",
        flush=True,
    )


def run():
    name = "Expiry" + uuid4().hex
    if any(n.get("text") == "새 여행" for n in tree().iter("node")):
        tap("새 여행")
    fill_trip_title(name)
    tap("여행 생성")
    find(name, exact=False)
    trip = find("여행 ID ", exact=False).get("text").split()[-1]
    if os.getenv("TRIPPICK_TEST_NETWORK") == "1":
        check_reconnect(trip)
    with sqlite3.connect(os.environ["TRIPPICK_TEST_DB"]) as db:
        updated = db.execute(
            "UPDATE vehicle_sessions SET expires=0 WHERE trip_id=? AND EXISTS "
            "(SELECT 1 FROM trips WHERE id=? AND title=?)",
            (trip, trip, name),
        )
        assert updated.rowcount == 1
    find("저장된 여행에 접근할 수 없습니다.", exact=False)
    find("여행 생성")
    with sqlite3.connect(os.environ["TRIPPICK_TEST_DB"]) as db:
        assert db.execute("SELECT title FROM trips WHERE id=?", (trip,)).fetchone() == (
            name,
        )
    print("Expired vehicle session returned to trip selection; server trip preserved.")


if __name__ == "__main__":
    run()
