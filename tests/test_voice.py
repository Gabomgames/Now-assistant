"""Control-flow tests use explicit test doubles, not claimed STT/TTS/model validation."""
import threading
import unittest
from unittest.mock import patch

from now_engine.assistant import LocalAssistant, LocalModelUnavailable
from now_voice import VoicePermissions, VoiceSession, VoiceSettings
from now_voice.contracts import ChatReply, PCMBuffer
from now_voice.errors import CapabilityUnavailable, PermissionRequired, ProviderFailure, VoiceBusy, VoiceCancelled
from now_voice.planner import plan_speech
from now_voice.session import VoiceState


class ChatDouble:
    local = True
    def __init__(self):
        self.calls = 0
    def reply(self, text, settings):
        self.calls += 1
        return ChatReply("Contract test. Second segment!", "test_double")


class SynthDouble:
    local = True
    styles = frozenset({"neutral"})
    def __init__(self, cancel=False):
        self.cancel, self.calls = cancel, []
    def synthesize(self, text, style, rate, language, cancel):
        self.calls.append((text, style, rate, language))
        if self.cancel:
            cancel.set()
        return PCMBuffer(b"\x00\x00" * 160)


class OutputDouble:
    local = True
    def __init__(self):
        self.calls = 0
    def play(self, audio, cancel):
        self.calls += 1


class VoiceTests(unittest.TestCase):
    def test_default_capabilities_do_not_advertise_audio_or_wake_word(self):
        session = VoiceSession(ChatDouble())
        self.assertEqual(session.capabilities, {"capture": False, "speech_output": False, "wake_word": False, "voice_quality_validated": False})
        with self.assertRaises(PermissionRequired):
            session.respond_text("test")

    def test_requested_speech_is_not_simulated_when_backend_is_absent(self):
        chat = ChatDouble()
        session = VoiceSession(chat)
        session.enable(VoicePermissions(playback=True))
        with self.assertRaises(CapabilityUnavailable):
            session.respond_text("test", speak=True)
        self.assertEqual(chat.calls, 0)

    def test_capture_requires_fresh_permission_and_real_adapter_bindings(self):
        session = VoiceSession(ChatDouble())
        session.enable()
        with self.assertRaises(PermissionRequired):
            session.capture_and_respond()
        session.enable(VoicePermissions(microphone=True))
        with self.assertRaises(CapabilityUnavailable):
            session.capture_and_respond(speak=False)

    def test_remote_stt_is_rejected_before_capturing_audio(self):
        class InputDouble:
            def capture(self, cancel):
                raise AssertionError("capture must not start")
        class RemoteRecognizer:
            local = False
        session = VoiceSession(ChatDouble(), audio_input=InputDouble(), recognizer=RemoteRecognizer())
        session.enable(VoicePermissions(microphone=True))
        with self.assertRaises(PermissionRequired):
            session.capture_and_respond(speak=False)

    def test_remote_tts_requires_permission_before_chat_or_audio(self):
        synthesizer = SynthDouble()
        synthesizer.local = False
        chat = ChatDouble()
        session = VoiceSession(chat, synthesizer=synthesizer, audio_output=OutputDouble())
        session.enable(VoicePermissions(playback=True))
        with self.assertRaises(PermissionRequired):
            session.respond_text("test", speak=True)
        self.assertEqual(chat.calls, 0)

    def test_remote_audio_output_requires_separate_permission(self):
        output = OutputDouble()
        output.local = False
        session = VoiceSession(ChatDouble(), synthesizer=SynthDouble(), audio_output=output)
        session.enable(VoicePermissions(playback=True))
        with self.assertRaises(PermissionRequired):
            session.respond_text("test", speak=True)
        self.assertEqual(output.calls, 0)

    def test_orchestration_contract_with_explicit_audio_test_doubles(self):
        synth, output = SynthDouble(), OutputDouble()
        session = VoiceSession(ChatDouble(), settings=VoiceSettings(pause_scale=0), synthesizer=synth, audio_output=output)
        session.enable(VoicePermissions(playback=True))
        turn = session.respond_text("test", speak=True)
        self.assertEqual(turn.reply.provider, "test_double")
        self.assertEqual(output.calls, 2)
        self.assertTrue(turn.playback_completed)
        self.assertEqual(turn.speech_plan.applied_style, "neutral")
        self.assertTrue(turn.speech_plan.style_fallback)
        self.assertEqual(session.state, VoiceState.IDLE)

    def test_cancel_between_synthesis_and_playback_prevents_output(self):
        output = OutputDouble()
        session = VoiceSession(ChatDouble(), synthesizer=SynthDouble(cancel=True), audio_output=output)
        session.enable(VoicePermissions(playback=True))
        with self.assertRaises(VoiceCancelled):
            session.respond_text("test", speak=True)
        self.assertEqual(output.calls, 0)
        self.assertEqual(session.state, VoiceState.IDLE)

    def test_disable_during_chat_stops_the_request_and_concurrent_requests(self):
        entered, released = threading.Event(), threading.Event()
        class BlockingChat:
            local = True
            def reply(self, text, settings):
                entered.set()
                if not released.wait(3):
                    raise RuntimeError("test driver timed out")
                return ChatReply("contract test", "test_double")
        session = VoiceSession(BlockingChat())
        session.enable()
        errors = []
        def worker():
            try:
                session.respond_text("test")
            except Exception as error:
                errors.append(error)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            with self.assertRaises(VoiceBusy):
                session.respond_text("another request")
            session.disable()
        finally:
            released.set()
            thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertIsInstance(errors[0], VoiceCancelled)
        self.assertEqual(session.state, VoiceState.DISABLED)

    def test_provider_error_exposes_an_error_code_without_private_content(self):
        class FailingChat:
            local = True
            def reply(self, text, settings):
                raise RuntimeError("private fixture content")
        session = VoiceSession(FailingChat())
        session.enable()
        with self.assertRaises(ProviderFailure) as error:
            session.respond_text("test")
        self.assertNotIn("private fixture", str(error.exception))
        self.assertEqual(session.last_error, "PROVIDER_FAILURE")
        self.assertEqual(session.state, VoiceState.ERROR)

    def test_segment_bounds_decimal_numbers_and_prosody_metadata(self):
        plan = plan_speech("Version 3.14 works. " + "word " * 90, VoiceSettings(), {"neutral"})
        self.assertIn("3.14", plan.segments[0].text)
        self.assertEqual(plan.segments[0].pause_after_ms, 280)
        self.assertTrue(all(len(segment.text) <= 240 for segment in plan.segments))
        self.assertTrue(plan.style_fallback)

    def test_audio_and_preference_resource_limits(self):
        for invalid in (b"", b"x", b"\x00\x00" * 16000 * 31):
            with self.assertRaises(ValueError):
                PCMBuffer(invalid)
        with self.assertRaises(ValueError):
            VoiceSettings(rate=float("nan"))
        with self.assertRaises(ValueError):
            VoicePermissions(microphone="yes")

    def test_real_local_commands_in_both_languages_need_no_model_connection(self):
        assistant = LocalAssistant()
        with patch("now_engine.assistant.urlopen", side_effect=AssertionError("model calls are forbidden")):
            for language, text, expected in (("pt-BR", "horas", "Agora são"), ("en-US", "time", "It is"), ("pt-BR", "data", "Hoje é"), ("en-US", "date", "Today is")):
                reply = assistant.reply(text, VoiceSettings(language=language))
                self.assertEqual(reply.provider, "offline")
                self.assertIn(expected, reply.text)

    def test_cloud_model_is_rejected_before_sending_user_text(self):
        with patch.dict("os.environ", {"OLLAMA_MODEL": "qwen3:CLOUD"}), patch("now_engine.assistant.urlopen", side_effect=AssertionError("network must not be called")):
            with self.assertRaises(LocalModelUnavailable):
                LocalAssistant().reply("Explain a variable.", VoiceSettings())


if __name__ == "__main__":
    unittest.main()
