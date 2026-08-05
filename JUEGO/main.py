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
            z=-0.05,
            ignore_paused=kwargs.get('ignore_paused', False)
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
                      accent='#00EFFF', primary=True, z=-0.25, ignore_paused=True)
        HudMenuButton(parent=self, text='LOGROS', y=-0.138, on_click=self.open_achievements,
                      accent='#4AA3C7', z=-0.25, ignore_paused=True)
        HudMenuButton(parent=self, text='OPCIONES', y=-0.226, on_click=self.open_options,
                      accent='#4AA3C7', z=-0.25, ignore_paused=True)
        HudMenuButton(parent=self, text='SALIR AL MENÚ', y=-0.314, on_click=self.return_to_main_menu,
                      accent='#FF4D5A', danger=True, z=-0.25, ignore_paused=True)

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
        self.cheat_buffer = ""
        self.last_key_time = 0

    def input(self, key):
        from ships import AVAILABLE_SHIPS
        
        # Atajos de desarrollador para probar la IA Enemiga
        if key == 'f5':
            if hasattr(self.game, 'player') and self.game.player and not self.game.player.is_dead:
                from enemy import EnemyShip
                import time
                sq_id = f"squad_{time.time()}"
                
                # Líder
                spawn_pos = self.game.player.position + self.game.player.forward * 100
                EnemyShip("nave-alien-enemy", spawn_pos, self.game, is_boss=False, is_leader=True, squadron_id=sq_id)
                # Escoltas
                EnemyShip("nave-alien-enemy", spawn_pos + self.game.player.right * 15 - self.game.player.forward * 15, self.game, is_boss=False, is_wingman=True, squadron_id=sq_id)
                EnemyShip("nave-alien-enemy", spawn_pos - self.game.player.right * 15 - self.game.player.forward * 15, self.game, is_boss=False, is_wingman=True, squadron_id=sq_id)
                print(f"Spawneado escuadrón Alien: {sq_id}")
        elif key == 'f6':
            if hasattr(self.game, 'player') and self.game.player and not self.game.player.is_dead:
                from enemy import EnemyShip
                import time
                sq_id = f"squad_{time.time()}"
                
                # Líder
                spawn_pos = self.game.player.position + self.game.player.forward * 100
                EnemyShip("nave-altech-enemy", spawn_pos, self.game, is_boss=False, is_leader=True, squadron_id=sq_id)
                # Escoltas
                EnemyShip("nave-altech-enemy", spawn_pos + self.game.player.right * 15 - self.game.player.forward * 15, self.game, is_boss=False, is_wingman=True, squadron_id=sq_id)
                EnemyShip("nave-altech-enemy", spawn_pos - self.game.player.right * 15 - self.game.player.forward * 15, self.game, is_boss=False, is_wingman=True, squadron_id=sq_id)
                print(f"Spawneado escuadrón Altech: {sq_id}")
        elif key == 'f7':
            if hasattr(self.game, 'player') and self.game.player and not self.game.player.is_dead:
                from enemy import EnemyShip
                spawn_pos = self.game.player.position + self.game.player.forward * 250
                EnemyShip("boss1-nodriza", spawn_pos, self.game, is_boss=True)
                print("Spawneado: boss1-nodriza")
        elif key == 'f8':
            if hasattr(self.game, 'player') and self.game.player and not self.game.player.is_dead:
                from enemy import EnemyShip
                spawn_pos = self.game.player.position + self.game.player.forward * 150
                EnemyShip("nave-exploradora", spawn_pos, self.game, is_npc=True)
                print("Spawneado: nave-exploradora (NPC)")
        
        # Solo registrar teclas si el alien no está desbloqueado
        if "nave-alien-enemy" not in AVAILABLE_SHIPS:
            if len(key) == 1 and key.isalpha():
                import time
                current_time = time.time()
                
                # Si pasa más de 1.5 segundos entre teclas, reiniciar el buffer
                if current_time - self.last_key_time > 1.5:
                    self.cheat_buffer = ""
                    
                self.last_key_time = current_time
                self.cheat_buffer += key.lower()
                
                if len(self.cheat_buffer) > 20:
                    self.cheat_buffer = self.cheat_buffer[-20:]
                    
                if "astra" in self.cheat_buffer:
                    self.cheat_buffer = "" # Limpiar tras activarse
                    if hasattr(self.game, 'unlock_alien_ship'):
                        self.game.unlock_alien_ship()
        
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
        
        self.environment = AsteroidManager(player=self.player, count=90, radius=1000, pool=self.pool)
        self.space_dust = SpaceDustManager(player=self.player, count=100, radius=80)
        self.intro_cinematic = IntroCinematic(self.player)
        
        from cinematics import PlanetAnalysisCinematic
        self.player.planet_cinematic = PlanetAnalysisCinematic(self.player)
        
        self.ship_tuner = ShipTuner(self.player)
        from missions import MissionManager
        self.mission_manager = MissionManager(player=self.player)
        self.player.mission_manager = self.mission_manager # Pasar referencia al jugador

        from ai_director import AIDirector
        self.ai_director = AIDirector(game_app=self)
        self.ai_director.enabled = False

        self.player.enabled = False
        
        # --- INITIALIZE AUDIO MANAGER ---
        from audio_manager import AudioManager
        self.audio_manager = AudioManager()
        self.audio_manager.play_menu_music()
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
        
        if hasattr(self, 'audio_manager'):
            self.audio_manager.stop_menu_music()
            self.audio_manager.play_ambient()
            
        # Aplicar ajustes gráficos
        window.vsync = GameSettings.vsync
        self.cosmic_bg.enabled = True
        self.cosmic_bg.set_quality(GameSettings.quality)
        
        if GameSettings.quality == 'Baja':
            self.environment.count = 60
            self.space_dust.count = 0
            self.space_dust.enabled = False
        else:
            self.environment.count = 150
            self.space_dust.count = 200
            self.space_dust.enabled = True
            self.space_dust.reset_particles()
            
        self.environment.clear_and_respawn()
        
        self.achievement_manager.reset_run()
        self.player.change_ship(ship_id)
        self.player.reset_ship()
        
        # NO encender el AI Director todavía, para que no salgan enemigos durante la cinemática
        self.ai_director.enabled = False
        
        # Iniciar Misiones (se resetan y quedan listas en Lote 0)
        self.mission_manager.reset()
        self.mission_manager.current_batch = 0
        # advance_batch() se llamará al terminar la cinemática
        
        self.mission_manager.ui.enable()
        self.mission_manager.waypoint.enable()
        
        # Reproducimos la cinemática inicial del juego
        # La cinemática misma se encarga de habilitar al jugador, posicionar la cámara y mostrar el HUD al finalizar.
        self.intro_cinematic.play()
        
        mouse.locked = True
            
        mouse.locked = True

    def intercept_buoy_data(self):
        # Desaparecer la boya físicamente
        if hasattr(self.mission_manager, 'altech_buoy') and self.mission_manager.altech_buoy:
            from ursina import destroy
            destroy(self.mission_manager.altech_buoy)
            self.mission_manager.altech_buoy = None
            
        self.mission_manager.complete_mission("main_02")
        if hasattr(self.player, 'ai_companion'):
            self.player.ai_companion.trigger_dialogue([
                ("IA: Conectando a los sistemas de la boya Altech...", 4.0),
                ("Tierra: Piloto, estamos recibiendo la transmisión. Desencriptando...", 4.5),
                ("Tierra: Dios mío... ¡Es tecnología terrestre! Altech es una corporación humana operando en las sombras.", 6.5),
                ("Tierra: Sus registros indican que han estado robando tecnología de una antigua civilización alienígena.", 6.5),
                ("IA: Datos extraídos con éxito. Nuestros sistemas de ingeniería se han actualizado.", 5.0),
                ("Tierra: Fabrica todo lo que puedas. Necesitaremos armas para lo que se avecina.", 5.5)
            ])

    def spawn_roaming_squad(self, target_pos):
        from cinematics import RoamingDummySquad
        # Detonamos la cinemática usando nuestra propia función cuando se acercan a 1500m
        self.roaming_squad = RoamingDummySquad(self.player, self, target_pos, self.start_altech_squad_cinematic)

    def start_altech_squad_cinematic(self):
        from cinematics import AltechSquadCinematic
        from ursina import scene, destroy
        
        # Pausar spawn de IA durante la cinemática
        if hasattr(self, 'ai_director'):
            self.ai_director.boss_fight_active = True
            
        # Limpiar enemigos actuales del mapa
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip' and getattr(e, 'faction', None) != 'npc':
                destroy(e)
                
        # Limpiar exceso de asteroides para rendimiento
        if hasattr(self, 'environment'):
            while len(self.environment.asteroids) > 30:
                ast = self.environment.asteroids.pop()
                destroy(ast)
                
        if not hasattr(self, 'altech_squad_cinematic'):
            self.altech_squad_cinematic = AltechSquadCinematic(self.player, self)
            
        self.altech_squad_cinematic.play()
        
    def spawn_altech_wreck(self, position):
        from ursina import Entity, color, Vec3
        from enemy_ships import ENEMY_SHIPS
        
        self.mission_manager.altech_wreck_spawned = True
        
        config = ENEMY_SHIPS.get("nave-altech-enemy")
        
        # El modelo representativo para la chatarra hackeable (oscurecido)
        self.altech_wreck = Entity(
            model=config.model if config else 'cube',
            color=color.rgba(40, 40, 40, 255),
            scale=config.scale if config else (20, 10, 20),
            position=position,
            rotation=Vec3(15, 45, 10),
            collider='box'
        )
        
        # Forzar al mission manager a apuntar a la chatarra
        tracked = self.mission_manager.get_tracked_mission()
        if tracked and tracked.id == "main_03":
            tracked.target_pos = self.altech_wreck.position
            tracked.description = "Hackea los restos de la nave líder Altech."
            tracked.short_description = "Acércate y pulsa X para hackear."
            
        if hasattr(self.player, 'ai_companion'):
            self.player.ai_companion.trigger_dialogue([
                ("IA: Amenaza neutralizada. Detecto un núcleo de datos intacto en los restos.", 4.5),
                ("Tierra: Acércate a los restos de esa nave y hackéala. Necesitamos saber qué planean.", 5.5)
            ])
            
    def hack_altech_wreck(self):
        self.mission_manager.altech_wreck_hacked = True
        if hasattr(self, 'altech_wreck') and self.altech_wreck:
            from ursina import destroy
            destroy(self.altech_wreck)
            self.altech_wreck = None
            
        # Al hackear, completamos el objetivo principal del Lote 3
        self.mission_manager.complete_mission("main_03")
        
        if hasattr(self.player, 'ai_companion'):
            self.player.ai_companion.trigger_dialogue([
                ("IA: Descargando base de datos táctica de Altech...", 4.0),
                ("Tierra: Excelente. Ahora termina las misiones pendientes.", 4.5),
            ])
            
    def start_boss_cinematic(self):
        from cinematics import BossIntroCinematic
        from ursina import scene, destroy
        
        if not hasattr(self, 'boss_cinematic'):
            self.boss_cinematic = BossIntroCinematic(self.player, self)
        
        # Pausar spawn de IA y limitar al máximo a 10 naves activas
        self.ai_director.boss_fight_active = True
        self.ai_director.max_ships = 10
        
        # Reducir asteroides
        if hasattr(self, 'environment'):
            # Eliminamos un montón de asteroides para que no haya tantos (los limitamos a 40)
            while len(self.environment.asteroids) > 40:
                ast = self.environment.asteroids.pop()
                destroy(ast)
        
        # Limpiar enemigos lejanos o todos para dar paso al jefe
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip':
                destroy(e)
                
        self.boss_cinematic.play()

    def start_ending_cinematic(self):
        from ending_cinematic import EndingCinematic
        from ursina import scene, destroy
        
        # Limpiar enemigos restantes
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip':
                destroy(e)
                
        if not hasattr(self, 'ending_cinematic'):
            self.ending_cinematic = EndingCinematic(self.player, self)
            
        self.ending_cinematic.play()

    def return_to_main_menu(self):
        if hasattr(self, 'audio_manager'):
            self.audio_manager.stop_ambient()
            self.audio_manager.play_menu_music()
            
        self.intro_cinematic.stop_and_clear()
        self.mission_manager.ui.disable()
        self.mission_manager.waypoint.disable()
        
        # Reiniciar misiones para que vuelvan al estado original al volver a jugar
        self.mission_manager.reset()
        self.mission_manager.current_batch = 0
        
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
        self.ai_director.enabled = False
        self.environment.clear_asteroids()
        
        # Limpiar enemigos que hayan quedado
        from ursina import scene, destroy
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip':
                destroy(e)

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
            
        # Reiniciar misiones por completo y reactivarlas (ya que la intro no se repite al revivir)
        self.mission_manager.reset()
        self.mission_manager.current_batch = 0
        self.mission_manager.advance_batch()
            
        self.achievement_manager.reset_run()
        self.player.reset_ship()
        self.environment.clear_and_respawn()
        
        # Limpiar enemigos antes de reiniciar
        from ursina import scene, destroy
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip':
                destroy(e)
                
        self.space_dust.reset_particles()
        self.game_over_menu.enabled = False

        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        mouse.locked = True
        application.paused = False
            
    def unlock_alien_ship(self):
        from ships import AVAILABLE_SHIPS
        if "nave-alien-enemy" not in AVAILABLE_SHIPS:
            try:
                from enemy_ships import ENEMY_SHIPS
                AVAILABLE_SHIPS["nave-alien-enemy"] = ENEMY_SHIPS["nave-alien-enemy"]
                # Actualizar el menú si está inicializado
                if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'ship_menu'):
                    self.main_menu.ship_menu.ship_keys = list(AVAILABLE_SHIPS.keys())
                    self.main_menu.ship_menu.update_ui()
                    
                # Notificación visual y sonido
                t = Text(parent=camera.ui, text="<cyan>¡CAZA ALIENÍGENA DESBLOQUEADO!", position=(0, 0.4), origin=(0, 0), scale=2.5, z=-10)
                destroy(t, delay=3)
            except ImportError:
                pass

    def run(self):
        self.app.run()


if __name__ == '__main__':
    game = GameApp()
    game.run()