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
    logger.info("=== Starting Master Automation Run (End-to-End Charon TTS) ===")
    
    script_path = "/home/ubuntu/the-origin-ai/output_dynamic/script.json"
    wav_path = "/home/ubuntu/the-origin-ai/output_dynamic/narration.wav"
    video_path = "/home/ubuntu/the-origin-ai/output_dynamic/final_video_high_quality.mp4"
    
    topic = None
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                topic = data.get("topic") # We'll need to add topic to script.json
                logger.info(f"Resuming existing run for topic: {topic}")
        except:
            pass

    if not topic:
        # Start each new job from a clean workspace. Old scene images and intermediate
        # videos must never be eligible for a new topic.
        stale_prefixes = ("scene_", "v_scene_", "final_scene_")
        stale_names = {
            "final_video_high_quality.mp4", "final_video.mp4", "concat.txt",
            "concat_final.txt", "concat_video.mp4", "temp_concat.mp4",
            "temp_subs.mp4", "bgm.wav", "narration.wav", "narration.pcm",
            "narration.mp3", "narration_raw.mp3", "narration_raw.wav",
            "NEED_SPEECH.txt", "script.json"
        }
        output_dir = "/home/ubuntu/the-origin-ai/output_dynamic"
        for name in os.listdir(output_dir):
            if name in stale_names or name.startswith(stale_prefixes):
                path = os.path.join(output_dir, name)
                if os.path.isfile(path):
                    os.remove(path)
        
        used = load_json(HISTORY_FILE)
        used_str = ", ".join(used) if used else "None"
        topic_prompt = f"""
        Generate one unique, fascinating, mysterious, and engaging topic in Thai for a cinematic science YouTube Short (Blurr Content style).
        Focus on: Deep space mysteries, quantum paradoxes, theoretical physics, or cosmic anomalies.
        STRICT RULE: You MUST NOT repeat or generate anything similar to these previous topics: {used_str}.
        Output ONLY the topic string in Thai.
        """
        try:
            response = client.models.generate_content(model="gemini-3.6-flash", contents=topic_prompt)
            topic = response.text.strip()
            logger.info(f"Selected New Topic: {topic}")
            used.append(topic)
            save_json(HISTORY_FILE, used[-500:])
            # Clean start
            if os.path.exists(video_path): os.remove(video_path)
            if os.path.exists(wav_path): os.remove(wav_path)
        except Exception as e:
            logger.error(f"Failed to generate topic: {e}")
            return

    # 2. Generate video (Script, Visuals, Assembly)
    logger.info(f"Running Dynamic Video Generation for topic: {topic}")
    result = subprocess.run(["python3", "/home/ubuntu/the-origin-ai/services/generate_dynamic_video.py", topic], 
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    print(result.stdout) # Show output to agent for Playbook actions
    
    if "[ACTION_REQUIRED]" in result.stdout:
        logger.info("Speech generation required by playbook.")
        return # Exit this run, agent will follow playbook
        
    if result.returncode != 0:
        logger.error(f"Video generation failed:\n{result.stdout}")
        return

    if not os.path.exists(video_path):
        logger.error("Final video not found after generation!")
        return

    # 2. Check duplicate hash
    file_hash = get_file_hash(video_path)
    uploaded_hashes = load_json(HASH_FILE)
    if file_hash in uploaded_hashes:
        logger.warning(f"Duplicate video detected (hash: {file_hash}). Skipping upload to prevent duplicate posting.")
        return

    # 3. Upload to YouTube
    yt_title = f"{topic} #Shorts #Science #BlurrContent"
    if len(yt_title) > 100:
        yt_title = yt_title[:97] + "..."
    yt_desc = f"สำรวจความลึกลับของจักรวาล: {topic} ในสไตล์ Cinematic Science ดำดิ่งสู่ปริศนาที่คุณคาดไม่ถึง"
    
    if not run_step("YouTube Upload", ["python3", "/home/ubuntu/the-origin-ai/services/uploader.py", video_path, yt_title, yt_desc]):
        return

    uploaded_hashes.append(file_hash)
    save_json(HASH_FILE, uploaded_hashes[-100:])
    
    # Cleanup after successful upload
    if os.path.exists(script_path): os.remove(script_path)
    if os.path.exists(wav_path): os.remove(wav_path)
    
    logger.info("Master automation completed successfully!")

if __name__ == "__main__":
    main()
