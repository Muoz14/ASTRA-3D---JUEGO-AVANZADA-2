from ursina import *
import random
import math
from achievements import AchievementsMenu
from score_menu import ScoreMenu
from menu_ships import ShipSelectionMenu


class GameSettings:
    quality = 'Alta'
    vsync = False
    resolutions = [(800, 600), (1024, 768), (1280, 720), (1366, 768), (1600, 900), (1920, 1080), (2560, 1440), (2560, 1600)]
    current_res_idx = 5  # Por defecto 1920x1080
    
    vol_master = 1.0
    vol_music = 0.8
    vol_sfx = 1.0
    vol_ai = 1.0

    @classmethod
    def load(cls):
        import json, os
        if os.path.exists('settings.json'):
            try:
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                    cls.quality = data.get('quality', 'Alta')
                    cls.vsync = data.get('vsync', False)
                    cls.current_res_idx = data.get('current_res_idx', 5)
                    cls.vol_master = data.get('vol_master', 1.0)
                    cls.vol_music = data.get('vol_music', 0.8)
                    cls.vol_sfx = data.get('vol_sfx', 1.0)
                    cls.vol_ai = data.get('vol_ai', 1.0)
            except:
                pass

    @classmethod
    def save(cls):
        import json
        with open('settings.json', 'w') as f:
            json.dump({
                'quality': cls.quality,
                'vsync': cls.vsync,
                'current_res_idx': cls.current_res_idx,
                'vol_master': cls.vol_master,
                'vol_music': cls.vol_music,
                'vol_sfx': cls.vol_sfx,
                'vol_ai': cls.vol_ai
            }, f)



class MenuSun(Entity):
    """Un sol masivo al fondo con efecto de corona térmica pulsante"""

    def __init__(self, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgb(255, 230, 150),
            scale=300,
            position=(150, 40, 800),
            **kwargs
        )
        self.glow1 = Entity(parent=self, model='sphere', color=color.rgba(255, 140, 0, 120), scale=1.10)
        self.glow2 = Entity(parent=self, model='sphere', color=color.rgba(255, 60, 0, 60), scale=1.25)

    def update(self):
        self.glow1.scale = 1.10 + math.sin(time.time() * 3) * 0.015
        self.glow2.scale = 1.25 + math.cos(time.time() * 2) * 0.03


class MenuPlanet(Entity):
    """Planetas con rotación lenta y majestuosa en el fondo"""

    def __init__(self, **kwargs):
        super().__init__(model='sphere', **kwargs)
        self.rot_speed = random.uniform(1.0, 2.5)

    def update(self):
        self.rotation_y += self.rot_speed * time.dt


class MenuMeteor(Entity):
    """Rocas rojizas/marrones que viajan desde muy lejos hacia la cámara"""

    def __init__(self, **kwargs):
        super().__init__(model='sphere', color=color.rgb(80, 55, 45), **kwargs)
        self.reset_meteor()

    def reset_meteor(self):
        self.position = (random.uniform(-150, 150), random.uniform(-60, 60), random.uniform(400, 600))
        target_pos = Vec3(random.uniform(-20, 20), random.uniform(-10, 10), -10)
        self.direction = (target_pos - self.position).normalized()
        self.speed = random.uniform(15, 40)
        self.rot_speed = Vec3(random.uniform(-40, 40), random.uniform(-40, 40), random.uniform(-40, 40))
        self.scale = random.uniform(1.0, 4.0)


class MenuDust(Entity):
    """Partículas de polvo estelar diminutas con movimiento y deriva constante"""

    def __init__(self, **kwargs):
        super().__init__(
            model='sphere',
            color=color.rgba(255, 255, 255, 90),
            scale=random.uniform(0.01, 0.03),
            **kwargs
        )
        self.speed = random.uniform(0.8, 2.5)

    def update(self):
        self.z -= self.speed * time.dt
        if self.z < 2:
            self.z = random.uniform(25, 35)
            self.x = random.uniform(-20, 20)
            self.y = random.uniform(-12, 12)


class OptionsMenu(Entity):
    def __init__(self, main_menu, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True, **kwargs)
        self.main_menu = main_menu
        
        self.bg_panel = Entity(parent=self, model='quad', color=color.black, alpha=0.85, scale=(99, 99), z=0.1)
        
        self.main_container = Entity(parent=self)
        self.graphics_container = Entity(parent=self, enabled=False)
        self.audio_container = Entity(parent=self, enabled=False)
        
        # --- MAIN CONTAINER ---
        Text(parent=self.main_container, text='AJUSTES DE SISTEMA', position=(0, 0.35), scale=3, origin=(0,0), color=color.white, z=-1)
        
        Button(parent=self.main_container, text='VIDEO', scale=(0.5, 0.08),
               position=(0, 0.15), color=color.dark_gray, highlight_color=color.gray,
               on_click=self.open_graphics, z=-1)
               
        Button(parent=self.main_container, text='AUDIO', scale=(0.5, 0.08),
               position=(0, 0.05), color=color.dark_gray, highlight_color=color.gray,
               on_click=self.open_audio, z=-1)
               
        Button(parent=self.main_container, text='CONTROLES', scale=(0.5, 0.08),
               position=(0, -0.05), color=color.rgb(30, 30, 30), text_color=color.gray, z=-1)
               
        Button(parent=self.main_container, text='VOLVER', scale=(0.4, 0.08), position=(0, -0.25),
               color=color.red, highlight_color=color.red.tint(0.2), on_click=self.close_options, z=-1)

        # --- GRAPHICS CONTAINER ---
        Text(parent=self.graphics_container, text='OPCIONES GRÁFICAS', position=(0, 0.35), scale=3, origin=(0,0), color=color.white, z=-1)
        
        self.btn_quality = Button(parent=self.graphics_container, text=f'CALIDAD GRÁFICA: {GameSettings.quality}', scale=(0.5, 0.08),
                                position=(0, 0.15), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.toggle_quality, z=-1)
                                
        res = GameSettings.resolutions[GameSettings.current_res_idx]
        self.btn_resolution = Button(parent=self.graphics_container, text=f'RESOLUCIÓN: {res[0]}x{res[1]}', scale=(0.5, 0.08),
                                position=(0, 0.05), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.toggle_resolution, z=-1)
                                
        self.btn_vsync = Button(parent=self.graphics_container, text=f'LÍMITE FPS (VSYNC): {"ON" if GameSettings.vsync else "OFF"}', scale=(0.5, 0.08),
                                position=(0, -0.05), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.toggle_vsync, z=-1)
                                
        Button(parent=self.graphics_container, text='VOLVER', scale=(0.4, 0.08), position=(0, -0.25),
               color=color.dark_gray, highlight_color=color.gray, on_click=self.close_graphics, z=-1)

        # --- AUDIO CONTAINER ---
        Text(parent=self.audio_container, text='OPCIONES DE AUDIO', position=(0, 0.35), scale=3, origin=(0,0), color=color.white, z=-1)
        
        Text(parent=self.audio_container, text='VOLUMEN MAESTRO', position=(0, 0.25), scale=1.5, origin=(0,0))
        self.sl_master = Slider(parent=self.audio_container, min=0, max=1, default=GameSettings.vol_master, position=(-0.15, 0.20), scale=0.6, on_value_changed=self.on_master_change)
        self.sl_master.bg.color = color.white
        
        Text(parent=self.audio_container, text='VOLUMEN MÚSICA', position=(0, 0.10), scale=1.5, origin=(0,0))
        self.sl_music = Slider(parent=self.audio_container, min=0, max=1, default=GameSettings.vol_music, position=(-0.15, 0.05), scale=0.6, on_value_changed=self.on_music_change)
        self.sl_music.bg.color = color.white
        
        Text(parent=self.audio_container, text='VOLUMEN EFECTOS', position=(0, -0.05), scale=1.5, origin=(0,0))
        self.sl_sfx = Slider(parent=self.audio_container, min=0, max=1, default=GameSettings.vol_sfx, position=(-0.15, -0.10), scale=0.6, on_value_changed=self.on_sfx_change)
        self.sl_sfx.bg.color = color.white
        
        Text(parent=self.audio_container, text='VOLUMEN IA (ASISTENTE)', position=(0, -0.20), scale=1.5, origin=(0,0))
        self.sl_ai = Slider(parent=self.audio_container, min=0, max=1, default=GameSettings.vol_ai, position=(-0.15, -0.25), scale=0.6, on_value_changed=self.on_ai_change)
        self.sl_ai.bg.color = color.white
        
        Button(parent=self.audio_container, text='VOLVER', scale=(0.4, 0.08), position=(0, -0.40),
               color=color.dark_gray, highlight_color=color.gray, on_click=self.close_audio, z=-1)

    def _update_ai_volume(self):
        # Actualiza el volumen de la IA si está reproduciendo audio actualmente
        for e in scene.entities:
            if type(e).__name__ == 'CompanionManager' and getattr(e, 'audio_player', None):
                e.audio_player.set_volume(GameSettings.vol_ai, GameSettings.vol_master)

    def on_master_change(self):
        GameSettings.vol_master = self.sl_master.value
        GameSettings.save()
        self._update_ai_volume()
        
    def on_music_change(self):
        GameSettings.vol_music = self.sl_music.value
        GameSettings.save()
        
    def on_sfx_change(self):
        GameSettings.vol_sfx = self.sl_sfx.value
        GameSettings.save()
        
    def on_ai_change(self):
        GameSettings.vol_ai = self.sl_ai.value
        GameSettings.save()
        self._update_ai_volume()

    def toggle_quality(self):
        GameSettings.quality = 'Baja' if GameSettings.quality == 'Alta' else 'Alta'
        self.btn_quality.text = f'CALIDAD GRÁFICA: {GameSettings.quality}'
        GameSettings.save()
        
    def toggle_resolution(self):
        GameSettings.current_res_idx = (GameSettings.current_res_idx + 1) % len(GameSettings.resolutions)
        res = GameSettings.resolutions[GameSettings.current_res_idx]
        self.btn_resolution.text = f'RESOLUCIÓN: {res[0]}x{res[1]}'
        # Ursina window resolution apply
        window.resolution = res
        # Para evitar estiramientos no deseados en modo completo si está activado
        if window.fullscreen:
            window.fullscreen = False
            invoke(setattr, window, 'fullscreen', True, delay=0.1)
            
        GameSettings.save()
        
        # Realinear el menú inmediatamente
        if hasattr(self.main_menu, 'align_ui'):
            self.main_menu.align_ui()

    def toggle_vsync(self):
        GameSettings.vsync = not GameSettings.vsync
        self.btn_vsync.text = f'LÍMITE FPS (VSYNC): {"ON" if GameSettings.vsync else "OFF"}'
        window.vsync = GameSettings.vsync
        GameSettings.save()

    def open_options(self, caller=None):
        self.caller = caller
        if self.caller:
            self.caller.disable()
        else:
            self.main_menu.ui_container.disable()
        self.graphics_container.disable()
        self.audio_container.disable()
        self.main_container.enable()
        self.enable()

    def close_options(self):
        self.disable()
        if hasattr(self, 'caller') and self.caller:
            self.caller.enable()
        else:
            self.main_menu.ui_container.enable()

    def open_graphics(self):
        self.main_container.disable()
        self.graphics_container.enable()
        
    def close_graphics(self):
        self.graphics_container.disable()
        self.main_container.enable()

    def open_audio(self):
        self.main_container.disable()
        self.audio_container.enable()
        
    def close_audio(self):
        self.audio_container.disable()
        self.main_container.enable()


class MainMenu(Entity):
    def __init__(self, start_game_func, achievement_manager, change_pilot_func=None, **kwargs):
        super().__init__(**kwargs)
        self.start_game_func = start_game_func
        self.change_pilot_func = change_pilot_func
        self.achievement_manager = achievement_manager
        
        self.score_menu = ScoreMenu(main_menu=self)

        # Contenedor del espacio de fondo
        self.bg_container = Entity(parent=self)

        self.sun = MenuSun(parent=self.bg_container)
        self.planet1 = MenuPlanet(parent=self.bg_container, color=color.rgb(25, 28, 35), scale=12.0,
                                  position=(-25, -10, 60))
        self.planet2 = MenuPlanet(parent=self.bg_container, color=color.rgb(40, 42, 45), scale=5.0,
                                  position=(18, -6, 40))

        self.meteors = []
        for _ in range(8):
            m = MenuMeteor(parent=self.bg_container)
            self.meteors.append(m)

        self.dust_particles = []
        for _ in range(140):
            d = MenuDust(parent=self.bg_container,
                         position=(random.uniform(-22, 22), random.uniform(-12, 12), random.uniform(4, 32)))
            self.dust_particles.append(d)

        # Interfaz de Usuario
        self.ui_container = Entity(parent=camera.ui)

        self.title_text = Text(parent=self.ui_container, text='ASTRA 3D', position=(0, 0.35), origin=(0, 0), scale=6,
                               color=color.white)
        self.subtitle_text = Text(parent=self.ui_container, text='SIMULADOR DE VIAJE ASTRONÁUTICO',
                                  position=(0, 0.23), origin=(0, 0), scale=1.5, color=color.cyan)

        # Main action button
        self.btn_start = Button(parent=self.ui_container, text='INICIAR VUELO', scale=(0.4, 0.1),
                                position=(0, 0.05), color=color.azure, highlight_color=color.cyan,
                                on_click=self.press_start, z=-1)

        # Horizontal button bar for other options at the bottom
        btn_y = -0.35
        self.btn_score = Button(parent=self.ui_container, text='PUNTUACIÓN', scale=(0.25, 0.08),
                                position=(-0.45, btn_y), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_score, z=-1)
        self.btn_achievements = Button(parent=self.ui_container, text='LOGROS', scale=(0.25, 0.08),
                                position=(-0.15, btn_y), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_achievements, z=-1)
        self.btn_options = Button(parent=self.ui_container, text='OPCIONES', scale=(0.25, 0.08),
                                  position=(0.15, btn_y), color=color.dark_gray, highlight_color=color.gray,
                                  on_click=self.press_options, z=-1)
                                  
        # Botón Cambiar Piloto
        self.btn_change_pilot = Button(parent=self.ui_container, text='CAMBIAR PILOTO', scale=(0.25, 0.08),
                                  position=(0.45, btn_y), color=color.dark_gray, highlight_color=color.gray,
                                  on_click=self.press_change_pilot, z=-1)
                                  
        self.btn_exit = Button(parent=self.ui_container, text='SALIR', scale=(0.15, 0.06),
                                position=(window.right.x - 0.1, window.bottom.y + 0.05), color=color.red.tint(-0.2), highlight_color=color.red.tint(0.1),
                                on_click=application.quit, z=-1)

        self.options_menu = OptionsMenu(main_menu=self)
        self.achievements_menu = AchievementsMenu(main_menu=self, achievement_manager=self.achievement_manager)
        self.ship_menu = ShipSelectionMenu(main_menu=self, start_game_func=self.start_game_func)

        self.fade_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 0), scale=(99, 99), z=-10,
                                   enabled=False)
        self.pan_direction = 1

    def update(self):
        """Animación de paneo suave para el fondo del menú"""
        if self.bg_container.enabled:
            self.bg_container.rotation_y += 0.5 * self.pan_direction * time.dt
            if self.bg_container.rotation_y > 5 or self.bg_container.rotation_y < -5:
                self.pan_direction *= -1

    def press_start(self):
        self.ui_container.disable()
        self.ship_menu.enable()

    def press_options(self):
        self.options_menu.open_options()

    def press_change_pilot(self):
        if self.change_pilot_func:
            self.change_pilot_func()

    def press_achievements(self):
        self.achievements_menu.open_achievements()

    def align_ui(self):
        self.btn_exit.position = (window.right.x - 0.1, window.bottom.y + 0.05)

    def press_score(self):
        self.score_menu.open_score()

    def disable(self):
        self.bg_container.disable()
        self.ui_container.disable()

    def enable(self):
        self.bg_container.enable()
        self.ui_container.enable()