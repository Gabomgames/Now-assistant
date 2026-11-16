"""Shared vault primitives; existing memory-v1 ciphertext format is preserved."""
import hashlib
import os
import stat

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def derive_key(passphrase, salt):
    if not isinstance(passphrase, str) or len(passphrase.strip()) < 12 or len(passphrase.encode("utf-8")) > 1024:
        raise ValueError("use a passphrase of at least 12 non-padding characters (maximum 1024 UTF-8 bytes)")
    return hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2**17, r=8, p=1,
                          maxmem=256 * 1024 * 1024, dklen=32)


def require_private_path(path):
    if path.is_symlink():
        raise ValueError("vault paths must not be symbolic links")
    if os.name == "posix" and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise PermissionError("vault directory/file must be accessible only to its owner")


class CipherBox:
    def __init__(self, key, context):
        self._aead = AESGCM(key)
        self._context = context

    def encrypt(self, name, data):
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, data, (self._context + ":" + name).encode())

    def decrypt(self, name, encrypted):
        if not isinstance(encrypted, bytes) or len(encrypted) < 28:
            raise ValueError("invalid ciphertext")
        return self._aead.decrypt(encrypted[:12], encrypted[12:], (self._context + ":" + name).encode())
