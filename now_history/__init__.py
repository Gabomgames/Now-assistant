"""Opt-in encrypted conversation history, separate from NOW Memory preferences."""

from .models import Conversation, Message, new_conversation
from .store import HistoryStore

__all__ = ["Conversation", "Message", "HistoryStore", "new_conversation"]
