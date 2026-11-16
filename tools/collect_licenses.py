"""Collect installed-package licenses and hash-pinned upstream Qt/PySide notices."""
import hashlib
from importlib.metadata import distributions
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import urlopen
import zipfile

from tools.distribution import safe_path, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def notice_file(name):
    parts = name.lower().split("/")
    basename = parts[-1]
    return ("licenses" in parts or basename.startswith(("license", "copying", "copyright", "notice"))
            or basename in {"ftl.txt", "qt_attribution.json"}
            or ("3rdparty" in parts and basename.startswith(("readme", "legal"))))


def collect(destination, cache=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    packages = []
    for package in sorted(distributions(), key=lambda item: item.metadata["Name"].casefold()):
        name = package.metadata["Name"]
        folder = destination / "Python-packages" / name
        copied = []
        for file in package.files or ():
            if not notice_file(str(file)) or ".." in file.parts:
                continue
            original = package.locate_file(file)
            if original.is_file():
                target = folder.joinpath(*safe_path(str(file).replace("\\", "/")).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, target)
                copied.append(target.relative_to(destination).as_posix())
        packages.append({"name": name, "version": package.version,
                         "license_expression": package.metadata.get("License-Expression"),
                         "license_declaration": package.metadata.get("License"), "copied_notices": copied})
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        raise ValueError("Python's redistribution license was not found")
    (destination / "Python").mkdir()
    shutil.copyfile(python_license, destination / "Python/LICENSE.txt")
    sources = json.loads((ROOT / "packaging/desktop/license-sources.json").read_text(encoding="utf-8"))["sources"]
    cache = Path(cache or Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "now-license-sources")
    cache.mkdir(parents=True, exist_ok=True)
    for source in sources:
        archive = cache / (source["name"] + "-" + source["commit"] + ".zip")
        if not archive.exists() or sha256_file(archive) != source["sha256"]:
            temporary = archive.with_suffix(".partial")
            with urlopen(source["url"], timeout=90) as response, temporary.open("wb") as stream:
                received, digest = 0, hashlib.sha256()
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > 150 * 1024**2:
                        raise ValueError("license source archive exceeds size limit")
                    digest.update(chunk)
                    stream.write(chunk)
            if digest.hexdigest() != source["sha256"]:
                raise ValueError("license source archive failed SHA-256 verification")
            temporary.replace(archive)
        with zipfile.ZipFile(archive) as upstream:
            for item in upstream.infolist():
                if item.is_dir():
                    continue
                relative = "/".join(item.filename.split("/")[1:])
                if not notice_file(relative):
                    continue
                path = safe_path(relative)
                if item.file_size > 4 * 1024**2:
                    raise ValueError("license notice exceeds size limit")
                target = destination / "Qt/upstream" / source["name"] / Path(*path.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(upstream.read(item))
    for name in ("LGPL-3.0-only.txt", "GPL-3.0-only.txt"):
        shutil.copyfile(destination / "Qt/upstream/qtbase/LICENSES" / name, destination / "Qt" / name)
    shutil.copyfile(ROOT / "packaging/desktop/THIRD-PARTY.md", destination / "LEIA-ME.md")
    (destination / "DEPENDENCIES.json").write_text(json.dumps({
        "scope": "Isolated build environment metadata; some tools are not included in the runtime.",
        "packages": packages, "qt_pyside_source_notices": sources,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
