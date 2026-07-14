import requests
import ctypes
import os
import time

API_KEY = "sk_0bee2e0078a766ba3431e303aeeefbbe7a368a7ccf190f7f"

def test_charlie():
    voice_id = "IKne3meq5aSn9XLyUdCD"
    texto = "Sistemas en línea, Capitán. Todo parece estar operando en parámetros normales. ¿Cuál es nuestro siguiente movimiento?"
    archivo = "prueba_charlie.mp3"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    data = {
        "text": texto,
        "model_id": "eleven_multilingual_v2"
    }
    
    print("Descargando voz de Charlie...")
    r = requests.post(url, json=data, headers=headers)
    
    if r.status_code == 200:
        with open(archivo, 'wb') as f:
            f.write(r.content)
            
        print("Reproduciendo Charlie...")
        ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
        ctypes.windll.winmm.mciSendStringW(f'open {archivo} alias myaudio', None, 0, None)
        ctypes.windll.winmm.mciSendStringW('play myaudio wait', None, 0, None)
        time.sleep(1)
        print("¡Reproducción finalizada!")
    else:
        print(f"Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    test_charlie()
