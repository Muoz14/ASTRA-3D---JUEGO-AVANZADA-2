from ursina import *
# Importamos el controlador de primera persona
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina(
    title='Examen II Parcial Avanzada 2 - Angel Muñoz',
    borderless=False,
    fullscreen=False,
)

# Configuración de la ventana
window.color = color.dark_gray
window.center_on_screen()
window.fps_counter.enabled = False
window.exit_button.visible = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

# Interfaz de usuario (UI)
puntuacion = 0
texto_puntuacion = Text(text=f'Puntuacion: {puntuacion}', position=window.top_left)

# --- ENTORNO 3D ---

# 1. El suelo: OBLIGATORIO poner collider='box' para que el jugador no caiga al vacío
suelo = Entity(model='plane', scale=(20, 1, 20), color=color.white33, collider='box')

# 2. El cubo: Lo subimos un poco (y=1) y lo alejamos (z=5) para verlo al aparecer
cubo = Entity(model='cube', color=color.red, position=(0, 1, 5), collider='box')

# 3. La cámara libre (Jugador)
jugador = FirstPersonController()


# Nota: Si el ingeniero te pide una cámara que "vuele" (sin gravedad, modo espectador),
# solo tendrías que agregar esta línea:
jugador.gravity = 0

# --- LÓGICA DEL JUEGO ---

def update():
    # Rotamos el cubo suavemente
    cubo.rotation_y += 50 * time.dt
    cubo.rotation_x += 20 * time.dt

    # held_keys verifica si la tecla está presionada continuamente.
    # Modificamos jugador.y (el eje vertical) multiplicado por una velocidad (5) y time.dt
    if held_keys['shift']:
        jugador.y += 5 * time.dt

    if held_keys['control']:
        jugador.y -= 5 * time.dt


def input(key):
    global puntuacion

    # Cambiamos la tecla de puntuación al clic izquierdo del mouse,
    # ya que la barra espaciadora ahora se usa para saltar.
    if key == 'left mouse down':
        puntuacion += 1
        texto_puntuacion.text = f'Puntuacion: {puntuacion}'

    # Salida segura
    if key == 'escape':
        application.quit()


app.run()