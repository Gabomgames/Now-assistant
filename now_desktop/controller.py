"""In-memory conversation state. Persistence is explicit and delegated to a history service."""
from dataclasses import replace
from uuid import uuid4

from now_history.models import new_conversation, utc_now

DEFAULT_SETTINGS = {"language": "pt-BR", "persona": "casual", "humor": 1, "reply_length": "balanced", "display_name": None}


class ChatController:
    def __init__(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.history_enabled = False
        self.cache = {}
        self._history_origins = {}
        self.current = self.new_chat()

    def new_chat(self):
        previous = getattr(self, "current", None)
        if previous is not None and previous.temporary and not previous.messages:
            self.cache.pop(previous.id, None)
        self.current = new_conversation(temporary=not self.history_enabled)
        self.cache[self.current.id] = self.current
        return self.current

    def select(self, conversation):
        messages = tuple(replace(message, status="failed") if message.status == "pending" else message for message in conversation.messages)
        self.current = replace(conversation, messages=messages)
        self.cache[self.current.id] = self.current
        return self.current

    def _update(self, conversation):
        self.cache[conversation.id] = conversation
        if conversation.id == self.current.id:
            self.current = conversation
        return conversation

    def add_user(self, text):
        if not self.current.temporary and not self.history_enabled:
            original = self.current
            self.current = replace(original, id=str(uuid4()), temporary=True, updated_at=utc_now())
            self._history_origins[self.current.id] = original.id
        return self._update(self.current.append("user", text, status="pending"))

    def finish(self, identifier, reply, provider):
        conversation = self.cache[identifier].mark_last_user("complete").append("assistant", reply, provider=provider)
        return self._update(conversation)

    def fail(self, identifier, *, cancelled=False):
        return self._update(self.cache[identifier].mark_last_user("cancelled" if cancelled else "failed"))

    def rename(self, identifier, title):
        return self._update(replace(self.cache[identifier], title=title.strip(), updated_at=utc_now()))

    def forget_persistent_cache(self):
        self.cache = {identifier: conversation for identifier, conversation in self.cache.items()
                      if conversation.temporary and identifier not in self._history_origins}
        self._history_origins.clear()
        self.history_enabled = False
        if self.current.id not in self.cache:
            self.new_chat()

    def delete_cached(self, identifier):
        affected = {identifier} | {key for key, source in self._history_origins.items() if source == identifier}
        for key in affected:
            self.cache.pop(key, None)
            self._history_origins.pop(key, None)
        if self.current.id in affected:
            self.new_chat()

    def fork_temporary(self, identifier):
        original = self.cache.pop(identifier)
        conversation = replace(original, id=str(uuid4()), temporary=True)
        self._history_origins[conversation.id] = identifier
        self.cache[conversation.id] = conversation
        if self.current.id == identifier:
            self.current = conversation
        return conversation

    def temporary_summaries(self, query=""):
        query = query.strip().casefold()
        result = []
        for conversation in self.cache.values():
            if conversation.temporary and (not query or query in conversation.title.casefold() or any(query in message.content.casefold() for message in conversation.messages)):
                result.append({"id": conversation.id, "title": conversation.title, "updated_at": conversation.updated_at,
                               "message_count": len(conversation.messages), "temporary": True})
        return result
