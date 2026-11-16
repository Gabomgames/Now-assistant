import json
import secrets
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from now_desktop.runtime import EngineProcess


def start_runtime():
    runtime = EngineProcess(model="now-uninstalled-test-" + secrets.token_hex(12))
    runtime.start()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if runtime.process.poll() is not None:
            runtime.stop()
            raise RuntimeError("test Engine exited before readiness")
        try:
            request = Request(runtime.url + "/v2/health", headers={"Authorization": "Bearer " + runtime.token})
            with urlopen(request, timeout=1) as response:
                if json.load(response)["instance_id"] == runtime.instance:
                    return runtime
        except URLError:
            time.sleep(0.05)
    runtime.stop()
    raise RuntimeError("test Engine did not become ready")


class DesktopAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = start_runtime()

    @classmethod
    def tearDownClass(cls):
        cls.runtime.stop()

    def request(self, path, payload=None, *, runtime=None, headers=None, authenticated=True, raw=None):
        runtime = runtime or self.runtime
        values = {"Content-Type": "application/json"}
        if authenticated:
            values["Authorization"] = "Bearer " + runtime.token
        values.update(headers or {})
        body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
        request = Request(runtime.url + path, data=body, headers=values)
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            body = error.read()
            try:
                return error.code, json.loads(body)
            except ValueError:
                return error.code, None

    def test_authentication_origin_host_and_payload_guards(self):
        payload = {"messages": [{"role": "user", "content": "horas"}]}
        self.assertEqual(self.request("/v2/health", authenticated=False)[0], 401)
        self.assertEqual(self.request("/v2/chat", payload, headers={"Origin": "https://untrusted.invalid"})[0], 403)
        self.assertEqual(self.request("/v2/health", headers={"Host": "untrusted.invalid"})[0], 400)
        self.assertEqual(self.request("/v2/chat", raw=b"x" * 65537)[0], 413)

    def test_real_offline_replies_both_languages(self):
        for language, prompt, marker in (("pt-BR", "horas", "Agora são"), ("en-US", "time", "It is")):
            status, result = self.request("/v2/chat", {"messages": [{"role": "user", "content": prompt}], "settings": {"language": language}})
            self.assertEqual(status, 200)
            self.assertEqual(result["provider"], "offline")
            self.assertIn(marker, result["reply"])

    def test_invalid_context_roles_and_configuration_are_rejected(self):
        for payload in (
            {"messages": [{"role": "system", "content": "untrusted"}]},
            {"messages": [{"role": "assistant", "content": "not a user request"}]},
            {"messages": [{"role": "user", "content": ""}]},
            {"messages": [{"role": "user", "content": "x" * 4001}]},
            {"messages": [{"role": "user", "content": "hi"}], "settings": {"humor": True}},
            {"messages": [{"role": "user", "content": "hi"}], "url": "https://external.invalid"},
        ):
            self.assertEqual(self.request("/v2/chat", payload)[0], 422)

    def test_model_unavailability_is_http_error_not_fabricated_reply(self):
        status, result = self.request("/v2/chat", {"messages": [{"role": "user", "content": "Explain a variable."}]})
        self.assertEqual(status, 503)
        self.assertEqual(result["detail"]["error"], "MODEL_UNAVAILABLE")
        self.assertNotIn("reply", result)

    def test_capabilities_do_not_claim_audio_vision_or_cloud(self):
        status, result = self.request("/v2/capabilities")
        self.assertEqual(status, 200)
        for key in ("capture", "speech_output", "wake_word", "screen_analysis", "cloud"):
            self.assertIs(result[key], False)
        self.assertFalse(result["model_installed"])

    def test_rate_limit_uses_real_authenticated_requests(self):
        runtime = start_runtime()
        try:
            payload = {"messages": [{"role": "user", "content": "oi"}]}
            for _ in range(60):
                self.assertEqual(self.request("/v2/chat", payload, runtime=runtime)[0], 200)
            self.assertEqual(self.request("/v2/chat", payload, runtime=runtime)[0], 429)
        finally:
            runtime.stop()


if __name__ == "__main__":
    unittest.main()
