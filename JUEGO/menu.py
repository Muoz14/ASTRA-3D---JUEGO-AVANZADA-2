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


class WormholeParticle(Entity):
    """Líneas brillantes que simulan un túnel de agujero de gusano (Wormhole)."""
    def __init__(self, **kwargs):
        super().__init__(
            model='cube', # Cambiado a cubo para evitar el warning de 'cylinder' perdido en Ursina
            color=color.rgba(50, 150, 255, random.randint(80, 160)),
            unlit=True,
            **kwargs
        )
        self.reset_particle()

    def reset_particle(self):
        # Nacen solo en los bordes (radio 15 a 30) para dejar el centro vacío y formar un TÚNEL
        self.angle = random.uniform(0, math.pi * 2)
        self.radius = random.uniform(15, 30)
        self.position = (math.cos(self.angle) * self.radius, math.sin(self.angle) * self.radius, random.uniform(150, 300))
        self.speed = random.uniform(150, 300)
        
        # Alargados en Z para simular velocidad hiperlumínica
        self.scale = (random.uniform(0.1, 0.3), random.uniform(0.1, 0.3), random.uniform(15, 50))
        self.rotation_z = math.degrees(self.angle)

    def update(self):
        # Avanzar hacia la cámara
        self.z -= self.speed * time.dt
        
        # Efecto de Espiral (Swirl): Rotar ligeramente alrededor del centro (0,0) en cada frame
        swirl_speed = 0.5 * time.dt
        new_x = self.x * math.cos(swirl_speed) - self.y * math.sin(swirl_speed)
        new_y = self.x * math.sin(swirl_speed) + self.y * math.cos(swirl_speed)
        self.x = new_x
        self.y = new_y
        self.rotation_z += 0.5 * time.dt * 50 # Girar sobre sí mismas un poco para acompañar
        
        if self.z < -20:
            self.reset_particle()


class MenuTurboEffect:
    """Clase base polimórfica para los efectos de turbo en el menú."""
    def spawn(self, ship):
        pass

class MenuTurboNave1(MenuTurboEffect):
    """Efectos de turbo ágiles y rápidos para la Nave 1."""
    def spawn(self, ship):
        from ursina import Entity, color, random, curve, destroy
        for offset in ship.config.thruster_offsets:
            # Cositos blancos/celestes simulando alta velocidad
            p = Entity(parent=ship.bob_container, model='sphere', color=color.rgba(255, 255, 255, 150), unlit=True,
                       scale=random.uniform(0.03, 0.06), position=offset)
            # Se alejan muy rápido hacia atrás
            p.animate_position(p.position + (random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), -2.5), duration=0.3, curve=curve.linear)
            p.animate_scale(0, duration=0.3, curve=curve.linear)
            destroy(p, delay=0.3)

class MenuTurboNave2(MenuTurboEffect):
    """Efectos de turbo masivos y pesados para el Coloso (Nave 2)."""
    def spawn(self, ship):
        from ursina import Entity, color, random, curve, destroy
        for offset in ship.config.thruster_offsets:
            # Cositos blancos/naranjas más grandes simulando potencia bruta
            p = Entity(parent=ship.bob_container, model='sphere', color=color.rgba(255, 200, 200, 200), unlit=True,
                       scale=random.uniform(0.06, 0.12), position=offset)
            # Se dispersan un poco más debido a la potencia del Coloso
            p.animate_position(p.position + (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), -2.0), duration=0.4, curve=curve.linear)
            p.animate_scale(0, duration=0.4, curve=curve.linear)
            destroy(p, delay=0.4)

class MenuDummyShip(Entity):
    """Nave dummy para el menú principal con efecto de flotación y propulsores."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bob_container = Entity(parent=self)
        self.model_entity = Entity(parent=self.bob_container)
        self.time_offset = random.uniform(0, 10)
        
        # Propulsores traseros simulando aceleración máxima
        self.thruster_glows = []
        self.turbo_effect = None
        self.trail_timer = 0

    def set_config(self, config):
        self.config = config
        self.model_entity.model = config.model
        self.model_entity.color = config.ship_color
        self.model_entity.rotation = getattr(config, 'model_rotation_offset', (0,0,0))
        
        # Polimorfismo: Instanciar la estrategia de partículas correcta según la nave
        if config.id == "nave1":
            self.turbo_effect = MenuTurboNave1()
        else:
            self.turbo_effect = MenuTurboNave2()
        
        # Usamos la escala grande del dummy_config si existe, de lo contrario un multiplicador
        if hasattr(config, 'dummy_config') and config.dummy_config:
            self.scale = config.dummy_config.scale_large
        else:
            multiplier = 1.5
            self.scale = (config.scale[0] * multiplier, config.scale[1] * multiplier, config.scale[2] * multiplier)
        
        for t in self.thruster_glows:
            destroy(t)
        self.thruster_glows.clear()
        
        # Crear propulsores brillantes adjuntos al bob_container para que floten junto con la nave
        for offset in config.thruster_offsets:
            local_offset = offset
            
            local_scale = (
                config.thruster_scale[0] * 1.5,
                config.thruster_scale[1] * 1.5,
                config.thruster_scale[2] * 2.0
            )
            
            glow = Entity(parent=self.bob_container, model='sphere', color=color.rgba(0, 255, 255, 200), unlit=True, scale=local_scale, position=local_offset)
            self.thruster_glows.append(glow)

    def update(self):
        t = time.time() + self.time_offset
        
        # Efecto de flotación suave aplicado al contenedor interior para no pelear con animaciones de posición globales
        self.bob_container.y = math.sin(t * 2) * 0.1
        self.bob_container.rotation_z = math.sin(t * 1.5) * 2
        
        # Pulsación intensa de los propulsores
        for glow in self.thruster_glows:
            glow.scale_z = glow.scale_x * (2.0 + math.sin(t * 40) * 0.8)
            
        # Emitir partículas polimórficas de velocidad
        self.trail_timer -= time.dt
        if self.trail_timer <= 0:
            if self.turbo_effect:
                self.turbo_effect.spawn(self)
            self.trail_timer = 0.05


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


class MenuSpeedLine(Entity):
    """Líneas de velocidad 2D para la UI del menú, simulando viaje interestelar a velocidad turbo."""
    def __init__(self, speed_mult=1.0, origin_x=0.45, origin_y=-0.15, **kwargs):
        # z=15 garantiza que se dibujen por detrás del panel izquierdo (que tiene z=10)
        super().__init__(parent=camera.ui, model='quad', z=15, **kwargs)
        self.angle = random.uniform(0, math.tau)
        self.distance = random.uniform(0.05, 0.35) # Comienzan más cerca del centro del efecto
        self.speed = random.uniform(3.0, 5.0) * speed_mult # Más lentas y ambientales
        self.max_scale_y = random.uniform(0.06, 0.20) 
        self.scale = (random.uniform(0.001, 0.002), 0.01)
        self.rotation_z = math.degrees(self.angle) - 90
        
        # El centro (origen de las líneas) está desplazado dinámicamente
        self.origin_x = origin_x
        self.origin_y = origin_y
        
        self.update_position()

    def update_position(self):
        self.x = self.origin_x + math.cos(self.angle) * self.distance
        self.y = self.origin_y + math.sin(self.angle) * self.distance

    def update(self):
        self.distance += self.speed * time.dt
        self.scale_y = min(self.max_scale_y, self.distance * 0.5)
        self.update_position()
        if self.distance > 0.8: self.alpha -= time.dt * 4 # Desvanecen más lejos
        if self.distance > 1.5 or self.alpha <= 0: destroy(self)


class MainMenu(Entity):
    def __init__(self, start_game_func, achievement_manager, change_pilot_func=None, **kwargs):
        super().__init__(**kwargs)
        self.start_game_func = start_game_func
        self.change_pilot_func = change_pilot_func
        self.achievement_manager = achievement_manager
        
        self.score_menu = ScoreMenu(main_menu=self)

        # Contenedor del espacio de fondo
        self.bg_container = Entity(parent=self)
        
        self.speed_line_timer = 0

        self.wormhole_container = Entity(parent=self.bg_container)

        self.wormhole_particles = []
        for _ in range(80):
            w = WormholeParticle(parent=self.wormhole_container)
            self.wormhole_particles.append(w)
            
        # Nave Dummy en la escena 3D (centrada en el panel derecho, más cerca de la cámara)
        from ships import AVAILABLE_SHIPS
        self.menu_ship = MenuDummyShip(parent=self.bg_container, position=(5.5, -2.5, 12), rotation=(0, 7, 0))
        self.menu_ship.set_config(AVAILABLE_SHIPS["nave1"])

        # Interfaz de Usuario (Columna Izquierda)
        self.ui_container = Entity(parent=camera.ui)
        
        # Asegurar que el fondo general del menú sea negro
        window.color = color.black
        
        # Fondo sólido para la columna izquierda
        self.ui_bg = Entity(parent=self.ui_container, model='quad', color=color.hex('#0a0c0f'), scale=(1.0, 2), position=(-0.6, 0), z=10)

        ui_x = -0.8  # Posición X para alinear más a la izquierda y evitar desborde

        self.title_text = Text(parent=self.ui_container, text='ASTRA 3D', position=(ui_x, 0.35), origin=(-0.5, 0), scale=4.5,
                               color=color.white)
        self.subtitle_text = Text(parent=self.ui_container, text='SIMULADOR DE VIAJE ASTRONÁUTICO',
                                  position=(ui_x, 0.23), origin=(-0.5, 0), scale=1.2, color=color.cyan)

        # Botones alineados verticalmente
        btn_start_y = 0.05
        self.btn_start = Button(parent=self.ui_container, text='INICIAR VUELO', scale=(0.4, 0.08),
                                position=(ui_x + 0.2, btn_start_y), color=color.azure, highlight_color=color.cyan,
                                on_click=self.press_start, z=-1)

        self.btn_score = Button(parent=self.ui_container, text='PUNTUACIÓN', scale=(0.4, 0.08),
                                position=(ui_x + 0.2, btn_start_y - 0.1), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_score, z=-1)
                                
        self.btn_achievements = Button(parent=self.ui_container, text='LOGROS', scale=(0.4, 0.08),
                                position=(ui_x + 0.2, btn_start_y - 0.2), color=color.dark_gray, highlight_color=color.gray,
                                on_click=self.press_achievements, z=-1)
                                
        self.btn_options = Button(parent=self.ui_container, text='OPCIONES', scale=(0.4, 0.08),
                                  position=(ui_x + 0.2, btn_start_y - 0.3), color=color.dark_gray, highlight_color=color.gray,
                                  on_click=self.press_options, z=-1)
                                  
        self.btn_change_pilot = Button(parent=self.ui_container, text='CAMBIAR PILOTO', scale=(0.4, 0.08),
                                  position=(ui_x + 0.2, btn_start_y - 0.4), color=color.dark_gray, highlight_color=color.gray,
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
        if self.bg_container.enabled and hasattr(self, 'menu_ship'):
            # El túnel 3D se alinea dinámicamente con la nave, pero con un desplazamiento exagerado 
            # a la derecha en el menú principal (multiplicador 2.5) para que el centro quede más allá de la nave.
            # En la selección de naves (x=0), el centro sigue siendo exactamente 0.
            self.wormhole_container.x = self.menu_ship.x * 2.5
            self.wormhole_container.y = self.menu_ship.y
            
            self.speed_line_timer -= time.dt
            if self.speed_line_timer <= 0:
                # Calcular dinámicamente el origen de las líneas en base a la posición de la nave
                # Cuando x=5.5 (menú principal), origin_x = 0.45. Cuando x=0 (selección de nave), origin_x = 0
                curr_origin_x = (self.menu_ship.x / 5.5) * 0.45 if self.menu_ship.x > 0 else 0
                
                MenuSpeedLine(color=color.rgba(200, 240, 255, 70), origin_x=curr_origin_x) 
                # Una secundaria ocasional para dar profundidad sin saturar
                if random.random() < 0.3:
                    MenuSpeedLine(color=color.rgba(100, 200, 255, 80), speed_mult=1.2, origin_x=curr_origin_x) 
                self.speed_line_timer = 0.05

    def press_start(self):
        self.ui_container.disable()
        # Animar la nave hacia el centro
        self.menu_ship.animate_position((0, -2, 12), duration=0.8, curve=curve.in_out_expo)
        self.menu_ship.animate_rotation((0, 0, 0), duration=0.8, curve=curve.in_out_expo)
        invoke(self.ship_menu.enable, delay=0.8)

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