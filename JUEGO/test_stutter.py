import asyncio
import edge_tts
import ctypes
import os
import time

async def test_audio():
    print("Generando audio con tartamudeo...")
    
    # Este es el texto que le pasamos al motor de voz (glitch fonético)
    texto_audio = "S-s-sistemas... fallando. La i-i-inte-gridad del c-c-casco... com-pro-metida. N-n-necesitamos... a-yu-da in-me-diata."
    
    # Configuramos la voz de Alvaro (más expresiva) con un poco de lentitud para que suene roto
    communicate = edge_tts.Communicate(texto_audio, 'es-ES-AlvaroNeural', rate="-10%")
    
    archivo = "prueba_glitch.mp3"
    
    # Limpiamos si existe
    if os.path.exists(archivo):
        try:
            os.remove(archivo)
        except:
            pass
            
    await communicate.save(archivo)
    print("Audio generado. Reproduciendo...")
    
    # Reproducimos usando la tarjeta de sonido nativa
    ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
    ctypes.windll.winmm.mciSendStringW(f'open {archivo} alias myaudio', None, 0, None)
    ctypes.windll.winmm.mciSendStringW('play myaudio', None, 0, None)
    
    # Mantenemos el script abierto unos segundos para que escuches el audio completo
    time.sleep(10)
    
    ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
    print("Prueba finalizada.")

if __name__ == "__main__":
    asyncio.run(test_audio())
