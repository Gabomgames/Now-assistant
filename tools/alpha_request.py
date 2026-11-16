"""Validate an owner's versioned request to build an artifact, never to publish it."""
import hashlib
import json
from pathlib import Path
import re
from uuid import UUID

from tools.distribution import parse_version

REQUEST_PATH = "packaging/releases/alpha-request.json"
ALPHA_WORKFLOW = ".github/workflows/windows-alpha.yml"
FIELDS = {"schema", "request_id", "version", "source_branch", "branding_original_sha256",
          "branding_reviewed", "prepare_artifact", "publish_release"}


def validate_request(data, *, version=None, branding_sha=None):
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError("invalid Alpha preparation request fields")
    if (data["schema"] != "now-alpha-request-v1" or data["source_branch"] != "work"
            or data["branding_reviewed"] is not True or data["prepare_artifact"] is not True
            or data["publish_release"] is not False):
        raise ValueError("request authorizes only a reviewed artifact build from work")
    parsed = parse_version(data["version"])
    if version is not None and parsed.value != version:
        raise ValueError("request version differs from the selected version")
    identifier = data["request_id"]
    if not isinstance(identifier, str) or str(UUID(identifier)) != identifier or UUID(identifier).version != 4:
        raise ValueError("request_id must be a canonical UUID v4")
    digest = data["branding_original_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("a full original-logo SHA-256 is required")
    if branding_sha is not None and digest != branding_sha:
        raise ValueError("request refers to a different official logo")
    return data


def read_request(root, *, version=None, branding_sha=None):
    path = Path(root) / REQUEST_PATH
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
        raise ValueError("missing, unsafe or oversized Alpha preparation request")
    raw = path.read_bytes()
    data = validate_request(json.loads(raw), version=version, branding_sha=branding_sha)
    return {"path": REQUEST_PATH, "sha256": hashlib.sha256(raw).hexdigest(), "request": data}


def select_preparation(environment, *, request=None, version, branding_sha):
    """Both entry points require the real owner, including the owner of a rerun."""
    owner = environment.get("REPOSITORY_OWNER", "").casefold()
    if (not owner or environment.get("REQUEST_ACTOR", "").casefold() != owner
            or environment.get("TRIGGER_ACTOR", "").casefold() != owner
            or environment.get("GITHUB_REF") != "refs/heads/work"):
        raise ValueError("only the repository owner can prepare an Alpha from work")
    event = environment.get("GITHUB_EVENT_NAME")
    if event == "workflow_dispatch":
        if environment.get("REVIEWED_INPUT", "").lower() != "true" or environment.get("REQUESTED_VERSION") != version:
            raise ValueError("manual preparation requires the exact version and reviewed branding")
        return None
    if event == "push":
        repository = environment.get("GITHUB_REPOSITORY", "")
        if (repository.split("/")[0].casefold() != owner
                or environment.get("GITHUB_WORKFLOW_REF") != repository + "/" + ALPHA_WORKFLOW + "@refs/heads/work"
                or request is None):
            raise ValueError("push preparation requires the dedicated Alpha workflow and a committed request")
        validate_request(request, version=version, branding_sha=branding_sha)
        return request
    raise ValueError("unsupported Alpha preparation event")
