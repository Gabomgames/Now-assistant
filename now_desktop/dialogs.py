from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
                              QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout)

from .i18n import text


class VaultDialog(QDialog):
    def __init__(self, language, *, creating=False, preferences=False, consent_required=False, parent=None):
        super().__init__(parent)
        self.setObjectName("vaultDialog")
        self.setWindowTitle(text("memory_title" if preferences else "history_create_title" if creating else "history_unlock_title", language))
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        note = QLabel(text("vault_note", language))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.password = QLineEdit()
        self.password.setObjectName("vaultPassword")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMaxLength(1024)
        self.password.setPlaceholderText(text("password", language))
        self.password.setAccessibleName(text("password", language))
        layout.addWidget(self.password)
        self.confirm = QLineEdit()
        self.confirm.setObjectName("vaultConfirm")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm.setMaxLength(1024)
        self.confirm.setAccessibleName(text("password_confirm", language))
        self.confirm.setPlaceholderText(text("password_confirm", language))
        self.confirm.setVisible(creating)
        layout.addWidget(self.confirm)
        self.consent = QCheckBox(text("consent_preferences" if preferences else "consent_history", language))
        self.consent.setObjectName("vaultConsent")
        self.consent.setVisible(creating or consent_required)
        layout.addWidget(self.consent)
        self.retention = QSpinBox()
        self.retention.setObjectName("retentionDays")
        self.retention.setRange(0, 3650)
        self.retention.setValue(30)
        if creating and not preferences:
            form = QFormLayout()
            form.addRow(text("retention_prompt", language), self.retention)
            layout.addLayout(form)
            history_note = QLabel(text("history_note", language))
            history_note.setWordWrap(True)
            history_note.setObjectName("muted")
            layout.addWidget(history_note)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(text("create" if creating else "unlock", language))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(text("cancel", language))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.creating = creating
        self.requires_consent = creating or consent_required
        self.password.textChanged.connect(self._validate)
        self.confirm.textChanged.connect(self._validate)
        self.consent.toggled.connect(self._validate)
        self._validate()

    def _validate(self):
        password = self.password.text()
        valid = len(password.strip()) >= 12 and len(password.encode("utf-8")) <= 1024
        if self.creating:
            valid = valid and password == self.confirm.text()
        if self.requires_consent:
            valid = valid and self.consent.isChecked()
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)

    def take_values(self):
        values = {"password": self.password.text(), "consent": self.consent.isChecked(), "retention_days": self.retention.value()}
        self.password.clear()
        self.confirm.clear()
        return values

    def reject(self):
        self.password.clear()
        self.confirm.clear()
        super().reject()


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.language = settings["language"]
        self.setObjectName("settingsDialog")
        self.setWindowTitle(text("settings", self.language))
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        form = QFormLayout()
        self.fields = {}
        options = {
            "language": [("Português brasileiro", "pt-BR"), ("English", "en-US")],
            "persona": [(name.title(), name) for name in ("casual", "classic", "gamer", "focus", "creative")],
            "reply_length": [(text("reply_" + value, self.language), value) for value in ("short", "balanced", "detailed")],
        }
        for key, values in options.items():
            field = QComboBox()
            field.setObjectName("setting_" + key)
            for label, value in values:
                field.addItem(label, value)
            field.setCurrentIndex(field.findData(settings[key]))
            self.fields[key] = field
            form.addRow(text(key, self.language), field)
        self.humor = QSpinBox()
        self.humor.setRange(0, 3)
        self.humor.setValue(settings["humor"])
        self.humor.setObjectName("setting_humor")
        form.addRow(text("humor", self.language), self.humor)
        self.display_name = QLineEdit(settings.get("display_name") or "")
        self.display_name.setMaxLength(80)
        self.display_name.setObjectName("setting_display_name")
        form.addRow(text("display_name", self.language), self.display_name)
        layout.addLayout(form)
        note = QLabel(text("session_settings", self.language))
        note.setWordWrap(True)
        note.setObjectName("muted")
        layout.addWidget(note)
        self.engine = getattr(parent, "engine", None)
        if self.engine is not None:
            self.protocol = QComboBox()
            self.protocol.setObjectName("setting_protocol")
            self.protocol.addItem("NOW Brain v1 · SSE", "v1")
            self.protocol.addItem(text("legacy_api", self.language), "v2")
            self.protocol.setCurrentIndex(self.protocol.findData(self.engine.protocol))
            form.addRow(text("api_mode", self.language), self.protocol)
            self.model = QComboBox()
            self.model.setObjectName("setting_model")
            form.addRow(text("model_selection", self.language), self.model)
            self.model_note = QLabel()
            self.model_note.setWordWrap(True)
            layout.addWidget(self.model_note)
            self.refresh_models = QPushButton(text("refresh_model", self.language))
            self.refresh_models.setObjectName("refreshModels")
            self.refresh_models.clicked.connect(self.engine.refresh_models)
            layout.addWidget(self.refresh_models)
            self.engine.capabilities_received.connect(self._models_updated)
            self.protocol.currentIndexChanged.connect(self._model_enabled)
            self._models_updated({})
            self.engine.refresh_models()
        self.memory_action = None
        for action in ("memory_load", "memory_save", "memory_disable", "memory_clear"):
            button = QPushButton(text(action, self.language))
            button.setObjectName(action)
            button.clicked.connect(lambda checked=False, value=action: self._memory(value))
            layout.addWidget(button)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(text("apply", self.language))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(text("cancel", self.language))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return {**{key: field.currentData() for key, field in self.fields.items()},
                "humor": self.humor.value(), "display_name": self.display_name.text().strip() or None}

    def _models_updated(self, values):
        selected = self.model.currentData() if self.model.count() else self.engine.selected_model
        self.model.clear()
        self.model.addItem(text("choose_model", self.language), None)
        for row in self.engine.models:
            self.model.addItem(row["model_id"], row["model_id"])
        if selected is not None and self.model.findData(selected) < 0:
            self.model.addItem(selected + " · " + text("model_missing", self.language), selected)
        self.model.setCurrentIndex(max(0, self.model.findData(selected)))
        key = "inventory_loading" if self.engine.inventory_loading else "model_inventory_empty" if not self.engine.models else "model_choice_note"
        self.model_note.setText(text(key, self.language))
        self.refresh_models.setEnabled(not self.engine.inventory_loading)
        self._model_enabled()

    def _model_enabled(self):
        self.model.setEnabled(self.protocol.currentData() == "v1")

    def _memory(self, action):
        self.memory_action = action
        self.accept()
