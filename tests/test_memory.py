import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest

from now_memory import ConsentRequired, IntegrityError, MemoryStore, UnlockError
from now_memory.store import DATABASE

PASSWORD = "test-only-memory-passphrase-2026"
ROOT = Path(__file__).resolve().parents[1]


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "vault"
        self.store = MemoryStore.create(self.directory, PASSWORD, consent=True)
        self.addCleanup(self.store.close)

    def test_status_and_opt_in_do_not_create_an_unapproved_vault(self):
        path = Path(self.temporary.name) / "not-created"
        self.assertFalse(MemoryStore.status(path)["initialized"])
        with self.assertRaises(ConsentRequired):
            MemoryStore.create(path, PASSWORD)
        self.assertFalse(path.exists())

    def test_cli_without_opt_in_never_requests_a_password_or_creates_storage(self):
        path = Path(self.temporary.name) / "not-created"
        result = subprocess.run([sys.executable, "-m", "now_memory", "--directory", str(path), "init"],
                                cwd=ROOT, input="", text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--consent", result.stdout)
        self.assertNotIn("Memory passphrase", result.stderr)
        self.assertFalse(path.exists())

    def test_encrypted_persistence_and_no_plaintext_secret_in_database(self):
        marker = "private-test-name-82938"
        self.store.set_preferences({"display_name": marker, "language": "en-US", "humor": 2})
        with MemoryStore.open(self.directory, PASSWORD) as reopened:
            self.assertEqual(reopened.get_preferences(), {"display_name": marker, "humor": 2, "language": "en-US"})
        raw = (self.directory / DATABASE).read_bytes()
        self.assertNotIn(marker.encode(), raw)
        self.assertNotIn(PASSWORD.encode(), raw)
        self.assertIsNone(MemoryStore.status(self.directory)["enabled"])

    def test_wrong_password_does_not_destroy_or_modify_data(self):
        self.store.set_preferences({"persona": "casual"})
        before = hashlib.sha256((self.directory / DATABASE).read_bytes()).hexdigest()
        with self.assertRaises(UnlockError):
            MemoryStore.open(self.directory, "wrong-test-passphrase-2026")
        self.assertEqual(self.store.get_preferences()["persona"], "casual")
        self.assertEqual(before, hashlib.sha256((self.directory / DATABASE).read_bytes()).hexdigest())

    def test_tampered_ciphertext_fails_authentication(self):
        self.store.set_preferences({"display_name": "test name"})
        with sqlite3.connect(self.directory / DATABASE) as connection:
            original = connection.execute("SELECT encrypted FROM preferences").fetchone()[0]
            connection.execute("UPDATE preferences SET encrypted=?", (original[:-1] + bytes([original[-1] ^ 1]),))
        with self.assertRaises(IntegrityError):
            self.store.get_preferences()
        self.store.delete("display_name")
        self.assertEqual(self.store.get_preferences(), {})

    def test_ciphertexts_cannot_be_swapped_between_preferences(self):
        self.store.set_preferences({"persona": "casual", "language": "en-US"})
        with sqlite3.connect(self.directory / DATABASE) as connection:
            values = dict(connection.execute("SELECT name, encrypted FROM preferences"))
            connection.execute("UPDATE preferences SET encrypted=? WHERE name='persona'", (values["language"],))
        with self.assertRaises(IntegrityError):
            self.store.get_preferences()

    def test_persisted_consent_state_is_authenticated(self):
        with sqlite3.connect(self.directory / DATABASE) as connection:
            connection.execute("UPDATE metadata SET value=? WHERE name='enabled'", (b"1",))
        with self.assertRaises(IntegrityError):
            self.store.get_preferences()

    def test_invalid_batch_is_atomic_and_capture_permissions_are_not_preferences(self):
        self.store.set_preferences({"humor": 1})
        for invalid in ({"humor": 2, "voice_rate": float("nan")}, {"microphone": True}, {"humor": True}):
            with self.assertRaises(ValueError):
                self.store.set_preferences(invalid)
        self.assertEqual(self.store.get_preferences(), {"humor": 1})

    def test_disabled_memory_blocks_automatic_use_but_allows_privacy_controls(self):
        self.store.set_preferences({"language": "en-US"})
        self.store.disable()
        with self.assertRaises(ConsentRequired):
            self.store.get_preferences()
        with self.assertRaises(ConsentRequired):
            self.store.set_preferences({"humor": 0})
        self.assertEqual(self.store.export_preferences()["preferences"], {"language": "en-US"})
        self.store.delete("language")
        with self.assertRaises(ConsentRequired):
            self.store.enable()
        self.store.enable(consent=True)
        self.assertEqual(self.store.get_preferences(), {})

    def test_delete_and_clear_remove_records_and_compact_the_database(self):
        self.store.set_preferences({"display_name": "remove me", "persona": "focus"})
        with sqlite3.connect(self.directory / DATABASE) as connection:
            encrypted = connection.execute("SELECT encrypted FROM preferences WHERE name='display_name'").fetchone()[0]
        self.store.delete("display_name")
        self.assertEqual(self.store.get_preferences(), {"persona": "focus"})
        self.assertNotIn(encrypted, (self.directory / DATABASE).read_bytes())
        self.store.clear()
        self.assertEqual(self.store.export_preferences()["preferences"], {})

    def test_creating_again_never_overwrites_an_existing_vault(self):
        self.store.set_preferences({"display_name": "preserved"})
        with self.assertRaises(FileExistsError):
            MemoryStore.create(self.directory, PASSWORD, consent=True)
        self.assertEqual(self.store.get_preferences()["display_name"], "preserved")

    @unittest.skipUnless(os.name == "posix", "POSIX permission check")
    def test_vault_permissions_are_owner_only(self):
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.directory / DATABASE).stat().st_mode), 0o600)

    def test_cli_export_is_explicit_private_and_never_overwrites(self):
        self.store.set_preferences({"persona": "casual"})
        output = Path(self.temporary.name) / "export.json"
        command = [sys.executable, "-m", "now_memory", "--directory", str(self.directory), "--password-env", "NOW_TEST_MEMORY_PASSWORD", "export", "--output", str(output)]
        environment = {**os.environ, "NOW_TEST_MEMORY_PASSWORD": PASSWORD}
        first = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=20)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(output.read_text())["preferences"], {"persona": "casual"})
        before = output.read_bytes()
        second = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, timeout=20)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(output.read_bytes(), before)
        self.assertNotIn(PASSWORD, first.stdout + first.stderr + second.stdout + second.stderr)

    def test_saved_preferences_personalize_the_new_offline_text_path(self):
        from now_engine.assistant import LocalAssistant
        from now_voice import VoiceSession, VoiceSettings
        self.store.set_preferences({"display_name": "Demo", "language": "en-US", "humor": 2, "voice_rate": 1.1})
        settings = VoiceSettings.from_preferences(self.store.get_preferences())
        session = VoiceSession(LocalAssistant(), settings=settings)
        session.enable()
        result = session.respond_text("hello")
        self.assertEqual(result.reply.provider, "offline")
        self.assertIn("Hi, Demo", result.reply.text)
        self.assertEqual(result.speech_plan.language, "en-US")
        self.assertEqual(result.speech_plan.segments[0].rate, 1.1)
        self.assertFalse(result.playback_completed)


if __name__ == "__main__":
    unittest.main()
