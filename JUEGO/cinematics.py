from ursina import *
import random
import math
from ships import AVAILABLE_SHIPS
from enemy_ships import ENEMY_SHIPS

class DummyActor(Entity):
    """
    Doble de acción puramente visual para cinemáticas. 
    Carga el modelo, escala y postquemadores pero no tiene colisiones ni IA.
    """
    def __init__(self, config_id, **kwargs):
        super().__init__(**kwargs)
        self.config_id = config_id
        
        # Intentar cargar la config
        self.config = ENEMY_SHIPS.get(config_id)
        if not self.config:
            self.config = AVAILABLE_SHIPS.get(config_id)
            
        if not self.config:
            print(f"Error: Dummy config {config_id} not found!")
            return
            
        self.visual = Entity(parent=self, model=self.config.model, scale=self.config.scale, rotation=getattr(self.config, 'model_rotation_offset', (0,0,0)))
        
        self.thrusters = []
        self._setup_thrusters()
        
    def _setup_thrusters(self):
        for offset in self.config.thruster_offsets:
            t_scale = self.config.thruster_scale
            scaled_offset = (offset[0] * self.config.scale[0], offset[1] * self.config.scale[1], offset[2] * self.config.scale[2])
            t = Entity(parent=self, model='sphere', unlit=True, color=self.config.thruster_color,
                       scale=(t_scale[0], t_scale[1], t_scale[2]),
                       position=scaled_offset)
            self.thrusters.append(t)
            
    def update(self):
        # Animación básica de los propulsores
        if hasattr(self, 'config'):
            for t in self.thrusters:
                # Variar levemente el tamaño para dar efecto de fuego
                t.scale_z = self.config.thruster_scale[2] * random.uniform(0.9, 1.2)
                
            # Partículas (estela) de los postquemadores
            if random.random() < 0.6: # Frecuencia de partículas
                base_color = self.config.thruster_color
                trail_color = color.rgba(base_color.r * 255, base_color.g * 255, base_color.b * 255, 120)
                for offset in self.config.thruster_offsets:
                    scaled_offset = (offset[0] * self.config.scale[0], offset[1] * self.config.scale[1], offset[2] * self.config.scale[2])
                    
                    # Calcular posición real basándose en rotación local (forward/right/up)
                    spawn_pos = self.world_position + self.forward * scaled_offset[2] + self.right * scaled_offset[0] + self.up * scaled_offset[1]
                    
                    p = Entity(parent=scene, model='sphere', color=trail_color, unlit=True,
                               scale=random.uniform(0.06, 0.12) * self.config.scale[0], 
                               position=spawn_pos)
                    # Se mueve en sentido opuesto al avance
                    p.animate_position(p.position + (-self.forward * 4.0), duration=0.3, curve=curve.linear)
                    p.animate_scale(0, duration=0.3, curve=curve.linear)
                    destroy(p, delay=0.3)

class IntroCinematic(Entity):
    """Director de Fotografía: Cinemática blindada con Control de Sesiones"""

    def __init__(self, player, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.is_playing = False
        self.session_id = 0  # Identificador único por cada vez que juegas
        self.camera_shake = 0.0
        self.base_cam_pos = Vec3(0, 0, 0)

        # 1. FORMATO CINEMATOGRÁFICO
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44),
                              enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15),
                                 position=(0, -0.44), enabled=False, z=-5)

        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.44), scale=1.3,
                             color=color.white, enabled=False, z=-6)

        self.skip_btn = Button(parent=camera.ui, text='OMITIR [ENTER]', scale=(0.18, 0.05), position=(window.right.x - 0.12, -0.44), 
                               color=color.rgba(0, 0, 0, 180), highlight_color=color.rgba(50, 50, 50, 200), text_color=color.gray, enabled=False, z=-6)
        self.skip_btn.on_click = self.skip_cinematic

        # 2. ACTOR DOBLE (DUMMY)
        # Lo configuraremos en play() en base al ship_id del player
        from menu import MenuDummyShip
        self.dummy_ship = MenuDummyShip(enabled=False)
        
        # 3. PORTAL HEXAGONAL
        self.portal = Entity(model=Cylinder(resolution=6), color=color.rgba(0, 255, 255, 180), scale=(0, 0.01, 0),
                             rotation_x=90, unlit=True, enabled=False)
        self.portal_inner = Entity(parent=self.portal, model=Cylinder(resolution=6), color=color.white,
                                   scale=(0.8, 1.1, 0.8), unlit=True)

    def play(self):
        self.session_id += 1  # Al iniciar, creamos un nuevo ID
        sid = self.session_id  # Guardamos el ID de esta partida en específico

        self.is_playing = True
        self.player.is_cinematic = True

        self.player.enabled = False
        self.player.hud_container.disable()

        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        
        # Configurar el Dummy en base al Player
        config = AVAILABLE_SHIPS.get(self.player.ship_id, AVAILABLE_SHIPS["nave1"])
        self.current_config = config
        self.dummy_ship.set_config(config)
            
        self.dummy_ship.enabled = True
        self.portal.enabled = True
        self.skip_btn.enabled = True

        # Pasamos el 'sid' a todas las llamadas futuras para validar la sesión
        self.execute_shot_1(sid)
        invoke(self.execute_shot_2, sid, delay=2.8)
        invoke(self.execute_shot_3, sid, delay=6.0)
        invoke(self.execute_shot_4, sid, delay=8.5)
        invoke(self.execute_shot_5, sid, delay=11.0)
        invoke(self.end_cinematic, sid, delay=16.5)

    def execute_shot_1(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.portal.position = (0, 0, -200)
        self.portal.scale = (0, 0.01, 0)
        self.portal.animate_scale(Vec3(35, 0.01, 35), duration=0.8, curve=curve.out_back)

        self.dummy_ship.enabled = True
        self.dummy_ship.scale = self.current_config.dummy_config.scale_large
        self.dummy_ship.position = (0, 0, -260)
        self.dummy_ship.rotation = (0, 0, 0)

        camera.parent = scene
        self.base_cam_pos = Vec3(3, -1.5, -165)
        camera.position = self.base_cam_pos
        camera.look_at((0, 0, -200))
        camera.fov = 70

        self.subtitle.text = "[SISTEMA]: Núcleo cuántico activado. Abriendo horizonte de sucesos..."
        invoke(self.dummy_ship.animate_position, (0, 0, -150), duration=2.3, curve=curve.in_out_expo, delay=0.4)

    def execute_shot_2(self, sid):
        """PLANO 2: Chase Cam en Ángulo Holandés (Persecución a alta velocidad)"""
        if sid != self.session_id or not self.is_playing: return

        # La nave arranca un poco más atrás
        self.dummy_ship.position = (0, 0, -160)

        # Nos colocamos detrás y a la derecha de la nave.
        # Al hacer a la cámara hija de la nave, evitamos cualquier jitter/lag por el orden de actualización del motor.
        camera.parent = self.dummy_ship
        # La posición relativa de (6, 1.5, -175) respecto a (0, 0, -160) es (6, 1.5, -15)
        self.base_cam_pos = Vec3(6, 1.5, -15)
        camera.position = self.base_cam_pos

        # Miramos hacia la nave, pero le metemos una inclinación de -15 grados (Dutch Angle)
        camera.look_at(self.dummy_ship)
        camera.rotation_z = -15
        camera.fov = 65

        self.subtitle.text = "[SISTEMA]: Estabilizando campos de inercia espacial..."

        # Solo animamos la nave, la cámara viajará con ella perfectamente estática en su posición relativa.
        self.dummy_ship.animate_position((0, 0, -40), duration=3.0, curve=curve.linear)

    def execute_shot_3(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.dummy_ship.scale = self.current_config.dummy_config.scale_normal
        self.dummy_ship.position = (0, 0, -115)
        self.dummy_ship.rotation = (0, 0, 0)

        # Desvinculamos la cámara de la nave
        camera.parent = scene
        self.base_cam_pos = Vec3(18, 4, -40)
        camera.position = self.base_cam_pos
        camera.rotation = (10, -60, 0)
        camera.fov = 70

        self.subtitle.text = "[PILOTO]: Atravesando cuadrante ciego. Compresión de espacio-tiempo al 92%."
        self.dummy_ship.animate_position((0, 0, -10), duration=2.5, curve=curve.linear)

    def execute_shot_4(self, sid):
        """PLANO 4: Llegada y frenazo - Vista frontal dramática con portal distante"""
        if sid != self.session_id or not self.is_playing: return

        self.portal.enabled = True
        self.portal.position = (0, 0, -150)
        self.portal.scale = Vec3(35, 0.01, 35)
        self.portal_inner.color = color.white

        self.dummy_ship.position = (0, 0, -145)

        self.base_cam_pos = Vec3(0, 2.5, 20)
        camera.position = self.base_cam_pos
        camera.rotation = (8, 180, 0)
        camera.fov = 60

        self.subtitle.text = "[SISTEMA]: Destino alcanzado. Aplicando contrapeso y frenos magnéticos."

        self.dummy_ship.animate_position((0, 0, 0), duration=1.5, curve=curve.out_expo)

        invoke(self.slam_brakes, sid, delay=1.2)

    def slam_brakes(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.camera_shake = 1.9
        self.portal.animate_scale(Vec3(0, 0.01, 0), duration=0.4, curve=curve.in_back)

    def execute_shot_5(self, sid):
        if sid != self.session_id or not self.is_playing: return

        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False

        self.dummy_ship.enabled = False
        self.portal.enabled = False
        self.skip_btn.enabled = False

        self.player.position = (0, 0, 0)
        self.player.rotation = (0, 0, 0)
        self.player.enabled = True
        self.player.is_cinematic = True

        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.world_rotation = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = self.player.base_fov

        self.cinematic_scan(sid)

    def cinematic_scan(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.cine_text.text = 'ESTAMOS A 4.2 AÑOS LUZ DE LA TIERRA...\nCONSIGUE MINERALES Y DESTRUYE TODO LO QUE VEAS'
        self.player.cine_text.enabled = True
        self.player.cine_text.color = color.rgba(255, 255, 255, 0)
        self.player.cine_text.animate_color(color.white, duration=0.5)

        self.player.animate('rotation_y', 20, duration=0.6, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', -20, delay=0.7, duration=1.2, curve=curve.in_out_sine)
        invoke(self.player.animate, 'rotation_y', 0, delay=2.0, duration=0.6, curve=curve.in_out_sine)

    def end_cinematic(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.cine_text.animate_color(color.rgba(255, 255, 255, 0), duration=1.0)
        invoke(self.give_control, sid, delay=1.0)

    def give_control(self, sid):
        if sid != self.session_id or not self.is_playing: return
        self.player.is_cinematic = False
        self.player.cine_text.enabled = False
        self.player.hud_container.enable()
        self.is_playing = False

        if hasattr(self.player, 'scanner') and self.player.scanner:
            self.player.scanner.toggle()
            
        # Al terminar la cinemática, ENCENDEMOS el motor de juego
        if hasattr(self.player, 'game_app'):
            app = self.player.game_app
            if hasattr(app, 'ai_director'):
                app.ai_director.enabled = True
                app.ai_director.spawn_timer = 5.0 # Retardo inicial de enemigos
                
            if hasattr(app, 'mission_manager'):
                app.mission_manager.advance_batch()

    def stop_and_clear(self):
        """Bloquea los invokes y apaga por completo las capas UI para no contaminar el menú"""
        self.session_id += 1  # Al sumar 1, todos los invokes pendientes de la sesión anterior mueren automáticamente.

        self.is_playing = False
        self.dummy_ship.enabled = False
        self.portal.enabled = False
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.skip_btn.enabled = False
        self.player.is_cinematic = False

    def skip_cinematic(self):
        if not self.is_playing: return
        self.session_id += 1  # Cancela todo invoke pendiente
        
        self.is_playing = False
        self.dummy_ship.enabled = False
        self.portal.enabled = False
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.skip_btn.enabled = False
        
        self.player.position = (0, 0, 0)
        self.player.rotation = (0, 0, 0)
        self.player.enabled = True
        self.player.hud_container.enable()
        self.player.is_cinematic = False
        
        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.world_rotation = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = self.player.base_fov
        
        self.player.cine_text.enabled = False
        
        if hasattr(self.player, 'scanner') and self.player.scanner:
            self.player.scanner.toggle()
            
        # ENCENDEMOS el motor de juego si se omite la cinemática
        if hasattr(self.player, 'game_app'):
            app = self.player.game_app
            if hasattr(app, 'ai_director'):
                app.ai_director.enabled = True
                app.ai_director.spawn_timer = 5.0
                
            if hasattr(app, 'mission_manager'):
                app.mission_manager.advance_batch()

    def update(self):
        if self.is_playing and held_keys['enter']:
            self.skip_cinematic()

        if not self.is_playing: return

        if self.portal.enabled and self.portal.scale_x > 0:
            self.portal.rotation_y += 140 * time.dt
            self.portal_inner.rotation_y -= 280 * time.dt

        if self.dummy_ship.enabled:
            if random.random() < 0.6:
                from player import SpeedLine
                SpeedLine()

        if self.camera_shake > 0:
            self.camera_shake -= time.dt * 6.0
            self.camera_shake = max(0.0, self.camera_shake)
            if camera.parent == scene:
                camera.x = self.base_cam_pos.x + random.uniform(-self.camera_shake, self.camera_shake)
                camera.y = self.base_cam_pos.y + random.uniform(-self.camera_shake, self.camera_shake)

class PlanetAnalysisCinematic(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.is_playing = False
        self.session_id = 0
        self.target_pos = Vec3(291, 950, 2193)

        # UI Cinematográfica
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44), enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, -0.44), enabled=False, z=-5)
        self.subtitle = Text(parent=camera.ui, text=' ', origin=(0, 0), position=(0, -0.44), scale=0.9, color=color.white, enabled=False, z=-6)
        self.subtitle.wordwrap = 75
        self.subtitle.text = ''
        
        # Elementos de animación de análisis
        self.scan_beams = []

    def play(self):
        if self.is_playing: return
        self.session_id += 1
        sid = self.session_id
        self.is_playing = True
        
        self.player.is_cinematic = True
        self.player.hud_container.disable()
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.disable()
            self.player.mission_manager.waypoint.disable()
            
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = False

        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True

        self.execute_shot_1(sid)
        invoke(self.execute_shot_2, sid, delay=6.5)
        invoke(self.execute_shot_3, sid, delay=13.0)
        invoke(self.execute_shot_4, sid, delay=21.0)
        invoke(self.end_cinematic, sid, delay=29.0)

    def execute_shot_1(self, sid):
        if sid != self.session_id: return
        camera.parent = scene
        # Paneo lento de la cima del planeta (enfocando hacia el centro del planeta real)
        planet_center = Vec3(300, 200, 2200)
        start_pos = self.target_pos + Vec3(0, 300, -800)
        camera.position = start_pos
        camera.look_at(planet_center)
        camera.animate_position(self.target_pos + Vec3(300, 100, -500), duration=6.5, curve=curve.linear)
        
        self.subtitle.text = "<cyan>[SISTEMA IA]:<default>\nAnalizando superficie...\nDetecto anomalías gravitacionales extremas\nen el núcleo expuesto del planeta."

    def execute_shot_2(self, sid):
        if sid != self.session_id: return
        planet_center = Vec3(300, 200, 2200)
        start_pos = self.target_pos + Vec3(-600, 200, 300)
        camera.position = start_pos
        camera.look_at(planet_center)
        camera.animate_position(self.target_pos + Vec3(-200, 50, 500), duration=6.5, curve=curve.linear)
        self.subtitle.text = "<orange>[COMANDO TIERRA]:<default>\nPiloto, ¿me recibe? Las lecturas indican que\neste planeta no fue destruido por causas naturales.\nFue... minado desde adentro."

    def execute_shot_3(self, sid):
        if sid != self.session_id: return
        planet_center = Vec3(300, 200, 2200)
        start_pos = self.target_pos + Vec3(300, 600, 300)
        camera.position = start_pos
        camera.look_at(planet_center) # Mirando profundamente hacia el núcleo
        camera.animate_position(self.target_pos + Vec3(0, 1000, 0), duration=8.0, curve=curve.linear)
        self.subtitle.text = "<cyan>[SISTEMA IA]:<default>\nLas fisuras coinciden con armamento clase Omega.\nLa alta densidad de asteroides en el sector es,\nde hecho, la corteza triturada de este mundo."

    def execute_shot_4(self, sid):
        if sid != self.session_id: return
        # Plano dramático de frente a la nave (close-up)
        start_pos = self.player.position + self.player.forward * 35 + self.player.up * 8
        camera.position = start_pos
        camera.look_at(self.player.position + self.player.up * 3)
        camera.animate_position(self.player.position + self.player.forward * 18 + self.player.up * 4, duration=8.0, curve=curve.linear)
        self.subtitle.text = "<orange>[COMANDO TIERRA]:<default>\nEntendido. Descargue los datos estructurales\nrestantes; esa información vale oro.\nManténgase alerta, no estamos solos."

    def end_cinematic(self, sid):
        if sid != self.session_id: return
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.subtitle.text = ''
        
        self.is_playing = False
        self.player.is_cinematic = False
        self.player.hud_container.enable()
        
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = True
        
        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.complete_mission("main_01")
            self.player.mission_manager.ui.enable()
            self.player.mission_manager.waypoint.enable()

class BossIntroCinematic(Entity):
    def __init__(self, player, game_app, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.game = game_app
        self.is_playing = False
        self.session_id = 0
        
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44), enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, -0.44), enabled=False, z=-5)
        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.44), scale=1.3, color=color.white, enabled=False, z=-6)
        
        # 3. PORTAL HEXAGONAL (igual al del inicio pero gigante y rojo)
        self.portal = Entity(model=Cylinder(resolution=6), color=color.rgba(255, 50, 0, 180), scale=(0, 0.01, 0),
                             rotation_x=90, unlit=True, enabled=False)
        self.portal_inner = Entity(parent=self.portal, model=Cylinder(resolution=6), color=color.white,
                                   scale=(0.8, 1.1, 0.8), unlit=True)
        
        self.escorts = []
        self.mothership = None

    def play(self):
        if self.is_playing: return
        self.session_id += 1
        sid = self.session_id
        self.is_playing = True
        
        self.player.is_cinematic = True
        self.player.hud_container.disable()
        
        # Ocultar jugador por completo
        self.player.enabled = False
        
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.disable()
            self.player.mission_manager.waypoint.disable()
            
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = False

        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        
        self.portal.enabled = True
        
        # Tiempos de las 4 tomas (total 18 segundos)
        self.execute_shot_1(sid)
        invoke(self.execute_shot_2, sid, delay=4.5)
        invoke(self.execute_shot_3, sid, delay=9.0)
        invoke(self.execute_shot_4, sid, delay=13.5)
        invoke(self.end_cinematic, sid, delay=18.0)

    def execute_shot_1(self, sid):
        if sid != self.session_id: return
        camera.parent = scene
        
        if self.mothership:
            destroy(self.mothership)
        for e in self.escorts:
            destroy(e)
        self.escorts = []
        
        # Usaremos los vectores del player como referencia constante
        forward = self.player.forward
        up = self.player.up
        right = self.player.right
        
        # Posición del portal alejada a 1000 metros de distancia para dar espacio en la pelea
        self.portal_pos = self.player.position + forward * 1000
        
        self.portal.position = self.portal_pos
        self.portal.look_at(self.player.position)
        self.portal.rotation_x -= 90 
        self.portal.scale = (0, 0.01, 0)
        
        # Animación de apertura retrasada 2 segundos.
        invoke(self.portal.animate_scale, Vec3(400, 0.01, 400), duration=1.5, curve=curve.out_back, delay=2.0)
        
        # SHOT 1: Cámara viendo hacia la nada
        camera.position = self.player.position + up * 60 - right * 30
        camera.look_at(self.portal_pos + up * 30)
        
        # SHAKE: Temblores violentos antes de abrir el portal
        import random
        def shake():
            if self.current_shot == 1 and self.is_playing:
                if hasattr(self, 'shake_timer'):
                    self.shake_timer += 0.05
                    if self.shake_timer < 2.0:
                        camera.x += random.uniform(-2.0, 2.0)
                        camera.y += random.uniform(-2.0, 2.0)
                invoke(shake, delay=0.05)
        self.current_shot = 1
        self.shake_timer = 0
        shake()
        
        # Generar Nodriza justo detrás del portal para que pase rápidamente a través de él
        self.mothership = DummyActor("boss1-nodriza", position=self.portal_pos + forward * 300)
        self.mothership.scale = (3, 3, 3)
        self.mothership.enabled = False 
        
        self.mothership.look_at(self.player.position)
        self.mothership.rotation_x = 0
        self.mothership.rotation_z = 0
        
        def spawn_mothership():
            if not self.is_playing or self.session_id != sid: return
            self.mothership.enabled = True
            # Se mueve rápidamente desde atrás para atravesar el portal visiblemente en el Shot 2
            self.mothership.animate_position(self.portal_pos - forward * 300, duration=10.0, curve=curve.linear)
            
        invoke(spawn_mothership, delay=2.5)
        
        self.subtitle.text = "<cyan>[IA DE LA NAVE]:<default>\n¡Alerta Crítica! Ruptura masiva del espacio-tiempo detectada."

    def execute_shot_2(self, sid):
        if sid != self.session_id: return
        self.current_shot = 2
        
        forward = self.player.forward
        up = self.player.up
        right = self.player.right
        
        # SHOT 2: Cámara frente al portal, mirando a la Nodriza emerger hacia nosotros.
        camera.position = self.portal_pos - forward * 200 + up * 80 + right * 80
        camera.look_at(self.portal_pos + up * 50)
        
        camera.animate_position(camera.position - right * 60, duration=4.5, curve=curve.linear)
        
        # Cierre del portal: Lo cerramos justo antes de que termine el shot 2 (a los 3.5s de iniciar el shot 2)
        # para asegurar que la nave ya ha salido casi por completo.
        self.portal.animate_scale((0, 0.01, 0), duration=1.0, curve=curve.in_expo, delay=3.0)
        
        self.subtitle.text = "<orange>[COMANDO TIERRA]:<default>\n¡El tamaño de esa nave... están enviando a su Nodriza!"

    def execute_shot_3(self, sid):
        if sid != self.session_id: return
        self.current_shot = 3
        
        forward = self.player.forward
        up = self.player.up
        right = self.player.right
        
        # SHOT 3: Cámara MÁS CERCA viendo el perfil de la Nodriza.
        # Usamos una función de rastreo dinámico para que la cámara acompañe a la Nodriza
        # y no se quede viendo a la nada mientras ésta avanza.
        self.shot_3_offset = - forward * 50 + up * 80 - right * 150
        
        def track_mothership():
            if self.current_shot == 3 and self.is_playing and self.mothership:
                # Movimiento Dolly relativo a la nave (avanza 100 unidades en 4.5s)
                self.shot_3_offset += forward * (100 * 0.02 / 4.5)
                camera.position = self.mothership.position + self.shot_3_offset
                camera.look_at(self.mothership.position + forward * 30)
                invoke(track_mothership, delay=0.02)
                
        track_mothership()
        
        # Llegan 8 cazas Altech (Dummys)
        import math
        for i in range(8):
            angle = (i / 8) * math.tau
            # Reducido el radio de la formación para que estén más pegadas
            radius = 120 
            
            spawn_pos = self.mothership.position + right * random.choice([-500, 500]) + up * random.uniform(50, 200)
            
            e = DummyActor("nave-altech-enemy", position=spawn_pos)
            e.look_at(self.mothership.position)
            
            # Posición destino: Anillo defensivo MUY PEGADO a la Nodriza
            target_pos = self.mothership.position - forward * 100 + right * math.cos(angle) * radius + up * math.sin(angle) * radius
            
            e.animate_position(target_pos, duration=2.5, curve=curve.out_expo)
            
            def face_player(entity=e):
                if entity:
                    entity.look_at(self.player.position)
                    entity.rotation_x = 0
                    entity.rotation_z = 0
            
            invoke(face_player, delay=2.5)
            
            invoke(e.animate_position, target_pos - forward * 60, duration=6.0, curve=curve.linear, delay=2.5)
            
            self.escorts.append(e)
            
        self.subtitle.text = "<red>[LÍDER ALTECH]:<default>\nNodriza desplegada. Escuadrón, adopten formación defensiva."

    def execute_shot_4(self, sid):
        if sid != self.session_id: return
        self.current_shot = 4
        
        forward = self.player.forward
        up = self.player.up
        right = self.player.right
        
        # SHOT 4: Ver al batallón, pero cámara un poco MÁS CERCA
        camera.position = self.player.position + up * 60 + right * 10 - forward * 20
        camera.look_at(self.mothership.position + up * 50)
        camera.fov = 65 
        
        camera.animate_position(camera.position + up * 20 - forward * 40, duration=4.5, curve=curve.linear)
        
        self.subtitle.text = "<cyan>[IA DE LA NAVE]:<default>\n¡Flota enemiga detectada! Es ahora o nunca, piloto."

    def end_cinematic(self, sid):
        if sid != self.session_id: return
        self.current_shot = 0
        camera.fov = 60 # Restaurar FOV normal
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.subtitle.text = ''
        
        self.portal.enabled = False
        
        # Matamos cualquier animación previa de la cámara
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
                
        # CAMBIAZO: Destruir Dummys e instanciar Nodriza y Escoltas IA Reales
        from enemy import Mothership, EnemyShip
        
        if self.mothership:
            m_pos = self.mothership.world_position
            m_rot = self.mothership.rotation
            destroy(self.mothership)
            real_m = Mothership(m_pos, self.game)
            real_m.rotation = m_rot
            
        for d in self.escorts:
            pos = d.world_position
            rot = d.rotation
            destroy(d)
            # Instanciar como minions. Usamos "nave-altech-enemy"
            real_e = EnemyShip("nave-altech-enemy", pos, self.game, is_minion=True, force_detection=True)
            real_e.rotation = rot
            # Disminuir su agresividad inicial para dar respiro al jugador
            real_e.fire_cooldown = 8.0 
            
        self.escorts.clear()
        
        self.is_playing = False
        self.player.is_cinematic = False
        self.player.enabled = True
        self.player.hud_container.enable()
        
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = True
        
        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.enable()
            self.player.mission_manager.waypoint.enable()
            
            # Marcar que el boss ya apareció (evita dobles spawns)
            self.player.mission_manager.waiting_for_boss = False
            self.player.mission_manager.boss_spawned = True
            
            # Limpiar waypoint si existía
            tracked = self.player.mission_manager.get_tracked_mission()
            if tracked and tracked.id == "main_03":
                tracked.target_pos = None

class RoamingDummySquad(Entity):
    def __init__(self, player, game_app, target_pos, trigger_callback, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.game = game_app
        self.target_pos = target_pos
        self.trigger_callback = trigger_callback
        
        self.squad = []
        
        # Formación ^ (Punta de flecha hacia -Z)
        offsets = [
            Vec3(0, 0, 0),        # 0: Líder
            Vec3(-25, 0, 30),     # 1: Izq 1
            Vec3(25, 0, 30),      # 2: Der 1
            Vec3(-50, 0, 60),     # 3: Izq 2
            Vec3(50, 0, 60),      # 4: Der 2
            Vec3(-75, 0, 90),     # 5: Izq 3
            Vec3(75, 0, 90),      # 6: Der 3
            Vec3(0, 20, 45),      # 7: Escolta superior central
        ]
        
        # El pivot es el Squad. Posición global: target_pos
        self.position = target_pos
        
        for i, offset in enumerate(offsets):
            d = DummyActor("nave-altech-enemy", parent=self, position=offset)
            d.rotation = (0, 180, 0)
            self.squad.append(d)
            
        # Animamos el escuadrón avanzando muy lentamente hacia -Z (hacia donde miran)
        self.animate_position(self.position - Vec3(0,0,1000), duration=100.0, curve=curve.linear)

    def update(self):
        if not hasattr(self, 'player') or not getattr(self.player, 'enabled', True): return
        
        # Verificar distancia al jugador
        dist = distance(self.world_position, self.player.world_position)
        if dist < 1500:
            if self.trigger_callback:
                self.trigger_callback()
            
            # Autodestrucción ya que la cinemática toma el control con sus propios Dummys
            for d in self.squad:
                destroy(d)
            destroy(self)

class AltechSquadCinematic(Entity):
    def __init__(self, player, game_app, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.game = game_app
        self.is_playing = False
        self.session_id = 0
        
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44), enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, -0.44), enabled=False, z=-5)
        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.44), scale=1.3, color=color.white, enabled=False, z=-6)
        
        self.target_pos = Vec3(3000, 500, 4000)
        self.squad = []

    def play(self):
        if self.is_playing: return
        self.session_id += 1
        sid = self.session_id
        self.is_playing = True
        
        self.player.is_cinematic = True
        self.player.hud_container.disable()
        
        # OCULTAR AL JUGADOR REAL POR COMPLETO DURANTE LA CINEMÁTICA
        self.player.enabled = False
        
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.disable()
            self.player.mission_manager.waypoint.disable()
            
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = False

        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        
        self.current_shot = 1
        self.execute_shot_1(sid)
        invoke(self.execute_shot_2, sid, delay=5.0)
        invoke(self.execute_shot_3, sid, delay=10.0)
        invoke(self.execute_shot_4, sid, delay=14.0)
        invoke(self.end_cinematic, sid, delay=18.0)

    def update(self):
        if not self.is_playing: return
        # Ya no usaremos tracking dinámico con look_at en el update para evitar inclinar la cámara.
        pass

    def execute_shot_1(self, sid):
        if sid != self.session_id: return
        camera.parent = scene
        
        # Limpieza de Dummys viejos por si se repite la cinemática
        if hasattr(self, 'squad'):
            for old_d in self.squad:
                destroy(old_d)
        
        self.player.position = self.target_pos - Vec3(0, 0, 1000)
        self.player.look_at(self.target_pos)
        
        # Generar las 8 naves Altech como Dummys (dobles de acción)
        self.squad = []
        
        # Formación ^ (Punta de flecha muy organizada).
        # Líder al frente (Z=0). Ala izquierda (-X, +Z), Ala derecha (+X, +Z)
        offsets = [
            Vec3(0, 0, 0),        # 0: Líder
            Vec3(-25, 0, 30),     # 1: Izq 1
            Vec3(25, 0, 30),      # 2: Der 1
            Vec3(-50, 0, 60),     # 3: Izq 2
            Vec3(50, 0, 60),      # 4: Der 2
            Vec3(-75, 0, 90),     # 5: Izq 3
            Vec3(75, 0, 90),      # 6: Der 3
            Vec3(0, 20, 45),      # 7: Escolta superior central
        ]
        
        for i, offset in enumerate(offsets):
            pos = self.target_pos + offset
            d = DummyActor("nave-altech-enemy", position=pos)
            # Rotación fija de 180 grados en Y para mirar hacia -Z
            d.rotation = (0, 180, 0)
            self.squad.append(d)
            
        # SHOT 1 (0-5s): Plano General Frontal
        # Nos ponemos frente a ellos (hacia -Z) y arriba.
        camera.position = self.target_pos + Vec3(0, 80, -250)
        camera.look_at(self.target_pos)
        # Dolly in frontal
        camera.animate_position(self.target_pos + Vec3(0, 40, -120), duration=5.0, curve=curve.linear)
        
        self.subtitle.text = "<cyan>[IA DE LA NAVE]:<default>\nLlegando a coordenadas. Múltiples contactos de la corporación Altech detectados en formación de ataque."
        
        # Animamos todo el escuadrón desde el inicio para que estén en movimiento real
        for d in self.squad:
            d.animate_position(d.position - Vec3(0, 0, 400), duration=20.0, curve=curve.linear)

    def execute_shot_2(self, sid):
        if sid != self.session_id: return
        self.current_shot = 2
        
        # Matamos cualquier animación previa de la cámara para que no interfiera
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
        
        # SHOT 2 (antiguo Shot 3) (5-10s): Plano contrapicado dramático desde abajo
        if len(self.squad) > 0:
            leader = self.squad[0]
            camera.parent = leader
            # Local: Abajo (-Y), a la izquierda (-X) y un poco al frente (+Z)
            camera.position = Vec3(-20, -15, 30)
            # Miramos hacia el líder
            camera.look_at(leader)
            
            # La cámara desciende y se aleja muy lentamente
            camera.animate_position(Vec3(-30, -25, 10), duration=5.0, curve=curve.linear)
            
        self.subtitle.text = "<orange>[COMANDO TIERRA]:<default>\nEse caza central emite firmas térmicas anómalas. Es el líder del escuadrón, no lo pierdas de vista."

    def execute_shot_3(self, sid):
        if sid != self.session_id: return
        self.current_shot = 3
        
        # Matamos cualquier animación previa de la cámara
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
        
        # SHOT 3 (10-14s): El jugador entra en escena pero de forma paralela, sin chocar
        if len(self.squad) > 0:
            leader = self.squad[0]
            
            # (El jugador real ya fue desactivado en play())
            
            # Creamos el Dummy
            ship_id = getattr(self.player, 'ship_id', 'nave1')
            self.player_dummy = DummyActor(ship_id, parent=scene)
            
            # Detectamos desde dónde viene el jugador
            direction_to_leader = (leader.world_position - self.player.world_position).normalized()
            if direction_to_leader.length() < 0.1: 
                direction_to_leader = Vec3(0, 0, -1)
                
            # Calculamos un vector hacia la derecha para hacer un desplazamiento (offset)
            # de esa forma el jugador vuela a un lado del escuadrón y no pasa por encima ni los atropella
            right_vector = Vec3(direction_to_leader.z, 0, -direction_to_leader.x).normalized()
            offset = right_vector * 120 + Vec3(0, 30, 0) # 120 a la derecha y 30 arriba
            
            # Ponemos al dummy a 300 unidades de distancia, pero desplazado
            self.player_dummy.position = leader.world_position - direction_to_leader * 300 + offset
            # Hacemos que mire en paralelo a la dirección de avance
            self.player_dummy.look_at(self.player_dummy.position + direction_to_leader)
            
            # Ocultamos todo el escuadrón (incluyendo partículas y propulsores)
            for d in self.squad:
                d.enabled = False
            
            # El jugador acelera a fondo cruzando el espacio
            self.player_dummy.animate_position(self.player_dummy.position + direction_to_leader * 600, duration=4.0, curve=curve.in_out_sine)
            
            # CÁMARA HEROICA ORBITAL
            self.cam_pivot = Entity(parent=self.player_dummy)
            camera.parent = self.cam_pivot
            
            self.cam_pivot.rotation = (-15, -25, 5) 
            
            # Cámara FRENTE al dummy
            camera.position = Vec3(0, 0, 45)
            camera.look_at(self.cam_pivot)
            
            self.cam_pivot.animate_rotation((10, 20, 0), duration=4.0, curve=curve.linear)
            camera.animate_position(Vec3(0, 0, 20), duration=4.0, curve=curve.linear)
            
        self.subtitle.text = "<cyan>[IA DE LA NAVE]:<default>\nIniciando maniobras de evasión e intercepción. Preparando sistemas de armas... ¡Dales duro!"

    def execute_shot_4(self, sid):
        if sid != self.session_id: return
        self.current_shot = 4
        
        # Matamos cualquier animación previa de la cámara
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
                
        # SHOT 4 (14-18s): Plano General, los Altech rompen formación!
        if len(self.squad) > 0:
            leader = self.squad[0]
            camera.parent = scene
            
            # Restauramos la visibilidad completa del escuadrón
            for d in self.squad:
                d.enabled = True
                
            # TRUCO DE CINE: Acercamos a todo el escuadrón al jugador antes de iniciar la toma.
            # Como es un corte de cámara (Jump Cut), el espectador no notará el salto espacial,
            # pero nos garantiza que al terminar la cinemática (en 4s), las naves estarán a ~150m
            # del jugador y no a 600m, haciéndolas perfectamente visibles y amenazantes.
            for d in self.squad:
                d.position += d.forward * 450
            
            # Cámara arriba y en frente, mirando hacia el escuadrón completo
            camera.parent = scene
            camera.rotation = (0, 0, 0) # Reiniciamos rotación para evitar flips por el pivot anterior
            camera.position = leader.world_position + Vec3(0, 150, -350)
            camera.look_at(leader)
            
            # La cámara hace un ligero zoom in (Dolly) hacia el caos
            camera.animate_position(leader.world_position + Vec3(0, 80, -200), duration=4.0, curve=curve.linear)
            
            # ¡LOS DUMMYS DEL ESCUADRÓN ROMPEN FILAS! (MANIOBRA STARBURST)
            import random
            for i, d in enumerate(self.squad):
                if i == 0:
                    # El líder rompe hacia adelante a una velocidad más moderada
                    d.animate_position(d.world_position + d.forward * 400, duration=10.0, curve=curve.in_out_sine)
                    continue
                
                # Desplazamiento radial respecto al líder para que se abran en abanico
                offset = d.world_position - leader.world_position
                
                # Tomamos la dirección radial en el plano relativo de la nave
                # Ignoramos la profundidad (forward) del offset para que sea un abanico perfecto
                right_dot = offset.dot(leader.right)
                up_dot = offset.dot(leader.up)
                
                radial_dir = (leader.right * right_dot + leader.up * up_dot).normalized()
                
                if radial_dir.length() < 0.1:
                    radial_dir = (leader.right * random.uniform(-1, 1) + leader.up * random.uniform(-1, 1)).normalized()
                
                # Destino: Más cerca para que la animación sea mucho más lenta y majestuosa
                final_pos = d.world_position + d.forward * 400 + radial_dir * 180
                
                # Para que el giro sea natural, usamos look_at para calcular la rotación exacta
                start_rot = d.rotation
                d.look_at(final_pos)
                target_rot = d.rotation
                d.rotation = start_rot # Restauramos
                
                # Asegurar interpolación corta (Shortest Path) para evitar giros de 360° (Gimbal Lock)
                for axis in ('x', 'y', 'z'):
                    start_val = getattr(start_rot, axis)
                    target_val = getattr(target_rot, axis)
                    diff = (target_val - start_val) % 360
                    if diff > 180: diff -= 360
                    setattr(target_rot, axis, start_val + diff)
                
                # Animamos rotación más lenta y posición muy extendida en el tiempo
                d.animate_rotation(target_rot, duration=2.5, curve=curve.in_out_quad)
                d.animate_position(final_pos, duration=12.0, curve=curve.in_out_sine)
                
        self.subtitle.text = "<red>[LÍDER ALTECH]:<default>\n¡Rompan filas, escoria espacial! ¡Quiero esa nave de la Tierra\nreducida a putas cenizas cósmicas! ¡FUEGO A DISCRECIÓN!"

    def end_cinematic(self, sid):
        if sid != self.session_id: return
        self.current_shot = 0
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        self.subtitle.text = ''
        
        # Matamos cualquier animación previa de la cámara para que no interfiera
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
                
        # CAMBIAZO: Destruir Dummys e instanciar Naves Reales con detección forzada
        from enemy import EnemyShip
        for i, d in enumerate(self.squad):
            pos = d.world_position
            rot = d.rotation
            destroy(d) # Adiós doble de acción
            
            # Instanciar el real y forzar que nos vean (force_detection=True)
            real_ship = EnemyShip("nave-altech-enemy", pos, self.game, is_boss=False, is_leader=(i==0), force_detection=True)
            real_ship.rotation = rot
            
        if hasattr(self, 'player_dummy') and self.player_dummy:
            destroy(self.player_dummy)
            
        self.is_playing = False
        
        # RESTAURAR AL JUGADOR REAL
        self.player.enabled = True
        self.player.is_cinematic = False
        
        self.player.hud_container.enable()
        
        if hasattr(self.player, 'ai_companion') and hasattr(self.player.ai_companion, 'ui'):
            self.player.ai_companion.ui.enabled = True
        
        camera.parent = self.player.camera_pivot
        camera.position = self.player.camera_modes[self.player.current_cam_index]
        camera.rotation = (0, 0, 0)
        
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.enable()
            self.player.mission_manager.waypoint.enable()
            self.player.mission_manager.altech_squad_spawned = True
            
            tracked = self.player.mission_manager.get_tracked_mission()
            if tracked and tracked.id == "main_03":
                tracked.target_pos = None
                
        # Reactivar el spawn de IA
        if hasattr(self.game, 'ai_director'):
            self.game.ai_director.boss_fight_active = False