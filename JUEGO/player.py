from ursina import *
from ships import AVAILABLE_SHIPS
from weapons import DualLaser
from map import TacticalMap
from ai_companion_manager import CompanionManager
from inventory import InventoryUI
from upgrades_ui import UpgradesUI
import random
import math


class SpeedLine(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, model='quad', color=color.rgba(200, 240, 255, 70), z=-1.1, **kwargs)
        self.angle = random.uniform(0, math.tau)
        self.distance = random.uniform(0.15, 0.35)
        self.speed = random.uniform(4.0, 7.0)
        self.max_scale_y = random.uniform(0.06, 0.18)
        self.scale = (0.0015, 0.01)
        self.rotation_z = math.degrees(self.angle) - 90
        self.update_position()

    def update_position(self):
        self.x = math.cos(self.angle) * self.distance
        self.y = math.sin(self.angle) * self.distance

    def update(self):
        self.distance += self.speed * time.dt
        self.scale_y = min(self.max_scale_y, self.distance * 0.4)
        self.update_position()
        if self.distance > 0.6: self.alpha -= time.dt * 5
        if self.distance > 1.2 or self.alpha <= 0: destroy(self)


class MaterialPopup(Entity):
    def __init__(self, target_asteroid, **kwargs):
        super().__init__(parent=camera.ui, z=-15, ignore_paused=True, **kwargs)
        self.target = target_asteroid

        self.bg = Entity(parent=self, model='quad', color=color.rgba(10, 15, 25, 230), scale=(0.4, 0.16),
                         position=(0.2, -0.08))
        Entity(parent=self.bg, model='quad', color=color.cyan, scale=(0.02, 1), position=(-0.5, 0), z=-0.01)
        Entity(parent=self.bg, model='quad', color=color.cyan, scale=(0.2, 0.05), position=(0.4, 0.475), z=-0.01)

        Text(parent=self, text='[ ANALISIS MINERAL ]', position=(0.02, -0.02), scale=1.2, color=color.cyan, z=-1)
        Text(parent=self, text=self.target.material_name, position=(0.02, -0.06), scale=1.8, color=color.white, z=-1)
        Text(parent=self, text=f"Tipo: {self.target.material_desc}", position=(0.02, -0.11), scale=1.1,
             color=color.light_gray, z=-1)

        self.dist_text = Text(parent=self, text='0m', position=(0.32, -0.02), scale=1.2, color=color.orange, z=-1)

        self.scale = 0
        self.animate_scale(1, duration=0.2, curve=curve.out_back)
        self.is_fading = False

    def fade_and_destroy(self):
        if self.is_fading: return
        self.is_fading = True
        self.animate_scale(0, duration=0.15)
        destroy(self, delay=0.2)

    def update(self):
        if application.paused:
            self.visible = False
            return
        if not self.target or getattr(self.target, 'is_empty', lambda: True)() or not self.target.enabled:
            self.fade_and_destroy()
            return

        dist = distance(self.target.position, camera.world_position)
        if dist > 500:
            self.fade_and_destroy()
            return

        new_dist_txt = f"{int(dist)}m"
        if self.dist_text.text != new_dist_txt:
            self.dist_text.text = new_dist_txt
        if (self.target.position - camera.world_position).dot(camera.forward) < 0:
            self.visible = False
        else:
            self.visible = True

        pos_2d = self.target.screen_position
        self.position = pos_2d + Vec2(0.06, 0.04)


class TacticalScanner:
    def __init__(self, player):
        self.player = player
        self.active = False
        self.scan_radius = 500
        self.max_targets = 15
        self.markers = []
        self.active_timer = 0
        self.current_popup = None

        self.scan_line = Entity(parent=camera.ui, model='quad', scale=(2.5, 0.03), color=color.cyan, z=-3,
                                enabled=False)
        self.analyzing_text = Text(parent=camera.ui, text='ANALIZANDO...', position=(0, 0.35), origin=(0, 0), scale=2.5,
                                   color=color.white, enabled=False)

    def toggle(self, force_off=False):
        if force_off:
            self.active = False
        else:
            self.active = not self.active

        if self.active:
            self.active_timer = 6.0
            self.play_scan_animation()
            self.scan_environment()
        else:
            self.clear_markers()

    def play_scan_animation(self):
        self.scan_line.enabled = True
        self.scan_line.y = 0.5
        self.scan_line.animate_y(-0.5, duration=0.6, curve=curve.linear)
        invoke(self.scan_line.disable, delay=0.6)
        self.analyzing_text.enabled = True
        invoke(self.analyzing_text.disable, delay=2.0)

    def scan_environment(self):
        self.clear_markers()
        asteroids_in_range = []
        
        # Buscar gestor
        if not hasattr(self, 'asteroid_manager'):
            for e in scene.entities:
                if type(e).__name__ == 'AsteroidManager':
                    self.asteroid_manager = e
                    break
                    
        scan_radius_sq = self.scan_radius ** 2
        
        if hasattr(self, 'asteroid_manager'):
            for entity in self.asteroid_manager.asteroids:
                if entity.enabled:
                    dist_sq = (self.player.position - entity.position).length_squared()
                    if dist_sq <= scan_radius_sq:
                        dist = dist_sq ** 0.5
                        asteroids_in_range.append((dist, entity))
                        
                        if getattr(entity, 'is_planet', False) and hasattr(self.player, 'mission_manager'):
                            self.player.mission_manager.complete_mission('main_01')

        asteroids_in_range.sort(key=lambda x: x[0])
        top_targets = asteroids_in_range[:self.max_targets]

        if getattr(self.player, 'achievements', None):
            self.player.achievements.register_scan_count(len(top_targets))

        for dist, entity in top_targets:
            marker = Entity(parent=entity, billboard=True)
            marker.scale = (0, 0, 0)
            marker.animate_scale((1, 1, 1), duration=0.4, curve=curve.out_back)

            c = color.rgba(0, 255, 255, 180)
            Entity(parent=marker, model='quad', scale=(2.0, 0.05), position=(0, 1.0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(2.0, 0.05), position=(0, -1.0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(0.05, 2.0), position=(1.0, 0, 0), color=c, unlit=True)
            Entity(parent=marker, model='quad', scale=(0.05, 2.0), position=(-1.0, 0, 0), color=c, unlit=True)

            marker.text_dist = Text(parent=marker, text=f'{int(dist)}m', position=(0, -1.8, 0), origin=(0, 0), scale=9,
                                    color=color.cyan)
            self.markers.append(marker)

    def update(self):
        if not self.active: return
        self.active_timer -= time.dt
        if self.active_timer <= 0:
            self.toggle(force_off=True)
            return

        hit_info = raycast(camera.world_position, camera.forward, distance=self.scan_radius, ignore=[self.player])
        if hit_info.hit and hasattr(hit_info.entity, 'is_asteroid'):
            target = hit_info.entity
            if getattr(self.current_popup, 'target', None) != target:
                if self.current_popup:
                    self.current_popup.fade_and_destroy()
                self.current_popup = MaterialPopup(target)
        else:
            if self.current_popup:
                self.current_popup.fade_and_destroy()
                self.current_popup = None

        for marker in self.markers[:]:
            # Evitar usar en scene.entities directamente por ser lento
            if getattr(marker, 'is_empty', lambda: True)() or getattr(marker.parent, 'is_empty', lambda: True)() or not marker.parent.enabled:
                if not getattr(marker, 'is_empty', lambda: True)():
                    destroy(marker)
                self.markers.remove(marker)
                continue

            dist_sq = (self.player.position - marker.parent.position).length_squared()
            if dist_sq > self.scan_radius ** 2:
                destroy(marker)
                self.markers.remove(marker)
                continue

            dist = dist_sq ** 0.5
            new_dist = f'{int(dist)}m'
            if marker.text_dist.text != new_dist:
                marker.text_dist.text = new_dist

            # OPTIMIZACIÓN: Solo reasigna el color si realmente cambió
            new_c = color.red if dist < 120 else color.cyan
            if marker.text_dist.color != new_c:
                marker.text_dist.color = new_c

    def clear_markers(self):
        for marker in self.markers:
            marker.animate_scale((0, 0, 0), duration=0.2)
            destroy(marker, delay=0.2)
        self.markers.clear()
        if getattr(self, 'current_popup', None):
            self.current_popup.fade_and_destroy()
            self.current_popup = None

class RadarWidget(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(parent=player.hud_container, **kwargs)
        self.player = player
        
        self.border = Entity(parent=self, model='circle', color=color.rgba32(0, 255, 255, 60), scale=(1.05, 1.05), z=1.1, unlit=True)
        self.bg = Entity(parent=self, model='circle', color=color.rgba32(5, 15, 25, 120), scale=(1, 1), z=1, unlit=True)
        
        self.blips_container = Entity(parent=self)
        
        # Crear mesh de triangulo mucho mas puntiagudo para que sea obvio cual es el frente
        self.tri_mesh_player = __import__('ursina').Mesh(vertices=[(-0.25, -0.5, 0), (0.25, -0.5, 0), (0, 0.6, 0)])
        self.center_blip = Entity(parent=self, model=self.tri_mesh_player, color=color.white, scale=(0.06, 0.06), z=-0.2, unlit=True, always_on_top=True)
        
        self.blips = []
        self.max_range = 3000
        
        self.debug_text = __import__('ursina').Text(parent=self, text='', scale=3, y=-0.6, color=color.yellow)
        
    def update(self):
        if not self.player or getattr(self.player, 'is_dead', False) or getattr(self.player, 'is_cinematic', False) or getattr(__import__('ursina').application, 'paused', False):
            if self.bg.enabled:
                self.bg.enabled = False
                self.border.enabled = False
                self.center_blip.enabled = False
                for b in self.blips: b.enabled = False
            return
        else:
            if not self.bg.enabled:
                self.bg.enabled = True
                self.border.enabled = True
                self.center_blip.enabled = True
                
        import math
        for b in self.blips:
            b.enabled = False
            
        blip_idx = 0
        
        self.center_blip.rotation_z = self.player.rotation_y

        for e in __import__('ursina').scene.entities:
            # Prevenir assertions de NodePath vacío
            if not e: continue
            
            # Solo procesar entidades que tengan las propiedades de un enemigo y estén habilitadas
            if hasattr(e, 'faction') and e.faction != 'npc' and getattr(e, 'enabled', False) and getattr(e, 'health', 0) > 0 and e != self.player:
                dist = distance(self.player.world_position, e.world_position)
                if dist <= self.max_range:
                    delta = e.world_position - self.player.world_position
                    rx = delta.x
                    rz = delta.z
                    
                    factor = 0.5 / self.max_range
                    radar_x = rx * factor
                    radar_y = rz * factor
                    
                    blip_dist = math.sqrt(radar_x**2 + radar_y**2)
                    if blip_dist > 0.48:
                        scale_f = 0.48 / blip_dist
                        radar_x *= scale_f
                        radar_y *= scale_f
                    elif blip_dist < 0.08:
                        # Mantener a los enemigos fuera del centro (debajo del jugador)
                        scale_f = 0.08 / (blip_dist + 0.0001)
                        radar_x *= scale_f
                        radar_y *= scale_f
                    
                    if blip_idx < len(self.blips):
                        blip = self.blips[blip_idx]
                        blip.enabled = True
                    else:
                        blip_mesh = __import__('ursina').Mesh(vertices=[(-0.25, -0.5, 0), (0.25, -0.5, 0), (0, 0.6, 0)])
                        blip = Entity(parent=self.blips_container, model=blip_mesh, color=color.red, scale=(0.05, 0.05), z=-0.1, unlit=True)
                        self.blips.append(blip)
                        
                    blip.position = (radar_x, radar_y, -0.1)
                    blip.rotation_z = e.rotation_y
                    
                    blip_idx += 1
                    
        self.debug_text.text = f"Enemies: {blip_idx}"

class PlayerShip(Entity):
    def __init__(self, game_over_menu=None, game_app=None, ship_id="nave1", **kwargs):
        self.ship_id = ship_id
        config = AVAILABLE_SHIPS.get(ship_id, AVAILABLE_SHIPS["nave1"])
        
        super().__init__(model=None, position=(0, 0, 0), **kwargs)
        self.collider = SphereCollider(self, center=Vec3(0,0,0), radius=6.0)
        
        self.ship_model_entity = Entity(parent=self, model=config.model, color=config.ship_color, 
                                        scale=config.scale, rotation=getattr(config, 'model_rotation_offset', (0,0,0)))

        self.game_over_menu = game_over_menu
        self.game_app = game_app
        self.is_dead = False
        self.is_cinematic = False
        self.pause_menu_open = False
        self.achievements = None
        self.scanner_warning = None
        
        # Target lock system
        self.locked_target = None
        self.lock_ui = Entity(parent=camera.ui, enabled=False)
        c = color.rgb(255, 80, 80)
        # Cuadrado retícula
        Entity(parent=self.lock_ui, model='quad', scale=(0.1, 0.005), position=(0, 0.05, 0), color=c, unlit=True)
        Entity(parent=self.lock_ui, model='quad', scale=(0.1, 0.005), position=(0, -0.05, 0), color=c, unlit=True)
        Entity(parent=self.lock_ui, model='quad', scale=(0.005, 0.1), position=(0.05, 0, 0), color=c, unlit=True)
        Entity(parent=self.lock_ui, model='quad', scale=(0.005, 0.1), position=(-0.05, 0, 0), color=c, unlit=True)
        self.lock_text = Text(parent=self.lock_ui, text='...', scale=1.0, y=0.08, origin=(0,0), color=c)

        
        # DEBUG: Mostrar posición para configurar misiones
        self.pos_debug = Text(parent=camera.ui, text="", position=(window.top_left.x + 0.05, window.top_left.y - 0.1), scale=1.5, color=color.yellow, enabled=False)
        self.mission_prompt = Text(parent=camera.ui, text="Presiona [X] para analizar el planeta", position=(0, -0.25), origin=(0,0), scale=1.5, color=color.yellow, enabled=False)
        self.session_score = 0.0
        self.session_time = 0.0

        self.shield_level = 1
        self.max_shield = 100 + (self.shield_level - 1) * 25
        self.shield = self.max_shield

        self.error_spawn_timer = 0.0
        self.speed_line_timer = 0.0

        self.thrusters = []
        self.scanner = TacticalScanner(self)
        self.tactical_map = TacticalMap(self)
        self.inventory = InventoryUI(self)
        self.upgrades_ui = UpgradesUI(self)
        
        self.camera_pivot = Entity(parent=self)
        camera.parent = self.camera_pivot
        
        self.ai_companion = CompanionManager()

        self.camera_modes = [(0, 1.0, -9), (0, 1.5, -14), (0, 2.5, -20)]
        self.current_cam_index = 1
        camera.position = self.camera_modes[self.current_cam_index]
        camera.rotation = (0, 0, 0)
        self.base_fov = camera.fov
        mouse.locked = True

        self.hud_container = Entity(parent=camera.ui)
        
        # Inicializar radar DESPUES del hud_container
        self.radar = RadarWidget(self, position=(window.top_left.x + 0.14, window.top_left.y - 0.20), scale=(0.18, 0.18))

        self.cine_text = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, 0.15), scale=2,
                              color=color.rgba(255, 255, 255, 0), enabled=False, z=-5)
        self.oob_warning = Text(parent=self.hud_container, text='', position=(0, 0.22), origin=(0, 0), scale=1.6,
                                enabled=False, z=-2)

        self.damage_flash_overlay = Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0),
                                           scale=(99, 99), z=-1.5)

        self.hud_borders = []
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(0.04, 2.0),
                   position=(window.left.x + 0.02, 0), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(0.04, 2.0),
                   position=(window.right.x - 0.02, 0), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(2.0, 0.04),
                   position=(0, window.top.y - 0.02), z=-1.4))
        self.hud_borders.append(
            Entity(parent=self.hud_container, model='quad', color=color.rgba(255, 0, 0, 0), scale=(2.0, 0.04),
                   position=(0, window.bottom.y + 0.02), z=-1.4))

        self.crosshair = Entity(parent=self.hud_container, model='circle', color=color.rgba(255, 255, 255, 200),
                                scale=(0.006, 0.006), position=(0, 0), z=-1)

        self.screen_cracks = []
        for _ in range(8):
            crack = Entity(parent=self.hud_container, model='quad', color=color.rgba(200, 230, 255, 140),
                           scale=(random.uniform(0.15, 0.45), 0.003),
                           position=(random.uniform(-0.6, 0.6), random.uniform(-0.4, 0.4)),
                           rotation_z=random.uniform(0, 360), enabled=False, z=-2)
            self.screen_cracks.append(crack)

        self.warning_text = Text(parent=self.hud_container, text='¡PELIGRO: NAVE INVERTIDA!', position=(0, 0.35),
                                 origin=(0, 0), color=color.red, scale=1.5, enabled=False)

        # BRÚJULA TÁCTICA
        self.compass_bg = Entity(parent=self.hud_container, position=(0, 0.43), z=-1)
        self.compass_marker = Entity(parent=self.hud_container, model='quad', color=color.cyan, scale=(0.003, 0.016),
                                     position=(0, 0.45), z=-1.1)

        self.compass_points = [
            ('N', 0), ('30', 30), ('NE', 45), ('60', 60),
            ('E', 90), ('120', 120), ('SE', 135), ('150', 150),
            ('S', 180), ('210', 210), ('SW', 225), ('240', 240),
            ('W', 270), ('300', 300), ('NW', 315), ('330', 330)
        ]

        self.compass_labels = []
        for label, angle in self.compass_points:
            if label in ['N', 'S', 'E', 'W']:
                base_c = color.cyan
            elif label in ['NE', 'SE', 'SW', 'NW']:
                base_c = color.white
            else:
                base_c = color.light_gray

            t = Text(parent=self.hud_container, text=label, scale=0.8, color=base_c, origin=(0, 0), z=-1.2,
                     enabled=False)
            self.compass_labels.append((t, angle))

        self.waypoint_compass_marker = Entity(parent=self.hud_container, model='triangle', color=color.yellow,
                                              scale=(0.015, 0.015), position=(0, 0.46), z=-1.3, rotation_z=180,
                                              enabled=False)
        self.waypoint_compass_dist = Text(parent=self.hud_container, text='0m', scale=0.7, color=color.yellow,
                                          origin=(0, 0), position=(0, 0.40), z=-1.3, enabled=False)

        # TACÓMETRO E INSTRUMENTAL
        tacho_center_x = window.right.x - 0.15
        tacho_center_y = -0.32
        self.tacho_bg = Entity(parent=self.hud_container, model='circle', color=color.hex('#111111'), scale=0.25,
                               position=(tacho_center_x, tacho_center_y), z=1)
        self.tacho_needle = Entity(parent=self.tacho_bg, model='quad', color=color.hex('#ff3333'), scale=(0.02, 0.45),
                                   origin=(0, -0.5), position=(0, 0), rotation_z=-130, z=-0.1)
        Entity(parent=self.tacho_bg, model='circle', color=color.black, scale=0.15, z=-0.2)

        Text(parent=self.hud_container, text='0', position=(tacho_center_x - 0.08, tacho_center_y - 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='1200', position=(tacho_center_x - 0.09, tacho_center_y + 0.02),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='2200', position=(tacho_center_x - 0.04, tacho_center_y + 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='3200', position=(tacho_center_x + 0.04, tacho_center_y + 0.08),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='4200', position=(tacho_center_x + 0.09, tacho_center_y + 0.02),
             origin=(0, 0), scale=0.9, color=color.light_gray, z=-1)
        Text(parent=self.hud_container, text='5000', position=(tacho_center_x + 0.08, tacho_center_y - 0.08),
             origin=(0, 0), scale=0.9, color=color.red, z=-1)

        self.speedometer = Text(parent=self.hud_container, text='0', position=(tacho_center_x, tacho_center_y + 0.02),
                                origin=(0, 0), scale=3, color=color.white, z=-1)
        Text(parent=self.hud_container, text='KM/H', position=(tacho_center_x, tacho_center_y - 0.04), origin=(0, 0),
             scale=1.0, color=color.gray, z=-1)

        self.inventory_open_sound = Audio('assets/sounds/ui/open_inventory.mp3', loop=False, autoplay=False, volume=0.8)
        
        self.session_distance = 0.0
        self.bottom_hud = Entity(parent=self.hud_container, position=(0, -0.42))
        Text(parent=self.bottom_hud, text='ESCUDO', position=(-0.25, 0.02), scale=0.8, color=color.cyan,
             origin=(0.5, 0))
        self.shield_bar_bg = Entity(parent=self.bottom_hud, model='quad', color=color.hex('#0a0f14'), alpha=0.8,
                                    scale=(0.22, 0.01), position=(-0.14, 0), z=0)
        self.shield_bar = Entity(parent=self.shield_bar_bg, model='quad', color=color.cyan, scale=(1, 1),
                                 origin=(0.5, 0), position=(0.5, 0), z=-0.01)

        Text(parent=self.bottom_hud, text='TURBO', position=(0.25, 0.02), scale=0.8, color=color.orange,
             origin=(-0.5, 0))
        self.boost_bar_bg = Entity(parent=self.bottom_hud, model='quad', color=color.hex('#0a0f14'), alpha=0.8,
                                   scale=(0.22, 0.01), position=(0.14, 0), z=0)
        self.boost_bar = Entity(parent=self.boost_bar_bg, model='quad', color=color.orange, scale=(1, 1),
                                origin=(-0.5, 0), position=(-0.5, 0), z=-0.01)

        self.base_fire_rate = 0.45
        self.min_fire_rate = 0.08
        self.current_fire_rate = self.base_fire_rate
        self.fire_timer = 0
        self.heat = 0
        self.max_heat = 100
        self.overheated = False

        self.heat_widget = Entity(parent=self.hud_container, position=(0.02, -0.02), enabled=False)
        self.heat_bar_bg = Entity(parent=self.heat_widget, model='quad', color=color.rgba(0, 0, 0, 150),
                                  scale=(0.06, 0.008), rotation_z=-20)
        self.heat_bar = Entity(parent=self.heat_bar_bg, model='quad', color=color.orange, scale=(0, 1),
                               origin=(-0.5, 0), position=(-0.5, 0))
        self.overheat_text = Text(parent=self.heat_widget, text='! ALERTA TERMICA !', color=color.red, scale=0.8,
                                  position=(0.04, -0.02), enabled=False)

        self.apply_config(config)

    def change_ship(self, ship_id):
        self.ship_id = ship_id
        config = AVAILABLE_SHIPS.get(ship_id, AVAILABLE_SHIPS["nave1"])
        self.ship_model_entity.model = config.model
        self.ship_model_entity.color = config.ship_color
        self.ship_model_entity.scale = config.scale
        self.ship_model_entity.rotation = getattr(config, 'model_rotation_offset', (0,0,0))
        self.collider = BoxCollider(self, center=Vec3(0,0,0), size=Vec3(*config.scale))
        self.apply_config(config)
        
    def apply_config(self, config):
        self.right_laser_offset = config.laser_offsets[1]
        self.left_laser_offset = config.laser_offsets[0]
        self.laser_scale = getattr(config, 'laser_scale', (0.2, 0.2, 2.0))
        self.laser_color = getattr(config, 'laser_color', color.red)
        self.thruster_color = getattr(config, 'thruster_color', color.rgba(0, 255, 255, 200))
        self.laser_level = 1
        self.vacuum_level = 0

        self.target_speed = 0
        self.current_speed = 0
        self.normal_max_speed = config.max_speed
        
        self.turbo_level = 1
        self.boost_max_speed = config.boost_max_speed + (self.turbo_level - 1) * 20
        self.acceleration = config.acceleration
        self.friction = config.friction
        self.mouse_sensitivity = 60
        self.roll_speed = 220
        self.max_boost = 100 + (self.turbo_level - 1) * 50
        self.boost_fuel = self.max_boost
        
        # Los propulsores se reconstruyen al final de apply_config

        self.auto_level_timer = 0
        self.auto_level_delay = 0.8
        self.level_damping = 1.2
        self.max_banking_angle = 30.0

        self.base_pitch = 0.0
        self.max_pitch_banking = 15.0

        self.dash_cooldown = 1.2
        self.dash_timer = 0
        self.is_dashing = False
        self.dash_duration = 0.4
        self.dash_time_left = 0
        self.dash_direction = 0
        self.dash_speed = 200
        self.dash_roll = 0.0
        self.camera_dash_drag = 0.3
        
        self.is_barrel_rolling = False

        self.shake_amount = 0.0
        self.shake_decay = 12.0

        self.max_boost = 100 + (self.turbo_level - 1) * 50
        self.boost_fuel = self.max_boost
        self.boost_recharge_delay = 1.5
        self.boost_timer = 0
        self.trail_timer = 0
        
        self.blackhole_cooldown = 5.0
        self.blackhole_timer = 0.0

        self.sector_radius = 15000
        self.oob_timer = 10.0
        
        # OPTIMIZACIÓN: Pre-calculamos los colores de los motores
        self.color_boost = color.rgb(0, 255, 255)
        self.color_w = color.cyan
        self.color_s = color.blue
        self.color_idle = color.rgba(0, 180, 255, 120)
        
        # Guardar la escala configurada
        self.base_thruster_scale = getattr(config, 'thruster_scale', (0.2, 0.2, 0.4))
        
        # Reposition thrusters
        for t in self.thrusters:
            destroy(t)
        self.thrusters.clear()
        
        for offset in config.thruster_offsets:
            scaled_offset = (offset[0] * config.scale[0], offset[1] * config.scale[1], offset[2] * config.scale[2])
            t = Entity(parent=self, model='sphere', color=self.thruster_color, scale=self.base_thruster_scale, position=scaled_offset)
            self.thrusters.append(t)



    def cracks_on_damage(self):
        disabled_cracks = [c for c in self.screen_cracks if not c.enabled]
        if disabled_cracks:
            random.choice(disabled_cracks).enabled = True

    def generate_trail(self):
        self.trail_timer -= time.dt
        if self.trail_timer <= 0:
            config = AVAILABLE_SHIPS.get(self.ship_id, AVAILABLE_SHIPS["nave1"])
            
            # Ajustamos la opacidad del color para la estela (50 de alfa aprox)
            base_color = self.thruster_color
            trail_color = color.rgba(base_color.r * 255, base_color.g * 255, base_color.b * 255, 50)
            
            if self.ship_id in ["nave2", "nave-altech-enemy"]:
                for offset in config.thruster_offsets:
                    scaled_offset = (offset[0] * config.scale[0], offset[1] * config.scale[1], offset[2] * config.scale[2])
                    p = Entity(parent=self, model='sphere', color=trail_color, unlit=True,
                               scale=random.uniform(0.06, 0.12) * config.scale[0], position=scaled_offset)
                    # Dispersión masiva hacia atrás
                    p.animate_position(p.position + (random.uniform(-0.15, 0.15) * config.scale[0], random.uniform(-0.15, 0.15) * config.scale[1], -2.0 * config.scale[2]), duration=0.4, curve=curve.linear)
                    p.animate_scale(0, duration=0.4, curve=curve.linear)
                    destroy(p, delay=0.4)
            else:
                for offset in config.thruster_offsets:
                    for _ in range(2):
                        direccion_expulsion = 1 if offset[0] > 0 else -1
                        trail_pos = self.position + (self.right * offset[0] * config.scale[0]) + (self.up * offset[1] * config.scale[1]) + (self.forward * offset[2] * config.scale[2])
                        pool = getattr(self.game_app, 'pool', None) if hasattr(self, 'game_app') else None
                        if pool:
                            p = pool.get_object(Entity, pool_key="TrailParticle", model='sphere', color=trail_color, position=trail_pos)
                            p.position = trail_pos
                            p.scale = random.uniform(0.06, 0.14)
                            p.color = trail_color
                        else:
                            p = Entity(model='sphere', color=trail_color, scale=random.uniform(0.06, 0.14), position=trail_pos)
                        
                        duracion_vida = random.uniform(0.12, 0.22)
                        
                        if hasattr(p, 'animations'):
                            for anim in p.animations: anim.finish()
                            p.animations.clear()
                            
                        p.animate_scale(Vec3(0, 0, 0), duration=duracion_vida, curve=curve.linear)
                        p.animate_color(color.rgba(0, 255, 255, 0), duration=duracion_vida, curve=curve.linear)
                        pos_final = p.position + (self.right * direccion_expulsion * random.uniform(1.2, 2.5)) + (self.forward * -1.5)
                        p.animate_position(pos_final, duration=duracion_vida, curve=curve.out_sine)
                        
                        if pool:
                            invoke(pool.return_object, p, delay=duracion_vida + 0.05)
                        else:
                            destroy(p, delay=duracion_vida + 0.05)
            self.trail_timer = 0.15  # OPTIMIZACIÓN: Bajamos DRASTICAMENTE la frecuencia de partículas

    def start_dash(self, direction):
        if getattr(self, 'achievements', None):
            self.achievements.register_dash()
        if self.is_dashing: return
        self.is_dashing = True
        self.dash_timer = self.dash_cooldown
        self.dash_direction = direction
        self.dash_time_left = self.dash_duration
        self.animate('dash_roll', -360 * direction, duration=self.dash_duration, curve=curve.in_out_sine)
        invoke(setattr, self, 'dash_roll', 0, delay=self.dash_duration + 0.05)

    def start_barrel_roll(self):
        self.is_barrel_rolling = True
        self.animate('rotation_z', self.rotation_z + 360, duration=0.6, curve=curve.in_out_sine)
        invoke(self.end_barrel_roll, delay=0.6)
        
    def end_barrel_roll(self):
        self.is_barrel_rolling = False
        self.rotation_z = self.rotation_z % 360
        if self.rotation_z > 180:
            self.rotation_z -= 360


    def take_damage(self, amount):
        if hasattr(self, 'ai_companion'):
            self.ai_companion.on_damage_taken()
        if getattr(self, 'achievements', None):
            self.achievements.register_damage_taken()
        # El escudo absorbe el daño, si llega a 0 mueres
        self.shield -= amount
        self.shield = max(0, self.shield)
        self.shake_amount = clamp(self.shake_amount + 0.4, 0, 0.9)
        self.damage_flash_overlay.alpha = 0.5
        self.cracks_on_damage()
        if self.shield <= 0: self.die()

    def repair_shield(self, amount):
        if self.is_dead: return
        self.shield += amount
        self.shield = min(self.max_shield, self.shield)
        if self.shield > 15:
            for crack in self.screen_cracks: crack.enabled = False
            for b in self.hud_borders: b.alpha = 0

    def die(self):
        self.is_dead = True
        self.clear_persistent_ui()
        self.hud_container.disable()
        camera.ui.x = 0
        camera.ui.y = 0
        self.camera_pivot.position = Vec3(0, 0, 0)
        self.scanner.clear_markers()
        self.scanner.active = False
        
        self.scanner.active = False

        if getattr(self.tactical_map, 'is_open', False):
            self.tactical_map.toggle()

        if self.game_app and hasattr(self.game_app, 'save_pilot_stats'):
            self.game_app.save_pilot_stats(int(self.session_score), int(self.session_time))

        if self.game_over_menu: self.game_over_menu.enabled = True
        mouse.locked = False
        self.visible = False
        self.collider = None

    def reset_ship(self):
        self.is_cinematic = False
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.base_pitch = 0.0
        self.current_speed = 0
        self.target_speed = 0
        self.session_score = 0.0
        self.session_time = 0.0
        self.session_distance = 0.0
        self.boost_fuel = 100
        self.shield = 100
        self.heat = 0
        self.overheated = False
        self.is_dead = False
        self.visible = True
        self.collider = 'box'
        self.dash_timer = 0
        self.is_dashing = False
        self.heat_widget.enabled = False
        self.overheat_text.enabled = False
        self.heat_bar.color = color.orange
        self.tacho_needle.color = color.hex('#ff3333')
        self.speedometer.color = color.white
        self.scanner.clear_markers()
        self.scanner.active = False

        if getattr(self.tactical_map, 'is_open', False):
            self.tactical_map.toggle()
        self.tactical_map.clear_waypoint()

        self.waypoint_compass_marker.enabled = False
        self.waypoint_compass_dist.enabled = False
        self.oob_timer = 10.0

        self.hud_container.enable()
        self.damage_flash_overlay.alpha = 0
        camera.ui.x = 0
        camera.ui.y = 0
        self.camera_pivot.position = Vec3(0, 0, 0)
        for b in self.hud_borders: b.alpha = 0
        for crack in self.screen_cracks: crack.enabled = False
        for t in self.thrusters: t.visible = True
        self.clear_persistent_ui()

    def clear_persistent_ui(self):
        if hasattr(self, 'scanner') and self.scanner:
            self.scanner.clear_markers()
            if hasattr(self.scanner, 'analyzing_text') and self.scanner.analyzing_text:
                self.scanner.analyzing_text.enabled = False
            if hasattr(self.scanner, 'scan_line') and self.scanner.scan_line:
                self.scanner.scan_line.enabled = False
        if hasattr(self, 'oob_warning') and self.oob_warning:
            self.oob_warning.enabled = False

    def add_score(self, amount):
        self.session_score += amount

    def update(self):
        # Actualizar texto de depuración de posición optimizado
        # Target Lock System
        if held_keys['right mouse'] and not self.is_dead and not self.is_cinematic:
            if not self.locked_target:
                closest_enemy = None
                closest_dist = float('inf')
                for e in __import__('ursina').scene.entities:
                    if type(e).__name__ == 'EnemyShip' and getattr(e, 'faction', 'unknown') != 'npc' and not getattr(e, 'is_dead', False):
                        if (e.position - self.position).length() < 2000:
                            
                            dir_to_enemy = (e.position - self.position).normalized()
                            dot_prod = self.forward.dot(dir_to_enemy)
                            if dot_prod > 0.95:  # ~18 degrees from center
                                d = 1.0 - dot_prod
                                if d < closest_dist:
                                    closest_dist = d
                                    closest_enemy = e
                if closest_enemy:
                    self.locked_target = closest_enemy
                    self.lock_time = 0.0
                    self.lock_ui.enabled = True
            
            if self.locked_target:
                if getattr(self.locked_target, 'is_dead', False) or (self.locked_target.position - self.position).length() > 2000:
                    self.locked_target = None
                    self.lock_time = 0.0
                    self.lock_ui.enabled = False
                else:
                    self.lock_time = getattr(self, 'lock_time', 0.0) + time.dt
                    
                    # Proyectar la posición 3D de la nave a la UI 2D
                    try:
                        screen_pos = __import__('ursina').world_position_to_screen_position(self.locked_target.position)
                    except AttributeError:
                        screen_pos = getattr(camera, 'world_position_to_screen_position', lambda x: Vec2(0,0))(self.locked_target.position)
                        
                    self.lock_ui.position = screen_pos
                    
                    dist = int((self.locked_target.position - self.position).length())
                    
                    if self.lock_time < 1.0:
                        self.lock_ui.rotation_z += 150 * time.dt
                        self.lock_ui.scale = lerp(Vec3(1.5,1.5,1.5), Vec3(1,1,1), self.lock_time)
                        self.lock_text.text = f'Fijando... {int(self.lock_time * 100)}%\nDIST: {dist}m'
                        self.lock_text.color = color.rgb(255, 150, 0)
                        for c in self.lock_ui.children:
                            if type(c).__name__ != 'Text':
                                c.color = color.rgb(255, 150, 0)
                    else:
                        self.lock_ui.rotation_z = 0
                        self.lock_ui.scale = Vec3(1,1,1)
                        hp = getattr(self.locked_target, 'health', 0)
                        self.lock_text.text = f'FIJADO!\nHP: {hp}\nDIST: {dist}m'
                        self.lock_text.color = color.red
                        for c in self.lock_ui.children:
                            if type(c).__name__ != 'Text':
                                c.color = color.red

        else:
            self.locked_target = None
            self.lock_time = 0.0
            if hasattr(self, 'lock_ui'):
                self.lock_ui.enabled = False

        new_pos_txt = f"POS: {int(self.x)}, {int(self.y)}, {int(self.z)}"
        if self.pos_debug.text != new_pos_txt:
            self.pos_debug.text = new_pos_txt
        
        if hasattr(self, 'scanner'): self.scanner.update()
        if getattr(self, 'achievements', None):
            self.achievements.update(time.dt, self)
            
        target = getattr(self, 'mission_manager', None) and self.mission_manager.get_active_target()
        if target and not self.is_cinematic and not self.is_dead and not application.paused:
            if (self.world_position - target).length_squared() < 10000:
                self.mission_prompt.enabled = True
            else:
                self.mission_prompt.enabled = False
        else:
            self.mission_prompt.enabled = False
            
        if not self.is_dead and not self.is_cinematic and not application.paused:
            self.session_time += time.dt
            self.session_score += 10 * time.dt # 10 puntos por segundo de supervivencia


        hide_ui = self.is_dead or self.is_cinematic
        self.compass_bg.enabled = not hide_ui
        self.compass_marker.enabled = not hide_ui

        current_heading = self.rotation_y % 360
        for lbl_text, angle in self.compass_labels:
            if hide_ui:
                if lbl_text.enabled: lbl_text.enabled = False
                continue

            diff = (angle - current_heading) % 360
            if diff > 180:
                diff -= 360

            if abs(diff) < 60:
                if not lbl_text.enabled: lbl_text.enabled = True
                lbl_text.x = (diff / 60) * 0.35
                lbl_text.y = 0.44

                # OPTIMIZACIÓN MÁXIMA: Modificamos SOLO el canal alpha, nada de regenerar mallas
                lbl_text.alpha = 1.0 - (abs(diff) / 60.0)
            else:
                if lbl_text.enabled: lbl_text.enabled = False

        if getattr(self.tactical_map, 'waypoint_pos_3d', None) and not hide_ui:
            wp_pos = self.tactical_map.waypoint_pos_3d
            dist_to_wp = distance(self.position, wp_pos)

            if dist_to_wp < 150:
                self.tactical_map.clear_waypoint()
                if self.waypoint_compass_marker.enabled:
                    self.waypoint_compass_marker.enabled = False
                    self.waypoint_compass_dist.enabled = False
            else:
                if not self.waypoint_compass_marker.enabled:
                    self.waypoint_compass_marker.enabled = True
                    self.waypoint_compass_dist.enabled = True

                scale_factor = clamp(dist_to_wp / 1500, 0.15, 1.0)
                self.tactical_map.world_waypoint.scale = Vec3(10, 40, 10) * scale_factor

                dir_to_wp = wp_pos - self.position
                angle_to_wp = math.degrees(math.atan2(dir_to_wp.x, dir_to_wp.z)) % 360

                diff_wp = (angle_to_wp - current_heading) % 360
                if diff_wp > 180: diff_wp -= 360

                if abs(diff_wp) < 60:
                    self.waypoint_compass_marker.x = (diff_wp / 60) * 0.35
                    self.waypoint_compass_dist.x = (diff_wp / 60) * 0.35
                    new_wp_text = f"{int(dist_to_wp)}m"
                    if self.waypoint_compass_dist.text != new_wp_text:
                        self.waypoint_compass_dist.text = new_wp_text
                else:
                    self.waypoint_compass_marker.enabled = False
                    self.waypoint_compass_dist.enabled = False
        else:
            if self.waypoint_compass_marker.enabled:
                self.waypoint_compass_marker.enabled = False
                self.waypoint_compass_dist.enabled = False

        if self.is_dead:
            self.current_speed = lerp(self.current_speed, 0, time.dt * self.friction)
            dead_speed_str = str(int(abs(self.current_speed)))
            if self.speedometer.text != dead_speed_str:
                self.speedometer.text = dead_speed_str
            self.tacho_needle.rotation_z = -130 + (clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1) * 260)
            self.warning_text.enabled = False
            self.camera_pivot.position = lerp(self.camera_pivot.position, Vec3(0, 0, 0), time.dt * 15)
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, 0, time.dt * 15)
                if t.visible: t.visible = False
            return

        if self.is_cinematic:
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, random.uniform(0.3, 0.5), time.dt * 12)
                if t.color != self.color_idle: t.color = self.color_idle
            return

        distancia_centro = self.position.length()
        if distancia_centro > self.sector_radius:
            if not self.oob_warning.enabled: self.oob_warning.enabled = True
            self.damage_flash_overlay.alpha = random.uniform(0.2, 0.4)
            self.shake_amount = max(self.shake_amount, 0.25)

            self.oob_timer -= time.dt
            new_oob_txt = f'<red>¡ADVERTENCIA CRITICA!\n<white>ABANDONANDO SECTOR DE EXTRACCION ALFA\n<red>DESPRESURIZACION EN: {max(0, int(self.oob_timer))}s'
            if self.oob_warning.text != new_oob_txt:
                self.oob_warning.text = new_oob_txt

            if self.oob_timer <= 0:
                self.shield = 0
                self.die()
                return
        else:
            if self.oob_warning.enabled: self.oob_warning.enabled = False
            self.oob_timer = 10.0

            if self.shield <= 15:
                pulso_alerta = 0.3 + math.sin(time.time() * 12) * 0.15
                for b in self.hud_borders: b.alpha = pulso_alerta
                for crack in self.screen_cracks: crack.enabled = True
                camera.fov += random.uniform(-0.8, 0.8)
                camera.ui.x = random.uniform(-0.006, 0.006)
                camera.ui.y = random.uniform(-0.006, 0.006)

                self.error_spawn_timer -= time.dt
                if self.error_spawn_timer <= 0:
                    mensajes_error = ["SISTEMA DEFECTUOSO", "NUCLEO CRITICO", "ERROR: 0x00F8C3", "FUGA DE VOLTAJE",
                                      "FALLO ESTRUCTURAL", "PRESION BAJA"]
                    err_txt = Text(text=random.choice(mensajes_error),
                                   position=(random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.2)), color=color.red,
                                   scale=random.uniform(1.1, 1.5), parent=self.hud_container)
                    destroy(err_txt, delay=random.uniform(0.15, 0.3))
                    self.error_spawn_timer = random.uniform(0.25, 0.55)
            else:
                for b in self.hud_borders: b.alpha = 0
                camera.ui.x = 0
                camera.ui.y = 0

        hit_info = self.intersects()
        if hit_info.hit:
            ent = hit_info.entity
            if hasattr(ent, 'is_planet'):
                self.shield = 0
                self.take_damage(9999)
                return
            if hasattr(ent, 'is_asteroid'):
                from weapons import ExplosionParticle
                for _ in range(25):
                    ExplosionParticle(pos=ent.position)

                rebound_dir = (self.position - ent.position).normalized()
                self.position += rebound_dir * 1.5
                self.current_speed = -self.current_speed * 0.15
                ent.split()
                self.take_damage(30)
                return

        if self.damage_flash_overlay.alpha > 0 and distancia_centro <= self.sector_radius:
            self.damage_flash_overlay.alpha = lerp(self.damage_flash_overlay.alpha, 0, time.dt * 6)

        # OPTIMIZACIÓN: Cambio de color de escudo seguro
        target_shield_c = color.red if self.shield <= 15 else color.cyan
        if self.shield_bar.color != target_shield_c:
            self.shield_bar.color = target_shield_c

        self.shield_bar.scale_x = self.shield / self.max_shield

        if self.up.y < -0.1:
            if not self.warning_text.enabled: self.warning_text.enabled = True
        else:
            if self.warning_text.enabled: self.warning_text.enabled = False

        is_boosting = held_keys['space'] and self.boost_fuel > 0
        
        if is_boosting and not getattr(self, 'was_boosting', False):
            # Solo activar el diálogo de la IA si el turbo está completamente lleno
            if self.boost_fuel >= self.max_boost - 1.0:
                self.ai_companion.on_boost_activated()
                self.has_strong_boost = True
            else:
                self.has_strong_boost = False
        self.was_boosting = is_boosting

        if is_boosting:
            self.target_speed = self.boost_max_speed
            self.boost_fuel -= 18 * time.dt
            self.boost_timer = self.boost_recharge_delay
            self.generate_trail()
            self.shake_amount = max(self.shake_amount, 0.15)
            self.speed_line_timer -= time.dt
            if self.speed_line_timer <= 0:
                SpeedLine() # Solo 1 por tick
                self.speed_line_timer = 0.08 # Mucho menos frecuente
        elif held_keys['w']:
            self.target_speed = self.normal_max_speed
        elif held_keys['s']:
            self.target_speed = -self.normal_max_speed / 2
        else:
            self.target_speed = 0

        lerp_factor = self.acceleration if abs(self.target_speed) > abs(self.current_speed) else self.friction
        
        # Aplicar aceleración extra fuerte si estamos en la primera etapa de un turbo lleno (primer 35%)
        if is_boosting and getattr(self, 'has_strong_boost', False) and self.boost_fuel >= self.max_boost * 0.65:
            lerp_factor *= 5.0 # Impulso 5x más fuerte inicial
            self.shake_amount = max(self.shake_amount, 0.25)
            
        self.current_speed = lerp(self.current_speed, self.target_speed, time.dt * lerp_factor)

        speed_ratio = clamp(abs(self.current_speed) / self.boost_max_speed, 0, 1)
        target_fov = self.base_fov + (speed_ratio * 35.0)
        camera.fov = lerp(camera.fov, target_fov, time.dt * 5)

        self.velocity = self.forward * self.current_speed
        self.position += self.velocity * time.dt
        self.session_distance += self.current_speed * time.dt
        if hasattr(self, 'mission_manager'):
            self.mission_manager.set_mission_progress('sec_03', int(self.session_distance))

        if is_boosting:
            target_scale_z = random.uniform(3.5, 4.8)
            t_color = self.color_boost
        elif held_keys['w']:
            target_scale_z = random.uniform(1.3, 1.6)
            t_color = self.color_w
        elif held_keys['s']:
            target_scale_z = 0.15
            t_color = self.color_s
        else:
            target_scale_z = random.uniform(0.3, 0.5)
            t_color = self.color_idle

        for t in self.thrusters:
            t.scale_z = lerp(t.scale_z, target_scale_z, time.dt * 12)
            if t.color != t_color:
                t.color = t_color

            if is_boosting or held_keys['w']:
                t.scale_x = lerp(t.scale_x, self.base_thruster_scale[0] * 1.2, time.dt * 20)
                t.scale_y = lerp(t.scale_y, self.base_thruster_scale[1] * 1.2, time.dt * 20)
            else:
                t.scale_x = lerp(t.scale_x, self.base_thruster_scale[0], time.dt * 10)
                t.scale_y = lerp(t.scale_y, self.base_thruster_scale[1], time.dt * 10)

        if self.dash_timer > 0: self.dash_timer -= time.dt

        if self.is_dashing:
            self.dash_time_left -= time.dt
            self.position += self.right * self.dash_direction * self.dash_speed * time.dt
            self.generate_trail()
            self.generate_trail()
            if self.dash_time_left <= 0:
                self.is_dashing = False
                self.dash_roll = 0

        if not is_boosting:
            if self.boost_timer > 0:
                self.boost_timer -= time.dt
            else:
                self.boost_fuel += 30 * time.dt
        self.boost_fuel = clamp(self.boost_fuel, 0, self.max_boost)
        self.boost_bar.scale_x = self.boost_fuel / self.max_boost

        display_speed = int(abs(self.current_speed) * 20)
        display_speed_str = str(display_speed)
        if self.speedometer.text != display_speed_str:
            self.speedometer.text = display_speed_str
        self.tacho_needle.rotation_z = -130 + (speed_ratio * 260)

        # OPTIMIZACIÓN: Tacómetro sin lag
        new_tacho_c = color.red if speed_ratio > 0.8 else color.hex('#ff3333')
        if self.tacho_needle.color != new_tacho_c:
            self.tacho_needle.color = new_tacho_c
            self.speedometer.color = color.orange if speed_ratio > 0.8 else color.white

        if held_keys['middle mouse']:
            self.camera_pivot.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
            self.camera_pivot.rotation_y = clamp(self.camera_pivot.rotation_y, -90, 90)
            self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, -45, 45)
            target_cam_offset_x = 0
            target_cam_offset_y = 0
        else:
            self.camera_pivot.rotation_y = lerp(self.camera_pivot.rotation_y, 0, time.dt * 10)
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            self.base_pitch -= mouse.velocity[1] * self.mouse_sensitivity
            self.base_pitch = clamp(self.base_pitch, -85, 85)
            
            accel_pitch = 0
            if is_boosting:
                accel_pitch = 8.0
            elif held_keys['w']:
                accel_pitch = 3.0
            elif held_keys['s']:
                accel_pitch = -3.0

            target_pitch = self.base_pitch + accel_pitch
            self.rotation_x = lerp(self.rotation_x, target_pitch, time.dt * 12)
            visual_pitch_offset = self.rotation_x - self.base_pitch
            self.camera_pivot.rotation_x = lerp(self.camera_pivot.rotation_x, -visual_pitch_offset, time.dt * 12)

            target_cam_offset_x = 0
            target_cam_offset_y = 0

        if self.is_dashing: target_cam_offset_x -= self.dash_direction * self.camera_dash_drag
        target_cam_offset_x = clamp(target_cam_offset_x, -1.2, 1.2)
        target_cam_offset_y = clamp(target_cam_offset_y, -0.7, 0.7)
        self.camera_pivot.position = lerp(self.camera_pivot.position, Vec3(target_cam_offset_x, target_cam_offset_y, 0),
                                          time.dt * 18)

        base_z_target = self.rotation_z
        if self.is_barrel_rolling:
            base_z_target = self.rotation_z
        else:
            if held_keys['q']:
                self.rotation_z -= self.roll_speed * time.dt
                self.auto_level_timer = self.auto_level_delay
                base_z_target = self.rotation_z
            elif held_keys['e']:
                self.rotation_z += self.roll_speed * time.dt
                self.auto_level_timer = self.auto_level_delay
                base_z_target = self.rotation_z
            elif held_keys['r']:
                self.rotation_z += self.roll_speed * time.dt
                self.auto_level_timer = self.auto_level_delay
                base_z_target = self.rotation_z
            else:
                target_z = round(self.rotation_z / 360) * 360
                if not held_keys['middle mouse']:
                    target_banking = clamp(mouse.velocity[0] * 350, -self.max_banking_angle, self.max_banking_angle)
                    target_z += target_banking

                if self.auto_level_timer > 0:
                    self.auto_level_timer -= time.dt
                    if not held_keys['middle mouse'] and abs(mouse.velocity[0]) > 0.005:
                        self.rotation_z = lerp(self.rotation_z, target_z, time.dt * 6)
                else:
                    self.rotation_z = lerp(self.rotation_z, target_z, time.dt * self.level_damping)
                base_z_target = target_z

        if self.is_dashing: self.rotation_z = base_z_target + self.dash_roll
        self.camera_pivot.world_rotation_z = 0

        base_cam_pos = self.camera_modes[self.current_cam_index]
        dynamic_z_back = speed_ratio * 4.0

        if self.shake_amount > 0:
            self.shake_amount -= time.dt * self.shake_decay
            self.shake_amount = max(0.0, self.shake_amount)
            camera.x = base_cam_pos[0] + random.uniform(-self.shake_amount, self.shake_amount)
            camera.y = base_cam_pos[1] + random.uniform(-self.shake_amount, self.shake_amount)
        else:
            camera.x = base_cam_pos[0]
            camera.y = base_cam_pos[1]

        if held_keys['c']:
            camera.rotation_y = 180
            camera.z = -base_cam_pos[2] + dynamic_z_back
        else:
            camera.rotation_y = 0
            camera.z = base_cam_pos[2] - dynamic_z_back

        if self.blackhole_timer > 0:
            self.blackhole_timer -= time.dt

        self.fire_timer -= time.dt
        self.heat -= 40 * time.dt
        if not held_keys['left mouse']: self.current_fire_rate = lerp(self.current_fire_rate, self.base_fire_rate,
                                                                      time.dt * 3)
        self.heat = clamp(self.heat, 0, self.max_heat)

        # OPTIMIZACIÓN: Barra de calor segura
        if self.heat > 1:
            if not self.heat_widget.enabled: self.heat_widget.enabled = True
            alpha_val = clamp(self.heat / 20, 0, 1)

            target_bar_color = color.red if self.overheated else color.orange
            if self.heat_bar.color != target_bar_color:
                self.heat_bar.color = target_bar_color

            self.heat_bar.alpha = alpha_val
            self.heat_bar_bg.alpha = alpha_val * (150 / 255)
        else:
            if self.heat_widget.enabled: self.heat_widget.enabled = False

        self.heat_bar.scale_x = self.heat / self.max_heat

        if self.heat >= self.max_heat and not self.overheated:
            self.overheated = True
            self.ai_companion.on_weapon_overheated()
            if not self.overheat_text.enabled: self.overheat_text.enabled = True

        if self.overheated and self.heat <= 20:
            self.overheated = False
            if self.overheat_text.enabled: self.overheat_text.enabled = False

        if held_keys['left mouse'] and not self.overheated and self.fire_timer <= 0:
            true_aim_rotation = Vec3(self.base_pitch, self.rotation_y, self.rotation_z)
            from weapons import DualLaser
            
            laser_dmg = self.laser_level # De 1 a 5 de daño
            pool = getattr(self.game_app, 'pool', None) if hasattr(self, 'game_app') else None
            
            if pool:
                config = AVAILABLE_SHIPS.get(self.ship_id, AVAILABLE_SHIPS["nave1"])
                scale_x, scale_y, scale_z = config.scale
                pool.get_object(DualLaser, self.position, true_aim_rotation, self.forward, self.right, self.up,
                                offset_x=self.right_laser_offset[0] * scale_x, offset_y=self.right_laser_offset[1] * scale_y,
                                offset_z=self.right_laser_offset[2] * scale_z, damage_level=laser_dmg, owner=self,
                                laser_scale=self.laser_scale, target=getattr(self, 'locked_target', None))
                pool.get_object(DualLaser, self.position, true_aim_rotation, self.forward, self.right, self.up,
                                offset_x=self.left_laser_offset[0] * scale_x, offset_y=self.left_laser_offset[1] * scale_y,
                                offset_z=self.left_laser_offset[2] * scale_z, damage_level=laser_dmg, owner=self,
                                laser_scale=self.laser_scale, target=getattr(self, 'locked_target', None))
            else:
                config = AVAILABLE_SHIPS.get(self.ship_id, AVAILABLE_SHIPS["nave1"])
                scale_x, scale_y, scale_z = config.scale
                DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                          offset_x=self.right_laser_offset[0] * scale_x, offset_y=self.right_laser_offset[1] * scale_y,
                          offset_z=self.right_laser_offset[2] * scale_z, damage_level=laser_dmg, owner=self,
                          laser_scale=self.laser_scale, target=getattr(self, 'locked_target', None))
                DualLaser(self.position, true_aim_rotation, self.forward, self.right, self.up,
                          offset_x=self.left_laser_offset[0] * scale_x, offset_y=self.left_laser_offset[1] * scale_y,
                          offset_z=self.left_laser_offset[2] * scale_z, damage_level=laser_dmg, owner=self,
                          laser_scale=self.laser_scale, target=getattr(self, 'locked_target', None))

            self.shake_amount = clamp(self.shake_amount + 0.2, 0, 0.6)
            
            heat_cost = max(3, 8 - self.laser_level) # De 7 (nivel 1) baja hasta 3 (nivel 5)
            self.heat += heat_cost
            
            min_rate = self.min_fire_rate if self.laser_level < 5 else max(0.05, self.min_fire_rate - 0.04)
            self.current_fire_rate = max(min_rate, self.current_fire_rate - 0.05)
            self.fire_timer = self.current_fire_rate

    def input(self, key):
        if self.is_dead or (self.is_cinematic and not getattr(self.tactical_map, 'is_open', False)): return

        if key == 'v':
            self.current_cam_index += 1
            if self.current_cam_index >= len(self.camera_modes):
                self.current_cam_index = 0
            camera.position = self.camera_modes[self.current_cam_index]
        if key == 'd' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(-1)
        if key == 'a' and self.dash_timer <= 0 and self.boost_fuel >= 15:
            self.start_dash(1)
        if key == 'x':
            # 1. Comprobar misiones
            target = getattr(self, 'mission_manager', None) and self.mission_manager.get_active_target()
            if target and (self.world_position - target).length_squared() < 10000: # 100 metros de distancia al cuadrado
                if hasattr(self, 'planet_cinematic') and not self.planet_cinematic.is_playing:
                    self.planet_cinematic.play()
                return

            # 2. Comportamiento normal del escáner
            if getattr(self.scanner, 'active', False):
                if not self.scanner_warning or not self.scanner_warning.enabled:
                    self.scanner_warning = Text(text="No puedes hacer eso, ya hay un escaneo en proceso", position=(0, -0.3), origin=(0,0), scale=1.5, color=color.red)
                    destroy(self.scanner_warning, delay=2.0)
            else:
                self.scanner.toggle()
        if key == 'u':
            if not self.is_dead and not self.is_cinematic and not self.pause_menu_open and not getattr(self.tactical_map, 'is_open', False) and not getattr(self.inventory, 'is_open', False):
                self.upgrades_ui.toggle()
        if key == '1':
            if not self.is_dead and hasattr(self, 'inventory'):
                if self.shield >= self.max_shield:
                    if not hasattr(self, 'heal_warning') or not self.heal_warning.enabled:
                        self.heal_warning = Text(text="Integridad estructural al máximo", position=(0, -0.3), origin=(0,0), scale=1.5, color=color.orange)
                        destroy(self.heal_warning, delay=1.5)
                elif self.inventory.logic.items.get("Kit de Reparación", 0) > 0:
                    # Heal 35%
                    self.inventory.logic.remove_item("Kit de Reparación", 1)
                    heal_amount = self.max_shield * 0.35
                    self.repair_shield(heal_amount)
                    
                    # Mostrar texto de sanación
                    if not hasattr(self, 'heal_text') or not self.heal_text.enabled:
                        self.heal_text = Text(text="+35% Integridad", position=(0, -0.3), origin=(0,0), scale=2.0, color=color.lime)
                        destroy(self.heal_text, delay=1.5)
                else:
                    if not hasattr(self, 'heal_warning') or not self.heal_warning.enabled:
                        self.heal_warning = Text(text="No tienes Kits de Reparación", position=(0, -0.3), origin=(0,0), scale=1.5, color=color.red)
                        destroy(self.heal_warning, delay=1.5)
        if key == 'r':
            if not self.is_barrel_rolling and not self.is_dead:
                self.start_barrel_roll()
        if key == 'mouse4' or key == 'mouse5':
            if self.blackhole_timer <= 0:
                # TODO: Requerir costo de Materia Oscura y otro mineral en el futuro
                from weapons import BlackHoleProjectile
                BlackHoleProjectile(self.position, camera.forward)
                self.blackhole_timer = self.blackhole_cooldown
            else:
                if not hasattr(self, 'cooldown_warning') or not self.cooldown_warning.enabled:
                    self.cooldown_warning = Text(text="Espera a que el Cañón de Antimateria se enfríe.", position=(0, -0.3), origin=(0,0), scale=1.5, color=color.orange)
                    destroy(self.cooldown_warning, delay=2.0)