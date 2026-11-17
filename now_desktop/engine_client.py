"""Asynchronous native HTTP client. UI code knows the API contract, not model implementations."""
import json
import time

from .sse import SSEDecoder
from urllib.parse import urlsplit
from uuid import uuid4

from PySide6.QtCore import QByteArray, QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class EngineClient(QObject):
    ready = Signal()
    failed = Signal(str)
    capabilities_received = Signal(object)
    chat_finished = Signal(str, object, object)
    chat_delta = Signal(str, str, object)

    def __init__(self, url, token, instance, parent=None, *, protocol="v1", force_protocol=False):
        super().__init__(parent)
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValueError("the desktop client accepts only its owned loopback Engine")
        self.protocol, self.force_protocol = protocol, force_protocol
        self.selected_model, self.models, self.inventory_error = None, [], None
        self.inventory_loading = False
        self._legacy_capabilities = {}
        self._turn = None
        self.url, self._token, self._instance = url.rstrip("/"), token, instance
        self._network = QNetworkAccessManager(self)
        self._active = None
        self._closed = False
        self._attempts = 0

    def _request(self, path):
        request = QNetworkRequest(QUrl(self.url + path))
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("ascii"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(315000)
        return request

    def start(self):
        if self._closed:
            return
        self._attempts += 1
        request = self._request("/v2/health" if self.protocol == "v2" else "/api/now/v1/health?check_provider=false")
        request.setTransferTimeout(1200)
        reply = self._network.get(request)

        def finished():
            if self._closed:
                reply.deleteLater()
                return
            try:
                data = json.loads(bytes(reply.readAll()))
                valid = reply.error() == QNetworkReply.NetworkError.NoError and data.get("instance_id") == self._instance
            except (ValueError, TypeError):
                valid = False
            reply.deleteLater()
            if valid:
                self.ready.emit()
                self.refresh_capabilities()
            elif self._attempts < 30:
                QTimer.singleShot(300, self.start)
            else:
                self.failed.emit("ENGINE_UNAVAILABLE")
        reply.finished.connect(finished)

    def reconnect(self):
        self._attempts = 0
        self.start()

    def refresh_capabilities(self):
        if self._closed:
            return
        if self.protocol == "v1":
            self.refresh_models()
            return
        reply = self._network.get(self._request("/v2/capabilities"))
        def finished():
            if self._closed:
                reply.deleteLater()
                return
            try:
                data = json.loads(bytes(reply.readAll()))
                if not self._closed and reply.error() == QNetworkReply.NetworkError.NoError:
                    self._legacy_capabilities = data
                    self.capabilities_received.emit(data)
            except (ValueError, TypeError):
                pass
            reply.deleteLater()
        reply.finished.connect(finished)

    def chat(self, messages, settings, conversation_id=None):
        if self.protocol == "v1":
            return self._stream_chat(messages, settings, conversation_id)
        if self._closed or self._active is not None:
            raise RuntimeError("the client is closed or already has an active request")
        identifier = str(uuid4())
        payload = QByteArray(json.dumps({"messages": messages, "settings": settings}, ensure_ascii=False).encode("utf-8"))
        reply = self._network.post(self._request("/v2/chat"), payload)
        self._active = reply

        def finished():
            if self._active is reply:
                self._active = None
            if self._closed:
                reply.deleteLater()
                return
            error = None
            data = None
            try:
                data = json.loads(bytes(reply.readAll()))
            except (ValueError, TypeError):
                error = "ENGINE_UNAVAILABLE"
            if reply.error() == QNetworkReply.NetworkError.OperationCanceledError:
                error = "CANCELLED"
            elif reply.error() != QNetworkReply.NetworkError.NoError:
                detail = data.get("detail", data) if isinstance(data, dict) else {}
                error = detail.get("error", "ENGINE_UNAVAILABLE") if isinstance(detail, dict) else "INVALID_MESSAGE"
            if not self._closed:
                self.chat_finished.emit(identifier, None if error else data, error)
            reply.deleteLater()
        reply.finished.connect(finished)
        return identifier

    @staticmethod
    def _error_code(data, default):
        if not isinstance(data, dict):
            return default
        detail = data.get("error", {})
        code = detail.get("code", default) if isinstance(detail, dict) else detail
        return code if isinstance(code, str) else default

    def refresh_models(self):
        if self._closed or self.inventory_loading:
            return
        self.inventory_loading = True
        self.capabilities_received.emit({"model_installed": bool(self.models), "models": self.models})
        reply = self._network.get(self._request("/api/now/v1/models"))
        reply.setReadBufferSize(1048576)
        def finished():
            if self._closed:
                reply.deleteLater()
                return
            self.inventory_loading = False
            self.models, self.inventory_error = [], None
            try:
                data = json.loads(bytes(reply.readAll()))
                if reply.error() != QNetworkReply.NetworkError.NoError:
                    self.inventory_error = self._error_code(data, "unavailable")
                else:
                    self.models = data["models"]
            except (ValueError, KeyError, TypeError):
                self.inventory_error = "unavailable"
            self.capabilities_received.emit({"model_installed": bool(self.models) if self.protocol == "v1" else bool(self._legacy_capabilities.get("model_installed")), "models": self.models,
                                             "model": self.selected_model, "protocol": self.protocol,
                                             "inventory_error": self.inventory_error})
            reply.deleteLater()
        reply.finished.connect(finished)

    def _stream_chat(self, messages, settings, conversation_id=None):
        if self._closed or self._active is not None:
            raise RuntimeError("the client is closed or busy")
        # Useful deterministic commands survive missing models. Once a model is
        # explicitly selected, greetings and open-ended chat always use inference.
        from now_engine.assistant import offline_reply
        from types import SimpleNamespace
        deterministic = offline_reply(messages[-1]["content"], SimpleNamespace(**settings))
        command = messages[-1]["content"].strip().casefold().rstrip("!?.")
        mode = "offline" if deterministic is not None and (self.selected_model is None or command in {
            "horas", "time", "data", "date", "ajuda", "help", "comandos", "commands", "what time is it", "que horas sao",
        }) else "model"
        identifier = str(uuid4())
        if mode == "model" and self.selected_model is None and self.models:
            QTimer.singleShot(0, lambda: self.chat_finished.emit(identifier, None, "MODEL_UNAVAILABLE"))
            return identifier
        payload = {"messages": messages, "options": settings, "mode": mode}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        if self.selected_model is not None:
            payload["model_id"] = self.selected_model
        request = self._request("/api/now/v1/chat/stream")
        request.setRawHeader(b"Accept", b"text/event-stream")
        reply = self._network.post(request, QByteArray(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
        reply.setReadBufferSize(131072)
        turn = {"reply": reply, "id": identifier, "decoder": SSEDecoder(), "server_id": None,
                "text": "", "result": None, "error": None, "cancelled": False,
                "started": time.monotonic(), "first_token_ms": None}
        self._turn, self._active = turn, reply

        def consume():
            if turn["cancelled"] or self._closed:
                return
            status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if status and int(status) != 200:
                return  # Keep JSON error for finished().
            try:
                for event, data in turn["decoder"].feed(bytes(reply.readAll())):
                    if turn["result"] is not None or turn["error"] is not None:
                        raise ValueError("data after terminal event")
                    if event == "state":
                        turn["server_id"] = data["request_id"]
                    elif event == "delta":
                        piece = data["text"]
                        if not isinstance(piece, str) or len(turn["text"]) + len(piece) > 12000:
                            raise ValueError("invalid text delta")
                        turn["text"] += piece
                        if piece and turn["first_token_ms"] is None:
                            turn["first_token_ms"] = (time.monotonic() - turn["started"]) * 1000
                        self.chat_delta.emit(identifier, piece, {"first_token_ms": turn["first_token_ms"],
                                              "elapsed_ms": (time.monotonic() - turn["started"]) * 1000})
                    elif event == "done":
                        if data["status"] == "cancelled":
                            turn["error"] = "CANCELLED"
                        elif (data["request_id"] != turn["server_id"] or data["reply"] != turn["text"] or data["provider_id"] not in {"ollama", "offline"}
                              or data["status"] not in {"completed", "truncated"}):
                            raise ValueError("invalid terminal reply")
                        else:
                            turn["result"] = {**data, "provider": "local" if data["provider_id"] == "ollama" else "offline",
                                              "output_truncated": data["status"] == "truncated"}
                    elif event == "error":
                        turn["error"] = data["error"]["code"]
                    else:
                        raise ValueError("unsupported SSE event")
            except (ValueError, KeyError, TypeError, UnicodeError):
                turn["error"] = "STREAM_INTERRUPTED"
                reply.abort()
        reply.readyRead.connect(consume)

        def finished():
            consume()
            if self._active is reply:
                self._active, self._turn = None, None
            if self._closed:
                reply.deleteLater()
                return
            error = turn["error"]
            if turn["cancelled"]:
                error = "CANCELLED"
            elif reply.error() != QNetworkReply.NetworkError.NoError and not error:
                try:
                    data = json.loads(bytes(reply.readAll()))
                    error = self._error_code(data, "ENGINE_UNAVAILABLE")
                except (ValueError, AttributeError):
                    error = "STREAM_INTERRUPTED"
            elif turn["result"] is None and not error:
                error = "STREAM_INTERRUPTED"
            error = {"unavailable": "MODEL_UNAVAILABLE", "model_not_installed": "MODEL_UNAVAILABLE",
                     "timeout": "MODEL_TIMEOUT", "interrupted": "STREAM_INTERRUPTED", "provider_error": "STREAM_INTERRUPTED",
                     "output_limit": "STREAM_INTERRUPTED", "busy": "ENGINE_BUSY", "quota_exceeded": "RATE_LIMITED",
                     "invalid_request": "INVALID_MESSAGE", "unauthorized": "UNAUTHORIZED"}.get(error, error)
            self.chat_finished.emit(identifier, None if error else turn["result"], error)
            reply.deleteLater()
        reply.finished.connect(finished)
        return identifier

    def cancel(self):
        turn = self._turn
        if turn is not None:
            turn["cancelled"] = True
            if turn["server_id"]:
                request = self._request("/api/now/v1/chat/cancel")
                control = self._network.post(request, QByteArray(json.dumps({"request_id": turn["server_id"]}).encode()))
                control.finished.connect(control.deleteLater)
            self._turn = None
        active, self._active = self._active, None
        if active is not None:
            active.abort()  # Disconnect also interrupts the upstream socket.

    def close(self):
        self.cancel()
        self._closed = True
        for reply in self._network.findChildren(QNetworkReply):
            if reply.isRunning():
                reply.abort()
