from ursina import *
from player import PlayerShip
from environment import AsteroidManager, CosmicBackground, SpaceDustManager
from menu import MainMenu
from cinematics import IntroCinematic
from ship_tuner import ShipTuner
from menu import MainMenu, GameSettings
from achievements import AchievementManager
from accounts import AccountMenu


class HudMenuButton(Entity):
    def __init__(self, text, y, on_click, accent='#00EFFF', danger=False, primary=False, **kwargs):
        super().__init__(parent=kwargs.pop('parent', camera.ui), z=kwargs.pop('z', -2), **kwargs)
        border_color = color.hex(accent)
        fill_color = color.hex('#123049') if primary else color.hex('#071526')
        if danger:
            border_color = color.hex('#FF4D5A')
            fill_color = color.hex('#331019') if primary else color.hex('#120912')

        self.border = Entity(
            parent=self,
            model=Quad(radius=0.010),
            color=border_color,
            scale=(0.520, 0.076),
            position=(0, y),
            z=0.04
        )
        self.button = Button(
            parent=self,
            text=text,
            scale=(0.502, 0.062),
            position=(0, y),
            color=fill_color,
            highlight_color=border_color,
            pressed_color=color.hex('#061526'),
            text_color=color.white,
            on_click=on_click,
            z=-0.05
        )
        Entity(parent=self, model='quad', color=border_color, scale=(0.018, 0.004), position=(-0.222, y), z=-0.12)
        Entity(parent=self, model='quad', color=border_color, scale=(0.018, 0.004), position=(0.222, y), z=-0.12)


def add_hud_corners(parent, edge_color, scale=(0.72, 0.58), z=-0.14):
    x = scale[0] / 2 - 0.040
    y = scale[1] / 2 - 0.040
    corner_len = 0.050
    for sx in (-1, 1):
        for sy in (-1, 1):
            Entity(parent=parent, model='quad', color=edge_color, scale=(corner_len, 0.003), position=(sx * x, sy * y), z=z)
            Entity(parent=parent, model='quad', color=edge_color, scale=(0.003, corner_len), position=(sx * (x + sx * 0.024), sy * (y - sy * 0.024)), z=z)


def add_resting_ship_icon(parent, position=(0, 0.060), accent='#00EFFF'):
    accent_color = color.hex(accent)
    x, y = position
    Entity(parent=parent, model='quad', color=accent_color, scale=(0.070, 0.020), position=(x, y), z=-0.22)
    Entity(parent=parent, model='quad', color=accent_color, scale=(0.028, 0.028), position=(x + 0.044, y), rotation_z=45, z=-0.23)
    Entity(parent=parent, model='quad', color=color.hex('#123049'), scale=(0.020, 0.010), position=(x - 0.010, y + 0.002), z=-0.24)
    Entity(parent=parent, model='quad', color=accent_color, scale=(0.032, 0.008), position=(x - 0.020, y - 0.020), rotation_z=-20, z=-0.22)
    Entity(parent=parent, model='quad', color=accent_color, scale=(0.032, 0.008), position=(x - 0.020, y + 0.020), rotation_z=20, z=-0.22)
    Entity(parent=parent, model='quad', color=color.hex('#4AA3C7'), scale=(0.045, 0.004), position=(x - 0.075, y + 0.012), z=-0.22)
    Entity(parent=parent, model='quad', color=color.hex('#4AA3C7'), scale=(0.030, 0.004), position=(x - 0.085, y - 0.012), z=-0.22)
    Text(parent=parent, text='motores en espera', origin=(0, 0), position=(x, y - 0.052), scale=0.45,
         color=color.hex('#8AA8B8'), z=-0.30)


def add_failed_ship_icon(parent, position=(0, 0.070)):
    x, y = position
    red = color.hex('#FF4D5A')
    cyan_dark = color.hex('#123049')
    Entity(parent=parent, model='quad', color=red, scale=(0.076, 0.020), position=(x, y), rotation_z=-8, z=-0.22)
    Entity(parent=parent, model='quad', color=red, scale=(0.026, 0.026), position=(x + 0.045, y - 0.006), rotation_z=37, z=-0.23)
    Entity(parent=parent, model='quad', color=cyan_dark, scale=(0.018, 0.010), position=(x - 0.006, y + 0.001), z=-0.24)
    Entity(parent=parent, model='quad', color=red, scale=(0.032, 0.007), position=(x - 0.026, y - 0.020), rotation_z=-34, z=-0.22)
    Entity(parent=parent, model='quad', color=red, scale=(0.032, 0.007), position=(x - 0.018, y + 0.021), rotation_z=30, z=-0.22)
    Text(parent=parent, text='x_x', origin=(0, 0), position=(x + 0.087, y + 0.003), scale=0.60,
         color=red, z=-0.30)
    Entity(parent=parent, model='quad', color=color.hex('#FF9A55'), scale=(0.018, 0.005), position=(x - 0.072, y), z=-0.22)
    Entity(parent=parent, model='quad', color=color.hex('#FF9A55'), scale=(0.011, 0.004), position=(x - 0.092, y + 0.014), z=-0.22)


class PauseMenu(Entity):
    def __init__(self, game_instance, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, z=0, **kwargs)
        self.game = game_instance
        self.bg = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 170), scale=(99, 99), z=5)

        self.border = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#00EFFF'),
            scale=(0.88, 0.94),
            z=0.20
        )
        self.panel = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#05101E'),
            scale=(0.862, 0.918),
            z=0.10
        )
        add_hud_corners(self, color.hex('#6EEBFF'), scale=(0.84, 0.90), z=-0.10)

        Text(parent=self, text='ASTRA 3D', origin=(0, 0), position=(0, 0.370), scale=0.82,
             color=color.hex('#6E8798'), z=-0.30)
        self.title = Text(parent=self, text='PAUSA', origin=(0, 0), scale=4.2,
                          color=color.hex('#BFEFFF'), position=(0, 0.292), z=-0.30)

        Entity(parent=self, model='quad', color=color.hex('#00EFFF'), scale=(0.42, 0.004),
               position=(0, 0.228), z=-0.20)
        add_resting_ship_icon(self, position=(0, 0.151), accent='#00EFFF')
        self.message_text = Text(parent=self, text='',
             origin=(0, 0), position=(0, 0.052), scale=0.92, color=color.hex('#D8E7F0'), z=-0.30)

        HudMenuButton(parent=self, text='REANUDAR VUELO', y=-0.050, on_click=self.resume,
                      accent='#00EFFF', primary=True, z=-0.25)
        HudMenuButton(parent=self, text='LOGROS', y=-0.138, on_click=self.open_achievements,
                      accent='#4AA3C7', z=-0.25)
        HudMenuButton(parent=self, text='OPCIONES', y=-0.226, on_click=self.open_options,
                      accent='#4AA3C7', z=-0.25)
        HudMenuButton(parent=self, text='SALIR AL MENÚ', y=-0.314, on_click=self.return_to_main_menu,
                      accent='#FF4D5A', danger=True, z=-0.25)

    def resume(self):
        application.paused = False
        self.game.player.pause_menu_open = False
        self.disable()
        mouse.locked = True
        self.game.player.hud_container.enable()
        if hasattr(self.game.player, 'ai_companion'):
            self.game.player.ai_companion.ui.enable()

    def change_pilot(self):
        self.resume()
        self.game.change_pilot()

    def return_to_main_menu(self):
        self.resume()
        self.game.return_to_main_menu()

    def open_options(self):
        if hasattr(self.game, 'main_menu') and hasattr(self.game.main_menu, 'options_menu'):
            self.game.main_menu.options_menu.open_options(caller=self)

    def open_achievements(self):
        if hasattr(self.game, 'main_menu') and hasattr(self.game.main_menu, 'achievements_menu'):
            self.game.main_menu.achievements_menu.open_achievements(caller=self)

    def on_enable(self):
        import random
        msgs = [
            "Motores en espera. Revisa sistemas y vuelve cuando estés listo.",
            "Sistemas auxiliares en modo de ahorro de energía.",
            "Analizando telemetría y daños del casco...",
            "Oxígeno al 100%. Sistemas vitales estables.",
            "Escáner de corto alcance en modo pasivo.",
            "Recargando bancos de capacitores principales...",
        ]
        if hasattr(self, 'message_text'):
            self.message_text.text = random.choice(msgs)


class GlobalInputController(Entity):
    def __init__(self, game_instance, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.game = game_instance

    def input(self, key):
        if key == 'f11':
            window.fullscreen = not window.fullscreen
            
        if key == 'f12':
            if hasattr(self.game, 'ship_tuner'):
                self.game.ship_tuner.enabled = not self.game.ship_tuner.enabled
                
        if key == 'p':
            if (self.game.game_over_menu.enabled
                    or self.game.main_menu.ui_container.enabled
                    or self.game.main_menu.options_menu.enabled
                    or getattr(self.game.main_menu, 'achievements_menu', None) and self.game.main_menu.achievements_menu.enabled
                    or not getattr(self.game.player, 'enabled', False)):
                return
            if getattr(self.game.player.tactical_map, 'is_open', False) or getattr(self.game.player.inventory, 'is_open', False) or getattr(self.game.player.upgrades_ui, 'is_open', False):
                return
            application.paused = not application.paused
            self.game.player.pause_menu_open = application.paused
            self.game.pause_menu.enabled = application.paused
            mouse.locked = not application.paused
            if application.paused:
                self.game.player.hud_container.disable()
                if hasattr(self.game.player, 'ai_companion'):
                    self.game.player.ai_companion.ui.disable()
            else:
                self.game.player.hud_container.enable()
                if hasattr(self.game.player, 'ai_companion'):
                    self.game.player.ai_companion.ui.enable()


class GameOverMenu(Entity):
    def __init__(self, restart_func, menu_func=None, change_pilot_func=None, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, **kwargs)
        self.menu_func = menu_func
        self.change_pilot_func = change_pilot_func
        Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 210), scale=(99, 99), z=1)

        self.panel_border = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#00EFFF'),
            scale=(0.90, 0.90),
            z=0.20
        )
        self.panel = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#05101E'),
            scale=(0.88, 0.88),
            z=0.10
        )
        add_hud_corners(self, color.hex('#FF4D5A'), scale=(0.86, 0.86), z=-0.10)

        Entity(parent=self, model='quad', color=color.hex('#FF4D5A'), scale=(0.24, 0.004),
               position=(0, 0.310), z=-0.20)
        Text(parent=self, text='!', origin=(0, 0), position=(0, 0.338), scale=1.1,
             color=color.hex('#FF4D5A'), z=-0.30)

        Text(parent=self, text='MISIÓN FALLIDA', origin=(0, 0), scale=3.6,
             color=color.hex('#FF4D5A'), position=(0, 0.252), z=-0.30)

        add_failed_ship_icon(self, position=(0, 0.142))
        self.msg1 = Text(parent=self, text='',
             origin=(0, 0), position=(0, 0.056), scale=0.90, color=color.white, z=-0.30)
        self.msg2 = Text(parent=self, text='',
             origin=(0, 0), position=(0, 0.010), scale=0.72, color=color.hex('#4ACBFF'), z=-0.30)

        HudMenuButton(parent=self, text='REINTENTAR', y=-0.112, on_click=restart_func,
                      accent='#FF4D5A', danger=True, primary=True, z=-0.25)
        HudMenuButton(parent=self, text='VOLVER AL MENU', y=-0.202, on_click=self.go_to_menu,
                      accent='#4AA3C7', z=-0.25)
        HudMenuButton(parent=self, text='SALIR', y=-0.292, on_click=application.quit,
                      accent='#4AA3C7', z=-0.25)

    def go_to_menu(self):
        self.disable()
        if self.menu_func:
            self.menu_func()

    def on_enable(self):
        import random
        msgs = [
            ("Se perdió la señal de la nave.", "Recalibra sistemas y vuelve a intentarlo."),
            ("Fallo catastrófico en el núcleo.", "Soporte vital desconectado."),
            ("Integridad del casco comprometida.", "La tripulación ha sido evacuada."),
            ("Destrucción inminente.", "Escombros dispersos en la órbita baja."),
            ("Sistemas principales fuera de línea.", "No hay respuesta de los motores."),
            ("La misión ha fracasado.", "Se requiere un nuevo intento de inserción."),
        ]
        t1, t2 = random.choice(msgs)
        if hasattr(self, 'msg1') and hasattr(self, 'msg2'):
            self.msg1.text = t1
            self.msg2.text = t2


class GameApp:
    def __init__(self):
        # vsync=False quita el límite de FPS y development_mode=False optimiza el rendimiento interno
        self.app = Ursina(development_mode=False, vsync=False)
        
        GameSettings.load()
        res = GameSettings.resolutions[GameSettings.current_res_idx]
        window.size = res
        window.vsync = GameSettings.vsync
        
        window.center_on_screen()
        window.color = color.black
        window.title = "Astra 3D"
        window.fps_counter.enabled = True
        window.exit_button.visible = False

        # Plano de renderizado seguro para evitar el quiebre de profundidad
        camera.clip_plane_far = 10000
        self.sky = Sky(color=color.black)

        self.game_over_menu = GameOverMenu(restart_func=self.restart_game, menu_func=self.return_to_main_menu, change_pilot_func=self.change_pilot)
        self.pause_menu = PauseMenu(game_instance=self)
        self.global_input = GlobalInputController(game_instance=self)
        self.achievement_manager = AchievementManager()
        self.main_menu = MainMenu(start_game_func=self.start_actual_game, achievement_manager=self.achievement_manager, change_pilot_func=self.change_pilot)
        self.main_menu.ui_container.disable() # Ocultar hasta seleccionar cuenta
        self.main_menu.bg_container.disable() # Ocultar fondo 3D brillante

        self.account_menu = AccountMenu(on_account_selected=self.on_account_selected)
        self.main_menu.account_manager = self.account_menu.manager

        self.cosmic_bg = CosmicBackground()
        self.cosmic_bg.enabled = False

        self.player = PlayerShip(game_over_menu=self.game_over_menu, game_app=self)
        self.achievement_manager.set_player(self.player)
        self.player.achievements = self.achievement_manager
        
        # --- INITIALIZE OBJECT POOL ---
        from pool_manager import ObjectPool
        self.pool = ObjectPool()
        
        self.environment = AsteroidManager(player=self.player, count=60, radius=300, pool=self.pool)
        self.space_dust = SpaceDustManager(player=self.player, count=200, radius=60)
        self.intro_cinematic = IntroCinematic(self.player)
        
        from cinematics import PlanetAnalysisCinematic
        self.player.planet_cinematic = PlanetAnalysisCinematic(self.player)
        
        self.ship_tuner = ShipTuner(self.player)
        from missions import MissionManager
        self.mission_manager = MissionManager(player=self.player)
        self.player.mission_manager = self.mission_manager # Pasar referencia al jugador

        self.player.enabled = False
        self.space_dust.enabled = False
        self.environment.clear_asteroids() # No mostrar asteroides en el menú
        mouse.locked = False

        self.player.hud_container.disable()

    def change_pilot(self):
        self.return_to_main_menu()
        self.main_menu.ui_container.disable()
        self.main_menu.bg_container.disable()
        self.account_menu.enable()
        self.account_menu.build_ui()
        
    def save_pilot_stats(self, score, time_flown):
        acc_id = getattr(self.main_menu, 'current_account_id', None)
        if acc_id:
            for acc in self.account_menu.manager.accounts:
                if acc['id'] == acc_id:
                    stats = acc.setdefault('stats', {
                        'total_score': 0, 'high_score': 0, 'enemies_destroyed': 0, 'time_flown': 0
                    })
                    stats['total_score'] += score
                    if score > stats['high_score']:
                        stats['high_score'] = score
                    stats['time_flown'] += int(time_flown)
                    self.account_menu.manager.save()
                    break

    def on_account_selected(self, acc_id, acc_name):
        self.achievement_manager.set_account(acc_id)
        self.main_menu.current_account_id = acc_id
        
        # Cargar la nave guardada para este piloto
        selected_ship = 'nave1'
        for acc in self.account_menu.manager.accounts:
            if acc['id'] == acc_id:
                selected_ship = acc.get('selected_ship', 'nave1')
                break
                
        # Sincronizar el menú de selección de naves
        if hasattr(self.main_menu, 'ship_menu'):
            try:
                idx = self.main_menu.ship_menu.ship_keys.index(selected_ship)
                self.main_menu.ship_menu.current_idx = idx
            except:
                pass
                
        # Actualizar la nave visual en el menú
        # Actualizar la nave visual en el menú
        from ships import AVAILABLE_SHIPS
        if hasattr(self.main_menu, 'menu_ship') and selected_ship in AVAILABLE_SHIPS:
            self.main_menu.menu_ship.set_config(AVAILABLE_SHIPS[selected_ship])
            # Forzar la posición y rotación inmediatamente
            self.main_menu.menu_ship.position = (5.5, -2.5, 12)
            self.main_menu.menu_ship.rotation = (0, 7, 0)
            
        # Forzar el restablecimiento de la cámara a su posición por defecto en Ursina
        camera.parent = scene
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)
        camera.fov = 40

        self.main_menu.ui_container.enable()
        self.main_menu.bg_container.enable()

    def start_actual_game(self, ship_id="nave1"):
        window.color = color.black
        
        # Aplicar ajustes gráficos
        window.vsync = GameSettings.vsync
        self.cosmic_bg.enabled = True
        self.cosmic_bg.set_quality(GameSettings.quality)
        
        if GameSettings.quality == 'Baja':
            self.environment.count = 20
            self.space_dust.count = 0
            self.space_dust.enabled = False
        else:
            self.environment.count = 60
            self.space_dust.count = 200
            self.space_dust.enabled = True
            self.space_dust.reset_particles()
            
        self.environment.clear_and_respawn()
        
        self.achievement_manager.reset_run()
        self.player.change_ship(ship_id)
        self.player.reset_ship()
        
        # Iniciar Misiones
        self.mission_manager.reset()
        self.mission_manager.add_mission(
            id="main_01",
            title="Investiga la Anomalía",
            description="Llega a la cima del Planeta Fracturado y analízalo usando el escáner incorporado en tu nave para descifrar su origen.",
            short_description="Analiza la cima del Planeta Fracturado.",
            target_pos=Vec3(291, 1130, 2193),
            is_main=True
        )
        self.mission_manager.add_mission(
            id="sec_01",
            title="Limpieza Orbital",
            description="El sector está plagado de asteroides inestables. Destruye 25 asteroides pequeños para despejar la ruta de navegación.",
            short_description="Destruye 25 asteroides pequeños.",
            is_main=False,
            max_progress=25
        )
        self.mission_manager.add_mission(
            id="sec_02",
            title="Recolector de Recursos",
            description="Destruye asteroides para encontrar y extraer 15 fragmentos de minerales raros que nos servirán para mejorar la nave.",
            short_description="Extrae 15 fragmentos minerales.",
            is_main=False,
            max_progress=15
        )
        self.mission_manager.add_mission(
            id="sec_03",
            title="Exploración Profunda",
            description="Navega 15,000 metros a través de los peligrosos escombros del cuadrante para cartografiar la zona de forma segura.",
            short_description="Navega 15,000 metros.",
            is_main=False,
            max_progress=15000
        )
        
        self.mission_manager.ui.enable()
        self.mission_manager.waypoint.enable()
        
        self.intro_cinematic.play()
        mouse.locked = True

    def return_to_main_menu(self):
        self.intro_cinematic.stop_and_clear()
        self.mission_manager.ui.disable()
        self.mission_manager.waypoint.disable()
        
        if hasattr(self, 'save_pilot_stats') and hasattr(self.player, 'is_dead') and not self.player.is_dead:
            self.save_pilot_stats(int(self.player.session_score), int(self.player.session_time))
        
        if getattr(self.player.tactical_map, 'is_open', False):
            self.player.tactical_map.toggle()
        if getattr(self.player.inventory, 'is_open', False):
            self.player.inventory.toggle()
        if hasattr(self.player, 'upgrades_ui') and getattr(self.player.upgrades_ui, 'is_open', False):
            self.player.upgrades_ui.toggle()
            
        if hasattr(self.player, 'inventory'):
            self.player.inventory.clear_inventory()
            
        self.player.enabled = False
        self.player.clear_persistent_ui()
        self.player.hud_container.disable()
        # Apagar inmediatamente cualquier mensaje de IA pendiente
        if hasattr(self.player, 'ai_companion'):
            self.player.ai_companion.ui.hide_message_instant()
            
        self.cosmic_bg.enabled = False
        self.space_dust.enabled = False
        self.environment.clear_asteroids()

        camera.parent = scene
        camera.position = (0, 0, -20)
        camera.rotation = (0, 0, 0)
        camera.fov = 40
        self.main_menu.enable()
        self.main_menu.ui_container.enable()
        self.main_menu.bg_container.enable()
        if hasattr(self.main_menu, 'menu_ship'):
            # Detener cualquier animación en curso para que no sobreescriba la posición al reanudar
            if hasattr(self.main_menu.menu_ship, 'animations'):
                for anim in self.main_menu.menu_ship.animations:
                    anim.kill()
                self.main_menu.menu_ship.animations.clear()
            
            # Asegurar que la nave vuelva a su posición original a la derecha
            self.main_menu.menu_ship.position = (5.5, -2.5, 12)
            self.main_menu.menu_ship.rotation = (0, 7, 0)
            
            # Forzar la posición de nuevo en el siguiente frame para evitar bugs del motor con secuencias interrumpidas
            invoke(setattr, self.main_menu.menu_ship, 'position', (5.5, -2.5, 12), delay=0.05)
            invoke(setattr, self.main_menu.menu_ship, 'rotation', (0, 7, 0), delay=0.05)
            
        if hasattr(self.main_menu, 'ship_menu'):
            self.main_menu.ship_menu.disable()
        mouse.locked = False

    def restart_game(self):
        self.intro_cinematic.stop_and_clear()
        
        if hasattr(self, 'save_pilot_stats') and hasattr(self.player, 'is_dead') and not self.player.is_dead:
            self.save_pilot_stats(int(self.player.session_score), int(self.player.session_time))
            
        if getattr(self.player.tactical_map, 'is_open', False):
            self.player.tactical_map.toggle()
        if getattr(self.player.inventory, 'is_open', False):
            self.player.inventory.toggle()
        if hasattr(self.player, 'inventory'):
            self.player.inventory.clear_inventory()
            
        self.achievement_manager.reset_run()
        self.player.reset_ship()
        self.environment.clear_and_respawn()
        self.space_dust.reset_particles()
        self.game_over_menu.enabled = False

        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        mouse.locked = True
        application.paused = False

    def run(self):
        self.app.run()


if __name__ == '__main__':
    game = GameApp()
    game.run()