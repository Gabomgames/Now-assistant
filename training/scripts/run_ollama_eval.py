"""Evaluate actual local Ollama replies; dry-run validates the plan without inference."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    from .validate_dataset import ROOT, check_eval_file, read_jsonl
except ImportError:
    from validate_dataset import ROOT, check_eval_file, read_jsonl


def load_plan(model=None, cases_path=None):
    settings = json.loads((ROOT / "config/evaluation.json").read_text(encoding="utf-8"))
    cases_path = Path(cases_path) if cases_path else ROOT / settings["cases"]
    count, errors = check_eval_file(cases_path)
    if errors:
        raise ValueError("; ".join(errors))
    persona = (ROOT / settings["persona"]).read_text(encoding="utf-8").strip()
    if not persona:
        raise ValueError("empty evaluation persona")
    model = model or settings["default_model"]
    if not model.strip() or ":cloud" in model.casefold() or "://" in model:
        raise ValueError("use a local Ollama model tag")
    cases = [row for _, row in read_jsonl(cases_path)[0]]
    overrides = settings["expected_language_overrides"]
    if set(overrides) - {row["id"] for row in cases}:
        raise ValueError("language override references an unknown evaluation case")
    plan = {
        "model": model, "cases_total": count, "generated": 0, "not_run": count,
        "persona_sha256": hashlib.sha256(persona.encode("utf-8")).hexdigest(),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "options": settings["options"], "quality": "NOT_SCORED",
        "review_dimensions": settings["manual_review_dimensions"],
        "expected_languages": {row["id"]: overrides.get(row["id"], row["language"]) for row in cases},
    }
    return plan, cases, persona


def query_local(model, prompt, persona, options, timeout=90):
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps({"model": model, "messages": [
            {"role": "system", "content": persona}, {"role": "user", "content": prompt},
        ], "stream": False, "options": options}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        output = json.load(response)
    answer = (output.get("message") or {}).get("content", "")
    if not isinstance(answer, str) or not answer.strip() or output.get("done") is not True:
        raise ValueError("Ollama did not complete a nonempty reply")
    return answer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan, cases, persona = load_plan(args.model, args.cases)
    except (OSError, UnicodeError, ValueError) as error:
        print("INVALID EVALUATION PLAN:", error)
        return 1
    if args.dry_run:
        print(json.dumps({**plan, "status": "DRY_RUN", "inference_executed": False}, ensure_ascii=False, indent=2))
        return 0

    tag = re.sub(r"[^A-Za-z0-9_.-]", "-", plan["model"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or ROOT / "reports" / f"eval-{tag}-{stamp}.jsonl"
    metadata = output.with_suffix(output.suffix + ".meta.json")
    if output.exists() or metadata.exists():
        print("REPORT NOT CREATED: output already exists; choose a new path.")
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        metadata.touch(exist_ok=False)
        stream = output.open("x", encoding="utf-8")
    except OSError as error:
        print("REPORT NOT CREATED:", type(error).__name__)
        return 1
    summary = {**plan, "started_at_utc": datetime.now(timezone.utc).isoformat(), "status": "PREFLIGHT", "failed": 0}

    def save():
        metadata.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    save()
    with stream:
        try:
            with urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
                inventory = json.load(response)
            matches = [row for row in inventory.get("models", []) if row.get("name") == plan["model"] or row.get("model") == plan["model"]]
            if not matches:
                raise ValueError("requested model is not installed")
            if any(row.get("remote_host") or row.get("remote_model") for row in matches):
                raise ValueError("remote/cloud model entries are not accepted")
        except (URLError, TimeoutError, OSError, ValueError) as error:
            summary.update(status="BLOCKED", error=f"{type(error).__name__}: {error}")
            save()
            print("REAL EVALUATION NOT STARTED:", error)
            return 2
        for case in cases:
            started = time.perf_counter()
            try:
                answer = query_local(plan["model"], case["prompt"], persona, plan["options"])
            except (URLError, TimeoutError, OSError, ValueError) as error:
                summary.update(status="PARTIAL" if summary["generated"] else "FAILED",
                               failed=1, failed_case=case["id"], error=f"{type(error).__name__}: {error}")
                summary["not_run"] = len(cases) - summary["generated"] - 1
                save()
                print("REAL EVALUATION INCOMPLETE:", error)
                return 2
            record = {
                **case, "expected_language": plan["expected_languages"][case["id"]],
                "model": plan["model"], "answer": answer, "quality": "NOT_SCORED",
                "seconds": round(time.perf_counter() - started, 3),
                "persona_sha256": plan["persona_sha256"], "cases_sha256": plan["cases_sha256"],
                "options": plan["options"], "source": "actual_local_ollama_response",
            }
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            summary["generated"] += 1
            summary["not_run"] -= 1
            summary["status"] = "RUNNING_UNSCORED"
            save()
            print(f"{case['id']}: {answer[:110]!r}", flush=True)
    summary.update(status="COMPLETED_UNSCORED", completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    print(f"Completed {summary['generated']} actual generations; human review required. Saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
