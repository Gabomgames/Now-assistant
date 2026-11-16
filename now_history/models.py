from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from uuid import UUID, uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def valid_id(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError("invalid conversation/message id")


def valid_time(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamps must have a timezone")
    return parsed


@dataclass(frozen=True)
class Message:
    id: str
    role: str
    content: str
    created_at: str
    status: str = "complete"
    provider: str | None = None

    def __post_init__(self):
        valid_id(self.id)
        valid_time(self.created_at)
        if self.role not in {"user", "assistant"} or self.status not in {"pending", "complete", "failed", "cancelled"}:
            raise ValueError("invalid message role/status")
        limit = 4000 if self.role == "user" else 12000
        if not isinstance(self.content, str) or not self.content.strip() or len(self.content) > limit:
            raise ValueError("invalid message content size")
        if self.provider not in {None, "offline", "local"}:
            raise ValueError("unsupported provider")


@dataclass(frozen=True)
class Conversation:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: tuple[Message, ...] = ()
    temporary: bool = True

    def __post_init__(self):
        valid_id(self.id)
        valid_time(self.created_at)
        valid_time(self.updated_at)
        if not isinstance(self.title, str) or not 1 <= len(self.title.strip()) <= 100:
            raise ValueError("invalid conversation title")
        if (len(self.messages) > 200 or len({message.id for message in self.messages}) != len(self.messages)
                or sum(len(message.content) for message in self.messages) > 200000):
            raise ValueError("conversation limit exceeded")
        if type(self.temporary) is not bool:
            raise ValueError("temporary must be a boolean")

    def append(self, role, text, *, status="complete", provider=None):
        message = Message(str(uuid4()), role, text, utc_now(), status, provider)
        title = self.title
        if not self.messages and role == "user":
            title = " ".join(text.split())[:70]
        return replace(self, title=title, updated_at=utc_now(), messages=(*self.messages, message))

    def mark_last_user(self, status):
        messages = list(self.messages)
        for index in range(len(messages) - 1, -1, -1):
            if messages[index].role == "user":
                messages[index] = replace(messages[index], status=status)
                break
        return replace(self, messages=tuple(messages), updated_at=utc_now())

    def context(self):
        # Failed/cancelled attempts are not silently replayed to a model.
        messages = [{"role": message.role, "content": message.content} for message in self.messages
                    if message.status == "complete" or (message.role == "user" and message.status == "pending")][-12:]
        while len(messages) > 1 and (sum(len(message["content"]) for message in messages) > 6000 or messages[0]["role"] != "user"):
            messages.pop(0)
        return messages

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) != {"id", "title", "created_at", "updated_at", "messages", "temporary"}:
            raise ValueError("invalid conversation fields")
        if not isinstance(value["messages"], list):
            raise ValueError("invalid messages")
        return cls(**{**value, "messages": tuple(Message(**message) for message in value["messages"])})


def new_conversation(title="Nova conversa", *, temporary=True):
    now = utc_now()
    return Conversation(str(uuid4()), title, now, now, temporary=temporary)
