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
        
        super().__init__(
            model='cube',
            color=color.red,
            unlit=True,
            scale=(0.2, 0.2, 2),
            collider='box',
            **kwargs
        )
        self.reset(*args, offset_x=offset_x, offset_y=offset_y, offset_z=offset_z, damage_level=damage_level, owner=self.owner)

    def reset(self, ship_position, ship_rotation, ship_forward, ship_right, ship_up, offset_x=0, offset_y=0, offset_z=0, damage_level=1, owner=None, **kwargs):
        self.owner = owner
        self.damage_level = damage_level
        self.position = ship_position + (ship_right * offset_x) + (ship_up * offset_y) + (ship_forward * offset_z)
        self.rotation = ship_rotation
        self.speed = 120
        self.lifetime = 2.0
        self.age = 0.0

    def update(self):
        self.age += time.dt
        if self.age > self.lifetime:
            if hasattr(self, 'pool'): self.pool.return_object(self)
            else: destroy(self)
            return

        # Calculamos cuánto va a avanzar el láser en este exacto frame
        distancia_avance = self.speed * time.dt

        # RAYCASTING: Disparamos un rayo invisible hacia adelante para ver si golpearemos algo
        hit_info = raycast(self.position, self.forward, distance=distancia_avance + (self.scale_z / 2), ignore=(self,))

        if hit_info.hit and hasattr(hit_info.entity, 'is_asteroid'):
            impact_position = hit_info.entity.position

            from weapons import ExplosionParticle
            for _ in range(random.randint(15, 25)):
                if hasattr(self, 'pool'):
                    self.pool.get_object(ExplosionParticle, pos=impact_position)
                else:
                    ExplosionParticle(pos=impact_position)

            # Aplicar daño múltiple según nivel de láser
            for _ in range(self.damage_level):
                if hit_info.entity and hit_info.entity.enabled:
                    hit_info.entity.split()
            if hasattr(self, 'owner') and self.owner and getattr(self.owner, 'achievements', None):
                self.owner.achievements.register_asteroid_destroyed(hit_info.entity)
            if hasattr(self, 'pool'):
                self.pool.return_object(self)
            else:
                destroy(self)
        else:
            # Si no hay nada en el camino, avanzamos de forma normal
            self.position += self.forward * distancia_avance

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