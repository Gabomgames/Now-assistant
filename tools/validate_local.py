"""Exercise actual Ollama/Engine/HTTP/CLI paths; never replace model replies with mocks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MODEL = "qwen2.5:0.5b"
PROMPTS = {
    "pt-BR": "Responda em português brasileiro, em uma frase: para que serve uma lista de compras?",
    "en-US": "Answer only in English, in one short sentence: what is a shopping list useful for?",
}


def http_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=100) as response:
        return json.load(response)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--cli-executable", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.api_port <= 65535:
        parser.error("--api-port must be between 1 and 65535")

    # Explicitly disable Gemini for the Engine and CLI; the API must use these same settings.
    os.environ["ENABLE_GEMINI_FALLBACK"] = "false"
    os.environ["OLLAMA_MODEL"] = MODEL
    from now_engine.core import route

    api = f"http://127.0.0.1:{args.api_port}"
    ollama = "http://127.0.0.1:11434"
    report = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "gemini_enabled_for_engine_and_cli": False,
        "language_review": "not_run",
        "checks": [],
    }

    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def check(name, operation):
        start = time.perf_counter()
        try:
            evidence = operation()
            item = {"name": name, "status": "passed", "evidence": evidence}
        except Exception as error:
            # Only fixed, non-sensitive test prompts are used. Do not include process environments.
            item = {"name": name, "status": "failed", "error": f"{type(error).__name__}: {error}"}
        item["seconds"] = round(time.perf_counter() - start, 3)
        report["checks"].append(item)
        save()
        print(f"{item['status']}: {name}", flush=True)
        return item

    def equal(actual, expected):
        if actual != expected:
            raise AssertionError(f"Expected {expected!r}; received {actual!r}")
        return actual

    def api_chat(message, provider):
        answer = http_json(api + "/v1/chat", {"message": message})
        equal(answer["provider"], provider)
        if not answer.get("reply", "").strip():
            raise AssertionError("Empty model reply")
        if answer["reply"] == "O modelo local não retornou uma resposta.":
            raise AssertionError("Provider returned its empty-response diagnostic")
        return answer

    cli = [str(args.cli_executable.resolve())] if args.cli_executable else [sys.executable, str(ROOT / "main.py")]

    def cli_chat(message, provider):
        result = subprocess.run(
            cli, input=message + "\nsair\n", text=True, encoding="utf-8",
            capture_output=True, cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=105, check=True,
        )
        if f"NOW [{provider}]:" not in result.stdout:
            raise AssertionError("CLI did not return the expected provider: " + result.stdout)
        return {"stdout": result.stdout, "stderr": result.stderr}

    check("api_health", lambda: equal(http_json(api + "/health")["status"], "ok"))
    for message in ("oi", "horas", "data"):
        check("api_offline_" + message, lambda m=message: api_chat(m, "offline"))
    check("cli_offline", lambda: cli_chat("ajuda", "offline"))
    check("ollama_version", lambda: http_json(ollama + "/api/version"))
    inventory = check("ollama_models", lambda: http_json(ollama + "/api/tags"))
    models = inventory.get("evidence", {}).get("models", [])
    installed = any(model.get("name") == MODEL or model.get("model") == MODEL for model in models)

    if not installed:
        report["status"] = "blocked"
        report["blocker"] = f"Model {MODEL} is not installed; generation tests were not run."
        for language in PROMPTS:
            for channel in ("ollama", "engine", "api", "cli"):
                report["checks"].append({"name": f"{channel}_{language}", "status": "not_run", "reason": report["blocker"]})
        save()
        print(report["blocker"], flush=True)
        return 2

    def generate(message):
        response = http_json(ollama + "/api/generate", {
            "model": MODEL, "prompt": message, "stream": False,
            "options": {"num_predict": 128, "temperature": 0},
        })
        if not response.get("response", "").strip() or not response.get("done"):
            raise AssertionError("Ollama did not complete a nonempty generation")
        return response

    def engine_chat(message):
        response = route(message)
        equal(response["provider"], "local")
        if not response["reply"].strip() or response["reply"] == "O modelo local não retornou uma resposta.":
            raise AssertionError("Engine did not return generated text")
        return response

    for language, message in PROMPTS.items():
        check("ollama_" + language, lambda m=message: generate(m))
        check("engine_" + language, lambda m=message: engine_chat(m))
        check("api_" + language, lambda m=message: api_chat(m, "local"))
        check("cli_" + language, lambda m=message: cli_chat(m, "local"))
    failed = any(item["status"] == "failed" for item in report["checks"])
    report["status"] = "failed" if failed else "transport_passed_language_review_required"
    report["language_review"] = "pending_review_of_actual_responses"
    save()
    print("Inspect actual replies in the JSON to assess language and answer quality.", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
