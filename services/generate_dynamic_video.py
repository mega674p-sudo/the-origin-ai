import os
import sys
import json
import subprocess
import base64
import time
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_dynamic_video(topic, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Generating Dynamic Video (Improved Stability) for Topic: {topic} ===")
    
    # 1. Generate Script & Scenes & Subtitles
    prompt = f"""
    Create a 45-second YouTube Short (Vertical 9:16) script in Thai about: "{topic}".
    Style: Blurr Content (Cinematic, Mysterious, Scientific, Authoritative documentary).
    
    Return a valid JSON object with EXACTLY this structure (no markdown formatting, raw JSON only):
    {{
      "narration": "Full Thai script text to be spoken in a deep, mysterious, authoritative documentary style, continuous and smooth, about 45 seconds long.",
      "scenes": [
        {{"image_prompt": "Detailed 8K cinematic cosmic space image prompt in English for Scene 1"}},
        {{"image_prompt": "Detailed 8K cinematic cosmic space image prompt in English for Scene 2"}},
        {{"image_prompt": "Detailed 8K cinematic cosmic space image prompt in English for Scene 3"}},
        {{"image_prompt": "Detailed 8K cinematic cosmic space image prompt in English for Scene 4"}}
      ],
      "subtitles": [
        {{"start": 0.0, "end": 11.0, "text": "Sub 1"}},
        {{"start": 11.0, "end": 22.0, "text": "Sub 2"}},
        {{"start": 22.0, "end": 33.0, "text": "Sub 3"}},
        {{"start": 33.0, "end": 45.0, "text": "Sub 4"}}
      ]
    }}
    """
    
    print("Requesting script from Gemini...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
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
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                sys.exit(1)
            time.sleep(5)
            
    narration_text = data["narration"]
    scenes = data["scenes"]
    subtitles = data.get("subtitles", [])
    
    # Save script.json
    with open(os.path.join(output_dir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 2. Generate Authentic Charon Voice using Gemini TTS API
    print("Generating authentic Charon voice via Gemini TTS...")
    tts_prompt = f"Speak in a deep, mysterious, authoritative, and informative documentary style in Thai: {narration_text}"
    
    wav_path = os.path.join(output_dir, "narration.wav")
    tts_success = False
    
    try:
        # Try interactions API
        interaction = client.interactions.create(
            model="gemini-3.1-flash-tts-preview",
            input=tts_prompt,
            response_format={"type": "audio"},
            generation_config={
                "speech_config": [
                    {"voice": "Charon"}
                ]
            }
        )
        
        if interaction.output_audio and interaction.output_audio.data:
            pcm_bytes = base64.b64decode(interaction.output_audio.data)
            if len(pcm_bytes) > 1000:
                pcm_raw_path = os.path.join(output_dir, "narration.pcm")
                with open(pcm_raw_path, "wb") as f:
                    f.write(pcm_bytes)
                subprocess.run([
                    "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                    "-i", pcm_raw_path, wav_path
                ], check=True)
                tts_success = True
                print("Gemini TTS (Charon) generated successfully.")
    except Exception as e:
        print(f"Gemini TTS Interaction Failed: {e}")

    if not tts_success:
        # Fallback to gTTS with deep pitch shift
        print("Falling back to gTTS with deep pitch shift (Simulated Charon)...")
        from gtts import gTTS
        temp_mp3 = os.path.join(output_dir, "temp_gtts.mp3")
        tts = gTTS(text=narration_text, lang='th')
        tts.save(temp_mp3)
        # Deep pitch shift: lower sample rate, keep tempo
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_mp3, 
            "-af", "asetrate=24000*0.8,aresample=24000,atempo=1.25", 
            wav_path
        ], check=True)
    
    # Get exact audio duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        stdout=subprocess.PIPE, text=True, check=True
    )
    total_duration = float(probe.stdout.strip())
    print(f"Exact narration duration: {total_duration}s")
    
    # 3. Generate 8K Cinematic Images
    print("Generating scene images / assets...")
    assets_dir = "/home/ubuntu/the-origin-ai/assets"
    nasa_roman = os.path.join(assets_dir, "nasa_roman_zoom.mp4")
    nasa_lensing = os.path.join(assets_dir, "dark_matter_lensing.mov")
    
    visual_sources = []
    for i, scene in enumerate(scenes):
        img_path = os.path.join(output_dir, f"scene_{i+1}.png")
        img_prompt = scene["image_prompt"] + ", vertical 9:16, photorealistic 8k, vibrant cosmic nebula, glowing stars, cinematic lighting"
        success = False
        try:
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=img_prompt,
                config=dict(number_of_images=1, aspect_ratio="9:16", output_mime_type="image/png")
            )
            for generated_image in result.generated_images:
                with open(img_path, "wb") as f:
                    f.write(generated_image.image.image_bytes)
            if os.path.exists(img_path) and os.path.getsize(img_path) > 10000:
                visual_sources.append({"type": "image", "path": img_path})
                success = True
                print(f"Generated AI image {i+1} successfully.")
        except Exception as e:
            print(f"Imagen failed for scene {i+1} ({e}), using NASA stock fallback...")
            
        if not success:
            if i % 2 == 0 and os.path.exists(nasa_roman):
                visual_sources.append({"type": "video", "path": nasa_roman, "start": i * 5})
            elif os.path.exists(nasa_lensing):
                visual_sources.append({"type": "video", "path": nasa_lensing, "start": i * 5})
            else:
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=navy:s=1080x1920:d=1",
                    "-frames:v", "1", img_path
                ], check=True)
                visual_sources.append({"type": "image", "path": img_path})

    # 4. Assemble video clips
    print("Assembling video clips...")
    scene_dur = total_duration / float(len(visual_sources))
    
    scene_clips = []
    for i, vis in enumerate(visual_sources):
        out = os.path.join(output_dir, f"v_scene_{i}.mp4")
        dur = scene_dur
        if i == len(visual_sources) - 1:
            dur = total_duration - (i * scene_dur)
            
        if vis["type"] == "image":
            # Fixed zoom effect to prevent flickering
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
                "-vf", f"scale=2160:-1,zoompan=z='min(zoom+0.0005,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*30)}:s=1080x1920,fps=30",
                "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", out
            ]
        else:
            start_t = vis.get("start", 0)
            cmd = [
                "ffmpeg", "-y", "-ss", str(start_t), "-i", vis["path"],
                "-vf", "scale=w=-1:h=1920,crop=1080:1920,fps=30",
                "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-an", out
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
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18", concat_video
    ], check=True)
    
    # 5. Add Subtitles
    print("Adding Thai subtitles...")
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"
    drawtext_filters = []
    for sub in subtitles:
        txt = sub["text"].replace("'", "").replace(":", "")
        start = float(sub["start"])
        end = float(sub["end"])
        if start >= total_duration:
            continue
        if end > total_duration:
            end = total_duration
            
        filter_str = (
            f"drawtext=fontfile='{FONT_PATH}':text='{txt}':fontcolor=white:fontsize=60:"
            f"x=(w-text_w)/2:y=h-400:box=1:boxcolor=black@0.7:boxborderw=15:"
            f"enable='between(t,{start},{end})'"
        )
        drawtext_filters.append(filter_str)
        
    video_with_subs = os.path.join(output_dir, "temp_subs.mp4")
    if drawtext_filters:
        subprocess.run([
            "ffmpeg", "-y", "-i", concat_video,
            "-vf", ",".join(drawtext_filters),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", video_with_subs
        ], check=True)
    else:
        video_with_subs = concat_video

    # 6. Mix Audio with Extreme Loudness Boost
    print("Mixing audio with Extreme Loudness Boost...")
    final_video = os.path.join(output_dir, "final_video_high_quality.mp4")
    
    bgm_path = os.path.join(output_dir, "bgm.wav")
    if not os.path.exists(bgm_path):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=40:d=60,lowpass=f=100,volume=0.5",
            "-t", str(total_duration), bgm_path
        ], check=True)
        
    subprocess.run([
        "ffmpeg", "-y", "-i", video_with_subs, "-i", wav_path, "-i", bgm_path,
        "-filter_complex", "[1:a]volume=8.0,loudnorm=I=-16:TP=-1.5:LRA=11[a1];[2:a]volume=0.4,lowpass=f=200[a2];[a1][a2]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", final_video
    ], check=True)
    
    print(f"Dynamic video successfully created at: {final_video}")
    return final_video

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "ความลับของจักรวาล"
    out_dir = "/home/ubuntu/the-origin-ai/output_dynamic"
    generate_dynamic_video(topic, out_dir)
