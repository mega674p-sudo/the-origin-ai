import logging
import sys
from core.executor import CommandExecutor
from core.self_corrector import SelfCorrector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def main():
    print("=== Testing GIGA PHONE AI with Gemini API Self-Correction ===")
    executor = CommandExecutor()
    corrector = SelfCorrector(executor)
    
    # Test command that initially fails (e.g. non-existent command or bad python syntax)
    test_cmd = "python3 -c 'print(undefined_variable)'"
    success, stdout, stderr = corrector.execute_with_correction(test_cmd)
    
    print(f"Result -> Success: {success}")
    print(f"Stdout: {stdout}")
    print(f"Stderr: {stderr}")

if __name__ == "__main__":
    main()
