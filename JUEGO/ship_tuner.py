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
            "[5] Thruster Pos  [6] Thruster Scale\n"
            "[7] Camera Pos\n\n"
            "CONTROLS: Arrows (X/Y) | Q/E (Z)\n"
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
            self.v_laser = Vec3(abs(self.player.left_laser_offset[0]), self.player.left_laser_offset[1], self.player.left_laser_offset[2])
        self.update_display()

    def update_display(self):
        modes = {
            1: ("Model Offset", self.v_model_offset),
            2: ("Model Rotation", self.v_model_rot),
            3: ("Model Scale", self.v_model_scale),
            4: ("Laser Offset", self.v_laser),
            5: ("Thruster Pos", self.v_thruster),
            6: ("Thruster Scale", self.v_thruster_scale),
            7: ("Camera Pos", Vec3(0,0,0)) # Dummy vector for display
        }
        name, val = modes.get(self.current_mode, ("Unknown", Vec3(0,0,0)))
        self.mode_text.text = f"MODE: {self.current_mode} - {name}"
        self.val_text.text = f"VAL: ({val.x:.2f}, {val.y:.2f}, {val.z:.2f})"

    def update_ship(self):
        if not self.player: return
        self.player.ship_model_entity.position = self.v_model_offset
        self.player.ship_model_entity.rotation = self.v_model_rot
        self.player.ship_model_entity.scale = self.v_model_scale
        
        if self.player.thrusters:
            self.player.base_thruster_scale = (self.v_thruster_scale.x, self.v_thruster_scale.y, self.v_thruster_scale.z)
            for i, thruster in enumerate(self.player.thrusters):
                x_mult = -1 if i % 2 != 0 else 1
                thruster.position = (abs(self.v_thruster.x) * x_mult, self.v_thruster.y, self.v_thruster.z)
                thruster.scale = (self.v_thruster_scale.x, self.v_thruster_scale.y, self.v_thruster_scale.z)
            
            
        self.player.left_laser_offset = (-self.v_laser.x, self.v_laser.y, self.v_laser.z)
        self.player.right_laser_offset = (self.v_laser.x, self.v_laser.y, self.v_laser.z)

    def input(self, key):
        if not self.enabled: return
        
        if key in '1234567':
            self.current_mode = int(key)
            # Adjust step sizes based on mode
            if self.current_mode == 2: self.step_size = 5.0 # Rotation needs larger steps
            elif self.current_mode in (3, 6): self.step_size = 0.01 # Scale needs smaller steps
            elif self.current_mode == 7: self.step_size = 2.0 # Camera needs large steps
            else: self.step_size = 0.05
            self.update_display()
            
        dx, dy, dz = 0, 0, 0
        if key == 'right arrow': dx += self.step_size
        if key == 'left arrow': dx -= self.step_size
        if key == 'up arrow': dy += self.step_size
        if key == 'down arrow': dy -= self.step_size
        if key == 'q': dz += self.step_size
        if key == 'e': dz -= self.step_size
        
        if dx != 0 or dy != 0 or dz != 0:
            change = Vec3(dx, dy, dz)
            if self.current_mode == 1: self.v_model_offset += change
            elif self.current_mode == 2: self.v_model_rot += change
            elif self.current_mode == 3: self.v_model_scale += change
            elif self.current_mode == 4: self.v_laser += change
            elif self.current_mode == 5: self.v_thruster += change
            elif self.current_mode == 6: self.v_thruster_scale += change
            elif self.current_mode == 7:
                cam_idx = self.player.current_cam_index
                old_cam = self.player.camera_modes[cam_idx]
                self.player.camera_modes[cam_idx] = (old_cam[0] + dx, old_cam[1] + dy, old_cam[2] + dz)
            
            self.update_ship()
            self.update_display()
            
        if key == 'enter':
            self.print_config()
            
    def print_config(self):
        print("====== SHIP TUNER CONFIG ======")
        print(f"scale=({self.v_model_scale.x:.2f}, {self.v_model_scale.y:.2f}, {self.v_model_scale.z:.2f}),")
        print(f"model_rotation_offset=({self.v_model_rot.x:.2f}, {self.v_model_rot.y:.2f}, {self.v_model_rot.z:.2f}),")
        
        # Calculate unscaled local offsets for printing
        scale_x = self.v_model_scale.x if self.v_model_scale.x != 0 else 1
        scale_y = self.v_model_scale.y if self.v_model_scale.y != 0 else 1
        scale_z = self.v_model_scale.z if self.v_model_scale.z != 0 else 1
        
        local_x = abs(self.v_thruster.x) / scale_x
        local_y = self.v_thruster.y / scale_y
        local_z = self.v_thruster.z / scale_z
        
        if self.player and len(self.player.thrusters) == 1:
            print(f"thruster_offsets=[({local_x:.4f}, {local_y:.4f}, {local_z:.4f})],")
        else:
            print(f"thruster_offsets=[({-local_x:.4f}, {local_y:.4f}, {local_z:.4f}), "
                  f"({local_x:.4f}, {local_y:.4f}, {local_z:.4f})],")
            
        print(f"thruster_scale=({self.v_thruster_scale.x:.2f}, {self.v_thruster_scale.y:.2f}, {self.v_thruster_scale.z:.2f}),")
        print(f"laser_offsets=(({-self.v_laser.x:.2f}, {self.v_laser.y:.2f}, {self.v_laser.z:.2f}), "
              f"({self.v_laser.x:.2f}, {self.v_laser.y:.2f}, {self.v_laser.z:.2f}))")
        print("===============================")
        t = Text(parent=camera.ui, text="Printed to console!", position=(0.18, 0.0), color=color.green, scale=1.5)
        destroy(t, delay=2)
