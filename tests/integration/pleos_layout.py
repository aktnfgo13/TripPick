"""Inspect the populated album journey on an official Form Factor Test display."""

import io
import os
import re
from pathlib import Path

import zxingcpp
from PIL import Image, ImageDraw
from pleos_album import capture, find, input_event, screen, tap, tree


def run():
    labels = {n.get("text") for n in tree().iter("node")}
    if "QR 닫기" in labels:
        tap("QR 닫기")
    if "기존 여행" in labels:
        tap("기존 여행")
    if any(n.get("text") == "지도 닫기" for n in tree().iter("node")):
        tap("지도 닫기")
    if any(n.get("text") == "목록" for n in tree().iter("node")):
        tap("목록")
    find("공유 앨범")
    capture("home")
    tap("새 여행")
    find("여행 생성")
    capture("create")
    tap("기존 여행")
    tap("참여 QR")
    find("QR 닫기")
    bounds = find("여행 QR", "content-desc").get("bounds")
    image = Image.open(io.BytesIO(screen()))
    assert zxingcpp.read_barcode(image)
    ImageDraw.Draw(image).rectangle(
        tuple(map(int, re.findall(r"\d+", bounds))), fill="gray"
    )
    image.save(Path(os.environ["TRIPPICK_TEST_SCREENSHOTS"]) / "qr-redacted.png")
    tap("QR 닫기")
    find("전체 사진")
    capture("gallery")
    tap(" · 좋아요 1", exact=False)
    find("좋아요 취소 1")
    capture("detail-vote")
    tap("목록")
    tap("공유 앨범")
    find("여행 사진", "content-desc")
    capture("album")
    tap("여행 지도")
    tap("전국 지도")
    find("충청남도 1")
    capture("national")
    tap("충청남도 1")
    find("통합검사 충남 장소")
    capture("region")
    tap("통합검사 충남 장소")
    find("여행일지")
    capture("place-journal")
    tap("장소 앨범 열기")
    find("장소 앨범 닫기")
    capture("place-album")
    tap("전국 지도")
    find("충청남도 1")
    tap("지도 닫기")
    find("전체 사진")
    print("Form Factor Test screen traversal passed", flush=True)


def compact_saved_trips():
    """Run on a short parked display with enough saved trips to overflow the list."""

    def rows():
        return [
            (n.get("text"), n.get("bounds"))
            for n in tree().iter("node")
            if n.get("text", "").startswith("다시 열기")
        ]

    tap("새 여행")
    find("기존 여행")
    area = next(n for n in tree().iter("node") if n.get("scrollable") == "true")
    left, top, right, bottom = map(int, re.findall(r"\d+", area.get("bounds")))
    x = str((left + right) // 2)
    before = rows()
    input_event("swipe", x, str(bottom - 30), x, str(top + 30), "500")
    assert rows() != before
    input_event("swipe", x, str(top + 30), x, str(bottom - 30), "500")
    tap("기존 여행")
    find("공유 앨범")


if __name__ == "__main__":
    if os.getenv("TRIPPICK_TEST_COMPACT_SCROLL") == "1":
        compact_saved_trips()
    else:
        run()
