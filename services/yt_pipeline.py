import os
import json
import requests
import subprocess
import time
import logging

logger = logging.getLogger("YTPipeline")

class YTPipeline:
    def __init__(self, api_key, output_dir="output"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
        os.makedirs(output_dir, exist_ok=True)

    def generate_script(self, topic):
        logger.info(f"Generating script for topic: {topic}")
        prompt = (
            f"Create a short viral video script about '{topic}'. "
            "Return ONLY a JSON object with the following structure: "
            "{'title': '...', 'scenes': [{'text': '...', 'image_prompt': '...'}]}. "
            "Keep it to 3-5 scenes. Each image_prompt should be descriptive for an AI image generator."
        )
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(f"{self.gemini_url}?key={self.api_key}", json=payload)
        
        if response.status_code == 200:
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Clean markdown if present
            content = content.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            raise Exception(f"Gemini API error: {response.text}")

    def generate_image(self, prompt, index):
        logger.info(f"Generating image {index} for prompt: {prompt}")
        # Using a reliable placeholder for testing assembly
        url = f"https://picsum.photos/seed/{index}/{1080}/{1920}"
        response = requests.get(url, allow_redirects=True)
        if response.status_code == 200:
            path = os.path.join(self.output_dir, f"scene_{index}.jpg")
            with open(path, "wb") as f:
                f.write(response.content)
            return path
        else:
            raise Exception("Image generation failed")

    def create_video(self, script_data):
        logger.info("Assembling video...")
        scenes = script_data["scenes"]
        image_paths = []
        
        for i, scene in enumerate(scenes):
            img_path = self.generate_image(scene["image_prompt"], i)
            image_paths.append(img_path)
            
        # Create a simple video using ffmpeg
        # For a real production, we'd add audio and transitions
        # Here we create a 15-second video (3 seconds per image)
        
        input_file = os.path.join(self.output_dir, "input.txt")
        with open(input_file, "w") as f:
            for path in image_paths:
                f.write(f"file '{os.path.abspath(path)}'\nduration 3\n")
            # Last file needs to be repeated or ffmpeg might cut it
            f.write(f"file '{os.path.abspath(image_paths[-1])}'\n")

        output_video = os.path.join(self.output_dir, "final_video.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_file,
            "-vsync", "vfr", "-pix_fmt", "yuv420p", output_video
        ]
        
        subprocess.run(cmd, check=True)
        return output_video

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Future of AI"
    api_key = os.getenv("GEMINI_API_KEY")
    
    pipeline = YTPipeline(api_key)
    script = pipeline.generate_script(topic)
    video = pipeline.create_video(script)
    print(f"Video created at: {video}")
