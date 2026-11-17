"""Shared native loopback authentication/body guard; no browser access."""
import secrets
from starlette.responses import JSONResponse


class LocalSecurity:
    def __init__(self, app, token):
        self.app, self.token = app, token.encode("ascii")

    def deny(self, scope, code, status):
        return JSONResponse({"error": code}, status_code=status)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {key.lower(): value for key, value in scope["headers"]}
        authorization = headers.get(b"authorization", b"")
        if not authorization.startswith(b"Bearer ") or not secrets.compare_digest(authorization[7:], self.token):
            return await self.deny(scope, "UNAUTHORIZED", 401)(scope, receive, send)
        if b"origin" in headers:
            return await self.deny(scope, "BROWSER_ORIGIN_FORBIDDEN", 403)(scope, receive, send)
        chunks, size = [], 0
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            chunk = event.get("body", b"")
            size += len(chunk)
            if size > 65536:
                return await self.deny(scope, "PAYLOAD_TOO_LARGE", 413)(scope, receive, send)
            chunks.append(chunk)
            if not event.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

