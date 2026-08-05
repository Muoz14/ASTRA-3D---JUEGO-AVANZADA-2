from ursina import *

app = Ursina( title = "Examen II Parcial - Angel Muñoz")

window.fps_counter.enabled = False
window.collider_counter.enabled = False
window.entity_counter.enabled = False
window.exit_button.enabled = False
window.color = color.white

app.run()