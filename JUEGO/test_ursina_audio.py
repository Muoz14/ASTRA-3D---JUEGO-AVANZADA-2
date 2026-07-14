from ursina import *
import os
import time

app = Ursina()

file_path = os.path.join(os.path.dirname(__file__), "assets", "ai_audio", "startup.mp3")
print("Trying to play:", file_path)
a = Audio(file_path, autoplay=True, volume=1.0)

def update():
    pass

def delayed_stop():
    print("Done playing.")
    application.quit()

invoke(delayed_stop, delay=3)
app.run()
