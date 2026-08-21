import os
import subprocess
import json

BASE_DIR = "/home/ubuntu/the-origin-ai/output_dm"
ASSETS_DIR = "/home/ubuntu/the-origin-ai/assets"
OUTPUT_FILE = os.path.join(BASE_DIR, "final_video_v2.mp4")
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def assemble_video():
    # 1. Prepare visual sequence
    # Scene 1: AI Cosmic (0-5s)
    # Scene 2: NASA Roman Zoom (5-15s) - Real
    # Scene 3: AI Galaxy (15-20s)
    # Scene 4: NASA Lensing (20-30s) - Real
    # Scene 5: AI Lab (30-35s)
    # Scene 6: AI Observer (35-end)
    
    total_duration = get_duration(os.path.join(BASE_DIR, "narration.wav"))
    
    visuals = [
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_1.png"), "duration": 5.0},
        {"type": "video", "path": os.path.join(ASSETS_DIR, "nasa_roman_zoom.mp4"), "start": 0, "duration": 10.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_2.png"), "duration": 5.0},
        {"type": "video", "path": os.path.join(ASSETS_DIR, "dark_matter_lensing.mov"), "start": 0, "duration": 10.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_3.png"), "duration": 5.0},
        {"type": "image", "path": os.path.join(BASE_DIR, "scene_4.png"), "duration": total_duration - 35.0}
    ]
    
    scene_clips = []
    for i, vis in enumerate(visuals):
        out = os.path.join(BASE_DIR, f"v2_scene_{i}.mp4")
        if vis["type"] == "image":
            # Pan & Zoom for AI images
            cmd = [
                "ffmpeg", "-y", "-loop", "1", "-i", vis["path"],
                "-vf", f"zoompan=z='min(zoom+0.0005,1.1)':d={int(vis['duration']*25)}:s=1080x1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", out
            ]
        else:
            # Crop and scale real video to 9:16
            cmd = [
                "ffmpeg", "-y", "-ss", str(vis["start"]), "-i", vis["path"],
                "-vf", "scale=w=-1:h=1920,crop=1080:1920",
                "-t", str(vis["duration"]), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out
            ]
        subprocess.run(cmd)
        scene_clips.append(out)
        
    # Concatenate
    concat_txt = os.path.join(BASE_DIR, "concat_v2.txt")
    with open(concat_txt, "w") as f:
        for sc in scene_clips:
            f.write(f"file '{sc}'\n")
    
    combined_v = os.path.join(BASE_DIR, "combined_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", combined_v])
    
    # 2. Add Subtitles using drawtext filter (better control)
    with open(os.path.join(BASE_DIR, "subtitles.json"), "r", encoding="utf-8") as f:
        subs = json.load(f)
    
    filter_parts = []
    for sub in subs:
        t = sub["text"].replace("'", "\\'").replace(":", "\\:")
        filter_parts.append(
            f"drawtext=fontfile={FONT_PATH}:text='{t}':fontcolor=white:fontsize=64:"
            f"x=(w-text_w)/2:y=h-400:box=1:boxcolor=black@0.6:boxborderw=20:"
            f"enable='between(t,{sub['start']},{sub['end']})'"
        )
    
    subbed_v = os.path.join(BASE_DIR, "subbed_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-i", combined_v, "-vf", ",".join(filter_parts), "-c:v", "libx264", "-c:a", "copy", subbed_v])
    
    # 3. Final Audio Mix
    final_cmd = [
        "ffmpeg", "-y", "-i", subbed_v,
        "-i", os.path.join(BASE_DIR, "narration.wav"),
        "-i", os.path.join(BASE_DIR, "bgm.wav"),
        "-filter_complex", "[2:a]volume=0.15[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", OUTPUT_FILE
    ]
    subprocess.run(final_cmd)
    print(f"Video V2 assembled: {OUTPUT_FILE}")

if __name__ == "__main__":
    assemble_video()
