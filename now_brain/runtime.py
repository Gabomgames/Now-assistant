"""Owned local API process for validators/clients. No Qt or user vault dependency."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request

from now_engine.processes import stop_owned_process
from now_engine.providers import local_open


class BrainProcess:
    def __init__(self, *, timeout=180):
        self.token, self.instance = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        self.timeout, self.process = timeout, None
        self.url = self._logs = self._stream = None

    def start(self):
        if self.process is not None:
            raise RuntimeError("process already started")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self._logs = tempfile.TemporaryDirectory(prefix="now-brain-")
        self._stream = (Path(self._logs.name) / "api.log").open("w", encoding="utf-8")
        environment = {**os.environ, "NOW_BRAIN_TOKEN": self.token, "NOW_BRAIN_INSTANCE": self.instance,
                       "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        self.process = subprocess.Popen([sys.executable, "-m", "now_brain", "--port", str(port),
                                         "--timeout", str(self.timeout)],
                                        cwd=Path(__file__).resolve().parents[1], env=environment,
                                        stdin=subprocess.DEVNULL, stdout=self._stream, stderr=self._stream, **options)
        # The fresh process token authenticates startup without requiring Ollama readiness.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.stop()
                raise RuntimeError("Brain exited before local API readiness")
            try:
                request = Request(self.url + "/api/now/v1/openapi.json", headers={"Authorization": "Bearer " + self.token})
                with local_open(request, timeout=1) as response:
                    if json.load(response).get("info", {}).get("title") == "NOW Brain local API":
                        return self.url
            except (URLError, OSError):
                time.sleep(0.05)
        self.stop()
        raise RuntimeError("Brain API startup timed out")

    def stop(self):
        stop_owned_process(self.process)
        if self._stream is not None:
            self._stream.close()
        if self._logs is not None:
            for attempt in range(20):
                try:
                    self._logs.cleanup()
                    break
                except PermissionError as error:
                    if os.name != "nt" or getattr(error, "winerror", None) != 32 or attempt == 19:
                        raise
                    time.sleep(0.05)
        self.process = None
