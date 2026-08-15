import os
import tempfile
import unittest

from core.playbooks import PlaybookStore


class PlaybookStoreTests(unittest.TestCase):
    def test_allowlisted_playbook_builds_goal(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "debug.md"), "w", encoding="utf-8") as playbook_file:
                playbook_file.write("Collect evidence first.")
            store = PlaybookStore(directory)
            goal = store.build_goal("debug", "diagnose failing test")
            self.assertIn("Collect evidence first.", goal)
            self.assertIn("diagnose failing test", goal)

    def test_unknown_playbook_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PlaybookStore(directory)
            self.assertEqual(store.build_goal("unknown", "anything"), "")


if __name__ == "__main__":
    unittest.main()
