"""Actual Qt widgets, actual authenticated HTTP Engine and actual encrypted SQLite.

Synthetic input data is confined to temporary directories; no model responses are mocked.
"""
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

if os.name != "nt" and not os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "now-qt-test-cache"))

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import (QApplication, QDialogButtonBox, QFileDialog, QInputDialog,
                                  QLabel, QLineEdit, QMessageBox, QPushButton)
    from PySide6.QtTest import QTest
    from now_desktop.dialogs import SettingsDialog, VaultDialog
    from now_desktop.engine_client import EngineClient
    from now_desktop.theme import apply_theme
    from now_desktop.window import MainWindow
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from tests.test_desktop_api import start_runtime

PASSWORD = "desktop-test-only-passphrase-2026"


@unittest.skipUnless(QT_AVAILABLE, "install requirements-desktop.txt to run actual GUI tests")
class DesktopGUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QTest operates the real Qt file picker. Native Windows shell dialogs
        # require separate manual accessibility/usability validation.
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)
        cls.application = QApplication.instance() or QApplication([])
        cls.application.setQuitOnLastWindowClosed(False)
        apply_theme(cls.application)
        cls.runtime = start_runtime()

    @classmethod
    def tearDownClass(cls):
        cls.runtime.stop()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self._new_window()

    def tearDown(self):
        self.window.close()
        self.application.processEvents()
        self.temporary.cleanup()

    def _new_window(self):
        self.client = EngineClient(self.runtime.url, self.runtime.token, self.runtime.instance)
        self.window = MainWindow(self.client, self.directory)
        self.window.show()
        self.client.start()
        self.wait(lambda: self.window._ready)

    def wait(self, predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.application.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        self.fail("actual GUI operation timed out")

    def send(self, message):
        self.window.composer.setPlainText(message)
        QTest.keyClick(self.window.composer, Qt.Key.Key_Return)
        self.wait(lambda: self.window._pending is None and not self.window._jobs)

    def dialog(self, action, handler):
        errors, handled = [], []
        deadline = time.monotonic() + 8
        timer = QTimer()
        timer.setInterval(15)
        def tick():
            widget = QApplication.activeModalWidget() or QApplication.activePopupWidget()
            if widget is None:
                return
            try:
                if time.monotonic() > deadline:
                    raise AssertionError("expected dialog did not appear")
                if handler(widget):
                    handled.append(True)
                    timer.stop()
            except Exception as error:
                errors.append(error)
                timer.stop()
                widget.reject() if hasattr(widget, "reject") else widget.close()
        timer.timeout.connect(tick)
        timer.start()
        try:
            action()
        finally:
            timer.stop()
        if errors:
            raise errors[0]
        self.assertTrue(handled, "dialog handler was not executed")

    def fill_vault(self, widget, password=PASSWORD):
        if not isinstance(widget, VaultDialog):
            return False
        widget.password.setText(password)
        if widget.creating:
            widget.confirm.setText(password)
        if widget.requires_consent:
            widget.consent.setChecked(True)
        button = widget.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.assertTrue(button.isEnabled())
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        return True

    def unlock_or_create(self, password=PASSWORD):
        self.dialog(self.window._history_action, lambda widget: self.fill_vault(widget, password))
        self.wait(lambda: not self.window._blocking_jobs)

    def confirm(self, widget):
        if isinstance(widget, QMessageBox):
            QTest.mouseClick(widget.button(QMessageBox.StandardButton.Yes), Qt.MouseButton.LeftButton)
            return True
        return False

    def test_actual_text_chat_and_temporary_default(self):
        self.assertFalse((self.directory / "history/history.sqlite3").exists())
        self.send("horas")
        messages = self.window.controller.current.messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[-1].provider, "offline")
        self.assertIn("Agora são", messages[-1].content)
        self.assertTrue(self.window.controller.current.temporary)
        self.assertFalse((self.directory / "history/history.sqlite3").exists())

    def test_history_consent_save_search_rename_export_lock_reopen_and_delete(self):
        self.send("horas")
        temporary_id = self.window.controller.current.id
        self.unlock_or_create()
        self.assertTrue(self.window._unlocked)
        self.assertEqual(self.window._summaries, [])  # temporary chat was not retroactively saved
        self.send("data")
        saved_id = self.window.controller.current.id
        self.assertNotEqual(saved_id, temporary_id)
        self.assertFalse(self.window.controller.current.temporary)
        marker = "PRIVATE HISTORY TITLE 937226"
        def rename(widget):
            if isinstance(widget, QInputDialog):
                widget.setTextValue(marker)
                QTest.mouseClick(widget.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
                return True
            return False
        self.dialog(self.window.rename_current, rename)
        self.wait(lambda: not self.window._jobs and self.window.controller.current.title == marker)
        self.window.search.setText("Hoje é")
        self.wait(lambda: self.window.conversations.count() == 1 and self.window._summaries and self.window._summaries[0].get("search_match"))
        raw = (self.directory / "history/history.sqlite3").read_bytes()
        self.assertNotIn(marker.encode(), raw)
        self.assertNotIn(PASSWORD.encode(), raw)
        output = self.directory / "user-requested-export.json"
        def export(widget):
            if isinstance(widget, QMessageBox):
                self.confirm(widget)
                return False
            if isinstance(widget, QFileDialog):
                widget.setDirectory(str(output.parent))
                filename = widget.findChild(QLineEdit, "fileNameEdit")
                self.assertIsNotNone(filename)
                filename.setText(output.name)
                # Qt expands Windows 8.3 aliases such as RUNNER~1. Compare the
                # resolved destination, keeping the filename assertion intact.
                self.assertEqual([Path(path).resolve() for path in widget.selectedFiles()], [output.resolve()])
                button = widget.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save)
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                return True
            return False
        self.dialog(self.window.export_current, export)
        self.wait(lambda: output.exists() and not self.window._jobs)
        self.assertEqual(json.loads(output.read_text())["conversation"]["id"], saved_id)
        self.window.lock_history()
        self.wait(lambda: not self.window._jobs)
        self.assertFalse(self.window._unlocked)
        self.assertNotIn(saved_id, self.window.controller.cache)
        self.assertEqual(self.window.search.text(), "")
        self.window.close()
        self.application.processEvents()
        self._new_window()
        self.assertFalse(self.window._unlocked)
        self.unlock_or_create("incorrect-test-passphrase-2026")
        self.assertFalse(self.window._unlocked)
        self.assertEqual(self.window._last_error, "WRONG_PASSWORD")
        self.unlock_or_create()
        self.assertTrue(self.window._unlocked)
        item = next(self.window.conversations.item(index) for index in range(self.window.conversations.count())
                    if self.window.conversations.item(index).data(Qt.ItemDataRole.UserRole) == saved_id)
        self.window.conversations.setCurrentItem(item)
        self.wait(lambda: self.window.controller.current.id == saved_id and not self.window._jobs)
        self.assertEqual(self.window.controller.current.title, marker)
        self.assertEqual(len(self.window.controller.current.messages), 2)
        self.dialog(self.window.delete_current, self.confirm)
        self.wait(lambda: not self.window._jobs)
        self.assertNotIn(saved_id, {row["id"] for row in self.window._summaries})

    def test_session_preferences_switch_the_actual_gui_and_engine_language(self):
        def configure(widget):
            if isinstance(widget, SettingsDialog):
                widget.fields["language"].setCurrentIndex(widget.fields["language"].findData("en-US"))
                widget.display_name.setText("Demo")
                buttons = widget.findChild(QDialogButtonBox)
                QTest.mouseClick(buttons.button(QDialogButtonBox.StandardButton.Ok), Qt.MouseButton.LeftButton)
                return True
            return False
        self.dialog(self.window._settings, configure)
        self.assertEqual(self.window.send_button.text(), "Send")
        self.send("hello")
        self.assertIn("Hi, Demo", self.window.controller.current.messages[-1].content)
        self.assertFalse((self.directory / "preferences/preferences.sqlite3").exists())

    def test_preferences_save_load_disable_and_erase_use_the_real_memory_vault(self):
        from now_memory import MemoryStore
        def memory_action(action, *, change=False):
            def interact(widget):
                if isinstance(widget, SettingsDialog):
                    if change:
                        widget.fields["language"].setCurrentIndex(widget.fields["language"].findData("en-US"))
                        widget.display_name.setText("Private test preference")
                    QTest.mouseClick(widget.findChild(QPushButton, action), Qt.MouseButton.LeftButton)
                    return False  # the password dialog follows the settings dialog
                if isinstance(widget, QMessageBox):
                    self.confirm(widget)
                    return False
                return self.fill_vault(widget)
            self.dialog(self.window._settings, interact)
            self.wait(lambda: not self.window._jobs)
        memory_action("memory_save", change=True)
        database = self.directory / "preferences/preferences.sqlite3"
        self.assertTrue(database.exists())
        self.assertNotIn(b"Private test preference", database.read_bytes())
        self.assertFalse((self.directory / "history/history.sqlite3").exists())
        self.window.close()
        self.application.processEvents()
        self._new_window()
        self.assertIsNone(self.window.controller.settings["display_name"])
        memory_action("memory_load")
        self.assertEqual(self.window.controller.settings["language"], "en-US")
        self.send("hello")
        self.assertIn("Hi, Private test preference", self.window.controller.current.messages[-1].content)
        memory_action("memory_disable")
        self.assertEqual(self.window.controller.settings["language"], "pt-BR")
        with MemoryStore.open(database.parent, PASSWORD) as store:
            self.assertFalse(store.enabled)
        memory_action("memory_load")
        self.assertEqual(self.window._last_error, "CONSENT_REQUIRED")
        memory_action("memory_clear")
        with MemoryStore.open(database.parent, PASSWORD) as store:
            self.assertFalse(store.enabled)
            store.enable(consent=True)
            self.assertEqual(store.get_preferences(), {})

    def test_hourly_retention_worker_evicts_expired_encrypted_history_from_gui(self):
        from dataclasses import replace
        self.unlock_or_create()
        self.send("horas")
        original_id = self.window.controller.current.id
        expired = replace(self.window.controller.current, updated_at="2020-01-01T00:00:00+00:00")
        self.window._storage("save", {"conversation": expired})
        self.wait(lambda: not self.window._jobs)
        self.window._prune_history()
        self.wait(lambda: not self.window._jobs)
        self.assertNotIn(original_id, self.window.controller.cache)
        self.assertNotIn(original_id, {row["id"] for row in self.window._summaries})

    def test_model_error_is_not_an_assistant_message_and_html_is_plain_text(self):
        user_text = "<b>untrusted user content</b>"
        self.send(user_text)
        self.assertEqual(len(self.window.controller.current.messages), 1)
        self.assertEqual(self.window.controller.current.messages[0].status, "failed")
        self.assertEqual(self.window._last_error, "MODEL_UNAVAILABLE")
        labels = self.window.findChildren(QLabel, "messageBody")
        current = [label for label in labels if label.isVisible() and label.text() == user_text]
        self.assertTrue(current)
        self.assertEqual(current[-1].textFormat(), Qt.TextFormat.PlainText)

    def test_input_limit_prevents_submission(self):
        self.window.composer.setPlainText("x" * 4001)
        self.assertFalse(self.window.send_button.isEnabled())
        QTest.keyClick(self.window.composer, Qt.Key.Key_Return)
        self.assertEqual(self.window.controller.current.messages, ())

    def test_repeated_render_has_no_old_visible_messages_or_clipped_body(self):
        for command in ("oi", "horas", "data"):
            self.send(command)
        self.wait(lambda: len([label for label in self.window.findChildren(QLabel, "messageBody") if label.isVisible()]) == 6)
        for label in self.window.findChildren(QLabel, "messageBody"):
            if label.isVisible():
                self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
        bar = self.window.scroll.verticalScrollBar()
        self.wait(lambda: bar.value() == bar.maximum())
        self.assertEqual(len([label for label in self.window.conversations.findChildren(QLabel) if label.isVisible()]),
                         self.window.conversations.count() * 2)

    def test_cancel_discards_a_real_http_reply_without_fabricating_an_answer(self):
        self.window.composer.setPlainText("horas")
        QTest.keyClick(self.window.composer, Qt.Key.Key_Return)
        self.assertIsNotNone(self.window._pending)
        QTest.mouseClick(self.window.cancel_button, Qt.MouseButton.LeftButton)
        self.application.processEvents()
        QTest.qWait(50)
        self.assertIsNone(self.window._pending)
        messages = self.window.controller.current.messages
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].status, "cancelled")


if __name__ == "__main__":
    unittest.main()
