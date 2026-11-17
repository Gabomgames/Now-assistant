"""Real Qt result rendering with synthetic API fixtures; no inference claim."""
import os
from pathlib import Path
import tempfile
import unittest

if os.name != "nt" and not os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from now_desktop.engine_client import EngineClient
from now_desktop.window import MainWindow
from now_desktop.i18n import text


class BrainResultGUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        cls.application.setQuitOnLastWindowClosed(False)

    def test_truncation_is_visible_in_both_languages_and_text_is_retained(self):
        for language in ("pt-BR", "en-US"):
            with tempfile.TemporaryDirectory() as directory:
                client = EngineClient("http://127.0.0.1:1", "x" * 32, "fixture-instance")
                window = MainWindow(client, Path(directory))
                try:
                    window.controller.settings["language"] = language
                    conversation = window.controller.add_user("Synthetic UI test request")
                    window._pending = ("fixture-request", conversation.id)
                    window._chat_finished("fixture-request", {
                        "reply": "Synthetic partial text", "provider": "local", "output_truncated": True,
                    }, None)
                    self.assertEqual(window.error_text.text(), text("output_truncated", language))
                    self.assertFalse(window.banner.isHidden())
                    self.assertEqual(window.controller.current.messages[-1].content, "Synthetic partial text")
                    self.assertFalse(list(Path(directory).rglob("*.sqlite3")))
                finally:
                    window.close()
                    self.application.processEvents()
