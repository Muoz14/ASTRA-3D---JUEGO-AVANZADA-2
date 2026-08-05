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
    
    # Prevenir que las naves se pongan de cabeza (bloqueamos el roll a 0 relativo al mundo)
    smooth_look_at.dummy.rotation_z = 0

    
    def clerp_capped(a, b, t, max_turn):
        from ursina import clamp
        diff = ((b - a + 180) % 360 - 180)
        step = diff * t
        step = clamp(step, -max_turn, max_turn)
        return a + step
        
    # Limitar el giro a un máximo de 100 grados por segundo independientemente de la diferencia angular
    max_turn_per_frame = 100.0 * time.dt 
    
    entity.rotation_x = clerp_capped(entity.rotation_x, smooth_look_at.dummy.rotation_x, time.dt * speed, max_turn_per_frame)
    entity.rotation_y = clerp_capped(entity.rotation_y, smooth_look_at.dummy.rotation_y, time.dt * speed, max_turn_per_frame)
    entity.rotation_z = clerp_capped(entity.rotation_z, smooth_look_at.dummy.rotation_z, time.dt * speed, max_turn_per_frame)

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
            
            # Si ya detectó al jugador alguna vez, nunca lo pierde de vista
            already_detected = getattr(entity, 'has_detected_player', False)
            
            if dist <= self.detection_radius or already_detected:
                entity.has_detected_player = True
                closest_target = player
                closest_dist = dist
                
        # 2. Comprobar otras naves en la escena (SOLO si no encontramos al jugador, o el jugador está muy lejos)
        if not closest_target:
            from enemy import EnemyShip
            for e in EnemyShip.active_ships:
                if e != entity and not getattr(e, 'is_dead', False):
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
            
        # EVASIÓN DE OBSTÁCULOS (Prioridad Máxima)
        from ursina import raycast, distance
        
        # 1. Evasión matemática estricta para el planeta gigante (por si spawnean adentro o el raycast falla)
        if hasattr(entity.game, 'environment') and hasattr(entity.game.environment, 'planet'):
            planet = entity.game.environment.planet
            if planet and getattr(planet, 'enabled', True):
                dist_to_planet = distance(entity.world_position, planet.world_position)
                if dist_to_planet < 2200: # El radio real del collider es mayor
                    # Evadir directamente alejándose del centro del planeta
                    avoid_dir = (entity.world_position - planet.world_position).normalized()
                    target_pos = entity.position + avoid_dir * 2500
                    smooth_look_at(entity, target_pos, speed=8.0)
                    entity.target_speed = entity.config.max_speed * 0.4
                    return NodeStatus.RUNNING
                    
                # 1.5 Evasión matemática para asteroides gigantes (chunks)
                if hasattr(planet, 'chunks'):
                    for chunk in planet.chunks.children:
                        chunk_pos = chunk.world_position
                        ast_radius = 150 * chunk.scale_x
                        if distance(entity.world_position, chunk_pos) < ast_radius + 50:
                            avoid_dir = (entity.world_position - chunk_pos).normalized()
                            target_pos = entity.position + avoid_dir * (ast_radius * 2)
                            smooth_look_at(entity, target_pos, speed=9.0)
                            entity.target_speed = entity.config.max_speed * 0.3
                            return NodeStatus.RUNNING

        # 2. Raycast para asteroides y otros obstáculos menores
        hit_info = raycast(entity.world_position, entity.forward, distance=400, ignore=(entity,))
        if hit_info.hit and hit_info.entity != target:
            # Si vamos a chocar, la prioridad absoluta es esquivar
            avoid_dir = hit_info.world_normal
            # Girar agresivamente hacia la normal de la superficie (rebotar visualmente)
            target_pos = entity.position + avoid_dir * 1000
            smooth_look_at(entity, target_pos, speed=8.0)
            entity.target_speed = entity.config.max_speed * 0.3
            return NodeStatus.RUNNING
            
        dist = distance(entity.position, target.position)
        
        # CONCIENCIA DE PROXIMIDAD: Si estamos a más de 900m del jugador, volver hacia él
        player = getattr(entity, 'player', None)
        if player and not getattr(player, 'is_dead', False):
            dist_to_player = distance(entity.world_position, player.world_position)
            if dist_to_player > 900:
                # Cancelar cualquier táctica y volver hacia el jugador
                smooth_look_at(entity, player.position, speed=4.0)
                entity.target_speed = entity.config.max_speed
                entity._tactic = "ENGAGE"  # Forzar modo ataque
                entity._is_breaking = False
                return NodeStatus.RUNNING
        
        is_breaking = getattr(entity, "_is_breaking", False)
        
        import time
        if getattr(entity, "_break_cooldown", 0) > 0:
            entity._break_cooldown -= time.dt

        if is_breaking:
            if dist > self.min_dist + 100 or getattr(entity, "_break_timer", 0) <= 0:
                entity._is_breaking = False
                entity._break_cooldown = 5.0 # Toman el valor de pelear por 5 segundos
            else:
                entity._break_timer -= time.dt
                break_dir = getattr(entity, "_break_dir", entity.up)
                target_pos = entity.position + break_dir * 1000
                smooth_look_at(entity, target_pos, speed=2.0)
                entity.target_speed = getattr(entity, 'boost_max_speed', 100)
                return NodeStatus.RUNNING
                
        # Comprobar si estamos demasiado cerca para iniciar maniobra evasiva
        if not is_breaking and getattr(entity, "_break_cooldown", 0) <= 0 and dist < self.break_dist:
            entity._is_breaking = True
            entity._break_timer = 3.5
            import random
            dir_to_target = (target.position - entity.position).normalized()
            cross_vec = entity.up if abs(dir_to_target.y) < 0.9 else entity.right
            ortho = dir_to_target.cross(cross_vec).normalized()
            ortho2 = dir_to_target.cross(ortho).normalized()
            offsets = [ortho, -ortho, ortho2, -ortho2]
            entity._break_dir = random.choice(offsets)
            
            target_pos = entity.position + entity._break_dir * 1000
            smooth_look_at(entity, target_pos, speed=1.2)
            entity.target_speed = getattr(entity, 'boost_max_speed', 100)
            return NodeStatus.RUNNING
            
        # Combate táctico dinámico
        import random
        if not hasattr(entity, "_tactic_timer") or getattr(entity, "_tactic_timer", 0) <= 0:
            entity._tactic_timer = random.uniform(2.0, 5.0)
            entity._strafe_dir = random.choice([1, -1])
            
            # Elegir táctica de combate aleatoria (MÁS AGRESIVO)
            options = ["ENGAGE", "ENGAGE", "ENGAGE", "FLANK", "FLANK", "REPOSITION"]
            entity._tactic = random.choice(options)
            
            if entity._tactic == "REPOSITION":
                # Irse a un punto cercano (100-250m) para no salirse del rango del jugador
                offsets = [target.forward, target.right, -target.right, target.up, -target.up]
                chosen = random.choice(offsets)
                entity._tactic_target = target.position + chosen * random.uniform(100, 250)
            elif entity._tactic == "FLANK":
                # Atacar desde un flanco (100-300m)
                offsets = [target.right, -target.right, target.up, -target.up, target.forward]
                chosen = random.choice(offsets)
                entity._tactic_target = target.position + chosen * random.uniform(100, 300)
                
        entity._tactic_timer -= time.dt
        
        # Aplicar la táctica actual
        if entity._tactic == "ENGAGE":
            # Combate directo, apuntar al jugador con giro suave
            smooth_look_at(entity, target.position, speed=1.5)
            if dist > self.min_dist:
                entity.target_speed = entity.config.max_speed
            else:
                entity.target_speed = entity.config.max_speed * 0.4 # Frenar un poco al acercarse
                # Strafe ligero
                entity.position += entity.right * (entity._strafe_dir * entity.config.max_speed * 0.3) * time.dt
                
        elif entity._tactic == "REPOSITION":
            # Volar hacia el punto de reposicionamiento, pero ENCARANDO al jugador
            # Calculamos la dirección del movimiento hacia el target
            dir_to_target = (entity._tactic_target - entity.position).normalized()
            entity.position += dir_to_target * (entity.config.max_speed * 0.8) * time.dt
            # Visualmente seguimos apuntando al jugador para disparar y no darle la espalda
            smooth_look_at(entity, target.position, speed=1.5)
            
            # Si llegó al punto o está muy lejos del jugador, cambiar a ENGAGE
            if distance(entity.position, entity._tactic_target) < 100 or dist > 800:
                entity._tactic = "ENGAGE"
                entity._tactic_timer = 4.0
                
        elif entity._tactic == "FLANK":
            # Apuntar hacia el objetivo de flanqueo, pero si estamos cerca del flanco, apuntar al jugador
            dist_to_flank = distance(entity.position, entity._tactic_target)
            if dist_to_flank > 150:
                smooth_look_at(entity, entity._tactic_target, speed=1.0)
            else:
                smooth_look_at(entity, target.position, speed=1.8) # Ya llegamos al flanco, encarar y atacar!
            entity.target_speed = entity.config.max_speed
            
        # Sobrescribir táctica: si el jugador se acerca muchísimo, simplemente volar de frente (pasar de largo) para ganar distancia
        if dist < self.min_dist - 40:
            entity.target_speed = entity.config.max_speed
            
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
            # Muy cerca, retroceder (velocidad negativa reducida para que sea más natural)
            entity.target_speed = -getattr(entity, 'max_speed', 50) * 0.3
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
            
        # No disparar si no estamos mirando hacia el objetivo
        dir_to_target = (target.position - entity.position).normalized()
        dot = dir_to_target.dot(entity.forward)
        
        # dot > 0.85 significa que el ángulo es un cono más amplio hacia el jugador
        if dot < 0.85:
            return NodeStatus.RUNNING
            
        # Disparar si el arma está lista
        if getattr(entity, 'fire_cooldown', 0) <= 0:
            if hasattr(entity, 'shoot'):
                entity.shoot()
            entity.fire_cooldown = getattr(entity, 'fire_rate', 1.0)
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

class MineAsteroidAction(Action):
    def tick(self, entity, blackboard):
        # Solo el lider mina, los wingmen siguen
        if getattr(entity, 'is_wingman', False):
            return NodeStatus.FAILURE
            
        import random, time
        from ursina import distance
        target_asteroid = blackboard.get("mining_target")
        
        # Buscar un asteroide cercano si no tenemos uno y ha pasado un tiempo
        if not target_asteroid:
            if getattr(entity, '_mining_cooldown', 0) > 0:
                entity._mining_cooldown -= time.dt
                return NodeStatus.FAILURE
                
            if hasattr(entity, 'game') and hasattr(entity.game, 'environment'):
                asteroids = getattr(entity.game.environment, 'asteroids', [])
            else:
                return NodeStatus.FAILURE
                
            if not asteroids: return NodeStatus.FAILURE
            
            # Ordenar por distancia (simplificado: tomar una muestra cercana)
            close_asteroids = [a for a in asteroids if distance(entity.position, a.position) < 3000]
            if not close_asteroids: return NodeStatus.FAILURE
            
            target_asteroid = random.choice(close_asteroids)
            blackboard.set("mining_target", target_asteroid)
            entity._mining_duration = random.uniform(5.0, 15.0)
            
        # Si el asteroide se destruyó o algo
        if not target_asteroid or getattr(target_asteroid, 'is_dead', False):
            blackboard.set("mining_target", None)
            entity._mining_cooldown = random.uniform(10.0, 30.0)
            return NodeStatus.FAILURE
            
        dist = distance(entity.position, target_asteroid.position)
        smooth_look_at(entity, target_asteroid.position, speed=1.5)
        
        if dist > 300:
            # Acercarse
            entity.target_speed = entity.config.max_speed
        else:
            # Minar (disparar)
            entity.target_speed = 0
            if getattr(entity, 'fire_cooldown', 0) <= 0:
                if hasattr(entity, 'shoot'):
                    entity.shoot()
                entity.fire_cooldown = getattr(entity, 'fire_rate', 1.0)
                
            entity._mining_duration -= time.dt
            if entity._mining_duration <= 0:
                blackboard.set("mining_target", None)
                entity._mining_cooldown = random.uniform(10.0, 30.0)
                
        return NodeStatus.RUNNING

class PatrolAction(Action):
    def __init__(self, patrol_radius):
        self.patrol_radius = patrol_radius
        
    def tick(self, entity, blackboard):
        target_waypoint = blackboard.get("patrol_waypoint")
        
        # Generar nuevo waypoint si no hay
        if not target_waypoint:
            # Usar su punto de aparición como origen de patrullaje para no seguir mágicamente al jugador
            origin = blackboard.get("spawn_point", entity.position)
            
            offset = Vec3(random.uniform(-self.patrol_radius, self.patrol_radius),
                          random.uniform(-self.patrol_radius, self.patrol_radius),
                          random.uniform(-self.patrol_radius, self.patrol_radius))
            target_waypoint = origin + offset
            
            # Asegurar que el waypoint no quede a más de su radio de patrullaje real
            dist_check = distance(target_waypoint, origin)
            if dist_check > self.patrol_radius * 1.5:
                pull_dir = (target_waypoint - origin).normalized()
                target_waypoint = origin + pull_dir * random.uniform(100, self.patrol_radius)
            
            blackboard.set("patrol_waypoint", target_waypoint)
            
        if distance(entity.position, target_waypoint) < 5:
            blackboard.set("patrol_waypoint", None)
            entity.target_speed = 0
            return NodeStatus.SUCCESS
            
        # Moverse al waypoint
        smooth_look_at(entity, target_waypoint, speed=1.5)
        entity.target_speed = entity.config.max_speed * 0.5 # Patrulla a media velocidad
        return NodeStatus.RUNNING

class FollowLeaderAction(Action):
    def tick(self, entity, blackboard):
        # Buscar al líder
        leader = getattr(entity, 'leader_entity', None)
        if not leader or getattr(leader, 'is_dead', False):
            from enemy import EnemyShip
            for e in EnemyShip.active_ships:
                if getattr(e, 'squadron_id', None) == getattr(entity, 'squadron_id', '') and getattr(e, 'is_leader', False) and not getattr(e, 'is_dead', False):
                    leader = e
                    break
                
        if not leader:
            # Si el líder muere, nos convertimos en cazas libres
            entity.is_wingman = False
            entity.squadron_id = None
            return NodeStatus.FAILURE
            
        # Volar en formación de V expandida
        f_idx = getattr(entity, 'formation_index', 0)
        
        # Asignar posiciones específicas basadas en el índice
        if f_idx == 0:
            # Wingman derecho (cerca)
            offset_right = 50
            offset_back = 40
        elif f_idx == 1:
            # Wingman izquierdo (cerca)
            offset_right = -50
            offset_back = 40
        else:
            # Wingman derecho o izquierdo más atrás (o centro atrás)
            offset_right = 0
            offset_back = 80
            
        target_pos = leader.position - leader.forward * offset_back + leader.right * offset_right
        
        smooth_look_at(entity, target_pos, speed=2.0)
        
        dist = distance(entity.position, target_pos)
        if dist > 20:
            entity.target_speed = getattr(leader, 'current_speed', 50) * 1.5 # Acelerar para alcanzar al líder
        else:
            entity.target_speed = getattr(leader, 'current_speed', 50) # Igualar velocidad
            
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

def safe_dist(e1, e2):
    try:
        if e1 and e2 and not getattr(e1, 'is_dead', False) and not getattr(e2, 'is_dead', False):
            return distance(e1.position, e2.position)
    except AssertionError:
        pass
    return 999999

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
                    Condition(lambda e, b: getattr(e, 'heat', 0) > 80 or safe_dist(e, b.get("target_entity")) < 30),
                    EvadeAction()
                ]),
                # 3. Combate normal (Moverse y Atacar en paralelo)
                Parallel([
                    # Movimiento: mantener distancia segura
                    DogfightAction(min_dist=150, break_dist=80),
                    # Ataque: si está a menos de 800 de distancia, ataca
                    Sequence([
                        Condition(lambda e, b: safe_dist(e, b.get("target_entity")) < 800),
                        AttackAction()
                    ])
                ])
            ])
        ]),
        Sequence([
            Condition(lambda e, b: getattr(e, 'is_wingman', False) and getattr(e, 'squadron_id', None) is not None),
            FollowLeaderAction()
        ]),
        MineAsteroidAction(),
        PatrolAction(patrol_radius=500)
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
                        Condition(lambda e, b: safe_dist(e, b.get("target_entity")) < 1500),
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
