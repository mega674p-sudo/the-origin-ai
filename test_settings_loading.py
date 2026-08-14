import json
import os
import unittest

from main import load_settings


class LocalSettingsTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__), "config", "settings.local.json")
        self.previous = None
        if os.path.exists(self.path):
            with open(self.path, "rb") as source:
                self.previous = source.read()

    def tearDown(self):
        if self.previous is None:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass
        else:
            with open(self.path, "wb") as destination:
                destination.write(self.previous)

    def test_local_values_override_template_placeholders(self):
        override = {
            "gemini": {"api_key": "test-gemini-key"},
            "telegram": {
                "bot_token": "test-bot-token",
                "chat_id": "111",
                "allowed_user_id": "222",
            },
        }
        with open(self.path, "w", encoding="utf-8") as destination:
            json.dump(override, destination)

        settings = load_settings()

        self.assertEqual(settings["gemini"]["api_key"], "test-gemini-key")
        self.assertEqual(settings["telegram"]["bot_token"], "test-bot-token")
        self.assertEqual(settings["telegram"]["chat_id"], "111")
        self.assertEqual(settings["telegram"]["allowed_user_id"], "222")


if __name__ == "__main__":
    unittest.main()
