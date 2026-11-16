"""Import the user's official raster logo unchanged and make proportional icon sizes.

This tool never draws a logo or removes its background. Inspect the generated icons
before a release; small sizes may lose detail present in a raster source.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 24, 32, 48, 64, 128, 192, 256, 512)


def import_logo(source: Path, destination: Path) -> dict:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QImageReader, QPainter

    source, destination = source.resolve(), destination.resolve()
    if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("provide the original PNG, JPEG or WebP; SVG needs a separately reviewed renderer")
    if not source.is_file() or source.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("logo must be a file of at most 32 MiB")
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous.get("status") == "imported_official_asset":
            if previous.get("original_sha256") != digest:
                raise FileExistsError("an official logo is already imported; review replacement separately")
            original = destination / previous["original"]
            if hashlib.sha256(original.read_bytes()).hexdigest() != digest:
                raise ValueError("the preserved original no longer matches its receipt")
            return previous
    reader = QImageReader(str(source))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.width() <= 0 or size.height() <= 0 or size.width() * size.height() > 40_000_000:
        raise ValueError("invalid logo dimensions or image exceeds 40 megapixels")
    image = reader.read()
    if image.isNull():
        raise ValueError("unable to decode the original image")
    original_name = "original" + source.suffix.lower()
    destination.mkdir(parents=True, exist_ok=True)
    original = destination / original_name
    if original.exists() and original.read_bytes() != data:
        raise FileExistsError("refusing to overwrite a preserved original")
    if not original.exists():
        with original.open("xb") as stream:
            stream.write(data)
    icons = destination / "icons"
    icons.mkdir(exist_ok=True)
    for side in SIZES:
        scaled = image.scaled(side, side, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        canvas = QImage(side, side, QImage.Format.Format_ARGB32)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.drawImage((side - scaled.width()) // 2, (side - scaled.height()) // 2, scaled)
        painter.end()
        if not canvas.save(str(icons / f"now-{side}.png"), "PNG"):
            raise OSError("unable to save a derived icon")
    # Windows ICO supports embedded PNG images, keeping all source colours/alpha.
    frames = [(side, (icons / f"now-{side}.png").read_bytes()) for side in SIZES if side <= 256]
    offset = 6 + 16 * len(frames)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    for side, encoded in frames:
        directory.extend(struct.pack("<BBBBHHII", side % 256, side % 256, 0, 0, 1, 32, len(encoded), offset))
        offset += len(encoded)
    (icons / "now.ico").write_bytes(bytes(directory) + b"".join(encoded for _, encoded in frames))
    receipt = {
        "status": "imported_official_asset", "brand": "NOW Assistant", "original": original_name,
        "original_sha256": digest, "source_dimensions": [image.width(), image.height()],
        "display_asset": "icons/now-128.png", "windows_icon": "icons/now.ico", "sizes": list(SIZES),
        "transform": "proportional resize and transparent padding only; original background preserved",
        "visual_review": "required_before_release", "vector": False,
    }
    temporary = destination / "manifest.pending.json"
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(manifest_path)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/branding")
    args = parser.parse_args(argv)
    try:
        receipt = import_logo(args.source, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
