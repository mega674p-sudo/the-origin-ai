import os
import tempfile
import unittest

from core.executor import CommandExecutor


class ExecutorTests(unittest.TestCase):
    def test_commands_run_in_configured_workspace(self):
        with tempfile.TemporaryDirectory() as workspace:
            executor = CommandExecutor(timeout=5, workspace=workspace)
            code, stdout, stderr = executor.run("pwd")

            self.assertEqual(code, 0)
            self.assertEqual(os.path.realpath(stdout), os.path.realpath(workspace))
            self.assertEqual(stderr, "")

    def test_output_is_bounded(self):
        with tempfile.TemporaryDirectory() as workspace:
            executor = CommandExecutor(timeout=5, workspace=workspace, max_output=1000)
            code, stdout, stderr = executor.run("python3 -c \"print('x' * 5000)\"")

            self.assertEqual(code, 0)
            self.assertLessEqual(len(stdout), 1000)
            self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
