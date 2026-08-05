import sys
from ursina import *
from main import GameApp

app = Ursina()
game = GameApp()
game.start_actual_game()

def skip_cin():
    print("SKIPPING CINEMATIC VIA skip_cinematic()")
    if hasattr(game, 'intro_cinematic') and game.intro_cinematic.is_playing:
        game.intro_cinematic.skip_cinematic()
        
invoke(skip_cin, delay=2.0)
invoke(application.quit, delay=8.0)

app.run()
