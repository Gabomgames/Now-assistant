"""Password-encrypted local history. No storage is created before explicit consent."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3

from cryptography.exceptions import InvalidTag

from now_memory.security import CipherBox, derive_key, require_private_path
from now_memory.store import ConsentRequired, IntegrityError, UnlockError

from .models import Conversation, new_conversation, utc_now, valid_id, valid_time

FORMAT = "now-history-v1"
DATABASE = "history.sqlite3"
VERIFIER = b"NOW Assistant encrypted conversation history v1"


def _connect(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)
    connection.execute("PRAGMA trusted_schema=OFF")
    connection.execute("PRAGMA secure_delete=ON")
    connection.execute("PRAGMA journal_mode=DELETE")
    return connection


class HistoryStore:
    def __init__(self, directory, connection, cipher):
        self.directory, self._connection, self._cipher = Path(directory), connection, cipher

    @classmethod
    def exists(cls, directory):
        return (Path(directory) / DATABASE).exists()

    @classmethod
    def create(cls, directory, passphrase, *, consent=False, retention_days=30):
        if consent is not True:
            raise ConsentRequired("explicit history consent is required")
        cls._valid_retention(retention_days)
        salt = os.urandom(16)
        cipher = CipherBox(derive_key(passphrase, salt), FORMAT)
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        require_private_path(directory)
        path = directory / DATABASE
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        connection = _connect(path)
        with connection:
            connection.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value BLOB NOT NULL)")
            connection.execute("CREATE TABLE conversations (id TEXT PRIMARY KEY, encrypted BLOB NOT NULL)")
            connection.executemany("INSERT INTO metadata VALUES (?, ?)", [
                ("format", FORMAT.encode()), ("salt", salt), ("verifier", cipher.encrypt("verifier", VERIFIER)),
                ("enabled", cipher.encrypt("enabled", b"1")),
                ("retention", cipher.encrypt("retention", str(retention_days).encode())),
            ])
        return cls(directory, connection, cipher)

    @classmethod
    def open(cls, directory, passphrase):
        directory = Path(directory)
        require_private_path(directory)
        path = directory / DATABASE
        require_private_path(path)
        connection = _connect(path)
        try:
            metadata = dict(connection.execute("SELECT name, value FROM metadata"))
            if (set(metadata) != {"format", "salt", "verifier", "enabled", "retention"}
                    or metadata["format"] != FORMAT.encode() or not isinstance(metadata["salt"], bytes)
                    or len(metadata["salt"]) != 16):
                raise IntegrityError("invalid history format")
            store = cls(directory, connection, CipherBox(derive_key(passphrase, metadata["salt"]), FORMAT))
            try:
                if store._decrypt("verifier", metadata["verifier"]) != VERIFIER:
                    raise UnlockError("incorrect passphrase or damaged history")
            except IntegrityError as error:
                raise UnlockError("incorrect passphrase or damaged history") from error
            store.enabled
            store.retention_days
            store.prune()
            return store
        except Exception:
            connection.close()
            raise

    def _decrypt(self, name, value):
        try:
            return self._cipher.decrypt(name, value)
        except (InvalidTag, ValueError, TypeError) as error:
            raise IntegrityError("history authentication failed") from error

    def _meta(self, name):
        row = self._connection.execute("SELECT value FROM metadata WHERE name=?", (name,)).fetchone()
        if row is None:
            raise IntegrityError("history metadata is incomplete")
        return self._decrypt(name, row[0])

    def _set_meta(self, name, value):
        with self._connection:
            self._connection.execute("UPDATE metadata SET value=? WHERE name=?", (self._cipher.encrypt(name, value), name))

    @property
    def enabled(self):
        value = self._meta("enabled")
        if value not in (b"0", b"1"):
            raise IntegrityError("invalid history consent state")
        return value == b"1"

    def enable(self, *, consent=False):
        if consent is not True:
            raise ConsentRequired("explicit history consent is required")
        self._set_meta("enabled", b"1")

    def disable(self):
        self._set_meta("enabled", b"0")

    @staticmethod
    def _valid_retention(days):
        if type(days) is not int or not 0 <= days <= 3650:
            raise ValueError("retention must be 0 to 3650 days")

    @property
    def retention_days(self):
        try:
            days = int(self._meta("retention"))
            self._valid_retention(days)
            return days
        except (ValueError, TypeError) as error:
            raise IntegrityError("invalid retention policy") from error

    def set_retention(self, days):
        self._valid_retention(days)
        self._set_meta("retention", str(days).encode())
        return self.prune()

    def save(self, conversation):
        if not self.enabled:
            raise ConsentRequired("history saving is disabled")
        if conversation.temporary:
            raise ConsentRequired("temporary sessions are not persisted implicitly")
        # Re-validate all fields before encrypting or starting a write transaction.
        validated = Conversation.from_dict(json.loads(json.dumps(conversation.to_dict())))
        exists = self._connection.execute("SELECT 1 FROM conversations WHERE id=?", (validated.id,)).fetchone()
        if not exists and self._connection.execute("SELECT count(*) FROM conversations").fetchone()[0] >= 200:
            raise ValueError("history limit reached; export or delete older conversations")
        encoded = json.dumps(validated.to_dict(), ensure_ascii=False, allow_nan=False).encode()
        encrypted = self._cipher.encrypt("conversation:" + validated.id, encoded)
        with self._connection:
            self._connection.execute("INSERT INTO conversations VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET encrypted=excluded.encrypted", (validated.id, encrypted))

    def create_conversation(self, title="Nova conversa"):
        conversation = new_conversation(title, temporary=False)
        self.save(conversation)
        return conversation

    def get(self, identifier):
        valid_id(identifier)
        row = self._connection.execute("SELECT encrypted FROM conversations WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError("conversation not found")
        try:
            conversation = Conversation.from_dict(json.loads(self._decrypt("conversation:" + identifier, row[0])))
            if conversation.id != identifier or conversation.temporary:
                raise ValueError("invalid stored identity")
            return conversation
        except (ValueError, TypeError, UnicodeError) as error:
            raise IntegrityError("invalid encrypted conversation") from error

    def list_conversations(self, query=""):
        query = query.strip().casefold()
        result = []
        for (identifier,) in self._connection.execute("SELECT id FROM conversations"):
            conversation = self.get(identifier)
            if query and query not in conversation.title.casefold() and not any(query in message.content.casefold() for message in conversation.messages):
                continue
            result.append({"id": conversation.id, "title": conversation.title, "updated_at": conversation.updated_at,
                           "message_count": len(conversation.messages), "temporary": False})
        return sorted(result, key=lambda row: row["updated_at"], reverse=True)

    def rename(self, identifier, title):
        conversation = replace(self.get(identifier), title=title.strip(), updated_at=utc_now())
        if not self.enabled:
            raise ConsentRequired("enable history before renaming")
        self.save(conversation)
        return conversation

    def delete(self, identifier):
        valid_id(identifier)
        with self._connection:
            self._connection.execute("DELETE FROM conversations WHERE id=?", (identifier,))
        self._connection.execute("VACUUM")

    def clear(self):
        with self._connection:
            self._connection.execute("DELETE FROM conversations")
        self._connection.execute("VACUUM")

    def prune(self, now=None):
        days = self.retention_days
        if days == 0:
            return 0
        cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days)
        expired = [row["id"] for row in self.list_conversations() if valid_time(row["updated_at"]) < cutoff]
        with self._connection:
            self._connection.executemany("DELETE FROM conversations WHERE id=?", [(identifier,) for identifier in expired])
        if expired:
            self._connection.execute("VACUUM")
        return len(expired)

    def export(self, identifier, target):
        conversation = self.get(identifier)
        descriptor = os.open(Path(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"format": FORMAT, "conversation": conversation.to_dict()}, stream, ensure_ascii=False, indent=2)

    def close(self):
        self._connection.close()
        self._cipher = None

    def __enter__(self):
        return self

    def __exit__(self, *ignored):
        self.close()
