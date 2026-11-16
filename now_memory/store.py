"""Encrypted SQLite preferences with explicit opt-in and no persisted encryption key.

Encryption protects a closed vault; it does not protect an unlocked process from
malware running as the same OS user. Exports are deliberately plaintext.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .preferences import validate_name, validate_preferences

DATABASE = "preferences.sqlite3"
FORMAT = "now-memory-v1"
VERIFIER = b"NOW Memory authenticated vault v1"


class MemoryErrorBase(Exception):
    pass


class ConsentRequired(MemoryErrorBase):
    pass


class UnlockError(MemoryErrorBase):
    pass


class IntegrityError(MemoryErrorBase):
    pass


def _derive(passphrase, salt):
    if not isinstance(passphrase, str) or len(passphrase.strip()) < 12 or len(passphrase.encode("utf-8")) > 1024:
        raise ValueError("use a passphrase of at least 12 non-padding characters (maximum 1024 UTF-8 bytes)")
    return hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2**17, r=8, p=1,
                          maxmem=256 * 1024 * 1024, dklen=32)


def _private(path):
    if path.is_symlink():
        raise ValueError("vault paths must not be symbolic links")
    if os.name == "posix" and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise PermissionError("vault directory/file must be accessible only to its owner")


def _connect(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)
    connection.execute("PRAGMA trusted_schema=OFF")
    connection.execute("PRAGMA secure_delete=ON")
    connection.execute("PRAGMA journal_mode=DELETE")
    return connection


def _metadata(connection):
    values = dict(connection.execute("SELECT name, value FROM metadata"))
    if (set(values) != {"format", "salt", "enabled", "verifier"}
            or values["format"] != FORMAT.encode()
            or not isinstance(values["salt"], bytes) or len(values["salt"]) != 16
            or any(not isinstance(values[key], bytes) or len(values[key]) < 28 for key in ("enabled", "verifier"))):
        raise IntegrityError("unsupported or invalid vault metadata")
    return values


class MemoryStore:
    def __init__(self, directory, connection, key):
        self.directory = Path(directory)
        self._connection = connection
        self._aead = AESGCM(key)

    @classmethod
    def create(cls, directory, passphrase, *, consent=False):
        if consent is not True:
            raise ConsentRequired("explicit opt-in is required before creating local memory")
        salt = os.urandom(16)
        key = _derive(passphrase, salt)
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        _private(directory)
        path = directory / DATABASE
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        connection = _connect(path)
        store = cls(directory, connection, key)
        try:
            with connection:
                connection.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value BLOB NOT NULL)")
                connection.execute("CREATE TABLE preferences (name TEXT PRIMARY KEY, encrypted BLOB NOT NULL, updated_at TEXT NOT NULL)")
                connection.executemany("INSERT INTO metadata VALUES (?, ?)", [
                    ("format", FORMAT.encode()), ("salt", salt), ("enabled", store._encrypt("enabled", b"1")),
                    ("verifier", store._encrypt("verifier", VERIFIER)),
                ])
        except Exception:
            store.close()
            raise
        return store

    @classmethod
    def open(cls, directory, passphrase):
        directory = Path(directory)
        _private(directory)
        path = directory / DATABASE
        _private(path)
        connection = _connect(path)
        try:
            metadata = _metadata(connection)
            store = cls(directory, connection, _derive(passphrase, metadata["salt"]))
            try:
                verifier = store._decrypt("verifier", metadata["verifier"])
            except IntegrityError as error:
                raise UnlockError("incorrect passphrase or damaged vault") from error
            if verifier != VERIFIER:
                raise UnlockError("incorrect passphrase or damaged vault")
            store.enabled  # Authenticate the persisted opt-in state before returning an unlocked store.
            return store
        except Exception:
            connection.close()
            raise

    @classmethod
    def status(cls, directory):
        directory = Path(directory)
        path = directory / DATABASE
        if not path.exists():
            return {"initialized": False, "enabled": False, "locked": True}
        _private(directory)
        _private(path)
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as connection:
            connection.execute("PRAGMA trusted_schema=OFF")
            _metadata(connection)
        return {"initialized": True, "enabled": None, "locked": True}

    def _encrypt(self, name, data):
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, data, (FORMAT + ":" + name).encode())

    def _decrypt(self, name, encrypted):
        try:
            if not isinstance(encrypted, bytes) or len(encrypted) < 28:
                raise ValueError("invalid ciphertext")
            return self._aead.decrypt(encrypted[:12], encrypted[12:], (FORMAT + ":" + name).encode())
        except (InvalidTag, ValueError) as error:
            raise IntegrityError("encrypted preference authentication failed") from error

    @property
    def enabled(self):
        value = self._connection.execute("SELECT value FROM metadata WHERE name='enabled'").fetchone()
        decrypted = self._decrypt("enabled", value[0]) if value else None
        if decrypted not in (b"0", b"1"):
            raise IntegrityError("invalid memory state")
        return decrypted == b"1"

    def _require_enabled(self):
        if not self.enabled:
            raise ConsentRequired("memory is disabled")

    def enable(self, *, consent=False):
        if consent is not True:
            raise ConsentRequired("explicit opt-in is required to enable memory")
        with self._connection:
            self._connection.execute("UPDATE metadata SET value=? WHERE name='enabled'", (self._encrypt("enabled", b"1"),))

    def disable(self):
        with self._connection:
            self._connection.execute("UPDATE metadata SET value=? WHERE name='enabled'", (self._encrypt("enabled", b"0"),))

    def set_preferences(self, values):
        self._require_enabled()
        validate_preferences(values)
        now = datetime.now(timezone.utc).isoformat()
        encrypted = [(name, self._encrypt(name, json.dumps(value, ensure_ascii=False, allow_nan=False).encode()), now)
                     for name, value in values.items()]
        with self._connection:
            self._connection.executemany(
                "INSERT INTO preferences VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET encrypted=excluded.encrypted, updated_at=excluded.updated_at",
                encrypted,
            )

    def _read_preferences(self):
        result = {}
        for name, encrypted in self._connection.execute("SELECT name, encrypted FROM preferences ORDER BY name"):
            try:
                result[name] = json.loads(self._decrypt(name, encrypted))
                validate_preferences({name: result[name]})
            except (UnicodeError, ValueError) as error:
                raise IntegrityError("stored preference is invalid") from error
        return result

    def get_preferences(self):
        self._require_enabled()
        return self._read_preferences()

    def export_preferences(self):
        # Explicit privacy control remains available when automatic use is disabled.
        return {"format": FORMAT, "preferences": self._read_preferences()}

    def delete(self, name):
        validate_name(name)
        with self._connection:
            self._connection.execute("DELETE FROM preferences WHERE name=?", (name,))
        self._connection.execute("VACUUM")

    def clear(self):
        with self._connection:
            self._connection.execute("DELETE FROM preferences")
        self._connection.execute("VACUUM")

    def close(self):
        self._connection.close()
        self._aead = None

    def __enter__(self):
        return self

    def __exit__(self, *ignored):
        self.close()
