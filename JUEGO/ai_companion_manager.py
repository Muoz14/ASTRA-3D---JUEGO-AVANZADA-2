from ursina import *
import random
import time
import ctypes
from ai_companion_ui import CompanionUI
from ai_dialogue_generator import DialogueGenerator
from ai_tts_manager import TTSManager

import pygame

# Inicializamos el mixer de pygame para reproducir MP3 con control real de volumen
try:
    pygame.mixer.init()
except Exception as e:
    print("Warning: pygame mixer failed to init:", e)

class MP3Player:
    """Reproductor de MP3 usando pygame.mixer. 
    Resuelve el problema de volumen y compatibilidad de MP3 en Ursina."""
    def __init__(self, file_path):
        from menu import GameSettings
        try:
            pygame.mixer.music.load(file_path)
            vol = GameSettings.vol_ai * GameSettings.vol_master
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play()
        except Exception as e:
            print("Error reproduciendo MP3 con pygame:", e)
        
    def set_volume(self, vol_ai, vol_master):
        vol = vol_ai * vol_master
        pygame.mixer.music.set_volume(vol)
        
    @property
    def playing(self):
        return pygame.mixer.music.get_busy()
        
    def pause(self):
        pygame.mixer.music.pause()
        
    def resume(self):
        pygame.mixer.music.unpause()
        
    def stop(self):
        pygame.mixer.music.stop()

class CompanionManager(Entity):
    """Gestor lógico de los diálogos de la IA de la nave."""
    
    def __init__(self, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.ui = CompanionUI()
        self.dialogue_gen = DialogueGenerator()
        self.tts = TTSManager()
        
        self.last_message_time = 0
        self.cooldown = 8.0
        
        self.idle_timer = 0.0
        self.idle_interval = random.uniform(2.0, 5.0)
        
        self.initial_delay_finished = False
        self.initial_delay_timer = 0.0
        
        self._waiting_for_tts = False
        self._tts_actually_started = False
        self.audio_player = None
        self._was_paused = False

    def _get_player(self):
        """Busca y retorna dinámicamente al jugador de la escena."""
        if hasattr(self, '_cached_player') and self._cached_player and self._cached_player.enabled:
            return self._cached_player
            
        for e in scene.entities:
            if type(e).__name__ == 'PlayerShip':
                self._cached_player = e
                return e
        return None

    def update(self):
        """Loop principal de la entidad para diálogos aleatorios."""
        
        player = self._get_player()
        is_cine = getattr(player, 'is_cinematic', False) if player else False
        
        if getattr(self, '_in_story_dialogue', False):
            return
            
        if application.paused or is_cine:
            if not self._was_paused:
                if self.audio_player:
                    self.audio_player.pause()
                self.ui.enabled = False
                self._was_paused = True
            return
        else:
            if self._was_paused:
                if self.audio_player:
                    self.audio_player.resume()
                self.ui.enabled = True
                self._was_paused = False
                
        # Limpieza total al morir o si el jugador está desactivado (ej. Menú Principal)
        if player and (getattr(player, 'is_dead', False) or not player.enabled):
            self.ui.hide_message_instant()
            self.tts.stop()
            if self.audio_player:
                self.audio_player.stop()
                self.audio_player = None
            self._waiting_for_tts = False
            self.initial_delay_finished = False
            self.initial_delay_timer = 0.0
            return
            
        # Control del retraso inicial
        if player:
            if not self.initial_delay_finished:
                # Contamos 5 segundos de silencio absoluto al inicio
                self.initial_delay_timer += time.dt
                if self.initial_delay_timer >= 5.0:
                    self.initial_delay_finished = True
                    self.idle_timer = 0.0 # El timer idle real arranca limpio desde aquí
                return
            
        self.idle_timer += time.dt
        
        # Comprobar si Edge-TTS generó un nuevo audio
        if self.tts.audio_ready:
            file_path = self.tts.audio_ready
            self.tts.audio_ready = None
            
            if self.audio_player:
                self.audio_player.stop()
                
            self.audio_player = MP3Player(file_path)
            self._tts_actually_started = True
            self._audio_confirmed_playing = False
            self._audio_start_time = time.time()

        # Lógica de sincronización del pop-up visual con la voz de la IA
        if self._waiting_for_tts:
            # Seguro general: Si el archivo nunca existió, cerramos la ventana rápido y abortamos
            if not self._tts_actually_started and time.time() - getattr(self, '_tts_request_time', 0) > 1.0:
                self.ui.hide_message()
                self._waiting_for_tts = False
                return
                
            is_speaking = self.audio_player and self.audio_player.playing
            
            # Confirmamos definitivamente si MCI logró arrancar el audio en algún momento
            if is_speaking:
                self._audio_confirmed_playing = True
                
            is_busy = self.tts.is_processing or is_speaking
            
            # Tiempo transcurrido desde que le dijimos a MCI que reproduzca
            time_waiting = time.time() - getattr(self, '_audio_start_time', time.time())
            
            # Si pasaron más de 3 segundos y nunca arrancó, forzamos el cierre por si MCI colapsó
            mci_failed_timeout = self._tts_actually_started and not self._audio_confirmed_playing and time_waiting > 3.0
            
            # Solo cerramos la ventana si el reproductor confirmó haber arrancado,
            # y ahora ya no está ocupado (es decir, terminó de forma natural), O si MCI falló
            if (self._tts_actually_started and self._audio_confirmed_playing and not is_busy) or mci_failed_timeout:
                self.ui.hide_message()
                self._waiting_for_tts = False
                self._tts_actually_started = False
                self._audio_confirmed_playing = False
                if self.audio_player:
                    self.audio_player.stop()
        
        if self.idle_timer >= self.idle_interval:
            self.idle_timer = 0.0
            self.idle_interval = random.uniform(15.0, 25.0) # Siguientes mensajes cada 15-25 segs
            
            # Verificar por la transparencia del color de fondo garantiza 100% saber si está oculto
            # (evita un bug donde una Sequence terminada no se volvía None)
            if self.ui.bg.color[3] <= 0.01:
                self._trigger_event("idle")

    def _trigger_event(self, event_type, ignore_cooldown=False):
        current_time = time.time()
        
        if not ignore_cooldown and (current_time - self.last_message_time) < self.cooldown:
            return
            
        player = self._get_player()
        
        is_critical = False
        if player:
            # 1. Bloquear diálogos si ya está en Game Over
            if getattr(player, 'is_dead', False):
                return
                
            # 2. Silencio completo durante la cinemática o el temporizador inicial de 5s
            if getattr(player, 'is_cinematic', False) or not self.initial_delay_finished:
                return
                
            # Extraemos la salud verificando la variable correcta
            hp = getattr(player, 'shield', getattr(player, 'health', 100))
            max_hp = getattr(player, 'max_shield', getattr(player, 'max_health', 100))
            
            # 3. Bloquear si este golpe es letal, para evitar hablar durante el frame del Game Over
            if hp <= 0:
                return
                
            # 4. Comprobar si está crítico para aplicar glitches
            if max_hp > 0 and (hp / max_hp) <= 0.10:
                is_critical = True
                
        # Generar el texto procedimentalmente según el evento
        message = self.dialogue_gen.generate(event_type)
        if message == "...":
            return
                
        # Si está crítico, corromper visualmente el diálogo y usar la llave de audio glitcheada
        if is_critical:
            visual_message = self.dialogue_gen.glitch_text(message)
            audio_key = message + "_glitch"
        else:
            visual_message = message
            audio_key = message
            
        if self.audio_player:
            self.audio_player.stop()
            
        self.ui.show_message(visual_message)
        
        from menu import GameSettings
        if getattr(GameSettings, 'ai_voice_enabled', True):
            self.tts.speak(audio_key)
        else:
            # Si la voz está desactivada, simulamos que el audio comenzó para que el UI se oculte después de un tiempo
            self._audio_confirmed_playing = True
            invoke(self.ui.hide_message, delay=4.0)
        
        self.last_message_time = current_time
        
        # Comenzar a esperar que la voz termine para ocultar el UI
        self._waiting_for_tts = True
        self._tts_actually_started = False
        self._tts_request_time = current_time

    def on_damage_taken(self):
        current_time = time.time()
        # Cooldown interno de 6.0s exclusivo para evitar spam de daño por colisiones múltiples
        if current_time - getattr(self, '_last_damage_time', 0) < 6.0:
            return
            
        self._last_damage_time = current_time
        self._trigger_event("damage", ignore_cooldown=True)
        # Reiniciar el idle timer al recibir eventos para no interrumpir
        self.idle_timer = 0.0
        
    def on_boost_activated(self):
        self._trigger_event("boost")
        self.idle_timer = 0.0
        
    def on_enemy_spotted(self):
        self._trigger_event("enemy_spotted")
        self.idle_timer = 0.0 # reset idle

    def trigger_dialogue(self, dialogue_sequence):
        # dialogue_sequence is a list of tuples: (text, duration)
        from ursina import invoke
        self._in_story_dialogue = True
        self.ui.enabled = True
        self._was_paused = False
        
        current_delay = 0.0
        for text, duration in dialogue_sequence:
            invoke(self._play_story_line, text, delay=current_delay)
            current_delay += duration
            
        invoke(self._end_story_dialogue, delay=current_delay)
        
    def _play_story_line(self, text):
        if self.audio_player:
            self.audio_player.stop()
        self.ui.show_message(text, title_text="[ COMUNICACIÓN ENTRANTE ]")
        from menu import GameSettings
        if getattr(GameSettings, 'ai_voice_enabled', True):
            self.tts.speak(text)
            
    def _end_story_dialogue(self):
        self._in_story_dialogue = False
        self.ui.hide_message()      
    def on_weapon_overheated(self):
        self._trigger_event("overheat", ignore_cooldown=True)
        self.idle_timer = 0.0

    def on_material_collected(self):
        current_time = time.time()
        # Cooldown de 8s para recolección de materiales
        if current_time - getattr(self, '_last_loot_time', 0) < 8.0:
            return
            
        self._last_loot_time = current_time
        # Asumiendo que "idle" o algún evento genérico sirve, o si hay un evento específico de loot:
        self._trigger_event("idle") # Usa idle por ahora ya que genera charlas esporádicas, o añade un tipo "loot" al generador
        self.idle_timer = 0.0
