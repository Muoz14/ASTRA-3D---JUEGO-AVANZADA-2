from ursina import Audio, Button

# Global Button Sound Patch
_original_button_input = Button.input

def _patched_button_input(self, key):
    if self.enabled:
        if self.hovered and key in ('left mouse down', 'left mouse up'):
            if key == 'left mouse down':
                AudioManager().play_ui_click()
    _original_button_input(self, key)

_original_button_on_mouse_enter = Button.on_mouse_enter
def _patched_button_on_mouse_enter(self):
    if self.enabled:
        AudioManager().play_ui_hover()
    if _original_button_on_mouse_enter:
        _original_button_on_mouse_enter(self)

Button.input = _patched_button_input
Button.on_mouse_enter = _patched_button_on_mouse_enter

class AudioManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AudioManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Efecto continuo del propulsor
            self.thruster = Audio('assets/sounds/thruster.wav', autoplay=False, loop=True, volume=0.0)
            
            # Efecto continuo del motor normal
            self.engine_accel = Audio('assets/sounds/engine_accel.wav', autoplay=False, loop=True, volume=0.0)
            
            # Zumbido de la nave en vuelo
            self.ship_flight = Audio('assets/sounds/ship_flight.wav', autoplay=False, loop=True, volume=0.0)
            
            # Ambiente
            self.space_ambient = Audio('assets/sounds/space_ambient2.wav', autoplay=False, loop=True, volume=0.7)
            
            # Musica Menu
            self.menu_music = Audio('assets/sounds/menu_music.wav', autoplay=False, loop=True, volume=0.5)
            
            # Pools para evitar exhausion de canales de audio (lo que corta la voz de la IA y ambientes)
            self.laser_pool = [Audio('assets/sounds/laser_shoot2.wav', autoplay=False, loop=False, volume=0.3) for _ in range(5)]
            self.laser_idx = 0
            
            self.exp_pool = [Audio('assets/sounds/explosion2.wav', autoplay=False, loop=False, volume=0.6) for _ in range(3)]
            self.exp_idx = 0
            
            self.hit_ast_pool = [Audio('assets/sounds/hit_asteroid.wav', autoplay=False, loop=False, volume=0.4) for _ in range(3)]
            self.hit_ast_idx = 0
            
            self.hit_ship_pool = [Audio('assets/sounds/hit_ship.wav', autoplay=False, loop=False, volume=0.5) for _ in range(3)]
            self.hit_ship_idx = 0
            
            self.enemy_laser_pool = [Audio('assets/sounds/enemy_laser.wav', autoplay=False, loop=False, volume=0.3) for _ in range(5)]
            self.enemy_laser_idx = 0
            
            self.player_hit_pool = [Audio('assets/sounds/player_hit.wav', autoplay=False, loop=False, volume=0.5) for _ in range(3)]
            self.player_hit_idx = 0
            
            self.ducking_multiplier = 1.0
            
            self.initialized = True
            
    def set_ducking(self, active: bool):
        self.ducking_multiplier = 0.2 if active else 1.0
        if self.space_ambient:
            self.space_ambient.animate('volume', 0.7 * self.ducking_multiplier, duration=0.3)
            
    def play_laser(self):
        self.laser_pool[self.laser_idx].volume = 0.08 * self.ducking_multiplier
        self.laser_pool[self.laser_idx].play()
        self.laser_idx = (self.laser_idx + 1) % 5

    def play_enemy_laser(self):
        self.enemy_laser_pool[self.enemy_laser_idx].volume = 0.10 * self.ducking_multiplier
        self.enemy_laser_pool[self.enemy_laser_idx].play()
        self.enemy_laser_idx = (self.enemy_laser_idx + 1) % 5

    def play_player_hit(self):
        self.player_hit_pool[self.player_hit_idx].volume = 0.7 * self.ducking_multiplier
        self.player_hit_pool[self.player_hit_idx].play()
        self.player_hit_idx = (self.player_hit_idx + 1) % 3

    def set_thruster_volume(self, volume):
        if self.thruster:
            if volume > 0 and not self.thruster.playing:
                self.thruster.play()
            self.thruster.volume = volume * self.ducking_multiplier
            if volume == 0 and self.thruster.playing:
                self.thruster.stop()
                
    def set_engine_volume(self, volume):
        if self.engine_accel:
            if volume > 0 and not self.engine_accel.playing:
                self.engine_accel.play()
            self.engine_accel.volume = volume * self.ducking_multiplier
            if volume <= 0 and self.engine_accel.playing:
                self.engine_accel.stop()
                
    def set_ship_flight_volume(self, volume):
        if self.ship_flight:
            if volume > 0 and not self.ship_flight.playing:
                self.ship_flight.play()
            self.ship_flight.volume = volume * self.ducking_multiplier
            if volume <= 0.05 and self.ship_flight.playing:
                self.ship_flight.stop()
                
    def play_ui_click(self):
        Audio('assets/sounds/ui_click.wav', autoplay=True, loop=False, volume=0.8, ignore_paused=True)
        
    def play_ui_hover(self):
        Audio('assets/sounds/ui_hover.wav', autoplay=True, loop=False, volume=0.5, ignore_paused=True)
            
    def play_explosion(self, volume=0.6):
        self.exp_pool[self.exp_idx].volume = volume * self.ducking_multiplier
        self.exp_pool[self.exp_idx].play()
        self.exp_idx = (self.exp_idx + 1) % 3

    def play_hit_asteroid(self, volume=0.4):
        self.hit_ast_pool[self.hit_ast_idx].volume = volume * self.ducking_multiplier
        self.hit_ast_pool[self.hit_ast_idx].play()
        self.hit_ast_idx = (self.hit_ast_idx + 1) % 3

    def play_hit_ship(self, volume=0.5):
        # Reducir mucho el volumen base para que no ensordezca al mezclarse
        vol_adj = (volume * 0.3) if volume == 0.5 else (volume * 0.5)
        self.hit_ship_pool[self.hit_ship_idx].volume = vol_adj * self.ducking_multiplier
        self.hit_ship_pool[self.hit_ship_idx].play()
        self.hit_ship_idx = (self.hit_ship_idx + 1) % 3

    def play_achievement(self):
        Audio('assets/sounds/achievement_unlock.wav', autoplay=True, loop=False, volume=0.7, ignore_paused=True)
            
    def play_ambient(self):
        if self.space_ambient and not self.space_ambient.playing:
            self.space_ambient.play()
            
    def stop_ambient(self):
        if self.space_ambient and self.space_ambient.playing:
            self.space_ambient.stop()
            
    def play_menu_music(self):
        if self.menu_music and not self.menu_music.playing:
            self.menu_music.play()
            
    def stop_menu_music(self):
        if self.menu_music and self.menu_music.playing:
            self.menu_music.stop()
