"""Authenticated local NOW Brain API v1. No remote deployment profile."""
import asyncio
from contextlib import suppress
import json
import re
from uuid import uuid4

import anyio
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer

from now_engine.security import LocalSecurity
from .contracts import ChatRequest, CancelRequest, ChatResult, ErrorResult, ModelList, Health, CancelResult
from .orchestrator import Brain
from .provider import BrainError, OllamaProvider

PREFIX = "/api/now/v1"


def error_body(code, request_id, retryable=False):
    return {"api_version": "1.0", "error": {"code": code, "request_id": request_id, "retryable": retryable}}


class BrainSecurity(LocalSecurity):
    """Reuse the legacy native process guard, with v1 errors and request correlation."""
    def deny(self, scope, code, status):
        identifier = scope["state"]["request_id"]
        return JSONResponse(error_body(code.lower(), identifier), status_code=status)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await super().__call__(scope, receive, send)
        identifier = str(uuid4())
        scope.setdefault("state", {})["request_id"] = identifier
        host = dict(scope["headers"]).get(b"host", b"").decode("ascii", errors="replace")
        if not re.fullmatch(r"(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?", host):
            return await JSONResponse(error_body("invalid_host", identifier), status_code=400,
                                      headers={"X-Request-ID": identifier, "Cache-Control": "no-store"})(scope, receive, send)

        async def versioned_send(message):
            # Correlate guard and application responses without logging their bodies.
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([(b"x-request-id", identifier.encode()),
                                                          (b"cache-control", b"no-store")])
            await send(message)

        # Guard validates auth, Origin and body before app code sees a request.
        await super().__call__(scope, receive, versioned_send)


def create_app(token, *, instance_id=None, provider=None):
    if not isinstance(token, str) or len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("a private ASCII process token of at least 32 characters is required")
    app = FastAPI(title="NOW Brain local API", version="1.0", docs_url=None, redoc_url=None,
                  openapi_url=None, dependencies=[Depends(HTTPBearer(auto_error=False))],
                  responses={code: {"model": ErrorResult} for code in (400, 401, 403, 409, 413, 422, 429, 502, 503, 504)})
    app.add_middleware(BrainSecurity, token=token)
    brain = Brain(provider or OllamaProvider())
    app.state.brain = brain
    identity = instance_id or str(uuid4())

    @app.exception_handler(BrainError)
    async def brain_error(request, error):
        return JSONResponse(error_body(error.code, request.state.request_id, error.retryable), status_code=error.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # FastAPI's default validation detail echoes private input values.
        return JSONResponse(error_body("invalid_request", request.state.request_id), status_code=422)

    def inventory():
        rows = brain.provider.models()
        default = OllamaProvider.default_model()
        return ModelList(models=rows, default_model_id=default if default in {row.model_id for row in rows} else None)

    @app.get(PREFIX + "/health", response_model=Health)
    async def health(check_provider: bool = True):
        if not check_provider:
            return {"api_version": "1.0", "live": True, "ready": False, "instance_id": identity,
                    "profile": "local", "provider_status": "not_checked"}
        try:
            models = await anyio.to_thread.run_sync(inventory)
            ready = models.default_model_id is not None
            provider_status = "available" if ready else "model_not_installed"
        except BrainError as error:
            ready, provider_status = False, error.code
        return {"api_version": "1.0", "live": True, "ready": ready, "instance_id": identity,
                "profile": "local", "provider_status": provider_status}

    @app.get(PREFIX + "/capabilities")
    async def capabilities():
        status = await health()
        return {"api_version": "1.0", "profile": "local", "model_ready": status["ready"],
                "provider_status": status["provider_status"], "chat": True, "streaming": True,
                "cancellation": "close_upstream_socket", "offline_commands": True,
                "persistence": False, "memory_api": False, "remote_providers": False,
                "multi_tenant": False, "voice": False, "vision": False, "tools": False,
                "limits": {"payload_bytes": 65536, "messages": 20, "context_characters": 6000,
                           "output_characters": 12000, "chat_requests_per_minute": 60},
                "telemetry": brain.telemetry()}

    @app.get(PREFIX + "/models", response_model=ModelList, responses={503: {"model": ErrorResult}})
    async def models():
        return await anyio.to_thread.run_sync(inventory)

    @app.get(PREFIX + "/openapi.json", include_in_schema=False)
    async def openapi():
        return app.openapi()

    async def prepare(payload, request):
        session = brain.begin(payload, request.state.request_id)
        try:
            await anyio.to_thread.run_sync(lambda: brain.prepare(session, payload))
            return session
        except BaseException:
            brain.finish(session, "failed")
            raise

    @app.post(PREFIX + "/chat", response_model=ChatResult,
              responses={503: {"model": ErrorResult}, 504: {"model": ErrorResult}, 429: {"model": ErrorResult}})
    async def chat(payload: ChatRequest, request: Request):
        session = await prepare(payload, request)

        async def disconnect():
            while True:
                if await request.is_disconnected():
                    session.cancel()
                    return
                await asyncio.sleep(0.1)

        watcher = asyncio.create_task(disconnect())
        events = brain.events(session, payload)
        try:
            async for event, data in events:
                if event == "error":
                    detail = data["error"]
                    raise BrainError(detail["code"], 504 if detail["code"] == "timeout" else 503, detail["retryable"])
                if event == "done":
                    return data
        finally:
            await events.aclose()
            watcher.cancel()
            with suppress(asyncio.CancelledError):
                await watcher

    @app.post(PREFIX + "/chat/stream", response_class=StreamingResponse,
              responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}},
                                                 503: {"model": ErrorResult}})
    async def stream(payload: ChatRequest, request: Request):
        session = await prepare(payload, request)

        async def encode():
            events = brain.events(session, payload)
            try:
                async for event, data in events:
                    yield "event: " + event + "\ndata: " + json.dumps(data, ensure_ascii=False) + "\n\n"
            finally:
                await events.aclose()
                brain.finish(session, "cancelled")

        return StreamingResponse(encode(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    @app.post(PREFIX + "/chat/cancel", response_model=CancelResult, responses={404: {"model": ErrorResult}})
    async def cancel(payload: CancelRequest):
        return {"api_version": "1.0", **brain.cancel(payload.request_id)}

    return app
