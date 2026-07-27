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
        
        # Deshabilitar botones para evitar clics dobles
        self.btn_prev.disable()
        self.btn_next.disable()
        self.btn_back.disable()
        self.btn_launch.disable()
        
        # Limpiar la pantalla: Desvanecer la UI suavemente
        self.title.animate_color(color.rgba(255, 255, 255, 0), duration=0.3)
        self.info_bg.animate_color(color.rgba(0, 0, 0, 0), duration=0.3)
        self.ship_name.animate_color(color.rgba(0, 255, 255, 0), duration=0.3)
        self.ship_desc.animate_color(color.rgba(200, 200, 200, 0), duration=0.3)
        self.btn_prev.animate_color(color.rgba(0, 0, 0, 0), duration=0.3)
        self.btn_next.animate_color(color.rgba(0, 0, 0, 0), duration=0.3)
        self.btn_back.animate_color(color.rgba(0, 0, 0, 0), duration=0.3)
        self.btn_launch.animate_color(color.rgba(0, 0, 0, 0), duration=0.3)
        
        self.btn_prev.text_entity.enabled = False
        self.btn_next.text_entity.enabled = False
        self.btn_back.text_entity.enabled = False
        self.btn_launch.text_entity.enabled = False

        from ursina import Cylinder, Vec3, curve, invoke
        
        # Crear portal idéntico al de cinematics.py
        portal_z = 250
        portal = Entity(parent=scene, model=Cylinder(resolution=6), color=color.rgba(0, 255, 255, 180), double_sided=True)
        portal.position = (0, 0, portal_z)
        portal.rotation_x = 90
        portal.scale = (0, 0.01, 0)
        
        portal_inner = Entity(parent=portal, model=Cylinder(resolution=6), color=color.white, double_sided=True)
        portal_inner.scale = (0.9, 1.1, 0.9)
        
        # Abrir el portal (esperamos a que la UI desaparezca)
        portal.animate_scale(Vec3(35, 0.01, 35), duration=0.8, curve=curve.out_back, delay=0.5)
        
        # Entidad temporal para rotar el portal
        spinner = Entity(parent=scene)
        def spin_portal():
            if portal:
                portal.rotation_y += 140 * time.dt
                portal_inner.rotation_y -= 280 * time.dt
        spinner.update = spin_portal
        
        # La nave despega y entra al portal
        if hasattr(self.main_menu, 'menu_ship'):
            # Centrarla perfectamente y acelerarla
            invoke(self.main_menu.menu_ship.animate_position, (0, 0, portal_z + 20), duration=1.5, curve=curve.in_expo, delay=1.2)
            
        # Fundido a negro (fade to black) total para limpiar antes de ceder control
        black_screen = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,0), scale=99, z=-99)
        invoke(black_screen.animate_color, color.black, duration=0.8, delay=2.2)
        
        def finish():
            destroy(portal)
            destroy(spinner)
            destroy(black_screen)
            self.disable()
            self.main_menu.bg_container.disable() 
            
            # Restaurar colores y estados originales para futuras entradas al menú
            self.title.color = color.white
            self.info_bg.color = color.hex('#0a0c0f')
            self.ship_name.color = color.cyan
            self.ship_desc.color = color.light_gray
            self.btn_prev.color = color.dark_gray
            self.btn_next.color = color.dark_gray
            self.btn_back.color = color.gray
            self.btn_launch.color = color.azure
            
            self.btn_prev.enable()
            self.btn_next.enable()
            self.btn_back.enable()
            self.btn_launch.enable()
            
            self.btn_prev.text_entity.enabled = True
            self.btn_next.text_entity.enabled = True
            self.btn_back.text_entity.enabled = True
            self.btn_launch.text_entity.enabled = True
            if hasattr(self.main_menu, 'menu_ship'):
                # Restaurar a la posición inicial del MENÚ PRINCIPAL (no de selección)
                self.main_menu.menu_ship.position = (5.5, -2.5, 12)
                self.main_menu.menu_ship.rotation = (0, 7, 0)
            
            # Arrancar la verdadera cinemática del juego
            self.start_game_func(ship_id)
            
        invoke(finish, delay=3.2)
