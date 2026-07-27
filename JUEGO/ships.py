from ursina import color

class DummyConfig:
    def __init__(self, scale_normal, scale_large):
        self.scale_normal = scale_normal
        self.scale_large = scale_large

class ShipConfig:
    def __init__(self, id, name, model, scale, menu_scale, ship_color, max_speed, boost_max_speed, 
                 acceleration, friction, laser_offsets, thruster_offsets, description,
                 model_rotation_offset=(0,0,0), thruster_scale=(0.3, 0.3, 3.5), max_health=100, laser_scale=(0.2, 0.2, 2.0),
                 dummy_config=None):
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
        self.max_health = max_health
        self.laser_scale = laser_scale
        self.dummy_config = dummy_config

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
        laser_offsets=((-3.50, -0.50, -6.25), (3.50, -0.50, -6.25)),
        thruster_offsets=[(-0.70, 0.32, -1.05), (0.70, 0.32, -1.05)],
        thruster_scale=(2.30, 2.36, 1.28),
        description="Nave de exploración estándar. Equilibrada en velocidad y maniobrabilidad. Ideal para misiones largas y recolección de recursos.",
        max_health=100,
        dummy_config=DummyConfig(scale_normal=(1.0, 1.0, 1.0), scale_large=(2.0, 2.0, 2.0))
    ),
    "nave2": ShipConfig(
        id="nave2",
        name="El Coloso",
        model='assets/nave2/naveHD.glb',  # Usando el modelo original
        scale=(4.0, 4.0, 4.0),            # Mucho más grande a petición del usuario
        menu_scale=(4.5, 4.5, 4.5),       # Tamaño perfecto para el menú principal
        ship_color=color.white,           # Más brillo (sin oscurecer la textura)
        max_speed=70,                     # MISMA STAT QUE NAVE1
        boost_max_speed=180,              # MISMA STAT QUE NAVE1
        acceleration=1.5,                 # MISMA STAT QUE NAVE1
        friction=0.8,                     # MISMA STAT QUE NAVE1
        laser_offsets=((-0.71, 0.04, -4.01), (0.71, 0.04, -4.01)),
        thruster_offsets=[(-0.1625, 0.025, -0.725), (0.1625, 0.025, -0.725)],
        description="Nave pesada de asalto. Su chasis reforzado le permite resistir un mayor castigo en combate directo.",
        model_rotation_offset=(0.00, 90.00, 0.00),
        thruster_scale=(0.05, 0.05, 0.1025),
        max_health=150,                   # AGUANTA MÁS GOLPES
        laser_scale=(0.8, 0.8, 12.0),     # LASERS MUCHO MÁS GRANDES
        dummy_config=DummyConfig(scale_normal=(1.2, 1.2, 1.2), scale_large=(6.5, 6.5, 6.5))
    )
}
