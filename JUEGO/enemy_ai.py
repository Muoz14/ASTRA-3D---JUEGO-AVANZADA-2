import random
import time
from ursina import Vec3, lerp, distance, scene

def smooth_look_at(entity, target_pos, speed=5):
    import time
    from ursina import Entity
    if not hasattr(smooth_look_at, 'dummy'):
        smooth_look_at.dummy = Entity(enabled=False)
        
    smooth_look_at.dummy.position = entity.position
    smooth_look_at.dummy.rotation = entity.rotation
    smooth_look_at.dummy.look_at(target_pos)
    
    def clerp(a, b, t):
        return a + ((b - a + 180) % 360 - 180) * t
        
    entity.rotation_x = clerp(entity.rotation_x, smooth_look_at.dummy.rotation_x, time.dt * speed)
    entity.rotation_y = clerp(entity.rotation_y, smooth_look_at.dummy.rotation_y, time.dt * speed)
    entity.rotation_z = clerp(entity.rotation_z, smooth_look_at.dummy.rotation_z, time.dt * speed)

# ==========================================
# MOTOR DE BEHAVIOR TREES (ARBOLES DE COMPORTAMIENTO)
# ==========================================

class NodeStatus:
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

class Blackboard:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value

class BTNode:
    def tick(self, entity, blackboard):
        raise NotImplementedError("Tick method must be implemented by subclasses.")

# --- COMPOSITES ---
class Selector(BTNode):
    def __init__(self, children):
        self.children = children
        
    def tick(self, entity, blackboard):
        for child in self.children:
            status = child.tick(entity, blackboard)
            if status != NodeStatus.FAILURE:
                return status
        return NodeStatus.FAILURE

class Sequence(BTNode):
    def __init__(self, children):
        self.children = children
        self.current_idx = 0
        
    def tick(self, entity, blackboard):
        if not self.children:
            return NodeStatus.SUCCESS
            
        while self.current_idx < len(self.children):
            status = self.children[self.current_idx].tick(entity, blackboard)
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            elif status == NodeStatus.FAILURE:
                self.current_idx = 0
                return NodeStatus.FAILURE
            self.current_idx += 1
            
        self.current_idx = 0
        return NodeStatus.SUCCESS

class Parallel(BTNode):
    def __init__(self, children):
        self.children = children
        
    def tick(self, entity, blackboard):
        any_running = False
        any_success = False
        for child in self.children:
            status = child.tick(entity, blackboard)
            if status == NodeStatus.RUNNING:
                any_running = True
            elif status == NodeStatus.SUCCESS:
                any_success = True
        
        if any_running:
            return NodeStatus.RUNNING
        if any_success:
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

# --- DECORATORS ---
class Inverter(BTNode):
    def __init__(self, child):
        self.child = child
        
    def tick(self, entity, blackboard):
        status = self.child.tick(entity, blackboard)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status

class Cooldown(BTNode):
    def __init__(self, cooldown_time, child):
        self.cooldown_time = cooldown_time
        self.child = child
        self.last_execution_time = 0
        
    def tick(self, entity, blackboard):
        current_time = time.time()
        if current_time - self.last_execution_time < self.cooldown_time:
            return NodeStatus.FAILURE
            
        status = self.child.tick(entity, blackboard)
        if status == NodeStatus.SUCCESS:
            self.last_execution_time = current_time
        return status

# --- LEAVES (CONDITIONS & ACTIONS) ---
class Condition(BTNode):
    def __init__(self, condition_func):
        self.condition_func = condition_func
        
    def tick(self, entity, blackboard):
        if self.condition_func(entity, blackboard):
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

class Action(BTNode):
    pass

# ==========================================
# ACCIONES ESPECÍFICAS DEL JUEGO
# ==========================================

class FindTargetAction(Action):
    def __init__(self, detection_radius):
        self.detection_radius = detection_radius
        
    def tick(self, entity, blackboard):
        closest_target = None
        closest_dist = float('inf')
        my_faction = getattr(entity, 'faction', 'unknown')
        
        # 1. Comprobar jugador primero (alta prioridad)
        player = getattr(entity, 'player', None)
        if player and not getattr(player, 'is_dead', True):
            dist = distance(entity.position, player.position)
            if dist <= self.detection_radius:
                closest_target = player
                closest_dist = dist
                
        # 2. Comprobar otras naves en la escena (SOLO si no encontramos al jugador, o el jugador está muy lejos)
        if not closest_target:
            for e in scene.entities:
                if type(e).__name__ == "EnemyShip" and e != entity:
                    # Los NPCs no atacan, así que no buscan objetivo
                    if my_faction == "npc": continue
                    
                    other_faction = getattr(e, 'faction', 'unknown')
                    if my_faction != other_faction:
                        dist = distance(entity.position, e.position)
                        if dist <= self.detection_radius and dist < closest_dist:
                            closest_target = e
                            closest_dist = dist
                        
        if closest_target:
            blackboard.set("has_target", True)
            blackboard.set("target_entity", closest_target)
            blackboard.set("target_pos", closest_target.position)
            return NodeStatus.SUCCESS
        
        blackboard.set("has_target", False)
        return NodeStatus.FAILURE

class DogfightAction(Action):
    def __init__(self, min_dist=150, break_dist=80):
        self.min_dist = min_dist
        self.break_dist = break_dist
        
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
            
        dist = distance(entity.position, target.position)
        is_breaking = getattr(entity, "_is_breaking", False)
        
        if is_breaking:
            import time
            if dist > self.min_dist + 100 or getattr(entity, "_break_timer", 0) <= 0:
                entity._is_breaking = False
            else:
                entity._break_timer -= time.dt
                break_dir = getattr(entity, "_break_dir", entity.up)
                target_pos = entity.position + break_dir * 1000
                smooth_look_at(entity, target_pos, speed=2.0)
                entity.target_speed = getattr(entity, 'boost_max_speed', 100)
                return NodeStatus.RUNNING
                
        # Comprobar si estamos demasiado cerca para iniciar maniobra evasiva
        if dist < self.break_dist:
            entity._is_breaking = True
            entity._break_timer = 2.0
            import random
            dir_to_target = (target.position - entity.position).normalized()
            cross_vec = entity.up if abs(dir_to_target.y) < 0.9 else entity.right
            ortho = dir_to_target.cross(cross_vec).normalized()
            ortho2 = dir_to_target.cross(ortho).normalized()
            offsets = [ortho, -ortho, ortho2, -ortho2]
            entity._break_dir = random.choice(offsets)
            
            target_pos = entity.position + entity._break_dir * 1000
            smooth_look_at(entity, target_pos, speed=2.0)
            entity.target_speed = getattr(entity, 'boost_max_speed', 100)
            return NodeStatus.RUNNING
            
        # Combate normal: apuntar al jugador
        smooth_look_at(entity, target.position, speed=3.0)
        
        if dist > self.min_dist:
            # Lejos, acercarse a toda velocidad
            entity.target_speed = entity.config.max_speed
        else:
            # En zona óptima de disparo, reducir un poco la velocidad para ganar más tiempo de tiro
            entity.target_speed = entity.config.max_speed * 0.4
            
        return NodeStatus.RUNNING

class MaintainDistanceAction(Action):
    def __init__(self, min_distance=800, max_distance=1200):
        self.min_dist = min_distance
        self.max_dist = max_distance
        
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
            
        dist = distance(entity.position, target.position)
        
        # Orientarse hacia el target suavemente
        smooth_look_at(entity, target.position, speed=1.0)
        
        if dist < self.min_dist:
            # Muy cerca, retroceder (velocidad negativa)
            entity.target_speed = -getattr(entity, 'max_speed', 50)
        elif dist > self.max_dist:
            # Muy lejos, avanzar
            entity.target_speed = getattr(entity, 'max_speed', 50)
        else:
            # En zona óptima, frenar
            entity.target_speed = 0
            
        return NodeStatus.RUNNING

class ChaseTargetAction(Action):
    def __init__(self, stop_distance):
        self.stop_distance = stop_distance
        
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
            
        dist = distance(entity.position, target.position)
        
        # Orientarse hacia el target suavemente
        smooth_look_at(entity, target.position, speed=3.0)
        
        if dist <= self.stop_distance:
            entity.target_speed = 0 # Frena si esta muy cerca
            return NodeStatus.SUCCESS # Ya esta lo suficientemente cerca
        
        entity.target_speed = entity.config.max_speed
        return NodeStatus.RUNNING

class AttackAction(Action):
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
            
        # Si está muy caliente, falla (debe evadir o esperar)
        if getattr(entity, 'heat', 0) >= getattr(entity, 'max_heat', 100):
            return NodeStatus.FAILURE
            
        # Disparar si el arma está lista
        if entity.fire_cooldown <= 0:
            entity.shoot()
            entity.fire_cooldown = entity.fire_rate
            # Consume calor
            if hasattr(entity, 'heat'):
                entity.heat += 20.0
            return NodeStatus.SUCCESS
            
        return NodeStatus.RUNNING

class EvadeAction(Action):
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        
        # Necesita boost_fuel para hacer un dash evasivo
        fuel = getattr(entity, 'boost_fuel', 0)
        if fuel < 30.0:
            return NodeStatus.FAILURE # No puede evadir
            
        # Orientarse hacia otro lado o usar strafe
        if target:
            # Aleatoria izquierda o derecha
            dir = entity.right if random.choice([True, False]) else -entity.right
            entity.position += dir * getattr(entity, 'boost_max_speed', 100) * time.dt
            
        entity.boost_fuel -= 30.0 # Consume fuel
        return NodeStatus.SUCCESS

class KamikazeAction(Action):
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
        if getattr(entity, "_kamikaze_failed", False):
            return NodeStatus.FAILURE
            
        import time
        if not hasattr(entity, "_kamikaze_timer"):
            entity._kamikaze_timer = 4.0 # 4 seconds to hit target
            
        entity._kamikaze_timer -= time.dt
        if entity._kamikaze_timer <= 0:
            entity._kamikaze_failed = True
            # Regresa al combate normal al fallar
            return NodeStatus.FAILURE
            
        # Se lanza directo ignorando armas y calor, usando boost
        smooth_look_at(entity, target.position, speed=3.0)
        entity.target_speed = getattr(entity, 'boost_max_speed', 100)
        
        # Si choca
        if distance(entity.position, target.position) < 5:
            # Hacer daño y destruirse (esto debería implementarse en la lógica de colisiones idealmente)
            if hasattr(target, 'take_damage'):
                target.take_damage(50)
            if hasattr(entity, 'explode'):
                entity.explode()
            else:
                entity.is_dead = True
                from ursina import destroy
                destroy(entity)
            return NodeStatus.SUCCESS
            
        return NodeStatus.RUNNING

class PatrolAction(Action):
    def __init__(self, patrol_radius):
        self.patrol_radius = patrol_radius
        
    def tick(self, entity, blackboard):
        target_waypoint = blackboard.get("patrol_waypoint")
        
        # Generar nuevo waypoint si no hay
        if not target_waypoint:
            origin = blackboard.get("spawn_point", Vec3(0,0,0))
            offset = Vec3(random.uniform(-self.patrol_radius, self.patrol_radius),
                          random.uniform(-self.patrol_radius, self.patrol_radius),
                          random.uniform(-self.patrol_radius, self.patrol_radius))
            target_waypoint = origin + offset
            blackboard.set("patrol_waypoint", target_waypoint)
            
        if distance(entity.position, target_waypoint) < 5:
            blackboard.set("patrol_waypoint", None)
            entity.target_speed = 0
            return NodeStatus.SUCCESS
            
        # Moverse al waypoint
        smooth_look_at(entity, target_waypoint, speed=3.0)
        entity.target_speed = entity.config.max_speed * 0.5 # Patrulla a media velocidad
        return NodeStatus.RUNNING

# --- ACCIONES DEL JEFE (NODRIZA) ---

class SpawnMinionsAction(Action):
    def __init__(self, minion_id, count):
        self.minion_id = minion_id
        self.count = count
        
    def tick(self, entity, blackboard):
        # Spawnea secuencialmente naves desde su "helipuerto"
        if hasattr(entity, 'spawn_minions'):
            entity.spawn_minions(self.minion_id, self.count)
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

class ChargeHomingLaserAction(Action):
    def tick(self, entity, blackboard):
        target = blackboard.get("target_entity")
        if not target:
            return NodeStatus.FAILURE
            
        # Apunta y dispara el Homing Laser (se implementará en la entidad)
        if hasattr(entity, 'fire_homing_laser'):
            entity.fire_homing_laser(target)
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE

# ==========================================
# ARBOLES PREFABRICADOS
# ==========================================

def build_basic_fighter_tree(detection_radius=1000):
    return Selector([
        Sequence([
            FindTargetAction(detection_radius=detection_radius),
            Selector([
                # 1. Kamikaze si la salud es muy baja (< 20%) y no ha fallado el intento
                Sequence([
                    Condition(lambda e, b: getattr(e, 'health', 0) < getattr(e, 'max_health', 100) * 0.2 and not getattr(e, '_kamikaze_failed', False)),
                    KamikazeAction()
                ]),
                # 2. Evadir si está sobrecalentado o muy cerca
                Sequence([
                    Condition(lambda e, b: getattr(e, 'heat', 0) > 80 or distance(e.position, b.get("target_entity").position) < 30),
                    EvadeAction()
                ]),
                # 3. Combate normal (Moverse y Atacar en paralelo)
                Parallel([
                    # Movimiento: mantener distancia segura
                    DogfightAction(min_dist=150, break_dist=80),
                    # Ataque: si está a menos de 800 de distancia, ataca
                    Sequence([
                        Condition(lambda e, b: distance(e.position, b.get("target_entity").position) < 800),
                        AttackAction()
                    ])
                ])
            ])
        ]),
        PatrolAction(patrol_radius=800)
    ])

def build_boss_tree():
    return Selector([
        Sequence([
            FindTargetAction(detection_radius=6000),
            Selector([
                Cooldown(15.0, SpawnMinionsAction("nave-altech-enemy", 3)),
                Cooldown(8.0, ChargeHomingLaserAction()),
                Parallel([
                    MaintainDistanceAction(min_distance=800, max_distance=1200),
                    Sequence([
                        Condition(lambda e, b: distance(e.position, b.get("target_entity").position) < 1500),
                        AttackAction()
                    ])
                ])
            ])
        ]),
        PatrolAction(patrol_radius=300)
    ])

def build_npc_tree():
    """
    Árbol de comportamiento para NPCs neutrales.
    Si detectan una amenaza (FindTargetAction encuentra a alguien de otra facción), huyen.
    """
    return Selector([
        Sequence([
            FindTargetAction(detection_radius=1500),
            # Si encuentra a alguien, huye (usa Evade para hacer dashes constantes y alejarse)
            EvadeAction()
        ]),
        PatrolAction(patrol_radius=8000)
    ])
