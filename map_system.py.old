# Asteroid Frontier RPG
# Map and Level System

import pygame
import csv
import os

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
        self.npcs = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        # Load tile images (these would be your actual game assets)
        self.tiles = {
            # Placeholder surfaces for now
            "wall": self.create_placeholder_tile((100, 100, 100)),
            "floor": self.create_placeholder_tile((50, 50, 50)),
            "door": self.create_placeholder_tile((150, 75, 0)),
            "water": self.create_placeholder_tile((0, 0, 150)),
            "npc": self.create_placeholder_tile((255, 0, 0)),
            "player_start": self.create_placeholder_tile((0, 255, 0))
        }
        
        # Load the map data
        self.load_map(map_file)
    
    def create_placeholder_tile(self, color):
        """Create a placeholder surface for a tile"""
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(color)
        return surface
    
    def load_map(self, filename):
        """Load map from a CSV file"""
        map_data = []
        
        # In a real game, you'd load from a file like this:
        # with open(os.path.join('assets', 'maps', filename), 'r') as file:
        #     reader = csv.reader(file)
        #     for row in reader:
        #         map_data.append(row)
        
        # For this example, let's create a simple map
        map_data = [
            ['wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall'],
            ['wall', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'npc', 'floor', 'floor', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'floor', 'floor', 'player_start', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'npc', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'water', 'water', 'floor', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'water', 'water', 'floor', 'floor', 'floor', 'floor', 'wall'],
            ['wall', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor', 'door', 'wall'],
            ['wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall', 'wall']
        ]
        
        # Process the map data
        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                # Calculate the position
                pos_x = x * self.tile_size
                pos_y = y * self.tile_size
                
                if tile == 'player_start':
                    # Mark the player starting position
                    self.start_x = pos_x
                    self.start_y = pos_y
                    # Also place a floor tile here
                    floor_tile = Tile(self.tiles['floor'], pos_x, pos_y, 'floor')
                    self.floor_tiles.add(floor_tile)
                    self.all_sprites.add(floor_tile)
                elif tile == 'npc':
                    # This position will be used to place an NPC
                    # For now, add a floor tile underneath
                    floor_tile = Tile(self.tiles['floor'], pos_x, pos_y, 'floor')
                    self.floor_tiles.add(floor_tile)
                    self.all_sprites.add(floor_tile)
                    # The actual NPC will be created elsewhere
                elif tile == 'wall':
                    wall = Tile(self.tiles['wall'], pos_x, pos_y, 'wall')
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif tile == 'door':
                    door = Tile(self.tiles['door'], pos_x, pos_y, 'door')
                    self.objects.add(door)
                    self.all_sprites.add(door)
                else:
                    # All other tiles (floor, water, etc.)
                    game_tile = Tile(self.tiles[tile], pos_x, pos_y, tile)
                    if tile == 'floor':
                        self.floor_tiles.add(game_tile)
                    else:
                        self.objects.add(game_tile)
                    self.all_sprites.add(game_tile)

class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height
    
    def apply(self, entity):
        """Move the entity by the camera offset"""
        return entity.rect.move(self.camera.topleft)
    
    def apply_rect(self, rect):
        """Move the rectangle by the camera offset"""
        return rect.move(self.camera.topleft)
    
    def update(self, target):
        """Update camera position to follow the target"""
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        
        # Limit scrolling to map size
        x = min(0, x)  # left
        y = min(0, y)  # top
        x = max(-(self.map_width - self.width), x)  # right
        y = max(-(self.map_height - self.height), y)  # bottom
        
        self.camera = pygame.Rect(x, y, self.map_width, self.map_height)

class Level:
    def __init__(self, level_name, screen_width, screen_height, tile_size):
        self.name = level_name
        self.map = Map(f"{level_name}.csv", tile_size)
        self.camera = Camera(screen_width, screen_height, 
                           len(self.map.map_data[0]) * tile_size,
                           len(self.map.map_data) * tile_size)
        
        # Additional level-specific data could go here:
        # - Available quests
        # - Special events
        # - Background music
        # - Weather effects
        # - etc.
    
    def setup_npcs(self, npc_data):
        """
        Add NPCs to the level based on provided data
        npc_data is a list of dictionaries containing NPC information
        """
        for npc_info in npc_data:
            x = npc_info['x'] * self.map.tile_size
            y = npc_info['y'] * self.map.tile_size
            # Create NPC (would use your actual NPC class)
            # npc = NPC(x, y, npc_info['name'], npc_info['dialogue'])
            # self.map.npcs.add(npc)
            # self.map.all_sprites.add(npc)
    
    def draw(self, screen, player):
        """Draw the level and all entities in camera view"""
        # Update camera to follow player
        self.camera.update(player)
        
        # Draw all sprites with camera offset
        for sprite in self.map.all_sprites:
            screen.blit(sprite.image, self.camera.apply(sprite))
        
        # You would also draw NPCs, objects, and the player here

# Example usage:
# level = Level("psyche_township", SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
# player = Player(level.map.start_x, level.map.start_y)
