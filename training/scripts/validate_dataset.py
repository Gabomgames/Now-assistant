"""Validate dataset structure and held-out separation, without model/network dependencies.

Structural checks do not certify authorship, licensing, content quality or model behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]


def normalize_prompt(value):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", value).casefold()))


def read_jsonl(path):
    rows, errors, count = [], [], 0
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return [], 0, [f"cannot read {Path(path).name}: {type(error).__name__}"]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        count += 1
        try:
            rows.append((number, json.loads(line)))
        except json.JSONDecodeError:
            errors.append(f"line {number}: invalid JSON")
    if not count:
        errors.append("empty dataset")
    return rows, count, errors


def check_file(path):
    rows, count, errors = read_jsonl(path)
    seen = set()
    for number, item in rows:
        if not isinstance(item, dict) or set(item) != {"prompt", "completion"}:
            errors.append(f"line {number}: expected prompt and completion keys only")
            continue
        invalid = False
        for field, role in (("prompt", "user"), ("completion", "assistant")):
            messages = item[field]
            if (not isinstance(messages, list) or len(messages) != 1
                    or not isinstance(messages[0], dict)
                    or set(messages[0]) != {"role", "content"}
                    or messages[0].get("role") != role
                    or not isinstance(messages[0].get("content"), str)
                    or not messages[0]["content"].strip()
                    or len(messages[0]["content"]) > 2000):
                errors.append(f"line {number}: malformed {field} message")
                invalid = True
        if invalid:
            continue
        prompt = normalize_prompt(item["prompt"][0]["content"])
        if not prompt:
            errors.append(f"line {number}: prompt has no words")
        elif prompt in seen:
            errors.append(f"line {number}: duplicate prompt")
        seen.add(prompt)
    return count, errors


def check_eval_file(path):
    rows, count, errors = read_jsonl(path)
    seen_ids, seen_prompts = set(), set()
    fields = {"id", "language", "category", "prompt", "expected_behavior"}
    for number, item in rows:
        if not isinstance(item, dict) or set(item) != fields:
            errors.append(f"line {number}: invalid evaluation fields")
            continue
        if any(not isinstance(item[key], str) or not item[key].strip() for key in fields):
            errors.append(f"line {number}: evaluation values must be nonempty strings")
            continue
        if item["language"] not in {"pt-BR", "en", "en-US", "en-GB"}:
            errors.append(f"line {number}: unsupported evaluation language")
        if len(item["prompt"]) > 2000:
            errors.append(f"line {number}: evaluation prompt exceeds 2000 characters")
        prompt = normalize_prompt(item["prompt"])
        if item["id"] in seen_ids:
            errors.append(f"line {number}: duplicate evaluation id")
        if prompt in seen_prompts:
            errors.append(f"line {number}: duplicate evaluation prompt")
        seen_ids.add(item["id"])
        seen_prompts.add(prompt)
    return count, errors


def prompt_set(path, evaluation=False):
    result = set()
    for _, row in read_jsonl(path)[0]:
        try:
            text = row["prompt"] if evaluation else row["prompt"][0]["content"]
            if isinstance(text, str):
                result.add(normalize_prompt(text))
        except (KeyError, IndexError, TypeError):
            continue
    return result


def check_separation(training, evaluation, validation=None):
    groups = {"train": prompt_set(training), "evaluation": prompt_set(evaluation, evaluation=True)}
    if validation is not None:
        groups["validation"] = prompt_set(validation)
    errors = []
    names = list(groups)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            overlap = groups[left] & groups[right]
            if overlap:
                errors.append(f"{left}/{right}: {len(overlap)} overlapping prompt(s)")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=ROOT / "data/now_seed.jsonl")
    parser.add_argument("--eval", dest="evaluation", type=Path, default=ROOT / "data/eval_cases.jsonl")
    parser.add_argument("--validation", type=Path)
    args = parser.parse_args(argv)
    count, errors = check_file(args.path)
    evaluation_count, evaluation_errors = check_eval_file(args.evaluation)
    errors += ["evaluation: " + error for error in evaluation_errors]
    if args.validation is not None:
        _, validation_errors = check_file(args.validation)
        errors += ["validation: " + error for error in validation_errors]
    errors += check_separation(args.path, args.evaluation, args.validation)
    print(f"Training records: {count}; evaluation records: {evaluation_count}; issues: {len(errors)}")
    for error in errors:
        print("ERROR:", error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
