from ursina import *
from ships import AVAILABLE_SHIPS

class ShipSelectionMenu(Entity):
    def __init__(self, main_menu, start_game_func, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, **kwargs)
        self.main_menu = main_menu
        self.start_game_func = start_game_func
        
        self.ship_keys = list(AVAILABLE_SHIPS.keys())
        self.current_idx = 0
        
        # UI Elements
        self.title = Text(parent=self, text="SELECCIONA TU NAVE", scale=3, position=(0, 0.4), origin=(0, 0), color=color.white)
        
        # UI Container for Ship Info
        self.info_bg = Entity(parent=self, model='quad', color=color.rgba(10, 15, 25, 200), scale=(1.2, 0.25), position=(0, -0.28), z=1)
        
        self.ship_name = Text(parent=self, text="", scale=2.5, position=(0, -0.21), origin=(0, 0), color=color.cyan)
        self.ship_desc = Text(parent=self, text="", scale=1.2, position=(0, -0.30), origin=(0, 0), color=color.light_gray)

        # Buttons
        self.btn_prev = Button(parent=self, text="< ANTERIOR", scale=(0.2, 0.08), position=(-0.5, 0.0), color=color.dark_gray, on_click=self.prev_ship)
        self.btn_next = Button(parent=self, text="SIGUIENTE >", scale=(0.2, 0.08), position=(0.5, 0.0), color=color.dark_gray, on_click=self.next_ship)
        
        self.btn_launch = Button(parent=self, text="DESPEGAR", scale=(0.3, 0.1), position=(0, -0.42), color=color.azure, highlight_color=color.cyan, on_click=self.launch)
        self.btn_back = Button(parent=self, text="VOLVER AL MENÚ", scale=(0.25, 0.08), position=(-0.65, -0.42), color=color.gray, on_click=self.go_back)

        # 3D Model Showcase (Centered)
        self.showcase_model = Entity(parent=camera.ui, position=(0, 0.05), scale=(0.5, 0.5, 0.5), rotation=(20, 45, 0), enabled=False)

    def on_enable(self):
        if hasattr(self, 'showcase_model'):
            self.showcase_model.enabled = True
            self.update_ui()

    def on_disable(self):
        if hasattr(self, 'showcase_model'):
            self.showcase_model.enabled = False

    def update(self):
        if self.showcase_model.enabled:
            self.showcase_model.rotation_y += 30 * time.dt

    def update_ui(self):
        ship_id = self.ship_keys[self.current_idx]
        config = AVAILABLE_SHIPS[ship_id]
        
        self.ship_name.text = config.name
        self.ship_desc.text = config.description
        self.ship_desc.wordwrap = 50
        
        # Update 3D Model
        self.showcase_model.model = config.model
        self.showcase_model.color = config.ship_color
        # Adjust scale slightly for UI
        self.showcase_model.scale = Vec3(*config.menu_scale)

    def prev_ship(self):
        self.current_idx = (self.current_idx - 1) % len(self.ship_keys)
        self.update_ui()

    def next_ship(self):
        self.current_idx = (self.current_idx + 1) % len(self.ship_keys)
        self.update_ui()

    def go_back(self):
        self.disable()
        self.main_menu.ui_container.enable()

    def launch(self):
        ship_id = self.ship_keys[self.current_idx]
        self.disable()
        self.main_menu.bg_container.disable() # Hide background
        self.start_game_func(ship_id)
