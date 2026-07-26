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
        
        # UI Container for Ship Info (Rounded like inventory)
        self.info_bg = Entity(parent=self, model='quad', color=color.hex('#0a0c0f'), scale=(1.2, 0.25), position=(0, 0.22), z=1)
        
        self.ship_name = Text(parent=self, text="", scale=2.5, position=(0, 0.28), origin=(0, 0), color=color.cyan)
        self.ship_desc = Text(parent=self, text="", scale=1.2, position=(0, 0.20), origin=(0, 0), color=color.light_gray)

        # Buttons
        self.btn_prev = Button(parent=self, text="< ANTERIOR", scale=(0.15, 0.08), position=(-0.5, -0.1), color=color.dark_gray, on_click=self.prev_ship)
        self.btn_next = Button(parent=self, text="SIGUIENTE >", scale=(0.15, 0.08), position=(0.5, -0.1), color=color.dark_gray, on_click=self.next_ship)
        
        self.btn_back = Button(parent=self, text="VOLVER AL MENÚ", scale=(0.25, 0.08), position=(-0.65, -0.42), color=color.gray, on_click=self.go_back)
        self.btn_launch = Button(parent=self, text="DESPEGAR", scale=(0.25, 0.08), position=(0.65, -0.42), color=color.azure, highlight_color=color.cyan, on_click=self.launch)

    def on_enable(self):
        self.update_ui()

    def on_disable(self):
        pass

    def update(self):
        pass

    def update_ui(self):
        ship_id = self.ship_keys[self.current_idx]
        config = AVAILABLE_SHIPS[ship_id]
        
        self.ship_name.text = config.name
        self.ship_desc.text = config.description
        self.ship_desc.wordwrap = 50
        
        # Update 3D Model in the background
        if hasattr(self.main_menu, 'menu_ship'):
            self.main_menu.menu_ship.set_config(config)
            
        # Guardar en la cuenta activa (así al salir se mantiene guardado)
        acc_id = getattr(self.main_menu, 'current_account_id', None)
        if acc_id and hasattr(self.main_menu, 'account_manager'):
            for acc in self.main_menu.account_manager.accounts:
                if acc['id'] == acc_id:
                    acc['selected_ship'] = ship_id
                    self.main_menu.account_manager.save()
                    break

    def prev_ship(self):
        self.current_idx = (self.current_idx - 1) % len(self.ship_keys)
        self.update_ui()

    def next_ship(self):
        self.current_idx = (self.current_idx + 1) % len(self.ship_keys)
        self.update_ui()

    def go_back(self):
        self.disable()
        self.main_menu.ui_container.enable()
        if hasattr(self.main_menu, 'menu_ship'):
            self.main_menu.menu_ship.animate_position((5.5, -2.5, 12), duration=0.8, curve=curve.in_out_expo)
            self.main_menu.menu_ship.animate_rotation((0, 7, 0), duration=0.8, curve=curve.in_out_expo)

    def launch(self):
        ship_id = self.ship_keys[self.current_idx]
        self.disable()
        self.main_menu.bg_container.disable() # Hide background
        self.start_game_func(ship_id)
