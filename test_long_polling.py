import unittest
from unittest.mock import patch

from core.notifier import TelegramNotifier
from main import command_from_text


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class TelegramNotifierTests(unittest.TestCase):
    def setUp(self):
        self.notifier = TelegramNotifier("test-token", "123456")

    @patch("core.notifier.requests.get")
    def test_get_updates_uses_bounded_long_polling(self, mock_get):
        mock_get.return_value = FakeResponse({"ok": True, "result": [{"update_id": 7}]})

        updates = self.notifier.get_updates(offset=8, timeout=30)

        self.assertEqual(updates, [{"update_id": 7}])
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["timeout"], 30)
        self.assertEqual(kwargs["params"], {"timeout": 25, "offset": 8})

    @patch("core.notifier.requests.post")
    def test_notify_posts_to_configured_chat(self, mock_post):
        mock_post.return_value = FakeResponse({"ok": True, "result": {}})

        self.assertTrue(self.notifier.notify("listener online"))
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["chat_id"], "123456")
        self.assertEqual(kwargs["json"]["text"], "listener online")


class CommandParsingTests(unittest.TestCase):
    def test_command_from_text(self):
        self.assertEqual(command_from_text("/run uname -a"), "uname -a")
        self.assertEqual(command_from_text("/help"), "__HELP__")
        self.assertIsNone(command_from_text("  "))
        self.assertIsNone(command_from_text("uname -a"))


if __name__ == "__main__":
    unittest.main()
