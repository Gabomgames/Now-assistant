"""Synchronous orchestration for a worker thread; adapters must honor cancellation.

No default STT/TTS/microphone/wake-word implementation is installed by this module.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from threading import Event, Lock, RLock

from now_engine.assistant import LocalModelUnavailable

from .contracts import ChatReply, PCMBuffer, VoicePermissions, VoiceSettings
from .errors import CapabilityUnavailable, PermissionRequired, ProviderFailure, ProviderUnavailable, VoiceBusy, VoiceCancelled, VoiceError
from .planner import SpeechPlan, plan_speech


class VoiceState(str, Enum):
    DISABLED = "disabled"
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SYNTHESIZING = "synthesizing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass(frozen=True)
class VoiceTurn:
    reply: ChatReply
    speech_plan: SpeechPlan
    playback_completed: bool


class VoiceSession:
    def __init__(self, chat, *, settings=None, audio_input=None, recognizer=None, synthesizer=None, audio_output=None):
        self.chat = chat
        self.settings = settings or VoiceSettings()
        self.audio_input, self.recognizer = audio_input, recognizer
        self.synthesizer, self.audio_output = synthesizer, audio_output
        self._busy, self._state_lock, self._cancel = Lock(), RLock(), Event()
        self._enabled = False
        self._permissions = VoicePermissions()
        self.state, self.last_error = VoiceState.DISABLED, None

    @property
    def capabilities(self):
        return {"capture": self.audio_input is not None and self.recognizer is not None,
                "speech_output": self.synthesizer is not None and self.audio_output is not None,
                "wake_word": False, "voice_quality_validated": False}

    def enable(self, permissions=None):
        if permissions is not None and not isinstance(permissions, VoicePermissions):
            raise ValueError("use explicit VoicePermissions")
        with self._state_lock:
            if self._busy.locked():
                raise VoiceBusy("a voice request is still active")
            self._permissions = permissions or VoicePermissions()
            self._enabled, self.state, self.last_error = True, VoiceState.IDLE, None

    def disable(self):
        with self._state_lock:
            self._enabled = False
            self._permissions = VoicePermissions()
            self._cancel.set()
            self.state = VoiceState.DISABLED

    def cancel(self):
        self._cancel.set()

    def _checkpoint(self):
        if self._cancel.is_set() or not self._enabled:
            raise VoiceCancelled("request cancelled")

    def _transition(self, state):
        with self._state_lock:
            self._checkpoint()
            self.state = state

    @contextmanager
    def _request(self):
        if not self._busy.acquire(blocking=False):
            raise VoiceBusy("a voice request is already active")
        try:
            with self._state_lock:
                if not self._enabled:
                    raise PermissionRequired("enable the session before submitting a request")
                self._cancel.clear()
                self.last_error = None
            yield
        except VoiceCancelled:
            raise
        except VoiceError as error:
            with self._state_lock:
                self.last_error = error.code
                self.state = VoiceState.ERROR if self._enabled else VoiceState.DISABLED
            raise
        except Exception as error:
            with self._state_lock:
                self.last_error = "PROVIDER_FAILURE"
                self.state = VoiceState.ERROR if self._enabled else VoiceState.DISABLED
            raise ProviderFailure("voice provider failed") from error
        finally:
            with self._state_lock:
                if not self._enabled:
                    self.state = VoiceState.DISABLED
                elif self.state != VoiceState.ERROR:
                    self.state = VoiceState.IDLE
            self._busy.release()

    def _locality(self, provider):
        if getattr(provider, "local", None) is not True and not self._permissions.remote_processing:
            raise PermissionRequired("remote processing requires separate permission")

    def _speech_ready(self):
        if not self._permissions.playback:
            raise PermissionRequired("audio playback requires permission")
        if not self.capabilities["speech_output"]:
            raise CapabilityUnavailable("no synthesizer/audio output is installed")
        self._locality(self.synthesizer)
        self._locality(self.audio_output)

    def _respond(self, text, speak):
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            raise ValueError("chat text must contain 1 to 4000 characters")
        if speak:
            self._speech_ready()
        self._locality(self.chat)
        self._transition(VoiceState.THINKING)
        try:
            reply = self.chat.reply(text, self.settings)
        except LocalModelUnavailable as error:
            raise ProviderUnavailable(str(error)) from error
        self._checkpoint()
        if not isinstance(reply, ChatReply) or not reply.text.strip():
            raise ProviderFailure("chat returned no usable response")
        supported = self.synthesizer.styles if self.synthesizer is not None else frozenset({"neutral"})
        plan = plan_speech(reply.text, self.settings, supported)
        if speak:
            for segment in plan.segments:
                self._transition(VoiceState.SYNTHESIZING)
                audio = self.synthesizer.synthesize(segment.text, segment.style, segment.rate, self.settings.language, self._cancel)
                if not isinstance(audio, PCMBuffer):
                    raise ProviderFailure("synthesizer did not return PCM16 audio")
                self._transition(VoiceState.SPEAKING)
                self.audio_output.play(audio, self._cancel)
                if self._cancel.wait(segment.pause_after_ms / 1000):
                    raise VoiceCancelled("playback cancelled")
                self._checkpoint()
        return VoiceTurn(reply, plan, speak)

    def respond_text(self, text, *, speak=False):
        with self._request():
            return self._respond(text, speak)

    def capture_and_respond(self, *, speak=True):
        with self._request():
            if not self._permissions.microphone:
                raise PermissionRequired("microphone capture requires fresh permission")
            if not self.capabilities["capture"]:
                raise CapabilityUnavailable("no audio input/recognizer is installed")
            self._locality(self.recognizer)
            self._locality(self.audio_input)
            if speak:
                self._speech_ready()
            self._transition(VoiceState.LISTENING)
            audio = self.audio_input.capture(self._cancel)
            if not isinstance(audio, PCMBuffer):
                raise ProviderFailure("audio input did not return PCM16 audio")
            self._transition(VoiceState.TRANSCRIBING)
            text = self.recognizer.transcribe(audio, self.settings.language, self._cancel)
            return self._respond(text, speak)
