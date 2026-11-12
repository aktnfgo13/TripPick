import io
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import zxingcpp
from PIL import Image
from playwright.sync_api import expect, sync_playwright


def adb(*args):
    return subprocess.check_output(["adb", "-e", *args])


def tree():
    adb("shell", "uiautomator", "dump", "/data/local/tmp/test-tree.xml")
    return ET.fromstring(adb("shell", "cat", "/data/local/tmp/test-tree.xml"))


def find(label, field="text", exact=True):
    root = tree()
    for n in root.iter("node"):
        val = n.get(field, "")
        if val == label if exact else label in val:
            return n
    raise AssertionError(
        (label, [n.get("text") for n in root.iter("node") if n.get("text")])
    )


def tap(label, field="text", exact=True):
    n = find(label, field, exact)
    x, y, a, b = map(int, re.findall(r"\d+", n.get("bounds")))
    adb("shell", "input", "tap", str((x + a) // 2), str((y + b) // 2))
    time.sleep(0.45)


def qr(label):
    tap(label)
    for _ in range(5):
        image = Image.open(io.BytesIO(adb("exec-out", "screencap", "-p")))
        result = zxingcpp.read_barcode(image)
        if result:
            tap("QR 닫기")
            return result.text
        time.sleep(0.3)
    raise RuntimeError("QR decode failed")


def run():
    stamp = str(int(time.time()))
    name = "Trip" + stamp
    if any(n.get("text") == "새 여행" for n in tree().iter("node")):
        tap("새 여행")
    tap("android.widget.EditText", "class")
    adb("shell", "input", "text", name)
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
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
                dict(name="image.png", mimeType="image/png", buffer=img.getvalue())
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
        first.get_by_role("button").click()
        expect(first.get_by_role("button")).to_have_text("좋아요 취소 1")
        print("Four isolated browser joins, uploads, sync OK", flush=True)
        pair = qr("계정 연결")
        pages[0].goto(pair)
        pages[0].get_by_text("연결 확인", exact=True).click()
        expect(pages[0].get_by_role("heading", name=name)).to_be_visible()
        time.sleep(5)
        tap(" · 좋아요 1", exact=False)
        tap("좋아요 취소 1")
        expect(first.get_by_role("button")).to_have_text("좋아요 0", timeout=15000)
        tap("좋아요 0")
        expect(first.get_by_role("button")).to_have_text("좋아요 취소 1", timeout=15000)
        adb("shell", "am", "force-stop", "kr.trippick.vehicle")
        adb(
            "shell", "am", "start", "-n", "kr.trippick.vehicle/kr.trippick.MainActivity"
        )
        time.sleep(2)
        tap("목록")
        tap("최종 선정")
        tap("앨범 확정")
        for p in pages:
            link = p.get_by_role("link", name="다운로드")
            expect(link).to_be_visible(timeout=15000)
            with p.expect_download() as dl:
                link.click()
            assert Image.open(dl.value.path()).format == "PNG"
        tap("공유 앨범")
        assert (
            sum(n.get("content-desc") == "여행 사진" for n in tree().iter("node")) == 1
        )
        print(
            "Vehicle detail, same-member votes, restart, vehicle publish + 4 album downloads OK",
            flush=True,
        )
        browser.close()


if __name__ == "__main__":
    run()
