import os
import json
import subprocess
import logging
from google import genai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/ubuntu/the-origin-ai/automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MasterAutomation")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
HISTORY_FILE = "/home/ubuntu/the-origin-ai/used_topics.json"

def load_used_topics():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_used_topic(topic):
    topics = load_used_topics()
    topics.append(topic)
    # Keep last 50 topics
    if len(topics) > 50:
        topics = topics[-50:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

def run_step(name, cmd):
    logger.info(f"Starting step: {name}")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        logger.info(f"Step {name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step {name} failed with error:\n{e.stdout}")
        return False

def main():
    logger.info("Generating new science short topic...")
    used = load_used_topics()
    used_str = ", ".join(used[-10:]) if used else "None"
    
    topic_prompt = f"""
    Generate one fascinating, mysterious, and engaging topic in Thai for a cinematic science YouTube Short (Blurr Content style), such as about space, quantum physics, black holes, time, parallel universes, or deep cosmos mysteries.
    AVOID these recently used topics: {used_str}.
    Output ONLY the topic string in Thai, without quotes or extra text.
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=topic_prompt,
        )
        topic = response.text.strip()
        logger.info(f"Selected Topic: {topic}")
        save_used_topic(topic)
    except Exception as e:
        logger.error(f"Failed to generate topic: {e}")
        return

    if not run_step("Video Assembly", ["python3", "/home/ubuntu/the-origin-ai/services/assemble_dm_v2.py"]):
        return

    if not run_step("YouTube Upload", ["python3", "/home/ubuntu/the-origin-ai/services/uploader.py"]):
        return

    logger.info("Master automation completed successfully!")

if __name__ == "__main__":
    main()
