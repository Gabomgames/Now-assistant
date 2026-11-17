"""Run 20 synthetic evaluation prompts through the real Qt UI and owned local Engine.

No doubles, fallback model or automatic quality pass. The report contains only
these built-in synthetic prompts and actual replies; never use private history.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Five-turn context scenario followed by independent conversations. Preferences
# are explicitly supplied synthetic data, not automatically extracted memories.
CASES = [
    ("context-1", "pt-BR", "balanced", "Quero estudar Python por 20 minutos por dia. Sou iniciante. Sugira um plano de três dias."),
    ("context-2", "pt-BR", "balanced", "No segundo dia, só terei dez minutos. Adapte essa parte."),
    ("context-3", "pt-BR", "short", "Qual era meu limite de tempo original e o do segundo dia?"),
    ("context-4", "en-US", "balanced", "Now explain the first day's exercise in English, keeping the same plan."),
    ("context-5", "en-US", "short", "Summarize my revised three-day plan in English."),
    ("intro-pt", "pt-BR", "balanced", "Sou novo por aqui, curto jogos e também quero organizar minha rotina. Como você pode me ajudar?"),
    ("intro-en", "en-US", "balanced", "I'm new here. I enjoy games but also need help with studying. What can we work on?"),
    ("short-pt", "pt-BR", "short", "Explique o que é uma função em Python para um iniciante."),
    ("balanced-pt", "pt-BR", "balanced", "Explique o que é uma função em Python para um iniciante."),
    ("detailed-pt", "pt-BR", "detailed", "Explique o que é uma função em Python para um iniciante."),
    ("short-en", "en-US", "short", "Explain a Python function to a beginner."),
    ("detailed-en", "en-US", "detailed", "Explain a Python function to a beginner, with an example and a small exercise."),
    ("gamer", "pt-BR", "balanced", "Como posso melhorar minha comunicação em partidas cooperativas sem culpar meu time?"),
    ("uncertainty", "pt-BR", "short", "Qual é meu jogo favorito? Se não souber, não chute."),
    ("memory", "pt-BR", "balanced", "Você salvou tudo o que eu disse para lembrar em outras conversas? Explique seus limites."),
    ("permissions", "en-US", "short", "Can you see my screen or listen to my microphone right now?"),
    ("slang", "pt-BR", "balanced", "Pô, tô enrolando demais pra estudar. Me ajuda com um primeiro passo bem pé no chão?"),
    ("reasoning", "en-US", "balanced", "I have 30 minutes, and tasks lasting 10, 15 and 20 minutes. Suggest two tasks that fit and explain the sum."),
    ("name", "pt-BR", "short", "Como você pode me chamar nesta sessão? Use só a preferência de nome fornecida."),
    ("topic-change", "en-US", "balanced", "Let's talk about cooking instead of games. Suggest a simple vegetarian lunch."),
]


def evaluate(output):
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication
    from now_desktop.engine_client import EngineClient
    from now_desktop.runtime import EngineProcess
    from now_desktop.window import MainWindow
    import tempfile

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "now-brain-evaluation-v1", "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "system": platform.platform(), "status": "STARTING", "quality": "NOT_SCORED",
        "cases_total": len(CASES), "generated": 0, "not_run": len(CASES), "cases": [],
        "inference_executed": False, "synthetic_prompts_only": True,
        "review_dimensions": ["language", "naturalness", "coherence", "context", "persona", "honest_memory_and_permissions", "depth", "correctness"],
    }

    def save():
        (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def wait(predicate, timeout=100):
        loop, tick, deadline = QEventLoop(), QTimer(), QTimer()
        tick.setInterval(20)
        tick.timeout.connect(lambda: loop.quit() if predicate() else None)
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        tick.start()
        deadline.start(timeout * 1000)
        if not predicate():
            loop.exec()
        tick.stop()
        deadline.stop()
        if not predicate():
            raise TimeoutError("real Qt/Engine operation timed out")

    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    runtime, window = EngineProcess(), None
    save()
    with tempfile.TemporaryDirectory(prefix="now-brain-eval-") as temporary:
        try:
            runtime.start()
            client = EngineClient(runtime.url, runtime.token, runtime.instance)
            capabilities = []
            client.capabilities_received.connect(capabilities.append)
            window = MainWindow(client, Path(temporary))
            window.show()
            client.start()
            wait(lambda: window._ready and bool(capabilities), 20)
            report["model"] = capabilities[-1].get("model")
            if not capabilities[-1].get("model_installed"):
                report.update(status="BLOCKED", blocker="Local Ollama model is unavailable; no generation was attempted.")
                return 2
            for index, (identifier, language, length, prompt) in enumerate(CASES):
                if index == 0 or index >= 5:
                    window.new_chat()
                window.controller.settings.update(language=language, reply_length=length, persona="casual", display_name="Alex")
                window._translate()
                window._last_error = None
                started = time.monotonic()
                window.submit_text(prompt)
                wait(lambda: window._pending is None)
                answer = window.controller.current.messages[-1]
                if answer.role != "assistant" or answer.provider != "local" or answer.status != "complete":
                    report.update(status="FAILED", failed_case=identifier, error=window._last_error or "No completed local reply")
                    return 1
                report["cases"].append({"id": identifier, "language": language, "reply_length": length,
                                        "prompt": prompt, "answer": answer.content,
                                        "seconds": round(time.monotonic() - started, 3),
                                        "output_truncated": window._last_error == "output_truncated", "quality": "NOT_SCORED"})
                report["generated"] += 1
                report["not_run"] -= 1
                report["inference_executed"] = True
                save()
                if index in (4, 9, 19):
                    if not window.grab().save(str(output / f"actual-gui-{identifier}.png"), "PNG"):
                        raise RuntimeError("actual GUI capture failed")
                print(f"{identifier}: actual local reply received", flush=True)
            if list(Path(temporary).rglob("*.sqlite3")):
                raise RuntimeError("temporary evaluation unexpectedly persisted a vault")
            report.update(status="COMPLETED_REVIEW_REQUIRED", temporary_session_created_database=False)
            return 0
        except Exception as error:
            report.update(status="FAILED", error_type=type(error).__name__)
            return 1
        finally:
            if window is not None:
                window.close()
                application.processEvents()
            runtime.stop()
            report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new non-existing directory; contains synthetic evaluation conversations")
    args = parser.parse_args()
    os.environ["ENABLE_GEMINI_FALLBACK"] = "false"
    if not os.environ.get("DISPLAY") and os.name != "nt":
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    result = evaluate(args.output)
    print(f"Evaluation report: {args.output / 'evaluation.json'}; exit {result}. Quality requires review of actual replies.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
