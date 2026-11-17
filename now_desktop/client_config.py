"""Explicit technical choices only; never stores conversation preferences or tokens."""
import json
from pathlib import Path
import os
import tempfile

from now_brain.provider import valid_model, BrainError


def load(directory):
    path = Path(directory) / "client.json"
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 4096:
            return {"protocol": "v1", "model": None}
        data = json.loads(path.read_text(encoding="utf-8"))
        if set(data) != {"protocol", "model"} or data["protocol"] not in {"v1", "v2"}:
            raise ValueError("invalid technical configuration")
        if data["model"] is not None:
            valid_model(data["model"])
        return data
    except (ValueError, TypeError, OSError, BrainError):
        # Invalid local configuration must not prevent access to protected history.
        return {"protocol": "v1", "model": None}


def save(directory, protocol, model):
    if protocol not in {"v1", "v2"}:
        raise ValueError("unsupported protocol")
    if model is not None:
        valid_model(model)
    path = Path(directory) / "client.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump({"protocol": protocol, "model": model}, stream)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
