"""Real bounded Ollama NDJSON transport; no HTTP proxy, remote URL or redirects."""
from dataclasses import dataclass
import http.client
import json
import os
import re
import socket
from threading import Event, Lock
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request

from now_engine.providers import local_open
from .contracts import ModelInfo

MODEL_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$")


class BrainError(Exception):
    def __init__(self, code, status=503, retryable=True):
        super().__init__(code)
        self.code, self.status, self.retryable = code, status, retryable


def valid_model(model):
    if not isinstance(model, str) or not MODEL_TAG.fullmatch(model) or ":cloud" in model.casefold() or "://" in model:
        raise BrainError("model_not_allowed", 422, False)
    return model


@dataclass(frozen=True)
class Chunk:
    text: str = ""
    finish_reason: str | None = None
    output_tokens: int | None = None
    eval_duration_ns: int | None = None


class ModelProvider(Protocol):
    def models(self) -> list[ModelInfo]: ...
    def select(self, model_id: str | None) -> str: ...
    def stream(self, model_id: str, messages: list[dict], max_tokens: int): ...


class OllamaStream:
    """One blocking read at a time. Closing shuts down the socket to interrupt I/O."""
    def __init__(self, endpoint, model, messages, max_tokens, timeout):
        self.endpoint, self.model = endpoint, model
        self.messages, self.max_tokens, self.timeout = messages, max_tokens, timeout
        self.cancelled = Event()
        self._lock = Lock()
        self._connection = self._response = self._socket = None
        self._started = time.monotonic()
        self._characters, self._finished = 0, False

    def close(self):
        self.cancelled.set()
        with self._lock:
            sock = self._socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        # The reading worker owns response.close(); do not race its buffered reader.

    def _open(self):
        parsed = urlsplit(self.endpoint)
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=min(5, self.timeout))
        self._connection = connection
        connection.connect()
        with self._lock:
            self._socket = connection.sock
        if self.cancelled.is_set():
            self.close()
            raise BrainError("interrupted", 409, False)
        remaining = self.timeout - (time.monotonic() - self._started)
        if remaining <= 0:
            raise BrainError("timeout", 504)
        connection.sock.settimeout(remaining)
        body = json.dumps({"model": self.model, "messages": self.messages, "stream": True,
                           "options": {"num_predict": self.max_tokens, "temperature": 0.6}}, ensure_ascii=False).encode()
        connection.request("POST", "/api/chat", body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        self._response = response
        if response.status == 404:
            raise BrainError("model_not_installed")
        if response.status != 200:
            raise BrainError("provider_error")

    def read(self):
        failed = True
        try:
            if self.cancelled.is_set():
                raise BrainError("interrupted", 409, False)
            if self._response is None:
                self._open()
            remaining = self.timeout - (time.monotonic() - self._started)
            if remaining <= 0:
                raise BrainError("timeout", 504)
            self._socket.settimeout(remaining)
            line = self._response.readline(65537)
            if not line or len(line) > 65536:
                raise BrainError("interrupted" if not line else "provider_error")
            payload = json.loads(line)
            if not isinstance(payload, dict) or payload.get("error"):
                raise BrainError("provider_error")
            text = (payload.get("message") or {}).get("content", "")
            if not isinstance(text, str):
                raise BrainError("provider_error")
            self._characters += len(text)
            if self._characters > 12000:
                raise BrainError("output_limit", 502, False)
            reason = None
            if payload.get("done") is True:
                reason = payload.get("done_reason")
                if reason not in {"stop", "length"} or not self._characters:
                    raise BrainError("provider_error")
                self._finished = True
            elif payload.get("done") is not False:
                raise BrainError("provider_error")
            count, duration = payload.get("eval_count"), payload.get("eval_duration")
            count = count if type(count) is int and count >= 0 else None
            duration = duration if type(duration) is int and duration > 0 else None
            failed = False
            return Chunk(text, reason, count, duration)
        except BrainError:
            raise
        except (TimeoutError, socket.timeout) as error:
            raise BrainError("timeout", 504) from error
        except (OSError, http.client.HTTPException) as error:
            raise BrainError("unavailable" if self._response is None else "interrupted") from error
        except (ValueError, TypeError, AttributeError) as error:
            raise BrainError("provider_error", 502) from error
        finally:
            if failed or self.cancelled.is_set() or self._finished:
                self.dispose()

    def dispose(self):
        if self._response is not None:
            self._response.close()
        if self._connection is not None:
            self._connection.close()


class OllamaProvider:
    def __init__(self, *, endpoint="http://127.0.0.1:11434", timeout=180):
        # Dependency injection for loopback HTTP integration tests, never a client option.
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port
                or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
            raise ValueError("Ollama must use an explicit loopback port")
        if not 1 <= timeout <= 900:
            raise ValueError("timeout must be between 1 and 900 seconds")
        self.endpoint, self.timeout = endpoint, timeout

    @staticmethod
    def default_model():
        return os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b").strip()

    def models(self):
        try:
            with local_open(self.endpoint + "/api/tags", timeout=5) as response:
                data = response.read(1048577)
            if len(data) > 1048576:
                raise BrainError("provider_error", 502)
            payload = json.loads(data)
            rows = payload.get("models")
            if not isinstance(rows, list) or len(rows) > 200:
                raise BrainError("provider_error", 502)
            models = []
            for row in rows:
                if not isinstance(row, dict):
                    raise BrainError("provider_error", 502)
                name = row.get("name") or row.get("model")
                try:
                    valid_model(name)
                except BrainError:
                    continue
                if row.get("remote_host") or row.get("remote_model"):
                    continue
                details = row.get("details") or {}
                def string(value):
                    return value[:256] if isinstance(value, str) else None
                size = row.get("size")
                models.append(ModelInfo(model_id=name, digest=string(row.get("digest")),
                                        size_bytes=size if type(size) is int and size >= 0 else None,
                                        parameter_size=string(details.get("parameter_size")),
                                        quantization=string(details.get("quantization_level"))))
            return models
        except BrainError:
            raise
        except (TimeoutError, socket.timeout) as error:
            raise BrainError("timeout", 504) from error
        except (HTTPError, URLError, OSError) as error:
            raise BrainError("unavailable") from error
        except (ValueError, TypeError, AttributeError) as error:
            raise BrainError("provider_error", 502) from error

    def select(self, model_id):
        model = valid_model(model_id if model_id is not None else self.default_model())
        if model not in {row.model_id for row in self.models()}:
            raise BrainError("model_not_installed")
        return model

    def stream(self, model_id, messages, max_tokens):
        return OllamaStream(self.endpoint, model_id, messages, max_tokens, self.timeout)
