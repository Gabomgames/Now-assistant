"""Bounded local generation lifecycle. No conversations or prompts are persisted."""
from collections import deque
from dataclasses import dataclass, field
from threading import Event, Lock
import time
from uuid import uuid4

import anyio

from now_engine.assistant import LocalAssistant, TOKEN_LIMITS, offline_reply, system_instruction
from .contracts import ChatResult, Metrics
from .provider import BrainError, ModelProvider


@dataclass
class Session:
    request_id: str
    conversation_id: str
    model_id: str | None
    used: list
    trimmed: bool
    started: float = field(default_factory=time.monotonic)
    cancelled: Event = field(default_factory=Event)
    stream: object = None
    first_token_ms: float | None = None

    def cancel(self):
        self.cancelled.set()
        if self.stream is not None:
            self.stream.close()


class Brain:
    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self._lock, self._rate = Lock(), deque()
        self._active = None
        self._counts = {"completed": 0, "truncated": 0, "cancelled": 0, "failed": 0}

    def begin(self, payload, request_id):
        with self._lock:
            now = time.monotonic()
            while self._rate and self._rate[0] <= now - 60:
                self._rate.popleft()
            if len(self._rate) >= 60:
                raise BrainError("quota_exceeded", 429)
            self._rate.append(now)
            if self._active is not None:
                raise BrainError("busy", 409)
            messages = [message.model_dump() for message in payload.messages]
            used = LocalAssistant.messages(messages[-1]["content"], messages[:-1])
            session = Session(request_id, payload.conversation_id or str(uuid4()), None,
                              used, len(used) < len(messages))
            self._active = session
            return session

    def prepare(self, session, payload):
        if payload.mode == "model":
            session.model_id = self.provider.select(payload.model_id)
            session.stream = self.provider.stream(session.model_id, [
                {"role": "system", "content": system_instruction(payload.options)}, *session.used,
            ], TOKEN_LIMITS[payload.options.reply_length])
            if session.cancelled.is_set():
                session.stream.close()
        elif offline_reply(session.used[-1]["content"], payload.options) is None:
            raise BrainError("offline_command_unknown", 422, False)

    def finish(self, session, status):
        session.cancel()
        with self._lock:
            if self._active is session:
                self._active = None
                self._counts[status] += 1

    def cancel(self, request_id):
        with self._lock:
            session = self._active
            if session is None or session.request_id != request_id:
                raise BrainError("request_not_found", 404, False)
            session.cancel()
        return {"request_id": request_id, "status": "cancelling"}

    def telemetry(self):
        with self._lock:
            return {"active_generations": int(self._active is not None), "max_concurrency": 1,
                    "counters": dict(self._counts), "scope": "process_only_no_content"}

    @staticmethod
    def result(session, text, reason, count=None, duration=None):
        return ChatResult(
            request_id=session.request_id, conversation_id=session.conversation_id,
            model_id=session.model_id, provider_id="ollama" if session.model_id else "offline",
            status={"stop": "completed", "length": "truncated", "cancelled": "cancelled"}[reason],
            reply=text, finish_reason=reason, context_messages=len(session.used), context_trimmed=session.trimmed,
            metrics=Metrics(elapsed_ms=round((time.monotonic() - session.started) * 1000, 3),
                            first_token_ms=session.first_token_ms, output_tokens=count,
                            tokens_per_second=round(count * 1e9 / duration, 3) if count is not None and duration else None),
        )

    async def events(self, session, payload):
        status, text = "cancelled", ""
        try:
            yield "state", {"api_version": "1.0", "request_id": session.request_id,
                            "conversation_id": session.conversation_id, "status": "generating",
                            "model_id": session.model_id}
            if payload.mode == "offline":
                text = offline_reply(session.used[-1]["content"], payload.options)
                yield "delta", {"request_id": session.request_id, "text": text}
                status = "completed"
                yield "done", self.result(session, text, "stop").model_dump()
                return
            while not session.cancelled.is_set():
                # Pull one bounded chunk only after downstream has consumed the last.
                chunk = await anyio.to_thread.run_sync(session.stream.read, abandon_on_cancel=True)
                if session.cancelled.is_set():
                    break
                if chunk.text:
                    if session.first_token_ms is None:
                        session.first_token_ms = round((time.monotonic() - session.started) * 1000, 3)
                    text += chunk.text
                    yield "delta", {"request_id": session.request_id, "text": chunk.text}
                if chunk.finish_reason:
                    if not text.strip():
                        raise BrainError("provider_error", 502)
                    result = self.result(session, text, chunk.finish_reason, chunk.output_tokens, chunk.eval_duration_ns)
                    status = result.status
                    yield "done", result.model_dump()
                    return
            status = "cancelled"
            yield "done", self.result(session, text, "cancelled").model_dump()
        except BrainError as error:
            if session.cancelled.is_set():
                status = "cancelled"
                yield "done", self.result(session, text, "cancelled").model_dump()
            else:
                status = "failed"
                yield "error", {"api_version": "1.0", "error": {"code": error.code,
                                "request_id": session.request_id, "retryable": error.retryable}}
        except Exception:
            status = "failed"
            raise
        finally:
            self.finish(session, status)
