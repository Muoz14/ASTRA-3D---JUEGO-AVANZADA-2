from ursina import *
from inventory import RECETAS, MATERIALES

class UpgradesUI(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False, z=-50, **kwargs)
        self.player = player
        self.is_open = False
        
        # Dimmer
        self.dimmer = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 220), scale=(2, 2), z=0.1)
        
        # Contenedor del menú (Fullscreen)
        self.bg_width = min(1.74, window.aspect_ratio - 0.06)
        border_width = self.bg_width + 0.02
        self.card_width = min(1.6, window.aspect_ratio - 0.12)
        
        self.panel = Entity(parent=self, model='quad', color=color.hex('#1e1f22'), scale=(self.bg_width, 0.96), z=0.05)
        self.border = Entity(parent=self, model='quad', color=color.cyan, scale=(border_width, 0.98), z=0.06)
        
        Text(parent=self, text='SISTEMA DE MEJORAS Y TECNOLOGÍA', position=(0, 0.43), origin=(0, 0), scale=2, color=color.cyan, z=0)
        Text(parent=self, text='Presiona [U] o [ESC] para cerrar', position=(0, -0.45), origin=(0, 0), scale=1.1, color=color.gray, z=0)
        
        # Tabs
        self.tab_disponibles = Button(parent=self, text='PLANOS DISPONIBLES', scale=(0.35, 0.08), position=(-0.19, 0.33), color=color.hex('#2b2d31'), highlight_color=color.hex('#35373c'), z=0)
        self.tab_instaladas = Button(parent=self, text='TECNOLOGÍA INSTALADA', scale=(0.35, 0.08), position=(0.19, 0.33), color=color.hex('#2b2d31'), highlight_color=color.hex('#35373c'), z=0)
        
        self.tab_disponibles.on_click = Func(self.show_tab, 'disponibles')
        self.tab_instaladas.on_click = Func(self.show_tab, 'instaladas')
        
        self.content_disponibles = Entity(parent=self, enabled=True, z=0, y=0)
        self.content_instaladas = Entity(parent=self, enabled=False, z=0, y=0)
        
        self.scroll_y_disp = 0
        self.scroll_y_inst = 0
        self.popup_time_left = 0
        
        # Crear elementos visuales para todas las recetas, se filtrarán en update_ui
        self.create_upgrade_cards()
        self.create_installed_cards()
        
        self.show_tab('disponibles')

    def create_upgrade_cards(self):
        # Cartas en disponibles
        self.disponibles_cards = []
        start_y = 0.15
        
        for nombre, datos in RECETAS.items():
            card = Entity(parent=self.content_disponibles, model='quad', color=color.hex('#2b2d31'), scale=(self.card_width, 0.2), position=(0, start_y), z=-0.01)
            
            t_name = Text(parent=self.content_disponibles, text=nombre, position=(-self.card_width/2 + 0.1, start_y + 0.05), scale=1.5, color=color.white, z=-0.02)
            t_info = Text(parent=self.content_disponibles, text='', position=(-self.card_width/2 + 0.1, start_y - 0.02), scale=1.0, color=color.light_gray, z=-0.02)
            
            btn_upgrade = Button(parent=self.content_disponibles, text='+ Mejorar', scale=(0.25, 0.08), position=(self.card_width/2 - 0.2, start_y), color=color.hex('#105020'), highlight_color=color.hex('#1a7030'), z=-0.02)
            btn_upgrade.on_click = Func(self.intentar_mejora, nombre)
            
            self.disponibles_cards.append((card, t_info, t_name, btn_upgrade, nombre, datos))
            start_y -= 0.22

    def create_installed_cards(self):
        self.instaladas_cards = []
        start_y = 0.15
        
        for nombre, datos in RECETAS.items():
            card = Entity(parent=self.content_instaladas, model='quad', color=color.hex('#2b2d31'), scale=(self.card_width, 0.2), position=(0, start_y), z=-0.01)
            
            t_name = Text(parent=self.content_instaladas, text=nombre, position=(-self.card_width/2 + 0.1, start_y + 0.05), scale=1.5, color=color.green, z=-0.02)
            t_info = Text(parent=self.content_instaladas, text='', position=(-self.card_width/2 + 0.1, start_y - 0.02), scale=1.0, color=color.light_gray, z=-0.02)
            self.instaladas_cards.append((card, t_info, t_name, nombre, datos))
            start_y -= 0.22
            
        # Materia oscura (Especial)
        card = Entity(parent=self.content_instaladas, model='quad', color=color.hex('#2b2d31'), scale=(self.card_width, 0.2), position=(0, start_y), z=-0.01)
        t_name = Text(parent=self.content_instaladas, text="MATERIA OSCURA [Prototipo]", position=(-self.card_width/2 + 0.1, start_y + 0.05), scale=1.5, color=color.magenta, z=-0.02)
        t_info = Text(parent=self.content_instaladas, text="Armamento experimental.\nSe utilizará para tecnología de manipulación espacial.", position=(-self.card_width/2 + 0.1, start_y - 0.02), scale=1.0, color=color.light_gray, z=-0.02)
        self.instaladas_cards.append((card, t_info, t_name, "Materia Oscura", {"tipo": "especial"}))

    def show_tab(self, tab_name):
        if tab_name == 'disponibles':
            self.tab_disponibles.color = color.hex('#45474c')
            self.tab_instaladas.color = color.hex('#2b2d31')
            self.content_disponibles.enabled = True
            self.content_instaladas.enabled = False
        else:
            self.tab_disponibles.color = color.hex('#2b2d31')
            self.tab_instaladas.color = color.hex('#45474c')
            self.content_disponibles.enabled = False
            self.content_instaladas.enabled = True
        self.update_ui()

    def get_nivel(self, tipo):
        if tipo == "cadencia": return getattr(self.player, 'laser_level', 1), 5
        if tipo == "velocidad": return getattr(self.player, 'turbo_level', 1), 3
        if tipo == "blindaje": return getattr(self.player, 'shield_level', 1), 5
        if tipo == "aspiradora": return getattr(self.player, 'vacuum_level', 0), 1
        return 1, 5

    def show_popup(self, msg, col):
        import time as pytime
        if hasattr(self, 'popup_txt') and self.popup_txt: 
            destroy(self.popup_txt)
        self.popup_txt = Text(parent=self, text=msg, position=(0, -0.4), origin=(0,0), scale=1.5, color=col, z=-0.1)
        self.popup_end_time = pytime.time() + 2.0
        
    def update(self):
        import time as pytime
        if hasattr(self, 'popup_end_time') and self.popup_end_time > 0:
            if pytime.time() >= self.popup_end_time:
                self.popup_end_time = 0
                if hasattr(self, 'popup_txt') and self.popup_txt:
                    destroy(self.popup_txt)

    def intentar_mejora(self, recipe_name):
        recipe = RECETAS.get(recipe_name)
        if recipe:
            nivel, max_nivel = self.get_nivel(recipe["tipo"])
            if nivel >= max_nivel: return
            
            if self.player.inventory.logic.craft(recipe_name, self.player):
                print(f"[Mejoras]: Estructura mejorada con éxito -> {recipe_name}")
                self.show_popup("Mejora Instalada con Éxito", color.green)
                self.update_ui()
                if hasattr(self.player, 'inventory'):
                    self.player.inventory.update_ui()
            else:
                print("[Mejoras]: Recursos insuficientes.")
                self.show_popup("Recursos Insuficientes", color.red)

    def update_ui(self):
        # Actualizar disponibles
        disp_y = 0.15
        inst_y = 0.15
        
        for card, t_info, t_name, btn_upgrade, nombre, datos in self.disponibles_cards:
            if datos["tipo"] == "consumible":
                count = self.player.inventory.logic.items.get(nombre, 0)
                if count < 5:
                    card.original_enabled = True
                    card.y = disp_y
                    t_name.y = disp_y + 0.05
                    t_info.y = disp_y - 0.02
                    btn_upgrade.y = disp_y
                    disp_y -= 0.22
                    costo_str = " | ".join([f"{mat}: {self.player.inventory.logic.items.get(mat, 0)}/{cant}" for mat, cant in datos["costo"].items()])
                    t_info.text = f"{datos['desc']}\nEn Bodega: {count}/5 | Costo: {costo_str}"
                else:
                    card.original_enabled = False
            else:
                nivel, max_nivel = self.get_nivel(datos["tipo"])
                if nivel < max_nivel:
                    card.original_enabled = True
                    card.y = disp_y
                    t_name.y = disp_y + 0.05
                    t_info.y = disp_y - 0.02
                    btn_upgrade.y = disp_y
                    disp_y -= 0.22
                    costo_str = " | ".join([f"{mat}: {self.player.inventory.logic.items.get(mat, 0)}/{cant}" for mat, cant in datos["costo"].items()])
                    t_info.text = f"{datos['desc']} [Nivel {nivel}/{max_nivel}]\nCosto: {costo_str}"
                else:
                    card.original_enabled = False
                
        # Actualizar instaladas
        for card, t_info, t_name, nombre, datos in self.instaladas_cards:
            if datos.get("tipo") == "consumible":
                count = self.player.inventory.logic.items.get(nombre, 0)
                if count > 0:
                    card.original_enabled = True
                    card.y = inst_y
                    t_name.y = inst_y + 0.05
                    t_info.y = inst_y - 0.02
                    inst_y -= 0.22
                    t_info.text = f"Consumible Listo para Usar\nEn Bodega: {count} (Usa la tecla C)"
                else:
                    card.original_enabled = False
            else:
                nivel, max_nivel = self.get_nivel(datos.get("tipo", "none"))
                if nivel > 1 or (datos.get("tipo") == "aspiradora" and nivel > 0) or datos.get("tipo") == "especial":
                    card.original_enabled = True
                    card.y = inst_y
                    t_name.y = inst_y + 0.05
                    t_info.y = inst_y - 0.02
                    inst_y -= 0.22
                    
                    if datos.get("tipo") != "especial":
                        if nivel >= max_nivel:
                            t_info.text = f"{datos['desc']} [NIVEL MÁXIMO ALCANZADO]"
                        else:
                            t_info.text = f"{datos['desc']} [Nivel {nivel}/{max_nivel}]"
                else:
                    card.original_enabled = False

        self.update_scroll()

    def update_scroll(self):
        # Efecto de clipping (recorte manual) para que no desborde
        for card, t_info, t_name, btn, _, _ in self.disponibles_cards:
            if not getattr(card, 'original_enabled', False):
                card.enabled = False
                t_info.enabled = False
                t_name.enabled = False
                btn.enabled = False
                continue
            gy = card.y + self.content_disponibles.y
            is_visible = (-0.40 < gy < 0.25)
            card.enabled = is_visible
            t_info.enabled = is_visible
            t_name.enabled = is_visible
            btn.enabled = is_visible
            
        for card, t_info, t_name, _, _ in self.instaladas_cards:
            if not getattr(card, 'original_enabled', False):
                card.enabled = False
                t_info.enabled = False
                t_name.enabled = False
                continue
            gy = card.y + self.content_instaladas.y
            is_visible = (-0.40 < gy < 0.25)
            card.enabled = is_visible
            t_info.enabled = is_visible
            t_name.enabled = is_visible

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.enabled = True
            application.paused = True
            mouse.locked = False
            self.update_ui()
        else:
            self.enabled = False
            application.paused = False
            mouse.locked = True

    def input(self, key):
        if not self.enabled: return
        if key == 'escape':
            self.toggle()
        
        # Calcular el máximo scroll basado en el número de tarjetas activas (original_enabled)
        max_scroll_disp = max(0, sum(1 for c in self.disponibles_cards if getattr(c[0], 'original_enabled', False)) * 0.22 - 0.4)
        max_scroll_inst = max(0, sum(1 for c in self.instaladas_cards if getattr(c[0], 'original_enabled', False)) * 0.22 - 0.4)
        
        # Scroll up and down
        if key == 'scroll up':
            if self.content_disponibles.enabled:
                self.scroll_y_disp = max(0, self.scroll_y_disp - 0.2)
                self.content_disponibles.y = self.scroll_y_disp
            elif self.content_instaladas.enabled:
                self.scroll_y_inst = max(0, self.scroll_y_inst - 0.2)
                self.content_instaladas.y = self.scroll_y_inst
            self.update_scroll()
                
        if key == 'scroll down':
            if self.content_disponibles.enabled:
                self.scroll_y_disp = min(max_scroll_disp, self.scroll_y_disp + 0.2)
                self.content_disponibles.y = self.scroll_y_disp
            elif self.content_instaladas.enabled:
                self.scroll_y_inst = min(max_scroll_inst, self.scroll_y_inst + 0.2)
                self.content_instaladas.y = self.scroll_y_inst
            self.update_scroll()
