import logging
import sys
from core.agent import GigaAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    print("=== Training & Testing GIGA PHONE AI Agent with Ollama (qwen2.5-coder:1.5b) ===")
    agent = GigaAgent()
    
    goal = "Create a python file named 'hello_giga.py' that prints system info, then execute it using bash, and finish."
    result = agent.run(goal, max_steps=4)
    print(f"\nAgent Final Result:\n{result}")

if __name__ == "__main__":
    main()
