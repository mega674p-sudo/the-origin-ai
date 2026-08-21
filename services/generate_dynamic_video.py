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

def generate_dynamic_video(topic, output_dir, skip_generation=False):
    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Assembling Dynamic Video (High Relevance Visuals) for Topic: {topic} ===")
    
    script_path = os.path.join(output_dir, "script.json")
    if not os.path.exists(script_path):
        print("Error: script.json not found. Run generation first.")
        sys.exit(1)
        
    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    narration_text = data["narration"]
    segments = data["segments"]
    subtitles = data.get("subtitles", [])
    
    wav_path = os.path.join(output_dir, "narration.wav")
    if not os.path.exists(wav_path):
        print("Generating authentic Charon voice...")
        tts_prompt = f"Speak in a deep, mysterious, authoritative, and informative documentary style in Thai: {narration_text}"
        try:
            interaction = client.interactions.create(
                model="gemini-3.1-flash-tts-preview",
                input=tts_prompt,
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": "Charon"}]}
            )
            if interaction.output_audio and interaction.output_audio.data:
                pcm_bytes = base64.b64decode(interaction.output_audio.data)
                pcm_raw_path = os.path.join(output_dir, "narration.pcm")
                with open(pcm_raw_path, "wb") as f:
                    f.write(pcm_bytes)
                subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", pcm_raw_path, wav_path], check=True)
        except Exception as e:
            print(f"TTS Failed: {e}")
            # Fallback to existing or gTTS...
    
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path],
        stdout=subprocess.PIPE, text=True, check=True
    )
    total_duration = float(probe.stdout.strip())
    
    # 3. Collect Scene Visuals (Pre-generated)
    visual_sources = []
    for i in range(len(segments)):
        img_path = os.path.join(output_dir, f"scene_{i+1}.png")
        if os.path.exists(img_path):
            visual_sources.append({"type": "image", "path": img_path})
        else:
            print(f"Warning: scene_{i+1}.png not found, using fallback.")
            visual_sources.append({"type": "video", "path": "/home/ubuntu/the-origin-ai/assets/nasa_roman_zoom.mp4", "start": i*5})

    # 4. Assemble video clips
    print("Assembling video clips...")
    num_scenes = len(visual_sources)
    scene_dur = total_duration / float(num_scenes)
    
    scene_clips = []
    for i, vis in enumerate(visual_sources):
        out = os.path.join(output_dir, f"v_scene_{i}.mp4")
        dur = scene_dur
        if i == num_scenes - 1:
            dur = total_duration - (i * scene_dur)
            
        if vis["type"] == "image":
            z_speed = 0.0006 + (random.random() * 0.0006)
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
                "-vf", f"scale=2560:-1,zoompan=z='min(zoom+{z_speed},1.4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(dur*30)}:s=1080x1920,fps=30",
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
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18", concat_video], check=True)
    
    # 5. Add Subtitles
    print("Adding Thai subtitles...")
    FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"
    drawtext_filters = []
    for sub in subtitles:
        txt = sub["text"].replace("'", "").replace(":", "")
        start = float(sub["start"])
        end = float(sub["end"])
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
    print("Mixing audio...")
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
