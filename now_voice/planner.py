"""Plain-text segments and prosody hints; producing a plan is not speech synthesis."""
from dataclasses import dataclass
import re
import textwrap

from .contracts import VoiceSettings


@dataclass(frozen=True)
class SpeechSegment:
    text: str
    pause_after_ms: int
    style: str
    rate: float


@dataclass(frozen=True)
class SpeechPlan:
    language: str
    requested_style: str
    applied_style: str
    style_fallback: bool
    segments: tuple[SpeechSegment, ...]


def plan_speech(text: str, settings: VoiceSettings, supported_styles=frozenset({"neutral"})):
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise ValueError("speech text must contain 1 to 12000 characters")
    if settings.style not in supported_styles and "neutral" not in supported_styles:
        raise ValueError("the synthesizer has no compatible voice style")
    style = settings.style if settings.style in supported_styles else "neutral"
    segments = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text.strip()):
        for piece in textwrap.wrap(sentence, width=240, break_on_hyphens=False):
            pause = 280 if piece.endswith((".", "!", "?")) else 100
            segments.append(SpeechSegment(piece, round(pause * settings.pause_scale), style, settings.rate))
    return SpeechPlan(settings.language, settings.style, style, style != settings.style, tuple(segments))
