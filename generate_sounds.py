import os
import requests

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"
URL = "https://api.elevenlabs.io/v1/sound-generation"

HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

PROMPTS = {
    "laser_shoot.mp3": "Sci-fi laser blaster pew sound effect, futuristic, short, energetic",
    "thruster.mp3": "Spaceship engine thruster roar, sci-fi afterburner, deep rumble, continuous",
    "ui_click.mp3": "Digital futuristic UI click, holographic beep, sharp and quick",
    "explosion.mp3": "Deep space explosion, muffled sci-fi blast, heavy impact, cinematic",
    "space_ambient.mp3": "Deep space ambient drone, cinematic sci-fi background hum, slow evolving synthesizer, mysterious dark space"
}

os.makedirs("c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds", exist_ok=True)

def generate_sound(filename, prompt):
    print(f"Generating {filename} with prompt: {prompt}")
    payload = {
        "text": prompt,
        "duration_seconds": 2.0 if "click" in filename or "laser" in filename else 5.0,
        "prompt_influence": 0.3
    }
    
    if filename == "space_ambient.mp3":
        payload["duration_seconds"] = 15.0
    
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
