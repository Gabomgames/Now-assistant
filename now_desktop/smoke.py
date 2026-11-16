"""Exercise the actual Qt window and its owned HTTP Engine, without model doubles."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import tempfile
import time


def capture(output_directory):
    import sys
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication
    from .branding import logo_path
    from .engine_client import EngineClient
    from .runtime import EngineProcess
    from .theme import apply_theme
    from .window import MainWindow
    from .version import VERSION

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=False)
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    apply_theme(application)
    runtime = EngineProcess()
    records = []
    window = None

    def wait(predicate, timeout=20):
        loop, timer, expired = QEventLoop(), QTimer(), QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: loop.quit() if predicate() else None)
        expired.setSingleShot(True)
        expired.timeout.connect(loop.quit)
        timer.start()
        expired.start(int(timeout * 1000))
        loop.exec()
        timer.stop()
        expired.stop()
        if not predicate():
            raise RuntimeError("real desktop operation timed out")

    def screenshot(name):
        settled = QTimer()
        settled.setSingleShot(True)
        settled.start(60)
        wait(lambda: not settled.isActive())
        if not window.grab().save(str(output_directory / name), "PNG"):
            raise RuntimeError("actual window capture failed")

    def resident_kib(pid):
        path = Path(f"/proc/{pid}/status")
        if path.exists():
            return int(next(row.split()[1] for row in path.read_text().splitlines() if row.startswith("VmRSS:")))
        return None

    with tempfile.TemporaryDirectory(prefix="now-desktop-smoke-") as temporary:
        try:
            runtime.start()
            client = EngineClient(runtime.url, runtime.token, runtime.instance)
            window = MainWindow(client, Path(temporary))
            window.show()
            client.start()
            wait(lambda: window._ready)
            screenshot("NOW-Assistant-welcome.png")
            for language, prompts in (("pt-BR", ("oi", "horas", "data")), ("en-US", ("hello", "time", "date"))):
                window.controller.settings["language"] = language
                window.new_chat()
                window._translate()
                for prompt in prompts:
                    started = time.monotonic()
                    window.submit_text(prompt)
                    wait(lambda: window._pending is None)
                    answer = window.controller.current.messages[-1]
                    if answer.role != "assistant" or answer.provider != "offline" or answer.status != "complete":
                        raise RuntimeError("actual offline chat check failed")
                    records.append({"language": language, "input": prompt, "output": answer.content,
                                    "provider": answer.provider, "latency_ms": round((time.monotonic() - started) * 1000, 1)})
                screenshot(f"NOW-Assistant-{language}.png")
            if list(Path(temporary).rglob("*.sqlite3")):
                raise RuntimeError("temporary GUI session unexpectedly created a private vault")
            report = {
                "checked_at_utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
                "system": platform.system(), "version": VERSION, "frozen_executable": bool(getattr(sys, "frozen", False)),
                "python_version": platform.python_version(), "python_bits": 64 if sys.maxsize > 2**32 else 32,
                "qt_platform": application.platformName(), "official_logo_loaded": logo_path() is not None,
                "real_gui_and_http_engine": True, "mocked_responses": False, "offline_commands": records,
                "temporary_session_created_database": False, "gemini_sdk_present": importlib.util.find_spec("google") is not None,
                "model_inference_executed": False, "audio_executed": False,
                "gui_resident_kib": resident_kib(os.getpid()), "engine_resident_kib": resident_kib(runtime.process.pid),
                "metrics_scope": "Linux current RSS during offline GUI smoke; not peak KDF/model RAM or target Windows/game performance",
            }
            (output_directory / "REAL-GUI-VALIDACAO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return report
        finally:
            if window is not None:
                window.close()
                application.processEvents()
            runtime.stop()
