from ursina import color

class DummyConfig:
    def __init__(self, scale_normal, scale_large):
        self.scale_normal = scale_normal
        self.scale_large = scale_large

class ShipConfig:
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
        self.laser_color = laser_color
        self.thruster_color = thruster_color

AVAILABLE_SHIPS = {
    "nave1": ShipConfig(
        id="nave1",
        name="El prototipo",
        model='assets/nave1/SpaceShip.obj',
        scale=(1.0, 1.0, 1.0),            # Aumentado para que no se vea tan pequeña en el juego
        menu_scale=(1.25, 1.25, 1.25),    # Tamaño perfecto para el menú principal
        ship_color=color.white,
        max_speed=70,
        boost_max_speed=180,
        acceleration=1.5,
        friction=0.8,
        laser_offsets=((-3.05, -0.50, -4.60), (3.05, -0.50, -4.60)),
        thruster_offsets=[(-0.6000, 0.3200, -1.0500), (0.6000, 0.3200, -1.0500)],
        thruster_scale=(0.20, 0.20, 0.40),
        description="Nave de exploración estándar. Equilibrada en velocidad y maniobrabilidad. Ideal para misiones largas y recolección de recursos.",
        max_health=100,
        dummy_config=DummyConfig(scale_normal=(1.0, 1.0, 1.0), scale_large=(2.0, 2.0, 2.0))
    ),
    "nave2": ShipConfig(
        id="nave2",
        name="El Coloso",
        model='assets/nave2/naveHD.glb',  # Usando el modelo original
        scale=(4.00, 4.00, 4.00),            # Mucho más grande a petición del usuario
        menu_scale=(4.5, 4.5, 4.5),       # Tamaño perfecto para el menú principal
        ship_color=color.white,           # Más brillo (sin oscurecer la textura)
        max_speed=70,                     # MISMA STAT QUE NAVE1
        boost_max_speed=180,              # MISMA STAT QUE NAVE1
        acceleration=1.5,                 # MISMA STAT QUE NAVE1
        friction=0.8,                     # MISMA STAT QUE NAVE1
        laser_offsets=((-0.66, -0.06, -1.11), (0.66, -0.06, -1.11)),
        thruster_offsets=[(-0.1625, 0.0250, -0.6875), (0.1625, 0.0250, -0.6875)],
        description="Nave pesada de asalto. Su chasis reforzado le permite resistir un mayor castigo en combate directo.",
        model_rotation_offset=(0.00, 90.00, 0.00),
        thruster_scale=(0.31, 0.31, 0.55),
        max_health=150,                   # AGUANTA MÁS GOLPES
        laser_scale=(0.2, 0.2, 2.0),      # Tamaño ajustado temporalmente para tuning
        dummy_config=DummyConfig(scale_normal=(1.2, 1.2, 1.2), scale_large=(6.5, 6.5, 6.5))
    ),
    "nave-exploradora": ShipConfig(
        id="nave-exploradora",
        name="Nave Exploradora Neutral",
        model='assets/nave_exploradora/nave-npc_neutral.glb',
        scale=(3.00, 3.00, 3.00),
        menu_scale=(3.00, 3.00, 3.00),
        ship_color=color.white,
        max_speed=60,
        boost_max_speed=140,
        acceleration=1.5,
        friction=0.8,
        laser_offsets=((-0.00, -0.20, -1.25), (0.00, -0.20, -1.25)),
        thruster_offsets=[(-0.2667, 0.0333, -0.7333), (0.2667, 0.0333, -0.7333)],
        thruster_scale=(0.38, 0.38, 0.37),
        model_rotation_offset=(0.00, 90.00, 0.00),
        description="Nave de exploración neutral. No posee armamento predeterminado, pero es excelente para recolección pasiva.",
        max_health=100,
        laser_scale=(0.2, 0.2, 2.0),      # Restaurado para que puedas afinar el "láser único"
        thruster_color=color.orange,      # Propulsores naranjas
        dummy_config=DummyConfig(scale_normal=(1.0, 1.0, 1.0), scale_large=(2.0, 2.0, 2.0))
    )
}

# --- INYECCIÓN TEMPORAL PARA TUNING ---
try:
    from enemy_ships import ENEMY_SHIPS
    AVAILABLE_SHIPS["nave-alien-enemy"] = ENEMY_SHIPS["nave-alien-enemy"]
    AVAILABLE_SHIPS["nave-altech-enemy"] = ENEMY_SHIPS["nave-altech-enemy"]
    AVAILABLE_SHIPS["boss1-nodriza"] = ENEMY_SHIPS["boss1-nodriza"]
except ImportError:
    pass
# --------------------------------------


