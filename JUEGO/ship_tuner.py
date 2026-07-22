from ursina import *

class ShipTuner(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui, enabled=False, z=-100, **kwargs)
        self.player = player
        
        self.bg = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 200), scale=(0.7, 0.5), position=(0.5, 0.2), z=0.1)
        self.title = Text(parent=self, text="SHIP TUNER (Keyboard Mode)", scale=1.5, position=(0.18, 0.42), color=color.yellow, z=-0.1)
        
        self.instructions = Text(parent=self, text=
            "[1] Model Offset  [2] Model Rotation\n"
            "[3] Model Scale   [4] Laser Offset\n"
            "[5] Thruster Pos  [6] Thruster Scale\n\n"
            "CONTROLS: Arrows (X/Y) | W/S (Z)\n"
            "Press [ENTER] to print config.\n"
            "Press [F12] to close.", 
            scale=1, position=(0.18, 0.35), color=color.light_gray, z=-0.1)
            
        self.mode_text = Text(parent=self, text="MODE: 1 - Model Offset", scale=1.5, position=(0.18, 0.1), color=color.cyan, z=-0.1)
        self.val_text = Text(parent=self, text="VAL: (0, 0, 0)", scale=1.5, position=(0.18, 0.05), color=color.white, z=-0.1)
        
        self.current_mode = 1
        self.step_size = 0.05
        
        # Working variables
        self.v_model_offset = Vec3(0,0,0)
        self.v_model_rot = Vec3(0,0,0)
        self.v_model_scale = Vec3(1,1,1)
        self.v_laser = Vec3(0,0,0)
        self.v_thruster = Vec3(0,0,0)
        self.v_thruster_scale = Vec3(0.3, 0.3, 3.5)

    def on_enable(self):
        if self.player:
            self.v_model_offset = Vec3(*self.player.ship_model_entity.position)
            self.v_model_rot = Vec3(*self.player.ship_model_entity.rotation)
            self.v_model_scale = Vec3(*self.player.ship_model_entity.scale)
            if self.player.thrusters:
                self.v_thruster = Vec3(*self.player.thrusters[0].position)
                self.v_thruster_scale = Vec3(*self.player.thrusters[0].scale)
            self.v_laser = Vec3(*self.player.left_laser_offset)
        self.update_display()

    def update_display(self):
        modes = {
            1: ("Model Offset", self.v_model_offset),
            2: ("Model Rotation", self.v_model_rot),
            3: ("Model Scale", self.v_model_scale),
            4: ("Laser Offset", self.v_laser),
            5: ("Thruster Pos", self.v_thruster),
            6: ("Thruster Scale", self.v_thruster_scale)
        }
        name, val = modes.get(self.current_mode, ("Unknown", Vec3(0,0,0)))
        self.mode_text.text = f"MODE: {self.current_mode} - {name}"
        self.val_text.text = f"VAL: ({val.x:.2f}, {val.y:.2f}, {val.z:.2f})"

    def update_ship(self):
        if not self.player: return
        self.player.ship_model_entity.position = self.v_model_offset
        self.player.ship_model_entity.rotation = self.v_model_rot
        self.player.ship_model_entity.scale = self.v_model_scale
        
        if len(self.player.thrusters) >= 2:
            self.player.thrusters[0].position = (self.v_thruster.x, self.v_thruster.y, self.v_thruster.z)
            self.player.thrusters[1].position = (-self.v_thruster.x, self.v_thruster.y, self.v_thruster.z)
            self.player.thrusters[0].scale = (self.v_thruster_scale.x, self.v_thruster_scale.y, self.v_thruster_scale.z)
            self.player.thrusters[1].scale = (self.v_thruster_scale.x, self.v_thruster_scale.y, self.v_thruster_scale.z)
            
        self.player.left_laser_offset = (self.v_laser.x, self.v_laser.y, self.v_laser.z)
        self.player.right_laser_offset = (-self.v_laser.x, self.v_laser.y, self.v_laser.z)

    def input(self, key):
        if not self.enabled: return
        
        if key in '123456':
            self.current_mode = int(key)
            # Adjust step sizes based on mode
            if self.current_mode == 2: self.step_size = 5.0 # Rotation needs larger steps
            elif self.current_mode in (3, 6): self.step_size = 0.01 # Scale needs smaller steps
            else: self.step_size = 0.05
            self.update_display()
            
        dx, dy, dz = 0, 0, 0
        if key == 'right arrow': dx += self.step_size
        if key == 'left arrow': dx -= self.step_size
        if key == 'up arrow': dy += self.step_size
        if key == 'down arrow': dy -= self.step_size
        if key == 'w': dz += self.step_size
        if key == 's': dz -= self.step_size
        
        if dx != 0 or dy != 0 or dz != 0:
            change = Vec3(dx, dy, dz)
            if self.current_mode == 1: self.v_model_offset += change
            elif self.current_mode == 2: self.v_model_rot += change
            elif self.current_mode == 3: self.v_model_scale += change
            elif self.current_mode == 4: self.v_laser += change
            elif self.current_mode == 5: self.v_thruster += change
            elif self.current_mode == 6: self.v_thruster_scale += change
            
            self.update_ship()
            self.update_display()
            
        if key == 'enter':
            self.print_config()
            
    def print_config(self):
        print("====== SHIP TUNER CONFIG ======")
        print(f"scale=({self.v_model_scale.x:.2f}, {self.v_model_scale.y:.2f}, {self.v_model_scale.z:.2f}),")
        print(f"model_rotation_offset=({self.v_model_rot.x:.2f}, {self.v_model_rot.y:.2f}, {self.v_model_rot.z:.2f}),")
        print(f"thruster_offsets=[({self.v_thruster.x:.2f}, {self.v_thruster.y:.2f}, {self.v_thruster.z:.2f}), "
              f"({-self.v_thruster.x:.2f}, {self.v_thruster.y:.2f}, {self.v_thruster.z:.2f})],")
        print(f"thruster_scale=({self.v_thruster_scale.x:.2f}, {self.v_thruster_scale.y:.2f}, {self.v_thruster_scale.z:.2f}),")
        print(f"laser_offsets=(({self.v_laser.x:.2f}, {self.v_laser.y:.2f}, {self.v_laser.z:.2f}), "
              f"({-self.v_laser.x:.2f}, {self.v_laser.y:.2f}, {self.v_laser.z:.2f}))")
        print("===============================")
        t = Text(parent=camera.ui, text="Printed to console!", position=(0.18, 0.0), color=color.green, scale=1.5)
        destroy(t, delay=2)
