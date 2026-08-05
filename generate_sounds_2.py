import os
import requests

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"
URL = "https://api.elevenlabs.io/v1/sound-generation"

HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

PROMPTS = {
    "ui_hover.mp3": "Soft digital futuristic UI hover beep, subtle holographic tick, extremely short",
    "explosion2.mp3": "Sharp sci-fi explosion, metallic crunch, space blast, energetic, loud",
    "laser_shoot2.mp3": "Pew, high-pitched sci-fi laser blaster, sharp energy bolt, quick",
    "ship_flight.mp3": "Spaceship interior ambient hum, sci-fi engine vibrating drone, smooth travel, continuous",
    "space_ambient2.mp3": "Loud deep space ambient drone, eerie sci-fi background hum, slow synthesizer, cosmic wind",
    "menu_music.mp3": "Epic cinematic sci-fi menu theme, orchestral electronic hybrid, space adventure, slow tempo"
}

os.makedirs("c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds", exist_ok=True)

def generate_sound(filename, prompt):
    print(f"Generating {filename} with prompt: {prompt}")
    payload = {
        "text": prompt,
        "duration_seconds": 2.0 if "ui" in filename or "laser" in filename else 5.0,
        "prompt_influence": 0.3
    }
    
    if "ambient" in filename or "menu" in filename:
        payload["duration_seconds"] = 15.0
    elif "flight" in filename:
        payload["duration_seconds"] = 10.0
    
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
