import os
import subprocess
import json

BASE_DIR = "/home/ubuntu/the-origin-ai/output_dm"
OUTPUT_FILE = os.path.join(BASE_DIR, "final_video.mp4")
FONT_PATH = "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"

def get_audio_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def assemble_video():
    # Load script for narrations
    with open(os.path.join(BASE_DIR, "script.json"), "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    scenes = script_data["scenes"]
    total_duration = get_audio_duration(os.path.join(BASE_DIR, "narration.wav"))
    scene_duration = total_duration / len(scenes)
    
    # Create individual scene clips with Pan & Zoom
    scene_files = []
    for i, scene in enumerate(scenes):
        img = os.path.join(BASE_DIR, f"scene_{i+1}.png")
        out = os.path.join(BASE_DIR, f"scene_{i+1}.mp4")
        text = scene["narration"]
        
        # FFmpeg command for Pan & Zoom + Subtitles
        # Zoom from 1.0 to 1.1 over the duration
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img,
            "-vf", f"zoompan=z='min(zoom+0.0005,1.1)':d={int(scene_duration*25)}:s=1080x1920,drawtext=fontfile={FONT_PATH}:text='{text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black@0.5:boxborderw=10",
            "-t", str(scene_duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            out
        ]
        subprocess.run(cmd)
        scene_files.append(out)
    
    # Concatenate scenes
    concat_list = os.path.join(BASE_DIR, "concat.txt")
    with open(concat_list, "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")
    
    combined_v = os.path.join(BASE_DIR, "combined_v.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", combined_v])
    
    # Add Audio (Narration + BGM)
    # BGM at 0.2 volume
    final_cmd = [
        "ffmpeg", "-y",
        "-i", combined_v,
        "-i", os.path.join(BASE_DIR, "narration.wav"),
        "-i", os.path.join(BASE_DIR, "bgm.wav"),
        "-filter_complex", "[2:a]volume=0.2[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        OUTPUT_FILE
    ]
    subprocess.run(final_cmd)
    print(f"Video assembled: {OUTPUT_FILE}")

if __name__ == "__main__":
    assemble_video()
