"""Validator/client contracts only; no inference is performed by these tests."""
from io import BytesIO
import json
import tempfile
from pathlib import Path
import unittest

from now_brain.client import Client
from now_brain.provider import BrainError, OllamaProvider, valid_model
from tools.validate_brain_api import percentiles, evaluate, ROOT


class BrainValidatorTests(unittest.TestCase):
    def test_twenty_original_cases_cover_context_languages_and_minecraft(self):
        plan = json.loads((ROOT / "validation/brain-v5-cases.json").read_text())
        cases = plan["cases"]
        self.assertEqual(len(cases), 20)
        self.assertFalse(plan["training_allowed"])
        self.assertEqual(len({row["id"] for row in cases}), 20)
        self.assertEqual(sum(row.get("conversation") == "plan" for row in cases), 5)
        self.assertEqual({row["language"] for row in cases}, {"pt-BR", "en-US"})
        self.assertEqual({row["length"] for row in cases}, {"short", "balanced", "detailed"})
        self.assertTrue(any("Minecraft" in row["prompt"] for row in cases))

    def test_percentile_report_has_no_numbers_without_observations(self):
        self.assertIsNone(percentiles([])["p95_ms"])
        result = percentiles([4, 1, 3, 2])
        self.assertEqual(result["samples"], 4)
        self.assertEqual(result["p50_ms"], 2)
        self.assertEqual(result["p95_ms"], 4)

    def test_client_rejects_remote_urls_and_preserves_unicode_events(self):
        for url in ("https://external.invalid", "http://127.0.0.1:8000/path", "http://user@127.0.0.1:8000"):
            with self.assertRaises(ValueError):
                Client(url, "not-a-secret")
            with self.assertRaises(ValueError):
                OllamaProvider(endpoint=url)
        raw = BytesIO('event: delta\ndata: {"text":"Olá"}\n\nevent: done\ndata: {"status":"completed"}\n\n'.encode())
        self.assertEqual(list(Client.events(raw)), [("delta", {"text": "Olá"}), ("done", {"status": "completed"})])
        with self.assertRaises(ValueError):
            list(Client.events(BytesIO(b"x" * 131073 + b"\n")))

    def test_evaluation_refuses_to_overwrite_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "keep.txt"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                evaluate(Path(directory), ["qwen2.5:0.5b"], 1)
            self.assertEqual(marker.read_text(), "preserve")

    def test_remote_cloud_tags_are_rejected_before_opening_api(self):
        for model in ("qwen:CLOUD", "https://host/model", "", "has spaces"):
            with self.assertRaises(BrainError):
                valid_model(model)
