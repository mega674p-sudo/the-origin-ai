import os
import sys

from core.ai_brain import GeminiBrain


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set; skipping live planning test.")
        return 0

    brain = GeminiBrain(api_key=api_key)
    plan = brain.plan_task("Inspect the current working directory and report free disk space.")
    print(plan)
    return 0 if plan.get("steps") else 1


if __name__ == "__main__":
    sys.exit(main())
