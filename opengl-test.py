import pygame
from pygame.locals import *
import os
import sys
import math
from OpenGL.GL import *
from OpenGL.GLU import *

# Import the 3D engine
from opengl_engine import OpenGL3DEngine

# Test map layout
test_map = [
    ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'],
    ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'W', 'W', 'D', 'D', 'W', 'W', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'W', 'F', 'F', 'F', 'F', 'W', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'D', 'F', 'F', 'F', 'F', 'D', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'D', 'F', 'F', 'F', 'F', 'D', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'W', 'F', 'F', 'F', 'F', 'W', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'W', 'W', 'D', 'D', 'W', 'W', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
    ['W', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'F', 'W'],
    ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W']
]

def create_placeholder_textures():
    """Create placeholder textures for testing"""
    os.makedirs('assets/textures', exist_ok=True)
    os.makedirs('assets/textures/sprites', exist_ok=True)
    
    # Default colors for different tile types
    default_colors = {
        'W': (100, 100, 100),     # Wall - Gray
        'D': (150, 75, 0),        # Door - Brown
        'F': (50, 50, 50),        # Floor - Dark gray
    }
    
    texture_paths = {}
    
    # Create textures for each tile type
    for tile_type, color in default_colors.items():
        path = f'assets/textures/{tile_type.lower()}.png'
        texture_paths[tile_type] = path
        
        if not os.path.exists(path):
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
            pygame.image.save(surface, path)
            print(f"Created placeholder texture: {path}")
    
    # Create a test sprite
    sprite_path = 'assets/textures/sprites/test_npc.png'
    if not os.path.exists(sprite_path):
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
        
        # Add a label
        font = pygame.font.SysFont(None, 24)
        text = font.render("Test NPC", True, (255, 255, 255))
        text_rect = text.get_rect(center=(64, 15))
        surface.blit(text, text_rect)
        
        # Save the sprite
        pygame.image.save(surface, sprite_path)
        print(f"Created test sprite: {sprite_path}")
    
    texture_paths['test_npc'] = sprite_path
    
    return texture_paths

def main():
    """Run a simple test of the 3D engine"""
    pygame.init()
    
    # Set up display for OpenGL
    screen_width, screen_height = 1024, 768
    screen = pygame.display.set_mode((screen_width, screen_height), DOUBLEBUF|OPENGL)
    pygame.display.set_caption("OpenGL 3D Engine Test")
    
    # Create the 3D engine
    engine = OpenGL3DEngine(screen_width, screen_height)
    
    # Create and load textures
    textures = create_placeholder_textures()
    wall_textures = {
        'W': textures['W'],
        'D': textures['D'],
        'F': textures['F']
    }
    engine.load_textures(wall_textures)
    
    # Load sprite textures
    sprite_textures = {
        'test_npc': textures['test_npc']
    }
    engine.load_sprite_textures(sprite_textures)
    
    # Load test map
    engine.load_level(test_map)
    
    # Add test sprites
    engine.add_sprite('npc', 'test_npc', [3.0, 0.0, 3.0], 1.0)
    engine.add_sprite('npc', 'test_npc', [8.0, 0.0, 8.0], 1.0)
    
    # Set initial camera position (middle of the map)
    engine.camera_pos = [5.0, 1.0, 5.0]
    engine.camera_angle = 0.0
    
    # Movement state
    forward = False
    backward = False
    strafe_left = False
    strafe_right = False
    turn_left = False
    turn_right = False
    
    # Simple HUD for testing
    def draw_hud(surface):
        # Draw position and controls
        font = pygame.font.SysFont(None, 24)
        pos_text = font.render(f"Position: ({engine.camera_pos[0]:.1f}, {engine.camera_pos[2]:.1f})", True, (255, 255, 255))
        angle_text = font.render(f"Angle: {engine.camera_angle:.1f}°", True, (255, 255, 255))
        controls_text = font.render("WASD: Move | Arrows: Turn | ESC: Exit", True, (255, 255, 255))
        
        surface.blit(pos_text, (10, 10))
        surface.blit(angle_text, (10, 40))
        surface.blit(controls_text, (screen_width - controls_text.get_width() - 10, 10))
    
    # Game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Calculate delta time
        dt = clock.tick(60) / 1000.0
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    forward = True
                elif event.key == pygame.K_s:
                    backward = True
                elif event.key == pygame.K_a:
                    strafe_left = True
                elif event.key == pygame.K_d:
                    strafe_right = True
                elif event.key == pygame.K_LEFT:
                    turn_left = True
                elif event.key == pygame.K_RIGHT:
                    turn_right = True
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    forward = False
                elif event.key == pygame.K_s:
                    backward = False
                elif event.key == pygame.K_a:
                    strafe_left = False
                elif event.key == pygame.K_d:
                    strafe_right = False
                elif event.key == pygame.K_LEFT:
                    turn_left = False
                elif event.key == pygame.K_RIGHT:
                    turn_right = False
        
        # Update engine
        engine.update(forward, backward, strafe_left, strafe_right, turn_left, turn_right)
        
        # Render scene
        engine.render(draw_hud)
        
        # Update display
        pygame.display.flip()
    
    # Clean up
    engine.cleanup()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
