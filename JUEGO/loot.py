from ursina import *
import random
import math

class MeteoriteFragment(Entity):
    def __init__(self, player, position, material_data, **kwargs):
        super().__init__(
            model='sphere',
            texture='noise',
            collider='box',
            **kwargs
        )
        self.aura = Entity(
            parent=self,
            model='sphere',
            color=color.rgba(1, 1, 1, 0.2),
            scale=1.4,
            unlit=True
        )
        self.reset(player, position, material_data)
        
    def reset(self, player, position, material_data):
        self.player = player
        self.material_data = material_data
        
        # Color final (rocoso/metálico basado en el mineral)
        c_rgb = color.hex(self.material_data['color'])
        c_final = color.rgb(
            clamp(c_rgb.r * random.uniform(0.7, 1.3), 0, 255),
            clamp(c_rgb.g * random.uniform(0.7, 1.3), 0, 255),
            clamp(c_rgb.b * random.uniform(0.7, 1.3), 0, 255)
        )
        
        base_size = random.uniform(0.8, 1.5)
        deformed_scale = Vec3(base_size, base_size * random.uniform(0.6, 1.4), base_size * random.uniform(0.6, 1.4))

        self.color = c_final
        self.scale = deformed_scale
        self.position = position
        
        self.aura.scale = 1.4
        self.aura_time = random.uniform(0, 10)
        
        # Dinámicas de movimiento
        self.rotation_speed = Vec3(random.uniform(-40, 40), random.uniform(-40, 40), random.uniform(-40, 40))
        self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * random.uniform(1, 3)
        self.lifespan = 60.0 # Desaparece después de 60 segundos si no se recoge
        
        # Para optimizar la recolección, verificamos la distancia cada 0.1 segundos
        self.check_timer = 0
        self.check_interval = 0.1
        self.base_pickup_radius = 15.0 # Distancia a la que la nave "aspira" el mineral

    def update(self):
        if application.paused:
            return
            
        self.rotation += self.rotation_speed * time.dt
        self.position += self.velocity * time.dt
        
        # Animación del aura (pulsación)
        self.aura_time += time.dt
        self.aura.scale = 1.3 + math.sin(self.aura_time * 4) * 0.15
        self.aura.color = color.rgba(1, 1, 1, 0.15 + math.sin(self.aura_time * 4) * 0.05)
        
        self.lifespan -= time.dt
        if self.lifespan <= 0:
            if hasattr(self, 'pool'):
                self.pool.return_object(self)
            else:
                destroy(self)
            return

        if not getattr(self.player, 'enabled', True) or getattr(self.player, 'is_dead', False):
            return
            
        self.check_timer += time.dt
        if self.check_timer >= self.check_interval:
            self.check_timer = 0
            
            # Usar length_squared para optimizar (evita raiz cuadrada pesada)
            dist_sq = (self.position - self.player.position).length_squared()
            
            # Efecto de magnetismo suave si está cerca
            pickup_radius = self.base_pickup_radius + getattr(self.player, 'vacuum_level', 0) * 80.0
            pickup_radius_sq = pickup_radius ** 2
            
            if dist_sq < pickup_radius_sq * 4: # el equivalente a pickup_radius * 2
                dir_to_player = (self.player.position - self.position).normalized()
                self.velocity = lerp(self.velocity, dir_to_player * 15, time.dt * 4)
                
            # Recolección efectiva
            if dist_sq < pickup_radius_sq:
                if hasattr(self.player, 'inventory'):
                    added = self.player.inventory.logic.add_item(self.material_data['name'], 1)
                    if added:
                        self.player.inventory.update_ui()
                        if hasattr(self.player, 'mission_manager'):
                            self.player.mission_manager.increment_mission('sec_02')
                if hasattr(self, 'pool'):
                    self.pool.return_object(self)
                else:
                    destroy(self)
