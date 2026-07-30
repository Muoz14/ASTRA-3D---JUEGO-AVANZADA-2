from ursina import color
from ships import DummyConfig

class EnemyShipConfig:
    def __init__(self, id, name, model, scale, menu_scale, ship_color, max_speed, boost_max_speed, 
                 acceleration, friction, laser_offsets, thruster_offsets, description,
                 model_rotation_offset=(0,0,0), thruster_scale=(0.3, 0.3, 3.5), max_health=100, laser_scale=(0.2, 0.2, 2.0),
                 dummy_config=None, laser_color=color.red, thruster_color=color.rgba(0, 255, 255, 200)):
        self.id = id
        self.name = name
        self.model = model
        self.scale = scale
        self.menu_scale = menu_scale
        self.ship_color = ship_color
        self.max_speed = max_speed
        self.boost_max_speed = boost_max_speed
        self.acceleration = acceleration
        self.friction = friction
        self.laser_offsets = laser_offsets
        self.thruster_offsets = thruster_offsets
        self.thruster_scale = thruster_scale
        self.description = description
        self.model_rotation_offset = model_rotation_offset
        self.laser_scale = laser_scale
        self.dummy_config = dummy_config
        self.max_health = max_health
        self.laser_color = laser_color
        self.thruster_color = thruster_color

# Configuraciones de naves enemigas base
ENEMY_SHIPS = {
    "nave-alien-enemy": EnemyShipConfig(
        id="nave-alien-enemy",
        name="Caza Alienígena",
        model='assets/enemigos/nave-alien_enemy/nave_enemiga1-alien.glb',
        scale=(3.00, 3.00, 3.00),
        menu_scale=(3.00, 3.00, 3.00),
        ship_color=color.white,
        max_speed=65,
        boost_max_speed=150,
        acceleration=2.0,
        friction=1.0,
        laser_offsets=((-0.85, -0.05, -2.55), (0.85, -0.05, -2.55)),
        thruster_offsets=[(0.0000, 0.0000, -0.8500)],
        thruster_scale=(0.31, 0.31, 0.25),
        model_rotation_offset=(0.00, 90.00, 0.00),
        description="Nave enemiga de origen desconocido. Muy ágil pero frágil.",
        max_health=50,
        laser_color=color.magenta,           # Láseres rosas
        thruster_color=color.rgba(180, 0, 255, 200), # Propulsor morado claro
        dummy_config=DummyConfig(scale_normal=(1.0, 1.0, 1.0), scale_large=(2.0, 2.0, 2.0))
    ),
    "nave-altech-enemy": EnemyShipConfig(
        id="nave-altech-enemy",
        name="Caza Altech",
        model='assets/enemigos/nave-altech_enemy/nave_enemiga2-tech.glb',
        scale=(4.50, 4.50, 4.50),
        menu_scale=(4.50, 4.50, 4.50),
        ship_color=color.white,
        max_speed=65,
        boost_max_speed=150,
        acceleration=2.0,
        friction=1.0,
        laser_offsets=((-0.35, -0.05, -1.15), (0.35, -0.05, -1.15)),
        thruster_offsets=[(-0.2222, 0.0556, -0.9833), (0.2222, 0.0556, -0.9833)],
        thruster_scale=(0.31, 0.31, 0.41),
        model_rotation_offset=(0.00, 90.00, 0.00),
        description="Nave enemiga de alta tecnología. Blindaje mejorado.",
        max_health=75,
        laser_color=color.blue,              # Láseres azules
        thruster_color=color.rgba(0, 200, 255, 200), # Propulsor azul brillante
        dummy_config=DummyConfig(scale_normal=(1.0, 1.0, 1.0), scale_large=(2.0, 2.0, 2.0))
    ),
    "boss1-nodriza": EnemyShipConfig(
        id="boss1-nodriza",
        name="Nave Nodriza (Jefe)",
        model='assets/enemigos/boss1_nodriza_tech/boss1_nodriza-tech.glb',
        scale=(50.0, 50.0, 50.0),
        menu_scale=(5.0, 5.0, 5.0),
        ship_color=color.white,
        max_speed=20,
        boost_max_speed=50,
        acceleration=0.5,
        friction=2.0,
        laser_offsets=((-0.00, -0.10, 0.05), (0.00, -0.10, 0.05)),
        thruster_offsets=[(-0.1700, -0.1200, -1.0050), (0.1700, -0.1200, -1.0050)],
        thruster_scale=(1.00, 1.00, 0.38),
        model_rotation_offset=(0.00, 90.00, 0.00),
        description="Nave nodriza fuertemente armada y con escudos impenetrables. Base móvil de los Caza Altech.",
        max_health=1000,
        laser_color=color.red,
        thruster_color=color.blue,
        dummy_config=DummyConfig(scale_normal=(3.0, 3.0, 3.0), scale_large=(5.0, 5.0, 5.0))
    )
}
