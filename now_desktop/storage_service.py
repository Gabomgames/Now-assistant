"""Single storage worker owns SQLite connections and expensive password derivation."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, Signal

from now_history import HistoryStore
from now_memory import MemoryStore, UnlockError
from now_memory.store import ConsentRequired


class StorageService(QObject):
    completed = Signal(str, str, int, object, object)

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.directory = Path(directory)
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="now-storage")
        self._history = None
        self._closed = False

    def submit(self, operation, payload=None, *, epoch=0):
        if self._closed:
            raise RuntimeError("storage service is closed")
        identifier = str(uuid4())
        values = dict(payload or {})

        def run():
            result, error = None, None
            try:
                result = self._run(operation, values)
            except UnlockError:
                error = "WRONG_PASSWORD"
            except ConsentRequired:
                error = "CONSENT_REQUIRED"
            except FileExistsError:
                error = "OUTPUT_EXISTS"
            except Exception:
                # Never expose SQL, passwords, conversation text or filesystem details to UI logs.
                error = "STORAGE_ERROR"
            finally:
                if "password" in values:
                    values["password"] = None
            self.completed.emit(identifier, operation, epoch, result, error)
        self._executor.submit(run)
        return identifier

    def _snapshot(self):
        if self._history is None:
            return {"unlocked": False, "enabled": False, "retention_days": None, "summaries": []}
        return {"unlocked": True, "enabled": self._history.enabled, "retention_days": self._history.retention_days,
                "summaries": self._history.list_conversations()}

    def _run(self, operation, values):
        directory = self.directory / "history"
        if operation in {"create", "unlock"}:
            if self._history is not None:
                self._history.close()
                self._history = None
            if operation == "create":
                self._history = HistoryStore.create(directory, values["password"], consent=values.get("consent", False),
                                                    retention_days=values.get("retention_days", 30))
            else:
                self._history = HistoryStore.open(directory, values["password"])
            return self._snapshot()
        if operation == "lock":
            if self._history is not None:
                self._history.close()
                self._history = None
            return self._snapshot()
        if operation.startswith("memory_"):
            directory = self.directory / "preferences"
            if operation == "memory_save" and not (directory / "preferences.sqlite3").exists():
                store = MemoryStore.create(directory, values["password"], consent=values.get("consent", False))
            else:
                store = MemoryStore.open(directory, values["password"])
            with store:
                if operation == "memory_load":
                    return store.get_preferences()
                if operation == "memory_save":
                    if not store.enabled:
                        store.enable(consent=values.get("consent", False))
                    preferences = values["preferences"]
                    if preferences.get("display_name") is None:
                        store.delete("display_name")
                    store.set_preferences({key: value for key, value in preferences.items() if value is not None})
                elif operation == "memory_disable":
                    store.disable()
                elif operation == "memory_clear":
                    store.clear()
                    store.disable()
                return None
        if self._history is None:
            raise ConsentRequired("unlock history first")
        before = set()
        if operation in {"save", "rename", "retention", "prune"}:
            before = {row["id"] for row in self._history.list_conversations()}
            if operation == "retention":
                self._history.set_retention(values["days"])
            else:
                self._history.prune()
        if operation == "search":
            return {"query": values["query"], "summaries": self._history.list_conversations(values["query"])}
        if operation == "save":
            self._history.save(values["conversation"])
        elif operation == "load":
            return self._history.get(values["id"])
        elif operation == "rename":
            self._history.save(values["conversation"])
        elif operation == "delete":
            self._history.delete(values["id"])
        elif operation == "export":
            self._history.export(values["id"], values["path"])
        elif operation == "disable":
            self._history.disable()
        elif operation == "enable":
            self._history.enable(consent=values.get("consent", False))
        elif operation == "clear":
            self._history.clear()
        elif operation not in {"refresh", "retention", "prune"}:
            raise ValueError("unsupported storage operation")
        snapshot = self._snapshot()
        return {**snapshot, "removed_ids": list(before - {row["id"] for row in snapshot["summaries"]})}

    def close(self):
        if not self._closed:
            self._closed = True
            self._executor.submit(lambda: self._run("lock", {})).result(timeout=20)
            self._executor.shutdown(wait=True, cancel_futures=True)
