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
        "costo": {"HIERRO (Fe)": 5, "COBRE (Cu)": 3},
        "desc": "+ Daño / - Calentamiento de Armas",
        "tipo": "cadencia"
    },
    "Motor de Hiper-Impulso": {
        "costo": {"TITANIO (Ti)": 5, "URANIO (U)": 2},
        "desc": "+ Capacidad de Turbo / + Velocidad Punta",
        "tipo": "velocidad"
    },
    "Blindaje de Núcleo": {
        "costo": {"ORO (Au)": 3, "TITANIO (Ti)": 5},
        "desc": "Aumenta la vida máxima del escudo",
        "tipo": "blindaje"
    },
    "Aspiradora Magnética": {
        "costo": {"COBRE (Cu)": 8, "ORO (Au)": 2},
        "desc": "Atrae minerales automáticamente",
        "tipo": "aspiradora"
    },
    "Kit de Reparación": {
        "costo": {"HIERRO (Fe)": 5, "COBRE (Cu)": 2},
        "desc": "Consumible (Tecla '1'): Repara 35% de la vida (Max: 5)",
        "tipo": "consumible"
    }
}

class InventorySystem:
    """Manejo lógico interno de los materiales y el almacenamiento"""
    def __init__(self, max_slots=16, max_stack=99):
        self.max_slots = max_slots
        self.max_stack = max_stack
        self.items = {}
        # Comenzar con 2 kits de reparación por defecto
        self.add_item("Kit de Reparación", 2)

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
            
            # Limitar a máximo 5 consumibles en el inventario
            if recipe["tipo"] == "consumible":
                if self.items.get(recipe_name, 0) >= 5:
                    return False
            
            for material, cantidad in recipe["costo"].items():
                self.remove_item(material, cantidad)
            
            if recipe["tipo"] == "consumible":
                self.add_item(recipe_name, 1)
            elif recipe["tipo"] == "cadencia":
                if hasattr(player, 'laser_level'):
                    player.laser_level = min(5, player.laser_level + 1)
            elif recipe["tipo"] == "velocidad":
                if hasattr(player, 'turbo_level'):
                    player.turbo_level = min(3, player.turbo_level + 1)
                    player.max_boost = 100 + (player.turbo_level - 1) * 50
                    player.boost_max_speed += 20
            elif recipe["tipo"] == "blindaje":
                if hasattr(player, 'shield_level'):
                    player.shield_level = min(5, player.shield_level + 1)
                    player.max_shield = 100 + (player.shield_level - 1) * 25
                    player.shield = player.max_shield
            elif recipe["tipo"] == "aspiradora":
                if hasattr(player, 'vacuum_level'):
                    player.vacuum_level = min(1, player.vacuum_level + 1)
                else:
                    player.vacuum_level = 1
                    
            # Incrementar misión de ingeniería inversa
            player.upgrades_crafted = getattr(player, 'upgrades_crafted', 0) + 1
            if hasattr(player, 'mission_manager'):
                player.mission_manager.increment_mission("sec_05")
                    
            if getattr(player, 'achievements', None):
                player.achievements.register_craft(recipe_name)
            return True
        return False

MINERAL_COLORS = {
    "HIERRO (Fe)": color.hex("#b0bec5"),     # Gris plateado suave
    "COBRE (Cu)": color.hex("#ffb74d"),      # Naranja cobre suave
    "TITANIO (Ti)": color.hex("#90a4ae"),     # Gris titanio azulado
    "ORO (Au)": color.hex("#ffd54f"),         # Dorado suave
    "URANIO (U)": color.hex("#a5d6a7")        # Verde suave
}

class InventoryUI(Entity):
    """Componente visual interactivo con diseño UI unificado y estilizado"""
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=True, z=-50, **kwargs)
        self.player = player
        self.logic = InventorySystem()
        self.is_open = False

        self.container = Entity(parent=self, enabled=False)

        # 1. Capa de oscurecimiento suave
        self.dimmer = Entity(parent=self.container, model='quad', color=color.rgba(0, 0, 0, 0.75), scale=(2, 2), z=0.1)

        # 2. El Marco Principal Redondeado (Estilo ScoreMenu)
        bg_width = min(1.74, window.aspect_ratio - 0.06)
        border_width = bg_width + 0.02
        
        self.border = Entity(
            parent=self.container, 
            model=Quad(radius=0.02), 
            color=color.hex('#6EEBFF'), 
            scale=(border_width, 0.98), 
            z=0.06
        )
        self.panel = Entity(
            parent=self.container, 
            model=Quad(radius=0.02), 
            color=color.hex('#071526'), 
            scale=(bg_width, 0.96), 
            z=0.05
        )

        # 3. Título de la Interfaz
        self.title_text = Text(
            parent=self.container, 
            text='SISTEMA DE GESTIÓN DE BODEGA', 
            position=(window.left.x + 0.08, 0.43), 
            scale=1.8, 
            color=color.white, 
            z=0
        )

        # Grilla de almacenamiento (Lado Izquierdo)
        self.slot_ui_list = []
        start_x, start_y = -bg_width / 2 + 0.16, 0.26
        for i in range(16):
            row = i // 4
            col = i % 4
            slot = Button(
                parent=self.container, 
                model=Quad(radius=0.01), 
                color=color.hex('#0b1d33'), 
                highlight_color=color.hex('#123049'),
                scale=(0.16, 0.16),  
                position=(start_x + (col * 0.18), start_y - (row * 0.19)), 
                z=0
            )
            slot.index = i
            slot.on_mouse_enter = Func(self.show_details, slot)
            slot.on_mouse_exit = Func(self.hide_details, slot)
            
            # Símbolo químico centrado
            slot.item_text = Text(parent=slot, text='', position=(0, 0.01), origin=(0, 0), scale=7.5, color=color.white, z=-0.01)
            # Icono para objetos no químicos
            slot.item_icon = Entity(parent=slot, model='quad', texture='assets/wrench_icon.png', scale=(0.5, 0.5), position=(0, 0), color=color.white, z=-0.01, enabled=False)
            # Cantidad en esquina inferior derecha
            slot.count_text = Text(parent=slot, text='', position=(0.4, -0.45), origin=(0.5, -0.5), scale=4.5, color=color.hex('#6EEBFF'), z=-0.01)
            self.slot_ui_list.append(slot)

        # Panel de Detalles del Material (Lado Derecho, Estilo Piloto/Clasificación)
        detail_x = bg_width / 2 - 0.44
        self.detail_border = Entity(
            parent=self.container, 
            model=Quad(radius=0.02), 
            color=color.hex('#123049'), 
            scale=(0.75, 0.75), 
            position=(detail_x, -0.02), 
            z=0.045
        )
        self.detail_bg = Entity(
            parent=self.container, 
            model=Quad(radius=0.02), 
            color=color.hex('#091c32'), 
            scale=(0.73, 0.73), 
            position=(detail_x, -0.02), 
            z=0.04
        )
        
        # Elementos dentro del panel de detalles
        self.detail_title = Text(
            parent=self.container, 
            text='SELECCIONA UN RECURSO', 
            position=(detail_x - 0.33, 0.30), 
            scale=1.6, 
            color=color.hex('#94a3b8'), 
            z=0
        )
        
        self.detail_symbol_bg = Entity(
            parent=self.container,
            model=Quad(radius=0.01),
            color=color.hex('#0b1d33'),
            scale=(0.22, 0.22),
            position=(detail_x - 0.22, 0.12),
            z=0.03
        )
        self.detail_symbol_text = Text(
            parent=self.container,
            text='-',
            position=(detail_x - 0.22, 0.12),
            origin=(0, 0),
            scale=10.5,
            color=color.white,
            z=0
        )
        self.detail_symbol_icon = Entity(
            parent=self.container,
            model='quad',
            texture='assets/wrench_icon.png',
            scale=(0.15, 0.15),
            position=(detail_x - 0.22, 0.12),
            color=color.white,
            z=0,
            enabled=False
        )
        
        self.detail_desc_title = Text(
            parent=self.container,
            text='ESPECIFICACIÓN DEL RECURSO:',
            position=(detail_x - 0.33, -0.06),
            scale=1.1,
            color=color.hex('#6EEBFF'),
            z=0
        )
        self.detail_desc = Text(
            parent=self.container,
            text='Pasa el cursor sobre un recurso para escanear sus\npropiedades físicas y químicas.',
            position=(detail_x - 0.33, -0.12),
            scale=1.0,
            color=color.light_gray,
            z=0
        )
        
        self.detail_amount = Text(
            parent=self.container,
            text='',
            position=(detail_x - 0.33, -0.28),
            scale=1.2,
            color=color.white,
            z=0
        )
        
        # Botones de Acción Globales
        self.btn_goto_upgrades = Button(
            parent=self.container,
            text='[ IR A MEJORAS (U) ]',
            scale=(0.4, 0.08),
            position=(detail_x, 0.40),
            color=color.hex('#123049'),
            highlight_color=color.hex('#6EEBFF'),
            z=0
        )
        self.btn_goto_upgrades.on_click = Func(self.open_upgrades)

        Text(parent=self.container, text='Presiona [I] o [ESC] para salir de la estación', position=(0, -0.42), origin=(0, 0), scale=1.1, color=color.gray, z=0)

    def show_details(self, slot):
        if slot.item_text.text != '' or slot.item_icon.enabled:
            nombre_completo = getattr(slot, 'full_name', slot.item_text.text)
            desc = getattr(slot, 'desc', '')
            simbolo = slot.item_text.text
            cantidad = slot.count_text.text
            
            # Obtener color según mineral
            col = MINERAL_COLORS.get(nombre_completo, color.hex('#FFD700')) if nombre_completo == "Kit de Reparación" else MINERAL_COLORS.get(nombre_completo, color.white)
            if nombre_completo == "Kit de Reparación":
                col = color.hex('#FFD700')
            
            # Actualizar panel de detalles
            self.detail_title.text = nombre_completo.upper()
            self.detail_title.color = col
            
            if nombre_completo == "Kit de Reparación":
                self.detail_symbol_text.text = ''
                self.detail_symbol_icon.enabled = True
                self.detail_symbol_icon.color = color.hex('#FFD700')
            else:
                self.detail_symbol_text.text = simbolo
                self.detail_symbol_icon.enabled = False
                self.detail_symbol_text.color = col
                
            self.detail_symbol_bg.color = color.rgba(col.r, col.g, col.b, 0.15)
            self.detail_desc.text = desc
            self.detail_amount.text = f"CANTIDAD DISPONIBLE: {cantidad} unidades"
            
            # Animación de hover en el slot
            slot.animate_scale(0.17, duration=0.1) 
            slot.color = color.rgba(col.r, col.g, col.b, 0.25)
            self.detail_border.color = col

    def hide_details(self, slot=None):
        if slot:
            slot.animate_scale(0.16, duration=0.1) 
            nombre_completo = getattr(slot, 'full_name', '')
            if nombre_completo:
                col = MINERAL_COLORS.get(nombre_completo, color.hex('#FFD700')) if nombre_completo == "Kit de Reparación" else MINERAL_COLORS.get(nombre_completo, color.white)
                if nombre_completo == "Kit de Reparación":
                    col = color.hex('#FFD700')
                slot.color = color.rgba(col.r, col.g, col.b, 0.15)
            else:
                slot.color = color.hex('#0b1d33')
            
        # Limpiar/restaurar panel de detalles
        self.detail_title.text = 'SELECCIONA UN RECURSO'
        self.detail_title.color = color.hex('#94a3b8')
        self.detail_symbol_text.text = '-'
        self.detail_symbol_text.color = color.white
        self.detail_symbol_icon.enabled = False
        self.detail_symbol_bg.color = color.hex('#0b1d33')
        self.detail_desc.text = 'Pasa el cursor sobre un recurso para escanear sus\npropiedades físicas y químicas.'
        self.detail_amount.text = ''
        self.detail_border.color = color.hex('#123049')

    def clear_inventory(self):
        """Vacia el inventario por completo (para inicio de nuevas partidas)"""
        self.logic.items.clear()
        self.logic.add_item("Kit de Reparación", 2)
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
            self.hide_details(None) 

    def intentar_crafteo(self, recipe_name):
        pass

    def open_upgrades(self):
        self.toggle()
        if hasattr(self.player, 'upgrades_ui'):
            self.player.upgrades_ui.toggle()

    def update_ui(self):
        for slot in self.slot_ui_list:
            slot.item_text.text = ''
            slot.item_icon.enabled = False
            slot.count_text.text = ''
            slot.full_name = '' 
            slot.desc = ''
            slot.color = color.hex('#0b1d33')
            slot.highlight_color = color.hex('#123049')

        idx = 0
        for mat_name, total_count in self.logic.items.items():
            simbolo = mat_name.split('(')[1].replace(')', '') if '(' in mat_name else mat_name
            if mat_name in RECETAS:
                desc = RECETAS[mat_name]["desc"]
            else:
                desc = MATERIALES.get(mat_name, {}).get("desc", "Sin descripción")
            col = MINERAL_COLORS.get(mat_name, color.white)
            
            # Dividir en slots según max_stack
            while total_count > 0 and idx < 16:
                count = min(total_count, self.logic.max_stack)
                slot = self.slot_ui_list[idx]
                
                if mat_name == "Kit de Reparación":
                    slot.item_text.text = ''
                    slot.item_icon.enabled = True
                    slot.item_icon.color = color.hex('#FFD700')
                    col = color.hex('#FFD700')
                else:
                    slot.item_text.text = simbolo
                    slot.item_icon.enabled = False
                    slot.item_text.color = col
                    
                slot.count_text.text = str(count)
                slot.full_name = mat_name
                slot.desc = desc
                slot.color = color.rgba(col.r, col.g, col.b, 0.15)
                slot.highlight_color = color.rgba(col.r, col.g, col.b, 0.25)
                total_count -= count
                idx += 1