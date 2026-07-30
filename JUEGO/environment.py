from ursina import *
from loot import MeteoriteFragment
import random


class Asteroid(Entity):
    def __init__(self, manager, pos, tier=1, material_data=None):
        self.manager = manager
        self.tier = tier

        if material_data is None:
            materials = [
                {'name': 'HIERRO (Fe)', 'color': '#a14d26', 'desc': 'Uso Estructural'},
                {'name': 'COBRE (Cu)', 'color': '#28795c', 'desc': 'Conductor Eléctrico'},
                {'name': 'TITANIO (Ti)', 'color': '#5a6578', 'desc': 'Blindaje Pesado'},
                {'name': 'ORO (Au)', 'color': '#c4a627', 'desc': 'Microtecnología'},
                {'name': 'URANIO (U)', 'color': '#4d821a', 'desc': 'Núcleo Combustible'}
            ]
            self.mat_data = random.choice(materials)
        else:
            self.mat_data = material_data

        self.material_name = self.mat_data['name']
        self.material_desc = self.mat_data['desc']

        c_rgb = color.hex(self.mat_data['color'])
        c_final = color.rgb(
            clamp(c_rgb.r * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.g * random.uniform(0.8, 1.2), 0, 255),
            clamp(c_rgb.b * random.uniform(0.8, 1.2), 0, 255)
        )

        if tier == 1:
            base_size = random.uniform(8, 12)
        elif tier == 2:
            base_size = random.uniform(4, 6)
        else:
            base_size = random.uniform(1.5, 3)

        deformed_scale = Vec3(base_size, base_size * random.uniform(0.7, 1.2), base_size * random.uniform(0.7, 1.2))

        super().__init__(
            model='sphere',
            texture='noise',
            color=c_final,
            scale=deformed_scale,
            position=pos,
            collider='sphere'
        )
        self.is_asteroid = True

        if tier < 3:
            for _ in range(random.randint(4, 7)):
                offset_dir = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()
                Entity(parent=self, model='sphere', texture='noise', color=c_final * random.uniform(0.7, 1.1),
                       scale=random.uniform(0.25, 0.45), position=offset_dir * 0.45)

        self.reset(manager, pos, tier, material_data)

    def reset(self, manager, pos, tier=1, material_data=None):
        self.position = pos
        self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                             random.uniform(-1, 1)).normalized() * random.uniform(2, 5)
        self.rotation_speed = Vec3(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
        
        # Timer para reducir la carga de CPU
        self.check_timer = 0
        self.check_interval = random.uniform(0.4, 0.6)

    def update(self):
        self.position += self.velocity * time.dt
        self.rotation += self.rotation_speed * time.dt

        if not getattr(self.manager, 'player', None): return
        
        self.check_timer += time.dt
        if self.check_timer >= self.check_interval:
            self.check_timer = 0
            dist = distance(self.position, self.manager.player.position)
            
            planet_pos = Vec3(300, 200, 2200)
            if distance(self.position, planet_pos) < 550:
                if self in self.manager.asteroids: self.manager.asteroids.remove(self)
                if hasattr(self, 'pool'): self.pool.return_object(self)
                else: destroy(self)
                return
                
            hit_info = self.intersects()
            if hit_info.hit and hasattr(hit_info.entity, 'is_planet'):
                if self in self.manager.asteroids: self.manager.asteroids.remove(self)
                if hasattr(self, 'pool'): self.pool.return_object(self)
                else: destroy(self)
                return
    
            if dist > self.manager.despawn_radius:
                if self.tier == 1:
                    spawn_dir = (self.manager.player.forward + Vec3(random.uniform(-0.5, 0.5), 0,
                                                                    random.uniform(-0.5, 0.5))).normalized()
                    self.position = self.manager.player.position + (spawn_dir * (self.manager.despawn_radius - 50))
                else:
                    if self in self.manager.asteroids: self.manager.asteroids.remove(self)
                    if hasattr(self, 'pool'):
                        self.pool.return_object(self)
                    else:
                        destroy(self)

    def split(self):
        if self.tier == 1:
            next_tier = 2; pieces = 2
        elif self.tier == 2:
            next_tier = 3; pieces = 3
        else:
            pieces = 0

        for _ in range(pieces):
            offset = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * (self.scale_x * 0.35)
            
            if hasattr(self.manager, 'pool') and self.manager.pool:
                new_ast = self.manager.pool.get_object(Asteroid, self.manager, self.position + offset, tier=next_tier, material_data=self.mat_data, pool_key=f"Asteroid_{next_tier}_{self.material_name}")
            else:
                new_ast = Asteroid(self.manager, self.position + offset, tier=next_tier, material_data=self.mat_data)
                
            new_ast.velocity = self.velocity + (offset.normalized() * random.uniform(1.5, 3.5))
            self.manager.asteroids.append(new_ast)
            
        # Si es de tier 3, soltamos el fragmento
        if self.tier == 3 and getattr(self.manager, 'player', None):
            # Soltar 1 o 2 fragmentos
            for _ in range(random.randint(1, 2)):
                MeteoriteFragment(self.manager.player, self.position, self.mat_data)
                
        if getattr(self.manager, 'player', None) and hasattr(self.manager.player, 'mission_manager'):
            self.manager.player.mission_manager.increment_mission('sec_01')

        if self in self.manager.asteroids: self.manager.asteroids.remove(self)
        if hasattr(self, 'pool'):
            self.pool.return_object(self)
        else:
            destroy(self)


class AsteroidManager(Entity):
    def __init__(self, player, count=40, radius=200, pool=None, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.count = count
        self.spawn_radius = radius
        self.despawn_radius = radius * 1.5
        self.asteroids = []
        self.pool = pool
        
        self.materials = [
            {'name': 'HIERRO (Fe)', 'color': '#a14d26', 'desc': 'Uso Estructural'},
            {'name': 'COBRE (Cu)', 'color': '#28795c', 'desc': 'Conductor Eléctrico'},
            {'name': 'TITANIO (Ti)', 'color': '#5a6578', 'desc': 'Blindaje Pesado'},
            {'name': 'ORO (Au)', 'color': '#c4a627', 'desc': 'Microtecnología'},
            {'name': 'URANIO (U)', 'color': '#4d821a', 'desc': 'Núcleo Combustible'}
        ]

        self.spawn_initial_asteroids()

    def spawn_initial_asteroids(self):
        for _ in range(self.count):
            pos = Vec3(random.uniform(-1, 1), random.uniform(-1, 1),
                       random.uniform(-1, 1)).normalized() * random.uniform(100, self.spawn_radius)
            mat = random.choice(self.materials)
            tier = random.randint(1, 3)
            
            if self.pool:
                a = self.pool.get_object(Asteroid, self, pos, tier=tier, material_data=mat, pool_key=f"Asteroid_{tier}_{mat['name']}")
            else:
                a = Asteroid(self, pos, tier=tier, material_data=mat)
            self.asteroids.append(a)

    def clear_asteroids(self):
        for a in self.asteroids:
            if a in scene.entities:
                if hasattr(a, 'pool'): a.pool.return_object(a)
                else: destroy(a)
        self.asteroids.clear()

    def clear_and_respawn(self):
        self.clear_asteroids()
        self.spawn_initial_asteroids()


class ShatteredPlanet(Entity):
    """Planeta fracturado masivo, gris negroso con tintes de magma y textura de asteroide"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_planet = True

        # 1. EL NÚCLEO (Gris/negro con un toque rojo/naranja quemado + textura de asteroide)
        # El color oscuro evita que el 'noise' se rompa en cuadros blancos gigantes.
        self.core = Entity(
            parent=self,
            model='assets/planeta/kepler_10_b.glb',
            scale=0.5,
            collider='sphere',
            is_planet=True
        )
        # Ajustamos el tamaño del collider para que coincida con el diámetro real (1000)
        self.core.collider = SphereCollider(self.core, radius=1000)

        # (¡Eliminadas las pelotas rojas de sarampión!)

        # 2. LOS ESCOMBROS GIGANTES
        self.chunks = Entity(parent=self)

        for _ in range(25):  # Reducido de 60 a 25 para no saturar
            dist = random.uniform(700, 1300)
            dir_v = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized()

            c_size = random.uniform(40, 140) # Ajustado un poco hacia abajo porque el GLB tiene tamaño base ~1.6
            chunk_scale = Vec3(c_size, c_size * random.uniform(0.8, 1.2), c_size * random.uniform(0.8, 1.2))

            chunk = Entity(
                parent=self.chunks,
                model='assets/asteroides-gigantes/meteor.glb',
                scale=chunk_scale,
                position=dir_v * dist,
                rotation=(random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)),
                collider='sphere',
                is_planet=True
            )
            chunk.collider = SphereCollider(chunk, radius=0.9)

    def update(self):
        self.core.rotation_y += 1.5 * time.dt
        self.chunks.rotation_y -= 0.8 * time.dt
        self.chunks.rotation_x += 0.4 * time.dt

class CosmicBackground(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.star_radius = 15000
        self.stars_container = Entity(parent=self)
        
        # Generar vértices para malla de puntos (Point Cloud)
        low_verts = [Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * self.star_radius for _ in range(150)]
        high_verts = low_verts + [Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)).normalized() * self.star_radius for _ in range(400)]
        
        self.stars_low_entity = Entity(
            parent=self.stars_container,
            model=Mesh(vertices=low_verts, mode='point', thickness=6),
            color=color.white,
            unlit=True,
            enabled=False
        )
        
        self.stars_high_entity = Entity(
            parent=self.stars_container,
            model=Mesh(vertices=high_verts, mode='point', thickness=6),
            color=color.white,
            unlit=True,
            enabled=False
        )

        # Lo centramos casi al frente del jugador (300 en X en lugar de 1200) y a 2200 metros de profundidad.
        self.planet = ShatteredPlanet(parent=self, position=(300, 200, 2200))
        
    def set_quality(self, quality):
        if quality == 'Baja':
            self.stars_low_entity.enabled = True
            self.stars_high_entity.enabled = False
        else:
            self.stars_low_entity.enabled = False
            self.stars_high_entity.enabled = True
            
    def update(self):
        # El contenedor de estrellas sigue a la cámara para dar la ilusión de lejanía infinita
        self.stars_container.position = camera.world_position

class SpaceDustManager(Entity):
    def __init__(self, player, count=200, radius=60, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.radius = radius
        self.count = count
        
        # OPCIÓN B (MÁS ÓPTIMA): Sistema de Nube de Puntos (Point Cloud)
        # Generamos una lista de vectores en lugar de Entidades para cero overhead de CPU
        self.vertices = [
            Vec3(random.uniform(-radius, radius),
                 random.uniform(-radius, radius),
                 random.uniform(-radius, radius))
            for _ in range(count)
        ]
        
        # Un solo Mesh dibujando vértices como puntos (cero overdraw de GPU)
        self.dust_mesh = Mesh(vertices=self.vertices, mode='point', thickness=5)
        
        self.dust_entity = Entity(
            parent=self,
            model=self.dust_mesh,
            color=color.rgba(255, 255, 255, 180),
            unlit=True
        )

    def reset_particles(self):
        self.vertices = [
            Vec3(random.uniform(-self.radius, self.radius),
                 random.uniform(-self.radius, self.radius),
                 random.uniform(-self.radius, self.radius))
            for _ in range(self.count)
        ]
        self.dust_mesh.vertices = self.vertices
        self.dust_mesh.generate()
        self.dust_entity.position = self.player.position

    def update(self):
        if not self.player or self.player not in scene.entities: return
        
        # La entidad sigue al jugador para que los vértices se mantengan en coordenadas locales
        self.dust_entity.position = self.player.position
        
        # Desplazamiento basado en la velocidad
        vel = self.player.forward * self.player.current_speed * time.dt
        radius_sq = self.radius ** 2
        
        # Actualizamos la lista de vértices matemáticamente (mucho más rápido que actualizar entidades)
        for i in range(self.count):
            self.vertices[i] -= vel
            
            # Si la partícula sale del radio (usamos distancia al cuadrado para mayor rapidez)
            if self.vertices[i].length_squared() > radius_sq:
                # Reaparece delante del jugador con una variación aleatoria
                self.vertices[i] = self.player.forward * self.radius + Vec3(random.uniform(-30, 30), random.uniform(-30, 30), random.uniform(-10, 10))
                
        # Actualizamos y regeneramos la malla visual
        self.dust_mesh.vertices = self.vertices
        self.dust_mesh.generate()