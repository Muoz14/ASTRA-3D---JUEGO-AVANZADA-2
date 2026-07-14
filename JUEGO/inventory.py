from ursina import *
import random

MATERIALES = {
    "HIERRO (Fe)": {"desc": "Útil para la integridad estructural."},
    "COBRE (Cu)": {"desc": "Excelente conductor eléctrico."},
    "TITANIO (Ti)": {"desc": "Metal resistente para blindaje."},
    "ORO (Au)": {"desc": "Clave para microtecnología."},
    "URANIO (U)": {"desc": "Núcleo combustible altamente energético."}
}

# Definición global de recetas y mejoras adaptadas a tus variables
RECETAS = {
    "Láser de Fuego Rápido": {
        "costo": {"HIERRO (Fe)": 15, "COBRE (Cu)": 10},
        "desc": "-20% Tiempo de Recarga de Armas",
        "tipo": "cadencia"
    },
    "Motor de Hiper-Impulso": {
        "costo": {"TITANIO (Ti)": 12, "URANIO (U)": 6},
        "desc": "+10 Velocidad de Crucero",
        "tipo": "velocidad"
    },
    "Blindaje de Núcleo": {
        "costo": {"ORO (Au)": 8, "TITANIO (Ti)": 15},
        "desc": "Optimiza la resistencia estructural",
        "tipo": "blindaje"
    },
    "Aspiradora Magnética": {
        "costo": {"COBRE (Cu)": 20, "ORO (Au)": 5},
        "desc": "Atrae minerales desde lejos",
        "tipo": "aspiradora"
    }
}

class InventorySystem:
    """Manejo lógico interno de los materiales y el almacenamiento"""
    def __init__(self, max_slots=16, max_stack=99):
        self.max_slots = max_slots
        self.max_stack = max_stack
        self.items = {}

    def add_item(self, item_name, amount):
        if item_name not in self.items:
            if len(self.items) >= self.max_slots:
                return False  
            self.items[item_name] = 0
            
        limite_total = self.max_slots * self.max_stack
        if self.items[item_name] + amount > limite_total:
            self.items[item_name] = limite_total
        else:
            self.items[item_name] += amount
        return True

    def remove_item(self, item_name, amount):
        if item_name in self.items and self.items[item_name] >= amount:
            self.items[item_name] -= amount
            if self.items[item_name] <= 0:
                del self.items[item_name]
            return True
        return False

    def can_craft(self, recipe_name):
        recipe = RECETAS.get(recipe_name)
        if not recipe: return False
        for material, cantidad in recipe["costo"].items():
            if self.items.get(material, 0) < cantidad:
                return False
        return True

    def craft(self, recipe_name, player):
        if self.can_craft(recipe_name):
            recipe = RECETAS[recipe_name]
            for material, cantidad in recipe["costo"].items():
                self.remove_item(material, cantidad)
            
            if recipe["tipo"] == "cadencia":
                if hasattr(player, 'laser_level'):
                    player.laser_level = min(5, player.laser_level + 1)
            elif recipe["tipo"] == "velocidad":
                if hasattr(player, 'turbo_level'):
                    player.turbo_level = min(3, player.turbo_level + 1)
            elif recipe["tipo"] == "blindaje":
                if hasattr(player, 'shield_level'):
                    player.shield_level = min(5, player.shield_level + 1)
            elif recipe["tipo"] == "aspiradora":
                if hasattr(player, 'vacuum_level'):
                    player.vacuum_level = min(1, player.vacuum_level + 1)
                else:
                    player.vacuum_level = 1
            if getattr(player, 'achievements', None):
                player.achievements.register_craft(recipe_name)
            return True
        return False

class InventoryUI(Entity):
    """Componente visual interactivo con diseño UI moderno y ampliado"""
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=True, z=-50, **kwargs)
        self.player = player
        self.logic = InventorySystem()
        self.is_open = False

        ### --- EL FIX DEL TOOLTIP --- ###
        # Contenedor principal
        self.tooltip_container = Entity(parent=self, enabled=False, z=-60)
        
        # 1. El Fondo Negro (Independiente)
        self.tooltip_bg = Entity(
            parent=self.tooltip_container, 
            model=Quad(radius=0.1), 
            color=color.rgba(0, 0, 0, 0.85), # Transparencia corregida con valores 0-1
            origin=(-0.5, 0.5), # Pivote arriba a la izquierda
            z=1 # Z positivo = Se dibuja ATRÁS
        )
        
        # 2. El Texto Principal (Independiente)
        self.tooltip_txt = Text(
            parent=self.tooltip_container, 
            text='', 
            scale=1.5, 
            color=color.white,
            origin=(-0.5, 0.5), 
            position=(0.02, -0.02), # Ligero margen interno
            z=-1 # Z negativo fuerte = Se dibuja muy ADELANTE
        )
        
        # 3. El Texto de Descripción
        self.tooltip_desc = Text(
            parent=self.tooltip_container, 
            text='', 
            scale=0.9, 
            color=color.light_gray,
            origin=(-0.5, 0.5), 
            position=(0.02, -0.06),
            z=-1
        )
        ### -------------------------- ###

        self.container = Entity(parent=self, enabled=False)

        # 1. Capa de oscurecimiento
        self.dimmer = Entity(parent=self.container, model='quad', color=color.rgba(0, 0, 0, 200), scale=(2, 2), z=0.1)

        # 2. El Marco Visual Ampliado
        bg_width = min(1.70, window.aspect_ratio - 0.06)
        border_width = bg_width + 0.02
        self.border = Entity(parent=self.container, model='quad', color=color.cyan, scale=(border_width, 0.95), z=0.06)
        self.panel = Entity(parent=self.container, model='quad', color=color.hex('#1e1f22'), scale=(bg_width, 0.93), z=0.05)

        # 3. Textos y Controles Ajustados
        Text(parent=self.container, text='SISTEMA DE GESTIÓN DE BODEGA', position=(window.left.x + 0.08, 0.40), scale=1.8, color=color.cyan, z=0)

        # Grilla de almacenamiento (Lado Izquierdo)
        self.slot_ui_list = []
        start_x, start_y = -bg_width / 2 + 0.12, 0.25
        for i in range(16):
            row = i // 4
            col = i % 4
            slot = Button(
                parent=self.container, 
                model='quad', 
                color=color.hex('#2b2d31'), 
                highlight_color=color.hex('#35373c'),
                scale=(0.13, 0.13),  
                position=(start_x + (col * 0.15), start_y - (row * 0.16)), 
                z=0
            )
            
            slot.on_mouse_enter = Func(self.show_tooltip, slot)
            slot.on_mouse_exit = Func(self.hide_tooltip)
            
            slot.item_text = Text(parent=slot, text='', position=(0, 0), origin=(0, 0), scale=6.5, color=color.white, z=-0.01)
            slot.count_text = Text(parent=slot, text='', position=(0.4, -0.4), origin=(0.5, -0.5), scale=4, color=color.cyan, z=-0.01)
            self.slot_ui_list.append(slot)

        # Botón para ir a Mejoras
        self.btn_goto_upgrades = Button(
            parent=self.container, 
            text='[ IR A MEJORAS (U) ]', 
            scale=(0.4, 0.08), 
            position=(0.45, 0.40),
            color=color.hex('#105020'),
            highlight_color=color.hex('#1a7030'),
            z=0
        )
        self.btn_goto_upgrades.on_click = Func(self.open_upgrades)

        Text(parent=self.container, text='Presiona [I] o [ESC] para salir de la estación', position=(0, -0.42), origin=(0, 0), scale=1.1, color=color.gray, z=0)


    def show_tooltip(self, slot):
        if slot.item_text.text != '':
            nombre_completo = getattr(slot, 'full_name', slot.item_text.text)
            desc = getattr(slot, 'desc', '')
            
            # 1. Asignamos los textos
            self.tooltip_txt.text = nombre_completo 
            self.tooltip_desc.text = desc
            
            # 2. Medimos exactamente cuánto ocupa
            ancho_exacto = max(self.tooltip_txt.width, self.tooltip_desc.width) + 0.04
            alto_exacto = 0.05 + (0.04 if desc else 0)
            
            # 3. Aplicamos esas dimensiones al cuadrado de fondo
            self.tooltip_bg.scale = (ancho_exacto, alto_exacto)

            # Posicionamos y mostramos el contenedor padre abajo y a la derecha del slot
            self.tooltip_container.position = (slot.x + 0.08, slot.y - 0.08)
            self.tooltip_container.enabled = True
            
            slot.animate_scale(0.14, duration=0.1) 
            slot.color = color.gray

    def hide_tooltip(self):
        self.tooltip_container.enabled = False
        for slot in self.slot_ui_list:
            slot.animate_scale(0.13, duration=0.1) 
            slot.color = color.hex('#2b2d31')

    def clear_inventory(self):
        """Vacia el inventario por completo (para inicio de nuevas partidas)"""
        self.logic.items.clear()
        self.update_ui()

    def input(self, key):
        # Abrir: SOLO con 'i'
        if key == 'i' and not self.is_open:
            if not getattr(self.player, 'enabled', True) or getattr(self.player, 'is_dead', False) or getattr(self.player, 'is_cinematic', False) or getattr(self.player, 'pause_menu_open', False) or getattr(self.player.tactical_map, 'is_open', False) or getattr(self.player.upgrades_ui, 'is_open', False):
                return
            self.toggle()

        # Cerrar: con 'i' o con 'escape', solo si está abierto
        elif (key == 'i' or key == 'escape') and self.is_open:
            self.toggle()

    def toggle(self):
        self.is_open = not self.is_open
        self.container.enabled = self.is_open

        if self.is_open:
            application.paused = True
            mouse.locked = False
            mouse.visible = True
            self.update_ui()
        else:
            application.paused = False
            mouse.locked = True
            mouse.visible = False
            self.hide_tooltip() 

    def intentar_crafteo(self, recipe_name):
        pass

    def open_upgrades(self):
        self.toggle()
        if hasattr(self.player, 'upgrades_ui'):
            self.player.upgrades_ui.toggle()

    def update_ui(self):
        for slot in self.slot_ui_list:
            slot.item_text.text = ''
            slot.count_text.text = ''
            slot.full_name = '' 
            slot.desc = ''

        idx = 0
        for mat_name, total_count in self.logic.items.items():
            simbolo = mat_name.split('(')[1].replace(')', '') if '(' in mat_name else mat_name
            desc = MATERIALES.get(mat_name, {}).get("desc", "Sin descripción")
            
            # Dividir en slots según max_stack
            while total_count > 0 and idx < 16:
                count = min(total_count, self.logic.max_stack)
                self.slot_ui_list[idx].item_text.text = simbolo
                self.slot_ui_list[idx].count_text.text = str(count)
                self.slot_ui_list[idx].full_name = mat_name
                self.slot_ui_list[idx].desc = desc
                total_count -= count
                idx += 1