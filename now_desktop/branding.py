"""Load only the provided official asset; never draw or generate a substitute logo."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "assets/branding"


def _asset_path(key):
    manifest = ROOT / "manifest.json"
    if not manifest.exists():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("status") != "imported_official_asset":
            return None
        candidate = (ROOT / data[key]).resolve()
        if candidate.is_relative_to(ROOT.resolve()) and candidate.is_file():
            return candidate
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return None


def logo_path():
    return _asset_path("display_asset")


def window_icon_path():
    """Use all native ICO resolutions for Windows chrome/taskbar and DPI scaling."""
    return _asset_path("windows_icon") or logo_path()
