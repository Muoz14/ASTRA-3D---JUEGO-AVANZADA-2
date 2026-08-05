import os
import requests

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"
URL = "https://api.elevenlabs.io/v1/sound-generation"

HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

PROMPTS = {
    "enemy_laser.mp3": "soft alien laser pew, muffled enemy blaster shot, short sci-fi zip, low frequency, quiet energy bolt",
    "player_hit.mp3": "dull metallic thud inside cockpit, sci-fi shield absorbing damage, low impact, subtle damage rumble, very quiet"
}

os.makedirs("c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds", exist_ok=True)

def generate_sound(filename, prompt):
    print(f"Generating {filename} with prompt: {prompt}")
    payload = {
        "text": prompt,
        "duration_seconds": 1.0,
        "prompt_influence": 0.4
    }
    
    response = requests.post(URL, json=payload, headers=HEADERS)
    
    if response.status_code == 200:
        path = os.path.join("c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds", filename)
        with open(path, 'wb') as f:
            f.write(response.content)
        print(f"Saved: {path}")
    else:
        print(f"Failed to generate {filename}: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    for filename, prompt in PROMPTS.items():
        generate_sound(filename, prompt)
