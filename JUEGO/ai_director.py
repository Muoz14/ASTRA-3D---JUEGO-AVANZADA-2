from ursina import Entity, Vec3, time, random, distance, scene
import uuid

class AIDirector(Entity):
    def __init__(self, game_app, **kwargs):
        super().__init__(**kwargs)
        self.game = game_app
        self.max_ships = 14
        self.spawn_timer = 0
        self.spawn_interval = 5.0 # Check every 5 seconds
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
            
        if self.boss_fight_active:
            return # La Nave Nodriza se encarga de spawnear sus propios enemigos
            
        # Aumentar gradualmente el límite de naves con el tiempo
        session_time = getattr(self.game.player, 'session_time', 0)
        current_limit = min(self.max_ships, 4 + int(session_time / 30) * 2)
            
        self.spawn_timer -= time.dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval
            
            current_count = self.get_active_ships_count()
            
            # Lógica especial para el Escuadrón Altech (Lote 3)
            mm = getattr(self.game.player, 'mission_manager', None)
            is_altech_battle = mm and getattr(mm, 'current_batch', 0) == 3 and getattr(mm, 'altech_squad_spawned', False) and not getattr(mm, 'altech_wreck_spawned', False)
            
            if is_altech_battle:
                # Si es la batalla Altech, solo spawneamos refuerzos si quedan 2 o menos (el líder y otro más)
                if current_count <= 2:
                    spawned_so_far = getattr(mm, 'altech_total_spawned', 8)
                    if spawned_so_far < 45:
                        squad_size = min(6, 45 - spawned_so_far)
                        mm.altech_total_spawned = spawned_so_far + squad_size
                        self.spawn_squad(squad_size)
            else:
                # Comportamiento normal
                if current_count < current_limit:
                    squad_size = random.choice([1, 2, 4])
                    # Evitar pasarnos del límite
                    if current_count + squad_size <= self.max_ships:
                        self.spawn_squad(squad_size)
                
    def spawn_squad(self, squad_size=4):
        # Elegir facción
        ship_type = random.choice([self.altech_ship, self.alien_ship])
        
        squadron_id = str(uuid.uuid4())
        
        # Posición base por defecto
        base_pos = self.game.player.position
        
        # Override para el Lote 3: Batalla del Escuadrón Altech
        mm = getattr(self.game.player, 'mission_manager', None)
        if mm and getattr(mm, 'current_batch', 0) == 3 and getattr(mm, 'altech_squad_spawned', False) and not getattr(mm, 'waiting_for_boss', False):
            ship_type = self.altech_ship
            base_pos = Vec3(8000, 2000, -8000) # Centro de la batalla
        elif random.random() < 0.3 and hasattr(self.game, 'fractured_planet') and self.game.fractured_planet:
            base_pos = self.game.fractured_planet.position
            
        dist = random.uniform(500, 2500)
            
        # Generar punto aleatorio en esfera
        dir_vec = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
        spawn_center = base_pos + dir_vec * dist
        
        # IMPORTANTE: No salirnos de los límites del universo (ej. +/- 20000)
        # Vamos a usar el sector_radius del jugador como límite máximo
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
