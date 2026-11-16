"""Pure state/privacy checks; these do not claim GUI, model or audio execution."""
import unittest

from now_desktop.controller import ChatController


class ControllerTests(unittest.TestCase):
    def test_temporary_chat_never_becomes_persistent_by_enabling_future_history(self):
        controller = ChatController()
        temporary = controller.add_user("temporary private text")
        controller.history_enabled = True
        controller.finish(temporary.id, "deterministic fixture", "offline")
        self.assertTrue(controller.current.temporary)
        self.assertFalse(controller.new_chat().temporary)

    def test_disabling_history_forks_to_ram_and_lock_forgets_inherited_private_content(self):
        controller = ChatController()
        controller.history_enabled = True
        saved = controller.new_chat()
        controller.add_user("stored fixture")
        controller.finish(saved.id, "fixture reply", "offline")
        controller.history_enabled = False
        fork = controller.add_user("RAM only fixture")
        self.assertTrue(fork.temporary)
        self.assertNotEqual(fork.id, saved.id)
        controller.forget_persistent_cache()
        self.assertNotIn(saved.id, controller.cache)
        self.assertNotIn(fork.id, controller.cache)
        self.assertEqual(controller.current.messages, ())

    def test_storage_failure_preserves_unsaved_text_until_explicit_lock(self):
        controller = ChatController()
        controller.history_enabled = True
        original = controller.new_chat()
        controller.add_user("unsaved fixture")
        fork = controller.fork_temporary(original.id)
        self.assertTrue(fork.temporary)
        self.assertEqual(fork.messages[0].content, "unsaved fixture")
        self.assertNotIn(original.id, controller.cache)
        controller.forget_persistent_cache()
        self.assertNotIn(fork.id, controller.cache)

    def test_resuming_pending_request_marks_failed_and_never_replays_it_as_context(self):
        controller = ChatController()
        pending = controller.add_user("unfinished request fixture")
        controller.new_chat()
        controller.select(pending)
        self.assertEqual(controller.current.messages[0].status, "failed")
        self.assertEqual(controller.current.context(), [])

    def test_empty_temporary_chats_are_discarded_when_opening_a_new_chat(self):
        controller = ChatController()
        first = controller.current.id
        controller.new_chat()
        self.assertNotIn(first, controller.cache)
