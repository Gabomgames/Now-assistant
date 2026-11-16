"""Asynchronous native HTTP client. UI code knows the API contract, not model implementations."""
import json
from urllib.parse import urlsplit
from uuid import uuid4

from PySide6.QtCore import QByteArray, QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class EngineClient(QObject):
    ready = Signal()
    failed = Signal(str)
    capabilities_received = Signal(object)
    chat_finished = Signal(str, object, object)

    def __init__(self, url, token, instance, parent=None):
        super().__init__(parent)
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username or parsed.path not in ("", "/"):
            raise ValueError("the desktop client accepts only its owned loopback Engine")
        self.url, self._token, self._instance = url.rstrip("/"), token, instance
        self._network = QNetworkAccessManager(self)
        self._active = None
        self._closed = False
        self._attempts = 0

    def _request(self, path):
        request = QNetworkRequest(QUrl(self.url + path))
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("ascii"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(95000)
        return request

    def start(self):
        if self._closed:
            return
        self._attempts += 1
        request = self._request("/v2/health")
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
        reply = self._network.get(self._request("/v2/capabilities"))
        def finished():
            if self._closed:
                reply.deleteLater()
                return
            try:
                data = json.loads(bytes(reply.readAll()))
                if not self._closed and reply.error() == QNetworkReply.NetworkError.NoError:
                    self.capabilities_received.emit(data)
            except (ValueError, TypeError):
                pass
            reply.deleteLater()
        reply.finished.connect(finished)

    def chat(self, messages, settings):
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

    def cancel(self):
        if self._active is not None:
            self._active.abort()

    def close(self):
        self._closed = True
        for reply in self._network.findChildren(QNetworkReply):
            if reply.isRunning():
                reply.abort()
