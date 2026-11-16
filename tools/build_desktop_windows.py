"""Build NOW Assistant GUI on real Windows x64/Python 3.12 and run its real offline smoke.

Source runs are available before the official logo arrives. A branded release must
preserve the original logo and have its scaled icons visually reviewed first.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "release/desktop")
    parser.add_argument("--branding-reviewed", action="store_true", help="confirm that you inspected the official original and its derived icons")
    args = parser.parse_args(argv)
    if os.name != "nt" or sys.maxsize <= 2**32 or sys.version_info[:2] != (3, 12):
        parser.error("Build requires real Windows x64 and Python 3.12; Linux cannot validate this executable.")
    branding = ROOT / "assets/branding"
    receipt = json.loads((branding / "manifest.json").read_text(encoding="utf-8"))
    if receipt.get("status") != "imported_official_asset" or not args.branding_reviewed:
        parser.error("Import the official logo, inspect the icons, then pass --branding-reviewed.")
    original = (branding / receipt["original"]).resolve()
    icon = (branding / receipt["windows_icon"]).resolve()
    if not original.is_relative_to(branding.resolve()) or not icon.is_relative_to(branding.resolve()):
        parser.error("invalid branding asset path")
    if hashlib.sha256(original.read_bytes()).hexdigest() != receipt["original_sha256"] or not icon.is_file():
        parser.error("the preserved logo differs from its receipt or the icon is missing")
    environment = {**os.environ, "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, env=environment, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-v"], cwd=ROOT, env=environment, check=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output.resolve() / stamp
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="now-assistant-build-") as temporary:
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed", "--noupx",
            "--name", "NOW-Assistant", "--paths", str(ROOT), "--icon", str(icon),
            "--collect-submodules", "uvicorn", "--copy-metadata", "PySide6_Essentials",
            "--copy-metadata", "shiboken6", "--add-data", f"{branding}{os.pathsep}assets/branding",
            "--distpath", str(output), "--workpath", str(Path(temporary) / "work"),
            "--specpath", temporary, str(ROOT / "packaging/desktop/entry.py"),
        ], cwd=ROOT, env=environment, check=True)
    bundle = output / "NOW-Assistant"
    executable = bundle / "NOW-Assistant.exe"
    smoke = output / "packaged-real-gui-checks"
    subprocess.run([str(executable), "--smoke-output", str(smoke)], cwd=bundle, env=environment,
                   timeout=90, check=True)
    results = json.loads((smoke / "REAL-GUI-VALIDACAO.json").read_text(encoding="utf-8"))
    if not results["official_logo_loaded"] or len(results["offline_commands"]) != 6:
        raise RuntimeError("packaged GUI/Engine/branding smoke failed")
    shutil.copy2(ROOT / "docs/DESKTOP_WINDOWS.md", bundle / "LEIA-ME.md")
    shutil.copy2(ROOT / "docs/DESKTOP_ARCHITECTURE.md", bundle / "ARQUITETURA.md")
    shutil.copytree(smoke, bundle / "validation")
    (bundle / "BUILD-VALIDACAO.json").write_text(json.dumps({
        "built_at_utc": stamp, "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "offline_gui_smoke": "passed", "manual_windows_usability": "pending",
        "windows_10_hardware_target": "pending", "qwen_inference": "not_tested_by_this_build",
        "audio_wake_word": "not_implemented", "digital_signature": "not_signed",
    }, indent=2) + "\n", encoding="utf-8")
    print(shutil.make_archive(str(output / "NOW-Assistant-Windows-x64"), "zip", output, "NOW-Assistant"))
    print("Complete manual Windows, accessibility and license review before distributing a release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
