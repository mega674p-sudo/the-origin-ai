import os
import sys
import json
import subprocess
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_dynamic_video(topic, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Generating Dynamic Video for Topic: {topic} ===")
    
    # 1. Generate Script & Scenes
    prompt = f"""
    Create a 4-scene script for a 45-second YouTube Short (Vertical 9:16) in Thai about: "{topic}".
    Style: Blurr Content (Cinematic, Mysterious, Scientific).
    
    Return a valid JSON object with EXACTLY this structure (no markdown formatting, raw JSON only):
    {{
      "narration": "Full Thai script text to be spoken by Charon voice, continuous and smooth, about 45 seconds long.",
      "scenes": [
        {{"image_prompt": "Detailed 8K cinematic image prompt in English for Scene 1"}},
        {{"image_prompt": "Detailed 8K cinematic image prompt in English for Scene 2"}},
        {{"image_prompt": "Detailed 8K cinematic image prompt in English for Scene 3"}},
        {{"image_prompt": "Detailed 8K cinematic image prompt in English for Scene 4"}}
      ]
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    text_resp = response.text.strip()
    if text_resp.startswith("```json"):
        text_resp = text_resp[7:-3].strip()
    elif text_resp.startswith("```"):
        text_resp = text_resp[3:-3].strip()
        
    data = json.loads(text_resp)
    narration_text = data["narration"]
    scenes = data["scenes"]
    
    # 2. Generate Thai Speech using gTTS or text-to-speech
    print("Generating speech...")
    speech_path = os.path.join(output_dir, "narration.mp3")
    # Using gtts for reliable Thai speech generation
    from gtts import gTTS
    tts = gTTS(text=narration_text, lang='th', slow=False)
    tts.save(speech_path)
    
    # Convert mp3 to wav for ffmpeg
    wav_path = os.path.join(output_dir, "narration.wav")
    subprocess.run(["ffmpeg", "-y", "-i", speech_path, "-ar", "24000", "-ac", "1", wav_path], check=True)
    
    # 3. Generate 8K Cinematic Images using Gemini Imagen or Imagen 3 (or fallback to Gemini image gen)
    print("Generating scene images...")
    for i, scene in enumerate(scenes):
        img_path = os.path.join(output_dir, f"scene_{i+1}.png")
        img_prompt = scene["image_prompt"] + ", vertical 9:16, photorealistic, 8k, cinematic lighting"
        try:
            # Generate image using Gemini model supporting image generation
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=img_prompt,
                config=dict(number_of_images=1, aspect_ratio="9:16", output_mime_type="image/png")
            )
            for generated_image in result.generated_images:
                with open(img_path, "wb") as f:
                    f.write(generated_image.image.image_bytes)
            print(f"Generated image {i+1} using Imagen.")
        except Exception as e:
            print(f"Imagen failed ({e}), using fallback solid/gradient generator...")
            # Fallback: create a solid cinematic gradient image with ffmpeg
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=1080x1920:d=1",
                "-frames:v", "1", img_path
            ], check=True)

    # 4. Assemble video with ffmpeg
    print("Assembling video...")
    assets_dir = "/home/ubuntu/the-origin-ai/assets"
    
    # Get audio duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        stdout=subprocess.PIPE, text=True, check=True
    )
    total_duration = float(probe.stdout.strip())
    scene_dur = total_duration / 6.0
    
    visuals = [
        {"type": "image", "path": os.path.join(output_dir, "scene_1.png"), "duration": scene_dur},
        {"type": "video", "path": os.path.join(assets_dir, "nasa_roman_zoom.mp4"), "start": 0, "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_2.png"), "duration": scene_dur},
        {"type": "video", "path": os.path.join(assets_dir, "dark_matter_lensing.mov"), "start": 0, "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_3.png"), "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_4.png"), "duration": total_duration - (5 * scene_dur)}
    ]
    
    scene_clips = []
    for i, vis in enumerate(visuals):
        out = os.path.join(output_dir, f"v_scene_{i}.mp4")
        if vis["type"] == "image":
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
                "-vf", f"zoompan=z='min(zoom+0.0005,1.1)':d={int(vis['duration']*25)}:s=1080x1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", out
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-ss", str(vis["start"]), "-i", vis["path"],
                "-vf", "scale=w=-1:h=1920,crop=1080:1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out
            ]
        subprocess.run(cmd, check=True)
        scene_clips.append(out)
        
    concat_txt = os.path.join(output_dir, "concat.txt")
    with open(concat_txt, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")
            
    concat_video = os.path.join(output_dir, "concat_video.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", concat_video
    ], check=True)
    
    final_video = os.path.join(output_dir, "final_video.mp4")
    bgm_path = os.path.join(output_dir, "bgm.wav")
    # Generate ambient background music if not exists
    if not os.path.exists(bgm_path):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(total_duration), bgm_path
        ], check=True)
        
    subprocess.run([
        "ffmpeg", "-y", "-i", concat_video, "-i", wav_path, "-i", bgm_path,
        "-filter_complex", "[1:a]volume=2.0[a1];[2:a]volume=0.4[a2];[a1][a2]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final_video
    ], check=True)
    
    print(f"Dynamic video successfully created at: {final_video}")
    return final_video

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "หลุมดำจิ๋วที่อาจซ่อนอยู่ในระบบสุริยะ"
    out_dir = "/home/ubuntu/the-origin-ai/output_dynamic"
    generate_dynamic_video(topic, out_dir)
