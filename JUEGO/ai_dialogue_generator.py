import random

class DialogueGenerator:
    """Generador procedimental de diálogos para la IA de la nave."""
    
    def __init__(self):
        # --- Fragmentos para estado Aleatorio (Idle) ---
        self.idle_subjects = [
            "El vacío del espacio", "Los escáneres estáticos", "El sistema de navegación", 
            "El núcleo de energía", "El silencio cósmico", "El radar de largo alcance",
            "La temperatura del reactor", "El panel de sensores"
        ]
        self.idle_actions = [
            "está mostrando lecturas inusuales", "parece estar en completa calma", 
            "registra fluctuaciones menores", "mantiene una estabilidad perfecta",
            "detecta ecos de radiación antigua", "funciona dentro de los parámetros normales",
            "capta una leve interferencia electromagnética"
        ]
        self.idle_contexts = [
            "en este sector abandonado.", "más allá de nuestra trayectoria actual.",
            "lo cual es muy tranquilizador.", "y me resulta extrañamente relajante.",
            "pero sigo alerta por si acaso.", "así que puedes relajarte un poco, Capitán.",
            "lo registraré en la bitácora."
        ]
        
        # --- Fragmentos para Daño (Damage) ---
        self.damage_subjects = [
            "¡El casco", "¡Nuestros escudos", "¡La integridad estructural", 
            "¡El sistema de soporte vital"
        ]
        self.damage_actions = [
            "acaba de recibir un impacto crítico!", "está cediendo rápidamente!", 
            "sufrió daños considerables!", "está perdiendo energía por el golpe!",
            "está comprometido!"
        ]
        self.damage_contexts = [
            "¡Necesitamos evasión inmediata!", "¡Cuidado con el próximo ataque!",
            "¡Mantén la nave estable, por favor!", "¡Confío en tus reflejos para salir de esta!",
            "¡No soportaremos muchos más de esos!"
        ]
        
        # --- Fragmentos para Turbo (Boost) ---
        self.boost_subjects = [
            "¡Los propulsores principales", "¡Los inyectores de plasma", 
            "¡El motor de hipervelocidad", "¡Los sistemas de empuje"
        ]
        self.boost_actions = [
            "están al máximo rendimiento!", "acaban de encenderse con todo!", 
            "están quemando combustible rápidamente!", "han redirigido toda la energía!"
        ]
        self.boost_contexts = [
            "¡Qué velocidad tan increíble!", "¡Sujétate fuerte, Capitán!", 
            "¡Eres el mejor piloto para esto!", "¡Allá vamos!"
        ]
        
        # --- Fragmentos para Sobrecalentamiento (Overheat) ---
        self.overheat_subjects = [
            "¡Los cañones láser", "¡El sistema de armamento", "¡Los disipadores térmicos",
            "¡Los circuitos de disparo"
        ]
        self.overheat_actions = [
            "están a punto de fundirse!", "han superado el límite de calor!", 
            "necesitan un respiro urgente!", "están bloqueados por temperatura!"
        ]
        self.overheat_contexts = [
            "¡Relaja los gatillos un segundo!", "¡Espera a que se enfríen!",
            "¡Busca cobertura mientras se reinician!", "¡Dales tiempo para disipar la energía!"
        ]

    def generate(self, event_type):
        """Genera una frase uniendo fragmentos aleatorios según el contexto."""
        if event_type == "idle":
            s = random.choice(self.idle_subjects)
            a = random.choice(self.idle_actions)
            c = random.choice(self.idle_contexts)
        elif event_type == "damage":
            s = random.choice(self.damage_subjects)
            a = random.choice(self.damage_actions)
            c = random.choice(self.damage_contexts)
        elif event_type == "boost":
            s = random.choice(self.boost_subjects)
            a = random.choice(self.boost_actions)
            c = random.choice(self.boost_contexts)
        elif event_type == "overheat":
            s = random.choice(self.overheat_subjects)
            a = random.choice(self.overheat_actions)
            c = random.choice(self.overheat_contexts)
        else:
            return "..."
            
        return f"{s} {a} {c}"
        
    def glitch_text(self, text):
        """Simula un fallo en el sistema corrompiendo el texto progresivamente."""
        glitch_chars = "!@#$%^&*{}[];:/?310"
        words = text.split(" ")
        glitched_words = []
        
        for word in words:
            # Probabilidad de que una letra se corrompa por un símbolo o número
            new_word = ""
            for char in word:
                if char.isalpha() and random.random() < 0.20:
                    new_word += random.choice(glitch_chars)
                else:
                    new_word += char
            glitched_words.append(new_word)
            
        return " ".join(glitched_words)
        
    def get_phonetic_stutter(self, text):
        """Genera un tartamudeo fonético legible por TTS para simular corrupción de audio."""
        words = text.split(" ")
        stuttered_words = []
        
        for word in words:
            # Ignorar palabras muy cortas
            if len(word) > 3 and word.isalpha() and random.random() < 0.50:
                # Tartamudear la primera letra un par de veces
                stutter = f"{word[0]}-{word[0].lower()}-{word[0].lower()}-{word}"
                stuttered_words.append(stutter)
            else:
                stuttered_words.append(word)
                
            # Agregar algunas pausas dramáticas aleatorias
            if random.random() < 0.2:
                stuttered_words.append("...")
                
        return " ".join(stuttered_words)
