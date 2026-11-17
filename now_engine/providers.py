"""Local inference transport, independent of GUI, history and preference storage."""
from dataclasses import dataclass
import json
import os
from typing import Protocol
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_open(request, *, timeout):
    # Inference must stay on loopback even when the machine has an HTTP proxy.
    return build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout)


class LocalModelUnavailable(Exception):
    pass


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    finish_reason: str


class ModelProvider(Protocol):
    def installed_model(self) -> str: ...
    def generate(self, messages: list[dict], *, max_tokens: int) -> Generation: ...


class OllamaProvider:
    """Fixed loopback endpoint; remote model entries and redirects are rejected."""
    endpoint = "http://127.0.0.1:11434"

    def __init__(self, opener=local_open):
        self._open = opener

    def _json(self, request, timeout):
        with self._open(request, timeout=timeout) as response:
            # Do not accept a redirect to a remote service as local inference.
            if not response.geturl().startswith(self.endpoint + "/"):
                raise ValueError("unexpected inference destination")
            return json.load(response)

    def installed_model(self):
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b").strip()
        if not model or ":cloud" in model.casefold() or "://" in model:
            raise LocalModelUnavailable("configure an installed local model tag")
        try:
            inventory = self._json(self.endpoint + "/api/tags", 5)
            matches = [row for row in inventory.get("models", [])
                       if row.get("name") == model or row.get("model") == model]
            if not matches or any(row.get("remote_host") or row.get("remote_model") for row in matches):
                raise ValueError("model is absent or remote")
        except (URLError, OSError, ValueError, TypeError, AttributeError) as error:
            raise LocalModelUnavailable("the local Ollama model is unavailable") from error
        return model

    def generate(self, messages, *, max_tokens):
        model = self.installed_model()
        try:
            request = Request(self.endpoint + "/api/chat", data=json.dumps({
                "model": model, "messages": messages, "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.6},
            }, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"})
            payload = self._json(request, 90)
            answer = (payload.get("message") or {}).get("content")
            reason = payload.get("done_reason")
            if (not isinstance(answer, str) or not answer.strip() or len(answer) > 12000
                    or payload.get("done") is not True or reason not in {"stop", "length"}):
                raise ValueError("invalid or incomplete local response")
        except (URLError, OSError, ValueError, TypeError, AttributeError) as error:
            raise LocalModelUnavailable("the local Ollama model is unavailable or returned an invalid reply") from error
        return Generation(answer.strip(), model, reason)
