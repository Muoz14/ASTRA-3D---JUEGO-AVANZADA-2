import os
import hashlib
import requests

API_KEY = "2d5f09eebd5df59e135d7df3d51c463a64a33ce02e6758f7dab328eaef5e4cde"
CHARLIE_ID = "IKne3meq5aSn9XLyUdCD"
CALLUM_ID = "N2lVS1w4EtoT3dr4eOWO"
NODRIZA_ID = "IKne3meq5aSn9XLyUdCD" # Reutilizamos Charlie para Nodriza temporalmente

HEADERS = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY
}

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "ai_audio")
os.makedirs(ASSETS_DIR, exist_ok=True)

STORY_DIALOGUES = [
    # enemy.py
    "Nodriza Altech: Piloto, has interferido demasiado en nuestros planes.",
    "Nodriza Altech: Tu nave y su IA serán asimiladas por nuestra tecnología superior.",
    "IA: Detecto firmas de energía masivas. Precaución extrema.",
    "Tierra: Destruye sus escoltas y ataca el núcleo central. ¡Es nuestra única oportunidad!",
    "IA: Alerta. La Nodriza está desplegando cazas de escolta.",
    # main.py
    "IA: Conectando a los sistemas de la boya Altech...",
    "Tierra: Piloto, estamos recibiendo la transmisión. Desencriptando...",
    "Tierra: Dios mío... ¡Es tecnología terrestre! Altech es una corporación humana operando en las sombras.",
    "Tierra: Sus registros indican que han estado robando tecnología de una antigua civilización alienígena.",
    "IA: Datos extraídos con éxito. Nuestros sistemas de ingeniería se han actualizado.",
    "Tierra: Fabrica todo lo que puedas. Necesitaremos armas para lo que se avecina.",
    "IA: Amenaza neutralizada. Detecto un núcleo de datos intacto en los restos.",
    "Tierra: Acércate a los restos de esa nave y hackéala. Necesitamos saber qué planean.",
    "IA: Descargando base de datos táctica de Altech...",
    "Tierra: Excelente. Ahora termina las misiones pendientes.",
    # missions.py
    "IA: Sistemas en línea. Necesitamos calibrar la telemetría.",
    "Tierra: Piloto, dirígete a las coordenadas marcadas en tu HUD.",
    "Tierra: Piloto, excelente trabajo con la anomalía.",
    "Tierra: Los datos sugieren tecnología de una facción humana clandestina...",
    "Tierra: Se llaman 'Altech'. Están usando tecnología alienígena robada.",
    "IA: Detecto una boya de transmisión de Altech cerca. Procedamos a interceptarla.",
    "IA: Nuevas coordenadas detectadas en la transmisión.",
    "Tierra: Piloto, dirígete a esas coordenadas. Creemos que es un escuadrón de reconocimiento.",
    "Tierra: ¡Piloto! Hemos descifrado toda la información de Altech.",
    "Tierra: Su Nave Nodriza está en camino. Dirígete a las coordenadas marcadas.",
    "IA: Coordenadas cargadas. Prepárate para combate extremo. Presiona [ 3 ] al llegar."
]

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def generate_story_audio():
    for text in STORY_DIALOGUES:
        file_hash = hash_text(text)
        filepath = os.path.join(ASSETS_DIR, f"{file_hash}.mp3")
        
        if os.path.exists(filepath):
            print(f"[{file_hash}] Ya existe, saltando: {text[:20]}...")
            continue
            
        # Determinar Voice ID y limpiar prefijo
        clean_text = text
        voice_id = CHARLIE_ID
        
        if text.startswith("Tierra: "):
            clean_text = text.replace("Tierra: ", "")
            voice_id = CALLUM_ID
        elif text.startswith("IA: "):
            clean_text = text.replace("IA: ", "")
            voice_id = CHARLIE_ID
        elif text.startswith("Nodriza Altech: "):
            clean_text = text.replace("Nodriza Altech: ", "")
            voice_id = CHARLIE_ID # Podríamos ponerle otro efecto luego
            
        print(f"Generando [{file_hash}] -> {clean_text}")
        
        data = {
            "text": clean_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        response = requests.post(url, json=data, headers=HEADERS)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print("  -> OK")
        else:
            print(f"  -> Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    generate_story_audio()
