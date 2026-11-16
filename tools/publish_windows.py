"""Publish only a reviewed, tested Alpha artifact after explicit owner dispatch.

Do not invoke this script while preparing a candidate. Its only caller is the
manual publication workflow; CI/build workflows have no contents write token.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.distribution import parse_version, sha256_file, valid_sha, verify_archive
from tools.alpha_request import ALPHA_WORKFLOW, REQUEST_PATH, validate_request


def authorization(environment):
    required = ("GH_REPO", "RELEASE_VERSION", "RELEASE_SOURCE_SHA", "CANDIDATE_RUN_ID", "RELEASE_AUTHORIZATION",
                "RELEASE_OWNER", "RELEASE_ACTOR", "RELEASE_TRIGGER_ACTOR")
    if any(not environment.get(name) for name in required):
        raise ValueError("missing explicit publication context")
    owner, actor, trigger = (environment[name].casefold() for name in ("RELEASE_OWNER", "RELEASE_ACTOR", "RELEASE_TRIGGER_ACTOR"))
    repository = environment["GH_REPO"]
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or repository.split("/")[0].casefold() != owner or actor != owner or trigger != owner
            or environment.get("GITHUB_EVENT_NAME") != "workflow_dispatch" or environment.get("GITHUB_REF") != "refs/heads/work"):
        raise ValueError("only an explicit owner dispatch from work can publish")
    version, source = parse_version(environment["RELEASE_VERSION"]), valid_sha(environment["RELEASE_SOURCE_SHA"])
    if environment["RELEASE_AUTHORIZATION"] != f"PUBLICAR {version.tag} @ {source}":
        raise ValueError("explicit approval must identify the exact version and full source SHA")
    run_id = environment["CANDIDATE_RUN_ID"]
    if not re.fullmatch(r"[1-9][0-9]{0,19}", run_id):
        raise ValueError("invalid candidate run ID")
    return repository, version, source, run_id


def validate_run(run, workflow, repository, owner, source, run_id, *, request=None):
    if (str(run["id"]) != run_id or run["repository"]["full_name"].casefold() != repository.casefold()
            or run["head_repository"]["full_name"].casefold() != repository.casefold()
            or run["status"] != "completed" or run["conclusion"] != "success"
            or run["head_branch"] != "work" or run["head_sha"] != source
            or run["actor"]["login"].casefold() != owner.casefold() or workflow["path"] != ALPHA_WORKFLOW):
        raise ValueError("candidate must be a successful owner Alpha build from this repository/work and commit")
    if run["event"] == "push":
        if request is None:
            raise ValueError("push candidates require their explicit versioned preparation request")
        validate_request(request)
    elif run["event"] != "workflow_dispatch":
        raise ValueError("unsupported Alpha preparation event")
    attempt = str(run["run_attempt"])
    if not re.fullmatch(r"[1-9][0-9]*", attempt):
        raise ValueError("invalid candidate run attempt")
    return attempt


def validate_origin(report, repository, run_id, attempt, event, request_proof=None):
    ci = report["ci"]
    if (ci["provider"] != "github-actions" or ci["run_id"] != run_id or ci["run_attempt"] != attempt
            or ci["event"] != event or ci["workflow_ref"] != repository + "/" + ALPHA_WORKFLOW + "@refs/heads/work"):
        raise ValueError("artifact provenance differs from the reviewed Alpha run")
    if event == "push":
        if request_proof is None or report.get("preparation_request") != request_proof:
            raise ValueError("artifact request differs from the committed request at its source SHA")
        validate_request(request_proof["request"], version=report["version"],
                         branding_sha=report["branding"]["original_sha256"])


def gh_json(endpoint, *arguments, missing_ok=False):
    result = subprocess.run(["gh", "api", endpoint, *arguments], text=True, encoding="utf-8", capture_output=True)
    if result.returncode:
        if missing_ok and "(HTTP 404)" in result.stderr:
            return None
        raise RuntimeError("GitHub API request failed; no release was published by this step: " + endpoint)
    return json.loads(result.stdout)


def publish(directory):
    repository, version, source, run_id = authorization(os.environ)
    base = f"repos/{repository}"
    run = gh_json(base + f"/actions/runs/{run_id}")
    workflow = gh_json(base + f"/actions/workflows/{run['workflow_id']}")
    request_proof = None
    if run["event"] == "push":
        blob = gh_json(base + "/contents/" + REQUEST_PATH + "?ref=" + source)
        if blob.get("encoding") != "base64":
            raise ValueError("cannot verify the committed preparation request")
        raw = base64.b64decode("".join(blob["content"].splitlines()), validate=True)
        if len(raw) > 4096:
            raise ValueError("committed preparation request exceeds size limit")
        request = validate_request(json.loads(raw), version=version.value)
        request_proof = {"path": REQUEST_PATH, "sha256": hashlib.sha256(raw).hexdigest(), "request": request}
    attempt = validate_run(run, workflow, repository, os.environ["RELEASE_OWNER"], source, run_id,
                           request=request_proof["request"] if request_proof else None)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    artifact = f"now-assistant-windows-{version.value}-{source}-attempt-{attempt}"
    subprocess.run(["gh", "run", "download", run_id, "--repo", repository, "--name", artifact,
                    "--dir", str(directory)], check=True)
    archives = list(directory.glob("*.zip"))
    if len(archives) != 1:
        raise ValueError("exactly one reviewed ZIP is required")
    archive = archives[0]
    report = verify_archive(archive, version=version.value, source_sha=source)
    external = directory / "BUILD-VALIDACAO.json"
    if json.loads(external.read_text(encoding="utf-8")) != report:
        raise ValueError("external evidence differs from the tested ZIP")
    validate_origin(report, repository, run_id, attempt, run["event"], request_proof)
    checksums, notes = directory / "SHA256SUMS.txt", directory / "RELEASE-NOTES.md"
    expected = f"{sha256_file(archive)}  {archive.name}"
    if checksums.read_text(encoding="utf-8").strip() != expected:
        raise ValueError("reviewed ZIP failed its external SHA-256 check")
    with zipfile.ZipFile(archive) as bundle:
        if notes.read_bytes() != bundle.read("NOW-Assistant/CHANGELOG.md"):
            raise ValueError("release notes differ from the reviewed artifact")
    tag_path = quote(version.tag, safe="")
    if gh_json(base + "/releases/tags/" + tag_path, missing_ok=True) is not None:
        raise ValueError("this release already exists; publication never overwrites it")
    tag = gh_json(base + "/git/ref/tags/" + tag_path, missing_ok=True)
    if tag is not None:
        target = tag["object"]
        for _ in range(8):
            if target["type"] != "tag":
                break
            target = gh_json(base + "/git/tags/" + target["sha"])["object"]
        if target["type"] != "commit" or target["sha"] != source:
            raise ValueError("existing version tag points to a different commit")
    else:
        gh_json(base + "/git/refs", "--method", "POST", "-f", "ref=refs/tags/" + version.tag, "-f", "sha=" + source)
    # All validation and explicit authorization precede the first release write.
    # Upload failures leave a draft; the public release appears only at the final edit.
    command = ["gh", "release", "create", version.tag, str(archive), str(checksums), str(external),
               "--repo", repository, "--verify-tag", "--draft", "--title", f"NOW Assistant {version.value} — Windows x64",
               "--notes-file", str(notes)]
    if version.experimental:
        command.append("--prerelease")
    subprocess.run(command, check=True)
    subprocess.run(["gh", "release", "edit", version.tag, "--repo", repository, "--draft=false",
                    "--prerelease=" + str(version.experimental).lower(),
                    "--latest=" + str(not version.experimental).lower()], check=True)
    print("Published exactly the reviewed Windows artifact:", version.tag, source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    try:
        publish(parser.parse_args().directory)
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
