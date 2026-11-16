"""Build and smoke-test a Windows executable on a real Windows x64 Python 3.12 runner."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "release" / "windows")
    args = parser.parse_args(argv)
    if os.name != "nt" or sys.maxsize <= 2**32 or sys.version_info[:2] != (3, 12):
        parser.error("Build requires Windows x64 and Python 3.12; PyInstaller cannot cross-compile from Linux.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output.resolve() / stamp
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="now-ai-build-") as temporary:
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--console", "--noupx",
            "--name", "NOW-AI", "--paths", str(ROOT), "--collect-submodules", "uvicorn",
            "--distpath", str(output), "--workpath", str(Path(temporary) / "work"),
            "--specpath", temporary, str(ROOT / "packaging" / "windows" / "entry.py"),
        ], cwd=ROOT, check=True)
    bundle = output / "NOW-AI"
    executable = bundle / "NOW-AI.exe"
    shutil.copy2(ROOT / ".env.example", bundle / ".env.example")
    shutil.copy2(ROOT / "docs" / "WINDOWS_VSCODE.md", bundle / "LEIA-ME-WINDOWS.md")
    shutil.copy2(ROOT / "README.md", bundle / "README-ORIGINAL.md")
    environment = {**os.environ, "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}
    terminal = subprocess.run(
        [str(executable)], input="ajuda\nsair\n", cwd=bundle, env=environment,
        text=True, encoding="utf-8", capture_output=True, timeout=30, check=True,
    )
    if "NOW [offline]:" not in terminal.stdout or "Comandos offline" not in terminal.stdout:
        raise RuntimeError("Packaged CLI smoke test failed: " + terminal.stdout)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    log = output / "packaged-api-smoke.log"
    with log.open("w", encoding="utf-8") as stream:
        server = subprocess.Popen([str(executable), "--api", "--port", str(port)], cwd=bundle, env=environment, stdout=stream, stderr=stream)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError(f"Packaged API exited; inspect {log}")
                try:
                    with urlopen(base + "/health", timeout=1) as response:
                        health = json.load(response)
                    break
                except (URLError, TimeoutError):
                    time.sleep(0.5)
            else:
                raise RuntimeError(f"Packaged API startup timed out; inspect {log}")
            if health != {"status": "ok", "engine": "NOW AI", "version": "0.2.0"}:
                raise RuntimeError("Unexpected packaged API health response")
            request = Request(base + "/v1/chat", data=b'{"message":"oi"}', headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=5) as response:
                answer = json.load(response)
            if answer.get("provider") != "offline" or "NOW" not in answer.get("reply", ""):
                raise RuntimeError("Packaged API offline request failed")
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
    report = {
        "platform": platform.platform(), "python": sys.version, "built_at_utc": stamp,
        "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "packaged_cli_offline": "passed", "packaged_api_health": "passed", "packaged_api_offline": "passed",
        "packaged_model_conversations": "not_tested_by_build_script_run_tools_validate_local_afterwards",
    }
    (bundle / "BUILD-VALIDACAO.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = shutil.make_archive(str(output / "NOW-AI-0.2-Windows-x64"), "zip", output, "NOW-AI")
    print("Executable:", executable)
    print("ZIP:", archive)
    print("Offline executable checks passed. Run tools/validate_local.py with --cli-executable for actual model validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
