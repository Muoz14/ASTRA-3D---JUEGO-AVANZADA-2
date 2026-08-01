from ursina import *

class Mission:
    def __init__(self, id, title, description, short_description=None, target_pos=None, is_main=True, max_progress=0):
        self.id = id
        self.title = title
        self.description = description
        self.short_description = short_description if short_description else description
        self.target_pos = target_pos # Vec3 o None
        self.is_main = is_main
        self.completed = False
        self.current_progress = 0
        self.max_progress = max_progress
        
    @property
    def progress_text(self):
        if self.max_progress > 0:
            return f" [{self.current_progress}/{self.max_progress}]"
        return ""

class MissionUI(Entity):
    def __init__(self, manager, **kwargs):
        super().__init__(parent=camera.ui, z=1, **kwargs)
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
        
        # Texto en la esquina inferior izquierda dinámico
        self.secondary_text = Text(parent=camera.ui, text=" ", scale=0.9, position=(window.bottom_left.x + 0.03, -0.15), origin=(-0.5, 0), color=color.white, z=1)
        self.secondary_text.wordwrap = 40
        
        # Diamante 3D en el mundo para el objetivo de la misión principal
        self.world_diamond = Entity(model='diamond', color=color.yellow, scale=(10, 40, 10), unlit=True, enabled=False)
        self.world_diamond.animate_rotation_y(360, duration=3.0, loop=True)

    def on_enable(self):
        if hasattr(self, 'distance_text'):
            self.distance_text.enabled = True
            self.secondary_text.enabled = True
            
    def on_disable(self):
        if hasattr(self, 'distance_text'):
            self.distance_text.enabled = False
            self.secondary_text.enabled = False
            if hasattr(self, 'world_diamond'):
                self.world_diamond.enabled = False

    def update(self):
        hide_ui = application.paused or not getattr(self.player, 'enabled', True) or getattr(self.player, 'is_cinematic', False) or getattr(self.player, 'pause_menu_open', False) or getattr(self.player.tactical_map, 'is_open', False) or getattr(self.player, 'is_dead', False)
        
        if hide_ui:
            self.arrow.enabled = False
            self.distance_text.enabled = False
            if hasattr(self, 'world_diamond'): self.world_diamond.enabled = False
            return
        tracked = self.manager.get_tracked_mission()
        
        if hide_ui or not tracked:
            self.arrow.enabled = False
            self.distance_text.enabled = False
            self.secondary_text.enabled = False
            if hasattr(self, 'world_diamond'): self.world_diamond.enabled = False
            return
            
        if tracked.is_main:
            self.secondary_text.enabled = False
            if tracked.target_pos:
                self.arrow.enabled = True
                self.distance_text.enabled = True
                if hasattr(self, 'world_diamond'):
                    self.world_diamond.enabled = True
                    self.world_diamond.position = tracked.target_pos
                
                # Posicionarlo alto por encima de la nave para que se vea
                self.arrow.position = self.player.world_position + Vec3(0, 25, 0) + self.player.forward * 10
                # Oscilación suave vertical
                self.arrow.y += math.sin(time.time() * 3) * 2.0
                
                # Apuntar hacia el objetivo
                self.arrow.look_at(tracked.target_pos)
                
                # Texto HUD
                dist = int(distance(self.player.world_position, tracked.target_pos))
                new_text = f"OBJETIVO: {dist}m"
                if self.distance_text.text != new_text:
                    self.distance_text.text = new_text
            else:
                self.arrow.enabled = False
                self.distance_text.enabled = False
                if hasattr(self, 'world_diamond'): self.world_diamond.enabled = False
        else:
            self.arrow.enabled = False
            self.distance_text.enabled = False
            if hasattr(self, 'world_diamond'): self.world_diamond.enabled = False
            self.secondary_text.enabled = True
            
            # Mostrar la misión con progreso si lo tiene
            new_text = f"> {tracked.title}{tracked.progress_text}\n\n{tracked.short_description}"
            if self.secondary_text.text != new_text:
                self.secondary_text.text = new_text
            # Posicionamiento dinámico en tiempo real
            self.secondary_text.position = (window.bottom_left.x + 0.03, -0.15)

class MissionManager(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.missions = []
        self.current_batch = 1
        self.tracked_mission_id = None
        self.ui = MissionUI(self)
        self.waypoint = WaypointArrow(self, player)
        
        self.ui.disable() # Comienza desactivado (por ej en menú)
        self.waypoint.disable()

    def reset(self):
        self.missions.clear()
        self.current_batch = 1
        self.tracked_mission_id = None
        self.ui.update_ui()

    def add_mission(self, id, title, description, short_description=None, target_pos=None, is_main=True, max_progress=0):
        m = Mission(id, title, description, short_description, target_pos, is_main, max_progress)
        self.missions.append(m)
        if not getattr(self, 'tracked_mission_id', None) and is_main:
            self.tracked_mission_id = id
        self.ui.update_ui()
        
    def increment_mission(self, id, amount=1):
        for m in self.missions:
            if m.id == id and not m.completed:
                m.current_progress += amount
                if m.max_progress > 0 and m.current_progress >= m.max_progress:
                    m.current_progress = m.max_progress
                    self.complete_mission(id)
                else:
                    self.ui.show_notification(f"ACTUALIZACIÓN DE MISIÓN\n{m.title} {m.progress_text}", duration=3)
                self.ui.update_ui()
                return
                
    def set_mission_progress(self, id, progress):
        for m in self.missions:
            if m.id == id and not m.completed:
                old_progress = m.current_progress
                if m.current_progress != progress:
                    m.current_progress = progress
                    if m.max_progress > 0 and m.current_progress >= m.max_progress:
                        m.current_progress = m.max_progress
                        self.complete_mission(id)
                    else:
                        # Para evitar spam de notificaciones continuas (como en Exploración Profunda)
                        # Notificamos cada cierto porcentaje o valor.
                        if id == 'sec_03':
                            if int(old_progress / 2500) < int(progress / 2500) and progress >= 2500:
                                self.ui.show_notification(f"ACTUALIZACIÓN DE MISIÓN\n{m.title} {m.progress_text}m", duration=3)
                        elif id != 'sec_03' and old_progress != progress:
                            self.ui.show_notification(f"ACTUALIZACIÓN DE MISIÓN\n{m.title} {m.progress_text}", duration=3)

                    self.ui.update_ui()
                return

    def complete_mission(self, id):
        for m in self.missions:
            if m.id == id and not m.completed:
                m.completed = True
                print(f"Misión completada: {m.title}")
                
                # Notificación visual
                self.ui.show_notification(f"¡MISIÓN COMPLETADA!\n{m.title}", duration=6)
                
                # auto-untrack if completed and it was tracked
                if self.tracked_mission_id == id:
                    self.tracked_mission_id = None
                    
                # Intentar rastrear la siguiente misión principal disponible, o en su defecto cualquier otra
                    for next_m in self.missions:
                        if not next_m.completed:
                            self.tracked_mission_id = next_m.id
                            break
                            
                self.ui.update_ui()
                
                # Check if all missions in the current batch are completed
                if all(miss.completed for miss in self.missions):
                    invoke(self.advance_batch, delay=5.0)
                    
                return
                
    def advance_batch(self):
        self.current_batch += 1
        self.missions.clear()
        self.tracked_mission_id = None
        
        if self.current_batch == 2:
            self.player.survival_timer = 0.0
            self.add_mission(
                id="main_02",
                title="Intercepta las Transmisiones",
                description="Localiza la boya de comunicaciones enemiga para extraer datos sobre la corporación Altech.",
                short_description="Escanea la boya de comunicaciones.",
                target_pos=Vec3(2500, -500, -3500), # Un punto lejano para la boya
                is_main=True
            )
            
            # Crear la boya física en el mundo
            if not hasattr(self, 'altech_buoy') or not self.altech_buoy:
                self.altech_buoy = Entity(model='cube', color=color.cyan, scale=15, position=Vec3(2500, -500, -3500))
                Entity(parent=self.altech_buoy, model='sphere', color=color.red, scale=1.2, y=1)
                
            self.add_mission(
                id="sec_04",
                title="Caza de Cazas",
                description="Destruye 15 naves enemigas de Altech para mermar sus fuerzas.",
                short_description="Destruye 15 naves enemigas.",
                is_main=False,
                max_progress=15
            )
            self.add_mission(
                id="sec_05",
                title="Ingeniería Inversa",
                description="Fabrica 2 mejoras para tu nave en el menú de Inventario usando la tecnología recolectada.",
                short_description="Fabrica 2 mejoras de nave.",
                is_main=False,
                max_progress=2
            )
            
            # Chequeo retroactivo: si el jugador ya crafteó mejoras, sumarlas
            upgrades_crafted = getattr(self.player, 'upgrades_crafted', 0)
            if upgrades_crafted > 0:
                self.set_mission_progress("sec_05", upgrades_crafted)
                
            self.add_mission(
                id="sec_06",
                title="Maniobras Evasivas",
                description="Demuestra tu destreza. Sobrevive 3 minutos enteros sin morir.",
                short_description="Sobrevive por 180 segundos.",
                is_main=False,
                max_progress=180
            )
            
            if hasattr(self.player, 'ai_companion'):
                self.player.ai_companion.trigger_dialogue([
                    ("Tierra: Piloto, excelente trabajo con la anomalía.", 4.0),
                    ("Tierra: Los datos sugieren tecnología de una facción humana clandestina...", 5.0),
                    ("Tierra: Se llaman 'Altech'. Están usando tecnología alienígena robada.", 5.0),
                    ("IA: Detecto una boya de transmisión de Altech cerca. Procedamos a interceptarla.", 5.5)
                ])
                
        elif self.current_batch == 3:
            self.add_mission(
                id="main_03",
                title="Escuadrón Altech",
                description="Intercepta al escuadrón de reconocimiento Altech en las coordenadas indicadas.",
                short_description="Intercepta escuadrón Altech.",
                target_pos=Vec3(8000, 2000, -8000),
                is_main=True
            )
            self.add_mission(
                id="sec_07",
                title="Depuración Total",
                description="Destruye a 15 naves enemigas.",
                short_description="Destruye 15 enemigos.",
                is_main=False,
                max_progress=15
            )
            
            self.altech_squad_spawned = False
            self.altech_wreck_spawned = False
            self.altech_wreck_hacked = False
            self.waiting_for_boss = False
            self.altech_squad_kills = 0
            
            if hasattr(self.player, 'ai_companion'):
                self.player.ai_companion.trigger_dialogue([
                    ("IA: Nuevas coordenadas detectadas en la transmisión.", 3.5),
                    ("Tierra: Piloto, dirígete a esas coordenadas. Creemos que es un escuadrón de reconocimiento.", 5.0)
                ])
        
    def get_tracked_mission(self):
        if not getattr(self, 'tracked_mission_id', None): return None
        for m in self.missions:
            if m.id == self.tracked_mission_id and not m.completed:
                return m
        return None

    def get_active_target(self):
        m = self.get_tracked_mission()
        return m.target_pos if m else None
