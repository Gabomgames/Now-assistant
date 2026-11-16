"""Authenticated loopback API for native clients. No history, passwords or audio routes."""
from collections import deque
import argparse
import os
import secrets
from threading import Lock
import time
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

from .assistant import LocalAssistant, LocalModelUnavailable


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["pt-BR", "en-US"] = "pt-BR"
    persona: Literal["classic", "casual", "gamer", "focus", "creative"] = "casual"
    humor: int = Field(default=1, ge=0, le=3, strict=True)
    reply_length: Literal["short", "balanced", "detailed"] = "balanced"
    display_name: str | None = Field(default=None, min_length=1, max_length=80)


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[Message] = Field(min_length=1, max_length=20)
    settings: Settings = Field(default_factory=Settings)


class LocalSecurity:
    def __init__(self, app, token):
        self.app, self.token = app, token.encode("ascii")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {key.lower(): value for key, value in scope["headers"]}
        authorization = headers.get(b"authorization", b"")
        if not authorization.startswith(b"Bearer ") or not secrets.compare_digest(authorization[7:], self.token):
            return await JSONResponse({"error": "UNAUTHORIZED"}, status_code=401)(scope, receive, send)
        if b"origin" in headers:
            return await JSONResponse({"error": "BROWSER_ORIGIN_FORBIDDEN"}, status_code=403)(scope, receive, send)
        chunks, size = [], 0
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            chunk = event.get("body", b"")
            size += len(chunk)
            if size > 65536:
                return await JSONResponse({"error": "PAYLOAD_TOO_LARGE"}, status_code=413)(scope, receive, send)
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


def create_app(token, instance_id):
    if not isinstance(token, str) or len(token) < 32 or not token.isascii():
        raise ValueError("a fresh ASCII token of at least 32 characters is required")
    app = FastAPI(title="NOW Assistant", version="0.3.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(LocalSecurity, token=token)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    assistant, active, rate_lock, requests = LocalAssistant(), Lock(), Lock(), deque()

    @app.get("/v2/health")
    def health():
        return {"status": "ok", "product": "NOW Assistant", "api_version": "0.3.0", "instance_id": instance_id}

    @app.get("/v2/capabilities")
    def capabilities():
        try:
            model = assistant.installed_model()
        except LocalModelUnavailable:
            model = None
        return {"text_chat": True, "processing": "local", "model": model,
                "model_installed": model is not None, "capture": False, "speech_output": False,
                "wake_word": False, "screen_analysis": False, "cloud": False}

    @app.post("/v2/chat")
    def chat(payload: ChatRequest):
        if payload.messages[-1].role != "user":
            raise HTTPException(422, detail={"error": "LAST_MESSAGE_MUST_BE_USER"})
        with rate_lock:
            now = time.monotonic()
            while requests and requests[0] < now - 60:
                requests.popleft()
            if len(requests) >= 60:
                raise HTTPException(429, detail={"error": "RATE_LIMITED"})
            requests.append(now)
        if not active.acquire(blocking=False):
            raise HTTPException(409, detail={"error": "ENGINE_BUSY"})
        try:
            messages = [message.model_dump() for message in payload.messages]
            last = messages[-1]["content"]
            if not last.strip() or len(last) > 4000:
                raise HTTPException(422, detail={"error": "INVALID_MESSAGE"})
            used = assistant.messages(last, messages[:-1])
            reply = assistant.reply(last, payload.settings, messages[:-1])
            return {"reply": reply.text, "provider": reply.provider, "processing": "local",
                    "context_messages": len(used), "context_trimmed": len(used) < len(messages)}
        except LocalModelUnavailable:
            raise HTTPException(503, detail={"error": "MODEL_UNAVAILABLE"}) from None
        except ValueError:
            raise HTTPException(422, detail={"error": "INVALID_CONTEXT"}) from None
        finally:
            active.release()

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("invalid port")
    token = os.environ.get("NOW_DESKTOP_TOKEN", "")
    instance = os.environ.get("NOW_DESKTOP_INSTANCE", "")
    if not instance:
        parser.error("a desktop instance id is required")
    import uvicorn
    uvicorn.run(create_app(token, instance), host="127.0.0.1", port=args.port,
                access_log=False, log_level="warning", timeout_graceful_shutdown=2)


if __name__ == "__main__":
    main()
