import os
import requests
import wave
import struct
import random

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"

VOICES = {
    "Callum_Radio": "N2lVS1w4EtoT3dr4eOWO"
}

HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

def apply_radio_effect(pcm_data):
    samples = list(struct.unpack(f"<{len(pcm_data)//2}h", pcm_data))
    
    new_samples = []
    # Filtro paso-bajo simple para opacar el audio
    prev = 0
    for s in samples:
        # Clipping (distorsión)
        s = int(s * 1.5)
        if s > 20000: s = 20000
        if s < -20000: s = -20000
        
        # Low pass simple (muy fuerte)
        s = int(prev + 0.3 * (s - prev))
        prev = s
        
        # Noise (estática de radio)
        noise = random.randint(-1200, 1200)
        
        # Reducción de bits (crunch) para sonido lo-fi
        s = (s // 500) * 500
        
        val = s + noise
        if val > 32767: val = 32767
        if val < -32768: val = -32768
        new_samples.append(val)
        
    return struct.pack(f"<{len(new_samples)}h", *new_samples)

def generate_wav_samples():
    print("Generando múltiples muestras de voz...")
    
    payload = {
        "text": "Atención piloto, habla el Comando de Tierra. Hemos interceptado una señal hostil.",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    for name, voice_id in VOICES.items():
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_16000"
        response = requests.post(url, json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            pcm_data = response.content
            
            # Aplicar el efecto de radio
            pcm_data = apply_radio_effect(pcm_data)
            
            wav_path = f"c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds/ejemplo_tierra_{name.lower()}.wav"
            
            with wave.open(wav_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(pcm_data)
                
            print(f"Muestra '{name}' guardada en: {wav_path}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    generate_wav_samples()
