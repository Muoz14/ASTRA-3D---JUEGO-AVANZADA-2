from ursina import *
from ships import AVAILABLE_SHIPS
from menu import MenuDummyShip

app = Ursina()

bg = Entity()
ship = MenuDummyShip(parent=bg, position=(4.5, -2, 12), rotation=(0, 7, 0))
ship.set_config(AVAILABLE_SHIPS["nave1"])

def change_pilot():
    bg.disable()
    invoke(select_pilot, delay=1)

def select_pilot():
    ship.set_config(AVAILABLE_SHIPS["nave2"])
    ship.position = (4.5, -2, 12)
    ship.rotation = (0, 7, 0)
    bg.enable()

invoke(change_pilot, delay=2)

app.run()
