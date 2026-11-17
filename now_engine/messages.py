"""Application contracts shared by optional clients; legacy Engine interfaces remain unchanged."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatReply:
    text: str
    provider: str
    model: str | None = None
    finish_reason: str = "stop"


class ConversationSettings(Protocol):
    language: str
    persona: str
    humor: int
    reply_length: str
    display_name: str | None
