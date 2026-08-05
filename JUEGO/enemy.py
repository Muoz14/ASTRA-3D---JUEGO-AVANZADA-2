import random
import time
import random
import time
from ursina import *
from enemy_ships import ENEMY_SHIPS
from enemy_ai import build_basic_fighter_tree, build_boss_tree, build_npc_tree, Blackboard, NodeStatus
from weapons import DualLaser

class EnemyShip(Entity):
    active_ships = []

    def __init__(self, ship_id, spawn_position, game_app, is_boss=False, is_npc=False, is_minion=False, is_leader=False, is_wingman=False, squadron_id=None, force_detection=False, **kwargs):
        super().__init__(model=None, position=spawn_position, **kwargs)
        self.game = game_app
        self.is_boss = is_boss
        self.is_npc = is_npc
        self.is_minion = is_minion
        self.is_leader = is_leader
        self.is_wingman = is_wingman
        self.squadron_id = squadron_id
        
        # Modo actor para cinemáticas (se saltan la IA de ataque y seguimiento)
        self.is_cinematic_actor = False
        
        # Intentar cargar de ENEMY_SHIPS primero, si no, de AVAILABLE_SHIPS (para NPCs)
        self.config = ENEMY_SHIPS.get(ship_id)
        if not self.config:
            from ships import AVAILABLE_SHIPS
            self.config = AVAILABLE_SHIPS.get(ship_id)
            if not self.config:
                print(f"Error: Enemy ship config {ship_id} not found!")
                return
            
        # La entidad principal tiene escala 1. La escala real se aplica al modelo visual
        # para que las matemáticas de offsets funcionen exactamente igual que en el Tuner.
        self.scale = (1, 1, 1)
        self.visual = Entity(parent=self, model=self.config.model, scale=self.config.scale, rotation=getattr(self.config, 'model_rotation_offset', (0,0,0)))
        
        from ursina import SphereCollider, Vec3
        # Use SphereCollider for extremely robust hit detection regardless of ship orientation
        self.collider = SphereCollider(self, center=Vec3(0,0,0), radius=5.5)
        
        # Stats
        self.max_health = getattr(self.config, 'max_health', 100)
        self.health = self.max_health
        self.max_speed = getattr(self.config, 'max_speed', 50)
        self.boost_max_speed = getattr(self.config, 'boost_max_speed', 100)
        self.acceleration = getattr(self.config, 'acceleration', 2)
        self.friction = getattr(self.config, 'friction', 1)
        
        self.target_speed = 0
        self.current_speed = 0
        
        self.fire_rate = 0.35 # Dispara cada 0.35 segundos (más agresivo)
        self.fire_cooldown = 0
        
        self.max_heat = 100.0
        self.heat = 0.0
        
        # Throttling IA: 15 FPS para lógica pesada en lugar de 60 FPS
        self.ai_timer = random.uniform(0, 0.1)
        self.ai_interval = 1.0 / 15.0
        
        self.player = None
        self.max_boost_fuel = 100.0
        self.boost_fuel = 100.0
        
        EnemyShip.active_ships.append(self)
        
        # Determinar facción
        if self.is_npc:
            self.faction = "npc"
        elif "alien" in ship_id:
            self.faction = "alien"
        elif "altech" in ship_id or self.is_boss:
            self.faction = "altech"
        else:
            self.faction = "unknown"
        
        self.thrusters = []
        self._setup_thrusters()
        
        # Marcador visual sobre la nave para no perderla de vista
        # Un diamante brillante que siempre mira a la cámara (billboard=True)
        if not self.is_npc:
            self.visual_marker = Entity(parent=scene, model='sphere', color=color.red, scale=0.8, unlit=True, billboard=True)
        
        # Behavior Tree Setup
        self.blackboard = Blackboard()
        self.blackboard.set("spawn_point", spawn_position)
        
        if self.is_boss:
            self.bt = build_boss_tree()
        elif self.is_npc:
            self.bt = build_npc_tree()
        else:
            # Si estamos en el Lote 3 y la batalla Altech ha comenzado, forzar detección constante
            mm = getattr(self.game.player, 'mission_manager', None) if hasattr(self.game, 'player') else None
            is_altech_battle = mm and getattr(mm, 'current_batch', 0) == 3 and getattr(mm, 'altech_squad_spawned', False)
            
            if self.is_minion or force_detection or is_altech_battle:
                self.bt = build_basic_fighter_tree(detection_radius=15000) # Nunca nos pierde de vista
            else:
                self.bt = build_basic_fighter_tree(detection_radius=250) # Detectan al jugador solo a 250m de distancia
            
        # Para evitar un "instakill volley" masivo tras la cinemática, retrasamos el primer disparo
        if force_detection:
            self.fire_cooldown = random.uniform(3.0, 7.0)
            if self.is_leader:
                self.fire_cooldown = 4.0
            
    def _setup_thrusters(self):
        for offset in self.config.thruster_offsets:
            t_scale = self.config.thruster_scale
            scaled_offset = (offset[0] * self.config.scale[0], offset[1] * self.config.scale[1], offset[2] * self.config.scale[2])
            # Creamos un propulsor visual sencillo para los enemigos (versión anterior no-masiva)
            t = Entity(parent=self, model='sphere', unlit=True, color=self.config.thruster_color,
                       scale=(t_scale[0], t_scale[1], t_scale[2]),
                       position=scaled_offset)
            self.thrusters.append(t)
            
    def generate_trail(self):
        base_color = self.config.thruster_color
        trail_color = color.rgba(base_color.r * 255, base_color.g * 255, base_color.b * 255, 100)
        
        # VERSIÓN ANTERIOR: Partículas simples, sin la dispersión masiva del jugador
        for offset in self.config.thruster_offsets:
            scaled_offset = (offset[0] * self.config.scale[0], offset[1] * self.config.scale[1], offset[2] * self.config.scale[2])
            p = Entity(parent=self.game.scene if hasattr(self.game, 'scene') else scene, 
                       model='sphere', color=trail_color, unlit=True,
                       scale=random.uniform(0.06, 0.12) * self.config.scale[0], position=self.world_position + self.forward * scaled_offset[2] + self.right * scaled_offset[0] + self.up * scaled_offset[1])
            # Dispersión normal hacia atrás
            p.animate_position(p.position + (-self.forward * 2.0), duration=0.25, curve=curve.linear)
            p.animate_scale(0, duration=0.25, curve=curve.linear)
            destroy(p, delay=0.25)
            
    def get_nearby_allies(self, radius=800):
        allies = []
        for e in EnemyShip.active_ships:
            if e != self and not getattr(e, 'is_dead', False):
                if getattr(e, 'faction', None) == self.faction:
                    if distance(self.position, e.position) <= radius:
                        allies.append(e)
        return allies
        
    def shoot(self):
        # Calcular dirección hacia el jugador para mejorar la precisión (con dispersión para no ser aimbot)
        aim_rot = self.rotation
        if getattr(self, 'player', None):
            from ursina import Entity, Vec3
            dummy = Entity(position=self.position)
            
            # Error aleatorio mínimo (Casi AimBot) para obligar al jugador a usar dashes
            err_range = 1.0 # Reducido de 2.5 a 1.0
            
            # La nodriza ahora tiene precisión perfecta a medida que pierde salud
            if getattr(self, 'is_boss', False):
                health_percent = getattr(self, 'health', 1) / max(getattr(self, 'max_health', 1), 1)
                err_range = 0.8 * health_percent # De 0.8 baja a 0.0
                
            error_offset = Vec3(random.uniform(-err_range, err_range), random.uniform(-err_range, err_range), random.uniform(-err_range, err_range))
            
            # Apuntar hacia el jugador con el error añadido
            dummy.look_at(self.player.position + error_offset)
            aim_rot = dummy.rotation
            destroy(dummy)

        if hasattr(self, 'game') and hasattr(self.game, 'audio_manager'):
            self.game.audio_manager.play_enemy_laser()

        pool = getattr(self.game, 'pool', None) if hasattr(self, 'game') else None
        
        # Utiliza DualLaser de weapons.py
        for offset in self.config.laser_offsets:
            if pool:
                pool.get_object(DualLaser, self.position, aim_rot, self.forward, self.right, self.up,
                          offset_x=offset[0] * self.config.scale[0], 
                          offset_y=offset[1] * self.config.scale[1],
                          offset_z=offset[2] * self.config.scale[2], 
                          damage_level=12, owner=self, 
                          laser_scale=(0.2, 0.2, 2.0), laser_color=self.config.laser_color, pool=pool)
            else:
                DualLaser(self.position, aim_rot, self.forward, self.right, self.up,
                          offset_x=offset[0] * self.config.scale[0], 
                          offset_y=offset[1] * self.config.scale[1],
                          offset_z=offset[2] * self.config.scale[2], 
                          damage_level=12, owner=self, 
                          laser_scale=(0.2, 0.2, 2.0), laser_color=self.config.laser_color)
                      
    def spawn_minions(self, minion_id, count):
        from ursina import scene
        current_minions = sum(1 for e in scene.entities if type(e).__name__ == 'EnemyShip' and getattr(e, 'is_boss', False) == False)
        
        if current_minions >= 14:
            return
            
        allowed_count = min(count, 14 - current_minions)
        
        # Spawnea secuencialmente naves desde su "helipuerto" (centro / abajo)
        for i in range(allowed_count):
            spawn_pos = self.world_position + self.down * 5 * self.config.scale[1] + self.right * random.uniform(-10, 10)
            # Invoke el constructor de la nave, asegurando que se añade al juego
            minion = EnemyShip(minion_id, spawn_pos, self.game, is_boss=False, is_minion=True)
            
    def fire_homing_laser(self, target):
        # A desarrollar después: el super láser teledirigido.
        # Por ahora, simplemente dispara una ráfaga masiva hacia adelante
        self.shoot()
        self.shoot()
        self.shoot()
            
    def take_damage(self, amount):
        self.health -= amount
        # Flash rojo al recibir daño
        self.visual.color = color.red
        invoke(setattr, self.visual, 'color', color.white, delay=0.1)
        
        # Si reciben daño, te detectan a ti y avisan a todas las naves aliadas cercanas
        self.has_detected_player = True
        for e in EnemyShip.active_ships:
            if e != self and not getattr(e, 'is_dead', False) and getattr(e, 'faction', 'unknown') == getattr(self, 'faction', 'unknown'):
                if distance(self.position, e.position) <= 500: # Rango ajustado a 500m
                    e.has_detected_player = True
        
        if self.health <= 0:
            self.explode()
            
    def explode(self):
        self.is_dead = True
        # Partículas de explosión
        for _ in range(15 if not self.is_boss else 50):
            p = Entity(parent=scene, model='sphere', color=color.orange, unlit=True,
                       position=self.world_position + Vec3(random.uniform(-2,2), random.uniform(-2,2), random.uniform(-2,2)) * self.config.scale[0],
                       scale=random.uniform(0.5, 2.0) * self.config.scale[0])
            p.animate_position(p.position + Vec3(random.uniform(-5,5), random.uniform(-5,5), random.uniform(-5,5)) * self.config.scale[0], duration=0.5, curve=curve.out_expo)
            p.animate_scale(0, duration=0.5, curve=curve.linear)
            destroy(p, delay=0.5)
            
        if hasattr(self, 'visual_marker') and self.visual_marker:
            destroy(self.visual_marker)
            
        # Actualizar misiones si muere una nave enemiga
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'mission_manager') and getattr(self, 'faction', None) != 'npc':
            mm = self.game.player.mission_manager
            if not self.is_boss:
                mm.increment_mission('sec_01')
                mm.increment_mission('sec_04')
                mm.increment_mission('sec_07')
                
                # Check for Altech Squad
                if getattr(mm, 'current_batch', 0) == 3 and getattr(mm, 'altech_squad_spawned', False) and not getattr(mm, 'altech_wreck_spawned', False):
                    mm.altech_squad_kills += 1
                    # Si el líder muere Y ya hemos matado a 45 naves, spawneamos la chatarra
                    if self.is_leader and mm.altech_squad_kills >= 45:
                        if hasattr(self.game, 'spawn_altech_wreck'):
                            self.game.spawn_altech_wreck(self.world_position)
            else:
                mm.complete_mission('main_03')
                
        # Spawn loot (Materiales comunes, preciosos, y raros)
        if hasattr(self.game, 'player'):
            from loot import MeteoriteFragment
            
            num_items = random.randint(1, 3)
            if self.is_boss:
                num_items = random.randint(5, 10)
                
            materials_list = [
                {'name': 'HIERRO (Fe)', 'color': '#a14d26', 'desc': 'Uso Estructural'},
                {'name': 'COBRE (Cu)', 'color': '#28795c', 'desc': 'Conductor Eléctrico'},
                {'name': 'TITANIO (Ti)', 'color': '#5a6578', 'desc': 'Blindaje Pesado'},
                {'name': 'ORO (Au)', 'color': '#c4a627', 'desc': 'Microtecnología'},
                {'name': 'URANIO (U)', 'color': '#4d821a', 'desc': 'Núcleo Combustible'}
            ]
            
            for _ in range(num_items):
                r = random.random()
                if r < 0.95:
                    mat_data = random.choice(materials_list)
                else:
                    mat_data = {'name': 'ANTIMATERIA (Am)', 'color': '#ff00ff', 'desc': 'Energía Pura Exótica'}
                    
                drop_pos = self.world_position + Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
                item = MeteoriteFragment(self.game.player, drop_pos, mat_data)
            
        destroy(self)

    def on_destroy(self):
        if hasattr(self, 'visual_marker') and self.visual_marker:
            destroy(self.visual_marker)
        if self in EnemyShip.active_ships:
            EnemyShip.active_ships.remove(self)

    def update(self):
        if getattr(self, 'is_dead', False):
            return
            
        self.ai_timer += time.dt
        if self.ai_timer >= self.ai_interval:
            self.ai_timer = 0.0
            
            # Despawn automático si se alejan demasiado
            if hasattr(self, 'game') and hasattr(self.game, 'player') and self.game.player:
                dist = (self.world_position - self.game.player.world_position).length()
                
                # Limite de despawn
                despawn_limit = self.game.player.sector_radius if self.is_npc else 1100
                if getattr(self, 'is_boss', False):
                    despawn_limit = 4000
                    
                if dist > despawn_limit:
                    is_mission_critical = False
                    if getattr(self, 'is_boss', False):
                        is_mission_critical = True
                                
                    if not is_mission_critical:
                        if hasattr(self.game, 'ai_director') and self.game.ai_director.enabled:
                            from ursina import invoke
                            invoke(self.game.ai_director.spawn_squad, 1, delay=0.5)
                        destroy(self)
                        return

            # Tick del Behavior Tree a 15 FPS
            if hasattr(self.game, 'player') and getattr(self.game, 'player', None):
                self.player = self.game.player
            else:
                self.player = None
                
            self.bt.tick(self, self.blackboard)
            if getattr(self, 'is_dead', False):
                return
                
        # CONGELAR IA DURANTE CINEMÁTICAS
        # Si el jugador está viendo una cinemática, los enemigos reales no deben moverse ni atacar
        if getattr(self, 'player', None) and getattr(self.player, 'is_cinematic', False):
            self.target_speed = lerp(self.current_speed, 0, time.dt * 2)
            self.current_speed = lerp(self.current_speed, 0, time.dt * 2)
            return
            
        # Comportamiento especial de IA (Líder / Cinemática)
        if self.is_cinematic_actor:
            # Los actores de cinemática detienen su velocidad gradualmente y no disparan
            self.target_speed = lerp(self.current_speed, 0, time.dt)
            self.fire_cooldown = 1.0 # Nunca disparan
        # Eliminada la lógica de huida del líder para que combata de manera agresiva igual que el resto
            
        # Actualizar posición del marcador visual
        if hasattr(self, 'visual_marker') and self.visual_marker:
            self.visual_marker.position = self.world_position + Vec3(0, self.config.scale[1] * 2 + 5, 0)
            if self.player:
                dist = distance(self.visual_marker.position, self.player.position)
                self.visual_marker.scale = max(0.8, dist / 80.0)
        
        if self.fire_cooldown > 0:
            self.fire_cooldown -= time.dt
            
        # Regenerar tácticas
        if self.heat > 0:
            self.heat = max(0.0, self.heat - 25.0 * time.dt)
        if self.boost_fuel < self.max_boost_fuel:
            self.boost_fuel = min(self.max_boost_fuel, self.boost_fuel + 15.0 * time.dt)
            
        # Movimiento físico con lerp (igual que el jugador)
        lerp_factor = self.acceleration if self.target_speed > self.current_speed else self.friction
        self.current_speed = lerp(self.current_speed, self.target_speed, time.dt * lerp_factor)
        
        self.current_speed = clamp(self.current_speed, -self.max_speed, self.boost_max_speed)
        
        # DEBUG: print speed if fighting
        if hasattr(self, 'bt') and self.target_speed != 0:
            pass # print(f"Speed: {self.current_speed:.2f} / {self.target_speed:.2f}")

        if abs(self.current_speed) > 1.0:
            # Avanza en la dirección a la que mira
            self.position += self.forward * self.current_speed * time.dt
            
            # Limitar la generación de partículas para no saturar el rendimiento
            # DESACTIVADO para enemigos: generar partículas constantemente destruye los FPS cuando hay 10+ naves
            # if not hasattr(self, 'trail_timer'): self.trail_timer = 0
            # self.trail_timer -= time.dt
            # if self.trail_timer <= 0:
            #     self.generate_trail()
            #     self.trail_timer = 0.15
            
            # Animar propulsores visuales
            for t in self.thrusters:
                if self.target_speed > 10:
                    t.scale_z = lerp(t.scale_z, random.uniform(self.config.thruster_scale[2]*1.5, self.config.thruster_scale[2]*2.5), time.dt * 12)
                else:
                    t.scale_z = lerp(t.scale_z, self.config.thruster_scale[2], time.dt * 6)
        else:
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, self.config.thruster_scale[2], time.dt * 5)

class Mothership(EnemyShip):
    def __init__(self, spawn_position, game_app, **kwargs):
        # Usamos la base de boss1-nodriza
        super().__init__("boss1-nodriza", spawn_position, game_app, is_boss=True, **kwargs)
        
        self.max_health = 3000
        self.health = self.max_health
        
        # Escalar 3 veces el tamaño (la escala se propaga a visual y propulsores)
        self.scale = (3, 3, 3)
        
        # Ajustar colisionador a la nueva escala masiva
        from ursina import BoxCollider, Vec3
        # Dado que self.scale = 3 y visual.scale = 50, el tamaño real es gigantesco.
        # size=(60, 20, 80) x 3 = 180x60x240 en el mundo.
        self.collider = BoxCollider(self, center=Vec3(0,0,0), size=Vec3(60, 20, 80))
        
        self.spawn_timer = 20.0
        
        # Diálogos iniciales
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'ai_companion'):
            self.game.player.ai_companion.trigger_dialogue([
                ("Nodriza Altech: Piloto, has interferido demasiado en nuestros planes.", 4.0),
                ("Nodriza Altech: Tu nave y su IA serán asimiladas por nuestra tecnología superior.", 4.5),
                ("IA: Detecto firmas de energía masivas. Precaución extrema.", 3.5),
                ("Tierra: Destruye sus escoltas y ataca el núcleo central. ¡Es nuestra única oportunidad!", 4.5)
            ])
            
    def update(self):
        super().update()
        if getattr(self, 'is_dead', False): return
        
        # Spawneo periódico de minions (cazas)
        self.spawn_timer -= time.dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(20.0, 30.0)
            self.spawn_minions("nave-altech-enemy", 2)
            if hasattr(self.game, 'player') and hasattr(self.game.player, 'ai_companion'):
                self.game.player.ai_companion.trigger_dialogue([
                    ("IA: Alerta. La Nodriza está desplegando cazas de escolta.", 3.0)
                ])
