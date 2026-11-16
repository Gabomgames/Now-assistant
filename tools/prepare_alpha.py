"""Select authorized Alpha build inputs for GitHub Actions; contains no release writes."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from now_desktop.version import VERSION
from tools.alpha_request import read_request, select_preparation
from tools.distribution import branding_receipt


def main():
    branding = branding_receipt(ROOT)
    if not branding["verified"]:
        raise ValueError("the official logo must be imported before preparing an Alpha")
    proof = None
    if os.environ.get("GITHUB_EVENT_NAME") == "push":
        proof = read_request(ROOT, version=VERSION, branding_sha=branding["original_sha256"])
    select_preparation(os.environ, request=proof["request"] if proof else None,
                       version=VERSION, branding_sha=branding["original_sha256"])
    values = {"CANDIDATE_VERSION": VERSION, "BRANDING_REVIEWED": "true"}
    if proof:
        values["NOW_ALPHA_REQUEST_SHA256"] = proof["sha256"]
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as stream:
        for name, value in values.items():
            stream.write(name + "=" + value + "\n")
    print(json.dumps({"version": VERSION, "event": os.environ["GITHUB_EVENT_NAME"],
                      "request_id": proof["request"]["request_id"] if proof else None,
                      "publication_authorized": False}))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
