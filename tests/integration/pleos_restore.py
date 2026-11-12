"""Run on the dedicated Pleos AVD after the album scenario, with Virtual Console forwarded on 8088."""

import time

from playwright.sync_api import sync_playwright
from pleos_album import PACKAGE, adb, find, qr, tap, tree


def launch():
    adb("shell", "am", "start", "-W", "-n", PACKAGE + "/kr.trippick.MainActivity")


def check_restriction(page):
    page.goto("http://127.0.0.1:8088/", wait_until="domcontentloaded")
    page.wait_for_function(
        """async () => (await (await fetch('/vehicle/state')).json()).controls.emulator_active"""
    )

    def put(path):
        response = page.request.put("http://127.0.0.1:8088/vehicle/" + path)
        assert response.ok, (path, response.status)

    try:
        put("gear?gear=Drive")
        put("controls?speed=35&accelerator=0&brake=0")
        find("주차 및 화면 사용 허용", exact=False)
        assert all(
            n.get("text") not in ("목록", "좋아요 취소 1") for n in tree().iter("node")
        )
    finally:
        put("controls?speed=0&accelerator=0&brake=0")
        put("gear?gear=Park")


def run():
    if any(n.get("text") == "지도 닫기" for n in tree().iter("node")):
        tap("지도 닫기")
    trip_label = find("여행 ID ", exact=False).get("text")
    first = find(" · 좋아요 1", exact=False).get("text")
    tap(first)
    find("좋아요 취소 1")
    adb("reboot")
    time.sleep(3)
    adb("wait-for-device")
    for _ in range(90):
        if (
            adb("shell", "getprop", "sys.boot_completed").strip() == b"1"
            and adb("shell", "am", "get-current-user").strip() != b"0"
        ):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Automotive user did not boot")
    launch()
    find(trip_label)
    find("좋아요 취소 1")
    tap("목록")
    qr("참여 QR")
    find(trip_label)
    tap("공유 앨범")
    tap(first)
    adb("forward", "tcp:8088", "tcp:8088")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        check_restriction(browser.new_page())
        browser.close()
    find(trip_label)
    find("좋아요 취소 1")
    tap("목록")
    tap("공유 앨범")
    find(first)
    print(
        "Existing trip, selected photo, QR dismissal, album, driving lock and parked restoration passed."
    )


if __name__ == "__main__":
    run()
