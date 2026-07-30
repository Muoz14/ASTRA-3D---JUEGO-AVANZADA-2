import random
import time
from ursina import *
from enemy_ships import ENEMY_SHIPS
from enemy_ai import build_basic_fighter_tree, build_boss_tree, build_npc_tree, Blackboard, NodeStatus
from weapons import DualLaser

class EnemyShip(Entity):
    def __init__(self, ship_id, spawn_position, game_app, is_boss=False, is_npc=False, is_minion=False, **kwargs):
        super().__init__(model=None, position=spawn_position, **kwargs)
        self.game = game_app
        self.is_boss = is_boss
        self.is_npc = is_npc
        self.is_minion = is_minion
        
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
        
        from ursina import BoxCollider, Vec3
        # Adjust collider size to be slightly smaller than the visual scale for fair gameplay
        size = Vec3(self.config.scale[0] * 0.8, self.config.scale[1] * 0.8, self.config.scale[2] * 0.8)
        self.collider = BoxCollider(self, center=Vec3(0,0,0), size=size)
        
        # Stats
        self.max_health = getattr(self.config, 'max_health', 100)
        self.health = self.max_health
        self.max_speed = getattr(self.config, 'max_speed', 50)
        self.boost_max_speed = getattr(self.config, 'boost_max_speed', 100)
        self.acceleration = getattr(self.config, 'acceleration', 2)
        self.friction = getattr(self.config, 'friction', 1)
        
        self.target_speed = 0
        self.current_speed = 0
        
        self.fire_rate = 1.0 # Dispara cada 1 segundo (ajustable)
        self.fire_cooldown = 0
        
        # Nuevas mecánicas tácticas
        self.max_heat = 100.0
        self.heat = 0.0
        self.max_boost_fuel = 100.0
        self.boost_fuel = 100.0
        
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
        
        # Behavior Tree Setup
        self.blackboard = Blackboard()
        self.blackboard.set("spawn_point", spawn_position)
        
        if self.is_boss:
            self.bt = build_boss_tree()
        elif self.is_npc:
            self.bt = build_npc_tree()
        elif self.is_minion:
            self.bt = build_basic_fighter_tree(detection_radius=15000) # Nunca nos pierde de vista
        else:
            self.bt = build_basic_fighter_tree(detection_radius=1000) # Vagan por el espacio si nos alejamos mucho
            
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
        for e in scene.entities:
            if type(e).__name__ == "EnemyShip" and e != self:
                if getattr(e, 'faction', None) == self.faction:
                    if distance(self.position, e.position) <= radius:
                        allies.append(e)
        return allies
        
    def shoot(self):
        # Utiliza DualLaser de weapons.py (sin costo de calor ya que es enemigo)
        for offset in self.config.laser_offsets:
            DualLaser(self.position, self.rotation, self.forward, self.right, self.up,
                      offset_x=offset[0] * self.config.scale[0], 
                      offset_y=offset[1] * self.config.scale[1],
                      offset_z=offset[2] * self.config.scale[2], 
                      damage_level=1, owner=self, 
                      laser_scale=(0.2, 0.2, 2.0), laser_color=self.config.laser_color)
                      
    def spawn_minions(self, minion_id, count):
        # Spawnea secuencialmente naves desde su "helipuerto" (centro / abajo)
        for i in range(count):
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
            
        destroy(self)

    def update(self):
        if getattr(self, 'is_dead', False):
            return
            
        # Despawn automático para NPCs que se alejan demasiado
        if self.is_npc and hasattr(self, 'game') and hasattr(self.game, 'player'):
            dist = (self.position - self.game.player.position).length()
            if dist > self.game.player.sector_radius:
                destroy(self)
                return

        # Tick del Behavior Tree
        if hasattr(self.game, 'player') and self.game.player:
            self.player = self.game.player
        else:
            self.player = None
            
        self.bt.tick(self, self.blackboard)
        if getattr(self, 'is_dead', False):
            return
        
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
            if not hasattr(self, 'trail_timer'): self.trail_timer = 0
            self.trail_timer -= time.dt
            if self.trail_timer <= 0:
                self.generate_trail()
                self.trail_timer = 0.15 # Emitir estelas solo ~6 veces por segundo en lugar de 60
            
            # Animar propulsores visuales
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, self.config.thruster_scale[2] + random.uniform(0.1, 0.3), time.dt * 10)
        else:
            for t in self.thrusters:
                t.scale_z = lerp(t.scale_z, self.config.thruster_scale[2], time.dt * 5)
