"""Own a private loopback Engine child process; credentials never appear in argv or files."""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile


class EngineProcess:
    def __init__(self, model=None):
        self.token = secrets.token_urlsafe(32)
        self.instance = secrets.token_urlsafe(24)
        self.process = None
        self._logs = None
        self._stream = None
        self.url = None
        self.model = model

    def start(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self._logs = tempfile.TemporaryDirectory(prefix="now-engine-")
        self._stream = (Path(self._logs.name) / "engine.log").open("w", encoding="utf-8")
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--engine-child", "--port", str(port)]
        else:
            command = [sys.executable, "-m", "now_engine.desktop_api", "--port", str(port)]
        environment = {**os.environ, "NOW_DESKTOP_TOKEN": self.token, "NOW_DESKTOP_INSTANCE": self.instance,
                       "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}
        if self.model is not None:
            environment["OLLAMA_MODEL"] = self.model
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        self.process = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], env=environment,
                                        stdin=subprocess.DEVNULL, stdout=self._stream, stderr=self._stream, **options)
        return self.url

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=4)
        if self._stream is not None:
            self._stream.close()
        if self._logs is not None:
            self._logs.cleanup()
        self.process = None
