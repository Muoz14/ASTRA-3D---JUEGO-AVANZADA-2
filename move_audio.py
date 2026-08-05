import os
import shutil
import hashlib

ASSETS_DIR_AI = "c:/Users/angel/PycharmProjects/JUEGO3D/JUEGO/assets/ai_audio"
ASSETS_DIR_HISTORY = "c:/Users/angel/PycharmProjects/JUEGO3D/JUEGO/assets/history_audio"
os.makedirs(ASSETS_DIR_HISTORY, exist_ok=True)

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

print("Moviendo archivos a history_audio...")
for text in STORY_DIALOGUES:
    file_hash = hash_text(text)
    src = os.path.join(ASSETS_DIR_AI, f"{file_hash}.mp3")
    dst = os.path.join(ASSETS_DIR_HISTORY, f"{file_hash}.mp3")
    
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Movido: {file_hash}.mp3")
print("Terminado.")
