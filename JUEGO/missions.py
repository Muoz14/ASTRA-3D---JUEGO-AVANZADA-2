from ursina import *

class Mission:
    def __init__(self, id, title, description, target_pos=None, is_main=True):
        self.id = id
        self.title = title
        self.description = description
        self.target_pos = target_pos # Vec3 o None
        self.is_main = is_main
        self.completed = False

class MissionUI(Entity):
    def __init__(self, manager, **kwargs):
        super().__init__(parent=camera.ui, **kwargs)
        self.ignore_paused = True
        self.manager = manager
        
        # Contenedor de la notificación (Moverlo más arriba)
        self.container = Entity(parent=self, position=(window.bottom_left.x + 0.4, window.bottom_left.y + 0.50), enabled=False)
        self.container.alpha = 0
        
        # Fondo elegante (panel oscuro con borde brillante) más ajustado
        self.bg = Entity(parent=self.container, model='quad', color=color.hex('#04080f'), alpha=0.9, scale=(0.68, 0.12), z=0)
        self.border = Entity(parent=self.container, model='quad', color=color.cyan, scale=(0.685, 0.125), z=0.01)
        self.accent = Entity(parent=self.container, model='quad', color=color.cyan, scale=(0.01, 0.12), position=(-0.335, 0), z=-0.01)
        
        # Textos alineados a la izquierda del recuadro
        self.title_text = Text(parent=self.container, text="[ ACTUALIZACIÓN DE MISIÓN ]", color=color.cyan, scale=1.1, position=(-0.295, 0.04), z=-0.02)
        self.notification_text = Text(parent=self.container, text=" ", color=color.white, scale=1.1, position=(-0.295, 0.00), z=-0.02)
        self.notification_text.wordwrap = 50
        self.notification_text.text = ""
        
    def show_notification(self, text, duration=5):
        self.container.enabled = True
        self.notification_text.text = text
        self.container.alpha = 0
        self.bg.alpha = 0
        self.border.alpha = 0
        self.accent.alpha = 0
        self.title_text.alpha = 0
        self.notification_text.alpha = 0
        
        # Fade in
        self.bg.animate('alpha', 0.85, duration=0.8)
        self.border.animate('alpha', 1, duration=0.8)
        self.accent.animate('alpha', 1, duration=0.8)
        self.title_text.animate('alpha', 1, duration=0.8)
        self.notification_text.animate('alpha', 1, duration=0.8)
        
        invoke(self.hide_notification, delay=duration)
        
    def hide_notification(self):
        # Fade out
        self.bg.animate('alpha', 0, duration=1.0)
        self.border.animate('alpha', 0, duration=1.0)
        self.accent.animate('alpha', 0, duration=1.0)
        self.title_text.animate('alpha', 0, duration=1.0)
        self.notification_text.animate('alpha', 0, duration=1.0)
        invoke(setattr, self.container, 'enabled', False, delay=1.1)

    def update(self):
        # Ocultar visualmente la notificación si estamos en menú, mapa o cinemática
        if not hasattr(self, 'manager'): return
        p = self.manager.player
        hide = application.paused or not getattr(p, 'enabled', True) or getattr(p, 'is_dead', False) or getattr(p, 'pause_menu_open', False)
        
        # Controlar la visibilidad de los hijos sin apagar el Entity (para no matar las animaciones)
        self.bg.visible = not hide
        self.border.visible = not hide
        self.accent.visible = not hide
        self.title_text.visible = not hide
        self.notification_text.visible = not hide

    def update_ui(self):
        pass

class WaypointArrow(Entity):
    def __init__(self, manager, player, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.manager = manager
        self.player = player
        
        # Una flecha grande y visible en el mundo 3D sobre la nave
        self.arrow = Entity(model='cone', color=color.rgba(0, 255, 255, 200), scale=(5, 5, 15), rotation_x=90)
        self.glow = Entity(parent=self.arrow, model='cone', color=color.rgba(0, 255, 255, 50), scale=1.4, unlit=True)
        
        self.distance_text = Text(parent=camera.ui, text="", scale=1.2, position=(0, 0.35), origin=(0,0), color=color.cyan)

    def on_enable(self):
        if hasattr(self, 'distance_text'):
            self.distance_text.enabled = True
            
    def on_disable(self):
        if hasattr(self, 'distance_text'):
            self.distance_text.enabled = False

    def update(self):
        hide_ui = application.paused or not getattr(self.player, 'enabled', True) or getattr(self.player, 'is_cinematic', False) or getattr(self.player, 'pause_menu_open', False) or getattr(self.player.tactical_map, 'is_open', False) or getattr(self.player, 'is_dead', False)
        
        if hide_ui:
            self.arrow.enabled = False
            self.distance_text.enabled = False
            return
            
        target = self.manager.get_active_target()
        if target:
            self.arrow.enabled = True
            self.distance_text.enabled = True
            
            # Posicionarlo alto por encima de la nave para que se vea
            self.arrow.position = self.player.world_position + Vec3(0, 25, 0) + self.player.forward * 10
            # Oscilación suave vertical
            self.arrow.y += math.sin(time.time() * 3) * 2.0
            
            # Apuntar hacia el objetivo
            self.arrow.look_at(target)
            
            # Texto HUD
            dist = int(distance(self.player.world_position, target))
            new_text = f"OBJETIVO: {dist}m"
            if self.distance_text.text != new_text:
                self.distance_text.text = new_text
        else:
            self.arrow.enabled = False
            self.distance_text.enabled = False

class MissionManager(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.missions = []
        self.ui = MissionUI(self)
        self.waypoint = WaypointArrow(self, player)
        
        self.ui.disable() # Comienza desactivado (por ej en menú)
        self.waypoint.disable()

    def add_mission(self, id, title, description, target_pos=None, is_main=True):
        m = Mission(id, title, description, target_pos, is_main)
        self.missions.append(m)
        self.ui.update_ui()
        
    def complete_mission(self, id):
        for m in self.missions:
            if m.id == id:
                m.completed = True
                m.target_pos = None # Ya no apuntamos a él
                break
        self.ui.update_ui()
        
    def get_active_target(self):
        # Devuelve el target de la primera misión no completada que tenga target
        for m in self.missions:
            if not m.completed and m.target_pos:
                return m.target_pos
        return None
