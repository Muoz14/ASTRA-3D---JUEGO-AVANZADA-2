from ursina import *
import random
import math
from ships import AVAILABLE_SHIPS


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
            
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.show_notification("NUEVO OBJETIVO: IR A LA PUNTA DEL PLANETA", duration=5)

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
            
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.show_notification("NUEVO OBJETIVO: IR A LA PUNTA DEL PLANETA", duration=5)

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
        self.target_pos = Vec3(291, 1130, 2193)

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