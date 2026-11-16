"""Image pipeline tests use synthetic coloured rectangles, never substitute brand assets."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

try:
    from PySide6.QtGui import QColor, QImage
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from tools.import_branding import import_logo


@unittest.skipUnless(QT_AVAILABLE, "requires requirements-desktop.txt")
class BrandingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "synthetic-test-fixture.png"
        image = QImage(200, 100, QImage.Format.Format_ARGB32)
        image.fill(QColor("#0066cc"))
        self.assertTrue(image.save(str(self.source)))
        self.output = self.root / "branding"

    def tearDown(self):
        self.temporary.cleanup()

    def test_original_is_exact_and_derived_icons_preserve_ratio_alpha_and_colour(self):
        original = self.source.read_bytes()
        receipt = import_logo(self.source, self.output)
        self.assertEqual((self.output / receipt["original"]).read_bytes(), original)
        self.assertEqual(receipt["original_sha256"], hashlib.sha256(original).hexdigest())
        image = QImage(str(self.output / "icons/now-128.png"))
        self.assertEqual((image.width(), image.height()), (128, 128))
        self.assertEqual(image.pixelColor(64, 0).alpha(), 0)
        self.assertEqual(image.pixelColor(64, 64), QColor("#0066cc"))
        icon = (self.output / "icons/now.ico").read_bytes()
        reserved, kind, count = struct.unpack_from("<HHH", icon)
        self.assertEqual((reserved, kind, count), (0, 1, 8))
        for index in range(count):
            size, offset = struct.unpack_from("<II", icon, 6 + index * 16 + 8)
            self.assertTrue(icon[offset:offset + size].startswith(b"\x89PNG\r\n\x1a\n"))

    def test_idempotent_import_and_replacement_refusal(self):
        first = import_logo(self.source, self.output)
        self.assertEqual(import_logo(self.source, self.output), first)
        changed = QImage(20, 20, QImage.Format.Format_ARGB32)
        changed.fill(QColor("#ff0000"))
        changed.save(str(self.source))
        with self.assertRaises(FileExistsError):
            import_logo(self.source, self.output)
        self.assertEqual(json.loads((self.output / "manifest.json").read_text()), first)

    def test_invalid_image_and_active_vector_content_are_rejected_without_asset_creation(self):
        self.source.write_bytes(b"invalid image")
        with self.assertRaises(ValueError):
            import_logo(self.source, self.output)
        svg = self.root / "untrusted.svg"
        svg.write_text('<svg><image href="https://example.invalid/private"/></svg>')
        with self.assertRaises(ValueError):
            import_logo(svg, self.output)
        self.assertFalse(self.output.exists())
