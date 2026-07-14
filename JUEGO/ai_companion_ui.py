from ursina import *
import textwrap

class CompanionUI(Entity):
    def __init__(self, **kwargs):
        # z=-20 asegura que el contenedor principal esté súper al frente de la cámara UI
        super().__init__(parent=camera.ui, z=-20, **kwargs)
        
        # Posición base en pantalla
        self.position = (0.55, 0.15)
        
        # Fondo del pop-up (reducido al ~50%)
        self.bg = Entity(
            parent=self, 
            model='quad',
            color=color.rgba(0.05, 0.08, 0.12, 0), 
            scale=(0.36, 0.08), # Ancho fijo de 0.36
            position=(0, 0.045),
            origin=(0, 0.5), # Ancla arriba
            z=0 
        )
        
        # Borde izquierdo decorativo
        self.border = Entity(
            parent=self, 
            model='quad', 
            color=color.rgba(0, 1, 1, 0), 
            scale=(0.006, 0.08), 
            position=(-0.18, 0.045), 
            origin=(0, 0.5),
            z=-1
        )
        
        # Título - Reducido al ~50%
        self.title = Text(
            parent=self,
            text='[ IA DE LA NAVE ]',
            position=(-0.165, 0.033),
            scale=1.2, # Discreto pero destacado
            color=color.rgba(0, 1, 1, 0),
            z=-2 
        )
        
        # Texto principal - Reducido al ~50%
        self.dialogue_text = Text(
            parent=self,
            text=' ',
            position=(-0.165, -0.005),
            scale=0.85, # Legible pero compacto
            color=color.rgba(1, 1, 1, 0),
            z=-2 
        )
        self.dialogue_text.text = ''
        
        self.active_sequence = None
        
    def show_message(self, message, duration=5.0):
        if self.active_sequence:
            self.active_sequence.kill()
            
        # 24 caracteres encajan perfectamente en el ancho 0.36 a escala 0.85
        wrapped_message = "\n".join(textwrap.wrap(message, width=24))
        self.dialogue_text.text = wrapped_message
        
        # Ajuste dinámico de altura ESTRICTO
        line_count = len(wrapped_message.split('\n'))
        
        # Base: 0.06 (cubre el padding superior, el título y el gap)
        # Altura por línea: ~0.025 (es el alto real de una línea de fuente a escala 0.85)
        new_height = 0.06 + (line_count * 0.025)
        
        # Como bg tiene origin=(0, 0.5), al escalar en Y solo crece hacia abajo
        self.bg.animate_scale((0.36, new_height), duration=0.2)
        self.border.animate_scale((0.006, new_height), duration=0.2)
        
        # Animación de aparición
        self.bg.animate_color(color.rgba(0.05, 0.08, 0.12, 0.85), duration=0.2)
        self.border.animate_color(color.cyan, duration=0.2)
        self.title.animate_color(color.cyan, duration=0.2)
        self.dialogue_text.animate_color(color.white, duration=0.2)
        
    def hide_message(self):
        self.bg.animate_color(color.rgba(0.05, 0.08, 0.12, 0), duration=0.5)
        self.border.animate_color(color.rgba(0, 1, 1, 0), duration=0.5)
        self.title.animate_color(color.rgba(0, 1, 1, 0), duration=0.5)
        self.dialogue_text.animate_color(color.rgba(1, 1, 1, 0), duration=0.5)

    def hide_message_instant(self):
        if self.active_sequence:
            self.active_sequence.kill()
            self.active_sequence = None
        self.bg.color = color.rgba(0.05, 0.08, 0.12, 0)
        self.border.color = color.rgba(0, 1, 1, 0)
        self.title.color = color.rgba(0, 1, 1, 0)
        self.dialogue_text.color = color.rgba(1, 1, 1, 0)
