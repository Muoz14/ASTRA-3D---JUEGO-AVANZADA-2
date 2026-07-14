import os
import hashlib

class TTSManager:
    """Gestor de TTS offline. Lee archivos MP3 pregenerados basados en el hash del texto.
    Esto elimina el lag por completo y el requerimiento de internet."""
    
    def __init__(self):
        self.audio_ready = None
        self.is_processing = False
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets", "ai_audio")

    def speak(self, text_key):
        """Busca el archivo de audio pregenerado y avisa que está listo."""
        # text_key es el texto original (o con sufijo "_glitch")
        file_hash = hashlib.md5(text_key.encode('utf-8')).hexdigest()
        filepath = os.path.join(self.assets_dir, f"{file_hash}.mp3")
        
        if os.path.exists(filepath):
            self.audio_ready = filepath
        else:
            print(f"Advertencia: No se encontró audio pregenerado para: {file_hash}.mp3")
            self.audio_ready = None

    def stop(self):
        """Mantiene compatibilidad con el manager, pero en modo offline no hay cola que limpiar."""
        pass
