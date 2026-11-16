"""Opt-in encrypted local preferences. Importing this module creates no storage."""

from .store import ConsentRequired, IntegrityError, MemoryStore, UnlockError

__all__ = ["MemoryStore", "ConsentRequired", "IntegrityError", "UnlockError"]
