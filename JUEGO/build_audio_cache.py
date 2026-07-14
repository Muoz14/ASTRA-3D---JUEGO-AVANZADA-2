import os
import json
import hashlib
import requests
import random
import asyncio
from ai_dialogue_generator import DialogueGenerator

# Configuración de ElevenLabs
API_KEY = "sk_1842843063a5c53e6f570e930f521b198425639fc211926a"
# Charlie (Voz predeterminada de alta calidad)
VOICE_ID = "IKne3meq5aSn9XLyUdCD"
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
HEADERS = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY
}

# Carpetas
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "ai_audio")
os.makedirs(ASSETS_DIR, exist_ok=True)
MANIFEST_PATH = os.path.join(ASSETS_DIR, "audio_manifest.json")

random.seed(42)

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

async def generate_audio(text, filename):
    filepath = os.path.join(ASSETS_DIR, f"{filename}.mp3")
    if os.path.exists(filepath):
        return  # Ya fue generado

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Descargado: {filename}.mp3")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

async def main():
    gen = DialogueGenerator()
    manifest = {}

    async def process_combinations(subjects, actions, contexts, event_type, is_glitch=False):
        for s in subjects:
            for a in actions:
                for c in contexts:
                    base_text = f"{s} {a} {c}"
                    
                    if is_glitch:
                        # Generamos la versión fonética para enviar a Edge-TTS
                        spoken_text = gen.get_phonetic_stutter(base_text)
                        file_hash = hash_text(base_text + "_glitch")
                        manifest[file_hash] = {"base": base_text, "spoken": spoken_text, "type": f"{event_type}_glitch"}
                        await generate_audio(spoken_text, file_hash)
                    else:
                        file_hash = hash_text(base_text)
                        manifest[file_hash] = {"base": base_text, "spoken": base_text, "type": event_type}
                        await generate_audio(base_text, file_hash)

    print("Iniciando generación de audios usando Edge-TTS (Offline Cache)...")

    # Idle (392)
    await process_combinations(gen.idle_subjects, gen.idle_actions, gen.idle_contexts, "idle")
    # Idle Glitch (392)
    await process_combinations(gen.idle_subjects, gen.idle_actions, gen.idle_contexts, "idle", is_glitch=True)
    
    # Boost (64)
    await process_combinations(gen.boost_subjects, gen.boost_actions, gen.boost_contexts, "boost")
    # Boost Glitch (64)
    await process_combinations(gen.boost_subjects, gen.boost_actions, gen.boost_contexts, "boost", is_glitch=True)
    
    # Overheat (64)
    await process_combinations(gen.overheat_subjects, gen.overheat_actions, gen.overheat_contexts, "overheat")
    # Overheat Glitch (64)
    await process_combinations(gen.overheat_subjects, gen.overheat_actions, gen.overheat_contexts, "overheat", is_glitch=True)
    
    # Damage (100)
    await process_combinations(gen.damage_subjects, gen.damage_actions, gen.damage_contexts, "damage")
    # Damage Glitch (100)
    await process_combinations(gen.damage_subjects, gen.damage_actions, gen.damage_contexts, "damage", is_glitch=True)

    # Guardar manifiesto
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)
        
    print(f"\n¡Proceso completado! Manifiesto guardado en {MANIFEST_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
