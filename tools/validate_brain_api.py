"""Real local API/Ollama evaluator for Windows or Linux; never downloads or trains.

Only versioned, synthetic evaluation prompts are sent. Reports contain their
actual replies and stay in the explicit output directory; nothing is uploaded.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from now_brain.client import Client
from now_brain.provider import valid_model
from now_brain.runtime import BrainProcess
from now_engine.providers import local_open


def percentiles(samples):
    ordered = sorted(samples)
    if not ordered:
        return {"samples": 0, "p50_ms": None, "p95_ms": None, "p99_ms": None}
    return {"samples": len(ordered), **{
        f"p{p}_ms": round(ordered[max(0, math.ceil(p * len(ordered) / 100) - 1)], 3)
        for p in (50, 95, 99)}}


def model_metadata(model):
    # Installed model metadata is read through the same fixed local endpoint.
    # License text is evidence for review, not automatic legal approval.
    request = Request("http://127.0.0.1:11434/api/show",
                      data=json.dumps({"model": model, "verbose": False}).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with local_open(request, timeout=10) as response:
            raw = response.read(2097153)
        if len(raw) > 2097152:
            return {"status": "metadata_too_large", "license_review": "PENDING"}
        payload = json.loads(raw)
        license_text = payload.get("license", "")
        if not isinstance(license_text, str):
            license_text = ""
        return {"status": "observed", "license_sha256": hashlib.sha256(license_text.encode()).hexdigest(),
                "license_text": license_text[:65536], "license_text_truncated": len(license_text) > 65536,
                "license_review": "PENDING"}
    except (OSError, URLError, ValueError):
        return {"status": "NOT_OBSERVED", "license_review": "PENDING"}


def provenance():
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        sha, dirty = None, None
    files = [*sorted((ROOT / "now_brain").glob("*.py")), ROOT / "now_engine/assistant.py",
             ROOT / "now_engine/security.py", ROOT / "validation/brain-v5-cases.json", Path(__file__)]
    return {"source_sha": sha, "source_dirty": dirty, "files_sha256": {
        str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}}


def evaluate(output, models, timeout):
    cases_path = ROOT / "validation/brain-v5-cases.json"
    plan = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = plan["cases"]
    if len(cases) < 20 or len({row["id"] for row in cases}) != len(cases):
        raise ValueError("at least 20 distinct evaluation cases are required")
    for model in models:
        valid_model(model)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "now-brain-api-evaluation-v1", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              **provenance(), "system": platform.platform(), "python": platform.python_version(),
              "cpu_count": os.cpu_count(), "status": "STARTING", "quality": "NOT_SCORED",
              "inference_executed": False, "training_or_upload_executed": False,
              "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
              "models": [{"model_id": model, "status": "NOT_RUN", "generated": 0,
                          "cases": [{"id": row["id"], "status": "NOT_RUN"} for row in cases]} for model in models],
              "measurement_limits": "Single-client end-to-end local API wall times; Ollama-reported token timing. No GPU, model RAM, FPS, multi-user or SLO claim."}

    def save():
        (output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    runtime = BrainProcess(timeout=timeout)
    save()
    try:
        runtime.start()
        client = Client(runtime.url, runtime.token, timeout=timeout + 15)
        report["health"] = client.json("/health")
        schema = client.json("/openapi.json")
        (output / "openapi.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Independent API baseline: explicitly deterministic, never counted as inference.
        offline_times = []
        for _ in range(10):
            start = time.monotonic()
            answer = client.json("/chat", {"messages": [{"role": "user", "content": "horas"}], "mode": "offline"})
            if answer["provider_id"] != "offline" or not answer["reply"].startswith("Agora são"):
                raise ValueError("offline API check failed")
            offline_times.append((time.monotonic() - start) * 1000)
        report["offline_api_latency"] = percentiles(offline_times)
        try:
            inventory = client.json("/models")
        except HTTPError as error:
            report.update(status="BLOCKED", blocker=json.load(error)["error"]["code"])
            return 2
        installed = {row["model_id"]: row for row in inventory["models"]}
        for evaluation in report["models"]:
            model = evaluation["model_id"]
            if model not in installed:
                evaluation.update(status="BLOCKED", blocker="model_not_installed")
                continue
            evaluation["inventory"] = installed[model]
            evaluation["license"] = model_metadata(model)
            evaluation["status"] = "RUNNING"
            conversation, conversation_id, latencies, first_tokens, rates = [], None, [], [], []
            evaluation["cases"] = []
            for index, case in enumerate(cases):
                if case.get("conversation") != "plan":
                    conversation, conversation_id = [], None
                conversation.append({"role": "user", "content": case["prompt"]})
                payload = {"messages": conversation, "mode": "model", "model_id": model,
                           "options": {"language": case["language"], "reply_length": case["length"],
                                       "persona": "casual", "display_name": "Alex"}}
                if conversation_id:
                    payload["conversation_id"] = conversation_id
                started, first, text, terminal, stream_error = time.monotonic(), None, "", None, None
                try:
                    # Alternate complete JSON and real streaming within the same case set.
                    if index % 2 == 0:
                        terminal = client.json("/chat", payload)
                        text = terminal["reply"]
                    else:
                        with client.stream(payload) as events:
                            for event, data in events:
                                if event == "delta":
                                    if first is None:
                                        first = (time.monotonic() - started) * 1000
                                    text += data["text"]
                                elif event == "done":
                                    terminal = data
                                elif event == "error":
                                    stream_error = data["error"]["code"]
                        if not terminal or terminal["reply"] != text:
                            raise ValueError(stream_error or "incomplete_stream")
                    if terminal["provider_id"] != "ollama" or terminal["model_id"] != model or terminal["status"] not in {"completed", "truncated"} or not text.strip():
                        raise ValueError("unexpected generation result")
                except (OSError, URLError, ValueError) as error:
                    code = stream_error or type(error).__name__
                    if isinstance(error, HTTPError):
                        code = json.load(error)["error"]["code"]
                    evaluation["cases"].append({"id": case["id"], "status": "FAILED", "error": code})
                    evaluation["cases"].extend({"id": row["id"], "status": "NOT_RUN"} for row in cases[index + 1:])
                    evaluation["status"] = "FAILED"
                    break
                elapsed = (time.monotonic() - started) * 1000
                metrics = terminal["metrics"]
                latencies.append(elapsed)
                if metrics["first_token_ms"] is not None:
                    first_tokens.append(metrics["first_token_ms"])
                if metrics["tokens_per_second"] is not None:
                    rates.append(metrics["tokens_per_second"])
                evaluation["cases"].append({**case, "status": "GENERATED_REVIEW_REQUIRED", "answer": text,
                                            "generation_status": terminal["status"], "request_id": terminal["request_id"],
                                            "elapsed_ms": round(elapsed, 3), "client_first_token_ms": first,
                                            "metrics": metrics, "quality": "NOT_SCORED"})
                conversation_id = terminal["conversation_id"]
                conversation.append({"role": "assistant", "content": text})
                evaluation["generated"] += 1
                report["inference_executed"] = True
                save()
                print(f"{model}: {case['id']} generated; review required", flush=True)
            evaluation["latency"] = percentiles(latencies)
            evaluation["first_token_latency"] = percentiles(first_tokens)
            evaluation["mean_tokens_per_second"] = round(statistics.mean(rates), 3) if rates else None
            if evaluation["status"] != "FAILED":
                evaluation["status"] = "COMPLETED_REVIEW_REQUIRED"
                # Test authenticated cancellation using an actual installed model.
                payload = {"model_id": model, "messages": [{"role": "user", "content": "Explique detalhadamente como organizar um projeto Python em vinte etapas."}],
                           "options": {"reply_length": "detailed"}}
                start_cancel = time.monotonic()
                with client.stream(payload) as events:
                    terminal = None
                    for event, data in events:
                        if event == "state":
                            start_cancel = time.monotonic()
                            try:
                                client.json("/chat/cancel", {"request_id": data["request_id"]})
                            except HTTPError:
                                pass  # A completed generation may win the cancel race.
                        if event == "done":
                            terminal = data
                    evaluation["cancellation"] = {"status": "DEMONSTRATED" if terminal and terminal["status"] == "cancelled" else "NOT_DEMONSTRATED",
                                                  "elapsed_ms": round((time.monotonic() - start_cancel) * 1000, 3),
                                                  "scope": "upstream_socket_closed; backend compute reclamation not measured"}
            save()
        states = [row["status"] for row in report["models"]]
        report["status"] = "FAILED" if "FAILED" in states else "BLOCKED" if "BLOCKED" in states else "COMPLETED_REVIEW_REQUIRED"
        return {"FAILED": 1, "BLOCKED": 2, "COMPLETED_REVIEW_REQUIRED": 0}[report["status"]]
    except (OSError, URLError, ValueError, RuntimeError) as error:
        report.update(status="FAILED", error_type=type(error).__name__)
        return 1
    finally:
        try:
            runtime.stop()
        finally:
            for evaluation in report["models"]:
                observed = {row["id"] for row in evaluation["cases"]}
                evaluation["cases"].extend({"id": row["id"], "status": "NOT_RUN"}
                                           for row in cases if row["id"] not in observed)
            report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
            save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new report directory; synthetic prompts/replies only")
    parser.add_argument("--models", nargs="+", default=["qwen2.5:0.5b", "qwen2.5:1.5b"])
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 900 or len(args.models) > 5 or len(set(args.models)) != len(args.models):
        parser.error("use 1–5 distinct models and timeout between 1 and 900 seconds")
    result = evaluate(args.output, args.models, args.timeout)
    print(f"Report: {args.output / 'evaluation.json'}; exit={result}. No quality approval is automatic.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
