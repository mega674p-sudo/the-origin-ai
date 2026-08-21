import os
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_sample():
    # 1. Generate Topic
    topic_prompt = """
    Generate one fascinating, mysterious, and engaging topic in Thai for a cinematic science YouTube Short (Blurr Content style), such as about space, quantum physics, black holes, time, parallel universes, or deep cosmos mysteries.
    Output ONLY the topic string in Thai.
    """
    topic_resp = client.models.generate_content(model="gemini-3.6-flash", contents=topic_prompt)
    topic = topic_resp.text.strip()
    
    # 2. Generate Full Script
    script_prompt = f"""
    Create a detailed script for a 60-second YouTube Short (Vertical 9:16) in Thai for the topic: "{topic}".
    Style: Blurr Content (Cinematic, Mysterious, Scientific).
    Voice: Charon (Deep, Informative, Documentarian).
    
    Structure:
    - Scene 1 (0-10s): Hook - A mystery or big question.
    - Scene 2 (10-30s): Explanation - The science behind it.
    - Scene 3 (30-50s): Mind-blowing fact - Something to wow the audience.
    - Scene 4 (50-60s): Outro - Call to action (Subscribe for more mysteries).
    
    For each scene, provide:
    1. Visual Description (AI Image prompt or NASA Footage suggestion).
    2. Thai Narration Text.
    3. Thai Subtitle Text.
    """
    script_resp = client.models.generate_content(model="gemini-3.6-flash", contents=script_prompt)
    
    print(f"TOPIC: {topic}")
    print("-" * 20)
    print(script_resp.text)

if __name__ == "__main__":
    generate_sample()
