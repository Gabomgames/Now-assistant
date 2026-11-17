"""Actual Qt + cohosted API + HTTP fixture. This is protocol testing, not inference."""
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

if os.name != "nt" and not os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLabel
from now_desktop.engine_client import EngineClient
from now_desktop.window import MainWindow
from now_desktop.dialogs import SettingsDialog
from now_desktop.sse import SSEDecoder
from now_desktop import client_config
from now_engine.desktop_api import create_app
from now_brain.provider import OllamaProvider
from tests.test_brain_api_v1 import BrainAPIV1Tests as FixtureOwner, serve

# Prevent unittest from rediscovering the imported fixture class as a second suite.
del FixtureOwner
import tests.test_brain_api_v1 as fixtures


class DesktopStreamingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        cls.application.setQuitOnLastWindowClosed(False)
        fixtures.BrainAPIV1Tests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        fixtures.BrainAPIV1Tests.tearDownClass()

    def wait(self, predicate, timeout=6):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.application.processEvents()
            if predicate():
                return
            time.sleep(0.005)
        self.fail("real Qt/API operation timed out")

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        owner = fixtures.BrainAPIV1Tests
        owner.recorded.clear()
        owner.upstream_closed.clear()
        self.provider = OllamaProvider(endpoint=f"http://127.0.0.1:{owner.ollama.server_port}", timeout=10)
        self.server = serve(create_app("t" * 32, "qt-instance", brain_provider=self.provider))
        self.url = self.server.__enter__()
        self.client = EngineClient(self.url, "t" * 32, "qt-instance")
        self.window = MainWindow(self.client, Path(self.directory.name))
        self.window.show()
        self.client.start()
        self.wait(lambda: self.window._ready and bool(self.client.models))

    def tearDown(self):
        self.window.close()
        self.application.processEvents()
        self.server.__exit__(None, None, None)
        self.directory.cleanup()

    def configure(self, model="fixture:second", protocol="v1", length="detailed"):
        errors = []
        def apply():
            try:
                dialog = QApplication.activeModalWidget()
                self.assertIsInstance(dialog, SettingsDialog)
                dialog.model.setCurrentIndex(dialog.model.findData(model))
                dialog.protocol.setCurrentIndex(dialog.protocol.findData(protocol))
                dialog.fields["reply_length"].setCurrentIndex(dialog.fields["reply_length"].findData(length))
                dialog.accept()
            except Exception as error:
                errors.append(error)
                if QApplication.activeModalWidget():
                    QApplication.activeModalWidget().reject()
        QTimer.singleShot(10, apply)
        self.window._settings()
        if errors:
            raise errors[0]

    def test_model_discovery_selection_and_real_progress_before_completion(self):
        self.configure()
        configuration = json.loads((Path(self.directory.name) / "client.json").read_text())
        self.assertEqual(configuration, {"protocol": "v1", "model": "fixture:second"})
        ticks = []
        heartbeat = QTimer()
        heartbeat.setInterval(10)
        heartbeat.timeout.connect(lambda: ticks.append(True))
        heartbeat.start()
        self.window.submit_text("slow")
        self.wait(lambda: self.window._stream_body is not None and "Olá" in self.window._stream_body.text())
        self.assertIsNotNone(self.window._pending)
        self.assertEqual(len(self.window.controller.current.messages), 1)
        self.assertTrue(self.window.controller.current.temporary)
        self.assertFalse(list(Path(self.directory.name).rglob("*.sqlite3")))
        self.wait(lambda: len(ticks) > 6)
        self.assertIn("primeiro texto", self.window.generation_status.text())
        request = fixtures.BrainAPIV1Tests.recorded[-1]
        self.assertEqual(request["model"], "fixture:second")
        self.assertEqual(request["options"]["num_predict"], 1024)
        self.assertIn("português brasileiro natural", request["messages"][0]["content"])
        self.wait(lambda: self.window._pending is None)
        heartbeat.stop()
        self.assertEqual(self.window.controller.current.messages[-1].provider, "local")
        self.assertIn("tokens/s", self.window.generation_status.text())

    def test_cancel_closes_actual_upstream_and_drops_partial_history(self):
        self.configure()
        self.window.submit_text("slow")
        self.wait(lambda: bool(self.window._stream_text))
        self.window._cancel_pending()
        self.wait(fixtures.BrainAPIV1Tests.upstream_closed.is_set)
        self.assertEqual(len(self.window.controller.current.messages), 1)
        self.assertEqual(self.window.controller.current.messages[0].status, "cancelled")
        self.assertEqual(self.window.controller.current.context(), [])
        self.wait(lambda: self.client._active is None)

    def test_broken_stream_is_error_not_success_and_remains_responsive(self):
        self.configure()
        self.window.submit_text("malformed")
        self.wait(lambda: self.window._pending is None)
        self.assertEqual(self.window._last_error, "STREAM_INTERRUPTED")
        self.assertEqual(len(self.window.controller.current.messages), 1)
        self.assertEqual(self.window.controller.current.messages[0].status, "failed")
        self.assertTrue(self.window.composer.isEnabled())

    def test_rollback_uses_v2_on_same_engine_and_keeps_memory_schema_unchanged(self):
        self.configure(protocol="v2")
        self.assertEqual(self.client.protocol, "v2")
        self.window.submit_text("horas")
        self.wait(lambda: self.window._pending is None)
        self.assertIn("Agora são", self.window.controller.current.messages[-1].content)
        self.assertEqual(fixtures.BrainAPIV1Tests.recorded, [])
        self.assertEqual(set(self.window.controller.settings), {"language", "persona", "humor", "reply_length", "display_name"})

    def test_installed_models_require_explicit_choice_before_open_chat(self):
        self.window.submit_text("Explain recursion")
        self.wait(lambda: self.window._pending is None)
        self.assertEqual(self.window._last_error, "MODEL_NOT_SELECTED")
        self.assertEqual(fixtures.BrainAPIV1Tests.recorded, [])


class DecoderAndConfigTests(unittest.TestCase):
    def test_fragmented_unicode_crlf_and_multiple_events(self):
        raw = 'event: delta\r\ndata: {"text":"Olá 😃"}\r\n\r\nevent: done\ndata: {"status":"completed"}\n\n'.encode()
        decoder, events = SSEDecoder(), []
        for byte in raw:
            events.extend(decoder.feed(bytes([byte])))
        self.assertEqual(events, [("delta", {"text": "Olá 😃"}), ("done", {"status": "completed"})])
        with self.assertRaises(ValueError):
            SSEDecoder().feed(b"x" * 65537)

    def test_configuration_is_only_technical_and_does_not_create_a_vault(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(client_config.load(directory), {"protocol": "v1", "model": None})
            client_config.save(directory, "v1", "qwen2.5:1.5b")
            self.assertEqual(client_config.load(directory)["model"], "qwen2.5:1.5b")
            (Path(directory) / "client.json").write_text('{"display_name":"private"}')
            self.assertIsNone(client_config.load(directory)["model"])
            self.assertFalse(list(Path(directory).rglob("*.sqlite3")))

    def test_readable_report_escapes_model_markup_and_does_not_choose_a_winner(self):
        from tools.validate_brain_api import readable_report
        report = {"status": "COMPLETED_REVIEW_REQUIRED", "quality": "NOT_SCORED", "models": [{
            "model_id": "fixture", "status": "COMPLETED_REVIEW_REQUIRED", "generated": 1,
            "cases": [{"id": "fixture", "status": "GENERATED_REVIEW_REQUIRED", "answer": "<script>bad()</script>"}]}]}
        page = readable_report(report)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("nenhum vencedor", page)
