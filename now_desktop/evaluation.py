"""Packaged model evaluator: native UI, owned API, isolated cancellable worker."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from uuid import uuid4

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QLabel, QPushButton,
                              QVBoxLayout, QWidget)

from .engine_client import EngineClient
from .runtime import EngineProcess
from now_engine.processes import stop_owned_process


class EvaluationWindow(QWidget):
    def __init__(self, self_check=None):
        super().__init__()
        self.setObjectName("main")
        self.setWindowTitle("NOW Brain — avaliação local")
        self.resize(700, 500)
        from .branding import window_icon_path
        if window_icon_path():
            self.setWindowIcon(QIcon(str(window_icon_path())))
        self.runtime = EngineProcess()
        self.runtime.start()
        self.client = EngineClient(self.runtime.url, self.runtime.token, self.runtime.instance)
        self.client.ready.connect(self._ready)
        self.client.failed.connect(lambda code: self.status.setText("Engine indisponível: " + code))
        self.client.capabilities_received.connect(self._inventory)
        self.worker, self.output, self.last_report = None, None, None
        self.self_check, self.exit_code, self._closing = self_check, 1, False
        layout = QVBoxLayout(self)
        note = QLabel("Avalia apenas prompts sintéticos. Não lê histórico ou memória, não baixa modelos e não envia relatórios. A qualidade deve ser revisada; velocidade não escolhe o melhor modelo.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.status = QLabel("Conectando à Engine local…")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.choices, self.choice_layout = [], QVBoxLayout()
        layout.addLayout(self.choice_layout)
        self.refresh = QPushButton("Verificar Ollama e modelos")
        self.refresh.clicked.connect(self.client.refresh_models)
        layout.addWidget(self.refresh)
        self.start = QPushButton("Avaliar modelos selecionados (20 casos por modelo)")
        self.start.setEnabled(False)
        self.start.clicked.connect(self._choose_output)
        layout.addWidget(self.start)
        self.stop = QPushButton("Parar avaliação")
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self._stop)
        layout.addWidget(self.stop)
        self.open = QPushButton("Abrir relatório legível")
        self.open.setEnabled(False)
        self.open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output / "report.html"))))
        layout.addWidget(self.open)
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self._poll)
        QTimer.singleShot(0, self.client.start)

    def _ready(self):
        self.start.setEnabled(True)
        if self.self_check is not None:
            self._launch(Path(self.self_check), ["now-evaluation-self-check-" + secrets.token_hex(12)])

    def _inventory(self, values):
        if self._closing or self.worker is not None:
            return
        if self.client.inventory_loading:
            self.status.setText("Verificando os modelos instalados no Ollama…")
            return
        for checkbox in self.choices:
            self.choice_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.choices = []
        for row in self.client.models:
            checkbox = QCheckBox(row["model_id"])
            checkbox.setChecked(row["model_id"] in {"qwen2.5:0.5b", "qwen2.5:1.5b"})
            self.choices.append(checkbox)
            self.choice_layout.addWidget(checkbox)
        self.start.setEnabled(True)
        self.status.setText("Modelos locais detectados. Comparação sem vencedor automático." if self.choices else
                            "Ollama indisponível ou sem modelos locais. Abra o Ollama e verifique novamente.")

    def _choose_output(self):
        models = [choice.text() for choice in self.choices if choice.isChecked()]
        if not models:
            if self.choices:
                self.status.setText("Selecione ao menos um modelo instalado.")
                return
            models = ["qwen2.5:0.5b", "qwen2.5:1.5b"]
        parent = QFileDialog.getExistingDirectory(self, "Escolha onde salvar a avaliação")
        if parent:
            self._launch(Path(parent) / ("NOW-evaluation-" + str(uuid4())), models)

    def _launch(self, output, models):
        self.output, self.last_report = output, None
        command = [sys.executable] if getattr(sys, "frozen", False) else [sys.executable, "-m", "now_desktop"]
        command += ["--evaluate-child", "--output", str(output), "--models", *models]
        environment = {**os.environ, "NOW_EVAL_URL": self.runtime.url, "NOW_EVAL_TOKEN": self.runtime.token,
                       "PYTHONIOENCODING": "utf-8", "ENABLE_GEMINI_FALLBACK": "false"}
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        self.worker = subprocess.Popen(command, cwd=Path(__file__).resolve().parents[1], env=environment,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
        self.start.setEnabled(False)
        self.refresh.setEnabled(False)
        self.stop.setEnabled(True)
        self.open.setEnabled(False)
        self.status.setText("Executando casos reais no Ollama local. O tempo depende dos modelos e do computador…")
        self.timer.start()

    def _poll(self):
        if self.worker is None:
            return
        try:
            self.last_report = json.loads((self.output / "evaluation.json").read_text(encoding="utf-8"))
            rows = self.last_report["models"]
            self.status.setText("\n".join(f"{row['model_id']}: {row['generated']}/20 · {row['status']}" for row in rows))
        except (OSError, ValueError):
            pass
        code = self.worker.poll()
        if code is None:
            return
        self.exit_code, self.worker = code, None
        if self.last_report is None:
            self.status.setText("Falha ao iniciar a avaliação; nenhum resultado de inferência foi aprovado.")
        else:
            self.status.setText(self.last_report["status"] + "\n" + self.status.text())
        self.timer.stop()
        self.stop.setEnabled(False)
        self.start.setEnabled(True)
        self.refresh.setEnabled(True)
        self.open.setEnabled((self.output / "report.html").is_file())
        if self.self_check is not None:
            valid = (code == 2 and self.last_report is not None and self.last_report["status"] == "BLOCKED"
                     and not self.last_report["inference_executed"])
            if not self.grab().save(str(self.output / "evaluator-self-check.png"), "PNG"):
                valid = False
            self.exit_code = 0 if valid else 1
            self.close()
            QApplication.instance().exit(self.exit_code)

    def _stop(self):
        stop_owned_process(self.worker)
        self.worker = None
        self.timer.stop()
        # Own API only; closing its sockets interrupts current generation.
        self.client.close()
        self.runtime.stop()
        self.status.setText("Avaliação parada. Relatório parcial disponível; geração e qualidade não concluídas.")
        self.start.setEnabled(False)
        self.refresh.setEnabled(False)
        self.stop.setEnabled(False)
        self.open.setEnabled(bool(self.output and (self.output / "report.html").is_file()))
        if self.output:
            try:
                self.last_report = json.loads((self.output / "evaluation.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        if self.output and self.last_report:
            from tools.validate_brain_api import ROOT
            cases = json.loads((ROOT / "validation/brain-v5-cases.json").read_text(encoding="utf-8"))["cases"]
            for model in self.last_report["models"]:
                if model["status"] == "RUNNING":
                    model["status"] = "CANCELLED_PARTIAL"
                observed = {case["id"] for case in model["cases"]}
                model["cases"].extend({"id": case["id"], "status": "NOT_RUN"} for case in cases if case["id"] not in observed)
            self.last_report["status"] = "CANCELLED_PARTIAL"
            (self.output / "evaluation.json").write_text(json.dumps(self.last_report, ensure_ascii=False, indent=2), encoding="utf-8")
            from tools.validate_brain_api import readable_report
            (self.output / "report.html").write_text(readable_report(self.last_report), encoding="utf-8")

    def closeEvent(self, event):
        self._closing = True
        if self.worker is not None:
            self._stop()
        self.timer.stop()
        stop_owned_process(self.worker)
        self.client.close()
        self.runtime.stop()
        event.accept()


def child_main(output, models):
    if output is None or not models:
        return 1
    try:
        from now_brain.client import Client
        from tools.validate_brain_api import evaluate
        client = Client(os.environ["NOW_EVAL_URL"], os.environ["NOW_EVAL_TOKEN"], timeout=315)
        return evaluate(output, models, 300, client=client)
    except Exception as error:
        # Bounded packaging diagnosis, without prompts, tokens or environment dumps.
        output.mkdir(parents=True, exist_ok=True)
        (output / "worker-error.json").write_text(json.dumps({"error_type": type(error).__name__,
            "frozen_executable": bool(getattr(sys, "frozen", False))}), encoding="utf-8")
        return 1


def run(self_check=None):
    application = QApplication.instance() or QApplication([])
    from .theme import apply_theme
    apply_theme(application)
    window = EvaluationWindow(self_check)
    window.show()
    if self_check:
        QTimer.singleShot(45000, lambda: (window.close(), application.exit(1)))
    return application.exec()
