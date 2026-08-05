from ursina import *
import random
import math


class ExplosionParticle(Entity):
    """Partículas de altísimo rendimiento: Animación delegada al backend de C++, sin bucle Update"""

    def __init__(self, pos=Vec3(0,0,0), **kwargs):
        pool = kwargs.pop('pool', None)
        super().__init__(
            model='sphere',
            color=random.choice([color.orange, color.yellow, color.rgb(255, 100, 0), color.dark_gray]),
            scale=0.3,
            **kwargs
        )
        if pool:
            self.pool = pool
        self.reset(pos)

    def reset(self, pos, **kwargs):
        self.position = pos
        self.scale = random.uniform(0.15, 0.45)
        self.color = random.choice([color.orange, color.yellow, color.rgb(255, 100, 0), color.dark_gray])
        
        # Detenemos animaciones previas
        if hasattr(self, 'animations'):
            for anim in self.animations:
                anim.finish()
            self.animations.clear()

        direction = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
        speed = random.uniform(15, 45)
        lifetime = random.uniform(0.2, 0.5)

        target_pos = self.position + (direction * speed * lifetime)

        self.animate_position(target_pos, duration=lifetime, curve=curve.out_expo)
        self.animate_scale(Vec3(0, 0, 0), duration=lifetime, curve=curve.out_expo)

        # Destruir (o reciclar) al terminar la animación
        invoke(self._cleanup, delay=lifetime + 0.05)
        
    def _cleanup(self):
        if hasattr(self, 'pool') and self.pool:
            self.pool.return_object(self)
        else:
            destroy(self)


class DualLaser(Entity):
    """Clase que representa un disparo láser individual con detección de impactos avanzada"""
    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        offset_x = kwargs.pop('offset_x', 0)
        offset_y = kwargs.pop('offset_y', 0)
        offset_z = kwargs.pop('offset_z', 0)
        damage_level = kwargs.pop('damage_level', 1)
        laser_scale = kwargs.pop('laser_scale', (0.2, 0.2, 2.0))
        laser_color = kwargs.pop('laser_color', color.red)
        self.target = kwargs.pop('target', None)
        
        super().__init__(
            model='cube',
            color=laser_color,
            unlit=True,
            scale=laser_scale,
            collider='box',
            **kwargs
        )
        
        self.reset(*args, offset_x=offset_x, offset_y=offset_y, offset_z=offset_z, damage_level=damage_level, owner=self.owner, laser_scale=laser_scale, laser_color=laser_color)

    def reset(self, ship_position, ship_rotation, ship_forward, ship_right, ship_up, offset_x=0, offset_y=0, offset_z=0, damage_level=1, owner=None, **kwargs):
        self.owner = owner
        self.damage_level = damage_level
        self.target = kwargs.get('target', None)
        self.color = kwargs.get('laser_color', color.red)
        self.center_offset = (ship_right * offset_x) + (ship_up * offset_y)
        self.position = ship_position + self.center_offset + (ship_forward * offset_z)
        self.rotation = ship_rotation
        self.scale = kwargs.get('laser_scale', (0.2, 0.2, 2.0))
        self.speed = 200
        self.lifetime = 2.0
        self.age = 0.0

    def on_destroy(self):
        if hasattr(self, 'dummy') and self.dummy:
            destroy(self.dummy)

    def _cleanup(self):
        if hasattr(self, 'dummy') and self.dummy:
            destroy(self.dummy)
            self.dummy = None
        if hasattr(self, 'pool'): 
            self.pool.return_object(self)
        else: 
            destroy(self)

    def update(self):
        if getattr(self, 'is_empty', lambda: True)(): 
            return

        self.age += time.dt
        if self.age > self.lifetime:
            self._cleanup()
            return

        # Homing logic
        if getattr(self, 'target', None):
            try:
                # Validar existencia real en C++ para no generar Assertions
                if getattr(self.target, 'is_dead', False) or getattr(self.target, 'is_empty', lambda: True)():
                    self.target = None
                else:
                    dist_target = (self.target.position - self.position).length()
                    if dist_target > 0.01:
                        dir_to_target = (self.target.position - self.position).normalized()
                        if self.forward.dot(dir_to_target) > -0.2:
                            if not hasattr(self, 'dummy') or not self.dummy:
                                self.dummy = Entity(enabled=False)
                            self.dummy.position = self.position
                            self.dummy.rotation = self.rotation
                            self.dummy.look_at(self.target.position)
                            
                            def clerp(a, b, t):
                                return a + ((b - a + 180) % 360 - 180) * t
                            
                            owner = getattr(self, 'owner', None)
                            is_player = type(owner).__name__ == 'PlayerShip'
                            is_locked = getattr(owner, 'lock_time', 0) >= 1.0
                            
                            if is_player:
                                tracking_speed = 50.0 if is_locked else 0.0
                            else:
                                tracking_speed = 3.5
                                
                            if is_locked and is_player:
                                # Aimbot absoluto si está fijado al 100%
                                self.look_at(self.target.position)
                            else:
                                self.rotation_x = clerp(self.rotation_x, self.dummy.rotation_x, time.dt * tracking_speed)
                                self.rotation_y = clerp(self.rotation_y, self.dummy.rotation_y, time.dt * tracking_speed)
                                self.rotation_z = clerp(self.rotation_z, self.dummy.rotation_z, time.dt * tracking_speed)
                        else:
                            self.target = None
                    else:
                        self.target = None
            except:
                self.target = None

        distancia_avance = self.speed * time.dt
        cola_laser = self.position - (self.forward * (self.scale_z / 2))
        self.position += self.forward * distancia_avance
        remaining_dist = distancia_avance + self.scale_z
        ignore_list = [self, getattr(self, 'owner', None)]
        
        hit_entity = None
        while True:
            hit_info = __import__('ursina').raycast(
                cola_laser,
                self.forward,
                distance=remaining_dist,
                ignore=ignore_list
            )
            
            if hit_info.hit:
                if (hasattr(hit_info.entity, 'take_damage') or hasattr(hit_info.entity, 'is_asteroid')) and hit_info.entity != getattr(self, 'owner', None):
                    hit_entity = hit_info.entity
                    break
                else:
                    ignore_list.append(hit_info.entity)
            else:
                break

        if hit_entity:
            impact_position = hit_info.world_point if hit_info.hit else hit_entity.position
            
            is_critical = False
            if hit_entity and type(hit_entity).__name__ in ('EnemyShip', 'Mothership'):
                # Check directional damage: if laser and enemy are pointing roughly the same way, it's a rear hit
                if self.forward.dot(hit_entity.forward) > 0.5:
                    is_critical = True

            from weapons import ExplosionParticle
            num_particles = random.randint(3, 4) if is_critical else random.randint(1, 2)
            
            # Intentar obtener el pool de objetos de forma segura
            pool = None
            if hasattr(self, 'owner') and self.owner:
                if hasattr(self.owner, 'game_app'):
                    pool = getattr(self.owner.game_app, 'pool', None)
                elif hasattr(self.owner, 'player') and hasattr(self.owner.player, 'game_app'):
                    pool = getattr(self.owner.player.game_app, 'pool', None)
            
            for _ in range(num_particles):
                if pool:
                    pool.get_object(ExplosionParticle, pos=impact_position, pool=pool)
                else:
                    ExplosionParticle(pos=impact_position)

            is_asteroid = hasattr(hit_entity, 'is_asteroid') and hit_entity.is_asteroid
            am = None
            if pool and hasattr(pool, 'game_app') and hasattr(pool.game_app, 'audio_manager'):
                am = pool.game_app.audio_manager
            elif hasattr(self, 'owner') and hasattr(self.owner, 'game_app') and hasattr(self.owner.game_app, 'audio_manager'):
                am = self.owner.game_app.audio_manager
                
            if am:
                if is_asteroid:
                    am.play_hit_asteroid(volume=0.6)
                else:
                    am.play_hit_ship(volume=0.6)

            # Apply damage
            if hit_entity and hit_entity.enabled:
                if hasattr(hit_entity, 'split') and hasattr(hit_entity, 'is_asteroid'):
                    hit_entity.split()
                else:
                    final_damage = self.damage_level * 2.5 if is_critical else self.damage_level
                    hit_entity.take_damage(final_damage)
            if hasattr(self, 'owner') and self.owner and getattr(self.owner, 'achievements', None):
                if hasattr(hit_entity, 'is_asteroid') and hit_entity.is_asteroid:
                    self.owner.achievements.register_asteroid_destroyed(hit_entity)
            self._cleanup()

class BlackHoleProjectile(Entity):
    def __init__(self, ship_position, camera_forward, **kwargs):
        super().__init__(
            model='sphere',
            color=color.black,
            scale=4, # Más pequeño
            position=ship_position + camera_forward * 120, # Mucho más adelante
            collider='sphere',
            **kwargs
        )
        self.move_dir = camera_forward
        
        self.lifetime = 8.0
        self.age = 0.0
        
        self.aura = Entity(parent=self, model='sphere', color=color.rgba(100, 0, 150, 0.5), scale=1.4, unlit=True)
        self.aura_time = 0
        
    def update(self):
        if application.paused: return
        self.age += time.dt
        
        # Se mueve solo durante el 1.5 segundos de viaje
        if self.age < 1.5:
            self.position += self.move_dir * 35 * time.dt
        else:
            self.scale = lerp(self.scale, Vec3(0,0,0), time.dt * 2)
            if self.scale.x < 0.1:
                destroy(self)
            
        if self.age > self.lifetime:
            destroy(self)
            return
            
        self.aura_time += time.dt
        self.aura.scale = 1.3 + math.sin(self.aura_time * 8) * 0.15
        
        # Buscar el gestor de asteroides si no lo tenemos aún
        if not hasattr(self, 'asteroid_manager'):
            for e in scene.entities:
                if type(e).__name__ == 'AsteroidManager':
                    self.asteroid_manager = e
                    break
        
        # Gravedad: atrae asteroides
        if hasattr(self, 'asteroid_manager') and self.asteroid_manager:
            for e in list(self.asteroid_manager.asteroids):
                if e.enabled:
                    try:
                        # Usar distance_squared (alrededor de 150*150 = 22500)
                        dist_sq = (self.position - e.position).length_squared()
                        if dist_sq < 22500: # Equivalente a dist < 150
                            dist = dist_sq ** 0.5
                            dir_to_bh = (self.position - e.position).normalized()
                            pull_strength = (150 - dist) * 0.4
                            e.position += dir_to_bh * pull_strength * time.dt
                            
                            if dist < 12:
                                from weapons import ExplosionParticle
                                from loot import MeteoriteFragment
                                import random
                                
                                for _ in range(15):
                                    if hasattr(e, 'manager') and hasattr(e.manager, 'pool') and e.manager.pool:
                                        e.manager.pool.get_object(ExplosionParticle, pos=e.position)
                                    else:
                                        ExplosionParticle(pos=e.position)
                                
                                # Generar loot antes de destruir el asteroide
                                if hasattr(e, 'manager') and getattr(e.manager, 'player', None):
                                    for _ in range(random.randint(1, 3)):
                                        # Ahora usa pool internamente en MeteoriteFragment si está refactorizado, o crea uno nuevo
                                        MeteoriteFragment(e.manager.player, e.position, getattr(e, 'mat_data', None))
                                        
                                if hasattr(e, 'manager') and hasattr(e.manager, 'asteroids') and e in e.manager.asteroids:
                                    e.manager.asteroids.remove(e)
                                    
                                if hasattr(e, 'pool') and e.pool:
                                    e.pool.return_object(e)
                                else:
                                    destroy(e)
                    except AssertionError:
                        # El nodo fue destruido en el mismo frame por otra causa
                        pass