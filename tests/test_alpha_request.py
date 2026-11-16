"""Preparation/publication authorization fixtures; never fabricated native build evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.alpha_request import (ALPHA_WORKFLOW, REQUEST_PATH, read_request,
                                 select_preparation, validate_request)
from tools.publish_windows import validate_origin, validate_run

VERSION = "0.3.0-alpha.1"
BRAND = "9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc"
SOURCE = "a" * 40
REPOSITORY = "Owner/Project"


def request_fixture():
    return {"schema": "now-alpha-request-v1", "request_id": "e8b388a1-0e48-4b7e-8253-3db977224b04",
            "version": VERSION, "source_branch": "work", "branding_original_sha256": BRAND,
            "branding_reviewed": True, "prepare_artifact": True, "publish_release": False}


def environment_fixture(event):
    return {"GITHUB_EVENT_NAME": event, "GITHUB_REF": "refs/heads/work",
            "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_WORKFLOW_REF": REPOSITORY + "/" + ALPHA_WORKFLOW + "@refs/heads/work",
            "REPOSITORY_OWNER": "Owner", "REQUEST_ACTOR": "Owner", "TRIGGER_ACTOR": "Owner",
            "REQUESTED_VERSION": VERSION, "REVIEWED_INPUT": "true"}


class AlphaRequestTests(unittest.TestCase):
    def test_request_binds_version_logo_and_forbids_publication(self):
        data = request_fixture()
        self.assertEqual(validate_request(data, version=VERSION, branding_sha=BRAND), data)
        for field, value in (("publish_release", True), ("prepare_artifact", False), ("branding_reviewed", False),
                             ("source_branch", "main"), ("request_id", "not-an-id"), ("version", "0.3.0-alpha.2"),
                             ("branding_original_sha256", "b" * 64)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_request({**data, field: value}, version=VERSION, branding_sha=BRAND)

    def test_owner_manual_and_explicit_push_request_entry_points(self):
        self.assertIsNone(select_preparation(environment_fixture("workflow_dispatch"), version=VERSION, branding_sha=BRAND))
        request = request_fixture()
        self.assertEqual(select_preparation(environment_fixture("push"), request=request,
                                           version=VERSION, branding_sha=BRAND), request)
        with self.assertRaises(ValueError):
            select_preparation(environment_fixture("push"), version=VERSION, branding_sha=BRAND)
        for field, value in (("REQUEST_ACTOR", "Else"), ("TRIGGER_ACTOR", "Else"),
                             ("GITHUB_REF", "refs/heads/main"), ("GITHUB_EVENT_NAME", "pull_request"),
                             ("GITHUB_WORKFLOW_REF", REPOSITORY + "/.github/workflows/windows-ci.yml@refs/heads/work")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                select_preparation({**environment_fixture("push"), field: value}, request=request,
                                   version=VERSION, branding_sha=BRAND)

    def test_read_request_records_exact_bytes_and_rejects_oversize(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / REQUEST_PATH
            path.parent.mkdir(parents=True)
            raw = (json.dumps(request_fixture(), indent=2) + "\n").encode()
            path.write_bytes(raw)
            proof = read_request(temporary, version=VERSION, branding_sha=BRAND)
            self.assertEqual(proof["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(proof["request"], request_fixture())
            path.write_bytes(b" " * 4097)
            with self.assertRaises(ValueError):
                read_request(temporary)

    def test_publication_accepts_push_origin_only_with_matching_committed_request(self):
        request = request_fixture()
        run = {"id": 123, "repository": {"full_name": REPOSITORY}, "head_repository": {"full_name": REPOSITORY},
               "status": "completed", "conclusion": "success", "head_branch": "work", "head_sha": SOURCE,
               "event": "push", "actor": {"login": "Owner"}, "run_attempt": 1}
        self.assertEqual(validate_run(run, {"path": ALPHA_WORKFLOW}, REPOSITORY, "Owner", SOURCE, "123", request=request), "1")
        with self.assertRaises(ValueError):
            validate_run(run, {"path": ALPHA_WORKFLOW}, REPOSITORY, "Owner", SOURCE, "123")
        proof = {"path": REQUEST_PATH, "sha256": "b" * 64, "request": request}
        report = {"version": VERSION, "branding": {"original_sha256": BRAND}, "preparation_request": proof,
                  "ci": {"provider": "github-actions", "run_id": "123", "run_attempt": "1", "event": "push",
                         "workflow_ref": REPOSITORY + "/" + ALPHA_WORKFLOW + "@refs/heads/work"}}
        validate_origin(report, REPOSITORY, "123", "1", "push", proof)
        changed = deepcopy(proof)
        changed["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            validate_origin(report, REPOSITORY, "123", "1", "push", changed)
        with self.assertRaises(ValueError):
            validate_origin(report, REPOSITORY, "123", "1", "workflow_dispatch", proof)
