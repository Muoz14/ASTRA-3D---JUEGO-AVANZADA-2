from ursina import *
from player import PlayerShip
from cinematics import AltechSquadCinematic, BossIntroCinematic

class DummyMissionManager:
    def __init__(self):
        self.ui = Entity()
        self.waypoint = Entity()
        self.altech_squad_spawned = False
    
    def get_active_target(self):
        return None
        
    def complete_mission(self, ms_id):
        pass
        
    def set_mission_progress(self, ms_id, progress):
        pass
        
    def get_tracked_mission(self):
        class DummyM:
            id = "main_03"
            target_pos = None
        return DummyM()

class DummyCompanion:
    def __init__(self):
        self.ui = Entity()
    def trigger_dialogue(self, dialogues):
        print(f"DIALOGO: {dialogues}")

class DummyGameApp:
    def __init__(self):
        pass

app = Ursina(development_mode=True)
window.title = "TEST CINEMATICAS"

# Minimal environment
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(50, 50, 50, 255))
Sky(color=color.black)

game_app = DummyGameApp()
player = PlayerShip(game_app=game_app)
player.mission_manager = DummyMissionManager()
player.ai_companion = DummyCompanion()
game_app.player = player

# Cinematics
altech_cine = AltechSquadCinematic(player, game_app)
boss_cine = BossIntroCinematic(player, game_app)

def update():
    pass

def input(key):
    if key == '1':
        print(">> Jugando AltechSquadCinematic")
        altech_cine.is_playing = False # Reset for re-playability
        altech_cine.play()
    if key == '2':
        print(">> Jugando BossIntroCinematic")
        boss_cine.is_playing = False # Reset for re-playability
        boss_cine.play()
    if key == '0':
        print(">> Limpiando naves de prueba")
        from ursina import scene, destroy
        for e in list(scene.entities):
            if type(e).__name__ == 'EnemyShip' or type(e).__name__ == 'Mothership':
                destroy(e)

Text(text="1: Test Escuadrón Altech | 2: Test Nodriza | 0: Limpiar Escena", position=(-0.85, 0.45))

app.run()
