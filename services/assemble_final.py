import os
import subprocess
import json

BASE_DIR = "/home/ubuntu/the-origin-ai/output_dynamic"
ASSETS_DIR = "/home/ubuntu/the-origin-ai/assets"
OUTPUT_FILE = os.path.join(BASE_DIR, "final_video_high_quality.mp4")
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return float(result.stdout.strip())

def assemble_video():
    with open(os.path.join(BASE_DIR, "script.json"), "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    total_duration = get_duration(os.path.join(BASE_DIR, "narration.wav"))
    
    # Define visual sequence
    # 0-8s: Scene 1 (AI Singularity)
    # 8-18s: NASA Roman Zoom (Real)
    # 18-28s: Scene 2 (AI Big Bang)
    # 28-38s: NASA Lensing (Real)
    # 38-43s: Scene 3 (AI Expansion)
    # 43-end: Scene 4 (AI Human Eye)
    
    visuals = [
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_1.png"), "duration": 8.0},
        {"type": "video", "path": os.path.join(ASSETS_DIR, "nasa_roman_zoom.mp4"), "start": 0, "duration": 10.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_2.png"), "duration": 10.0},
        {"type": "video", "path": os.path.join(ASSETS_DIR, "dark_matter_lensing.mov"), "start": 0, "duration": 10.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_3.png"), "duration": 5.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_4.png"), "duration": max(2.0, total_duration - 43.0)}
    ]
    
    scene_clips = []
    for i, vis in enumerate(visuals):
        out = os.path.join(BASE_DIR, f"final_scene_{i}.mp4")
        if vis["type"] == "image":
            # Pan & Zoom
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
                "-vf", f"zoompan=z='min(zoom+0.0005,1.1)':d={int(vis['duration']*25)}:s=1080x1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", out
            ]
        else:
            # Scale and Crop
            cmd = [
                "ffmpeg", "-y", "-ss", str(vis["start"]), "-i", vis["path"],
                "-vf", "scale=w=-1:h=1920,crop=1080:1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out
            ]
        subprocess.run(cmd, check=True)
        scene_clips.append(out)
        
    # Concatenate
    concat_txt = os.path.join(BASE_DIR, "concat_final.txt")
    with open(concat_txt, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")
            
    temp_video = os.path.join(BASE_DIR, "temp_concat.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", temp_video
    ], check=True)
    
    # Add Subtitles
    # Build drawtext filter string
    subs = script_data["subtitles"]
    drawtext_filters = []
    for sub in subs:
        txt = sub["text"].replace("'", "").replace(":", "")
        start = sub["start"]
        end = sub["end"]
        # Draw background box + text
        filter_str = (
            f"drawtext=fontfile='{FONT_PATH}':text='{txt}':fontcolor=white:fontsize=60:"
            f"x=(w-text_w)/2:y=h-300:box=1:boxcolor=black@0.5:boxborderw=10:"
            f"enable='between(t,{start},{end})'"
        )
        drawtext_filters.append(filter_str)
    
    video_with_subs = os.path.join(BASE_DIR, "temp_subs.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-i", temp_video,
        "-vf", ",".join(drawtext_filters),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", video_with_subs
    ], check=True)
    
    # Mix Audio
    narration = os.path.join(BASE_DIR, "narration.wav")
    bgm = os.path.join(BASE_DIR, "bgm.wav")
    
    subprocess.run([
        "ffmpeg", "-y", "-i", video_with_subs, "-i", narration, "-i", bgm,
        "-filter_complex", "[1:a]volume=6.0,compand=0.3|0.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2,alimiter=limit=0.9[a1];[2:a]volume=0.6[a2];[a1][a2]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", OUTPUT_FILE
    ], check=True)
    
    print(f"Final high-quality video created: {OUTPUT_FILE}")

if __name__ == "__main__":
    assemble_video()
