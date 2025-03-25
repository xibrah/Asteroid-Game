from direct.actor.Actor import Actor
from panda3d.core import *
import math

class Player:
    """Player character for Asteroid Frontier"""
    
    def __init__(self, base, render_node):
        """Initialize the player
        
        Args:
            base: The ShowBase instance
            render_node: The parent node to attach the player to
        """
        self.base = base
        self.render_node = render_node
        
        # Player attributes
        self.move_speed = 5.0
        self.sprint_multiplier = 1.6
        self.turn_speed = 120.0  # Degrees per second
        self.jump_height = 1.0
        self.gravity = 9.8
        self.velocity = Vec3(0, 0, 0)
        
        # Character stats
        self.health = 100
        self.max_health = 100
        self.credits = 100
        self.level = 1
        self.experience = 0
        self.experience_to_level = 100
        
        # Create the player model
        self.setup_model()
        
        # Set up collision detection
        self.setup_collision()
        
        # Movement flags
        self.is_jumping = False
        self.is_sprinting = False
        self.on_ground = True
        
        # Interaction data
        self.near_exit = False
        self.near_npc = None
        self.near_item = None
        
        # Camera offsets for different view modes
        self.camera_offsets = {
            "first_person": (0, 0, 1.7),
            "third_person": (0, -5, 2),
            "top_down": (0, 0, 15)
        }
        
        # Current view mode
        self.view_mode = "third_person"
        
        # Heading and pitch
        self.heading = 0
        self.pitch = 0
    
    def setup_model(self):
        """Create the player model"""
        # Try to load an animated actor model
        try:
            self.actor = Actor("models/player/player-model", {
                "walk": "models/player/player-walk",
                "idle": "models/player/player-idle",
                "run": "models/player/player-run",
                "jump": "models/player/player-jump"
            })
            self.actor.reparentTo(self.render_node)
            
            # Start with idle animation
            self.actor.loop("idle")
            self.current_anim = "idle"
            
            # Store actor as the main model
            self.model = self.actor
            
        except:
            # Fall back to simple box model if character model isn't available
            print("Failed to load player model, using box placeholder")
            self.actor = None
            self.model = self.base.loader.loadModel("models/box")
            self.model.setScale(0.5, 0.5, 1.0)  # Make it person-shaped
            self.model.setColor(0, 0.5, 1)  # Blue
            self.model.reparentTo(self.render_node)
        
        # Initial position
        self.model.setPos(0, 0, 0.5)
        
        # Attach a node for first-person camera
        self.fp_camera_node = self.model.attachNewNode("fp_camera")
        self.fp_camera_node.setPos(0, 0, 1.7)  # Slightly below player height
    
    def setup_collision(self):
        """Set up collision detection for the player"""
        # Create a collision capsule
        self.collision_shape = CollisionCapsule(0, 0, 0.2, 0, 0, 1.8, 0.4)
        self.collision_node = CollisionNode("player")
        self.collision_node.addSolid(self.collision_shape)
        
        # Add collision node to player
        self.collider = self.model.attachNewNode(self.collision_node)
        
        # Debugging: Show the collision shape
        # self.collider.show()
        
        # Create a ray for ground detection
        self.ground_ray = CollisionRay()
        self.ground_ray.setOrigin(0, 0, 0.5)
        self.ground_ray.setDirection(0, 0, -1)
        
        self.ground_col = CollisionNode("ground_ray")
        self.ground_col.addSolid(self.ground_ray)
        self.ground_col.setFromCollideMask(BitMask32.bit(1))
        self.ground_col.setIntoCollideMask(BitMask32.allOff())
        
        self.ground_collider = self.model.attachNewNode(self.ground_col)
        
        # Create collision handlers
        self.base.cTrav = CollisionTraverser()
        self.collision_handler = CollisionHandlerPusher()
        self.collision_handler.addCollider(self.collider, self.model)
        self.base.cTrav.addCollider(self.collider, self.collision_handler)
        
        self.ground_handler = CollisionHandlerQueue()
        self.base.cTrav.addCollider(self.ground_collider, self.ground_handler)
    
    def update(self, keys, dt):
        """Update player position and state
        
        Args:
            keys: Dictionary of key states
            dt: Delta time since last frame
        """
        # Check for ground collision
        self.check_ground()
        
        # Handle movement
        move_dir = Vec3(0, 0, 0)
        
        # Apply inputs to direction
        if keys["forward"]:
            move_dir.y += 1
        if keys["backward"]:
            move_dir.y -= 1
        if keys["left"]:
            move_dir.x -= 1
        if keys["right"]:
            move_dir.x += 1
        
        # Normalize if moving diagonally
        if move_dir.length() > 0:
            move_dir.normalize()
        
        # Set sprinting state
        self.is_sprinting = keys["sprint"]
        
        # Apply speed modifiers
        speed = self.move_speed
        if self.is_sprinting:
            speed *= self.sprint_multiplier
        
        # Convert direction to world space based on camera heading
        heading_rad = deg2Rad(self.heading)
        
        world_move_dir = Vec3(0, 0, 0)
        world_move_dir.x = (move_dir.x * math.cos(heading_rad) - 
                           move_dir.y * math.sin(heading_rad))
        world_move_dir.y = (move_dir.x * math.sin(heading_rad) + 
                           move_dir.y * math.cos(heading_rad))
        
        # Apply movement
        self.model.setX(self.model.getX() + world_move_dir.x * speed * dt)
        self.model.setY(self.model.getY() + world_move_dir.y * speed * dt)
        
        # Handle jumping
        if keys["jump"] and self.on_ground and not self.is_jumping:
            self.velocity.z = math.sqrt(2 * self.gravity * self.jump_height)
            self.is_jumping = True
            self.on_ground = False
            
            # Play jump animation
            if self.actor and "jump" in self.actor.getAnimNames():
                self.actor.play("jump")
                self.current_anim = "jump"
        
        # Apply gravity
        if not self.on_ground:
            self.velocity.z -= self.gravity * dt
            self.model.setZ(self.model.getZ() + self.velocity.z * dt)
        
        # Update model facing direction
        if move_dir.length() > 0:
            # Smoothly rotate to face movement direction
            target_h = math.degrees(math.atan2(-world_move_dir.x, -world_move_dir.y))
            current_h = self.model.getH()
            
            # Find the shortest rotation
            delta_h = target_h - current_h
            while delta_h > 180:
                delta_h -= 360
            while delta_h < -180:
                delta_h += 360
            
            # Interpolate rotation
            turn_amount = self.turn_speed * dt
            if abs(delta_h) < turn_amount:
                self.model.setH(target_h)
            else:
                if delta_h > 0:
                    self.model.setH(current_h + turn_amount)
                else:
                    self.model.setH(current_h - turn_amount)
            
            # Update animation based on speed
            if self.actor:
                if self.on_ground:
                    if self.is_sprinting and "run" in self.actor.getAnimNames():
                        if self.current_anim != "run":
                            self.actor.loop("run")
                            self.current_anim = "run"
                    else:
                        if self.current_anim != "walk":
                            self.actor.loop("walk")
                            self.current_anim = "walk"
        else:
            # Idle animation when not moving
            if self.actor and self.on_ground and self.current_anim != "idle":
                self.actor.loop("idle")
                self.current_anim = "idle"
    
    def check_ground(self):
        """Check if player is on the ground"""
        # Only check for ground if we're falling or not moving vertically
        if self.velocity.z <= 0:
            if self.ground_handler.getNumEntries() > 0:
                # Get the closest collision entry
                self.ground_handler.sortEntries()
                entry = self.ground_handler.getEntry(0)
                
                # Check if we're close to the ground
                if entry.getSurfacePoint(self.render_node).getZ() <= self.model.getZ() + 0.1:
                    self.on_ground = True
                    self.is_jumping = False
                    self.velocity.z = 0
                    
                    # Snap to ground
                    self.model.setZ(entry.getSurfacePoint(self.render_node).getZ())
                else:
                    self.on_ground = False
            else:
                self.on_ground = False
    
    def set_camera_mode(self, mode):
        """Change the camera view mode
        
        Args:
            mode: View mode ("first_person", "third_person", "top_down")
        """
        if mode in self.camera_offsets:
            self.view_mode = mode
    
    def update_camera(self, camera, dt):
        """Update camera position based on view mode
        
        Args:
            camera: The camera node to update
            dt: Delta time since last frame
        """
        if self.view_mode == "first_person":
            # Position camera at player's eyes
            camera.setPos(self.fp_camera_node.getPos(self.render_node))
            camera.setHpr(self.heading, self.pitch, 0)
            
        elif self.view_mode == "third_person":
            # Position camera behind and above player
            target_pos = self.model.getPos()
            
            # Calculate camera position
            heading_rad = deg2Rad(self.heading)
            offset_x = -math.sin(heading_rad) * self.camera_offsets["third_person"][1]
            offset_y = -math.cos(heading_rad) * self.camera_offsets["third_person"][1]
            offset_z = self.camera_offsets["third_person"][2]
            
            camera_pos = Vec3(
                target_pos.x + offset_x,
                target_pos.y + offset_y,
                target_pos.z + offset_z
            )
            
            # Set camera position and look at player
            camera.setPos(camera_pos)
            camera.lookAt(target_pos + Vec3(0, 0, 1.0))
            
        elif self.view_mode == "top_down":
            # Position camera directly above player
            target_pos = self.model.getPos()
            offset_z = self.camera_offsets["top_down"][2]
            
            camera.setPos(target_pos.x, target_pos.y, target_pos.z + offset_z)
            camera.lookAt(target_pos)
    
    def set_position(self, pos):
        """Set player position
        
        Args:
            pos: New position (Vec3 or tuple)
        """
        if isinstance(pos, tuple):
            self.model.setPos(*pos)
        else:
            self.model.setPos(pos)
    
    def get_position(self):
        """Get player position
        
        Returns:
            Vec3: Current position
        """
        return self.model.getPos()
    
    def set_heading(self, heading):
        """Set player heading (yaw)
        
        Args:
            heading: Heading angle in degrees
        """
        self.heading = heading
        # Only update model heading in third-person mode
        if self.view_mode != "first_person":
            self.model.setH(heading)
    
    def set_pitch(self, pitch):
        """Set camera pitch
        
        Args:
            pitch: Pitch angle in degrees (clamped between -90 and 90)
        """
        self.pitch = max(-90, min(90, pitch))
    
    def interact(self):
        """Interact with the environment or NPCs"""
        # Implement interaction logic here
        if self.near_npc:
            return {"type": "npc", "target": self.near_npc}
        
        if self.near_item:
            return {"type": "item", "target": self.near_item}
            
        if self.near_exit:
            return {"type": "exit", "target": None}
            
        return None
    
    def gain_experience(self, amount):
        """Add experience and potentially level up
        
        Args:
            amount: Amount of experience to add
        """
        self.experience += amount
        
        # Check for level up
        if self.experience >= self.experience_to_level:
            self.level_up()
    
    def level_up(self):
        """Level up the character"""
        self.level += 1
        self.experience -= self.experience_to_level
        
        # Increase next level threshold
        self.experience_to_level = self.level * 100
        
        # Increase stats
        self.max_health += 10
        self.health = self.max_health  # Full heal on level