import random

from django.test import TestCase

from wx.services.chat_notifications import _acquire_debounce_lock, _release_debounce_lock


class RedisHealthTests(TestCase):
    def test_chat_unread_debounce_lock_roundtrip(self):
        conversation_id = random.randint(10_000_000, 99_999_999)
        user_id = random.randint(10_000_000, 99_999_999)
        ttl_seconds = 5

        _release_debounce_lock(conversation_id=conversation_id, user_id=user_id)

        first = _acquire_debounce_lock(
            conversation_id=conversation_id,
            user_id=user_id,
            ttl_seconds=ttl_seconds,
        )
        self.assertTrue(first)

        second = _acquire_debounce_lock(
            conversation_id=conversation_id,
            user_id=user_id,
            ttl_seconds=ttl_seconds,
        )
        self.assertFalse(second)

        _release_debounce_lock(conversation_id=conversation_id, user_id=user_id)

        third = _acquire_debounce_lock(
            conversation_id=conversation_id,
            user_id=user_id,
            ttl_seconds=ttl_seconds,
        )
        self.assertTrue(third)
