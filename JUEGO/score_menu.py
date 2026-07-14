from ursina import *

def get_rank(score):
    if score < 5000:
        return 'Cadete Espacial', color.hex('#BFC7D5')
    elif score < 15000:
        return 'Teniente de Vuelo', color.hex('#6EEBFF')
    elif score < 35000:
        return 'Capitán Estelar', color.hex('#D9A833')
    else:
        return 'Comandante Atlas', color.hex('#FF4D5A')

class ScoreMenu(Entity):
    def __init__(self, main_menu, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, z=-2, **kwargs)
        self.main_menu = main_menu
        
        self.bg_panel = Entity(parent=self, model='quad', color=color.black, alpha=0.85, scale=(99, 99), z=0.1)
        
        # Titulo
        Text(parent=self, text='PUNTUACIÓN ATLAS', position=(0, 0.40), scale=3, origin=(0,0), color=color.white, z=-1)
        
        # Tarjeta de Piloto (Izquierda)
        self.pilot_panel = Entity(parent=self, model=Quad(radius=0.02), color=color.hex('#071526'), scale=(0.6, 0.6), position=(-0.35, 0), z=0)
        self.pilot_border = Entity(parent=self.pilot_panel, model=Quad(radius=0.02), color=color.hex('#6EEBFF'), scale=(1.02, 1.02), z=0.01)
        
        self.pilot_name_txt = Text(parent=self.pilot_panel, text='Piloto', position=(0, 0.4), origin=(0,0), scale=2, color=color.white, z=-1)
        self.pilot_rank_txt = Text(parent=self.pilot_panel, text='Rango', position=(0, 0.25), origin=(0,0), scale=1.5, color=color.cyan, z=-1)
        
        self.pilot_score_txt = Text(parent=self.pilot_panel, text='Puntos Totales: 0', position=(-0.4, 0.05), origin=(-0.5,0), scale=1.3, color=color.light_gray, z=-1)
        self.pilot_high_txt = Text(parent=self.pilot_panel, text='Mejor Partida: 0', position=(-0.4, -0.1), origin=(-0.5,0), scale=1.3, color=color.light_gray, z=-1)
        self.pilot_time_txt = Text(parent=self.pilot_panel, text='Tiempo de Vuelo: 0s', position=(-0.4, -0.25), origin=(-0.5,0), scale=1.3, color=color.light_gray, z=-1)

        # Leaderboard Local (Derecha)
        self.lb_panel = Entity(parent=self, model=Quad(radius=0.02), color=color.hex('#071526'), scale=(0.6, 0.6), position=(0.35, 0), z=0)
        self.lb_border = Entity(parent=self.lb_panel, model=Quad(radius=0.02), color=color.hex('#FF9A55'), scale=(1.02, 1.02), z=0.01)
        
        Text(parent=self.lb_panel, text='CLASIFICACIÓN LOCAL', position=(0, 0.4), origin=(0,0), scale=1.8, color=color.white, z=-1)
        
        self.lb_entries = []
        for i in range(5):
            entry_txt = Text(parent=self.lb_panel, text=f'{i+1}. ---', position=(-0.4, 0.2 - (i * 0.15)), origin=(-0.5,0), scale=1.4, color=color.gray, z=-1)
            score_txt = Text(parent=self.lb_panel, text='0 pts', position=(0.4, 0.2 - (i * 0.15)), origin=(0.5,0), scale=1.4, color=color.cyan, z=-1)
            self.lb_entries.append((entry_txt, score_txt))

        # Botón Volver
        self.btn_back = Button(parent=self, text='VOLVER', scale=(0.3, 0.08), position=(0, -0.40),
                               color=color.dark_gray, highlight_color=color.gray, on_click=self.close_score, z=-1)

    def open_score(self):
        self.enable()
        self.main_menu.ui_container.disable()
        self.refresh_stats()
        
    def close_score(self):
        self.disable()
        self.main_menu.ui_container.enable()

    def refresh_stats(self):
        manager = getattr(self.main_menu, 'account_manager', None)
        if not manager: return
        
        current_id = getattr(self.main_menu, 'current_account_id', None)
        if not current_id or current_id == 'guest':
            # Invitado
            self.pilot_name_txt.text = 'Invitado'
            self.pilot_rank_txt.text = 'Sin Rango'
            self.pilot_rank_txt.color = color.gray
            self.pilot_score_txt.text = 'Puntos Totales: 0'
            self.pilot_high_txt.text = 'Mejor Partida: 0'
            self.pilot_time_txt.text = 'Tiempo de Vuelo: 0s'
        else:
            acc = next((a for a in manager.accounts if a['id'] == current_id), None)
            if acc:
                stats = acc.get('stats', {})
                tot = int(stats.get('total_score', 0))
                high = int(stats.get('high_score', 0))
                t_flown = int(stats.get('time_flown', 0))
                
                self.pilot_name_txt.text = acc.get('name', 'Piloto')
                rank_str, rank_color = get_rank(tot)
                self.pilot_rank_txt.text = rank_str
                self.pilot_rank_txt.color = rank_color
                
                self.pilot_score_txt.text = f'Puntos Totales: {tot:,}'
                self.pilot_high_txt.text = f'Mejor Partida: {high:,}'
                
                mins, secs = divmod(t_flown, 60)
                self.pilot_time_txt.text = f'Tiempo de Vuelo: {mins}m {secs}s'

        # Actualizar Leaderboard
        valid_accs = [a for a in manager.accounts if 'stats' in a]
        valid_accs.sort(key=lambda x: x['stats'].get('total_score', 0), reverse=True)
        
        for i in range(5):
            entry_txt, score_txt = self.lb_entries[i]
            if i < len(valid_accs):
                a = valid_accs[i]
                pts = int(a['stats'].get('total_score', 0))
                entry_txt.text = f"{i+1}. {a['name'][:12]}"
                entry_txt.color = color.white if a['id'] == current_id else color.light_gray
                score_txt.text = f"{pts:,} pts"
                score_txt.color = color.cyan if a['id'] == current_id else color.gray
            else:
                entry_txt.text = f"{i+1}. ---"
                entry_txt.color = color.dark_gray
                score_txt.text = ""
