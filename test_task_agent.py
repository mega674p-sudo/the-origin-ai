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


class FakeBrainWithRoles(FakeBrain):
    def security_review(self, goal, steps):
        return {"approved": True, "risk": "low", "issues": [], "required_confirmation": "none"}

    def verify_result(self, goal, command, stdout, stderr=""):
        return {"verified": True, "confidence": "high", "reason": "test evidence is present"}


class FakeVerifier:
    def run(self, command):
        return {"status": "passed", "verified": True, "command": command, "evidence": "ok"}


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
        self.assertTrue(state["task_id"].startswith("task_"))
        self.assertEqual(corrector.commands, [])

        pending_state, message = task_agent.approve_and_execute(corrector, "wrong-id")
        self.assertEqual(pending_state, {})
        self.assertIn("exact task ID", message)
        self.assertEqual(corrector.commands, [])

        completed, message = task_agent.approve_and_execute(corrector, state["task_id"])
        self.assertEqual(message, "Task completed with verification evidence.")
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(corrector.commands, ["pwd", "df -h"])

    def test_role_pipeline_records_security_and_verification(self):
        plan = {
            "summary": "Inspect workspace.",
            "steps": [{"tool": "run_bash", "command": "pwd", "purpose": "workspace", "verify": "pwd"}],
        }
        task_agent = TaskAgent(FakeBrainWithRoles(plan), self.state_path, verifier=FakeVerifier())
        corrector = FakeCorrector()

        state, error = task_agent.create_task("Inspect workspace")
        self.assertEqual(error, "")
        completed, message = task_agent.approve_and_execute(corrector, state["task_id"])

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["security"]["risk"], "low")
        self.assertEqual(completed["results"][0]["verification"]["status"], "passed")
        self.assertEqual(message, "Task completed with verification evidence.")

    def test_git_mutation_requires_checkpoint(self):
        git_plan = {
            "summary": "Commit reviewed changes.",
            "steps": [{"tool": "run_bash", "command": "git commit -am 'reviewed changes'", "purpose": "commit"}],
        }
        checkpoint_dir = os.path.join(self.temp_dir.name, "checkpoints")
        task_agent = TaskAgent(FakeBrain(git_plan), self.state_path, checkpoint_dir=checkpoint_dir)
        corrector = FakeCorrector()

        state, error = task_agent.create_task("Commit reviewed changes")
        self.assertEqual(error, "")
        paused, message = task_agent.approve_and_execute(corrector, state["task_id"])

        self.assertEqual(paused["status"], "checkpoint_required")
        self.assertIn("checkpoint", message.lower())
        self.assertEqual(corrector.commands, [])

        os.makedirs(checkpoint_dir, exist_ok=True)
        with open(os.path.join(checkpoint_dir, "before-git.json"), "w", encoding="utf-8") as checkpoint_file:
            checkpoint_file.write("{}")
        completed, message = task_agent.approve_and_execute(corrector, state["task_id"])
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(corrector.commands, ["git commit -am 'reviewed changes'"])

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

    def test_cancel_requires_matching_task_id(self):
        task_agent = TaskAgent(FakeBrain(self.plan), self.state_path)
        state, _ = task_agent.create_task("Inspect disk capacity")

        self.assertFalse(task_agent.cancel("wrong-id"))
        self.assertTrue(task_agent.cancel(state["task_id"]))
        self.assertEqual(task_agent.get_status(), {})


if __name__ == "__main__":
    unittest.main()
