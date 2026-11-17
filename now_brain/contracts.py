"""Strict versioned public contracts; no storage credentials or client identities."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Options(Contract):
    language: Literal["pt-BR", "en-US"] = "pt-BR"
    persona: Literal["classic", "casual", "gamer", "focus", "creative"] = "casual"
    humor: int = Field(default=1, ge=0, le=3)
    reply_length: Literal["short", "balanced", "detailed"] = "balanced"
    display_name: str | None = Field(default=None, min_length=1, max_length=80)


class Message(Contract):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(Contract):
    messages: list[Message] = Field(min_length=1, max_length=20)
    options: Options = Field(default_factory=Options)
    model_id: str | None = Field(default=None, min_length=1, max_length=200,
                                 pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
    # Correlation only: never used for identity, authorization or server storage.
    conversation_id: str | None = None
    mode: Literal["model", "offline"] = "model"

    @model_validator(mode="after")
    def valid_conversation(self):
        if self.conversation_id is not None:
            if str(UUID(self.conversation_id)) != self.conversation_id:
                raise ValueError("conversation_id must be a canonical UUID")
        if self.messages[-1].role != "user" or len(self.messages[-1].content) > 4000:
            raise ValueError("last message must be a user message of at most 4000 characters")
        if any(not message.content.strip() for message in self.messages):
            raise ValueError("messages cannot be blank")
        return self


class CancelRequest(Contract):
    request_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class Metrics(Contract):
    elapsed_ms: float
    first_token_ms: float | None = None
    output_tokens: int | None = None
    tokens_per_second: float | None = None


class ChatResult(Contract):
    api_version: Literal["1.0"] = "1.0"
    request_id: str
    conversation_id: str
    model_id: str | None
    provider_id: Literal["ollama", "offline"]
    status: Literal["completed", "truncated", "cancelled"]
    reply: str
    finish_reason: Literal["stop", "length", "cancelled"]
    context_messages: int
    context_trimmed: bool
    metrics: Metrics


class ErrorDetail(Contract):
    code: str
    request_id: str
    retryable: bool


class ErrorResult(Contract):
    api_version: Literal["1.0"] = "1.0"
    error: ErrorDetail


class ModelInfo(Contract):
    model_id: str
    digest: str | None = None
    size_bytes: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    license_status: Literal["not_audited"] = "not_audited"


class ModelList(Contract):
    api_version: Literal["1.0"] = "1.0"
    provider_id: Literal["ollama"] = "ollama"
    models: list[ModelInfo]
    default_model_id: str | None


class Health(Contract):
    api_version: Literal["1.0"] = "1.0"
    live: bool
    ready: bool
    instance_id: str
    profile: Literal["local"] = "local"
    provider_status: str


class CancelResult(Contract):
    api_version: Literal["1.0"] = "1.0"
    request_id: str
    status: Literal["cancelling"] = "cancelling"
