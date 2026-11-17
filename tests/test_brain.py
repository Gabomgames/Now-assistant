"""Transport fixtures test contracts, not language quality or real inference."""
from io import BytesIO
import json
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from now_engine.assistant import LocalAssistant, TOKEN_LIMITS, system_instruction
from now_engine.desktop_api import Settings
from now_engine.providers import LocalModelUnavailable, OllamaProvider, local_open


class Response(BytesIO):
    def __init__(self, data, url):
        super().__init__(json.dumps(data).encode())
        self.url = url

    def geturl(self):
        return self.url


class BrainTests(unittest.TestCase):
    def provider(self, payload=None, inventory=None):
        self.requests = []
        if inventory is None:
            inventory = {"models": [{"name": "fixture:local"}]}
        if payload is None:
            payload = {"message": {"content": "Synthetic transport fixture."}, "done": True, "done_reason": "stop"}

        def open_fixture(request, timeout):
            url = request if isinstance(request, str) else request.full_url
            self.requests.append(request)
            return Response(inventory if url.endswith("/api/tags") else payload, url)
        return OllamaProvider(opener=open_fixture)

    @patch.dict(os.environ, {"OLLAMA_MODEL": "fixture:local"})
    def test_ui_lengths_reach_model_and_context_and_preferences_are_preserved(self):
        for length in ("short", "balanced", "detailed"):
            settings = Settings(reply_length=length, display_name="Synthetic User", language="en-US", persona="focus")
            reply = LocalAssistant(self.provider()).reply("Explain that example.", settings, [
                {"role": "user", "content": "Explain Python lists."},
                {"role": "assistant", "content": "Prior synthetic context."},
            ])
            request = json.loads(self.requests[-1].data)
            self.assertEqual(request["options"]["num_predict"], TOKEN_LIMITS[length])
            self.assertFalse(request["stream"])
            self.assertEqual(request["messages"][-3]["content"], "Explain Python lists.")
            self.assertEqual(request["messages"][-1]["content"], "Explain that example.")
            self.assertIn("en-US", request["messages"][0]["content"])
            self.assertIn("Synthetic User", request["messages"][0]["content"])
            self.assertEqual(reply.model, "fixture:local")
            self.assertEqual(reply.finish_reason, "stop")
        self.assertLess(TOKEN_LIMITS["short"], TOKEN_LIMITS["balanced"])
        self.assertLess(TOKEN_LIMITS["balanced"], TOKEN_LIMITS["detailed"])

    @patch.dict(os.environ, {"OLLAMA_MODEL": "fixture:local"})
    def test_generation_limit_is_reported_without_hiding_partial_text(self):
        provider = self.provider({"message": {"content": "Synthetic partial answer"}, "done": True, "done_reason": "length"})
        reply = LocalAssistant(provider).reply("Explain recursion.", Settings())
        self.assertEqual(reply.finish_reason, "length")
        self.assertEqual(reply.text, "Synthetic partial answer")

    @patch.dict(os.environ, {"OLLAMA_MODEL": "fixture:local"})
    def test_invalid_incomplete_and_oversized_replies_fail_honestly(self):
        for payload in ({}, {"done": False}, {"message": {"content": ""}, "done": True, "done_reason": "stop"},
                        {"message": {"content": "x" * 12001}, "done": True, "done_reason": "stop"},
                        {"message": {"content": "fixture"}, "done": True, "done_reason": "unknown"}):
            with self.subTest(payload_type=list(payload)):
                with self.assertRaises(LocalModelUnavailable):
                    LocalAssistant(self.provider(payload)).reply("Open question", Settings())

    def test_cloud_tags_and_remote_inventory_never_receive_conversation(self):
        for model in ("qwen3:CLOUD", "https://remote.invalid/model", ""):
            with patch.dict(os.environ, {"OLLAMA_MODEL": model}):
                provider = self.provider()
                with self.assertRaises(LocalModelUnavailable):
                    provider.generate([{"role": "user", "content": "synthetic private text"}], max_tokens=192)
                self.assertEqual(self.requests, [])
        with patch.dict(os.environ, {"OLLAMA_MODEL": "fixture:local"}):
            for inventory in ({"models": []}, {"models": [{"name": "fixture:local", "remote_host": "cloud.invalid"}]}):
                provider = self.provider(inventory=inventory)
                with self.assertRaises(LocalModelUnavailable):
                    provider.generate([{"role": "user", "content": "synthetic private text"}], max_tokens=192)
                self.assertEqual(len(self.requests), 1)
                self.assertIsInstance(self.requests[0], str)

    def test_loopback_transport_rejects_redirect_before_following(self):
        paths = []

        class Redirect(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                self.send_response(302)
                self.send_header("Location", "/must-not-follow")
                self.end_headers()

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(HTTPError) as error:
                local_open(f"http://127.0.0.1:{server.server_port}/redirect", timeout=2)
            self.assertEqual(error.exception.code, 302)
            self.assertEqual(paths, ["/redirect"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_persona_distinguishes_context_from_authorized_memory(self):
        for language in ("pt-BR", "en-US"):
            prompt = system_instruction(Settings(language=language))
            self.assertIn("not persistent personal memory", prompt)
            self.assertIn("without a real software result", prompt)
            self.assertIn(language, prompt)
        # No mutable provider conversation state is shared across requests.
        assistant = LocalAssistant(self.provider())
        self.assertEqual(assistant.messages("new conversation"), [{"role": "user", "content": "new conversation"}])

    def test_offline_commands_still_work_when_inference_is_unavailable(self):
        provider = self.provider()
        reply = LocalAssistant(provider).reply("horas", Settings())
        self.assertEqual(reply.provider, "offline")
        self.assertEqual(self.requests, [])

    def test_unreachable_provider_does_not_fabricate_text(self):
        def unavailable(*args, **kwargs):
            raise URLError("synthetic connection failure")
        with self.assertRaises(LocalModelUnavailable):
            LocalAssistant(OllamaProvider(opener=unavailable)).reply("Explain a variable.", Settings())

    def test_v2_additive_metadata_keeps_offline_and_local_reply_contract(self):
        from now_engine.desktop_api import ChatRequest, create_app
        from now_engine.messages import ChatReply
        app = create_app("t" * 32, "synthetic-instance")
        chat = next(route.endpoint for route in app.routes if getattr(route, "path", None) == "/v2/chat")
        payload = ChatRequest(messages=[{"role": "user", "content": "horas"}])
        result = chat(payload)
        self.assertEqual(result["provider"], "offline")
        self.assertFalse(result["output_truncated"])
        self.assertIsNone(result["model"])
        with patch("now_engine.desktop_api.LocalAssistant.reply", return_value=ChatReply(
                "Synthetic partial text", "local", "fixture:local", "length")):
            result = chat(payload)
        self.assertTrue(result["output_truncated"])
        self.assertEqual(result["model"], "fixture:local")
        self.assertEqual(result["finish_reason"], "length")
        self.assertEqual(result["reply"], "Synthetic partial text")
