"""Load only the provided official asset; never draw or generate a substitute logo."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "assets/branding"


def logo_path():
    manifest = ROOT / "manifest.json"
    if not manifest.exists():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("status") != "imported_official_asset":
            return None
        candidate = (ROOT / data["display_asset"]).resolve()
        if candidate.is_relative_to(ROOT.resolve()) and candidate.is_file():
            return candidate
    except (ValueError, KeyError, TypeError):
        return None
    return None
