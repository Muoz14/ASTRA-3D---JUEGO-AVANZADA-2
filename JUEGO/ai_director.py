from ursina import Entity, Vec3, time, random, distance, scene
import uuid

class AIDirector(Entity):
    def __init__(self, game_app, **kwargs):
        super().__init__(**kwargs)
        self.game = game_app
        self.max_ships = 10 # Límite de IA simultánea
        self.spawn_timer = 0
        self.spawn_interval = 8.0 # Check cada 8 segundos para llenar rápido
        self.boss_fight_active = False
        
        # Opciones de naves enemigas comunes
        self.altech_ship = "nave-altech-enemy"
        self.alien_ship = "nave-alien-enemy"
        
    def get_active_ships_count(self):
        from enemy import EnemyShip
        return len([e for e in EnemyShip.active_ships if not getattr(e, 'is_dead', False)])

    def update(self):
        # Asegurarnos de que el jugador existe
        if not hasattr(self.game, 'player') or self.game.player is None:
            return
            
        # Eliminado el early return de boss_fight_active para permitir la lógica de Lote 4
            
        current_limit = self.max_ships
            
        self.spawn_timer -= time.dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval
            
            current_count = self.get_active_ships_count()
            
            # Lógica especial para el Escuadrón Altech (Lote 3)
            mm = getattr(self.game.player, 'mission_manager', None)
            is_altech_battle = mm and getattr(mm, 'current_batch', 0) == 3 and getattr(mm, 'altech_squad_spawned', False) and not getattr(mm, 'altech_wreck_spawned', False)
            
            if is_altech_battle:
                # Batalla Lote 3: Spawnea refuerzos por oleadas hasta 45
                if current_count <= 2:
                    spawned_so_far = getattr(mm, 'altech_total_spawned', 8)
                    if spawned_so_far < 45:
                        squad_size = min(6, 45 - spawned_so_far)
                        mm.altech_total_spawned = spawned_so_far + squad_size
                        self.spawn_squad(squad_size)
            elif mm and getattr(mm, 'current_batch', 0) == 4 and getattr(self, 'boss_fight_active', False):
                # Batalla Lote 4: Jefe Final. Mantener 10 naves constantemente
                boss_alive = False
                from enemy import EnemyShip
                for e in EnemyShip.active_ships:
                    if getattr(e, 'is_boss', False) and not getattr(e, 'is_dead', False):
                        boss_alive = True
                        break
                
                if boss_alive:
                    if current_count < self.max_ships:
                        squad_size = min(4, self.max_ships - current_count)
                        if squad_size > 0:
                            self.spawn_squad(squad_size)
            else:
                # Comportamiento normal
                if current_count < current_limit:
                    squad_size = random.choice([2, 3, 4])
                    # Evitar pasarnos del límite
                    if current_count + squad_size <= self.max_ships:
                        self.spawn_squad(squad_size)
                
    def spawn_squad(self, squad_size=4):
        # Elegir facción
        ship_type = random.choice([self.altech_ship, self.alien_ship])
        
        squadron_id = str(uuid.uuid4())
        
        # SIEMPRE usar la posición del jugador como base de spawn
        player_pos = self.game.player.world_position
        
        # Override de facción para Batallas Altech (Lote 3 y Lote 4)
        mm = getattr(self.game.player, 'mission_manager', None)
        
        # En Lote 4 (Jefe), solo spawnear si el jefe sigue vivo
        boss_alive = False
        from enemy import EnemyShip
        for e in EnemyShip.active_ships:
            if getattr(e, 'is_boss', False) and not getattr(e, 'is_dead', False):
                boss_alive = True
                break
                
        # Detener spawn si estamos en lote 4 y el jefe murió
        if mm and getattr(mm, 'current_batch', 0) == 4 and not boss_alive:
            # Si el jefe murió, NO spawneamos más refuerzos
            return
            
        if mm and getattr(mm, 'current_batch', 0) in [3, 4] and getattr(mm, 'altech_squad_spawned', False):
            ship_type = self.altech_ship
        
        # Distancia de spawn: siempre entre 300 y 800 metros del jugador
        dist = random.uniform(300, 800)
            
        # Generar punto aleatorio en esfera alrededor del jugador
        dir_vec = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
        spawn_center = player_pos + dir_vec * dist
        
        # VERIFICACIÓN DE SEGURIDAD: Nunca spawnear dentro del planeta fracturado ni de sus asteroides gigantes
        if hasattr(self.game, 'environment') and hasattr(self.game.environment, 'planet'):
            planet = self.game.environment.planet
            if planet:
                planet_pos = planet.world_position
                
                # 1. Chequeo del planeta (núcleo) - usando 2200 para dar más margen
                if distance(spawn_center, planet_pos) < 2200:
                    # Empujarlos hacia afuera del planeta, en dirección al jugador
                    push_dir = (player_pos - planet_pos).normalized()
                    spawn_center = planet_pos + push_dir * 2500
                    
                # 2. Chequeo de asteroides gigantes (chunks)
                if hasattr(planet, 'chunks'):
                    for chunk in planet.chunks.children:
                        chunk_world_pos = chunk.world_position
                        ast_radius = 150 * chunk.scale_x 
                        if distance(spawn_center, chunk_world_pos) < ast_radius:
                            # Empujar hacia el jugador en vez de en dirección aleatoria
                            push_dir = (player_pos - chunk_world_pos).normalized()
                            spawn_center = chunk_world_pos + push_dir * (ast_radius + 200)
        
        # CLAMP FINAL ABSOLUTO: Jamás spawnear a más de 1100m del jugador
        dist_to_player = distance(spawn_center, player_pos)
        if dist_to_player > 1100:
            # Traer de vuelta hacia el jugador
            pull_dir = (spawn_center - player_pos).normalized()
            spawn_center = player_pos + pull_dir * random.uniform(300, 800)
        
        # No salirnos de los límites del universo
        max_bound = self.game.player.sector_radius - 2000 if hasattr(self.game.player, 'sector_radius') else 30000
        spawn_center.x = max(-max_bound, min(max_bound, spawn_center.x))
        spawn_center.y = max(-max_bound, min(max_bound, spawn_center.y))
        spawn_center.z = max(-max_bound, min(max_bound, spawn_center.z))
        
        from enemy import EnemyShip
        
        # Spawn Líder
        leader_pos = spawn_center
        leader = EnemyShip(ship_type, leader_pos, self.game, is_leader=True, squadron_id=squadron_id)
        
        # Spawn Wingmen (escalonado para evitar tirones de rendimiento)
        from ursina import invoke
        
        def spawn_w(index):
            if getattr(self.game, 'player', None) and not getattr(self.game.player, 'is_dead', False):
                wingman_pos = leader_pos + Vec3(random.uniform(-50, 50), random.uniform(-50, 50), random.uniform(-50, 50))
                wingman = EnemyShip(ship_type, wingman_pos, self.game, is_wingman=True, squadron_id=squadron_id)
                wingman.formation_index = index
                
        for i in range(squad_size - 1):
            invoke(spawn_w, i, delay=(i + 1) * 0.2)
