from ursina import Ursina
app = Ursina()

from main import GameApp
game = GameApp()

print("\n--- TEST START ---")
print("Selecting account...")
game.on_account_selected("cff85d78-fafc-46db-82b4-c3c5ea286a36", "Muoz")

print("Opening score menu...")
game.main_menu.score_menu.open_score()

print(f"Pilot name is now: {game.main_menu.score_menu.pilot_name_txt.text}")
print(f"Pilot rank is now: {game.main_menu.score_menu.pilot_rank_txt.text}")
print("--- TEST END ---\n")
