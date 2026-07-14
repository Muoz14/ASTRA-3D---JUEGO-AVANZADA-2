from ursina import *

app = Ursina(
    title='Examen II Parcial Avanzada 2 - Angel Muñoz',
    borderless=False,
    fullscreen=False,
)

window.color =  color.dark_gray
window.center_on_screen()
window.fps_counter.enabled = False
window.exit_button.visible = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

app.run()