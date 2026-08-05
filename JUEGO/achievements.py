from ursina import *
import json
import os
import math


def fitted_text_scale(text, base_scale, comfortable_chars, minimum_scale):
    """Reduce una linea larga para mantenerla dentro de su espacio visual."""
    length = max(1, len(str(text)))
    if length <= comfortable_chars:
        return base_scale
    return max(minimum_scale, base_scale * comfortable_chars / length)


ACHIEVEMENT_TIERS = ('Bronce', 'Plata', 'Oro')
TIER_COLORS = {
    'Bronce': '#BFC7D5',
    'Plata': '#BFC7D5',
    'Oro': '#BFC7D5',
}
TIER_BADGE_COLOR = '#BFC7D5'
POPUP_TIER_STYLES = {
    'Bronce': {
        'edge': '#C46F3A',
        'accent': '#FF9A55',
        'badge': '#B87333',
        'badge_dark': '#3A1B10',
        'mark': 'B',
        'phrase': 'Primer destello en la bitacora.',
    },
    'Plata': {
        'edge': '#BFCFE0',
        'accent': '#E8F4FF',
        'badge': '#BFC7D5',
        'badge_dark': '#162331',
        'mark': 'P',
        'phrase': 'La nave ya presume un poco.',
    },
    'Oro': {
        'edge': '#D9A833',
        'accent': '#FFD35C',
        'badge': '#D9A833',
        'badge_dark': '#3A2A09',
        'mark': 'O',
        'phrase': 'Eso merece una vuelta galactica.',
    },
}

ACHIEVEMENT_GROUPS = [
    {
        'categoria': 'Tiempo',
        'stat': 'tiempo_vivo',
        'unit': 's',
        'tiers': {
            'Bronce': ('tiempo_cadete', 'Cadete del Vacio', 'Sobrevive 1 minuto en una sola partida.', 60),
            'Plata': ('tiempo_veterano', 'Veterano Orbital', 'Sobrevive 3 minutos en una sola partida.', 180),
            'Oro': ('tiempo_cronauta', 'Crononauta del Vacio', 'Sobrevive 5 minutos completos en una sola partida.', 300),
        }
    },
    {
        'categoria': 'Combate',
        'stat': 'asteroides_destruidos',
        'unit': '',
        'tiers': {
            'Bronce': ('combate_iniciado', 'Primer Cazador', 'Destruye 20 asteroides con los laseres.', 20),
            'Plata': ('combate_veterano', 'Demoledor Estelar', 'Destruye 60 asteroides con los laseres.', 60),
            'Oro': ('combate_cazador', 'Cazador de Fragmentos', 'Destruye 100 asteroides con los laseres.', 100),
        }
    },
    {
        'categoria': 'Supervivencia',
        'stat': 'sin_danio',
        'unit': 's',
        'tiers': {
            'Bronce': ('supervivencia_firme', 'Escudo Sereno', 'Pasa 30 segundos sin recibir ningun dano.', 30),
            'Plata': ('supervivencia_preciso', 'Piloto Fantasma', 'Pasa 60 segundos sin recibir ningun dano.', 60),
            'Oro': ('supervivencia_intocable', 'Piloto Intocable', 'Pasa 90 segundos sin recibir ningun dano.', 90),
        }
    },
    {
        'categoria': 'Exploracion',
        'stat': 'distancia',
        'unit': 'm',
        'tiers': {
            'Bronce': ('exploracion_ruta', 'Ruta Marcada', 'Recorre 5,000 metros acumulados en una partida.', 5000),
            'Plata': ('exploracion_nomada', 'Nomada del Sector', 'Recorre 12,000 metros acumulados en una partida.', 12000),
            'Oro': ('exploracion_cartografo', 'Cartografo del Vacio', 'Recorre 20,000 metros acumulados en una partida.', 20000),
        }
    },
    {
        'categoria': 'Escaner',
        'stat': 'asteroides_escaneados',
        'unit': '',
        'tiers': {
            'Bronce': ('scanner_aprendiz', 'Pulso Inicial', 'Analiza 10 asteroides usando el escaner tactico.', 10),
            'Plata': ('scanner_rastreador', 'Rastreador de Nucleo', 'Analiza 30 asteroides usando el escaner tactico.', 30),
            'Oro': ('scanner_ojo', 'Ojo de la Galaxia', 'Analiza 50 asteroides usando el escaner tactico.', 50),
        }
    },
    {
        'categoria': 'Recursos',
        'stat': 'minerales',
        'unit': '',
        'tiers': {
            'Bronce': ('recursos_recolector', 'Recolector Alfa', 'Recolecta 50 minerales destruyendo asteroides.', 50),
            'Plata': ('recursos_prospector', 'Prospector de Cinturon', 'Recolecta 150 minerales destruyendo asteroides.', 150),
            'Oro': ('recursos_minero', 'Minero Alfa', 'Recolecta 250 minerales destruyendo asteroides.', 250),
        }
    },
    {
        'categoria': 'Ingenieria',
        'stat': 'mejoras_creadas',
        'unit': '',
        'tiers': {
            'Bronce': ('ingenieria_iniciada', 'Llave Inglesa', 'Fabrica 1 mejora de ingenieria.', 1),
            'Plata': ('ingenieria_avanzada', 'Tecnico de Hangar', 'Fabrica 2 mejoras de ingenieria.', 2),
            'Oro': ('ingenieria_suprema', 'Ingeniero Supremo', 'Fabrica las 3 mejoras de ingenieria disponibles.', 3),
        }
    },
    {
        'categoria': 'Velocidad',
        'stat': 'velocidad_alta',
        'unit': 's',
        'tiers': {
            'Bronce': ('velocidad_chispa', 'Chispa de Motor', 'Acumula 5 segundos viajando a mas de 4500 KM/H.', 5),
            'Plata': ('velocidad_turbo', 'Turbina Roja', 'Acumula 12 segundos viajando a mas de 4500 KM/H.', 12),
            'Oro': ('velocidad_imposible', 'Motor Imposible', 'Acumula 20 segundos viajando a mas de 4500 KM/H.', 20),
        }
    },
    {
        'categoria': 'Maniobra',
        'stat': 'dash_sin_danio',
        'unit': '',
        'tiers': {
            'Bronce': ('maniobra_agil', 'Giro Limpio', 'Realiza 8 maniobras dash sin recibir dano entre medio.', 8),
            'Plata': ('maniobra_acrobata', 'Acrobata del Vacio', 'Realiza 18 maniobras dash sin recibir dano entre medio.', 18),
            'Oro': ('maniobra_evasion', 'Evasion Perfecta', 'Realiza 30 maniobras dash sin recibir dano entre medio.', 30),
        }
    },
    {
        'categoria': 'Riesgo',
        'stat': 'fuera_sector_max',
        'unit': 's',
        'tiers': {
            'Bronce': ('riesgo_borde', 'Borde del Sector', 'Permanece 3 segundos fuera del sector y regresa vivo.', 3),
            'Plata': ('riesgo_retorno', 'Retorno Peligroso', 'Permanece 5 segundos fuera del sector y regresa vivo.', 5),
            'Oro': ('riesgo_abismo', 'Al Filo del Abismo', 'Permanece 7 segundos fuera del sector y regresa vivo.', 7),
        }
    },
]

ACHIEVEMENTS = []
for tier in ACHIEVEMENT_TIERS:
    for group in ACHIEVEMENT_GROUPS:
        ach_id, name, desc, target = group['tiers'][tier]
        ACHIEVEMENTS.append({
            'id': ach_id,
            'rango': tier,
            'categoria': group['categoria'],
            'stat': group['stat'],
            'unit': group['unit'],
            'nombre': name,
            'desc': desc,
            'objetivo': target,
        })


class AchievementPopup(Entity):
    """Mensaje bonito cuando se desbloquea un logro."""

    def __init__(self, achievement, on_closed=None, **kwargs):
        super().__init__(
            parent=camera.ui,
            ignore_paused=True,
            position=(0, 0.55),
            z=-90,
            **kwargs
        )

        tier = achievement.get('rango', 'Logro')
        style = POPUP_TIER_STYLES.get(tier, POPUP_TIER_STYLES['Plata'])
        edge_color = color.hex(style['edge'])
        accent_color = color.hex(style['accent'])
        badge_color = color.hex(style['badge'])
        badge_dark = color.hex(style['badge_dark'])
        phrase = style['phrase']
        mark = style['mark']
        self.on_closed = on_closed
        self.is_closing = False

        # Sombra exterior
        self.shadow = Entity(
            parent=self,
            model=Quad(radius=0.014),
            color=color.rgba(0, 0, 0, 160),
            scale=(0.545, 0.162),
            position=(0.008, -0.009),
            z=0.40
        )

        # Tarjeta HUD
        self.border = Entity(
            parent=self,
            model=Quad(radius=0.014),
            color=edge_color,
            scale=(0.530, 0.150),
            z=0.30
        )

        self.panel = Entity(
            parent=self,
            model=Quad(radius=0.014),
            color=color.hex('#061526'),
            scale=(0.518, 0.138),
            z=0.20
        )

        # Franja y lineas de categoria
        Entity(
            parent=self,
            model='quad',
            color=edge_color,
            scale=(0.006, 0.112),
            position=(-0.252, 0),
            z=-0.20
        )

        Entity(
            parent=self,
            model='quad',
            color=edge_color,
            scale=(0.420, 0.003),
            position=(0.018, 0.061),
            z=-0.20
        )

        Entity(
            parent=self,
            model='quad',
            color=color.hex('#17304A'),
            scale=(0.265, 0.003),
            position=(0.094, -0.061),
            z=-0.20
        )

        # Medalla simple
        Entity(
            parent=self,
            model='circle',
            color=badge_dark,
            scale=(0.075, 0.075),
            position=(-0.196, 0.002),
            z=-0.12
        )

        Entity(
            parent=self,
            model='circle',
            color=badge_color,
            scale=(0.057, 0.057),
            position=(-0.196, 0.002),
            z=-0.18
        )

        Entity(
            parent=self,
            model='circle',
            color=color.hex('#061526'),
            scale=(0.041, 0.041),
            position=(-0.196, 0.002),
            z=-0.22
        )

        Text(
            parent=self,
            text=mark,
            origin=(0, 0),
            position=(-0.196, -0.009),
            scale=0.46,
            color=accent_color,
            z=-0.30
        )

        Entity(
            parent=self,
            model='quad',
            color=badge_color,
            scale=(0.040, 0.005),
            position=(-0.196, -0.031),
            z=-0.22
        )

        # Texto principal
        Text(
            parent=self,
            text='LOGRO DESBLOQUEADO',
            position=(-0.135, 0.045),
            scale=0.53,
            color=color.hex('#66E8FF'),
            z=-0.30
        )

        Text(
            parent=self,
            text=achievement['nombre'],
            position=(-0.135, 0.010),
            scale=fitted_text_scale(achievement['nombre'], 0.82, 22, 0.58),
            color=color.white,
            z=-0.30
        )

        Text(
            parent=self,
            text=phrase,
            position=(-0.135, -0.034),
            scale=fitted_text_scale(phrase, 0.50, 37, 0.40),
            color=color.hex('#C6D6E0'),
            z=-0.30
        )

        Text(
            parent=self,
            text='ASTRA 3D',
            origin=(0, 0),
            position=(0.213, 0.045),
            scale=0.33,
            color=color.hex('#6E8798'),
            z=-0.30
        )

        # Animación de entrada
        self.scale = (0.84, 0.84, 0.84)
        self.animate_y(0.34, duration=0.30, curve=curve.out_back)
        self.animate_scale((1, 1, 1), duration=0.30, curve=curve.out_back)

        # Se cierra solo
        invoke(self.close, delay=3.5)

    def close(self):
        if not self or self.is_closing:
            return

        self.is_closing = True

        self.animate_y(0.55, duration=0.22, curve=curve.in_back)
        self.animate_scale((0.86, 0.86, 0.86), duration=0.22, curve=curve.in_back)
        destroy(self, delay=0.35)
        if self.on_closed:
            invoke(self.on_closed, delay=0.36)


class AchievementManager(Entity):
    """Sistema global de logros persistentes y estadísticas de una partida."""

    def __init__(self, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.save_path = os.path.join(os.path.dirname(__file__), 'achievements_save.json')
        self.defs = ACHIEVEMENTS
        self.def_by_id = {a['id']: a for a in self.defs}
        self.player = None
        self.unlocked = {a['id']: False for a in self.defs}
        self.stats = {}
        self.last_pos = None
        self.refresh_callback = None
        self.popup_queue = []
        self.active_popup = None
        self.reset_run()

    def _is_gameplay_active(self):
        """Indica si los avisos de logros pueden verse en pantalla."""
        return bool(
            self.player
            and getattr(self.player, 'enabled', False)
            and not getattr(self.player, 'is_dead', False)
            and not getattr(self.player, 'is_cinematic', False)
            and not application.paused
        )

    def _show_next_popup(self):
        """Muestra un solo logro y espera a que termine antes del siguiente."""
        # Previene superposición por race condition entre update() y on_closed
        if self.active_popup and bool(self.active_popup) and not getattr(self.active_popup, 'is_closing', False):
            return
            
        self.active_popup = None
        if not self.popup_queue or not self._is_gameplay_active():
            return

        achievement = self.popup_queue.pop(0)
        self.active_popup = AchievementPopup(
            achievement,
            on_closed=self._show_next_popup,
        )

    def set_player(self, player):
        self.player = player
        self.last_pos = Vec3(player.position) if player else None

    def set_refresh_callback(self, callback):
        self.refresh_callback = callback

    def set_account(self, acc_id):
        if acc_id == 'guest':
            self.save_path = None
        else:
            self.save_path = os.path.join(os.path.dirname(__file__), f'achievements_{acc_id}.json')
        self.load()

    def load(self):
        # Reset unlocked before loading
        self.unlocked = {a['id']: False for a in self.defs}
        if not self.save_path:
            return
        try:
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                saved_unlocked = data.get('unlocked', {})
                for ach in self.defs:
                    self.unlocked[ach['id']] = bool(saved_unlocked.get(ach['id'], False))
                if self.sync_lower_tiers():
                    self.save()
        except Exception as e:
            print(f"[Logros]: No se pudo cargar el guardado: {e}")

    def save(self):
        if not self.save_path:
            return
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump({'unlocked': self.unlocked}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Logros]: No se pudo guardar: {e}")

    def reset_run(self):
        self.stats = {
            'tiempo_vivo': 0.0,
            'asteroides_destruidos': 0,
            'sin_danio': 0.0,
            'distancia': 0.0,
            'asteroides_escaneados': 0,
            'minerales': 0,
            'mejoras_creadas': set(),
            'velocidad_alta': 0.0,
            'dash_sin_danio': 0,
            'fuera_sector_actual': 0.0,
            'fuera_sector_max': 0.0,
        }
        self.last_pos = Vec3(self.player.position) if self.player else None

    def format_progress(self, ach_id):
        achievement = self.def_by_id.get(ach_id)
        if not achievement:
            return "0/0"

        target = achievement['objetivo']
        value = self.get_stat_value(achievement['stat'])
        if achievement.get('unit') in ('s', 'm'):
            value = int(value)
        return f"{min(value, target)}/{target}{achievement.get('unit', '')}"

    def get_stat_value(self, stat_name):
        value = self.stats.get(stat_name, 0)
        if isinstance(value, set):
            return len(value)
        return value

    def sync_lower_tiers(self):
        changed = False
        for group in ACHIEVEMENT_GROUPS:
            tier_ids = [group['tiers'][tier][0] for tier in ACHIEVEMENT_TIERS]
            unlocked_indexes = [i for i, ach_id in enumerate(tier_ids) if self.unlocked.get(ach_id, False)]
            if not unlocked_indexes:
                continue

            highest_unlocked = max(unlocked_indexes)
            for ach_id in tier_ids[:highest_unlocked]:
                if not self.unlocked.get(ach_id, False):
                    self.unlocked[ach_id] = True
                    changed = True
        return changed

    def unlock_by_stat(self, stat_name):
        value = self.get_stat_value(stat_name)
        for achievement in self.defs:
            if achievement.get('stat') == stat_name and value >= achievement['objetivo']:
                self.unlock(achievement['id'])

    def unlock(self, ach_id):
        if self.unlocked.get(ach_id, False):
            return
        achievement = self.def_by_id.get(ach_id)
        if not achievement:
            return
        self.unlocked[ach_id] = True
        self.save()
        self.popup_queue.append(achievement)
        
        # Reproducir sonido de logro
        if hasattr(self, 'player') and hasattr(self.player, 'game_app') and hasattr(self.player.game_app, 'audio_manager'):
            self.player.game_app.audio_manager.play_achievement()
            
        if self.active_popup is None:
            self._show_next_popup()
        print(f"[Logros]: Desbloqueado -> {achievement['nombre']}")
        
        tier = achievement.get('tier', 'Bronce')
        pts = {'Bronce': 500, 'Plata': 1500, 'Oro': 5000}.get(tier, 500)
        if hasattr(self, 'player') and hasattr(self.player, 'add_score'):
            self.player.add_score(pts)
            
        if self.refresh_callback:
            self.refresh_callback()

    def update(self, dt=None, player=None):
        # Ursina llama automaticamente a update() sin parametros por ser Entity.
        # Para que no se caiga el juego ni cuente doble, solo actualizamos
        # cuando PlayerShip lo llama con time.dt y self.
        if dt is None or player is None:
            gameplay_active = self._is_gameplay_active()
            if self.active_popup:
                self.active_popup.enabled = gameplay_active
            elif gameplay_active and self.popup_queue:
                self._show_next_popup()
            return
        if not player or not getattr(player, 'enabled', False):
            return
        if getattr(player, 'is_dead', False) or getattr(player, 'is_cinematic', False):
            self.last_pos = Vec3(player.position)
            return

        self.stats['tiempo_vivo'] += dt
        self.stats['sin_danio'] += dt

        if self.last_pos is not None:
            moved = distance(player.position, self.last_pos)
            if moved < 1000:  # protección por si se reinicia/teletransporta la nave
                self.stats['distancia'] += moved
        self.last_pos = Vec3(player.position)

        display_speed = abs(getattr(player, 'current_speed', 0)) * 20
        if display_speed >= 4500:
            self.stats['velocidad_alta'] += dt

        sector_radius = getattr(player, 'sector_radius', 2500)
        outside_sector = player.position.length() > sector_radius
        if outside_sector:
            self.stats['fuera_sector_actual'] += dt
            self.stats['fuera_sector_max'] = max(self.stats['fuera_sector_max'], self.stats['fuera_sector_actual'])
        else:
            if self.stats['fuera_sector_actual'] > 0:
                self.unlock_by_stat('fuera_sector_max')
            self.stats['fuera_sector_actual'] = 0.0

        self.check_continuous_goals()

    def check_continuous_goals(self):
        self.unlock_by_stat('tiempo_vivo')
        self.unlock_by_stat('sin_danio')
        self.unlock_by_stat('distancia')
        self.unlock_by_stat('velocidad_alta')

    def register_damage_taken(self):
        self.stats['sin_danio'] = 0.0
        self.stats['dash_sin_danio'] = 0

    def register_dash(self):
        self.stats['dash_sin_danio'] += 1
        self.unlock_by_stat('dash_sin_danio')

    def register_scan_count(self, amount):
        if amount <= 0:
            return
        self.stats['asteroides_escaneados'] += amount
        self.unlock_by_stat('asteroides_escaneados')

    def register_asteroid_destroyed(self, asteroid):
        self.stats['asteroides_destruidos'] += 1
        self.unlock_by_stat('asteroides_destruidos')

    def register_materials(self, amount):
        self.stats['minerales'] += amount
        self.unlock_by_stat('minerales')

    def register_craft(self, recipe_name):
        self.stats['mejoras_creadas'].add(recipe_name)
        self.unlock_by_stat('mejoras_creadas')


class AchievementsMenu(Entity):
    """Pantalla de logros estilo futurista oscuro."""

    def __init__(self, main_menu, achievement_manager, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, ignore_paused=True, **kwargs)
        self.main_menu = main_menu
        self.manager = achievement_manager
        self.active_tier = 'Bronce'

        if self.manager:
            self.manager.set_refresh_callback(self.refresh)

        # =========================
        # PANEL PRINCIPAL
        # =========================

        self.border = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#00EFFF'),
            scale=(1.56, 0.98),
            position=(0, 0),
            z=0.30
        )

        # Panel oscuro principal
        self.panel = Entity(
            parent=self,
            model=Quad(radius=0.025),
            color=color.hex('#050D19'),
            scale=(1.53, 0.95),
            position=(0, 0),
            z=0.20
        )

        # Sombra interna azul
        self.inner_panel = Entity(
            parent=self,
            model=Quad(radius=0.018),
            color=color.hex('#071A2E'),
            scale=(1.46, 0.86),
            position=(0, -0.015),
            z=0.10
        )

        # =========================
        # TÍTULO
        # =========================

        Text(
            parent=self,
            text='LOGROS DE LA NAVE',
            origin=(0, 0),
            position=(0, 0.42),
            scale=2.55,
            color=color.white,
            z=-0.30
        )

        Text(
            parent=self,
            text='Retos difíciles que debe cumplir la nave durante el vuelo',
            origin=(0, 0),
            position=(0, 0.37),
            scale=0.82,
            color=color.hex('#D8E7F0'),
            z=-0.30
        )

        # Línea cyan debajo del título
        Entity(
            parent=self,
            model='quad',
            color=color.hex('#00EFFF'),
            scale=(1.35, 0.004),
            position=(0, 0.32),
            z=-0.20
        )

        # Pequeño detalle del centro
        Entity(
            parent=self,
            model='quad',
            color=color.hex('#00EFFF'),
            scale=(0.025, 0.010),
            position=(0, 0.315),
            rotation_z=45,
            z=-0.25
        )

        # HUD del rango seleccionado
        self.tier_label = Text(
            parent=self,
            text='',
            position=(-0.65, 0.23),
            scale=0.65,
            color=color.hex('#8FEFFF'),
            z=-0.30
        )

        self.tier_progress = Text(
            parent=self,
            text='',
            origin=(0, 0),
            position=(0.50, 0.27),
            scale=1.2,
            color=color.hex('#D8E7F0'),
            z=-0.30
        )



        self.tier_buttons = {}
        tier_x = {'Bronce': -0.45, 'Plata': -0.15, 'Oro': 0.15}
        for tier in ACHIEVEMENT_TIERS:
            self.tier_buttons[tier] = Button(
                parent=self,
                text=tier.upper(),
                scale=(0.28, 0.05),
                position=(tier_x[tier], 0.27),
                color=color.hex('#061526'),
                highlight_color=color.hex('#BFC7D5'),
                text_color=color.white,
                on_click=lambda selected=tier: self.set_tier(selected),
                z=-0.30
            )

        # =========================
        # CONTENEDOR SCROLL Y TARJETAS
        # =========================

        self.content = Entity(parent=self, z=0, y=0)
        self.scroll_y = 0
        self.cards = []
        self.card_width = 1.35
        self.card_height = 0.22
        self.spacing = 0.25

        for ach in ACHIEVEMENTS:
            card = Entity(parent=self.content, model=Quad(radius=0.015), color=color.hex('#071C31'), scale=(self.card_width, self.card_height), position=(0, 0), z=-0.05, enabled=False)
            card_border = Entity(parent=card, model=Quad(radius=0.015), color=color.hex('#143A55'), scale=(1.01, 1.05), z=0.01)

            t_category = Text(parent=self.content, text=ach['categoria'].upper(), position=(0, 0), scale=0.85, color=color.hex('#00EFFF'), z=-0.25, enabled=False)
            t_title = Text(parent=self.content, text=ach['nombre'], position=(0, 0), scale=1.5, color=color.white, z=-0.25, enabled=False)
            t_desc = Text(parent=self.content, text=ach['desc'], position=(0, 0), scale=0.9, color=color.hex('#C6D6E0'), z=-0.25, wordwrap=55, enabled=False)
            
            p_bg = Entity(parent=self.content, model=Quad(radius=0.008), color=color.hex('#061526'), scale=(0.35, 0.035), position=(0, 0), z=-0.16, enabled=False)
            p_fill = Entity(parent=self.content, model=Quad(radius=0.008), color=color.hex('#00EFFF'), scale=(0.001, 0.035), position=(0, 0), z=-0.24, enabled=False)
            t_prog = Text(parent=self.content, text='', origin=(0, 0), position=(0, 0), scale=1.1, color=color.white, z=-0.30, enabled=False)
            
            self.cards.append({
                'ach': ach,
                'card': card,
                'border': card_border,
                't_category': t_category,
                't_title': t_title,
                't_desc': t_desc,
                'p_bg': p_bg,
                'p_fill': p_fill,
                't_prog': t_prog
            })

        # =========================
        # BOTÓN VOLVER
        # =========================

        self.btn_back = Button(
            parent=self,
            text='VOLVER',
            scale=(0.32, 0.060),
            position=(0, -0.41),
            color=color.hex('#8B0000'),
            highlight_color=color.hex('#D61F1F'),
            text_color=color.white,
            on_click=self.close_achievements,
            z=-0.30
        )

    def input(self, key):
        if not self.enabled: return
        
        active_count = sum(1 for c in self.cards if c['ach'].get('rango') == self.active_tier)
        max_scroll = max(0, (active_count - 1) * self.spacing)
        
        if key == 'scroll up':
            self.scroll_y = max(0, self.scroll_y - self.spacing)
        elif key == 'scroll down':
            self.scroll_y = min(max_scroll, self.scroll_y + self.spacing)

    def update(self):
        if self.enabled and hasattr(self, 'cards'):
            self.content.y += (self.scroll_y - self.content.y) * 0.25
            self.update_scroll()

    def set_tier(self, tier):
        self.active_tier = tier
        self.scroll_y = 0
        self.content.y = 0
        self.refresh()

    def open_achievements(self, caller=None):
        self.caller = caller
        if self.caller:
            self.caller.disable()
        else:
            self.main_menu.ui_container.disable()
        self.set_tier('Bronce')
        self.enable()

    def close_achievements(self):
        self.disable()
        if hasattr(self, 'caller') and self.caller:
            self.caller.enable()
        else:
            self.main_menu.ui_container.enable()

    def refresh(self):
        if not self.manager:
            return

        tier_achievements = [ach for ach in ACHIEVEMENTS if ach.get('rango') == self.active_tier]
        active_color = color.hex(TIER_COLORS.get(self.active_tier, '#00EFFF'))
        completed = sum(1 for ach in tier_achievements if self.manager.unlocked.get(ach['id'], False))
        total = max(1, len(tier_achievements))
        tier_ratio = completed / total

        self.tier_label.text = f'RANGO {self.active_tier.upper()}'
        self.tier_progress.text = f'{completed}/{total} COMPLETADOS'

        for tier, button in self.tier_buttons.items():
            if tier == self.active_tier:
                button.color = color.hex('#BFC7D5')
                button.text_color = color.black if tier in ('Bronce', 'Plata', 'Oro') else color.white
            else:
                button.color = color.hex('#061526')
                button.text_color = color.white

        start_y = 0.06
        for c in self.cards:
            ach = c['ach']
            if ach.get('rango') != self.active_tier:
                c['card'].original_enabled = False
                continue
                
            y = start_y
            start_y -= self.spacing
            
            c['card'].y = y
            c['card'].original_enabled = True
            
            c['t_category'].position = (-0.62, y + 0.08)
            c['t_title'].position = (-0.62, y + 0.04)
            c['t_desc'].position = (-0.62, y - 0.02)
            
            c['p_bg'].position = (0.45, y)
            c['t_prog'].position = (0.45, y)
            c['p_fill'].y = y
            
            unlocked = self.manager.unlocked.get(ach['id'], False)
            value = self.manager.get_stat_value(ach['stat'])
            ratio = 1.0 if unlocked else min(float(value) / max(1, ach['objetivo']), 1.0)
            
            c['p_fill'].scale_x = max(0.001, 0.35 * ratio)
            c['p_fill'].x = 0.45 - 0.175 + (c['p_fill'].scale_x / 2)
            
            if unlocked:
                c['border'].color = active_color
                c['t_category'].color = active_color
                c['p_fill'].color = active_color
                c['t_prog'].text = 'COMPLETADO'
                c['t_prog'].color = color.white
            else:
                c['border'].color = color.hex('#143A55')
                c['t_category'].color = color.hex('#00EFFF')
                c['p_fill'].color = color.hex('#00EFFF')
                c['t_prog'].text = self.manager.format_progress(ach['id'])
                c['t_prog'].color = color.white
                
        self.update_scroll()

    def update_scroll(self):
        for c in self.cards:
            if not getattr(c['card'], 'original_enabled', False):
                c['card'].enabled = False
                c['t_category'].enabled = False
                c['t_title'].enabled = False
                c['t_desc'].enabled = False
                c['p_bg'].enabled = False
                c['p_fill'].enabled = False
                c['t_prog'].enabled = False
                continue
                
            gy = c['card'].y + self.content.y
            
            alpha = 1.0
            if gy > 0.10:
                alpha = max(0, 1.0 - (gy - 0.10) / 0.08)
            elif gy < -0.25:
                alpha = max(0, 1.0 - (-0.25 - gy) / 0.10)
                
            is_visible = alpha > 0
            
            c['card'].enabled = is_visible
            c['t_category'].enabled = is_visible
            c['t_title'].enabled = is_visible
            c['t_desc'].enabled = is_visible
            c['p_bg'].enabled = is_visible
            c['p_fill'].enabled = is_visible
            c['t_prog'].enabled = is_visible
            
            if is_visible:
                c['card'].alpha = alpha
                c['border'].alpha = alpha
                c['t_category'].alpha = alpha
                c['t_title'].alpha = alpha
                c['t_desc'].alpha = alpha
                c['p_bg'].alpha = alpha
                c['p_fill'].alpha = alpha
                c['t_prog'].alpha = alpha
