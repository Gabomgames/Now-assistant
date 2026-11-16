import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from training.scripts import run_ollama_eval as evaluation
from training.scripts import train_lora_gpu as training
from training.scripts.validate_dataset import ROOT, check_eval_file, check_file, check_separation


def example(prompt="Oi", completion="Olá"):
    return {"prompt": [{"role": "user", "content": prompt}],
            "completion": [{"role": "assistant", "content": completion}]}


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def write_rows(self, name, rows):
        path = self.directory / name
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return path

    def test_malformed_json_is_reported(self):
        path = self.directory / "bad.jsonl"
        path.write_text("{bad json}\n", encoding="utf-8")
        count, errors = check_file(path)
        self.assertEqual(count, 1)
        self.assertTrue(any("invalid JSON" in error for error in errors))

    def test_wrong_role_and_oversized_message_are_rejected(self):
        record = example(completion="x" * 2001)
        record["prompt"][0]["role"] = "system"
        errors = check_file(self.write_rows("bad.jsonl", [record]))[1]
        self.assertTrue(any("malformed prompt" in error for error in errors))
        self.assertTrue(any("malformed completion" in error for error in errors))

    def test_unicode_case_whitespace_and_punctuation_duplicates(self):
        path = self.write_rows("duplicate.jsonl", [example("ＯＩ,  NOW!"), example("oi now")])
        self.assertTrue(any("duplicate" in error for error in check_file(path)[1]))

    def test_unreadable_utf8_is_a_validation_error(self):
        path = self.directory / "invalid.jsonl"
        path.write_bytes(b"\xff\xfe")
        self.assertTrue(check_file(path)[1])

    def test_duplicate_eval_ids_are_rejected(self):
        row = {"id": "one", "language": "pt-BR", "category": "tone", "prompt": "Oi", "expected_behavior": "Resposta honesta"}
        errors = check_eval_file(self.write_rows("eval.jsonl", [row, {**row, "prompt": "Outro"}]))[1]
        self.assertTrue(any("duplicate evaluation id" in error for error in errors))

    def test_invalid_eval_language_is_rejected(self):
        row = {"id": "one", "language": "unknown", "category": "tone", "prompt": "Oi", "expected_behavior": "Resposta honesta"}
        self.assertTrue(check_eval_file(self.write_rows("eval.jsonl", [row]))[1])

    def test_train_eval_and_validation_leakage_is_rejected(self):
        train = self.write_rows("train.jsonl", [example("Oi, NOW!")])
        validation = self.write_rows("validation.jsonl", [example("oi now")])
        held_out = self.write_rows("eval.jsonl", [{"prompt": "OI NOW"}])
        errors = check_separation(train, held_out, validation)
        self.assertEqual(len(errors), 3)


class PreparationTests(unittest.TestCase):
    def test_seed_provenance_is_bound_to_original_data_and_unapproved(self):
        provenance = json.loads((ROOT / "data/PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["dataset_sha256"], hashlib.sha256((ROOT / "data/now_seed.jsonl").read_bytes()).hexdigest())
        self.assertIs(provenance["approved_for_training"], False)
        self.assertIsNone(provenance["license"])

    def test_training_dry_run_is_offline_and_does_not_import_gpu_libraries(self):
        before = {name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "trl", "peft", "datasets", "accelerate"}}
        capture = io.StringIO()
        with patch("socket.create_connection", side_effect=AssertionError("network forbidden")), contextlib.redirect_stdout(capture):
            result = training.main(["--dry-run"])
        after = {name for name in sys.modules if name.split(".")[0] in {"torch", "transformers", "trl", "peft", "datasets", "accelerate"}}
        plan = json.loads(capture.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(before, after)
        self.assertEqual(plan["train_records"], 36)
        self.assertFalse(plan["training_executed"])
        self.assertTrue(plan["local_files_only"])
        self.assertGreaterEqual(len(plan["training_blockers"]), 3)

    def test_real_training_is_refused_for_pilot_before_gpu_imports(self):
        with contextlib.redirect_stdout(io.StringIO()), patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
            self.assertEqual(training.main([]), 2)

    def test_provenance_checksum_mismatch_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "review.json"
            path.write_text(json.dumps({"dataset_sha256": "wrong", "approved_for_training": True}), encoding="utf-8")
            plan = training.build_plan(training.parse_args(["--dry-run", "--provenance", str(path)]))
        self.assertTrue(any("checksum" in error for error in plan["errors"]))

    def test_output_history_is_protected(self):
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing"
            existing.mkdir()
            marker = existing / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")
            plan = training.build_plan(training.parse_args(["--output", str(existing)]))
            self.assertTrue(any("already exists" in error for error in plan["training_blockers"]))
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")

    def test_evaluation_dry_run_has_no_model_calls_and_no_quality_claim(self):
        capture = io.StringIO()
        with patch.object(evaluation, "urlopen", side_effect=AssertionError("network forbidden")), contextlib.redirect_stdout(capture):
            self.assertEqual(evaluation.main(["--dry-run"]), 0)
        plan = json.loads(capture.getvalue())
        self.assertEqual(plan["cases_total"], 12)
        self.assertEqual(plan["generated"], 0)
        self.assertEqual(plan["not_run"], 12)
        self.assertEqual(plan["quality"], "NOT_SCORED")
        self.assertFalse(plan["inference_executed"])
        self.assertEqual(plan["expected_languages"]["en-langswitch"], "pt-BR")

    def test_existing_evaluation_output_is_not_overwritten_or_queried(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.jsonl"
            path.write_text("existing report", encoding="utf-8")
            with patch.object(evaluation, "urlopen", side_effect=AssertionError("network forbidden")), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluation.main(["--output", str(path)]), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "existing report")

    def test_cloud_tag_is_rejected(self):
        for tag in ("qwen3:cloud", "qwen3:CLOUD", "https://example.invalid/model"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                evaluation.load_plan(tag)


if __name__ == "__main__":
    unittest.main()
