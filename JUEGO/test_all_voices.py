import requests
import ctypes
import os
import time

API_KEY = "sk_0bee2e0078a766ba3431e303aeeefbbe7a368a7ccf190f7f"

def test_elevenlabs_default_voices():
    voces = {
        "1. Charlie (Voz Profunda y Confiada)": "IKne3meq5aSn9XLyUdCD",
        "2. George (Narrador Cálido)": "JBFqnCBsd6RMkjVDRZzb",
        "3. Callum (Voz Rasposa y Táctica)": "N2lVS1w4EtoT3dr4eOWO"
    }
    
    texto = "¡Cuidado Capitán! Los sensores detectan una anomalía. S-s-sistemas fallando."
    archivo = "prueba_elevenlabs.mp3"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    for nombre, voice_id in voces.items():
        print(f"\nGenerando {nombre}...")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        data = {
            "text": texto,
            "model_id": "eleven_multilingual_v2"
        }
        
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except:
                pass
                
        r = requests.post(url, json=data, headers=headers)
        
        if r.status_code == 200:
            with open(archivo, 'wb') as f:
                f.write(r.content)
                
            print(f"Reproduciendo {nombre}...")
            ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'open {archivo} alias myaudio', None, 0, None)
            ctypes.windll.winmm.mciSendStringW('play myaudio wait', None, 0, None)
            time.sleep(1)
        else:
            print(f"Error {r.status_code}: {r.text}")

    print("\n¡Prueba finalizada!")

if __name__ == "__main__":
    test_elevenlabs_default_voices()
