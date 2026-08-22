import os
import sys
import json
import subprocess
import base64
import time
import random
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_dynamic_video(topic, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== YouTube Shorts Automation Pipeline for Topic: {topic} ===")
    
    script_path = os.path.join(output_dir, "script.json")
    wav_path = os.path.join(output_dir, "narration.wav")
    
    # 1. Generate or Load Script
    if not os.path.exists(script_path):
        print("Step 1: Generating Script & Visual Plan...")
        prompt = f"""
        Create a 45-second YouTube Short (Vertical 9:16) script in Thai about: "{topic}".
        Style: Blurr Content (Cinematic, Mysterious, Scientific, Authoritative documentary).
        
        Return a valid JSON object with EXACTLY this structure:
        {{
          "narration": "Full Thai script text (about 45s long).",
          "segments": [
            {{
              "text": "Thai narration for segment 1",
              "image_prompt": "Literal visualization prompt in English"
            }},
            ... (repeat for all 6 segments)
          ],
          "subtitles": [
            {{"start": 0.0, "end": 7.5, "text": "Sub 1"}},
            ... (mapping the segments to time)
          ]
        }}
        """
        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        text_resp = response.text.strip()
        if text_resp.startswith("```json"): text_resp = text_resp[7:-3].strip()
        elif text_resp.startswith("```"): text_resp = text_resp[3:-3].strip()
        data = json.loads(text_resp)
        data["topic"] = topic
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        with open(script_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    narration_text = data["narration"]
    segments = data["segments"]
    subtitles = data.get("subtitles", [])

    # 2. Check for Narration Audio (Playbook Requirement)
    if not os.path.exists(wav_path):
        print("\n[ACTION_REQUIRED]")
        print(f"Please use the generate_speech tool with Charon voice for this Thai text:")
        print(f"TEXT: {narration_text}")
        print(f"SAVE_TO: {wav_path}")
        print("\nAfter generating the audio, re-run this script to complete the assembly.")
        sys.exit(0) # Exit cleanly to allow agent to perform tool call

    # 3. Generate Scene Visuals
    print("Step 3: Generating Visual Assets...")
    visual_sources = []
    for i, seg in enumerate(segments):
        img_path = os.path.join(output_dir, f"scene_{i+1}.png")
        # Always overwrite the scene asset. Reusing an existing filename is the
        # source of stale visuals appearing in later uploads.
        if os.path.exists(img_path):
            os.remove(img_path)
        img_prompt = seg["image_prompt"] + ", cinematic 8k, photorealistic, extreme detail, atmospheric lighting, professional documentary style, vertical 9:16"
        try:
            result = client.models.generate_images(
                model='gemini-3.1-flash-image',
                prompt=img_prompt,
                config=dict(number_of_images=1, aspect_ratio="9:16", output_mime_type="image/png")
            )
            for generated_image in result.generated_images:
                with open(img_path, "wb") as f:
                    f.write(generated_image.image.image_bytes)
        except Exception as e:
            print(f"Image {i+1} failed: {e}")

        if not os.path.exists(img_path):
            raise RuntimeError(f"Fresh image generation failed for scene {i+1}; refusing to use an old or generic fallback asset.")
        visual_sources.append({"type": "image", "path": img_path})

    # 4. Assemble video clips
    print("Step 4: Assembling Video...")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path], stdout=subprocess.PIPE, text=True, check=True)
    total_duration = float(probe.stdout.strip())
    
    num_scenes = len(visual_sources)
    scene_dur = total_duration / float(num_scenes)
    scene_clips = []
    for i, vis in enumerate(visual_sources):
        out = os.path.join(output_dir, f"v_scene_{i}.mp4")
        dur = scene_dur if i < num_scenes - 1 else total_duration - (i * scene_dur)
        if vis["type"] == "image":
            z_speed = 0.0006 + (random.random() * 0.0006)
            cmd = ["ffmpeg", "-y", "-loop", "1", "-i", vis["path"], "-vf", f"scale=2560:-1,zoompan=z='min(zoom+{z_speed},1.4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*30)}:s=1080x1920,fps=30", "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", out]
        else:
            cmd = ["ffmpeg", "-y", "-ss", str(vis.get("start", 0)), "-i", vis["path"], "-vf", "scale=w=-1:h=1920,crop=1080:1920,fps=30", "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-an", out]
        subprocess.run(cmd, check=True)
        scene_clips.append(out)
        
    concat_txt = os.path.join(output_dir, "concat.txt")
    with open(concat_txt, "w") as f:
        for clip in scene_clips: f.write(f"file '{clip}'\n")
            
    concat_video = os.path.join(output_dir, "concat_video.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18", concat_video], check=True)
    
    # 5. Add Subtitles
    print("Step 5: Adding Thai Subtitles...")
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"
    drawtext_filters = []
    for sub in subtitles:
        txt = sub["text"].replace("'", "").replace(":", "")
        start, end = float(sub["start"]), float(sub["end"])
        if start >= total_duration: continue
        if end > total_duration: end = total_duration
        filter_str = f"drawtext=fontfile='{FONT_PATH}':text='{txt}':fontcolor=white:fontsize=55:x=(w-text_w)/2:y=h-400:box=1:boxcolor=black@0.7:boxborderw=15:enable='between(t,{start},{end})'"
        drawtext_filters.append(filter_str)
        
    video_with_subs = os.path.join(output_dir, "temp_subs.mp4")
    if drawtext_filters:
        subprocess.run(["ffmpeg", "-y", "-i", concat_video, "-vf", ",".join(drawtext_filters), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", video_with_subs], check=True)
    else:
        video_with_subs = concat_video

    # 6. Mix Audio
    print("Step 6: Final Audio Mixing...")
    final_video = os.path.join(output_dir, "final_video_high_quality.mp4")
    bgm_path = os.path.join(output_dir, "bgm.wav")
    if not os.path.exists(bgm_path):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=40:d=60,lowpass=f=100,volume=0.4", "-t", str(total_duration), bgm_path], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", video_with_subs, "-i", wav_path, "-i", bgm_path, "-filter_complex", "[1:a]volume=8.0,loudnorm=I=-16:TP=-1.5:LRA=11[a1];[2:a]volume=0.3,lowpass=f=200[a2];[a1][a2]amix=inputs=2:duration=first[a]", "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", final_video], check=True)
    
    print(f"Dynamic video successfully created at: {final_video}")
    return final_video

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "ความลับของจักรวาล"
    out_dir = "/home/ubuntu/the-origin-ai/output_dynamic"
    generate_dynamic_video(topic, out_dir)
