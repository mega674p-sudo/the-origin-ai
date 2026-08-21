import os
import sys
import json
import subprocess
from google import genai
from gtts import gTTS

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_dynamic_video(topic, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Generating Biology Dynamic Video for Topic: {topic} ===")
    
    # 1. Generate Script & Scenes
    prompt = f"""
    Create a 4-scene script for a 45-second YouTube Short (Vertical 9:16) in Thai about Biology / Nature: "{topic}".
    Style: Blurr Content (Cinematic, Mysterious, Biological wonders).
    
    Return a valid JSON object with EXACTLY this structure (no markdown formatting, raw JSON only):
    {{
      "narration": "Full Thai script text to be spoken by Charon voice, continuous and smooth, about 45 seconds long.",
      "scenes": [
        {{"image_prompt": "Detailed 8K cinematic macro/nature image prompt in English for Scene 1"}},
        {{"image_prompt": "Detailed 8K cinematic macro/nature image prompt in English for Scene 2"}},
        {{"image_prompt": "Detailed 8K cinematic macro/nature image prompt in English for Scene 3"}},
        {{"image_prompt": "Detailed 8K cinematic macro/nature image prompt in English for Scene 4"}}
      ],
      "subtitles": [
        {{"start": 0.0, "end": 10.0, "text": "Sub 1"}},
        {{"start": 10.0, "end": 20.0, "text": "Sub 2"}},
        {{"start": 20.0, "end": 30.0, "text": "Sub 3"}},
        {{"start": 30.0, "end": 45.0, "text": "Sub 4"}}
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
    subtitles = data.get("subtitles", [])
    
    # Save script.json
    with open(os.path.join(output_dir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 2. Generate Thai Speech
    print("Generating speech...")
    speech_path = os.path.join(output_dir, "narration.mp3")
    tts = gTTS(text=narration_text, lang='th', slow=False)
    tts.save(speech_path)
    
    wav_path = os.path.join(output_dir, "narration.wav")
    subprocess.run(["ffmpeg", "-y", "-i", speech_path, "-ar", "24000", "-ac", "1", wav_path], check=True)
    
    # 3. Generate 8K Cinematic Images
    print("Generating scene images...")
    for i, scene in enumerate(scenes):
        img_path = os.path.join(output_dir, f"scene_{i+1}.png")
        img_prompt = scene["image_prompt"] + ", vertical 9:16, photorealistic, 8k, macro photography, dramatic lighting"
        try:
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
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=darkgreen:s=1080x1920:d=1",
                "-frames:v", "1", img_path
            ], check=True)

    # 4. Assemble video with ffmpeg & Extreme Audio Boost
    print("Assembling video...")
    
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        stdout=subprocess.PIPE, text=True, check=True
    )
    total_duration = float(probe.stdout.strip())
    scene_dur = total_duration / 4.0
    
    visuals = [
        {"type": "image", "path": os.path.join(output_dir, "scene_1.png"), "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_2.png"), "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_3.png"), "duration": scene_dur},
        {"type": "image", "path": os.path.join(output_dir, "scene_4.png"), "duration": total_duration - (3 * scene_dur)}
    ]
    
    scene_clips = []
    for i, vis in enumerate(visuals):
        out = os.path.join(output_dir, f"v_scene_{i}.mp4")
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
            "-vf", f"zoompan=z='min(zoom+0.0005,1.1)':d={int(vis['duration']*25)}:s=1080x1920",
            "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", out
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
    
    # Add subtitles
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"
    drawtext_filters = []
    for sub in subtitles:
        txt = sub["text"].replace("'", "").replace(":", "")
        start = sub["start"]
        end = sub["end"]
        filter_str = (
            f"drawtext=fontfile='{FONT_PATH}':text='{txt}':fontcolor=white:fontsize=60:"
            f"x=(w-text_w)/2:y=h-300:box=1:boxcolor=black@0.5:boxborderw=10:"
            f"enable='between(t,{start},{end})'"
        )
        drawtext_filters.append(filter_str)
        
    video_with_subs = os.path.join(output_dir, "temp_subs.mp4")
    if drawtext_filters:
        subprocess.run([
            "ffmpeg", "-y", "-i", concat_video,
            "-vf", ",".join(drawtext_filters),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", video_with_subs
        ], check=True)
    else:
        video_with_subs = concat_video

    final_video = os.path.join(output_dir, "final_video_high_quality.mp4")
    bgm_path = os.path.join(output_dir, "bgm.wav")
    if not os.path.exists(bgm_path):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(total_duration), bgm_path
        ], check=True)
        
    # Apply Extreme Volume Boost (volume=6.0 + compand + alimiter)
    subprocess.run([
        "ffmpeg", "-y", "-i", video_with_subs, "-i", wav_path, "-i", bgm_path,
        "-filter_complex", "[1:a]volume=6.0,compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,alimiter=limit=0.9[a1];[2:a]volume=0.6[a2];[a1][a2]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final_video
    ], check=True)
    
    print(f"Biology dynamic video successfully created at: {final_video}")
    return final_video

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "ความลับของเซลล์ในร่างกายมนุษย์"
    out_dir = "/home/ubuntu/the-origin-ai/output_dynamic"
    generate_dynamic_video(topic, out_dir)
