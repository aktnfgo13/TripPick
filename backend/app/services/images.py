from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 32_000_000


def thumbnail(data, mime):
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in ("JPEG", "PNG") or Image.MIME[image.format] != mime:
                raise ValueError("JPEG 또는 PNG 파일을 선택하세요.")
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("이미지 해상도 제한 초과")
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image.thumbnail((640, 640))
            preview = ImageOps.exif_transpose(image).convert("RGB")
            out = BytesIO()
            preview.save(out, "JPEG", quality=83)
            return out.getvalue()
    except (OSError, Image.DecompressionBombError, UnidentifiedImageError) as exc:
        raise ValueError("손상되었거나 지원하지 않는 이미지") from exc
