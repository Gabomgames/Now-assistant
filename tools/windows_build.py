"""Build and test a portable Windows application; never create a GitHub Release."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from now_desktop.version import VERSION
from tools.collect_licenses import collect
from tools.distribution import (branding_receipt, inventory, parse_version, sha256_file,
                                validate_evidence, verify_archive)

ROOT = Path(__file__).resolve().parents[1]


def version_resource(version, path):
    number = (version.major, version.minor, version.patch, 0)
    if any(part > 65535 for part in number):
        raise ValueError("Windows file version fields must fit in 16 bits")
    path.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={number!r}, prodvers={number!r}, mask=0x3f,
    flags=0x2 if {version.experimental!r} else 0, OS=0x40004, fileType=0x1, subtype=0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'NOW Assistant'),
    StringStruct('FileVersion', {version.value!r}), StringStruct('ProductVersion', {version.value!r}),
    StringStruct('ProductName', 'NOW Assistant'), StringStruct('OriginalFilename', 'NOW-Assistant.exe')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
""", encoding="utf-8")


def build(args):
    if os.name != "nt" or platform.system() != "Windows" or sys.maxsize <= 2**32 or sys.version_info[:2] != (3, 12):
        raise ValueError("Build requires real Windows x64 and Python 3.12; Linux cannot validate this executable.")
    version = parse_version(VERSION)
    if args.version and args.version != version.value:
        raise ValueError("requested version must match now_desktop/version.py")
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("build source must be committed and clean; preserve local changes first")
    branding = branding_receipt(ROOT)
    if not args.diagnostic_build and (not branding["verified"] or not args.branding_reviewed):
        raise ValueError("Import the original official logo, inspect icons, then confirm --branding-reviewed. No Alpha is approved without it.")
    if args.branding_reviewed and not branding["verified"]:
        raise ValueError("a missing original cannot be confirmed as reviewed")
    environment = {**os.environ, "ENABLE_GEMINI_FALLBACK": "false", "PYTHONIOENCODING": "utf-8"}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tests = output / "source-tests.json"
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, env=environment, check=True)
    subprocess.run([sys.executable, str(ROOT / "tools/run_tests.py"), "--report", str(tests)], cwd=ROOT,
                   env=environment, check=True)
    with tempfile.TemporaryDirectory(prefix="now-assistant-build-") as temporary:
        temp = Path(temporary)
        resource = temp / "version-info.txt"
        version_resource(version, resource)
        command = [
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed", "--noupx",
            "--name", "NOW-Assistant", "--paths", str(ROOT), "--version-file", str(resource),
            "--collect-submodules", "uvicorn", "--copy-metadata", "PySide6_Essentials",
            "--copy-metadata", "shiboken6", "--add-data", f"{ROOT / 'assets/branding'}{os.pathsep}assets/branding",
            "--distpath", str(output / "dist"), "--workpath", str(temp / "work"), "--specpath", str(temp),
        ]
        if branding["verified"]:
            manifest = json.loads((ROOT / "assets/branding/manifest.json").read_text(encoding="utf-8"))
            command.extend(["--icon", str(ROOT / "assets/branding" / manifest["windows_icon"])])
        else:
            command.extend(["--icon", "NONE"])  # diagnostic is explicitly unbranded, never a substitute logo
        command.append(str(ROOT / "packaging/desktop/entry.py"))
        subprocess.run(command, cwd=ROOT, env=environment, check=True)
    bundle = output / "dist/NOW-Assistant"
    executable = bundle / "NOW-Assistant.exe"
    smoke = output / "packaged-smoke"
    subprocess.run([str(executable), "--smoke-output", str(smoke)], cwd=bundle, env=environment,
                   timeout=120, check=True)
    shutil.copy2(ROOT / "packaging/releases/INSTALL-WINDOWS.md", bundle / "LEIA-ME.md")
    shutil.copy2(ROOT / "packaging/releases" / (version.value + ".md"), bundle / "CHANGELOG.md")
    shutil.copytree(smoke, bundle / "validation")
    collect(bundle / "LICENSES")
    from pefile import PE, RESOURCE_TYPE
    pe = PE(str(executable), fast_load=False)
    try:
        icons_present = any(entry.id == RESOURCE_TYPE["RT_GROUP_ICON"] for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries)
    finally:
        pe.close()
    if branding["verified"] and not icons_present:
        raise ValueError("the official icon was not embedded into the PE executable")
    report = {
        "schema": "now-windows-candidate-v1", "version": version.value, "tag": version.tag,
        "experimental": version.experimental, "source_sha": source, "source_dirty": False,
        "built_at_utc": datetime.now(timezone.utc).isoformat(), "build_system": platform.platform(),
        "branding": branding, "branding_review_confirmed": bool(args.branding_reviewed),
        "pe_icon_resource_present": icons_present, "executable_sha256": sha256_file(executable),
        "release_eligible": not args.diagnostic_build and branding["verified"] and args.branding_reviewed,
        "diagnostic_only": bool(args.diagnostic_build), "digital_signature": "not_signed",
        "unit_tests": json.loads(tests.read_text(encoding="utf-8")),
        "packaged_smoke": json.loads((smoke / "REAL-GUI-VALIDACAO.json").read_text(encoding="utf-8")),
        "ci": {"provider": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local_windows",
               "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
               "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"), "event": os.environ.get("GITHUB_EVENT_NAME")},
        "manual_windows_10_hardware_accessibility_acl": "pending",
        "ollama_and_weights_included": False, "model_inference_tested": False, "physical_audio_tested": False,
        "private_file_scan": "passed", "files": inventory(bundle),
    }
    validate_evidence(report, require_publishable=not args.diagnostic_build)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (bundle / "BUILD-VALIDACAO.json").write_text(encoded, encoding="utf-8")
    suffix = "-diagnostic" if args.diagnostic_build else ""
    basename = f"NOW-Assistant-{version.value}{suffix}-Windows-x64"
    archive = Path(shutil.make_archive(str(output / basename), "zip", bundle.parent, bundle.name))
    verify_archive(archive, version=version.value, source_sha=source, require_publishable=not args.diagnostic_build)
    (output / "BUILD-VALIDACAO.json").write_text(encoded, encoding="utf-8")
    shutil.copy2(bundle / "CHANGELOG.md", output / "RELEASE-NOTES.md")
    (output / "SHA256SUMS.txt").write_text(f"{sha256_file(archive)}  {archive.name}\n", encoding="utf-8")
    print("Actual Windows packaged GUI + Engine checks passed:", archive)
    print("Release eligible:", report["release_eligible"], "— no GitHub Release was created.")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "release/desktop" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    parser.add_argument("--version", help="must match the committed product version")
    parser.add_argument("--branding-reviewed", action="store_true", help="confirm visual inspection of the original and its derived icons")
    parser.add_argument("--diagnostic-build", action="store_true", help="internal packaging test only; cannot be published by the release pipeline")
    args = parser.parse_args(argv)
    try:
        build(args)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            message = str(error).replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
            print("::error title=NOW Windows packaging::" + message[:1000])
        parser.exit(1, str(error) + "\n")
    return 0
