from __future__ import annotations

from dataclasses import dataclass
import math
from threading import Event
from typing import Protocol

from now_engine.messages import ChatReply


@dataclass(frozen=True)
class VoiceSettings:
    language: str = "pt-BR"
    style: str = "expressive"
    rate: float = 1.0
    humor: int = 1
    pause_scale: float = 1.0
    persona: str = "casual"
    reply_length: str = "balanced"
    display_name: str | None = None

    def __post_init__(self):
        if self.language not in {"pt-BR", "en-US"} or self.style not in {"neutral", "expressive"}:
            raise ValueError("unsupported language or voice style")
        if self.persona not in {"classic", "casual", "gamer", "focus", "creative"} or self.reply_length not in {"short", "balanced", "detailed"}:
            raise ValueError("unsupported persona or response length")
        if self.display_name is not None and (not isinstance(self.display_name, str) or not 1 <= len(self.display_name.strip()) <= 80):
            raise ValueError("display_name must contain 1 to 80 characters")
        if type(self.humor) is not int or not 0 <= self.humor <= 3:
            raise ValueError("humor must be between 0 and 3")
        for value, low, high in ((self.rate, 0.5, 2.0), (self.pause_scale, 0, 2.0)):
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError("invalid rate or pause scale")

    @classmethod
    def from_preferences(cls, preferences):
        return cls(language=preferences.get("language", "pt-BR"),
                   style=preferences.get("voice_style", "expressive"),
                   rate=preferences.get("voice_rate", 1.0), humor=preferences.get("humor", 1),
                   persona=preferences.get("persona", "casual"), reply_length=preferences.get("reply_length", "balanced"),
                   display_name=preferences.get("display_name"))


@dataclass(frozen=True)
class VoicePermissions:
    microphone: bool = False
    playback: bool = False
    remote_processing: bool = False

    def __post_init__(self):
        if any(type(value) is not bool for value in (self.microphone, self.playback, self.remote_processing)):
            raise ValueError("permissions must be explicit booleans")


@dataclass(frozen=True)
class PCMBuffer:
    data: bytes
    sample_rate: int = 16000
    channels: int = 1

    def __post_init__(self):
        if (not isinstance(self.data, bytes) or not self.data or type(self.sample_rate) is not int
                or not 8000 <= self.sample_rate <= 48000 or type(self.channels) is not int
                or self.channels not in (1, 2) or len(self.data) % (2 * self.channels)
                or len(self.data) / (2 * self.channels * self.sample_rate) > 30):
            raise ValueError("expected aligned PCM16 audio, 8–48 kHz, at most 30 seconds")


class ChatProvider(Protocol):
    local: bool
    def reply(self, text: str, settings: VoiceSettings) -> ChatReply: ...


class AudioInput(Protocol):
    local: bool
    def capture(self, cancel: Event) -> PCMBuffer: ...


class SpeechRecognizer(Protocol):
    local: bool
    def transcribe(self, audio: PCMBuffer, language: str, cancel: Event) -> str: ...


class SpeechSynthesizer(Protocol):
    local: bool
    styles: frozenset[str]
    def synthesize(self, text: str, style: str, rate: float, language: str, cancel: Event) -> PCMBuffer: ...


class AudioOutput(Protocol):
    local: bool
    def play(self, audio: PCMBuffer, cancel: Event) -> None: ...


class WakeWordDetector(Protocol):
    """Future local adapter for 'Now'; no detector or background loop is supplied yet."""
    local: bool
    keyword: str
    def feed(self, audio: PCMBuffer) -> bool: ...
