import ctypes
import os

def test_vol():
    file_path = os.path.join(os.path.dirname(__file__), "assets", "ai_audio", "startup.mp3")
    if not os.path.exists(file_path):
        for f in os.listdir(os.path.join(os.path.dirname(__file__), "assets", "ai_audio")):
            if f.endswith('.mp3'):
                file_path = os.path.join(os.path.dirname(__file__), "assets", "ai_audio", f)
                break
                
    alias = "test_audio"
    
    ctypes.windll.winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, None)
    
    buffer = ctypes.create_unicode_buffer(255)
    err = ctypes.windll.winmm.mciSendStringW(f'setaudio {alias} volume to 0', buffer, 254, None)
    if err:
        ctypes.windll.winmm.mciGetErrorStringW(err, buffer, 255)
        print("Error:", buffer.value)
    else:
        print("Volume set to 0. Error 0.")
    
test_vol()
