import json
import logging
import requests
import os
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
            "options": {"temperature": 0.0, "num_predict": 256}
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return json.loads(response.json().get("response", "{}"))
            return {}
        except:
            return {}

    def execute_tool(self, tool_name: str, arg) -> str:
        # Ensure arg is string
        if isinstance(arg, dict):
            arg = json.dumps(arg)
        arg = str(arg).strip().strip("'\"")
        
        logger.info(f"Action: {tool_name} | Arg: {arg}")
        
        if tool_name == "run_bash":
            success, stdout, stderr = self.corrector.execute_with_correction(arg)
            return f"STDOUT: {stdout}\nSTDERR: {stderr}"
        elif tool_name == "write_file":
            try:
                if "|||" in arg:
                    path, content = arg.split("|||", 1)
                else:
                    return "Error: Use 'path ||| content'"
                path = path.strip().strip("'\"")
                content = content.strip().strip("'\"")
                with open(path, "w") as f:
                    f.write(content)
                return f"Success: {path} written."
            except Exception as e:
                return f"Error: {str(e)}"
        elif tool_name == "read_file":
            try:
                with open(arg, "r") as f: return f.read()
            except Exception as e: return str(e)
        return "Unknown tool"

    def run(self, goal: str, max_steps: int = 5):
        system = """You are GIGA PHONE AI. Output ONLY JSON: {"thought": "...", "tool": "...", "arg": "..."}
Tools: write_file (path ||| content), run_bash (cmd), read_file (path), finish (summary)."""
        
        history = f"Goal: {goal}\n"
        for step in range(max_steps):
            decision = self.call_llm(f"{system}\n\n{history}\nNext Step (JSON):")
            tool = decision.get("tool")
            arg = decision.get("arg")
            if tool == "finish" or not tool:
                return arg if arg else "Finished."
            obs = self.execute_tool(tool, arg)
            history += f"Step {step+1}: {tool} -> {obs}\n"
        return "Max steps reached."
