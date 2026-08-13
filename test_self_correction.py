import unittest
from unittest.mock import patch

from core.ai_brain import GeminiBrain
from core.self_corrector import SelfCorrector


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload or {}

    def json(self):
        return self.payload


class FakeExecutor:
    def __init__(self):
        self.max_retries = 2
        self.commands = []

    def run(self, command):
        self.commands.append(command)
        if command == "echo repaired":
            return 0, "repaired", ""
        return 1, "", "command not found"


class GeminiBackoffTests(unittest.TestCase):
    @patch("core.ai_brain.time.sleep")
    @patch("core.ai_brain.requests.post")
    def test_rate_limit_retries_with_exponential_backoff(self, mock_post, mock_sleep):
        mock_post.side_effect = [
            FakeResponse(429),
            FakeResponse(429),
            FakeResponse(200, {
                "candidates": [{"content": {"parts": [{"text": "echo repaired"}]}}]
            }),
        ]
        brain = GeminiBrain(api_key="test-key")

        fixed = brain.analyze_error("bad-command", "command not found")

        self.assertEqual(fixed, "echo repaired")
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual([call.args[0] for call in mock_sleep.call_args_list], [1, 2])


class SelfCorrectionTests(unittest.TestCase):
    def test_failed_command_is_retried_with_gemini_suggestion(self):
        executor = FakeExecutor()
        corrector = SelfCorrector(executor, api_key="test-key")
        corrector.brain.analyze_error = lambda command, stderr: "echo repaired"

        success, stdout, stderr = corrector.execute("bad-command")

        self.assertTrue(success)
        self.assertEqual(stdout, "repaired")
        self.assertEqual(stderr, "")
        self.assertEqual(executor.commands, ["bad-command", "echo repaired"])


if __name__ == "__main__":
    unittest.main()
