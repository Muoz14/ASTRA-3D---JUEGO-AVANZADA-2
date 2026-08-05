from ursina import *

class EndingCinematic(Entity):
    def __init__(self, player, game, **kwargs):
        super().__init__(ignore_paused=True, **kwargs)
        self.player = player
        self.game = game
        self.is_playing = False
        
        self.top_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, 0.44), enabled=False, z=-5)
        self.bottom_bar = Entity(parent=camera.ui, model='quad', color=color.black, scale=(2, 0.15), position=(0, -0.44), enabled=False, z=-5)
        
        self.subtitle = Text(parent=camera.ui, text='', origin=(0, 0), position=(0, -0.44), scale=1.3, color=color.white, enabled=False, z=-6)
        
        # Portal para escapar
        self.portal = Entity(model=Cylinder(resolution=6), color=color.rgba(0, 255, 255, 180), scale=(0, 0.01, 0), rotation_x=90, unlit=True, enabled=False)
        self.portal_inner = Entity(parent=self.portal, model=Cylinder(resolution=6), color=color.white, scale=(0.8, 1.1, 0.8), unlit=True)
        
        # "Continuará" Text
        self.to_be_continued = Text(parent=camera.ui, text='Continuará...', origin=(0, 0), position=(0, 0), scale=3, color=color.rgba(255,255,255,0), enabled=False, z=-6)

    def play(self):
        self.is_playing = True
        self.player.is_cinematic = True
        
        # Stop gameplay UI
        self.player.hud_container.disable()
        if hasattr(self.player, 'mission_manager'):
            self.player.mission_manager.ui.disable()
            self.player.mission_manager.waypoint.disable()
            
        self.top_bar.enabled = True
        self.bottom_bar.enabled = True
        self.subtitle.enabled = True
        
        # Matamos previas anims
        if hasattr(camera, 'animations') and camera.animations:
            for anim in list(camera.animations):
                anim.kill()
                
        camera.parent = scene
        
        invoke(self.shot_1, delay=0.5)
        invoke(self.shot_2, delay=4.5)
        invoke(self.shot_3, delay=9.0)
        invoke(self.fade_text_out, delay=14.0)
        invoke(self.transition_to_menu, delay=16.0)
        invoke(self.cleanup, delay=18.5)

    def shot_1(self):
        # Toma lateral de la nave del jugador
        cam_offset = self.player.right * 15 + self.player.up * 5 + self.player.forward * -5
        camera.position = self.player.world_position + cam_offset
        camera.look_at(self.player)
        
        self.subtitle.text = "[TIERRA]: ¡Lo lograste Piloto! La Nodriza ha sido destruida."
        
        # Abrir portal al frente del jugador
        self.portal.position = self.player.world_position + self.player.forward * 100
        self.portal.rotation = self.player.rotation
        self.portal.rotation_x += 90
        self.portal.enabled = True
        self.portal.scale = (0, 0.01, 0)
        self.portal.animate_scale(Vec3(40, 0.01, 40), duration=2.0, curve=curve.out_back)

    def shot_2(self):
        # Toma desde atrás
        cam_offset = self.player.forward * -25 + self.player.up * 8
        camera.position = self.player.world_position + cam_offset
        camera.look_at(self.portal)
        
        self.subtitle.text = "[TIERRA]: Has limpiado el Sector Alfa con éxito. El siguiente sector te espera."
        
        # El jugador acelera hacia el portal
        self.player.animate_position(self.portal.world_position + self.player.forward * 50, duration=3.0, curve=curve.in_expo)

    def shot_3(self):
        self.subtitle.text = ""
        self.portal.animate_scale(Vec3(0, 0.01, 0), duration=0.5, curve=curve.in_back)
        
        # Ocultar la nave del jugador
        self.player.visible = False
        if hasattr(self.player, 'thrusters'):
            for t in self.player.thrusters:
                t.visible = False
        
        # Fade a negro total
        self.fade_overlay = Entity(parent=camera.ui, model='quad', color=color.rgba(0,0,0,0), scale=(window.aspect_ratio * 3, 3), z=-4)
        self.fade_overlay.animate_color(color.black, duration=1.0)
        
        # Mostrar continuará
        self.to_be_continued.enabled = True
        self.to_be_continued.animate_color(color.white, duration=2.0, delay=1.0)
        
    def fade_text_out(self):
        self.to_be_continued.animate_color(color.rgba(255,255,255,0), duration=1.5)
        
    def transition_to_menu(self):
        self.to_be_continued.enabled = False
        self.top_bar.enabled = False
        self.bottom_bar.enabled = False
        self.subtitle.enabled = False
        
        if hasattr(self.game, 'return_to_main_menu'):
            self.game.return_to_main_menu()
            
        # Ahora que el menú está cargado detrás de la pantalla negra, hacemos el fade in del menú (fade out de la pantalla negra)
        if hasattr(self, 'fade_overlay'):
            self.fade_overlay.animate_color(color.rgba(0,0,0,0), duration=2.0)
            
    def cleanup(self):
        if hasattr(self, 'fade_overlay'):
            destroy(self.fade_overlay)
        if hasattr(self, 'to_be_continued'):
            destroy(self.to_be_continued)
        destroy(self)
