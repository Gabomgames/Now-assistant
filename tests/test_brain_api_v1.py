"""Real HTTP/SSE integration against an explicit Ollama protocol fixture.

These tests execute the actual API and socket transport, not model inference.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
from threading import Event, Lock, Thread
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

import uvicorn

from now_engine.providers import local_open
from now_brain.api import PREFIX, create_app
from now_brain.provider import OllamaProvider


@contextmanager
def serve(app):
    import socket
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    config = uvicorn.Config(app, log_level="critical", access_log=False, lifespan="off", timeout_graceful_shutdown=1)
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        raise RuntimeError("test API failed to start")
    try:
        yield f"http://127.0.0.1:{listener.getsockname()[1]}"
    finally:
        server.should_exit = True
        thread.join(5)
        listener.close()
        if thread.is_alive():
            raise RuntimeError("test API did not stop")


def read_event(response):
    event, data = None, None
    while True:
        line = response.readline().decode("utf-8")
        if not line:
            return None, None
        if line.startswith("event: "):
            event = line[7:].strip()
        elif line.startswith("data: "):
            data = json.loads(line[6:])
        elif line in ("\n", "\r\n") and event:
            return event, data


class BrainAPIV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recorded, cls.record_lock, cls.upstream_closed = [], Lock(), Event()
        records, lock, closed = cls.recorded, cls.record_lock, cls.upstream_closed

        class OllamaFixture(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                body = json.dumps({"models": [
                    {"name": "fixture:local", "digest": "sha256:" + "1" * 64, "size": 100,
                     "details": {"parameter_size": "fixture", "quantization_level": "fixture"}},
                    {"name": "fixture:second"}, {"name": "fixture:remote", "remote_host": "remote.invalid"},
                    {"name": "fixture:CLOUD"},
                ]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                with lock:
                    records.append(payload)
                prompt = payload["messages"][-1]["content"]
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.end_headers()

                def line(data):
                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode() + b"\n")
                    self.wfile.flush()

                try:
                    if prompt == "stall":
                        time.sleep(2)
                    if prompt == "blank":
                        line({"message": {"content": "   "}, "done": True, "done_reason": "stop"})
                        return
                    if prompt == "oversized":
                        line({"message": {"content": "x" * 12001}, "done": False})
                        return
                    line({"message": {"content": "Olá "}, "done": False})
                    if prompt == "slow":
                        for _ in range(200):
                            time.sleep(0.02)
                            line({"message": {"content": "fixture "}, "done": False})
                    if prompt == "interrupted":
                        return
                    if prompt == "malformed":
                        self.wfile.write(b"not-json\n")
                        self.wfile.flush()
                        return
                    reason = "length" if prompt == "truncate" else "stop"
                    line({"message": {"content": "mundo"}, "done": True, "done_reason": reason,
                          "eval_count": 4, "eval_duration": 200000000})
                except (OSError, BrokenPipeError):
                    closed.set()

        cls.ollama = ThreadingHTTPServer(("127.0.0.1", 0), OllamaFixture)
        cls.thread = Thread(target=cls.ollama.serve_forever, daemon=True)
        cls.thread.start()
        cls.environment = patch.dict("os.environ", {"OLLAMA_MODEL": "fixture:local"})
        cls.environment.start()

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        cls.ollama.shutdown()
        cls.ollama.server_close()
        cls.thread.join()

    def setUp(self):
        self.token = secrets.token_urlsafe(32)
        self.app = create_app(self.token, provider=OllamaProvider(
            endpoint=f"http://127.0.0.1:{self.ollama.server_port}", timeout=1))
        self.server = serve(self.app)
        self.url = self.server.__enter__()
        self.recorded.clear()
        self.upstream_closed.clear()

    def tearDown(self):
        self.server.__exit__(None, None, None)

    def request(self, path, payload=None, *, token=None, headers=None, raw=None, stream=False):
        values = {"Authorization": "Bearer " + (self.token if token is None else token), "Content-Type": "application/json"}
        values.update(headers or {})
        body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
        request = Request(self.url + PREFIX + path, data=body, headers=values)
        try:
            response = local_open(request, timeout=4)
            if stream:
                return response
            with response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def payload(self, prompt="Explain a list.", **kwargs):
        return {"messages": [{"role": "user", "content": prompt}], **kwargs}

    def test_health_inventory_and_protected_openapi_are_truthful(self):
        self.assertTrue(self.request("/health")[1]["ready"])
        info = self.request("/models")[1]
        self.assertEqual({row["model_id"] for row in info["models"]}, {"fixture:local", "fixture:second"})
        self.assertEqual(info["models"][0]["license_status"], "not_audited")
        caps = self.request("/capabilities")[1]
        for key in ("persistence", "memory_api", "remote_providers", "multi_tenant", "voice", "vision", "tools"):
            self.assertFalse(caps[key])
        schema = self.request("/openapi.json")[1]
        self.assertIn(PREFIX + "/chat/stream", schema["paths"])
        self.assertEqual(set(schema["paths"][PREFIX + "/chat/stream"]["post"]["responses"]["200"]["content"]), {"text/event-stream"})
        self.assertIn("HTTPBearer", schema["components"]["securitySchemes"])
        self.assertEqual(self.request("/openapi.json", token="wrong")[0], 401)

    def test_security_payload_and_schema_errors_never_echo_private_input(self):
        private = "synthetic-private-marker"
        checks = [self.request("/chat", self.payload(private), token="wrong"),
                  self.request("/chat", self.payload(private), headers={"Origin": "https://browser.invalid"}),
                  self.request("/chat", self.payload(private), headers={"Host": "remote.invalid"}),
                  self.request("/chat", raw=b"x" * 65537),
                  self.request("/chat", {**self.payload(private), "user_id": "forged"}),
                  self.request("/chat", self.payload(private, options={"humor": True}))]
        self.assertEqual([row[0] for row in checks], [401, 403, 400, 413, 422, 422])
        for _, body in checks:
            self.assertNotIn(private, json.dumps(body))
            self.assertIn("code", body["error"])
        self.assertEqual(self.recorded, [])

    def test_missing_and_remote_models_fail_before_conversation_is_sent(self):
        for model, status in (("fixture:absent", 503), ("fixture:remote", 503), ("fixture:CLOUD", 422),
                              ("https://remote.invalid/model", 422)):
            response = self.request("/chat", self.payload(model_id=model))
            self.assertEqual(response[0], status)
            self.assertNotIn("reply", response[1])
        self.assertEqual(self.recorded, [])

    def test_context_preferences_model_choice_and_generation_budgets_reach_upstream(self):
        for length, budget in (("short", 192), ("balanced", 512), ("detailed", 1024)):
            payload = self.payload(model_id="fixture:second", options={"reply_length": length, "language": "en-US", "display_name": "Alex"})
            payload["messages"] = [{"role": "user", "content": "Earlier synthetic question"},
                                   {"role": "assistant", "content": "Earlier synthetic answer"}, *payload["messages"]]
            status, result = self.request("/chat", payload)
            self.assertEqual(status, 200)
            self.assertEqual(result["reply"], "Olá mundo")
            self.assertEqual(result["model_id"], "fixture:second")
            self.assertEqual(result["metrics"]["tokens_per_second"], 20)
            self.assertEqual(result["metrics"]["output_tokens"], 4)
            self.assertIsNotNone(result["metrics"]["first_token_ms"])
            actual = self.recorded[-1]
            self.assertEqual(actual["options"]["num_predict"], budget)
            self.assertEqual(actual["messages"][-3:], payload["messages"])
            self.assertIn("en-US", actual["messages"][0]["content"])
            self.assertTrue(actual["stream"])

    def test_sse_delivers_deltas_and_a_terminal_result_and_reports_truncation(self):
        with self.request("/chat/stream", self.payload("truncate"), stream=True) as response:
            events = []
            while True:
                event, data = read_event(response)
                if event is None:
                    break
                events.append((event, data))
            self.assertEqual([item[0] for item in events], ["state", "delta", "delta", "done"])
            self.assertEqual("".join(data["text"] for event, data in events if event == "delta"), "Olá mundo")
            self.assertEqual(events[-1][1]["status"], "truncated")
            self.assertEqual(events[0][1]["request_id"], response.headers["X-Request-ID"])

    def test_cancel_is_authenticated_and_closes_upstream_socket(self):
        with self.request("/chat/stream", self.payload("slow"), stream=True) as response:
            _, state = read_event(response)
            self.assertEqual(read_event(response)[0], "delta")
            identifier = state["request_id"]
            self.assertEqual(self.request("/chat/cancel", {"request_id": identifier}, token="wrong")[0], 401)
            self.assertEqual(self.request("/chat", self.payload())[0], 409)
            self.assertEqual(self.request("/chat/cancel", {"request_id": identifier})[0], 200)
            while True:
                event, data = read_event(response)
                if event == "done":
                    self.assertEqual(data["status"], "cancelled")
                    break
                self.assertIsNotNone(event)
        self.assertTrue(self.upstream_closed.wait(2), "upstream HTTP socket was not closed")
        self.assertEqual(self.request("/chat/cancel", {"request_id": identifier})[0], 404)
        self.assertEqual(self.request("/chat", self.payload("horas", mode="offline"))[0], 200)

    def test_disconnecting_sse_client_releases_generation_slot(self):
        response = self.request("/chat/stream", self.payload("slow"), stream=True)
        read_event(response)
        read_event(response)
        response.close()
        self.assertTrue(self.upstream_closed.wait(2), "disconnect did not interrupt upstream")
        deadline = time.monotonic() + 2
        while self.app.state.brain.telemetry()["active_generations"] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.app.state.brain.telemetry()["active_generations"], 0)
        self.assertEqual(self.app.state.brain.telemetry()["counters"]["cancelled"], 1)
        self.assertEqual(self.request("/chat", self.payload())[0], 200)

    def test_truncated_stream_and_provider_faults_are_explicit(self):
        for prompt, code in (("interrupted", "interrupted"), ("malformed", "provider_error"), ("blank", "provider_error"),
                             ("oversized", "output_limit"), ("stall", "timeout")):
            with self.request("/chat/stream", self.payload(prompt), stream=True) as response:
                events = []
                while True:
                    event, data = read_event(response)
                    if event is None:
                        break
                    events.append((event, data))
                self.assertEqual(events[-1][0], "error")
                self.assertEqual(events[-1][1]["error"]["code"], code)
                self.assertNotIn("done", [item[0] for item in events])

    def test_rate_limit_and_explicit_offline_mode(self):
        payload = self.payload("horas", mode="offline")
        for _ in range(60):
            self.assertEqual(self.request("/chat", payload)[0], 200)
        result = self.request("/chat", payload)
        self.assertEqual(result[0], 429)
        self.assertEqual(result[1]["error"]["code"], "quota_exceeded")
        self.assertEqual(self.recorded, [])

    def test_context_trimming_is_reported_and_does_not_leak_between_calls(self):
        payload = self.payload()
        payload["messages"] = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 1000} for i in range(18)] + payload["messages"]
        result = self.request("/chat", payload)[1]
        self.assertTrue(result["context_trimmed"])
        self.assertLessEqual(sum(len(row["content"]) for row in self.recorded[-1]["messages"][1:]), 6000)
        self.request("/chat", self.payload("brand new conversation"))
        self.assertEqual(len(self.recorded[-1]["messages"]), 2)

    def test_unavailable_provider_has_503_without_fabricated_reply(self):
        # Use a real OS-assigned port that is then closed, with no model fixture.
        import socket
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.app.state.brain.provider = OllamaProvider(endpoint=f"http://127.0.0.1:{port}")
        status, health = self.request("/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["live"])
        self.assertFalse(health["ready"])
        status, error = self.request("/chat", self.payload())
        self.assertEqual(status, 503)
        self.assertEqual(error["error"]["code"], "unavailable")
        self.assertNotIn("reply", error)
        self.assertEqual(self.app.state.brain.telemetry()["active_generations"], 0)

    def test_nonstream_client_disconnect_cancels_upstream_too(self):
        import socket
        parsed = __import__("urllib.parse", fromlist=["urlsplit"]).urlsplit(self.url)
        payload = json.dumps(self.payload("slow")).encode()
        connection = socket.create_connection(("127.0.0.1", parsed.port), timeout=2)
        header = (f"POST {PREFIX}/chat HTTP/1.1\r\nHost: 127.0.0.1:{parsed.port}\r\n"
                  f"Authorization: Bearer {self.token}\r\nContent-Type: application/json\r\n"
                  f"Content-Length: {len(payload)}\r\n\r\n").encode()
        connection.sendall(header + payload)
        deadline = time.monotonic() + 2
        while not self.recorded and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(self.recorded)
        connection.close()
        self.assertTrue(self.upstream_closed.wait(2))
        deadline = time.monotonic() + 2
        while self.app.state.brain.telemetry()["active_generations"] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertEqual(self.app.state.brain.telemetry()["active_generations"], 0)
        self.assertEqual(self.request("/chat", self.payload())[0], 200)
