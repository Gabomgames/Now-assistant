"""Expose measured Windows evidence in Actions Summary without credentials/private data."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    directory = parser.parse_args().directory
    report_path, tests_path = directory / "BUILD-VALIDACAO.json", directory / "source-tests.json"
    summary = {"packaged_build": "not_approved", "release_published": False}
    if tests_path.exists():
        tests = json.loads(tests_path.read_text(encoding="utf-8"))
        summary.update(source_sha=tests["source_sha"], unit_tests={key: tests[key] for key in
            ("system", "python_version", "tests_run", "passed", "failures", "errors", "skipped", "status")})
        summary["failed_tests"] = tests.get("failed_tests", [])
        summary["error_tests"] = tests.get("error_tests", [])
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        smoke = report["packaged_smoke"]
        summary.update(packaged_build="actual_windows_smoke_passed", version=report["version"],
            source_sha=report["source_sha"], release_eligible=report["release_eligible"],
            diagnostic_only=report["diagnostic_only"], branding=report["branding"],
            executable_sha256=report["executable_sha256"], frozen_executable=smoke["frozen_executable"],
            qt_platform=smoke["qt_platform"], actual_offline_commands=len(smoke["offline_commands"]),
            weights_included=False, model_inference_tested=False, digital_signature=report["digital_signature"])
    checksum = directory / "SHA256SUMS.txt"
    if checksum.exists():
        summary["zip_sha256"] = checksum.read_text(encoding="utf-8").strip()
    text = "## NOW Assistant — actual build evidence\n\n```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
            stream.write(text)
    print(text)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        data = json.dumps(summary, ensure_ascii=True).replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
        print("::notice title=NOW actual distribution results::" + data)


if __name__ == "__main__":
    main()
