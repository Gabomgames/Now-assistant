"""Release-gate unit fixtures. No fixture is a real Windows executable/build result."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.collect_licenses import notice_file
from tools.distribution import (inventory, parse_version, private_file_reason, safe_path,
                                validate_evidence, verify_archive)
from tools.publish_windows import ALPHA_WORKFLOW, authorization, validate_run

SOURCE = "a" * 40
VERSION = "0.3.0-alpha.1"


def evidence_fixture():
    # Synthetic metadata tests the gate. It must never be saved as actual build evidence.
    return {
        "schema": "now-windows-candidate-v1", "version": VERSION, "tag": "v" + VERSION,
        "experimental": True, "source_sha": SOURCE, "source_dirty": False,
        "branding": {"verified": True}, "branding_review_confirmed": True,
        "pe_icon_resource_present": True, "release_eligible": True,
        "unit_tests": {"status": "passed", "system": "Windows", "python_version": "3.12.0",
                       "source_sha": SOURCE, "failures": 0, "errors": 0, "unexpected_skips": [],
                       "real_gui_tests_passed": 9, "real_http_tests_passed": 6},
        "packaged_smoke": {"system": "Windows", "qt_platform": "windows", "version": VERSION,
                           "python_version": "3.12.0", "python_bits": 64, "frozen_executable": True,
                           "real_gui_and_http_engine": True, "mocked_responses": False,
                           "temporary_session_created_database": False, "official_logo_loaded": True,
                           "offline_commands": [{"language": language, "input": text, "provider": "offline",
                                                 "output": "synthetic gate fixture, not an actual response"}
                                                for language, prompts in (("pt-BR", ("oi", "horas", "data")),
                                                                          ("en-US", ("hello", "time", "date")))
                                                for text in prompts]},
    }


class DistributionTests(unittest.TestCase):
    def test_semver_prerelease_and_experimental_status(self):
        self.assertEqual(parse_version(VERSION).tag, "v" + VERSION)
        self.assertTrue(parse_version("0.3.0").experimental)
        self.assertTrue(parse_version("1.0.0-rc.2+build.01").experimental)
        self.assertFalse(parse_version("1.0.0+build.01").experimental)

    def test_malformed_versions_and_shell_path_inputs_are_rejected(self):
        for value in ("v0.3.0", "01.0.0", "1.0.0-alpha.01", "1.0.0-", "1.0.0\n", "1.١.0",
                      "1.0.0; command", "../1.0.0", "1.0.0+", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_version(value)
        for value in ("../escape", "C:/private", "/private", "a/../private", "a\\b", "a//b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_path(value)

    def test_real_windows_evidence_and_official_branding_are_required(self):
        validate_evidence(evidence_fixture())
        changes = (("unit_tests", "system", "Linux"), ("packaged_smoke", "qt_platform", "offscreen"),
                   ("packaged_smoke", "frozen_executable", False), ("packaged_smoke", "mocked_responses", True),
                   ("packaged_smoke", "official_logo_loaded", False), ("unit_tests", "errors", 1),
                   ("unit_tests", "real_gui_tests_passed", 0))
        for section, field, value in changes:
            report = evidence_fixture()
            report[section][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_evidence(report)
        diagnostic = evidence_fixture()
        diagnostic["release_eligible"] = False
        diagnostic["branding"]["verified"] = False
        diagnostic["packaged_smoke"]["official_logo_loaded"] = False
        validate_evidence(diagnostic, require_publishable=False)
        with self.assertRaises(ValueError):
            validate_evidence(diagnostic)

    def test_private_files_and_database_signatures_are_rejected(self):
        for name in (".env", ".env.production", "history.sqlite3", "backup.db", "identity.key", ".ssh/config"):
            self.assertIsNotNone(private_file_reason(name))
        self.assertIsNotNone(private_file_reason("arbitrary.dat", b"SQLite format 3\x00"))
        self.assertIsNotNone(private_file_reason("settings.json", text=("sk-" + "a" * 40).encode()))
        self.assertIsNone(private_file_reason("_internal/sqlite3.dll", b"MZ"))
        self.assertIsNone(private_file_reason("LICENSES/public-certificate.pem", text=b"BEGIN CERTIFICATE"))
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / ".env").write_text("not an actual credential")
            with self.assertRaises(ValueError):
                inventory(temporary)

    def make_archive(self, directory, *, added=None, changed=None):
        root = Path(directory) / "NOW-Assistant"
        root.mkdir(exist_ok=True)
        content = {"NOW-Assistant.exe": b"MZ synthetic container fixture; NOT EXECUTABLE",
                   "LEIA-ME.md": b"install fixture", "CHANGELOG.md": b"notes fixture",
                   "LICENSES/DEPENDENCIES.json": b"{}", "LICENSES/Python/LICENSE.txt": b"fixture",
                   "LICENSES/Qt/LGPL-3.0-only.txt": b"fixture"}
        for name, data in content.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        report = evidence_fixture()
        report["files"] = inventory(root)
        report["executable_sha256"] = hashlib.sha256(content["NOW-Assistant.exe"]).hexdigest()
        content["BUILD-VALIDACAO.json"] = json.dumps(report).encode()
        content.update(changed or {})
        archive = Path(directory) / "container-fixture.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for name, data in content.items():
                output.writestr("NOW-Assistant/" + name, data)
            for name, data in (added or {}).items():
                output.writestr(name, data)
        return archive

    def test_archive_checksums_and_exact_authorized_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = self.make_archive(temporary)
            self.assertEqual(verify_archive(archive, version=VERSION, source_sha=SOURCE)["source_sha"], SOURCE)
            with self.assertRaises(ValueError):
                verify_archive(archive, source_sha="b" * 40)
            with self.assertRaises(ValueError):
                verify_archive(archive, version="0.3.0-alpha.2")
            archive = self.make_archive(temporary, changed={"NOW-Assistant.exe": b"MZ tampered fixture"})
            with self.assertRaises(ValueError):
                verify_archive(archive)

    def test_archive_rejects_traversal_unrecorded_files_and_windows_case_collisions(self):
        for name in ("NOW-Assistant/../escape.txt", "NOW-Assistant/../escape/", "NOW-Assistant/.env",
                     "NOW-Assistant/unknown.txt", "NOW-Assistant/now-assistant.EXE"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                archive = self.make_archive(temporary, added={name: b"fixture"})
                with self.assertRaises(ValueError):
                    verify_archive(archive)

    def test_authorization_requires_exact_owner_manual_version_and_commit(self):
        context = {"GH_REPO": "Owner/Project", "RELEASE_VERSION": VERSION, "RELEASE_SOURCE_SHA": SOURCE,
                   "CANDIDATE_RUN_ID": "123", "RELEASE_AUTHORIZATION": f"PUBLICAR v{VERSION} @ {SOURCE}",
                   "RELEASE_OWNER": "Owner", "RELEASE_ACTOR": "Owner", "RELEASE_TRIGGER_ACTOR": "Owner",
                   "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/work"}
        self.assertEqual(authorization(context)[3], "123")
        for key, value in (("RELEASE_ACTOR", "someone-else"), ("RELEASE_TRIGGER_ACTOR", "someone-else"),
                           ("GITHUB_EVENT_NAME", "push"), ("GITHUB_REF", "refs/heads/main"),
                           ("RELEASE_AUTHORIZATION", "PUBLICAR"), ("CANDIDATE_RUN_ID", "123;bad")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                authorization({**context, key: value})

    def test_candidate_provenance_rejects_failed_ci_forks_or_other_commits(self):
        run = {"id": 123, "repository": {"full_name": "Owner/Project"}, "head_repository": {"full_name": "Owner/Project"},
               "status": "completed", "conclusion": "success", "head_branch": "work", "head_sha": SOURCE,
               "event": "workflow_dispatch", "actor": {"login": "Owner"}, "run_attempt": 1}
        workflow = {"path": ALPHA_WORKFLOW}
        self.assertEqual(validate_run(run, workflow, "Owner/Project", "Owner", SOURCE, "123"), "1")
        for field, value in (("event", "push"), ("conclusion", "failure"), ("head_sha", "b" * 40),
                             ("head_repository", {"full_name": "Fork/Project"})):
            changed = deepcopy(run)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_run(changed, workflow, "Owner/Project", "Owner", SOURCE, "123")
        with self.assertRaises(ValueError):
            validate_run(run, {"path": ".github/workflows/windows-ci.yml"}, "Owner/Project", "Owner", SOURCE, "123")

    def test_upstream_notice_selection_includes_attributions_and_nonstandard_freetype_license(self):
        for path in ("LICENSES/LGPL-3.0-only.txt", "src/3rdparty/freetype/docs/FTL.TXT", "src/3rdparty/x/README", "x/qt_attribution.json"):
            self.assertTrue(notice_file(path))
        self.assertFalse(notice_file("src/ordinary.py"))
