import pygame
from pygame.locals import *
import math
import os
from opengl_engine import OpenGL3DEngine

def initialize_3d(self):
    """Initialize the 3D engine and textures for the game"""
    # Create the 3D engine
    self.engine_3d = OpenGL3DEngine(self.screen_width, self.screen_height)
    
    # Set up texture dictionaries
    wall_textures = {
        'W': 'assets/textures/wall.png',
        'D': 'assets/textures/door.png',
        'F': 'assets/textures/floor.png',
        'T': 'assets/textures/table.png',
        'C': 'assets/textures/chair.png',
        'B': 'assets/textures/bar.png',
        'S': 'assets/textures/storage.png',
        'M': 'assets/textures/machine.png',
        'G': 'assets/textures/glass.png',
        'V': 'assets/textures/viewport.png',
        'H': 'assets/textures/hangar.png',
        'P': 'assets/textures/prison.png',
        'X': 'assets/textures/exhibit.png',
        'R': 'assets/textures/robot.png',
        'E': 'assets/textures/exit.png'
    }
    
    # Create placeholder textures if they don't exist
    create_placeholder_textures(wall_textures)
    
    # Load textures
    self.engine_3d.load_textures(wall_textures)
    
    # Load sprite textures for NPCs and items
    sprite_textures = {}
    for npc in self.npcs:
        sprite_id = f"npc_{npc.name.lower().replace(' ', '_')}"
        sprite_path = f"assets/textures/sprites/{sprite_id}.png"
        
        # Create placeholder sprite if it doesn't exist
        if not os.path.exists(sprite_path):
            create_placeholder_sprite(sprite_path, npc.name)
            
        sprite_textures[sprite_id] = sprite_path
    
    # Load the sprite textures
    self.engine_3d.load_sprite_textures(sprite_textures)
    
    # Add 3D view controls to the game
    self.fp_forward = False
    self.fp_backward = False
    self.fp_strafe_left = False
    self.fp_strafe_right = False
    self.fp_turn_left = False
    self.fp_turn_right = False
    
    # Initialize 3D view angle
    self.fp_angle = 0.0
    
    return True

def create_placeholder_textures(texture_dict):
    """Create placeholder textures if the texture files don't exist"""
    # Create textures directory if it doesn't exist
    os.makedirs('assets/textures', exist_ok=True)
    
    # Default colors for different tile types
    default_colors = {
        'W': (100, 100, 100),     # Wall - Gray
        'D': (150, 75, 0),        # Door - Brown
        'F': (50, 50, 50),        # Floor - Dark gray
        'T': (120, 60, 20),       # Table - Dark brown
        'C': (160, 82, 45),       # Chair - Sienna
        'B': (139, 69, 19),       # Bar/Bed - Saddle brown
        'S': (160, 120, 90),      # Storage - Tan
        'M': (70, 70, 90),        # Machine - Blue-gray
        'G': (173, 216, 230),     # Glass - Light blue
        'V': (135, 206, 235),     # Viewport - Sky blue
        'H': (105, 105, 105),     # Hangar - Dim gray
        'P': (169, 169, 169),     # Prison - Dark gray
        'X': (192, 192, 192),     # Exhibit - Silver
        'R': (128, 128, 128),     # Robot - Gray
        'E': (0, 128, 0)          # Exit - Green
    }
    
    # Create each texture
    for tile_type, path in texture_dict.items():
        if not os.path.exists(path):
            # Get color for this tile type
            color = default_colors.get(tile_type, (100, 100, 100))
            
            # Create a surface with the color
            surface = pygame.Surface((256, 256))
            surface.fill(color)
            
            # Add some texture by drawing lines/patterns
            for i in range(0, 256, 32):
                # Darker color for lines
                line_color = (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30))
                pygame.draw.line(surface, line_color, (0, i), (256, i), 2)
                pygame.draw.line(surface, line_color, (i, 0), (i, 256), 2)
            
            # Add the tile type as text
            font = pygame.font.SysFont(None, 64)
            text = font.render(tile_type, True, (255, 255, 255))
            text_rect = text.get_rect(center=(128, 128))
            surface.blit(text, text_rect)
            
            # Save the texture
            os.makedirs(os.path.dirname(path), exist_ok=True)
            pygame.image.save(surface, path)
            print(f"Created placeholder texture: {path}")

def create_placeholder_sprite(path, name):
    """Create a placeholder sprite texture with the NPC/item name"""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Create a surface for the sprite
    surface = pygame.Surface((128, 256), pygame.SRCALPHA)
    
    # Draw a simple humanoid shape
    # Head
    pygame.draw.circle(surface, (200, 150, 150), (64, 40), 30)
    
    # Body
    pygame.draw.rect(surface, (100, 100, 150), (44, 70, 40, 100))
    
    # Arms
    pygame.draw.rect(surface, (100, 100, 150), (24, 80, 20, 60))
    pygame.draw.rect(surface, (100, 100, 150), (84, 80, 20, 60))
    
    # Legs
    pygame.draw.rect(surface, (100, 100, 150), (44, 170, 15, 80))
    pygame.draw.rect(surface, (100, 100, 150), (69, 170, 15, 80))
    
    # Add the name
    font = pygame.font.SysFont(None, 24)
    text = font.render(name, True, (255, 255, 255))
    text_rect = text.get_rect(center=(64, 15))
    surface.blit(text, text_rect)
    
    # Save the sprite
    pygame.image.save(surface, path)
    print(f"Created placeholder sprite: {path}")

def toggle_3d_view(self):
    """Toggle between 2D and 3D views"""
    # If we're not in 3D, switch to 3D
    if self.game_state != 12:
        print("Switching to 3D view")
        self.previous_state = self.game_state
        self.game_state = 12
        
        # Initialize the 3D engine if not already done
        if not hasattr(self, 'engine_3d'):
            initialize_3d(self)
        
        # Load the current level into the 3D engine
        load_level_to_3d(self)
        
        # Set initial camera position based on player
        if hasattr(self, 'player') and hasattr(self.player, 'rect'):
            # Convert player position to 3D coordinates
            player_x = self.player.rect.centerx / self.map_tile_size
            player_z = self.player.rect.centery / self.map_tile_size
            
            # Set initial camera position and angle
            self.engine_3d.camera_pos = [player_x, 1.0, player_z]
            
            # Set angle based on player direction
            if hasattr(self.player, 'last_direction'):
                self.fp_angle = {
                    'up': 0,
                    'right': 90,
                    'down': 180,
                    'left': 270
                }.get(self.player.last_direction, 0)
                
                self.engine_3d.camera_angle = self.fp_angle
        
        return True
    else:
        # Switch back to previous state
        print("Switching back to 2D view")
        self.game_state = self.previous_state if hasattr(self, 'previous_state') else GameState.OVERWORLD
        
        # Update player position based on 3D camera position
        if hasattr(self, 'engine_3d') and hasattr(self, 'player') and hasattr(self.player, 'rect'):
            # Convert 3D coordinates back to player position
            self.player.rect.centerx = int(self.engine_3d.camera_pos[0] * self.map_tile_size)
            self.player.rect.centery = int(self.engine_3d.camera_pos[2] * self.map_tile_size)
            
            # Set player direction based on camera angle
            angle = self.engine_3d.camera_angle % 360
            if 45 <= angle < 135:
                self.player.last_direction = 'right'
            elif 135 <= angle < 225:
                self.player.last_direction = 'down'
            elif 225 <= angle < 315:
                self.player.last_direction = 'left'
            else:
                self.player.last_direction = 'up'
        
        return True

def load_level_to_3d(self):
    """Load the current game level into the 3D engine"""
    if not hasattr(self, 'engine_3d') or not hasattr(self, 'current_level'):
        return False
    
    # Check if we have a layout for the current level
    if "layout" in self.current_level and self.current_level["layout"]:
        # Pass the level layout to the 3D engine
        self.engine_3d.load_level(self.current_level["layout"])
        
        # Store the tile size for position conversions
        self.map_tile_size = getattr(self, 'map_tile_size', 32)
        
        # Add NPCs as sprites
        add_npcs_to_3d(self)
        
        return True
    else:
        print("Error: No layout available for current level")
        return False

def add_npcs_to_3d(self):
    """Add game NPCs as sprites in the 3D engine"""
    if not hasattr(self, 'engine_3d') or not hasattr(self, 'npcs'):
        return
    
    # Clear existing sprites
    self.engine_3d.sprites = []
    
    # Add each NPC as a sprite
    for npc in self.npcs:
        if hasattr(npc, 'rect'):
            # Convert position to 3D coordinates
            x = npc.rect.centerx / self.map_tile_size
            z = npc.rect.centery / self.map_tile_size
            
            # Create sprite ID from NPC name
            sprite_id = f"npc_{npc.name.lower().replace(' ', '_')}"
            
            # Add the sprite
            self.engine_3d.add_sprite('npc', sprite_id, [x, 0.0, z], 1.0)
            print(f"Added NPC sprite: {npc.name} at ({x}, {z})")

def update_3d_view(self, dt):
    """Update the 3D view state"""
    if self.game_state != 12 or not hasattr(self, 'engine_3d'):
        return
    
    # Update the 3D engine
    self.engine_3d.update(
        self.fp_forward,
        self.fp_backward,
        self.fp_strafe_left,
        self.fp_strafe_right,
        self.fp_turn_left,
        self.fp_turn_right
    )
    
    # Update NPC sprites if they moved
    if hasattr(self, 'npcs'):
        for i, npc in enumerate(self.npcs):
            if hasattr(npc, 'rect') and i < len(self.engine_3d.sprites):
                # Convert position to 3D coordinates
                x = npc.rect.centerx / self.map_tile_size
                z = npc.rect.centery / self.map_tile_size
                
                # Update sprite position
                self.engine_3d.sprites[i]['position'] = [x, 0.0, z]

def draw_3d_view(self):
    """Draw the 3D view"""
    if self.game_state != 12 or not hasattr(self, 'engine_3d'):
        return
    
    # Render the 3D scene
    def draw_hud(surface):
        # Draw UI elements on the HUD surface
        if hasattr(self, 'draw_ui'):
            self.draw_ui(surface)
        
        # Draw dialogue box if active
        if hasattr(self, 'dialogue_manager') and self.dialogue_manager.is_dialogue_active():
            self.dialogue_manager.draw(surface)
        
        # Draw other UI elements as needed
        # Add any game-specific HUD elements here
    
    # Render the scene with HUD overlay
    self.engine_3d.render(draw_hud)