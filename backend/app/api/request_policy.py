from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from ..services.images import MAX_BYTES


class RequestPolicy:
    """Reject cross-origin writes and bound the complete multipart envelope before parsing."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in {"GET", "HEAD", "OPTIONS"}:
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if origin and urlsplit(origin).netloc != headers.get("host"):
            return await JSONResponse({"detail": "다른 출처의 변경 요청"}, 403)(
                scope, receive, send
            )
        limit = (
            MAX_BYTES + 64 * 1024 if scope["path"].endswith("/photos") else 128 * 1024
        )
        # Vite, browsers and the vehicle HTTP client set Content-Length for these fixed-size payloads.
        length = headers.get("content-length", "0")
        if "transfer-encoding" in headers or not length.isdigit():
            return await JSONResponse({"detail": "Content-Length 필요"}, 411)(
                scope, receive, send
            )
        if int(length) > limit:
            return await JSONResponse({"detail": "요청 크기 제한 초과"}, 413)(
                scope, receive, send
            )
        await self.app(scope, receive, send)
