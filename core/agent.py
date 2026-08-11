import json
import logging
import requests
from core.executor import CommandExecutor
from core.self_corrector import SelfCorrector

logger = logging.getLogger("GigaAgent")

class GigaAgent:
    def __init__(self, model_name: str = "qwen2.5-coder:1.5b", ollama_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.executor = CommandExecutor()
        self.corrector = SelfCorrector(self.executor)

    def call_llm(self, prompt: str) -> dict:
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 256
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                raw_text = response.json().get("response", "{}")
                return json.loads(raw_text)
            else:
                return {"thought": "API Error", "tool": "finish", "arg": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"thought": "Exception", "tool": "finish", "arg": str(e)}

    def execute_tool(self, tool_name: str, arg: str) -> str:
        arg = arg.strip()
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            arg = arg[1:-1]

        logger.info(f"Executing tool [{tool_name}] with arg: {arg}")
        if tool_name == "run_bash":
            success, stdout, stderr = self.corrector.execute_with_correction(arg)
            return f"SUCCESS:\n{stdout}" if success else f"FAILURE:\n{stderr}"
        elif tool_name == "read_file":
            try:
                with open(arg, "r") as f:
                    return f"CONTENT:\n{f.read()}"
            except Exception as e:
                return f"Error: {str(e)}"
        elif tool_name == "write_file":
            try:
                parts = arg.split("|||", 1)
                path = parts[0].strip()
                if (path.startswith("'") and path.endswith("'")) or (path.startswith('"') and path.endswith('"')):
                    path = path[1:-1]
                content = parts[1] if len(parts) > 1 else ""
                with open(path, "w") as f:
                    f.write(content)
                return f"SUCCESS: Written to {path}"
            except Exception as e:
                return f"Error: {str(e)}"
        elif tool_name == "finish":
            return f"FINISHED: {arg}"
        else:
            return f"Unknown tool: {tool_name}"

    def run(self, goal: str, max_steps: int = 5):
        logger.info(f"Agent started with goal: {goal}")
        
        system_prompt = """You are GIGA PHONE AI, an autonomous agent. Respond ONLY in valid JSON format with keys: "thought", "tool", "arg".
Available tools:
- "write_file": arg format "<path> ||| <content>"
- "read_file": arg format "<path>"
- "run_bash": arg format "<bash command>"
- "finish": arg format "<summary of completed task>"
"""

        conversation = f"{system_prompt}\nGoal: {goal}\n"

        for step in range(max_steps):
            logger.info(f"=== Step {step + 1}/{max_steps} ===")
            decision = self.call_llm(conversation)
            logger.info(f"Agent Decision: {json.dumps(decision, indent=2)}")

            tool = decision.get("tool")
            arg = decision.get("arg", "")

            if tool == "finish":
                logger.info(f"Task finished: {arg}")
                return arg

            if tool and arg:
                observation = self.execute_tool(tool, arg)
                logger.info(f"Observation:\n{observation}")
                conversation += f"\nResponse: {json.dumps(decision)}\nObservation: {observation}\n"
            else:
                conversation += f"\nResponse: {json.dumps(decision)}\nObservation: Invalid tool format. Use JSON.\n"

        return "Max steps reached."
