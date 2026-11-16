from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from now_history import HistoryStore, new_conversation
from now_memory import ConsentRequired, IntegrityError, MemoryStore, UnlockError

PASSWORD = "history-test-only-passphrase-2026"


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "history"
        self.store = HistoryStore.create(self.directory, PASSWORD, consent=True)
        self.addCleanup(self.store.close)

    def test_no_implicit_history_or_temporary_session_persistence(self):
        path = Path(self.temporary.name) / "not-created"
        with self.assertRaises(ConsentRequired):
            HistoryStore.create(path, PASSWORD)
        self.assertFalse(path.exists())
        with self.assertRaises(ConsentRequired):
            self.store.save(new_conversation().append("user", "temporary only"))
        self.assertEqual(self.store.list_conversations(), [])

    def test_encrypted_roundtrip_search_rename_and_export(self):
        conversation = self.store.create_conversation("private-history-title-7732")
        conversation = conversation.append("user", "unique-private-message-8826").append("assistant", "Actual fixture data, not a model response", provider="offline")
        self.store.save(conversation)
        self.assertEqual(self.store.list_conversations("message-8826")[0]["id"], conversation.id)
        renamed = self.store.rename(conversation.id, "private-renamed-title-4482")
        with HistoryStore.open(self.directory, PASSWORD) as reopened:
            self.assertEqual(reopened.get(conversation.id), renamed)
        raw = (self.directory / "history.sqlite3").read_bytes()
        self.assertNotIn(b"private-renamed-title-4482", raw)
        self.assertNotIn(b"unique-private-message-8826", raw)
        output = Path(self.temporary.name) / "export.json"
        self.store.export(conversation.id, output)
        self.assertEqual(json.loads(output.read_text())["conversation"]["id"], conversation.id)
        with self.assertRaises(FileExistsError):
            self.store.export(conversation.id, output)

    def test_history_is_separate_from_preferences_and_wrong_password_preserves_data(self):
        conversation = self.store.create_conversation()
        self.store.save(conversation.append("user", "stored test message"))
        with self.assertRaises(UnlockError):
            HistoryStore.open(self.directory, "wrong-history-test-passphrase")
        self.assertEqual(len(self.store.get(conversation.id).messages), 1)
        with self.assertRaises(FileNotFoundError):
            MemoryStore.open(self.directory, PASSWORD)
        with self.assertRaises(FileExistsError):
            HistoryStore.create(self.directory, PASSWORD, consent=True)

    def test_ciphertext_tamper_and_row_identity_swap_are_detected(self):
        first = self.store.create_conversation("first")
        second = self.store.create_conversation("second")
        with closing(sqlite3.connect(self.directory / "history.sqlite3")) as connection, connection:
            encrypted = connection.execute("SELECT encrypted FROM conversations WHERE id=?", (first.id,)).fetchone()[0]
            connection.execute("UPDATE conversations SET encrypted=? WHERE id=?", (encrypted, second.id))
        with self.assertRaises(IntegrityError):
            self.store.get(second.id)
        self.store.delete(second.id)
        self.assertEqual(self.store.get(first.id).title, "first")

    def test_retention_uses_authenticated_dates_and_zero_keeps_history(self):
        old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        conversation = replace(new_conversation("old", temporary=False), created_at=old, updated_at=old)
        self.store.save(conversation)
        self.store.set_retention(0)
        self.assertEqual(self.store.prune(), 0)
        self.assertEqual(len(self.store.list_conversations()), 1)
        self.assertEqual(self.store.set_retention(7), 1)
        self.assertEqual(self.store.list_conversations(), [])

    def test_disable_prevents_new_writes_but_owner_can_export_delete(self):
        conversation = self.store.create_conversation()
        self.store.disable()
        with self.assertRaises(ConsentRequired):
            self.store.save(conversation.append("user", "not saved"))
        self.store.export(conversation.id, Path(self.temporary.name) / "disabled-export.json")
        self.store.delete(conversation.id)
        self.assertEqual(self.store.list_conversations(), [])
        with self.assertRaises(ConsentRequired):
            self.store.enable()
        self.store.enable(consent=True)
        self.store.create_conversation("enabled again")

    def test_context_excludes_failed_attempts_and_is_bounded(self):
        conversation = new_conversation().append("user", "failed input", status="failed")
        conversation = conversation.append("user", "a" * 3000).append("assistant", "b" * 8000)
        conversation = conversation.append("user", "current", status="pending")
        context = conversation.context()
        self.assertNotIn("failed input", [message["content"] for message in context])
        self.assertEqual(context[-1], {"role": "user", "content": "current"})
        self.assertLessEqual(sum(len(message["content"]) for message in context), 6000)
        self.assertEqual(context[0]["role"], "user")

    def test_memory_v1_wire_format_still_opens_after_crypto_refactor(self):
        import hashlib
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        # Independent fixture of the previous on-disk v1 schema, not new-store output.
        directory = Path(self.temporary.name) / "legacy-preferences"
        directory.mkdir(mode=0o700)
        path = directory / "preferences.sqlite3"
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        salt = os.urandom(16)
        key = hashlib.scrypt(PASSWORD.encode(), salt=salt, n=2**17, r=8, p=1, maxmem=256*1024*1024, dklen=32)
        def encrypt(name, value):
            nonce = os.urandom(12)
            return nonce + AESGCM(key).encrypt(nonce, value, ("now-memory-v1:" + name).encode())
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value BLOB NOT NULL)")
            connection.execute("CREATE TABLE preferences (name TEXT PRIMARY KEY, encrypted BLOB NOT NULL, updated_at TEXT NOT NULL)")
            connection.executemany("INSERT INTO metadata VALUES (?,?)", [("format", b"now-memory-v1"), ("salt", salt),
                ("enabled", encrypt("enabled", b"1")), ("verifier", encrypt("verifier", b"NOW Memory authenticated vault v1"))])
            connection.execute("INSERT INTO preferences VALUES (?,?,?)", ("persona", encrypt("persona", b'"casual"'), datetime.now(timezone.utc).isoformat()))
        with MemoryStore.open(directory, PASSWORD) as memory:
            self.assertEqual(memory.get_preferences(), {"persona": "casual"})


if __name__ == "__main__":
    unittest.main()
