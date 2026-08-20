import os
import json
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("Generating script for Dark Matter...")
prompt = """
Write a 35-second Thai narration script for a cinematic science short about Dark Matter (สสารมืด), in the style of Blurr Content.
It must be divided into 4 short scenes. Each scene has a Thai narration line (engaging, mysterious, deep, authoritative) and a detailed image generation prompt in English for a cinematic 8K cosmic scene.
Output strict JSON format with an array of objects under key "scenes", each having "scene_id", "narration", and "image_prompt".
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config={"response_mime_type": "application/json"}
)

data = json.loads(response.text)
os.makedirs("/home/ubuntu/the-origin-ai/output_dm", exist_ok=True)
with open("/home/ubuntu/the-origin-ai/output_dm/script.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Script saved successfully.")
print(json.dumps(data, ensure_ascii=False, indent=2))
