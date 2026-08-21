import os
import json
import subprocess
import logging
from google import genai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/home/ubuntu/the-origin-ai/batch_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BatchGenerator")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
BACKLOG_DIR = "/home/ubuntu/the-origin-ai/backlog"
os.makedirs(BACKLOG_DIR, exist_ok=True)

TOPICS = [
    "ดาวเคราะห์ที่ฝนตกเป็นเพชร: ความจริงสุดขั้วบนดาวเนปจูน",
    "ทฤษฎีควอนตัม: วัตถุที่อยู่สองที่ได้ในเวลาเดียวกันจริงหรือ?",
    "อมตะมีจริง? ปริศนาแมงกะพรุนที่ไม่มีวันแก่และตาย",
    "กำแพงที่ใหญ่ที่สุดในจักรวาล: โครงข่ายสิ่งก่อสร้างยักษ์ที่มนุษย์ไม่เคยรู้",
    "ปรสิตควบคุมสมอง: เมื่อมดกลายเป็นซอมบี้กลางป่าดิบ",
    "ความเร็วแสง: ทำไมเราถึงไม่มีวันเดินทางเร็วกว่าแสงได้?",
    "เสียงของหลุมดำ: คลื่นความถี่และเสียงคำรามที่น่าขนลุกที่สุดในจักรวาล",
    "ความลับของ DNA: ข้อมูลทั้งหมดในโลกเก็บได้ในเม็ดทรายเพียงเม็ดเดียว",
    "ดาวเคราะห์สีเลือด: โลกปริศนาที่อาจมีสิ่งมีชีวิตซ่อนอยู่ใต้พื้นน้ำแข็ง",
    "การย้อนเวลา: ปริศนาปู่ (Grandfather Paradox) ที่ฟิสิกส์ยังหาทางออกไม่ได้"
]

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
    logger.info(f"Starting batch production for {len(TOPICS)} topics...")
    
    for i, topic in enumerate(TOPICS, 1):
        logger.info(f"\n====================\nProcessing Topic {i}/{len(TOPICS)}: {topic}\n====================")
        
        # 1. Temporarily write topic to a config file that assemble script can read
        topic_data = {"topic": topic}
        with open("/home/ubuntu/the-origin-ai/services/current_topic.json", "w", encoding="utf-8") as f:
            json.dump(topic_data, f, ensure_ascii=False)
            
        # 2. Run video assembly (which generates script, speech, images, and assembles final_video_v2.mp4)
        if not run_step(f"Assemble Video {i}", ["python3", "/home/ubuntu/the-origin-ai/services/assemble_dm_v2.py"]):
            logger.error(f"Failed to assemble video for topic: {topic}")
            continue
            
        # 3. Move the generated video to backlog
        src_video = "/home/ubuntu/the-origin-ai/output_dm/final_video_v2.mp4"
        dest_video = os.path.join(BACKLOG_DIR, f"backlog_video_{i:02d}.mp4")
        if os.path.exists(src_video):
            subprocess.run(["cp", src_video, dest_video], check=True)
            logger.info(f"Saved to backlog: {dest_video}")
            
            # Save metadata
            meta_path = os.path.join(BACKLOG_DIR, f"backlog_video_{i:02d}.json")
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump({"index": i, "topic": topic}, mf, ensure_ascii=False, indent=2)
        else:
            logger.error(f"Output video not found for topic: {topic}")

    logger.info("Batch generation process completed!")

if __name__ == "__main__":
    main()
