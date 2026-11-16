"""Run the real full suite and write machine-readable results for distribution gates."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append(test.id())


def run(output):
    suite = unittest.defaultTestLoader.discover(str(ROOT), top_level_dir=str(ROOT))
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    allowed_reason = "POSIX permission check"
    unexpected = [(test.id(), reason) for test, reason in result.skipped
                  if not (platform.system() == "Windows" and reason == allowed_reason)]
    gui = [name for name in result.successes if name.startswith("tests.test_desktop_gui.")]
    http = [name for name in result.successes if name.startswith("tests.test_desktop_api.")]
    passed = result.wasSuccessful() and not unexpected and len(gui) >= 9 and len(http) >= 6
    report = {
        "schema": "now-tests-v1", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "system": platform.system(), "python_version": platform.python_version(),
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tests_run": result.testsRun, "passed": len(result.successes),
        "failures": len(result.failures), "errors": len(result.errors),
        "failed_tests": [test.id() for test, _ in result.failures],
        "error_tests": [test.id() for test, _ in result.errors],
        "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        "unexpected_skips": unexpected, "real_gui_tests_passed": len(gui), "real_http_tests_passed": len(http),
        "status": "passed" if passed else "failed",
        "scope": "Includes model/audio doubles and synthetic release-gate metadata/ZIP fixtures; native packaged smoke is separate. No model/physical audio approval.",
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        def annotation(kind, title, message):
            escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::{kind} title={title}::{escaped}")
        # Test fixtures contain no user data. Keep public diagnostics bounded;
        # never print process environments, tokens or application conversations.
        for test, detail in result.failures + result.errors:
            lines = [line for line in detail.splitlines() if line.strip()]
            exception = next((index for index in range(len(lines) - 1, -1, -1)
                              if re.match(r"^[A-Za-z][\w.]*?(?:Error|Exception):", lines[index])), len(lines) - 1)
            message = " | ".join(lines[exception:exception + 4]) if lines else "failed"
            annotation("error", "NOW source test", test.id() + " — " + message[:800])
        for test, reason in unexpected:
            annotation("error", "NOW unexpected test skip", test + " — " + reason)
        annotation("notice", "NOW source results", json.dumps({key: report[key] for key in
                   ("system", "python_version", "source_sha", "tests_run", "passed", "failures", "errors", "status")}))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    return run(parser.parse_args().report)


if __name__ == "__main__":
    raise SystemExit(main())
