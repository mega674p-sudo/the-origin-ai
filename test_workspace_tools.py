import json
import os
import tempfile
import unittest

from core.policy import ToolPolicy
from core.workspace_tools import WorkspaceTools


class FakeExecutor:
    workspace = "/tmp/giga-workspace"

    def run(self, command):
        outputs = {
            "git status --short": " M main.py",
            "git diff --stat": " main.py | 10 +++++",
            "git diff --check": "",
            "git log -1 --oneline": "abc123 test commit",
        }
        value = outputs.get(command, "")
        return 0, value, ""


class WorkspaceToolsTests(unittest.TestCase):
    def test_review_collects_read_only_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            tools = WorkspaceTools(
                FakeExecutor(),
                ToolPolicy(),
                directory,
                os.path.join(directory, "pending.json"),
                os.path.join(directory, "memory.json"),
            )
            report = tools.review()
            self.assertEqual(report["risk"], "reviewed")
            self.assertEqual(len(report["checks"]), 4)
            self.assertIn("main.py", report["checks"][0]["output"])

    def test_checkpoint_writes_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            pending_path = os.path.join(directory, "pending.json")
            with open(pending_path, "w", encoding="utf-8") as pending_file:
                json.dump({"task_id": "task_test"}, pending_file)
            tools = WorkspaceTools(
                FakeExecutor(),
                ToolPolicy(),
                directory,
                pending_path,
                os.path.join(directory, "memory.json"),
            )
            result = tools.checkpoint("before-git")
            self.assertTrue(result["ok"])
            self.assertTrue(os.path.exists(result["path"]))
            self.assertEqual(result["snapshot"]["pending_task"]["task_id"], "task_test")


if __name__ == "__main__":
    unittest.main()
