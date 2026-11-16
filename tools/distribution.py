"""Shared, fail-closed Windows artifact checks. No publishing side effects."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile


@dataclass(frozen=True)
class Version:
    value: str
    major: int
    minor: int
    patch: int
    prerelease: str | None

    @property
    def experimental(self):
        return self.major == 0 or self.prerelease is not None

    @property
    def tag(self):
        return "v" + self.value


def parse_version(value):
    if not isinstance(value, str):
        raise ValueError("version must be a SemVer string")
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?", value)
    if not match or len(value) > 80:
        raise ValueError("invalid semantic version")
    prerelease = match[4]
    if prerelease and any(part.isdigit() and len(part) > 1 and part.startswith("0") for part in prerelease.split(".")):
        raise ValueError("numeric prerelease identifiers must not have leading zeros")
    return Version(value, int(match[1]), int(match[2]), int(match[3]), prerelease)


def valid_sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("a full lowercase Git commit SHA is required")
    return value


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_path(value):
    path = PurePosixPath(value)
    if (not value or "\\" in value or ":" in value or path.is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("unsafe artifact path")
    return path


def private_file_reason(name, prefix=b"", text=b""):
    path = PurePosixPath(name)
    lowered = path.name.lower()
    if (lowered == ".env" or lowered.startswith(".env.") or lowered.endswith((".sqlite3", ".sqlite", ".db", ".pfx", ".p12", ".key"))
            or any(part.lower() in {".git", ".aws", ".ssh", "user-memory", "user-data"} for part in path.parts)
            or prefix.startswith(b"SQLite format 3\x00")):
        return "private file or database"
    patterns = (
        rb"AIza[0-9A-Za-z_-]{35}", rb"\bgh[pousr]_[A-Za-z0-9]{30,}",
        rb"\bsk-[A-Za-z0-9]{35,}",
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{64,}-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        return "credential pattern"
    return None


TEXT_EXTENSIONS = {".json", ".md", ".txt", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".pem", ".log", ".py", ".xml"}


def inventory(directory):
    directory = Path(directory)
    entries = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlinks are not allowed in the portable bundle")
        if not path.is_file() or path == directory / "BUILD-VALIDACAO.json":
            continue
        name = path.relative_to(directory).as_posix()
        safe_path(name)
        with path.open("rb") as stream:
            prefix = stream.read(16)
        text = path.read_bytes() if path.suffix.lower() in TEXT_EXTENSIONS else b""
        if private_file_reason(name, prefix, text):
            raise ValueError("private content rejected: " + name)
        entries.append({"path": name, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def branding_receipt(root):
    directory = Path(root) / "assets/branding"
    data = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if data.get("status") != "imported_official_asset":
        return {"status": "missing_original", "verified": False}
    required = ("original", "display_asset", "windows_icon")
    for key in required:
        path = directory.joinpath(*safe_path(data[key]).parts)
        if not path.is_file() or path.is_symlink():
            raise ValueError("missing or unsafe branding asset")
    original = directory / data["original"]
    if sha256_file(original) != data["original_sha256"]:
        raise ValueError("official original does not match its receipt")
    icon = directory / data["windows_icon"]
    display = directory / data["display_asset"]
    return {"status": "official_original_verified", "verified": True,
            "original": data["original"], "original_sha256": data["original_sha256"],
            "icon_sha256": sha256_file(icon), "display_sha256": sha256_file(display)}


def validate_evidence(report, *, require_publishable=True):
    version = parse_version(report["version"])
    valid_sha(report["source_sha"])
    if report.get("schema") != "now-windows-candidate-v1" or report.get("source_dirty") is not False:
        raise ValueError("unknown evidence format or dirty source")
    if report.get("tag") != version.tag or report.get("experimental") != version.experimental:
        raise ValueError("tag or experimental status differs from SemVer")
    tests, smoke = report["unit_tests"], report["packaged_smoke"]
    if (tests["status"] != "passed" or tests["system"] != "Windows"
            or not tests["python_version"].startswith("3.12.") or tests["source_sha"] != report["source_sha"]
            or tests["failures"] or tests["errors"] or tests["unexpected_skips"]
            or tests["real_gui_tests_passed"] < 9 or tests["real_http_tests_passed"] < 6):
        raise ValueError("Windows source tests were not approved")
    if (smoke.get("system") != "Windows" or smoke.get("qt_platform") != "windows"
            or smoke.get("frozen_executable") is not True or smoke.get("python_bits") != 64
            or not smoke.get("python_version", "").startswith("3.12.") or smoke.get("version") != version.value
            or smoke.get("real_gui_and_http_engine") is not True or smoke.get("mocked_responses") is not False
            or smoke.get("temporary_session_created_database") is not False):
        raise ValueError("real frozen Windows GUI/Engine smoke is required")
    commands = smoke.get("offline_commands", [])
    expected = {("pt-BR", "oi"), ("pt-BR", "horas"), ("pt-BR", "data"),
                ("en-US", "hello"), ("en-US", "time"), ("en-US", "date")}
    if (len(commands) != 6 or {(row["language"], row["input"]) for row in commands} != expected
            or any(row.get("provider") != "offline" or not row.get("output", "").strip() for row in commands)):
        raise ValueError("six actual bilingual offline replies are required")
    if require_publishable and (report.get("release_eligible") is not True
            or report.get("branding", {}).get("verified") is not True
            or report.get("branding_review_confirmed") is not True
            or report.get("pe_icon_resource_present") is not True
            or smoke.get("official_logo_loaded") is not True):
        raise ValueError("diagnostic/unbranded builds cannot be published")
    return version


def verify_archive(archive, *, version=None, source_sha=None, require_publishable=True):
    """Inspect without extracting; protect both the publication gate and Windows unzip."""
    with zipfile.ZipFile(archive) as bundle:
        entries = {}
        normalized = set()
        total = 0
        for item in bundle.infolist():
            path = safe_path(item.filename.rstrip("/") if item.is_dir() else item.filename)
            if not path.parts or path.parts[0] != "NOW-Assistant" or len(path.parts) < 2:
                if item.is_dir() and path.parts == ("NOW-Assistant",):
                    continue
                raise ValueError("ZIP must contain a single NOW-Assistant folder")
            if item.is_dir():
                continue
            relative = "/".join(path.parts[1:])
            if relative.casefold() in normalized or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("duplicate or symbolic ZIP entry")
            normalized.add(relative.casefold())
            total += item.file_size
            if total > 2 * 1024**3 or item.file_size > 512 * 1024**2:
                raise ValueError("artifact size exceeds release limits")
            entries[relative] = item
        if bundle.testzip() is not None:
            raise ValueError("ZIP CRC failed")
        required = {"NOW-Assistant.exe", "BUILD-VALIDACAO.json", "LEIA-ME.md", "CHANGELOG.md",
                    "LICENSES/DEPENDENCIES.json", "LICENSES/Python/LICENSE.txt", "LICENSES/Qt/LGPL-3.0-only.txt"}
        if not required.issubset(entries) or entries["BUILD-VALIDACAO.json"].file_size > 8 * 1024**2:
            raise ValueError("bundle is missing required runtime documentation/evidence")
        report = json.loads(bundle.read(entries["BUILD-VALIDACAO.json"]))
        parsed = validate_evidence(report, require_publishable=require_publishable)
        if version is not None and parsed.value != version:
            raise ValueError("artifact version differs from the authorized version")
        if source_sha is not None and report["source_sha"] != valid_sha(source_sha):
            raise ValueError("artifact source differs from the authorized commit")
        recorded = {entry["path"]: entry for entry in report["files"]}
        if len(recorded) != len(report["files"]) or set(recorded) != set(entries) - {"BUILD-VALIDACAO.json"}:
            raise ValueError("artifact inventory differs from its contents")
        if report["executable_sha256"] != recorded["NOW-Assistant.exe"]["sha256"]:
            raise ValueError("executable fingerprint differs from packaged smoke evidence")
        for name, item in entries.items():
            if PurePosixPath(name).suffix.lower() in TEXT_EXTENSIONS and item.file_size > 16 * 1024**2:
                raise ValueError("text resource exceeds inspection limit")
            text = bundle.read(item) if PurePosixPath(name).suffix.lower() in TEXT_EXTENSIONS else b""
            digest = hashlib.sha256()
            with bundle.open(item) as stream:
                prefix = stream.read(16)
                digest.update(prefix)
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if private_file_reason(name, prefix, text):
                raise ValueError("private content rejected from artifact")
            if name in recorded and (digest.hexdigest() != recorded[name]["sha256"] or item.file_size != recorded[name]["bytes"]):
                raise ValueError("artifact file failed its SHA-256/size verification")
        return report
