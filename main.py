import logging
import sys
from core.executor import CommandExecutor
from core.self_corrector import SelfCorrector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("GigaMain")

def main():
    logger.info("Initializing GIGA PHONE AI Agent...")
    executor = CommandExecutor()
    corrector = SelfCorrector(executor)
    
    # Test execution with self-correction
    test_cmd = "echo 'GIGA PHONE AI Agent is online and ready!'"
    success, stdout, stderr = corrector.execute_with_correction(test_cmd)
    
    if success:
        logger.info(f"Agent verification successful:\n{stdout}")
    else:
        logger.error(f"Agent verification failed: {stderr}")

if __name__ == "__main__":
    main()
