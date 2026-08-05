from ursina import *
import math
import random


class TacticalMap(Entity):
    """Interfaz de Mapa 2D Holográfico interactivo modular"""

    def __init__(self, player, **kwargs):
        # IMPORTANTE: Esta entidad base SIEMPRE está activa para poder leer la tecla 'M'
        # incluso si el juego está pausado por completo.
        super().__init__(parent=camera.ui, ignore_paused=True, z=-20, **kwargs)
        self.player = player
        self.max_radius = 2500
        self.is_open = False

        # CONTENEDOR BASE: Todo lo visual va aquí adentro para ocultarlo/mostrarlo
        self.container = Entity(parent=self, enabled=False, position=(-0.3, 0))

        self.panel = Entity(parent=self.container, model='quad', color=color.hex('#0a0c12'), alpha=0.95,
                            scale=(0.82, 0.82))
        Entity(parent=self.panel, model='quad', color=color.cyan, scale=(1.01, 1.01), z=0.05)

        Text(parent=self.container, text='> INTERFAZ TACTICA DE NAVEGACION', position=(-0.38, 0.37), scale=1.3,
             color=color.cyan)
        Text(parent=self.container, text='Sector: EXTRACCION ALFA', position=(-0.38, 0.33), scale=0.9,
             color=color.light_gray)

        Entity(parent=self.container, model='circle', color=color.red, scale=0.62, z=-0.1)
        Entity(parent=self.container, model='circle', color=color.hex('#0a0c12'), scale=0.61, z=-0.15)
        Text(parent=self.container, text='[!] UNIVERSO INTERESTELAR', position=(0, -0.36), origin=(0, 0), scale=1.2,
             color=color.red)

        px = (300 / self.max_radius) * 0.30
        py = (2200 / self.max_radius) * 0.30
        self.planet_icon = Entity(parent=self.container, model='circle', color=color.hex('#362826'), scale=0.05,
                                  position=(px, py), z=-0.2)
        Entity(parent=self.planet_icon, model='circle', color=color.hex('#ff3300'), scale=0.4, z=-0.01)
        Text(parent=self.container, text='PLANETA FRACTURADO', position=(px + 0.03, py + 0.01), scale=0.8,
             color=color.hex('#ff6644'))

        for _ in range(35):
            r = random.uniform(200, self.max_radius - 100)
            ang = random.uniform(0, math.tau)
            ax = math.cos(ang) * r
            az = math.sin(ang) * r
            uix = (ax / self.max_radius) * 0.30
            uiy = (az / self.max_radius) * 0.30
            Entity(parent=self.container, model='circle', color=color.rgba(140, 140, 145, 150), scale=0.008,
                   position=(uix, uiy), z=-0.18)

        self.click_area = Entity(parent=self.container, model='quad', scale=(0.60, 0.60), collider='box', alpha=0,
                                 z=-0.25)

        self.map_waypoint = Entity(parent=self.container, model='circle', color=color.yellow, scale=0.015, z=-0.4,
                                   enabled=False)
        Entity(parent=self.map_waypoint, model='circle', color=color.black, scale=0.6, z=-0.01)

        self.waypoint_pos_3d = None

        self.world_waypoint = Entity(model='diamond', color=color.yellow, scale=(10, 40, 10), unlit=True, enabled=False)
        self.world_waypoint.animate_rotation_y(360, duration=3.0, loop=True)

        # EL JUGADOR: Model=Circle(3) crea un triángulo perfecto y visible en la UI.
        self.player_icon = Entity(parent=self.container, model=Circle(3), color=color.cyan, scale=0.025, z=-5,
                                  unlit=True)

        Text(parent=self.container, text='[CLIC] Fija un rumbo  |  [M] Cierra el mapa', position=(0, 0.45),
             origin=(0, 0), color=color.yellow)

        # Panel de misiones (Derecha)
        self.mission_panel = Entity(parent=self.container, model='quad', color=color.hex('#080d1a'), alpha=0.95, scale=(0.56, 0.65), position=(0.76, 0.05), z=0)
        self.mission_border = Entity(parent=self.mission_panel, model='quad', color=color.cyan, scale=(1.01, 1.01), z=0.01)
        Text(parent=self.mission_panel, text="MISIONES ACTIVAS", color=color.cyan, scale=1.6, origin=(0, 0), position=(0, 0.42), z=-0.02)
        self.mission_counter = Text(parent=self.mission_panel, text="", color=color.orange, scale=0.9, origin=(0, 0), position=(0, 0.35), z=-0.02)
        
        self.mission_list = Entity(parent=self.mission_panel, y=0)
        self.mission_scroll_y = 0
        self.mission_spacing = 0.25
        self.mission_texts = []
        self.mission_rows = []

    def toggle(self):
        # Evita abrir el mapa si estás desactivado, muerto o en la cinemática de inicio
        if not getattr(self.player, 'enabled', True) or self.player.is_dead or (self.player.is_cinematic and not self.is_open):
            return

        self.is_open = not self.is_open
        self.container.enabled = self.is_open
        
        # Ocultar o mostrar el HUD del jugador cuando se abre/cierra el mapa
        if hasattr(self.player, 'hud_container'):
            self.player.hud_container.enabled = not self.is_open

        if self.is_open:
            application.paused = True  # Pausa TODO el universo
            mouse.locked = False  # Libera el mouse para el radar
            
            # Actualizar textos de misiones
            if hasattr(self.player, 'mission_manager'):
                self.mission_scroll_y = 0
                self.mission_list.y = 0
                self.build_mission_list()
        else:
            application.paused = False  # Reactiva la física del juego
            mouse.locked = True  # Atrapa el mouse de nuevo para la nave

    def toggle_track(self, m_id):
        if not hasattr(self.player, 'mission_manager'): return
        mgr = self.player.mission_manager
        
        # Avoid interacting with completed missions
        for m in mgr.missions:
            if m.id == m_id and m.completed:
                return

        if getattr(mgr, 'tracked_mission_id', None) == m_id:
            mgr.tracked_mission_id = None
        else:
            mgr.tracked_mission_id = m_id
        self.build_mission_list()

    def build_mission_list(self):
        for t in self.mission_texts:
            destroy(t)
        self.mission_texts.clear()
        self.mission_rows.clear()
        
        if not hasattr(self.player, 'mission_manager'): return
        
        sec_count = sum(1 for m in self.player.mission_manager.missions if not getattr(m, 'is_main', False) and not m.completed)
        self.mission_counter.text = f"Secundarias Pendientes: {sec_count}"
        
        y_offset = 0.22
        tracked_id = getattr(self.player.mission_manager, 'tracked_mission_id', None)
        
        for m in self.player.mission_manager.missions:
            status_color = color.gray if m.completed else color.white
            
            # Fondo individual de la tarjeta de misión
            card = Button(parent=self.mission_list, model='quad', color=color.hex('#0d1424'), highlight_color=color.hex('#1a2645'), alpha=0.9, scale=(0.95, 0.22), position=(0, y_offset - 0.05), z=-0.03, on_click=Func(self.toggle_track, m.id))
            
            border = None
            if getattr(m, 'is_main', False):
                tipo_color = "<yellow>"
                tipo_texto = "[PRINCIPAL]"
                # Borde resaltado para principales
                border = Entity(parent=card, model='quad', color=color.yellow, scale=(1.01, 1.05), z=0.01, alpha=0.5)
                self.mission_texts.append(border)
            else:
                tipo_color = "<orange>"
                tipo_texto = "[SECUNDARIA]"
                
            if m.id == tracked_id and not m.completed:
                if border:
                    border.color = color.green
                    border.alpha = 0.8
                else:
                    border = Entity(parent=card, model='quad', color=color.green, scale=(1.01, 1.05), z=0.01, alpha=0.8)
                    self.mission_texts.append(border)
                tipo_texto += " <green>[RASTREANDO]"
                
            status_icon = "[x] " if m.completed else "[ ] "
            # Titulo
            t_title = Text(parent=self.mission_list, text=f"{status_icon}{tipo_color}{tipo_texto}<default> {m.title}{m.progress_text}", color=status_color, scale=1.1, position=(-0.44, y_offset), z=-0.05)
            # Descripcion con más anchura
            t_desc = Text(parent=self.mission_list, text=m.description, color=color.light_gray, scale=0.85, position=(-0.44, y_offset - 0.06), z=-0.05, wordwrap=75)
            
            overlay = None
            if m.completed:
                overlay = Entity(parent=card, model='quad', color=color.rgba(0,0,0,180), scale=(1,1), z=-0.06)
                self.mission_texts.append(overlay)
                
            self.mission_texts.extend([card, t_title, t_desc])
            self.mission_rows.append({
                'card': card, 't_title': t_title, 't_desc': t_desc,
                'border': border, 'overlay': overlay
            })
            
            y_offset -= self.mission_spacing

    def input(self, key):
        # El mapa escucha su propia tecla "M" sin depender de la nave
        if key == 'm' and not self.is_open:
            if getattr(self.player, 'pause_menu_open', False) or getattr(self.player.inventory, 'is_open', False) or getattr(self.player.upgrades_ui, 'is_open', False):
                return
            self.toggle()
        elif (key == 'm' or key == 'escape') and self.is_open:
            self.toggle()
            return

        if not self.is_open: return

        # Scroll logic para misiones
        if key == 'scroll up':
            self.mission_scroll_y = max(0, self.mission_scroll_y - (self.mission_spacing * 2))
        elif key == 'scroll down':
            if hasattr(self.player, 'mission_manager'):
                max_scroll = max(0, (len(self.player.mission_manager.missions) - 1) * self.mission_spacing)
                self.mission_scroll_y = min(max_scroll, self.mission_scroll_y + (self.mission_spacing * 2))

        if key == 'left mouse down' and mouse.hovered_entity == self.click_area:
            lx = mouse.point.x
            ly = mouse.point.y

            world_x = lx * 2 * self.max_radius
            world_z = ly * 2 * self.max_radius

            self.map_waypoint.x = lx * 0.60
            self.map_waypoint.y = ly * 0.60
            self.map_waypoint.enabled = True

            self.waypoint_pos_3d = Vec3(world_x, 0, world_z)
            self.world_waypoint.position = self.waypoint_pos_3d
            self.world_waypoint.enabled = True

    def clear_waypoint(self):
        self.waypoint_pos_3d = None
        self.map_waypoint.enabled = False
        self.world_waypoint.enabled = False

    def update(self):
        if not self.is_open: return
        
        # Mantener el panel de misiones siempre visible a la derecha, adaptable a resolución.
        # Como el contenedor padre ahora está en x=-0.3, compensamos sumando +0.3 al cálculo (-0.35 + 0.30 = -0.05).
        self.mission_panel.position = (window.right.x - 0.05, 0.05)
        
        # Smooth scroll misiones
        self.mission_list.y += (self.mission_scroll_y - self.mission_list.y) * 0.25
        
        # Simulated clipping via alpha fading
        for r in self.mission_rows:
            gy = r['card'].y + self.mission_list.y
            
            alpha = 1.0
            if gy > 0.17:
                alpha = max(0, 1.0 - (gy - 0.17) / 0.05)
            elif gy < -0.38:
                alpha = max(0, 1.0 - (-0.38 - gy) / 0.05)
                
            is_visible = alpha > 0
            
            r['card'].enabled = is_visible
            r['t_title'].enabled = is_visible
            r['t_desc'].enabled = is_visible
            if r['border']: r['border'].enabled = is_visible
            if r['overlay']: r['overlay'].enabled = is_visible
            
            if is_visible:
                r['card'].alpha = alpha * 0.9
                r['t_title'].alpha = alpha
                r['t_desc'].alpha = alpha
                if r['border']: r['border'].alpha = alpha * 0.5
                if r['overlay']: r['overlay'].alpha = alpha * (180/255)

        # Update player icon position on map
        pos = self.player.position
        self.player_icon.x = (pos.x / self.max_radius) * 0.30
        self.player_icon.y = (pos.z / self.max_radius) * 0.30
        # Sincronizamos la rotación del triangulo 2D con la brújula real de la nave
        self.player_icon.rotation_z = 90 - self.player.rotation_y