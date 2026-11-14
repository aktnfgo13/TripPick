import io
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import zxingcpp
from PIL import Image
from playwright.sync_api import expect, sync_playwright


def adb(*args):
    return subprocess.check_output(["adb", "-e", *args])


DISPLAY = os.getenv("TRIPPICK_TEST_DISPLAY", "0")
PACKAGE = "kr.trippick.vehicle"


def tree():
    path = "/data/local/tmp/trippick-" + uuid4().hex + ".xml"
    try:
        result = adb("shell", "uiautomator", "dump", "--windows", path)
        if b"dumped to:" not in result:
            return ET.Element("pending")
        displays = ET.fromstring(adb("shell", "cat", path))
        display = displays.find(f"./display[@id='{DISPLAY}']")
        if display is not None:
            for window in display.findall("window"):
                if window.find(f".//node[@package='{PACKAGE}']") is not None:
                    return window
        return ET.Element("pending")
    except subprocess.CalledProcessError as exc:
        if exc.returncode == 137 and "uiautomator" in exc.cmd:
            return ET.Element("pending")
        raise
    finally:
        adb("shell", "rm", "-f", path)


def find(label, field="text", exact=True):
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        root = tree()
        for n in root.iter("node"):
            val = n.get(field, "")
            if (val == label if exact else label in val) and n.get("enabled") == "true":
                return n
        time.sleep(0.25)
    raise AssertionError(
        (label, [n.get("text") for n in root.iter("node") if n.get("text")])
    )


def input_event(*args):
    adb("shell", "input", "-d", DISPLAY, *args)


def tap(label, field="text", exact=True):
    n = find(label, field, exact)
    x, y, a, b = map(int, re.findall(r"-?\d+", n.get("bounds")))
    assert a > x and b > y, (label, n.get("bounds"))
    input_event("tap", str((x + a) // 2), str((y + b) // 2))


def screen():
    if DISPLAY == "0":
        return adb("exec-out", "screencap", "-p")
    with TemporaryDirectory() as folder:
        adb("emu", "screenrecord", "screenshot", "--display", "2", folder)
        return next(Path(folder).glob("*.png")).read_bytes()


def capture(name):
    folder = os.getenv("TRIPPICK_TEST_SCREENSHOTS")
    if folder:
        target = Path(folder)
        target.mkdir(parents=True, exist_ok=True)
        (target / (name + ".png")).write_bytes(screen())


def fill_trip_title(name):
    tap("android.widget.EditText", "class")
    input_event("keycombination", "KEYCODE_CTRL_LEFT", "KEYCODE_A")
    input_event("keyevent", "KEYCODE_DEL")
    input_event("text", name)
    input_event("keyevent", "KEYCODE_BACK")
    assert find("android.widget.EditText", "class").get("text") == name


def qr(label):
    tap(label)
    find("QR 닫기")
    for _ in range(5):
        result = zxingcpp.read_barcode(Image.open(io.BytesIO(screen())))
        if result:
            tap("QR 닫기")
            find("전체 사진")
            return result.text
        time.sleep(0.3)
    raise RuntimeError("QR decode failed")


def run():
    stamp = uuid4().hex[:8]
    name = "Trip" + stamp
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        labels = {n.get("text") for n in tree().iter("node")}
        if labels & {"새 여행", "여행 생성", "지도 닫기"}:
            break
    else:
        raise AssertionError(
            "TripPick launch window was not visible on the target display"
        )
    if "지도 닫기" in labels:
        tap("지도 닫기")
    capture("home")
    if any(n.get("text") == "새 여행" for n in tree().iter("node")):
        tap("새 여행")
    find("여행 생성")
    capture("create")
    fill_trip_title(name)
    tap("여행 생성")
    time.sleep(2)
    invite = qr("참여 QR")
    claim = qr("소유권 QR")
    print("Vehicle creation + actual QR decode OK", flush=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            headless=True,
            args=(
                [
                    "--host-resolver-rules=MAP trippick.test 127.0.0.1",
                    "--no-proxy-server",
                ]
                if os.getenv("TRIPPICK_TEST_LOOPBACK") == "1"
                else []
            ),
        )
        pages = []
        originals = {}
        for i in range(4):
            page = browser.new_context(
                ignore_https_errors=os.getenv("TRIPPICK_TEST_LOOPBACK") == "1",
                viewport={"width": 393, "height": 852},
            ).new_page()
            page.goto(claim if i == 0 else invite)
            page.get_by_label("닉네임").fill("Member" + str(i))
            page.get_by_role("button", name="여행 참여").click()
            expect(page.get_by_role("heading", name=name)).to_be_visible()
            img = io.BytesIO()
            Image.new("RGB", (40 + i, 32), (80 + 30 * i, 20, 10)).save(img, "PNG")
            originals["Member" + str(i)] = img.getvalue()
            matcher = "**/api/v1/trips/*/photos"
            if i == 0:
                page.route(
                    matcher,
                    lambda route: (
                        route.abort()
                        if route.request.method == "POST"
                        else route.continue_()
                    ),
                )
            page.locator("input[type=file]").set_input_files(
                {"name": "image.png", "mimeType": "image/png", "buffer": img.getvalue()}
            )
            if i == 0:
                retry = page.get_by_role("button", name="재시도")
                expect(retry).to_be_visible()
                page.unroute(matcher)
                retry.click()
            expect(page.get_by_text(re.compile("100% · 완료"))).to_be_visible()
            pages.append(page)
        for p in pages:
            expect(p.locator(".grid").first.locator("article")).to_have_count(4)
        first = pages[0].locator(".grid").first.locator("article").first
        original = originals[first.locator("p").inner_text()]
        pages[3].context.set_offline(True)
        try:
            first.get_by_role("button").click()
            expect(first.get_by_role("button")).to_have_text("좋아요 취소 1")
        finally:
            pages[3].context.set_offline(False)
        expect(
            pages[3]
            .locator(".grid")
            .first.locator("article")
            .first.get_by_role("button")
        ).to_have_text("좋아요 1", timeout=20000)
        expect(first.get_by_role("button")).to_have_text("좋아요 취소 1")
        print("Four isolated browser joins, uploads, sync OK", flush=True)
        if os.getenv("TRIPPICK_TEST_JOURNAL") == "1":
            tap("자동 기록 시작")
            time.sleep(2)
            page = pages[0]
            page.get_by_role("button", name="여행 지도").click()
            frame = page.frame_locator("iframe")
            count = page.evaluate("async () => (await (await fetch('/api/v1/regions')).json()).features.length")
            expect(frame.locator("#choices button")).to_have_count(count)
            for alias in ("광주", "전남"):
                frame.get_by_role("searchbox").fill(alias)
                expect(frame.locator("#choices button")).to_have_count(1)
                expect(frame.locator("#choices button")).to_contain_text(
                    "전남광주통합특별시"
                )
            frame.get_by_role("searchbox").fill("")
            frame.get_by_text("방문 기록과 사진 편집").click()
            frame.get_by_label("장소명").fill("통합검사 충남 장소")
            frame.get_by_label("위도").fill("36.8")
            frame.get_by_label("경도").fill("127.15")
            frame.get_by_role("button", name="방문 등록").click()
            option = frame.locator("#visit option").filter(
                has_text="통합검사 충남 장소"
            )
            expect(option).to_have_count(1)
            frame.locator("#visit").select_option(option.get_attribute("value"))
            frame.get_by_role("button", name="장소 연결 저장").click()
            frame.get_by_role("button", name="충청남도 1").click()
            expect(frame.locator("#map circle")).to_have_count(1)
            frame.locator("#map circle").click()
            expect(frame.locator("#detail img")).to_have_count(1)
            frame.get_by_role("button", name="확대").click()
            expect(frame.locator("#map circle")).to_have_count(1)
            page.get_by_role("button", name="지도 닫기").click()
            print(
                "Live recording requested; manual Chungnam fixture + photo link + map pin OK",
                flush=True,
            )
        pair = qr("계정 연결")
        pages[0].goto(pair)
        pages[0].get_by_text("연결 확인", exact=True).click()
        expect(pages[0].get_by_role("heading", name=name)).to_be_visible()
        time.sleep(5)
        capture("gallery")
        tap(" · 좋아요 1", exact=False)
        capture("detail")
        tap("좋아요 취소 1")
        expect(first.get_by_role("button")).to_have_text("좋아요 0", timeout=15000)
        tap("좋아요 0")
        expect(first.get_by_role("button")).to_have_text("좋아요 취소 1", timeout=15000)
        for p in pages[1:]:
            expect(
                p.locator(".grid").first.locator("article").first.get_by_role("button")
            ).to_have_text("좋아요 1", timeout=15000)
        adb("shell", "am", "force-stop", "kr.trippick.vehicle")
        adb(
            "shell",
            "am",
            "start",
            "-W",
            "--display",
            DISPLAY,
            "-n",
            "kr.trippick.vehicle/kr.trippick.MainActivity",
        )
        time.sleep(2)
        find("좋아요 취소 1")
        find(name, exact=False)
        tap("목록")
        tap("최종 선정")
        tap("앨범 확정")
        for p in pages:
            link = p.get_by_role("link", name="다운로드")
            expect(link).to_be_visible(timeout=15000)
            with p.expect_download() as dl:
                link.click()
            assert Image.open(dl.value.path()).format == "PNG"
            assert dl.value.path().read_bytes() == original
        tap("공유 앨범")
        find("여행 사진", "content-desc")
        capture("album")
        assert (
            sum(n.get("content-desc") == "여행 사진" for n in tree().iter("node")) == 1
        )
        print(
            "Vehicle detail, same-member votes, restart, vehicle publish + 4 album downloads OK",
            flush=True,
        )
        if os.getenv("TRIPPICK_TEST_JOURNAL") == "1":
            tap("여행 지도")
            time.sleep(2)
            find("충청남도 1")
            capture("national")
            tap("충청남도 1")
            find("통합검사 충남 장소")
            capture("region")
            tap("통합검사 충남 장소")
            find("사진 1장", exact=False)
            find("여행일지")
            capture("journal")
            tap("전국 지도")
            find("충청남도 1")
            print(
                "Pleos regional map, visit detail and shared photo verified", flush=True
            )
        browser.close()


if __name__ == "__main__":
    run()
