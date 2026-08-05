import os
import requests
import wave
import struct

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"

VOICES = {
    "Callum (Tierra)": ("N2lVS1w4EtoT3dr4eOWO", "Tierra: Piloto, dirígete a las coordenadas marcadas en tu HUD. Es una orden."),
    "Charlie (IA)": ("IKne3meq5aSn9XLyUdCD", "IA: Sistemas en línea. Nuevas coordenadas detectadas en la transmisión.")
}

HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

def generate_examples():
    print("Generando audios de prueba limpios...")
    
    for name, data in VOICES.items():
        voice_id, text = data
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_16000"
        response = requests.post(url, json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            pcm_data = response.content
            
            # Limpiamos el nombre para el archivo
            file_name_clean = name.split()[0].lower()
            wav_path = f"c:/Users/angel/PycharmProjects/JUEGO3D/assets/sounds/ejemplo_{file_name_clean}_limpio.wav"
            
            with wave.open(wav_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(pcm_data)
                
            print(f"Muestra '{name}' guardada en: {wav_path}")
        else:
            print(f"Error con voz {name}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    generate_examples()
