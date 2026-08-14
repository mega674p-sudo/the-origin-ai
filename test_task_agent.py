import os
import tempfile
import unittest

from core.task_agent import TaskAgent


class FakeBrain:
    def __init__(self, plan):
        self.plan = plan
        self.goals = []

    def plan_task(self, goal):
        self.goals.append(goal)
        return self.plan


class FakeCorrector:
    def __init__(self):
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return True, f"completed: {command}", ""


class TaskAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = os.path.join(self.temp_dir.name, "pending_task.json")
        self.plan = {
            "summary": "Inspect available disk capacity.",
            "steps": [
                {"tool": "run_bash", "command": "pwd", "purpose": "confirm the workspace"},
                {"tool": "run_bash", "command": "df -h", "purpose": "inspect disk capacity"},
            ],
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_task_requires_approval_before_execution(self):
        brain = FakeBrain(self.plan)
        task_agent = TaskAgent(brain, self.state_path)
        corrector = FakeCorrector()

        state, error = task_agent.create_task("Inspect disk capacity")
        self.assertEqual(error, "")
        self.assertEqual(state["status"], "awaiting_approval")
        self.assertEqual(corrector.commands, [])

        completed, message = task_agent.approve_and_execute(corrector)
        self.assertEqual(message, "Task completed.")
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(corrector.commands, ["pwd", "df -h"])

    def test_forbidden_plan_is_rejected(self):
        dangerous_plan = {
            "summary": "Unsafe plan.",
            "steps": [{"tool": "run_bash", "command": "rm -rf /", "purpose": "unsafe"}],
        }
        task_agent = TaskAgent(FakeBrain(dangerous_plan), self.state_path)

        state, error = task_agent.create_task("Delete everything")

        self.assertEqual(state, {})
        self.assertIn("Unsafe plan", error)
        self.assertFalse(os.path.exists(self.state_path))

    def test_cancel_removes_pending_task(self):
        task_agent = TaskAgent(FakeBrain(self.plan), self.state_path)
        task_agent.create_task("Inspect disk capacity")

        self.assertTrue(task_agent.cancel())
        self.assertEqual(task_agent.get_status(), {})


if __name__ == "__main__":
    unittest.main()
