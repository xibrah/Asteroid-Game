import pygame
from pygame.locals import *
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import os

class OpenGL3DEngine:
    def __init__(self, screen_width, screen_height):
        """Initialize the 3D engine"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fov = 60.0  # Field of view in degrees
        
        # Camera position and orientation
        self.camera_pos = [0.0, 0.0, 0.0]
        self.camera_angle = 0.0  # Angle in degrees
        self.camera_height = 1.0  # Height of camera from ground
        
        # Movement speeds
        self.move_speed = 0.2
        self.turn_speed = 2.0  # Degrees per frame
        
        # Wall and floor textures
        self.textures = {}
        self.sprite_textures = {}
        
        # Level data
        self.level_map = []
        self.wall_height = 2.0
        
        # Sprites (for NPCs, items, etc.)
        self.sprites = []
        
        # Initialize OpenGL when needed
        self.initialized = False
        
        # 2D surface for HUD elements
        self.hud_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Fog settings
        self.fog_color = (0.1, 0.1, 0.15, 1.0)
        self.fog_start = 8.0
        self.fog_end = 20.0
        
        # Lighting settings
        self.light_ambient = (0.3, 0.3, 0.3, 1.0)
        self.light_diffuse = (0.7, 0.7, 0.7, 1.0)
        self.light_position = (0.0, 5.0, 0.0, 1.0)
        
    def initialize(self):
        """Set up OpenGL context and settings"""
        if self.initialized:
            return
            
        # Set up perspective
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.screen_width / self.screen_height, 0.1, 100.0)
        
        # Set up model view
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Enable textures
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable depth testing for proper occlusion
        glEnable(GL_DEPTH_TEST)
        
        # Enable lighting (optional, can be toggled)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, self.light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.light_diffuse)
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        
        # Enable fog for depth cues
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        glFogf(GL_FOG_START, self.fog_start)
        glFogf(GL_FOG_END, self.fog_end)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        
        self.initialized = True
        
    def load_textures(self, texture_dict):
        """
        Load wall textures
        texture_dict: Dictionary of texture_id -> file_path
        """
        for tex_id, tex_path in texture_dict.items():
            if os.path.exists(tex_path):
                # Load texture with pygame
                tex_surface = pygame.image.load(tex_path)
                tex_surface = pygame.transform.scale(tex_surface, (256, 256))
                tex_data = pygame.image.tostring(tex_surface, "RGBA", 1)
                
                # Create OpenGL texture
                texture = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture)
                
                # Set texture parameters
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                
                # Upload texture data
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tex_surface.get_width(), tex_surface.get_height(), 
                           0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
                
                self.textures[tex_id] = texture
            else:
                print(f"Warning: Texture file not found: {tex_path}")
                
    def load_sprite_textures(self, sprite_dict):
        """
        Load sprite textures
        sprite_dict: Dictionary of sprite_id -> file_path
        """
        for sprite_id, sprite_path in sprite_dict.items():
            if os.path.exists(sprite_path):
                # Load texture with pygame
                tex_surface = pygame.image.load(sprite_path)
                tex_data = pygame.image.tostring(tex_surface, "RGBA", 1)
                
                # Create OpenGL texture
                texture = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture)
                
                # Set texture parameters
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                
                # Upload texture data
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tex_surface.get_width(), tex_surface.get_height(), 
                           0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
                
                self.sprite_textures[sprite_id] = {
                    'texture': texture,
                    'width': tex_surface.get_width(),
                    'height': tex_surface.get_height()
                }
            else:
                print(f"Warning: Sprite texture file not found: {sprite_path}")
    
    def load_level(self, level_map):
        """
        Load a level map
        level_map: 2D array of tile types
        """
        self.level_map = level_map
        
        # Create test level if none provided
        if not level_map:
            self.create_test_level()
            
    def create_test_level(self):
        """Create a simple test level if no level is loaded"""
        self.level_map = [
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
            ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W']
        ]
        
        # Create some sprites for testing
        self.sprites = [
            {'type': 'npc', 'texture': 'npc1', 'position': [2.5, 0.0, 2.5], 'scale': 1.0},
            {'type': 'item', 'texture': 'item1', 'position': [5.5, 0.0, 3.5], 'scale': 0.5}
        ]
        
    def update_camera(self, position, angle):
        """Update camera position and angle"""
        self.camera_pos = position
        self.camera_angle = angle
        
    def add_sprite(self, sprite_type, texture_id, position, scale=1.0):
        """Add a 2D billboard sprite to the 3D world"""
        self.sprites.append({
            'type': sprite_type,
            'texture': texture_id,
            'position': position,
            'scale': scale
        })
    
    def move_sprite(self, index, new_position):
        """Move a sprite to a new position"""
        if 0 <= index < len(self.sprites):
            self.sprites[index]['position'] = new_position
    
    def remove_sprite(self, index):
        """Remove a sprite from the world"""
        if 0 <= index < len(self.sprites):
            self.sprites.pop(index)
            
    def update(self, forward, backward, strafe_left, strafe_right, turn_left, turn_right):
        """Update engine state based on movement controls"""
        # Update camera angle
        if turn_left:
            self.camera_angle -= self.turn_speed
        if turn_right:
            self.camera_angle += self.turn_speed
            
        # Normalize angle to 0-360
        self.camera_angle %= 360
        
        # Get movement direction
        angle_rad = math.radians(self.camera_angle)
        dx, dz = 0, 0
        
        # Calculate forward/backward movement
        if forward:
            dx += math.sin(angle_rad) * self.move_speed
            dz += math.cos(angle_rad) * self.move_speed
        if backward:
            dx -= math.sin(angle_rad) * self.move_speed
            dz -= math.cos(angle_rad) * self.move_speed
            
        # Calculate strafing
        if strafe_left:
            dx -= math.cos(angle_rad) * self.move_speed
            dz += math.sin(angle_rad) * self.move_speed
        if strafe_right:
            dx += math.cos(angle_rad) * self.move_speed
            dz -= math.sin(angle_rad) * self.move_speed
            
        # Collision detection with walls
        new_x = self.camera_pos[0] + dx
        new_z = self.camera_pos[2] + dz
        
        # Check if new position would be inside a wall
        if self._check_collision(new_x, self.camera_pos[2]):
            new_x = self.camera_pos[0]  # Prevent X movement
            
        if self._check_collision(self.camera_pos[0], new_z):
            new_z = self.camera_pos[2]  # Prevent Z movement
            
        # Update camera position
        self.camera_pos[0] = new_x
        self.camera_pos[2] = new_z
    
    def _check_collision(self, x, z):
        """Check if position (x, z) collides with a wall"""
        # Convert world coordinates to map coordinates
        map_x = int(x)
        map_z = int(z)
        
        # Check boundary
        if map_x < 0 or map_z < 0 or map_x >= len(self.level_map[0]) or map_z >= len(self.level_map):
            return True  # Out of bounds is a collision
            
        # Check if this cell is a wall
        cell = self.level_map[map_z][map_x]
        return cell == 'W'  # 'W' represents a wall
    
    def render(self, hud_draw_callback=None):
        """Render the 3D scene"""
        if not self.initialized:
            self.initialize()
            
        # Clear the screen
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Apply camera rotation and position
        angle_rad = math.radians(self.camera_angle)
        # Look in the direction of camera angle
        gluLookAt(
            self.camera_pos[0], self.camera_height, self.camera_pos[2],  # Eye position
            self.camera_pos[0] + math.sin(angle_rad), self.camera_height, self.camera_pos[2] + math.cos(angle_rad),  # Look at point
            0, 1, 0  # Up vector
        )
        
        # Render walls and floor
        self._render_level()
        
        # Render sprites
        self._render_sprites()
        
        # Render 2D HUD elements if callback provided
        if hud_draw_callback:
            self._render_hud(hud_draw_callback)
    
    def _render_level(self):
        """Render the walls and floor of the level"""
        # Enable lighting for the level
        glEnable(GL_LIGHTING)
        
        # Define colors for walls without textures
        wall_colors = {
            'W': (0.7, 0.7, 0.7),  # Gray for walls
            'D': (0.8, 0.5, 0.2),  # Brown for doors
            'F': (0.3, 0.3, 0.3)   # Dark gray for floor
        }
        
        # Iterate through the level map
        for z, row in enumerate(self.level_map):
            for x, cell in enumerate(row):
                if cell == 'W':  # Wall
                    self._render_wall(x, z, cell)
                elif cell == 'D':  # Door
                    self._render_wall(x, z, cell)
                # Floor is rendered separately below
                
        # Render floor
        glBegin(GL_QUADS)
        glColor3f(0.3, 0.3, 0.3)  # Dark gray for floor
        
        # Floor texture coordinates
        tex_scale = 1.0
        
        # Render floor as a large quad
        map_width = len(self.level_map[0])
        map_height = len(self.level_map)
        
        glNormal3f(0, 1, 0)  # Floor normal points up
        
        glVertex3f(0, 0, 0)
        glTexCoord2f(0, 0)
        
        glVertex3f(map_width, 0, 0)
        glTexCoord2f(map_width * tex_scale, 0)
        
        glVertex3f(map_width, 0, map_height)
        glTexCoord2f(map_width * tex_scale, map_height * tex_scale)
        
        glVertex3f(0, 0, map_height)
        glTexCoord2f(0, map_height * tex_scale)
        
        glEnd()
    
    def _render_wall(self, x, z, cell_type):
        """Render a single wall cell"""
        # Wall texture
        wall_tex = self.textures.get(cell_type)
    
        # Enable texturing if we have a texture for this wall type
        if wall_tex:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, wall_tex)
        else:
            glDisable(GL_TEXTURE_2D)
            # Set wall color based on type
            color = (0.7, 0.7, 0.7)  # Default gray
            if cell_type in ['W', 'D', 'F']:
                color = {
                    'W': (0.7, 0.7, 0.7),  # Gray for walls
                    'D': (0.8, 0.5, 0.2),  # Brown for doors
                    'F': (0.3, 0.3, 0.3)   # Dark gray for floor
                }[cell_type]
            glColor3f(*color)
    
        # For each side of the cell, check if we need to render a wall
        # We only render walls if the adjacent cell is not a wall
    
        # Check north side (negative Z)
        if z == 0 or (z > 0 and x < len(self.level_map[z-1]) and self.level_map[z-1][x] != cell_type):
            glBegin(GL_QUADS)
            # Top-left, bottom-left, bottom-right, top-right
            glNormal3f(0, 0, -1)  # Normal pointing south
        
            glTexCoord2f(0, 0)
            glVertex3f(x, self.wall_height, z)
        
            glTexCoord2f(0, 1)
            glVertex3f(x, 0, z)
        
            glTexCoord2f(1, 1)
            glVertex3f(x+1, 0, z)
        
            glTexCoord2f(1, 0)
            glVertex3f(x+1, self.wall_height, z)
            glEnd()
    
        # Check south side (positive Z)
        if z == len(self.level_map)-1 or (z+1 < len(self.level_map) and x < len(self.level_map[z+1]) and self.level_map[z+1][x] != cell_type):
            glBegin(GL_QUADS)
            glNormal3f(0, 0, 1)  # Normal pointing north
        
            glTexCoord2f(0, 0)
            glVertex3f(x+1, self.wall_height, z+1)
        
            glTexCoord2f(0, 1)
            glVertex3f(x+1, 0, z+1)
        
            glTexCoord2f(1, 1)
            glVertex3f(x, 0, z+1)
        
            glTexCoord2f(1, 0)
            glVertex3f(x, self.wall_height, z+1)
            glEnd()
    
        # Check west side (negative X)
        if x == 0 or (x > 0 and self.level_map[z][x-1] != cell_type):
            glBegin(GL_QUADS)
            glNormal3f(-1, 0, 0)  # Normal pointing east
        
            glTexCoord2f(0, 0)
            glVertex3f(x, self.wall_height, z+1)
        
            glTexCoord2f(0, 1)
            glVertex3f(x, 0, z+1)
        
            glTexCoord2f(1, 1)
            glVertex3f(x, 0, z)
        
            glTexCoord2f(1, 0)
            glVertex3f(x, self.wall_height, z)
            glEnd()
    
        # Check east side (positive X)
        if x == len(self.level_map[z])-1 or (x+1 < len(self.level_map[z]) and self.level_map[z][x+1] != cell_type):
            glBegin(GL_QUADS)
            glNormal3f(1, 0, 0)  # Normal pointing west
        
            glTexCoord2f(0, 0)
            glVertex3f(x+1, self.wall_height, z)
        
            glTexCoord2f(0, 1)
            glVertex3f(x+1, 0, z)
        
            glTexCoord2f(1, 1)
            glVertex3f(x+1, 0, z+1)
        
            glTexCoord2f(1, 0)
            glVertex3f(x+1, self.wall_height, z+1)
            glEnd()
    
    def _render_sprites(self):
        """Render billboard sprites in the 3D world"""
        # Disable lighting for sprites
        glDisable(GL_LIGHTING)
        
        # Enable alpha blending for transparent sprites
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable texturing
        glEnable(GL_TEXTURE_2D)
        
        # Sort sprites by distance from camera (back to front)
        sorted_sprites = sorted(self.sprites, key=lambda s: 
                               self._distance_to_camera(s['position']), reverse=True)
        
        # Render each sprite as a billboard
        for sprite in sorted_sprites:
            texture_info = self.sprite_textures.get(sprite['texture'])
            if not texture_info:
                continue
                
            # Get sprite position and scale
            pos = sprite['position']
            scale = sprite['scale']
            
            # Don't render sprites that are behind the camera
            camera_to_sprite = [
                pos[0] - self.camera_pos[0],
                pos[2] - self.camera_pos[2]
            ]
            camera_dir = [
                math.sin(math.radians(self.camera_angle)),
                math.cos(math.radians(self.camera_angle))
            ]
            
            # Skip if sprite is behind camera (dot product is negative)
            if (camera_to_sprite[0] * camera_dir[0] + camera_to_sprite[1] * camera_dir[1]) < 0:
                continue
            
            # Calculate width and height of sprite in world units
            aspect_ratio = texture_info['width'] / texture_info['height']
            sprite_height = 1.0 * scale
            sprite_width = sprite_height * aspect_ratio
            
            # Bind texture
            glBindTexture(GL_TEXTURE_2D, texture_info['texture'])
            
            # Save the current matrix
            glPushMatrix()
            
            # Move to sprite position
            glTranslatef(pos[0], pos[1] + sprite_height/2, pos[2])
            
            # Billboard the sprite to face the camera
            # This rotates the sprite around the Y axis to face the camera
            billboard_angle = self.camera_angle - 180
            glRotatef(billboard_angle, 0, 1, 0)
            
            # Draw the sprite as a quad
            glBegin(GL_QUADS)
            glColor3f(1.0, 1.0, 1.0)  # Full brightness
            
            # Calculate vertices for the quad
            width_half = sprite_width / 2
            height_half = sprite_height / 2
            
            # Bottom-left
            glTexCoord2f(0, 1)
            glVertex3f(-width_half, -height_half, 0)
            
            # Bottom-right
            glTexCoord2f(1, 1)
            glVertex3f(width_half, -height_half, 0)
            
            # Top-right
            glTexCoord2f(1, 0)
            glVertex3f(width_half, height_half, 0)
            
            # Top-left
            glTexCoord2f(0, 0)
            glVertex3f(-width_half, height_half, 0)
            
            glEnd()
            
            # Restore the matrix
            glPopMatrix()
        
        # Restore states
        glEnable(GL_LIGHTING)
    
    def _distance_to_camera(self, position):
        """Calculate distance from camera to a position"""
        return math.sqrt((position[0] - self.camera_pos[0])**2 + 
                        (position[2] - self.camera_pos[2])**2)
    
    def _render_hud(self, hud_draw_callback):
        """Render 2D HUD elements using a callback function"""
        # Switch to orthographic projection for 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.screen_width, self.screen_height, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Disable depth testing for HUD
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Clear the HUD surface
        self.hud_surface.fill((0, 0, 0, 0))
        
        # Call the callback to draw on the HUD surface
        hud_draw_callback(self.hud_surface)
        
        # Convert pygame surface to OpenGL texture
        hud_data = pygame.image.tostring(self.hud_surface, "RGBA", 1)
        
        # Create texture for HUD
        hud_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.screen_width, self.screen_height, 
                   0, GL_RGBA, GL_UNSIGNED_BYTE, hud_data)
        
        # Draw textured quad for HUD
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        
        glBegin(GL_QUADS)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        
        glTexCoord2f(1, 0)
        glVertex2f(self.screen_width, 0)
        
        glTexCoord2f(1, 1)
        glVertex2f(self.screen_width, self.screen_height)
        
        glTexCoord2f(0, 1)
        glVertex2f(0, self.screen_height)
        
        glEnd()
        
        # Delete temporary texture
        glDeleteTextures(1, [hud_tex])
        
        # Restore states
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        # Delete textures
        if self.textures:
            glDeleteTextures(len(self.textures), list(self.textures.values()))
        if self.sprite_textures:
            glDeleteTextures(len(self.sprite_textures), 
                           [info['texture'] for info in self.sprite_textures.values()])
