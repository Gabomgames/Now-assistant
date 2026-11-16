from dataclasses import replace
from datetime import datetime
import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QSize, QStandardPaths
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QToolButton,
    QVBoxLayout, QWidget)

from now_history import HistoryStore
from now_history.models import utc_now

from .branding import logo_path, window_icon_path
from .controller import ChatController, DEFAULT_SETTINGS
from .dialogs import SettingsDialog, VaultDialog
from .i18n import text
from .storage_service import StorageService


class Composer(QPlainTextEdit):
    submitted = Signal()
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submitted.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, engine, data_directory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NOW Assistant")
        self.setObjectName("nowAssistantWindow")
        self.resize(1280, 840)
        self.setMinimumSize(920, 620)
        self.engine = engine
        self.controller = ChatController()
        self.directory = Path(data_directory)
        self.storage = StorageService(self.directory, self)
        self.storage.completed.connect(self._storage_completed)
        self._epoch, self._pending, self._ready, self._closing = 0, None, False, False
        self._unlocked, self._retention, self._summaries = False, 30, []
        self._jobs, self._blocking_jobs = {}, set()
        self._model_available = False
        self._last_error = None
        self._selection_version = 0
        self._build()
        self.engine.ready.connect(self._engine_ready)
        self.engine.failed.connect(self._show_error)
        self.engine.capabilities_received.connect(self._capabilities)
        self.engine.chat_finished.connect(self._chat_finished)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self._search_history)
        self.search.textChanged.connect(lambda: (self._refresh_list(), self._search_timer.start()))
        self._retention_timer = QTimer(self)
        self._retention_timer.setInterval(60 * 60 * 1000)
        self._retention_timer.timeout.connect(self._prune_history)
        self._retention_timer.start()
        self._translate()
        self._render()

    @property
    def language(self):
        return self.controller.settings["language"]

    def tr_key(self, key):
        return text(key, self.language)

    def _label(self, value, name=None):
        label = QLabel(value)
        label.setTextFormat(Qt.TextFormat.PlainText)
        if name:
            label.setObjectName(name)
        return label

    def _build(self):
        root = QWidget()
        root.setObjectName("main")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 26, 18, 18)
        side.setSpacing(16)
        brand = QHBoxLayout()
        asset = logo_path()
        if asset:
            self.setWindowIcon(QIcon(str(window_icon_path())))
            image = self._label("")
            image.setObjectName("officialLogo")
            image.setPixmap(QPixmap(str(asset)).scaled(58, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            image.setAccessibleName("NOW Assistant — official logo")
            brand.addWidget(image)
        words = QVBoxLayout()
        words.setSpacing(0)
        words.addWidget(self._label("NOW", "brand"))
        words.addWidget(self._label("ASSISTANT", "brandSubtitle"))
        brand.addLayout(words)
        brand.addStretch()
        side.addLayout(brand)
        self.new_button = QPushButton()
        self.new_button.setObjectName("primary")
        self.new_button.setMinimumHeight(43)
        self.new_button.clicked.connect(self.new_chat)
        side.addWidget(self.new_button)
        self.search = QLineEdit()
        self.search.setObjectName("conversationSearch")
        side.addWidget(self.search)
        self.section_label = self._label("", "section")
        side.addWidget(self.section_label)
        self.conversations = QListWidget()
        self.conversations.setObjectName("conversationList")
        self.conversations.currentItemChanged.connect(self._selected)
        side.addWidget(self.conversations, 1)
        self.history_button = QPushButton()
        self.history_button.setObjectName("historyButton")
        self.history_button.clicked.connect(self._history_action)
        side.addWidget(self.history_button)
        self.settings_button = QPushButton()
        self.settings_button.setObjectName("flat")
        self.settings_button.clicked.connect(self._settings)
        side.addWidget(self.settings_button)
        self.privacy_note = self._label("", "muted")
        self.privacy_note.setWordWrap(True)
        side.addWidget(self.privacy_note)
        layout.addWidget(sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(32, 24, 32, 24)
        content.setSpacing(18)
        top = QHBoxLayout()
        self.chat_title = self._label("", "chatTitle")
        self.badge = self._label("", "badge")
        top.addWidget(self.chat_title)
        top.addWidget(self.badge)
        top.addStretch()
        self.engine_status = self._label("", "engineStatus")
        top.addWidget(self.engine_status)
        self.menu_button = QToolButton()
        self.menu_button.setObjectName("conversationMenu")
        self.menu_button.setText("•••")
        self.menu_button.clicked.connect(self._conversation_menu)
        top.addWidget(self.menu_button)
        content.addLayout(top)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.verticalScrollBar().rangeChanged.connect(self._scroll_bottom)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages = QWidget()
        self.messages.setObjectName("messageSurface")
        self.messages.setStyleSheet("QWidget#messageSurface { background: transparent; }")
        self.messages_layout = QVBoxLayout(self.messages)
        self.messages_layout.setContentsMargins(12, 20, 12, 20)
        self.messages_layout.setSpacing(20)
        self.scroll.setWidget(self.messages)
        content.addWidget(self.scroll, 1)
        self.banner = QFrame()
        self.banner.setObjectName("banner")
        warning = QHBoxLayout(self.banner)
        self.error_text = self._label("", "errorText")
        self.error_text.setWordWrap(True)
        warning.addWidget(self.error_text, 1)
        self.retry_button = QPushButton()
        self.retry_button.clicked.connect(self._retry)
        warning.addWidget(self.retry_button)
        self.banner.hide()
        content.addWidget(self.banner)
        composer_frame = QFrame()
        composer_frame.setObjectName("composer")
        entry = QVBoxLayout(composer_frame)
        entry.setContentsMargins(14, 10, 14, 12)
        self.composer = Composer()
        self.composer.setObjectName("messageInput")
        self.composer.setFixedHeight(78)
        self.composer.submitted.connect(self.send_message)
        self.composer.textChanged.connect(self._update_enabled)
        entry.addWidget(self.composer)
        bottom = QHBoxLayout()
        self.keyboard_hint = self._label("", "hint")
        bottom.addWidget(self.keyboard_hint, 1)
        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("cancelRequest")
        self.cancel_button.clicked.connect(self._cancel_pending)
        bottom.addWidget(self.cancel_button)
        self.send_button = QPushButton()
        self.send_button.setObjectName("sendButton")
        self.send_button.setMinimumWidth(94)
        self.send_button.clicked.connect(self.send_message)
        bottom.addWidget(self.send_button)
        entry.addLayout(bottom)
        content.addWidget(composer_frame)
        self.voice_note = self._label("", "hint")
        self.voice_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(self.voice_note)
        layout.addLayout(content, 1)

    def _translate(self):
        for widget, key in ((self.new_button, "new_chat"), (self.section_label, "conversations"),
                            (self.settings_button, "settings"), (self.privacy_note, "temporary_note"),
                            (self.send_button, "send"), (self.cancel_button, "cancel"),
                            (self.keyboard_hint, "keyboard_hint"), (self.voice_note, "voice_pending"),
                            (self.retry_button, "retry")):
            widget.setText(self.tr_key(key))
        self.search.setPlaceholderText(self.tr_key("search"))
        self.composer.setPlaceholderText(self.tr_key("composer"))
        self.composer.setAccessibleName(self.tr_key("composer"))
        self.engine_status.setText(self.tr_key("connecting" if not self._ready else "model_ready" if self._model_available else "offline_commands"))
        self.history_button.setText(self.tr_key("history_on" if self._unlocked else "history_locked" if HistoryStore.exists(self.directory / "history") else "history_off"))

    def _update_enabled(self):
        busy = self._pending is not None
        allowed = self._ready and not busy and not self._blocking_jobs and not self._closing
        value = self.composer.toPlainText().strip()
        self.keyboard_hint.setText(self.tr_key("INVALID_MESSAGE" if len(value) > 4000 else "keyboard_hint"))
        self.send_button.setEnabled(allowed and 0 < len(value) <= 4000)
        self.settings_button.setEnabled(not self._blocking_jobs and not self._closing)
        self.composer.setEnabled(self._ready and not self._blocking_jobs and not self._closing)
        self.cancel_button.setVisible(busy)

    def _engine_ready(self):
        self._ready = True
        self._translate()
        self._update_enabled()

    def _capabilities(self, values):
        self._model_available = bool(values.get("model_installed"))
        self._translate()

    def _title(self, conversation):
        return self.tr_key("new_title") if not conversation.messages and conversation.title == "Nova conversa" else conversation.title

    def _render(self):
        self.chat_title.setText(self._title(self.controller.current))
        self.badge.setText(self.tr_key("temporary" if self.controller.current.temporary else "saved"))
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        if not self.controller.current.messages:
            self.messages_layout.addStretch()
            title = self._label(self.tr_key("welcome_title"), "welcomeTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_layout.addWidget(title)
            subtitle = self._label(self.tr_key("welcome_text"), "welcomeText")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)
            self.messages_layout.addWidget(subtitle)
            limit = self._label(self.tr_key("welcome_limit"), "muted")
            limit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            limit.setWordWrap(True)
            self.messages_layout.addWidget(limit)
            chips = QWidget()
            row = QHBoxLayout(chips)
            row.addStretch()
            for key, value in (("time_chip", "time" if self.language == "en-US" else "horas"), ("help_chip", "help" if self.language == "en-US" else "ajuda")):
                button = QPushButton(self.tr_key(key))
                button.clicked.connect(lambda checked=False, message=value: self.submit_text(message))
                row.addWidget(button)
            row.addStretch()
            self.messages_layout.addWidget(chips)
            self.messages_layout.addStretch(2)
        else:
            for message in self.controller.current.messages:
                self._message_widget(message)
            self.messages_layout.addStretch()
        self._refresh_list()
        self._update_enabled()
        QTimer.singleShot(0, self._scroll_bottom)

    def _scroll_bottom(self):
        if not self._closing:
            self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def _message_widget(self, message):
        row = QWidget()
        horizontal = QHBoxLayout(row)
        horizontal.setContentsMargins(0, 0, 0, 0)
        user = message.role == "user"
        if user:
            horizontal.addStretch(1)
        bubble = QFrame()
        bubble.setObjectName("userBubble" if user else "assistantBubble")
        bubble.setMaximumWidth(700)
        bubble.setMinimumWidth(180)
        box = QVBoxLayout(bubble)
        box.setContentsMargins(17, 13, 17, 12)
        head = QHBoxLayout()
        head.addWidget(self._label(self.tr_key("you" if user else "assistant"), "messageRole"))
        head.addStretch()
        if message.provider:
            head.addWidget(self._label(self.tr_key("offline" if message.provider == "offline" else "model"), "muted"))
        box.addLayout(head)
        body = self._label(message.content, "messageBody")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        body.setAccessibleName(self.tr_key("you" if user else "assistant"))
        box.addWidget(body)
        foot = QHBoxLayout()
        stamp = datetime.fromisoformat(message.created_at).astimezone().strftime("%H:%M")
        if message.status in {"failed", "cancelled"}:
            stamp += " · " + self.tr_key("cancelled_message" if message.status == "cancelled" else "failed_message")
        foot.addWidget(self._label(stamp, "muted"))
        foot.addStretch()
        copy = QPushButton(self.tr_key("copy"))
        copy.setObjectName("copy")
        copy.clicked.connect(lambda checked=False, value=message.content: QApplication.clipboard().setText(value))
        foot.addWidget(copy)
        box.addLayout(foot)
        horizontal.addWidget(bubble)
        if not user:
            horizontal.addStretch(1)
        self.messages_layout.addWidget(row)

    def _refresh_list(self):
        query = self.search.text().strip().casefold()
        summaries = [row for row in self._summaries if not query or query in row["title"].casefold() or row.get("search_match")]
        summaries += self.controller.temporary_summaries(query)
        current = self.controller.current
        if not any(row["id"] == current.id for row in summaries) and not query:
            summaries.append({"id": current.id, "title": self._title(current), "updated_at": current.updated_at, "temporary": current.temporary})
        self.conversations.blockSignals(True)
        for index in range(self.conversations.count()):
            widget = self.conversations.itemWidget(self.conversations.item(index))
            if widget:
                widget.hide()
        self.conversations.clear()
        for summary in sorted(summaries, key=lambda value: value["updated_at"], reverse=True):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, summary["id"])
            item.setSizeHint(QSize(200, 62))
            item.setData(Qt.ItemDataRole.AccessibleTextRole, summary["title"])
            widget = QWidget()
            labels = QVBoxLayout(widget)
            labels.setContentsMargins(10, 8, 8, 8)
            labels.setSpacing(5)
            title = self._label(summary["title"][:32])
            labels.addWidget(title)
            labels.addWidget(self._label(self.tr_key("temporary") if summary["temporary"] else datetime.fromisoformat(summary["updated_at"]).astimezone().strftime("%d/%m · %H:%M"), "muted"))
            self.conversations.addItem(item)
            self.conversations.setItemWidget(item, widget)
            if summary["id"] == current.id:
                self.conversations.setCurrentItem(item)
        self.conversations.blockSignals(False)

    def _persist(self, conversation):
        if not conversation.temporary and self._unlocked and self.controller.history_enabled:
            self._storage("save", {"conversation": conversation}, meta={"conversation_id": conversation.id})

    def submit_text(self, value):
        self.composer.setPlainText(value)
        self.send_message()

    def send_message(self):
        if not self.send_button.isEnabled():
            return
        value = self.composer.toPlainText().strip()
        conversation = None
        try:
            conversation = self.controller.add_user(value)
            identifier = self.engine.chat(conversation.context(), dict(self.controller.settings))
        except (ValueError, RuntimeError):
            if conversation is not None:
                self._persist(self.controller.fail(conversation.id))
                self._render()
            self._show_error("INVALID_MESSAGE")
            return
        self._pending = (identifier, conversation.id)
        self.composer.clear()
        self.banner.hide()
        self._persist(conversation)
        self._render()

    def _chat_finished(self, identifier, result, error):
        if self._closing or self._pending is None or self._pending[0] != identifier:
            return
        conversation_id = self._pending[1]
        self._pending = None
        if error:
            conversation = self.controller.fail(conversation_id, cancelled=error == "CANCELLED")
            self._show_error(error)
        else:
            try:
                conversation = self.controller.finish(conversation_id, result["reply"], result["provider"])
            except (ValueError, KeyError, TypeError):
                conversation = self.controller.fail(conversation_id)
                self._show_error("ENGINE_UNAVAILABLE")
            if result.get("context_trimmed"):
                self._show_error("context_trimmed")
        self._persist(conversation)
        self._render()

    def _cancel_pending(self):
        if self._pending:
            identifier = self._pending[1]
            self._pending = None
            self.engine.cancel()
            self._persist(self.controller.fail(identifier, cancelled=True))
            self._show_error("CANCELLED")
            self._render()

    def new_chat(self):
        self._selection_version += 1
        self._cancel_pending()
        self.controller.new_chat()
        self.banner.hide()
        self._render()

    def _selected(self, item, previous):
        if item is None:
            return
        identifier = item.data(Qt.ItemDataRole.UserRole)
        if identifier == self.controller.current.id:
            return
        self._selection_version += 1
        self._cancel_pending()
        if identifier in self.controller.cache:
            self.controller.select(self.controller.cache[identifier])
            self._render()
        elif self._unlocked:
            self._storage("load", {"id": identifier}, blocking=True, meta={"selection_version": self._selection_version})

    def _show_error(self, code):
        self._last_error = code
        self.error_text.setText(self.tr_key(code))
        self.banner.show()
        self._update_enabled()

    def _retry(self):
        if not self._ready:
            self.engine.reconnect()
        else:
            for message in reversed(self.controller.current.messages):
                if message.role == "user" and message.status == "failed":
                    self.submit_text(message.content)
                    break

    def _storage(self, operation, payload=None, *, blocking=False, meta=None):
        identifier = self.storage.submit(operation, payload, epoch=self._epoch)
        self._jobs[identifier] = meta or {}
        if blocking:
            self._blocking_jobs.add(identifier)
        self._update_enabled()
        return identifier

    def _search_history(self):
        if self._unlocked:
            self._storage("search", {"query": self.search.text().strip()})

    def _prune_history(self):
        if self._unlocked and not self._pending and not self._jobs and not self._closing:
            self._storage("prune", blocking=True)

    def _storage_completed(self, identifier, operation, epoch, result, error):
        self._blocking_jobs.discard(identifier)
        meta = self._jobs.pop(identifier, {})
        if self._closing or epoch != self._epoch:
            self._update_enabled()
            return
        if error:
            if operation == "save":
                conversation = self.controller.cache.get(meta.get("conversation_id"))
                if conversation:
                    fork = self.controller.fork_temporary(conversation.id)
                    if self._pending and self._pending[1] == conversation.id:
                        self._pending = (self._pending[0], fork.id)
                self._show_error("save_failed")
            else:
                self._show_error(error)
        elif operation == "load":
            if meta.get("selection_version") == self._selection_version:
                self.controller.select(result)
        elif operation == "search":
            if result["query"] == self.search.text().strip():
                self._summaries = [{**row, "search_match": True} for row in result["summaries"]]
        elif operation.startswith("memory_"):
            if operation == "memory_load":
                self.controller.settings = {**DEFAULT_SETTINGS, **{key: value for key, value in result.items() if key in DEFAULT_SETTINGS}}
            elif operation in {"memory_disable", "memory_clear"}:
                self.controller.settings = dict(DEFAULT_SETTINGS)
            self._translate()
        elif isinstance(result, dict):
            self._unlocked = result["unlocked"]
            self._retention = result["retention_days"] or 0
            self.controller.history_enabled = result["enabled"]
            self._summaries = result["summaries"]
            for removed_id in result.get("removed_ids", []):
                self.controller.delete_cached(removed_id)
            if operation in {"create", "unlock"}:
                self.controller.new_chat()
            if operation == "rename" and meta.get("updated_conversation"):
                self.controller._update(meta["updated_conversation"])
            if operation == "delete":
                self.controller.delete_cached(meta["conversation_id"])
            if operation == "clear":
                enabled = self.controller.history_enabled
                self.controller.forget_persistent_cache()
                self.controller.history_enabled = enabled
                self.controller.new_chat()
            if self.search.text().strip():
                self._search_timer.start()
        self._translate()
        self._render()

    def _history_action(self):
        if self._unlocked:
            menu = QMenu(self)
            menu.addAction(self.tr_key("lock"), self.lock_history)
            if self.controller.history_enabled:
                menu.addAction(self.tr_key("disable_history"), lambda: self._storage("disable", blocking=True))
            else:
                menu.addAction(self.tr_key("enable_history"), self._enable_history)
            menu.addAction(self.tr_key("retention"), self._change_retention)
            menu.addAction(self.tr_key("clear_history"), self._clear_history)
            menu.exec(self.history_button.mapToGlobal(self.history_button.rect().topLeft()))
            return
        creating = not HistoryStore.exists(self.directory / "history")
        dialog = VaultDialog(self.language, creating=creating, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.take_values()
            self._storage("create" if creating else "unlock", values, blocking=True)
            values["password"] = None
        dialog.deleteLater()

    def lock_history(self):
        self._cancel_pending()
        self._selection_version += 1
        self._epoch += 1
        self._summaries = []
        self._unlocked = False
        self.search.clear()
        self.controller.forget_persistent_cache()
        self._storage("lock", blocking=True)
        self._translate()
        self._render()

    def _confirm(self, key):
        return QMessageBox.question(self, "NOW Assistant", self.tr_key(key),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def _enable_history(self):
        if self._confirm("consent_history"):
            self._storage("enable", {"consent": True}, blocking=True)

    def _change_retention(self):
        days, accepted = QInputDialog.getInt(self, self.tr_key("retention"), self.tr_key("retention_prompt"), self._retention, 0, 3650)
        if accepted and self._confirm("confirm_retention"):
            self._cancel_pending()
            self._storage("retention", {"days": days}, blocking=True)

    def _clear_history(self):
        if self._confirm("confirm_clear"):
            self._cancel_pending()
            self._storage("clear", blocking=True)

    def _conversation_menu(self):
        menu = QMenu(self)
        menu.addAction(self.tr_key("rename"), self.rename_current)
        menu.addAction(self.tr_key("export"), self.export_current)
        menu.addAction(self.tr_key("delete"), self.delete_current)
        menu.addSeparator()
        menu.addAction(self.tr_key("refresh_model"), self.engine.refresh_capabilities)
        menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))

    def rename_current(self):
        self._cancel_pending()
        title, accepted = QInputDialog.getText(self, self.tr_key("rename"), self.tr_key("title_prompt"), text=self.controller.current.title)
        if not accepted or not title.strip():
            return
        try:
            conversation = replace(self.controller.current, title=title.strip()[:100], updated_at=utc_now())
            if conversation.temporary:
                self.controller._update(conversation)
            else:
                self._storage("rename", {"conversation": conversation}, blocking=True,
                              meta={"updated_conversation": conversation})
            self._render()
        except ValueError:
            self._show_error("STORAGE_ERROR")

    def delete_current(self):
        if not self._confirm("confirm_delete"):
            return
        self._cancel_pending()
        conversation = self.controller.current
        if conversation.temporary:
            self.controller.delete_cached(conversation.id)
            self._render()
        else:
            self._storage("delete", {"id": conversation.id}, blocking=True, meta={"conversation_id": conversation.id})

    def export_current(self):
        if not self._confirm("confirm_export"):
            return
        directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        path, _ = QFileDialog.getSaveFileName(self, self.tr_key("export"), str(Path(directory) / "NOW-conversation.json"), "JSON (*.json)")
        if not path:
            return
        conversation = self.controller.current
        if not conversation.temporary:
            self._storage("export", {"id": conversation.id, "path": path}, blocking=True)
        else:
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump({"format": "now-temporary-export-v1", "conversation": conversation.to_dict()}, stream, ensure_ascii=False, indent=2)
            except OSError:
                self._show_error("STORAGE_ERROR")

    def _settings(self):
        dialog = SettingsDialog(self.controller.settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            dialog.deleteLater()
            return
        self.controller.settings = dialog.values()
        self._translate()
        self._render()
        action = dialog.memory_action
        dialog.deleteLater()
        if not action:
            return
        exists = (self.directory / "preferences/preferences.sqlite3").exists()
        if action != "memory_save" and not exists:
            self._show_error("STORAGE_ERROR")
            return
        if action == "memory_clear" and not self._confirm("confirm_memory_clear"):
            return
        vault = VaultDialog(self.language, creating=not exists, preferences=True, consent_required=action == "memory_save", parent=self)
        if vault.exec() == QDialog.DialogCode.Accepted:
            values = vault.take_values()
            values["preferences"] = dict(self.controller.settings)
            self._storage(action, values, blocking=True)
            values["password"] = None
        vault.deleteLater()

    def closeEvent(self, event):
        self._cancel_pending()
        self._closing = True
        self._search_timer.stop()
        self._retention_timer.stop()
        self.engine.close()
        self.storage.close()
        event.accept()
