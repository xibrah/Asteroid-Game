# Asteroid Frontier RPG
# Map and Level System, 3/14/25

import pygame
import csv
import os
import random

class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, tile_type):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.tile_type = tile_type  # Can be "wall", "floor", "door", etc.

class Map:
    def __init__(self, map_file, tile_size):
        self.tile_size = tile_size
        self.start_x, self.start_y = 0, 0  # Starting position for the player
        self.walls = pygame.sprite.Group()
        self.floor_tiles = pygame.sprite.Group()
        self.objects = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.npc_positions = {}  # Dictionary to store NPC starting positions
        self.layout = []  # Store raw layout for easier access
        
        # Colors for different tile types
        self.tile_colors = {
            'W': (100, 100, 100),  # Wall - Gray
            'F': (50, 50, 50),     # Floor - Dark Gray
            'D': (150, 75, 0),     # Door - Brown
            'T': (120, 60, 20),    # Table - Dark Brown
            'C': (160, 82, 45),    # Chair - Sienna
            'B': (139, 69, 19),    # Bar/Bed - Saddle Brown
            'S': (160, 120, 90),   # Storage - Tan
            'M': (70, 70, 90),     # Machine/Military - Blue-Gray
            'G': (173, 216, 230),  # Glass/Guard - Light Blue
            'P': (169, 169, 169),  # Prison Cell - Dark Gray
            'V': (135, 206, 235),  # Viewport - Sky Blue
            'H': (105, 105, 105),  # Hangar/Helm - Dim Gray
            'X': (192, 192, 192),  # Exhibit - Silver
            'R': (128, 128, 128),  # Robot - Gray
            'E': (0, 128, 0)       # Exit - Green
        }
        
        # Load the map data
        self.width = 0
        self.height = 0
        self.load_map(map_file)
    
    def create_placeholder_tile(self, color):
        """Create a placeholder surface for a tile"""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(color)
        return surface
    
    def load_map(self, map_file):
        """Load map from a CSV file"""
        try:
            # Determine the map path
            map_path = os.path.join('assets', 'maps', map_file)
            print(f"Loading map from: {map_path}")
            
            # Check if file exists
            if not os.path.exists(map_path):
                print(f"Map file not found: {map_path}")
                return self.create_test_map()
                
            # Read the map file
            with open(map_path, 'r') as file:
                y = 0
                for line in file:
                    # Skip comments and empty lines
                    if line.strip().startswith('#') or not line.strip():
                        continue
                    
                    # Add the row to the raw layout
                    self.layout.append(line.strip())
                    
                    # Process each character in the line
                    for x, char in enumerate(line.strip()):
                        # Calculate the position
                        pos_x = x * self.tile_size
                        pos_y = y * self.tile_size
                        
                        # Create the appropriate tile based on the character
                        self.create_tile(char, pos_x, pos_y, x, y)
                    
                    y += 1  # Move to next row
            
            # Calculate map dimensions
            self.width = max([len(row) for row in self.layout]) * self.tile_size
            self.height = len(self.layout) * self.tile_size
            
            print(f"Map loaded with dimensions {self.width}x{self.height}")
            return True
            
        except Exception as e:
            print(f"Error loading map {map_file}: {e}")
            return self.create_test_map()
    
    def create_tile(self, char, pos_x, pos_y, grid_x, grid_y):
        """Create a tile based on its character representation"""
        if char == '@':  # Player starting position
            floor = Tile(self.create_placeholder_tile(self.tile_colors['F']), pos_x, pos_y, 'floor')
            self.floor_tiles.add(floor)
            self.all_sprites.add(floor)
            
            # Store player start position
            self.start_x = pos_x
            self.start_y = pos_y
            
        elif char in '123456789':  # NPC position
            floor = Tile(self.create_placeholder_tile(self.tile_colors['F']), pos_x, pos_y, 'floor')
            self.floor_tiles.add(floor)
            self.all_sprites.add(floor)
            
            # Store NPC position
            self.npc_positions[int(char)] = (pos_x, pos_y)
            
        elif char == 'W':  # Wall
            wall = Tile(self.create_placeholder_tile(self.tile_colors['W']), pos_x, pos_y, 'wall')
            self.walls.add(wall)
            self.all_sprites.add(wall)
            
        elif char == 'D':  # Door
            door = Tile(self.create_placeholder_tile(self.tile_colors['D']), pos_x, pos_y, 'door')
            self.doors.add(door)
            self.all_sprites.add(door)
            
        elif char == 'E':  # Exit
            exit_tile = Tile(self.create_placeholder_tile(self.tile_colors['E']), pos_x, pos_y, 'exit')
            exit_tile.is_exit = True  # Make sure this attribute is set
            self.objects.add(exit_tile)
            self.all_sprites.add(exit_tile)
            
        elif char == 'H':  # Hangar/Helm - special handling for ship controls
            helm = Tile(self.create_placeholder_tile(self.tile_colors['H']), pos_x, pos_y, 'helm')
            helm.tile_type = 'helm'  # Specifically mark as helm for interaction
            self.objects.add(helm)
            self.all_sprites.add(helm)
            
        elif char in self.tile_colors:  # Other defined tile types
            tile_color = self.tile_colors[char]
            tile = Tile(self.create_placeholder_tile(tile_color), pos_x, pos_y, char.lower())
            
            if char == 'F':
                self.floor_tiles.add(tile)
            else:
                self.objects.add(tile)
                
            self.all_sprites.add(tile)
            
        else:  # Default to floor for any other character
            floor = Tile(self.create_placeholder_tile(self.tile_colors['F']), pos_x, pos_y, 'floor')
            self.floor_tiles.add(floor)
            self.all_sprites.add(floor)
    
    def create_test_map(self):
        """Create a simple test map when loading fails"""
        print("Creating test map")
        
        # Create a simple room with walls around the edges
        for x in range(25):
            for y in range(20):
                if x == 0 or x == 24 or y == 0 or y == 19:
                    # Create a wall
                    wall = Tile(self.create_placeholder_tile(self.tile_colors['W']), 
                               x * self.tile_size, y * self.tile_size, 'wall')
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                else:
                    # Create a floor tile
                    floor = Tile(self.create_placeholder_tile(self.tile_colors['F']), 
                                x * self.tile_size, y * self.tile_size, 'floor')
                    self.floor_tiles.add(floor)
                    self.all_sprites.add(floor)
        
        # Add a test exit
        exit_tile = Tile(self.create_placeholder_tile(self.tile_colors['E']), 
                        12 * self.tile_size, 18 * self.tile_size, 'exit')
        exit_tile.is_exit = True
        self.objects.add(exit_tile)
        self.all_sprites.add(exit_tile)
        
        # Set dimensions
        self.width = 25 * self.tile_size
        self.height = 20 * self.tile_size
        
        # Set player start position
        self.start_x = 12 * self.tile_size
        self.start_y = 10 * self.tile_size
        
        return True

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = 0
        self.map_height = 0
        
    def set_map_size(self, map_width, map_height):
        """Set the size of the map to properly constrain the camera"""
        self.map_width = map_width
        self.map_height = map_height
        
    def apply(self, entity):
        """Return a rect with camera offset applied"""
        if hasattr(entity, 'rect'):
            new_rect = entity.rect.copy()
            new_rect.x += self.camera.x
            new_rect.y += self.camera.y
            return new_rect
        elif isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        else:
            return entity
        
    def update(self, target):
        """Update camera position to track target (usually the player)"""
        # Calculate camera offset to center the target
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        
        # Limit the camera so we don't see beyond the map edges
        if self.map_width > 0:
            x = min(0, x)  # left limit
            x = max(-(self.map_width - self.width), x)  # right limit
            
        if self.map_height > 0:
            y = min(0, y)  # top limit
            y = max(-(self.map_height - self.height), y)  # bottom limit
        
        # Update camera position
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Level:
    def __init__(self, level_id, map_file, screen_width, screen_height, tile_size=32):
        self.id = level_id
        self.name = level_id
        self.map = Map(map_file, tile_size)
        self.camera = Camera(screen_width, screen_height)
        self.camera.set_map_size(self.map.width, self.map.height)
        
        # Group all necessary components into a dictionary for easy access
        self.components = {
            "name": level_id,
            "walls": self.map.walls,
            "floor": self.map.floor_tiles,
            "objects": self.map.objects,
            "doors": self.map.doors,
            "all_sprites": self.map.all_sprites,
            "npc_positions": self.map.npc_positions,
            "player_start": (self.map.start_x, self.map.start_y),
            "width": self.map.width,
            "height": self.map.height,
            "layout": self.map.layout
        }
        
    def get_data(self):
        """Get all level data as a dictionary"""
        return self.components
    
    def setup_npcs(self, npc_data):
        """
        Add NPCs to the level based on provided data
        npc_data is a list of dictionaries containing NPC information
        """
        for npc_info in npc_data:
            x = npc_info.get('x', 0) * self.map.tile_size
            y = npc_info.get('y', 0) * self.map.tile_size
            # Create NPC (would use your actual NPC class)
            # npc = NPC(x, y, npc_info['name'], npc_info['dialogue'])
            # self.map.npcs.add(npc)
            # self.map.all_sprites.add(npc)
    
    def draw(self, screen, player, camera):
        """Draw the level with camera offset"""
        # Update camera to follow player
        camera.update(player)
        
        # Draw all sprites with camera offset
        for sprite in self.map.all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))