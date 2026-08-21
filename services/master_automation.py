import os
import json
import subprocess
import hashlib
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
HASH_FILE = "/home/ubuntu/the-origin-ai/uploaded_hashes.json"

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

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
    used = load_json(HISTORY_FILE)
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
        used.append(topic)
        save_json(HISTORY_FILE, used[-50:])
    except Exception as e:
        logger.error(f"Failed to generate topic: {e}")
        return

    # 1. Generate unique video for this topic
    if not run_step("Dynamic Video Generation", ["python3", "/home/ubuntu/the-origin-ai/services/generate_dynamic_video.py", topic]):
        return

    video_path = "/home/ubuntu/the-origin-ai/output_dynamic/final_video.mp4"
    if not os.path.exists(video_path):
        logger.error("Final video not found!")
        return

    # 2. Check duplicate hash
    file_hash = get_file_hash(video_path)
    uploaded_hashes = load_json(HASH_FILE)
    if file_hash in uploaded_hashes:
        logger.warning(f"Duplicate video detected (hash: {file_hash}). Skipping upload to prevent duplicate posting.")
        return

    # 3. Upload to YouTube
    yt_title = f"{topic} #Shorts #Science #BlurrContent"
    yt_desc = f"สำรวจความลึกลับของจักรวาล: {topic} ในสไตล์ Cinematic Science ดำดิ่งสู่ปริศนาที่คุณคาดไม่ถึง"
    
    if not run_step("YouTube Upload", ["python3", "/home/ubuntu/the-origin-ai/services/uploader.py", video_path, yt_title, yt_desc]):
        return

    uploaded_hashes.append(file_hash)
    save_json(HASH_FILE, uploaded_hashes[-50:])
    logger.info("Master automation completed successfully!")

if __name__ == "__main__":
    main()
