# Asteroid Frontier RPG
# Main Game

import pygame
import sys
import os
import random
import math
import json

# Import game modules
# In a real project, these would be separate files
from game_structure import Game, GameState, Player, NPC
from map_system import Map, Camera, Level, Tile
from character_system import Character, Player as PlayerCharacter, NPC as NPCCharacter
from dialogue_quest_system import DialogueManager, QuestManager, Quest
from item_inventory import Inventory, ItemFactory
from space_travel_system import SystemMap, Location
from space_travel import SpaceTravel
from camera import Camera
from save_system import SaveSystem, SaveLoadMenu
from merchant_system import MerchantSystem

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
SPACE_BG = (5, 5, 20)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Asteroid Frontier")
clock = pygame.time.Clock()

# Create asset directories if they don't exist
os.makedirs('assets/images', exist_ok=True)
os.makedirs('assets/maps', exist_ok=True)
os.makedirs('assets/dialogues', exist_ok=True)
os.makedirs('assets/quests', exist_ok=True)
os.makedirs('assets/items', exist_ok=True)
os.makedirs('assets/icons', exist_ok=True)
os.makedirs('saves', exist_ok=True)

class SpaceMap:
    """simple debug version 3/4/25"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.locations = {}  # Dictionary of locations {id: Location}
        
        # No need for the complex background generation yet
        self.background = pygame.Surface((width, height))
        self.background.fill((5, 5, 20))  # Simple dark background
        
        # Simple star field
        for _ in range(1000):
            x = random.randint(0, width)
            y = random.randint(0, height)
            brightness = random.randint(50, 255)
            size = 1 if brightness < 200 else 2
            pygame.draw.circle(self.background, 
                             (brightness, brightness, brightness), 
                             (x, y), size)
    
    def add_location(self, location_id, location_data):
        """Add a location to the space map"""
        self.locations[location_id] = location_data
        print(f"Added location: {location_id} at {location_data['position']}")

class PlayerShip:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.rotation = 0  # In degrees, 0 = up
        
        # For collision detection
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
    def update(self, keys, dt):
        """Update ship position based on input"""
        dx = 0
        dy = 0
        
        # Simplified movement for testing
        if keys[pygame.K_LEFT]:
            dx = -self.speed
        if keys[pygame.K_RIGHT]:
            dx = self.speed
        if keys[pygame.K_UP]:
            dy = -self.speed
        if keys[pygame.K_DOWN]:
            dy = self.speed
        
        # Update position
        self.x += dx
        self.y += dy
        
        # Update collision rectangle
        self.rect.x = self.x - 10
        self.rect.y = self.y - 10

class AsteroidFrontier:
    def __init__(self):
        self.game_state = GameState.MAIN_MENU
        self.player = PlayerCharacter("New_Droid", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)
        
        # Create camera
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Create game systems
        self.dialogue_manager = DialogueManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.quest_manager = QuestManager()

        # Initialize empty objects for safety
        self.current_level = None
        self.npcs = pygame.sprite.Group()
        
        # Load game data from files
        self.npcs_data = self.load_npcs()
        self.locations_data = self.load_locations()
        self.quests_data = self.load_quests()
        self.items_data = self.load_items()        
        
        # Create solar system map
        self.system_map = self.create_system_map()
        
         # Space travel initialization
        self.space_travel = None  # Will be created when entering space
        self.in_space_mode = False
        
        # Create locations
        self.locations = self.create_locations()
        self.docked_location = "psyche_township"
        
        # Try to load initial player location - use a fallback to ensure we have a valid current_level
        success = self.load_location("psyche_township")
        if not success or not self.current_level:
            # Create a minimal default level if loading failed
            self.create_default_level()
        
        self.near_exit = False  # Track if player is near an exit
        self.near_helm = False  # Track if player is near the helm
    
        self.near_repair = False  # Track if player is near a repair point
        self.current_repair_point = None
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        
        # Game flags
        self.show_inventory = False
        self.show_map = False
        self.show_quest_log = False

        # Initialize spaceship attributes
        self.space_map = None  # Will be created when needed
        self.player_ship = None
        self.camera_pos = (0, 0)
        self.near_location = None
   
    def initialize_systems(self):
        """Initialize all game systems, 3/11/25"""
        print("Initializing game systems...")
    
        # Initialize space travel system
        if not hasattr(self, 'space_travel') or self.space_travel is None:
            from space_travel import SpaceTravel
            self.space_travel = SpaceTravel(SCREEN_WIDTH, SCREEN_HEIGHT)
        
            # Add locations from your game data
            print("Adding locations to space travel")
            for loc in self.locations_data:
                if loc.get('id') != 'space':  # Skip the space location itself
                    # Generate a position based on some data from the location
                    # This ensures locations are consistently positioned
                    x = hash(loc.get('id', '')) % 3000 - 1500  # Generate x between -1500 and 1500
                    y = hash(loc.get('name', '')) % 2500 - 1250  # Generate y between -1250 and 1250
                
                    # Add location to space travel
                    self.space_travel.add_location(
                        loc.get('id'),
                        loc.get('name', 'Unknown'),
                        x, y,
                        (200, 200, 200)  # Default color - could vary based on faction
                    )
        
            # Initialize asteroid field
            #self.space_travel.integrate_asteroid_field()
            #print("Asteroid field integrated into space travel")
    
        # Initialize merchant system
        self.initialize_merchant_system()
    
        # Add weapon firing capability to space travel
        if not hasattr(self, 'last_weapon_fire_time'):
            self.last_weapon_fire_time = 0
    
        # Initialize save system if needed
        if not hasattr(self, 'save_system'):
            from save_system import SaveSystem
            self.save_system = SaveSystem(self)
            print("Save system initialized")
    
        # Track visited locations
        if not hasattr(self, 'visited_locations'):
            self.visited_locations = []
            # Add current location if one exists
            if self.current_level and "name" in self.current_level:
                location_id = self.current_level["name"]
                if location_id not in self.visited_locations:
                    self.visited_locations.append(location_id)
    
        print("All systems initialized")
        
    def create_default_level(self):
        """Create a minimal default level when other loading methods fail, 3/8/25"""
        print("Creating default level as fallback")
        self.current_level = {
            "name": "default_level",
            "walls": pygame.sprite.Group(),
            "floor": pygame.sprite.Group(),
            "objects": pygame.sprite.Group(),
            "all_sprites": pygame.sprite.Group(),
            "width": SCREEN_WIDTH,
            "height": SCREEN_HEIGHT,
            "player_start": (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        }
    
        # Create a basic room with walls and a floor
        wall_size = TILE_SIZE
        room_width = SCREEN_WIDTH - (wall_size * 2)
        room_height = SCREEN_HEIGHT - (wall_size * 2)
    
        # Create floor
        floor = pygame.sprite.Sprite()
        floor.image = pygame.Surface((room_width, room_height))
        floor.image.fill((50, 50, 50))  # Dark gray floor
        floor.rect = floor.image.get_rect()
        floor.rect.x = wall_size
        floor.rect.y = wall_size
        self.current_level["floor"].add(floor)
        self.current_level["all_sprites"].add(floor)
    
        # Create walls (top, right, bottom, left)
        wall_positions = [
            (0, 0, SCREEN_WIDTH, wall_size),  # Top
            (SCREEN_WIDTH - wall_size, 0, wall_size, SCREEN_HEIGHT),  # Right
            (0, SCREEN_HEIGHT - wall_size, SCREEN_WIDTH, wall_size),  # Bottom
            (0, 0, wall_size, SCREEN_HEIGHT)  # Left
        ]
    
        for x, y, w, h in wall_positions:
            wall = pygame.sprite.Sprite()
            wall.image = pygame.Surface((w, h))
            wall.image.fill((100, 100, 100))  # Gray walls
            wall.rect = wall.image.get_rect()
            wall.rect.x = x
            wall.rect.y = y
            self.current_level["walls"].add(wall)
            self.current_level["all_sprites"].add(wall)
    
        # Add an exit
        exit_tile = pygame.sprite.Sprite()
        exit_tile.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        exit_tile.image.fill((0, 255, 0))  # Green for exit
        exit_tile.rect = exit_tile.image.get_rect()
        exit_tile.rect.x = SCREEN_WIDTH // 2
        exit_tile.rect.y = SCREEN_HEIGHT - (wall_size * 2)
        exit_tile.is_exit = True
        self.current_level["objects"].add(exit_tile)
        self.current_level["all_sprites"].add(exit_tile)
    
        print("Default level created successfully")
        
    def load_npcs(self):
        """Load NPC data from JSON file"""
        try:
            with open(os.path.join('assets', 'dialogues', 'npcs.json'), 'r') as file:
                data = json.load(file)
                return data["npcs"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading NPCs: {e}")
            return []

    def load_npcs_from_json(self, location_id):
        """Load NPCs for a location from the npcs.json file"""
        try:
            import json
            npcs_file = os.path.join('assets', 'dialogues', 'npcs.json')
        
            # Check if file exists
            if os.path.exists(npcs_file):
                with open(npcs_file, 'r') as file:
                    data = json.load(file)
                print(f"NPCs file loaded with {len(data.get('npcs', []))} entries")
            else:
                print(f"NPCs file not found: {npcs_file}")
                return pygame.sprite.Group()
            
            npcs_data = data.get("npcs", [])
            location_npcs = pygame.sprite.Group()
        
            # Find NPCs for this location
            for npc_data in npcs_data:
                name = npc_data.get("name", "Unknown")
                position = npc_data.get("position", {})
                npc_location = position.get("location", "unknown")

                if npc_location == location_id:
                    from character_system import NPC as NPCCharacter
                
                    # Get NPC position
                    x = position.get("x", 0)
                    y = position.get("y", 0)
                
                    # Get dialogue
                    dialogue_data = npc_data.get("dialogue", {})
                    default_dialogue = dialogue_data.get("default", ["Hello."])
                
                    # Create NPC with default dialogue initially
                    npc = NPCCharacter(name, x=x, y=y, dialogue=default_dialogue)
                
                    # Store the full dialogue data for use when starting conversations
                    npc.full_dialogue = dialogue_data
                
                    # Set faction
                    npc.faction = npc_data.get("faction", "independent")
                
                    # Add quests if available
                    quest_ids = npc_data.get("quests", [])
                    if quest_ids:
                        from dialogue_quest_system import Quest
                        quest = Quest(quest_ids[0], f"{npc.name}'s Task", 
                                    "Help with an important task.", ["Complete the objective"])
                        quest.credit_reward = 100
                        quest.xp_reward = 50
                        npc.quest = quest
                
                    # Add to group
                    location_npcs.add(npc)
                    print(f"Loaded NPC from JSON: {npc.name}")
        
            return location_npcs
    
        except Exception as e:
            print(f"Error loading NPCs from JSON: {e}")
            return pygame.sprite.Group()

    def create_npc_from_data(self, npc_data):
        """Create an NPC object from loaded data"""
        # Extract basic NPC information
        npc_id = npc_data.get('id', 'unknown')
        name = npc_data.get('name', 'Unknown NPC')
        faction = npc_data.get('faction', 'independent')
    
        # Get position if available
        position = npc_data.get('position', {})
        x = position.get('x', 10) * TILE_SIZE
        y = position.get('y', 10) * TILE_SIZE
    
        # Get dialogue
        dialogue_data = npc_data.get('dialogue', {})
        default_dialogue = dialogue_data.get('default', ["Hello."])
    
        # Create NPC object
        from character_system import NPC as NPCCharacter
        npc = NPCCharacter(name, x=x, y=y, dialogue=default_dialogue)
    
        # Set additional properties
        npc.faction = faction
        npc.id = npc_id
    
        # Set quest if available
        quest_ids = npc_data.get('quests', [])
        if quest_ids:
            # For now, just create a simple placeholder quest
            from dialogue_quest_system import Quest
            quest = Quest(quest_ids[0], f"{name}'s Task", 
                         "Help with an important task.", ["Complete the objective"])
            quest.credit_reward = 100
            quest.xp_reward = 50
            npc.quest = quest
    
        # Set shop if available
        npc.has_shop = len(npc_data.get('shop_inventory', [])) > 0
    
        return npc

    def load_map_from_file(self, map_file):
        """Load a map from a text file, 3/8/25"""
        # At the beginning of the function
        print(f"Attempting to load map file: {map_file}")
        try:
            # Determine path for the map file
            map_path = os.path.join('assets', 'maps', map_file)
            print(f"Looking for map at: {map_path}")
        
            # Check if file exists
            if not os.path.exists(map_path):
                print(f"Map file not found: {map_path}")
                return self.create_test_level(map_file.split('.')[0])  # Fallback to test level
        
            # Initialize level data
            print(f"Map OK: {map_path}")
            level = {}
            level["name"] = map_file.split('.')[0]
            level["walls"] = pygame.sprite.Group()
            level["floor"] = pygame.sprite.Group()
            level["objects"] = pygame.sprite.Group()
            level["doors"] = pygame.sprite.Group()
            level["all_sprites"] = pygame.sprite.Group()
            level["npc_positions"] = {}  # Dictionary to store NPC starting positions
            level["player_start"] = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # Default position
        
            # Map from characters to colors/types
            tile_colors = {
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
                'H': (105, 105, 105),  # Hangar - Dim Gray
                'X': (192, 192, 192),  # Exhibit - Silver
                'R': (128, 128, 128),  # Robot - Gray
                'E': (0, 128, 0)       # Exit - Green
            }
        
            # Read the map file
            with open(map_path, 'r') as file:
                y = 0
                for line in file:
                    # Skip comments and empty lines
                    if line.strip().startswith('#') or not line.strip():
                        continue
                
                    # Process each character in the line
                    for x, char in enumerate(line.strip()):
                        # Create a position
                        pos_x = x * TILE_SIZE
                        pos_y = y * TILE_SIZE
                    
                        # Create the appropriate tile based on the character
                        if char == 'W':  # Wall
                            wall = pygame.sprite.Sprite()
                            wall.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            wall.image.fill(tile_colors['W'])
                            wall.rect = wall.image.get_rect()
                            wall.rect.x = pos_x
                            wall.rect.y = pos_y
                            level["walls"].add(wall)
                            level["all_sprites"].add(wall)
                    
                        elif char == 'D':  # Door
                            door = pygame.sprite.Sprite()
                            door.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            door.image.fill(tile_colors['D'])
                            door.rect = door.image.get_rect()
                            door.rect.x = pos_x
                            door.rect.y = pos_y
                            level["doors"].add(door)
                            level["all_sprites"].add(door)
                    
                        elif char == '@':  # Player starting position
                            floor = pygame.sprite.Sprite()
                            floor.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            floor.image.fill(tile_colors['F'])
                            floor.rect = floor.image.get_rect()
                            floor.rect.x = pos_x
                            floor.rect.y = pos_y
                            level["floor"].add(floor)
                            level["all_sprites"].add(floor)
                        
                            # Store player start position
                            level["player_start"] = (pos_x, pos_y)
                    
                        elif char in '123456789':  # NPC position
                            floor = pygame.sprite.Sprite()
                            floor.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            floor.image.fill(tile_colors['F'])
                            floor.rect = floor.image.get_rect()
                            floor.rect.x = pos_x
                            floor.rect.y = pos_y
                            level["floor"].add(floor)
                            level["all_sprites"].add(floor)
                        
                            # Store NPC position
                            level["npc_positions"][int(char)] = (pos_x, pos_y)
                            print(f"Found NPC position {char} at ({pos_x}, {pos_y})")
                    
                        elif char == 'E':  # Exit
                            exit_tile = pygame.sprite.Sprite()
                            exit_tile.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            exit_tile.image.fill((0, 255, 0))  # Bright green for visibility
                            exit_tile.rect = exit_tile.image.get_rect()
                            exit_tile.rect.x = pos_x
                            exit_tile.rect.y = pos_y
                            exit_tile.is_exit = True  # Make sure this attribute is set
                            level["objects"].add(exit_tile)
                            level["all_sprites"].add(exit_tile)
                            print(f"Created exit tile at ({pos_x}, {pos_y})")
                    
                        elif char in tile_colors:  # Other defined tile types
                            tile = pygame.sprite.Sprite()
                            tile.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            tile.image.fill(tile_colors[char])
                            tile.rect = tile.image.get_rect()
                            tile.rect.x = pos_x
                            tile.rect.y = pos_y
                        
                            if char == 'F':
                                level["floor"].add(tile)
                            else:
                                level["objects"].add(tile)
                            
                            level["all_sprites"].add(tile)
                    
                        else:  # Default to floor for any other character
                            floor = pygame.sprite.Sprite()
                            floor.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                            floor.image.fill(tile_colors['F'])
                            floor.rect = floor.image.get_rect()
                            floor.rect.x = pos_x
                            floor.rect.y = pos_y
                            level["floor"].add(floor)
                            level["all_sprites"].add(floor)
                
                    y += 1  # Move to next row
        
            # Calculate map size from the loaded map data
            map_width = 0
            map_height = 0
        
            # Find furthest right wall and lowest wall
            for sprite in level["all_sprites"]:
                map_width = max(map_width, sprite.rect.right)
                map_height = max(map_height, sprite.rect.bottom)
        
            # Store map dimensions in level data
            level["width"] = max(map_width, SCREEN_WIDTH)  # Ensure at least screen width
            level["height"] = max(map_height, SCREEN_HEIGHT)  # Ensure at least screen height
        
            # Update camera with map size
            self.camera.set_map_size(level["width"], level["height"])
        
            # Add special handling for helm tiles in ship cabin
            if map_file == "mvp_ship_cabin.csv":
                # Store raw layout for easier access
                level["layout"] = []
            
                # Open the map file again to read raw layout
                try:
                    map_path = os.path.join('assets', 'maps', map_file)
                    with open(map_path, 'r') as file:
                        for line in file:
                            # Skip comments and empty lines
                            if line.strip().startswith('#') or not line.strip():
                                continue
                        
                            # Add the row to the layout
                            level["layout"].append(line.strip())
                
                    print(f"Loaded raw layout with {len(level['layout'])} rows")
                
                    # Mark helm tiles specially
                    for y, row in enumerate(level["layout"]):
                        for x, tile in enumerate(row):
                            if tile == 'H':  # Helm tile
                                # Find the sprite at this position and mark it
                                for sprite in level["all_sprites"]:
                                    if sprite.rect.x == x * TILE_SIZE and sprite.rect.y == y * TILE_SIZE:
                                        sprite.tile_type = 'helm'
                                        print(f"Marked helm tile at ({x}, {y})")
                except Exception as e:
                    print(f"Error loading raw layout: {e}")
                    # Continue without the raw layout - not critical
        
            return level
    
        except Exception as e:
            print(f"Error loading map {map_file}: {e}")
            return self.create_test_level(map_file.split('.')[0])  # Fallback to test level

    def load_locations(self):
        """Load location data from JSON file"""
        try:
            with open(os.path.join('assets', 'maps', 'locations.json'), 'r') as file:
                data = json.load(file)
                return data["locations"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading locations: {e}")
            return []

    def load_quests(self):
        """Load quest data from JSON file"""
        try:
            with open(os.path.join('assets', 'quests', 'quests.json'), 'r') as file:
                data = json.load(file)
                return data["quests"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading quests: {e}")
            return []

    def load_items(self):
        """Load item data from JSON file"""
        try:
            with open(os.path.join('assets', 'items', 'items.json'), 'r') as file:
                data = json.load(file)
                return data["items"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading items: {e}")
            return []

    def load_location_npcs(self, location_id):
        """Load NPCs for a specific location from JSON data"""
        #npcs = pygame.sprite.Group()
    
        """Load NPCs for a location from the npcs.json file"""
        try:
            with open(os.path.join('assets', 'dialogues', 'npcs.json'), 'r') as file:
                data = json.load(file)
            
            npcs_data = data.get("npcs", [])
            location_npcs = pygame.sprite.Group()
        
            # Find NPCs for this location
            for npc_data in npcs_data:
                position = npc_data.get("position", {})
                if position.get("location") == location_id:
                    from character_system import NPC as NPCCharacter
                
                    # Get NPC position
                    x = position.get("x", 0)
                    y = position.get("y", 0)
                
                    # Get dialogue
                    dialogue_data = npc_data.get("dialogue", {})
                    default_dialogue = dialogue_data.get("default", ["Hello."])
                
                    # Create NPC
                    npc = NPCCharacter(npc_data.get("name", "Unknown"), 
                                      x=x, 
                                      y=y, 
                                      dialogue=default_dialogue)
                
                    # Set faction
                    npc.faction = npc_data.get("faction", "independent")
                
                    # Add quests if available
                    quest_ids = npc_data.get("quests", [])
                    if quest_ids:
                        from dialogue_quest_system import Quest
                        quest = Quest(quest_ids[0], f"{npc.name}'s Task", 
                                   "Help with an important task.", ["Complete the objective"])
                        quest.credit_reward = 100
                        quest.xp_reward = 50
                        npc.quest = quest
                
                    # Add to group
                    location_npcs.add(npc)
                    print(f"Loaded NPC from JSON: {npc.name}")
        
            return location_npcs
    
        except Exception as e:
            print(f"Error loading NPCs from JSON: {e}")
            return pygame.sprite.Group()
        
        if len(self.npcs) > 0 and "npc_positions" in self.current_level:
            print("Positioning JSON NPCs using map positions...")
            # Create a mapping of common NPC names to position IDs
            name_to_id = {
                "stella vega": 1,
                "robot #27": 2, 
                "#27": 2,
                "gus": 3,
                "mayor gus": 3,
                "township merchant": 4,
                "mining coordinator": 5,
                "bartender": 6,
                "leo": 7
            }
    
            # Try to position NPCs based on their names
            for npc in self.npcs:
                name_lower = npc.name.lower()
                for name_pattern, position_id in name_to_id.items():
                    if name_pattern in name_lower and position_id in self.current_level["npc_positions"]:
                        # Position this NPC according to the map
                        x, y = self.current_level["npc_positions"][position_id]
                        npc.rect.x = x
                        npc.rect.y = y
                        print(f"Positioned {npc.name} at map position {position_id}: ({x}, {y})")
                        break
    
        # If no NPCs found in data, create some default ones
        if len(npcs) == 0:
            if location_id == "psyche_township":
                # Create Stella
                stella = NPCCharacter("Stella", x=10*TILE_SIZE, y=8*TILE_SIZE, 
                                     dialogue=["Welcome to Psyche Township!", 
                                              "I'm Governor Stella Vega."])
                stella.faction = "mars"
                npcs.add(stella)
            
                # Create Gus
                gus = NPCCharacter("Gus", x=15*TILE_SIZE, y=12*TILE_SIZE, 
                                   dialogue=["As mayor, I'm trying to keep the peace here.", 
                                            "The Earth garrison is causing trouble."])
                npcs.add(gus)
            
                # Add quest to Gus
                from dialogue_quest_system import Quest
                quest = Quest("q001", "Supply Run", 
                             "Collect supplies for the township.", 
                             ["Collect 5 supply crates"])
                quest.credit_reward = 100
                quest.xp_reward = 50
                gus.quest = quest
    
        return npcs

    def create_system_map(self):
        """Create the solar system map with locations"""
        system_map = SystemMap(1000, 1000)
        
        # Add locations
        psyche = Location("Psyche", "Mining colony and shipyard", "psyche_map.csv", 
                          position=(500, 300), faction="mars")
        ceres = Location("Ceres", "Major trading hub", "ceres_map.csv", 
                         position=(300, 200), faction="earth")
        pallas = Location("Pallas", "Syndicate stronghold", "pallas_map.csv", 
                          position=(700, 400), faction="pallas")
        vesta = Location("Vesta", "Mining outpost", "vesta_map.csv", 
                         position=(400, 500), faction="earth")
        luna = Location("Luna", "Earth's moon and gateway to space", "luna_map.csv", 
                        position=(200, 300), faction="earth")
        mars = Location("Mars", "Industrialized planet", "mars_map.csv", 
                       position=(150, 400), faction="mars")
        
        # Add connections
        psyche.add_connection("ceres", 200)
        psyche.add_connection("pallas", 250)
        psyche.add_connection("vesta", 150)
        psyche.add_connection("mars", 350)
        
        ceres.add_connection("psyche", 200)
        ceres.add_connection("vesta", 180)
        ceres.add_connection("luna", 280)
        
        pallas.add_connection("psyche", 250)
        
        vesta.add_connection("psyche", 150)
        vesta.add_connection("ceres", 180)
        
        luna.add_connection("ceres", 280)
        luna.add_connection("mars", 300)
        
        mars.add_connection("luna", 300)
        mars.add_connection("psyche", 350)
        
        # Add locations to map
        system_map.add_location("psyche", psyche)
        system_map.add_location("ceres", ceres)
        system_map.add_location("pallas", pallas)
        system_map.add_location("vesta", vesta)
        system_map.add_location("luna", luna)
        system_map.add_location("mars", mars)
        
        # Set player location
        system_map.set_player_location("psyche")
        
        return system_map
    
    def create_locations(self):
        """Create detailed location information"""
        locations = {}
        
        # Psyche Township
        locations["psyche_township"] = {
            "map_file": "psyche_township.csv",
            "npcs": [
                {
                    "name": "Stella",
                    "x": 10,
                    "y": 8,
                    "dialogue": ["Welcome to Psyche Township!", "I'm Governor Stella Vega."],
                    "quest": None
                },
                {
                    "name": "Gus",
                    "x": 15,
                    "y": 12,
                    "dialogue": ["As mayor, I'm trying to keep the peace here.", "The Earth garrison is causing trouble."],
                    "quest": {
                        "id": "q001",
                        "title": "Supply Run",
                        "description": "Collect supplies for the township.",
                        "objectives": ["Collect 5 supply crates"],
                        "reward_credits": 100,
                        "reward_xp": 50
                    }
                },
                {
                    "name": "#27",
                    "x": 9,
                    "y": 8,
                    "dialogue": ["Unit designation 27 acknowledges your presence.", "Security protocols are active."],
                    "quest": None
                }
            ],
            "items": [
                {"id": "medkit", "x": 12, "y": 10, "quantity": 1},
                {"id": "space_pistol", "x": 18, "y": 15, "quantity": 1}
            ],
            "services": ["shop", "repair", "inn"]
        }
        
        # Rusty Rocket (on Ceres)
        locations["rusty_rocket"] = {
            "map_file": "rusty_rocket.csv",
            "npcs": [
                {
                    "name": "Ruby",
                    "x": 8,
                    "y": 5,
                    "dialogue": ["Welcome to The Rusty Rocket!", "We offer the finest hospitality in the Belt."],
                    "quest": None
                },
                {
                    "name": "CV",
                    "x": 15,
                    "y": 7,
                    "dialogue": ["Looking for news? I've got stories from all over the system.", "Just don't believe everything Earth tells you."],
                    "quest": {
                        "id": "q002",
                        "title": "The Truth Behind the News",
                        "description": "Help CV gather information for his next exposé.",
                        "objectives": ["Record 3 garrison conversations"],
                        "reward_credits": 150,
                        "reward_xp": 75
                    }
                }
            ],
            "items": [
                {"id": "energy_pack", "x": 10, "y": 12, "quantity": 2}
            ],
            "services": ["inn", "drinks"]
        }
        
        # Add more locations...
        
        return locations
    
    def load_location(self, location_id):
        """Load a specific location's map and NPCs, 3/8/25"""
        print(f"Loading location: {location_id}")
    
        try:
            # Special handling for ship cabin
            if location_id == "ship_cabin":
                # Load the ship cabin map file
                map_file = "mvp_ship_cabin.csv"
                self.current_level = self.load_map_from_file(map_file)
                if not self.current_level:
                    print("Failed to load ship cabin, creating fallback level")
                    self.create_default_level()
                    self.current_level["name"] = "ship_cabin"  # Override name
                else:
                    self.current_level["name"] = "ship_cabin"
            
                # Set up player position
                if hasattr(self, 'player') and self.current_level and "player_start" in self.current_level:
                    self.player.rect.x = self.current_level["player_start"][0]
                    self.player.rect.y = self.current_level["player_start"][1]
                    print(f"Placing player at start position: ({self.player.rect.x}, {self.player.rect.y})")
            
                # No NPCs in ship cabin yet
                self.npcs = pygame.sprite.Group()
            
                return True

            # Check if location exists in our data
            location_data = None
            for loc in self.locations_data:
                if loc.get('id') == location_id:
                    location_data = loc
                    break
        
            # Get map file name
            map_file = f"{location_id}.csv" # Use .csv extension
            if location_data and 'map_file' in location_data:
                map_file = location_data['map_file']
        
            # Load map from file
            self.current_level = self.load_map_from_file(map_file)
        
            # If loading failed, create default level
            if not self.current_level:
                print(f"Failed to load map for {location_id}, creating fallback level")
                self.create_default_level()
                self.current_level["name"] = location_id  # Override name
        
            # Place player at starting position
            if hasattr(self, 'player') and self.current_level and "player_start" in self.current_level:
                # First, ensure we have a valid start position
                if self.current_level["player_start"][0] > 0 and self.current_level["player_start"][1] > 0:
                    self.player.rect.x = self.current_level["player_start"][0]
                    self.player.rect.y = self.current_level["player_start"][1]
                    print(f"Placing player at start position: ({self.player.rect.x}, {self.player.rect.y})")
                else:
                    # Fallback: Place player in the center of the map
                    self.player.rect.x = self.current_level["width"] // 2
                    self.player.rect.y = self.current_level["height"] // 2
                    print(f"Using fallback player position: ({self.player.rect.x}, {self.player.rect.y})")

            # Try loading NPCs from JSON first
            self.npcs = self.load_npcs_from_json(location_id)
        
            # If no NPCs were loaded from JSON, fall back to map positions
            if len(self.npcs) == 0:
                print("No NPCs found in JSON, using map positions")
                # Create default NPCs based on map positions
                if self.current_level and "npc_positions" in self.current_level:
                    from character_system import NPC as NPCCharacter
                
                    # Dictionary of default NPCs for each location
                    default_npcs = {
                        "psyche_township": {
                            1: {"name": "Stella Vega", "dialogue": ["Welcome to Psyche Township!", "I'm Governor Stella Vega."]},
                            2: {"name": "Robot #27", "dialogue": ["Unit designation 27 acknowledges your presence.", "Security protocols are active."]},
                            3: {"name": "Gus", "dialogue": ["As mayor, I'm trying to keep the peace here.", "The Earth garrison is causing trouble."]},
                            4: {"name": "Township Merchant", "dialogue": ["Looking to trade?", "I've got supplies from all over the Belt."]},
                            5: {"name": "Mining Coordinator", "dialogue": ["The ore yields have been good this month.", "We need more workers though."]},
                            6: {"name": "Bartender", "dialogue": ["What'll it be?", "Martian whiskey is on special today."]},
                            7: {"name": "Leo", "dialogue": ["Great to see you!", "My robotics business is doing well here."]}
                        },
                        # Add default NPCs for other locations as needed
                    }
                
                    # Create NPCs based on the map positions and default data
                    if location_id in default_npcs:
                        for npc_id, position in self.current_level["npc_positions"].items():
                            if npc_id in default_npcs[location_id]:
                                npc_data = default_npcs[location_id][npc_id]
                                npc = NPCCharacter(npc_data["name"], 
                                                x=position[0], 
                                                y=position[1], 
                                                dialogue=npc_data["dialogue"])
                            
                                # Add quest if it's Gus in Psyche Township
                                if location_id == "psyche_township" and npc_id == 3:
                                    from dialogue_quest_system import Quest
                                    quest = Quest("q001", "Supply Run", 
                                                "Collect supplies for the township.", 
                                                ["Collect 5 supply crates"])
                                    quest.credit_reward = 100
                                    quest.xp_reward = 50
                                    npc.quest = quest
                            
                                self.npcs.add(npc)
                                print(f"Created NPC: {npc_data['name']} at position ({position[0]}, {position[1]})")
            else:
                print(f"Using {len(self.npcs)} NPCs loaded from JSON")

            # Initialize items group
            self.items = pygame.sprite.Group()
        
            return True
        
        except Exception as e:
            print(f"ERROR in load_location: {e}")
            # Create emergency fallback level
            self.create_default_level()
            self.current_level["name"] = location_id  # Override name
            self.npcs = pygame.sprite.Group()  # Empty NPCs
            return False  # Still return False to indicate failure
    
    def create_test_level(self, location_id):
        """Create a test level with walls and floor - would be replaced with actual level loading"""
        level = {}
        level["name"] = location_id
        level["walls"] = pygame.sprite.Group()
        level["floor"] = pygame.sprite.Group()
        level["objects"] = pygame.sprite.Group()
        level["all_sprites"] = pygame.sprite.Group()
        
        # Create a simple room with walls around the edges
        for x in range(25):
            for y in range(20):
                if x == 0 or x == 24 or y == 0 or y == 19:
                    # Create a wall
                    wall = pygame.sprite.Sprite()
                    wall.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    wall.image.fill((100, 100, 100))
                    wall.rect = wall.image.get_rect()
                    wall.rect.x = x * TILE_SIZE
                    wall.rect.y = y * TILE_SIZE
                    level["walls"].add(wall)
                    level["all_sprites"].add(wall)
                else:
                    # Create a floor tile
                    floor = pygame.sprite.Sprite()
                    floor.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    floor.image.fill((50, 50, 50))
                    floor.rect = floor.image.get_rect()
                    floor.rect.x = x * TILE_SIZE
                    floor.rect.y = y * TILE_SIZE
                    level["floor"].add(floor)
                    level["all_sprites"].add(floor)
        
        return level
    
    def check_exit_collision(self):
        """Check if player is colliding with an exit tile, 3/8/25"""
        # Make sure we have a valid current_level object
        if self.current_level is None:
            self.near_exit = False
            return False
        
        # Make sure we have the objects sprite group
        if "objects" not in self.current_level or not self.current_level["objects"]:
            return False
    
        # Get all exit objects
        exits = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_exit')]
    
        if not exits:
            self.near_exit = False
            return False
    
        # Check each exit tile
        for exit_tile in exits:
            # Calculate distance to exit
            dx = self.player.rect.centerx - exit_tile.rect.centerx
            dy = self.player.rect.centery - exit_tile.rect.centery
            distance = (dx**2 + dy**2)**0.5
        
            # If within interaction range
            if distance < TILE_SIZE * 1.5:
                self.near_exit = True
            
                # Only show travel menu if T key is pressed
                keys = pygame.key.get_pressed()
                if keys[pygame.K_t]:
                    # Special handling for ship cabin
                    if self.current_level and self.current_level.get("name") == "ship_cabin":
                        print("Exit from ship cabin detected")
                        self.process_ship_cabin_exit()
                        return True
                    else:
                        # Regular travel for other locations
                        print("T key pressed, showing travel menu")
                        self.show_travel_options()
                        return True
            
                # Display hint even if T is not pressed
                return False
    
        # Not near any exit
        self.near_exit = False
        return False

    def handle_events(self):
        """Process game events, eva mode 3/11/25"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
            # Handle merchant events if in merchant mode
            if self.game_state == GameState.MERCHANT:
                if self.handle_merchant_events(event):
                    continue
            
            if event.type == pygame.KEYDOWN:
                
                # Special key combinations for save/load
                if event.key == pygame.K_F5:
                    # Quick save
                    if hasattr(self, 'save_system'):
                        self.save_system.quick_save()
                        return True
        
                if event.key == pygame.K_F9:
                    # Quick load
                    if hasattr(self, 'save_system'):
                        self.save_system.quick_load()
                        return True
        
                if event.key == pygame.K_F6:
                    # Save menu
                    self.game_state = GameState.SAVE_MENU
                    self.update_save_load_menus()
                    return True
    
                if event.key == pygame.K_F7:
                    # Load menu
                    self.game_state = GameState.LOAD_MENU
                    self.update_save_load_menus()
                    return True

                # Special handling for EVA mode
                if event.key == pygame.K_ESCAPE and self.current_level and self.current_level.get("name") == "ship_eva":
                    print("ESC pressed in EVA mode - returning to ship")
                    self.end_eva()
                    return True
                
                # Merchant system

                # Main menu Enter key handling
                if self.game_state == GameState.MAIN_MENU and event.key == pygame.K_RETURN:
                    print("Enter key pressed at main menu, transitioning to OVERWORLD")
                    self.game_state = GameState.OVERWORLD
                    return True

                # Handle escape key safely
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == GameState.SPACE_TRAVEL:
                        # Ask for confirmation before exiting space mode
                        # For now, just go back to the last location
                        if self.current_level and 'name' in self.current_level:
                            self.load_location(self.current_level['name'])
                            self.game_state = GameState.OVERWORLD
                            self.in_space_mode = False
                        else:
                            # Fallback to main menu
                            self.game_state = GameState.MAIN_MENU
                    elif self.game_state == GameState.MAIN_MENU:
                        return False
                    # Other states...
                    elif self.game_state == GameState.MAIN_MENU:
                        return False
                    elif self.game_state == GameState.TRAVEL_MENU:
                        print("Escape from travel menu, returning to OVERWORLD")
                        self.game_state = GameState.OVERWORLD
                        return True
                    else:
                        self.game_state = GameState.MAIN_MENU
            
                # Handle events for Save Menu states
                if self.game_state == GameState.SAVE_MENU or self.game_state == GameState.LOAD_MENU:
                    if hasattr(self, 'save_load_menu'):
                        self.save_load_menu.handle_event(event, self)
                        return True
                
                # Safe travel menu input handling
                if self.game_state == GameState.TRAVEL_MENU:
                    try:
                        # Number keys 1-9
                        if pygame.K_1 <= event.key <= pygame.K_9:
                            index = event.key - pygame.K_1
                            print(f"Travel menu selection: index {index}")
                        
                            if 0 <= index < len(self.travel_options):
                                destination = self.travel_options[index]
                                print(f"Selected destination: {destination}")
                            
                                # First change state to avoid issues
                                self.game_state = GameState.OVERWORLD
                            
                                # Then initiate travel
                                success = self.travel_to_location(destination)
                                if not success:
                                    print(f"Travel to {destination} failed!")
                                    # No state change needed, already set to OVERWORLD
                            else:
                                print(f"Invalid selection index: {index}")
                    except Exception as e:
                        print(f"ERROR in travel menu handling: {e}")
                        self.game_state = GameState.OVERWORLD  # Recover gracefully
            
                # Your other key handlers here...
                if event.key == pygame.K_i:
                    self.show_inventory = not self.show_inventory
            
                if event.key == pygame.K_m:
                    self.show_map = not self.show_map
            
                if event.key == pygame.K_q:
                    self.show_quest_log = not self.show_quest_log
            
                # Handle dialogue key input
                if self.dialogue_manager.is_dialogue_active():
                    self.dialogue_manager.handle_key(event.key)
        
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.dialogue_manager.is_dialogue_active():
                        self.dialogue_manager.handle_click(event.pos)
                    elif self.game_state == GameState.OVERWORLD:
                        # Check for NPC interaction if we're close enough
                        for npc in self.npcs:
                            if pygame.sprite.collide_rect(self.player, npc):
                                self.dialogue_manager.start_dialogue(npc, self.player)
                                self.game_state = GameState.DIALOGUE
                                break
    
        return True
    
    def update(self, dt):
        """Update game state with ship interactions, 3/11/25"""
        if self.game_state == GameState.OVERWORLD:
            # Update player
            keys = pygame.key.get_pressed()
            if self.current_level and "walls" in self.current_level:
                self.player.update(keys, dt, self.current_level["walls"])
            else:
                # Fallback if no current level or walls
                self.player.update(keys, dt, None)
        
            # Update NPCs
            self.npcs.update(dt, self.player)
        
            # Check for repair interactions in EVA
            if self.current_level and self.current_level.get("name") == "ship_eva":
                self.check_repair_interaction()
            
                # Check for return to ship
                if keys[pygame.K_ESCAPE]:
                    self.end_eva()
                    return
            
            # Check for exit collision
            self.check_exit_collision()
        
            # Check for ship interactions
            if self.current_level and self.current_level.get("name") == "ship_cabin":
                # Only check ship interactions if we're in the cabin
                result = self.check_ship_interactions()
                if result:
                    # If interaction successful, we might have changed state
                    return

             # Check for merchant interactions
            self.check_merchant_interaction()
        
            # Handle E key for NPC interaction
            if keys[pygame.K_e]:
                for npc in self.npcs:
                    if pygame.sprite.collide_rect(self.player, npc):
                        self.dialogue_manager.start_dialogue(npc, self.player)
                        self.game_state = GameState.DIALOGUE
                        break
    
        elif self.game_state == GameState.DIALOGUE:
            # Check if dialogue has ended
            if not self.dialogue_manager.is_dialogue_active():
                self.game_state = GameState.OVERWORLD
    
        elif self.game_state == GameState.SPACE_TRAVEL:
            # Update space travel
            keys = pygame.key.get_pressed()
            self.space_travel.update(keys, dt)
            self.update_space_travel(dt)
        
            # Check if player is trying to dock
            if keys[pygame.K_e] and self.space_travel.near_location:
                location_id = self.space_travel.near_location
                self.dock_at_location(location_id)

        elif self.game_state == GameState.MERCHANT:
            # Update merchant interface
            self.update_merchant_menu(dt)
    
        elif self.game_state == GameState.TRAVEL_MENU:
            # Nothing to update for travel menu
            pass

    def show_travel_options(self):
        """Show available travel destinations"""
        self.game_state = GameState.TRAVEL_MENU
        self.travel_options = self.get_available_destinations()
        print(f"Travel options: {self.travel_options}")  # Debug

    def get_available_destinations(self):
        """Get a list of locations the player can travel to from the current location, ship_cabin 3/9/25"""
        valid_destinations = []
    
        # Get current location ID
        current_location_id = self.current_level['name'] if self.current_level else None
        if not current_location_id:
            print("Warning: No current location found")
            return valid_destinations
    
        print(f"Finding destinations from: {current_location_id}")
    
        # Special handling for ship cabin
        if current_location_id == "ship_cabin":
            # If docked, player can disembark to the docked location
            if hasattr(self, 'docked_location') and self.docked_location:
                valid_destinations.append(self.docked_location)
                print(f"Can disembark to: {self.docked_location}")
            # Always add EVA option from ship cabin
            valid_destinations.append("eva")
            print("Can perform EVA")
            return valid_destinations
    
        # Find current location in data
        current_location = None
        for loc in self.locations_data:
            if loc.get('id') == current_location_id:
                current_location = loc
                break
    
        # If location found in data, use its connections
        if current_location and 'connected_locations' in current_location:
            # Get all connected locations
            for connected_id in current_location.get('connected_locations', {}).keys():
                # Verify the destination map file exists before adding it as an option
                for loc in self.locations_data:
                    if loc.get('id') == connected_id:
                        map_file = loc.get('map_file', f"{connected_id}.csv")
                        map_path = os.path.join('assets', 'maps', map_file)
                    
                        if os.path.exists(map_path) or connected_id == "space":
                            valid_destinations.append(connected_id)
                            print(f"Valid destination found: {connected_id}")
                        else:
                            print(f"Warning: Map file not found for {connected_id}: {map_path}")
        else:
            # Use hardcoded connections if not found in data
            default_connections = {
                "psyche_township": ["shipyard_station", "ship_cabin"],
                "shipyard_station": ["psyche_township", "ship_cabin"],
                "rusty_rocket": ["ceres_port", "ship_cabin"],
                "ceres_port": ["rusty_rocket", "ship_cabin"],
                "pallas_wardenhouse": ["the_core_museum", "ship_cabin"],
                "the_core_museum": ["pallas_wardenhouse", "ship_cabin"]
            }
        
            # Check the default connections (only add ones that exist)
            if current_location_id in default_connections:
                for dest_id in default_connections[current_location_id]:
                    # Verify map file exists (except for special locations)
                    if dest_id in ["ship_cabin", "space", "eva"] or os.path.exists(os.path.join('assets', 'maps', f"{dest_id}.csv")):
                        valid_destinations.append(dest_id)
                        print(f"Valid default destination: {dest_id}")
    
        # If no valid destinations found, provide a safe default to avoid getting stuck
        if not valid_destinations and current_location_id != "psyche_township":
            # Always allow returning to psyche_township as a failsafe
            valid_destinations.append("psyche_township")
            print("No valid destinations found - adding psyche_township as failsafe")
    
        # Add ship cabin as an option if not already there (player can return to ship)
        if "ship_cabin" not in valid_destinations and current_location_id != "ship_cabin":
            valid_destinations.append("ship_cabin")
            print("Added ship_cabin as destination")
    
        print(f"Available destinations: {valid_destinations}")
        return valid_destinations

    def handle_travel_menu_events(self, event):
        """Handle events for the travel menu"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.game_state = GameState.OVERWORLD
                return True
            
            # Number keys 1-9 for selecting destinations
            if pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1
                if index < len(self.travel_options):
                    destination = self.travel_options[index]
                    self.travel_to_location(destination)
                    return True
                
        return False

    def travel_to_location(self, location_id):
        """Travel to a new location with special handling for ship-related destinations, 3/9/25"""
        print(f"Attempting to travel to {location_id}")
    
        # Special handling for ship cabin
        if location_id == "ship_cabin":
            # Going to ship
            print("Boarding the ship")
            self.enter_ship_cabin()
            return True
    
        # Special handling for EVA
        if location_id == "eva":
            print("Starting EVA operation")
            return self.perform_eva()
    
        # Special handling for space
        if location_id == "space":
            # This should now be handled at the helm console in the ship
            print("Warning: Space travel should be initiated from the ship's helm")
            return False
    
        # Check if we're in the ship cabin and trying to disembark
        if self.current_level and self.current_level.get("name") == "ship_cabin":
            if hasattr(self, 'docked_location') and self.docked_location == location_id:
                # Disembarking to the docked location
                print(f"Disembarking to {location_id}")
            
                # Store the destination before we load the location
                destination = self.docked_location
            
                # Clear the docked location since we're leaving the ship
                self.docked_location = None
            
                # Load the location
                success = self.load_location(destination)
                return success
            else:
                # If we're trying to go somewhere we're not docked, we need to go to space first
                print("Cannot travel directly to that location - not docked there")
                return False
    
        # For all other cases, verify this is a valid destination
        available_destinations = self.get_available_destinations()
        if location_id not in available_destinations:
            print(f"Error: {location_id} is not a valid destination")
            return False
    
        # Regular location loading
        success = self.load_location(location_id)
    
        if success:
            # If traveling to a location, dock the ship there
            if location_id not in ["ship_cabin", "space", "eva"]:
                self.docked_location = location_id
                print(f"Ship is now docked at {location_id}")
        
            # Reset game state
            self.game_state = GameState.OVERWORLD
            print(f"Successfully traveled to {location_id}")
            return True
        else:
            print(f"Failed to travel to {location_id}")
            return False
        
    def draw(self):
        """Render the game, space mvp 3/7/25"""
        screen.fill(SPACE_BG)

         # Draw space travel
        if self.game_state == GameState.SPACE_TRAVEL:
             # Draw space travel system
            self.space_travel.draw(screen)
        
            # Draw weapon visual effects 
            self.draw_weapon_visual(screen)
        
        elif self.game_state == GameState.MERCHANT:
            # Draw merchant interface
            self.draw_merchant(screen)

        # Draw Main Menu
        elif self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
    
        # Draw Overworld            
        elif self.game_state in [GameState.OVERWORLD, GameState.DIALOGUE, GameState.TRAVEL_MENU]:
            # Draw level with camera offset 3/4/25
            self.camera.update(self.player)
        
            if self.current_level and "all_sprites" in self.current_level:
                for sprite in self.current_level["all_sprites"]:
                    # Calculate position with camera offset
                    cam_pos = self.camera.apply(sprite)
                    screen.blit(sprite.image, cam_pos)
        
            # Draw NPCs with camera offset
            for npc in self.npcs:
                cam_pos = self.camera.apply(npc)
                screen.blit(npc.image, cam_pos)
        
            # Draw player with camera offset
            cam_pos = self.camera.apply(self.player)
            screen.blit(self.player.image, cam_pos)
        
            # Draw dialogue if active
            if self.dialogue_manager.is_dialogue_active():
                self.dialogue_manager.draw(screen)
        
            # Draw UI elements if not in dialogue
            if self.game_state != GameState.DIALOGUE:
                self.draw_ui()
        
            # Draw inventory if shown
            if self.show_inventory:
                self.draw_inventory()
        
            # Draw map if shown
            if self.show_map:
                self.draw_map()
        
            # Draw quest log if shown
            if self.show_quest_log:
                self.draw_quest_log()
        
            # Draw travel menu if in that state
            if self.game_state == GameState.TRAVEL_MENU:
                self.draw_travel_menu()
    
        # Draw save/load menus over everything else
        elif self.game_state in [GameState.SAVE_MENU, GameState.LOAD_MENU]:
            # First draw the game underneath
            if self.current_level and "all_sprites" in self.current_level:
                for sprite in self.current_level["all_sprites"]:
                    cam_pos = self.camera.apply(sprite)
                    screen.blit(sprite.image, cam_pos)
        
                # Draw NPCs
                for npc in self.npcs:
                    cam_pos = self.camera.apply(npc)
                    screen.blit(npc.image, cam_pos)
        
                # Draw player
                cam_pos = self.camera.apply(self.player)
                screen.blit(self.player.image, cam_pos)
    
            # Then draw the menu overlay
            if hasattr(self, 'save_load_menu'):
                self.save_load_menu.draw(screen, self)
        
        # Draw merchant interface
        elif self.game_state == GameState.MERCHANT:
            # First draw the game underneath
            if self.current_level and "all_sprites" in self.current_level:
                for sprite in self.current_level["all_sprites"]:
                    cam_pos = self.camera.apply(sprite)
                    screen.blit(sprite.image, cam_pos)
            
                # Draw NPCs
                for npc in self.npcs:
                    cam_pos = self.camera.apply(npc)
                    screen.blit(npc.image, cam_pos)
            
                # Draw player
                cam_pos = self.camera.apply(self.player)
                screen.blit(self.player.image, cam_pos)
        
            # Then draw the merchant interface
            if hasattr(self, 'merchant_system'):
                self.merchant_system.draw(screen, self)

        pygame.display.flip()
    
    def draw_main_menu(self):
        """Draw the main menu"""
        title_font = pygame.font.Font(None, 64)
        option_font = pygame.font.Font(None, 32)
        
        title = title_font.render("Asteroid Frontier", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        
        start = option_font.render("Press ENTER to Start", True, WHITE)
        start_rect = start.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        quit_text = option_font.render("Press ESC to Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        
        # Draw a starfield background
        for _ in range(100):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            brightness = random.randint(50, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), size)
        
        screen.blit(title, title_rect)
        screen.blit(start, start_rect)
        screen.blit(quit_text, quit_rect)
    
    def draw_ui(self):
        """Draw UI elements with ship-specific prompts, 3/8/25"""
        font = pygame.font.Font(None, 24)
    
        # Health bar
        health_text = font.render(f"Health: {self.player.health}/{self.player.max_health}", True, WHITE)
        screen.blit(health_text, (10, 10))
    
        # Credits
        money_text = font.render(f"Credits: {self.player.credits}", True, WHITE)
        screen.blit(money_text, (10, 40))
    
        # Current location
        location_name = self.current_level['name'].replace("_", " ").title() if self.current_level else "Unknown"
    
        # Special names for EVA
        if location_name == "Ship Eva":
            location_name = "Ship Exterior (EVA)"
        
        # Add docked status for ship cabin
        if location_name == "Ship Cabin" and hasattr(self, 'docked_location') and self.docked_location:
            docked_at = self.docked_location.replace("_", " ").title()
            location_name = f"Ship Cabin (Docked at {docked_at})"
    
        location_text = font.render(f"Location: {location_name}", True, WHITE)
        screen.blit(location_text, (SCREEN_WIDTH - location_text.get_width() - 10, 10))
    
        # Repair prompt for EVA
        if hasattr(self, 'near_repair') and self.near_repair and hasattr(self, 'current_repair_point'):
            repair_type = self.current_repair_point.repair_type.title()
            repair_text = font.render(f"Press E to repair {repair_type} System", True, (0, 255, 0))
            screen.blit(repair_text, (SCREEN_WIDTH//2 - repair_text.get_width()//2, SCREEN_HEIGHT - 90))
        
            hint_text = font.render("(ESC to return to ship)", True, (200, 200, 200))
            screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, SCREEN_HEIGHT - 60))
        
        # Exit hint - only show if player is near an exit
        if self.near_exit:
            exit_text = None
            if self.current_level and self.current_level.get("name") == "ship_cabin":
                if hasattr(self, 'docked_location') and self.docked_location:
                    exit_text = font.render(f"Press T to disembark to {self.docked_location.replace('_', ' ').title()}", True, (0, 255, 0))
                else:
                    exit_text = font.render("Press T to perform EVA", True, (0, 255, 0))
            else:
                exit_text = font.render("Press T to travel to a new location", True, (0, 255, 0))
            
            if exit_text:
                screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT - 60))
    
        # Helm interaction prompt
        if hasattr(self, 'near_helm') and self.near_helm:
            helm_text = None
            if hasattr(self, 'docked_location') and self.docked_location:
                helm_text = font.render(f"Press E to undock and launch into space", True, (0, 255, 255))
            else:
                helm_text = font.render("Press E to return to space flight", True, (0, 255, 255))
            
            if helm_text:
                screen.blit(helm_text, (SCREEN_WIDTH//2 - helm_text.get_width()//2, SCREEN_HEIGHT - 90))
    
        # Controls hint
        controls = font.render("I: Inventory | M: Map | Q: Quests | E: Interact | T: Travel", True, WHITE)
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, SCREEN_HEIGHT - 30))
    
    def draw_inventory(self):
        """Draw the player's inventory"""
        # Create an inventory panel
        panel_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        pygame.draw.rect(screen, (0, 0, 0, 200), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 2)
        
        font = pygame.font.Font(None, 32)
        title = font.render("Inventory", True, WHITE)
        screen.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 10))
        
        # In a real game, you'd list the player's inventory items here
        item_font = pygame.font.Font(None, 24)
        
        # Example items
        items = [
            {"name": "Medkit", "quantity": 2},
            {"name": "Space Pistol", "quantity": 1},
            {"name": "Energy Pack", "quantity": 3}
        ]
        
        for i, item in enumerate(items):
            item_text = item_font.render(f"{item['name']} x{item['quantity']}", True, WHITE)
            screen.blit(item_text, (panel_rect.x + 20, panel_rect.y + 50 + i * 30))
        
        close_text = item_font.render("Press I to close", True, WHITE)
        screen.blit(close_text, (panel_rect.centerx - close_text.get_width()//2, panel_rect.bottom - 30))
    
    def draw_map(self):
        """Draw the system map"""
        panel_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        pygame.draw.rect(screen, (0, 0, 0, 200), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 2)
        
        font = pygame.font.Font(None, 32)
        title = font.render("System Map", True, WHITE)
        screen.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 10))
        
        # Draw the system map
        self.system_map.draw(screen, offset=(panel_rect.x + 20, panel_rect.y + 50), scale=0.6)
        
        close_text = font.render("Press M to close", True, WHITE)
        screen.blit(close_text, (panel_rect.centerx - close_text.get_width()//2, panel_rect.bottom - 30))
    
    def draw_quest_log(self):
        """Draw the quest log"""
        panel_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        pygame.draw.rect(screen, (0, 0, 0, 200), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 2)
        
        font = pygame.font.Font(None, 32)
        title = font.render("Quest Log", True, WHITE)
        screen.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 10))
        
        # In a real game, you'd list active quests here
        quest_font = pygame.font.Font(None, 24)
        
        # Example quests
        quests = [
            {"title": "Supply Run", "description": "Collect supplies for the township.", "progress": "1/5 collected"},
            {"title": "The Truth Behind the News", "description": "Help CV gather information.", "progress": "0/3 recorded"}
        ]
        
        y_offset = panel_rect.y + 50
        for quest in quests:
            quest_title = quest_font.render(quest["title"], True, (255, 255, 0))
            screen.blit(quest_title, (panel_rect.x + 20, y_offset))
            y_offset += 25
            
            quest_desc = quest_font.render(quest["description"], True, WHITE)
            screen.blit(quest_desc, (panel_rect.x + 30, y_offset))
            y_offset += 25
            
            quest_progress = quest_font.render(quest["progress"], True, (0, 255, 0))
            screen.blit(quest_progress, (panel_rect.x + 30, y_offset))
            y_offset += 40
        
        close_text = quest_font.render("Press Q to close", True, WHITE)
        screen.blit(close_text, (panel_rect.centerx - close_text.get_width()//2, panel_rect.bottom - 30))

    def draw_travel_menu(self):
        """Draw the travel menu 3/4/25"""
        # Create menu panel
        panel_rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 200)
        pygame.draw.rect(screen, (0, 0, 0), panel_rect)
        pygame.draw.rect(screen, (255, 255, 255), panel_rect, 2)

        # Draw title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Travel to...", True, (255, 255, 255))
        screen.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 20))

        # Draw destination options
        option_font = pygame.font.Font(None, 24)
        y_offset = panel_rect.y + 70

        for i, destination in enumerate(self.travel_options):
            # Format destination name (replace underscores with spaces and capitalize)
            display_name = destination.replace("_", " ").title()
        
            # Highlight the option if mouse is hovering over it
            mouse_x, mouse_y = pygame.mouse.get_pos()
            option_rect = pygame.Rect(panel_rect.x + 50, y_offset, panel_rect.width - 100, 30)
        
            if option_rect.collidepoint(mouse_x, mouse_y):
                pygame.draw.rect(screen, (50, 50, 80), option_rect)
                option_text = option_font.render(f"{i+1}. {display_name}", True, (255, 255, 0))
            else:
                option_text = option_font.render(f"{i+1}. {display_name}", True, (200, 200, 200))
        
            screen.blit(option_text, (panel_rect.x + 50, y_offset))
            y_offset += 30

        # Draw instructions
        instructions = option_font.render("Press number key to select, ESC to cancel", True, (150, 150, 150))
        screen.blit(instructions, (panel_rect.centerx - instructions.get_width()//2, panel_rect.bottom - 40))

    def update_space_travel(self, dt):
        """Update space travel mode including weapon firing, 3/11/25"""
        if self.game_state != GameState.SPACE_TRAVEL:
            return

        # Debug
        #print("Updating space travel...")
    
        # Update player ship with pressed keys
        keys = pygame.key.get_pressed()
        #self.player_ship.update(keys, dt)
        self.space_travel.update(keys, dt)
    
        # Check for docking
        if keys[pygame.K_e] and self.space_travel.near_location:
            location_id = self.space_travel.near_location
            self.dock_at_location(location_id)
            return
        
        # Not near any location
        self.near_location = None
    
        # Add weapon firing with spacebar
        if keys[pygame.K_SPACE]:
            # Use the fire_weapon method from SpaceTravel class
            ship_x = self.space_travel.ship_pos[0]
            ship_y = self.space_travel.ship_pos[1]
            ship_angle = self.space_travel.ship_angle
        
            # This will handle the weapon firing logic
            self.space_travel.fire_weapon(ship_x, ship_y, ship_angle)
        
        # Debug resource info with I key
        if keys[pygame.K_i]:
            # Print resource information
            if hasattr(self.space_travel, 'asteroid_field'):
                resources = self.space_travel.asteroid_field.get_collected_resources()
                print(f"Collected resources: {resources}")
        
        # Handle returning to system map view
        if keys[pygame.K_m]:
            self.show_map = True
    
        # Update camera to follow player ship
        self.camera_pos = (
            int(self.space_travel.ship_pos[0] - SCREEN_WIDTH // 2),
            int(self.space_travel.ship_pos[1] - SCREEN_HEIGHT // 2)
    )

    def draw_space_travel(self, screen):
        """debug Draw the space travel view with direct screen access 3/4/25"""
        if self.game_state != GameState.SPACE_TRAVEL:
            return
    
        print("Drawing space travel...")
    
        try:
            # Get direct screen surface
            screen_surface = pygame.display.get_surface()
            if screen_surface is None:
                print("ERROR: No display surface available!")
                return
            
            # Fill with obvious color
            screen_surface.fill((255, 0, 0))  # Bright red
        
            # Draw a big test shape
            pygame.draw.rect(screen_surface, (0, 255, 0), (200, 150, 400, 300))  # Green rectangle
        
            # Draw text
            font = pygame.font.Font(None, 48)
            text = font.render("SPACE TEST", True, (255, 255, 255))
            screen_surface.blit(text, (300, 250))
        
            # Force immediate update
            pygame.display.update()
        
            print("Space drawing successful!")
        except Exception as e:
            print(f"SPACE DRAWING ERROR: {e}")

    def init_space_map(self):
        """Initialize the space map with all locations 3/4/25"""
        self.space_map = SpaceMap(10000, 8000)  # Large enough for the solar system
    
        # Add all locations from your location data
        location_count = 0
        for loc in self.locations_data:
            # Skip the "space" location itself
            if loc.get('id') == 'space':
                continue
            
            # Get position data or generate random position
            pos_x = random.randint(500, self.space_map.width - 500)
            pos_y = random.randint(500, self.space_map.height - 500)
        
            # If the location has map coordinates, use those instead
            if 'space_position' in loc:
                pos_x = loc['space_position'][0]
                pos_y = loc['space_position'][1]
        
            # Determine color based on faction
            color = (200, 200, 200)  # Default: gray
            if loc.get('faction') == 'earth':
                color = (0, 100, 255)  # Blue for Earth
            elif loc.get('faction') == 'mars':
                color = (255, 100, 0)  # Red-orange for Mars  
            elif loc.get('faction') == 'pallas':
                color = (150, 0, 150)  # Purple for Pallas
            
            # Add to space map
            self.space_map.add_location(loc.get('id'), {
                'name': loc.get('name', 'Unknown'),
                'position': (pos_x, pos_y),
                'color': color,
                'faction': loc.get('faction', 'independent')
            })
            location_count += 1
    
        print(f"Added {location_count} locations to space map")
        
        # Initialize player ship in center of map
        self.player_ship = PlayerShip(self.space_map.width // 2, self.space_map.height // 2)
        self.camera_pos = (
            self.player_ship.x - SCREEN_WIDTH // 2, 
            self.player_ship.y - SCREEN_HEIGHT // 2
        )
        self.near_location = None
        print("Space map initialization complete")

    def enter_space(self):
        """Transition to space travel mode, space mvp 3/7/25"""
        print("Entering space travel mode")
    
        try:
            # Initialize space travel system
            print("Creating SpaceTravel instance")
            self.space_travel = SpaceTravel(SCREEN_WIDTH, SCREEN_HEIGHT)
        
            # Add locations from your game data
            print("Adding locations to space travel")
            for loc in self.locations_data:
                if loc.get('id') != 'space':  # Skip the space location itself
                    self.space_travel.add_location(
                        loc.get('id'),
                        loc.get('name', 'Unknown'),
                        random.randint(-3000, 3000),  # Random x position
                        random.randint(-3000, 3000),  # Random y position
                        (200, 200, 200)  # Default color
                    )
        
            # Set game state
            self.game_state = GameState.SPACE_TRAVEL
            print("Space travel mode activated successfully")
            return True
        
        except Exception as e:
            print(f"ERROR initializing space travel: {e}")
            return False

    def enter_ship_cabin(self):
        """Transition to ship interior view, 3/8/25"""
        print("Entering ship cabin")
    
        # Set appropriate game state
        self.game_state = GameState.OVERWORLD
    
        # Load the ship cabin map
        self.load_location("ship_cabin")
    
        return True

    def exit_to_space(self):
        """Exit from cabin to space travel mode, 3/11/25"""
        print("Exiting to space")
    
        # Call the enter_space method to initialize space travel
        success = self.enter_space()
    
        if success and not hasattr(self, 'player_ship'):
            # Create the player ship
            from ship import PlayerShip  # Adjust import as needed
        
            # For now, create a simple PlayerShip object as a placeholder
            self.player_ship = PlayerShip(
                self.space_travel.ship_pos[0], 
                self.space_travel.ship_pos[1]
            )
            print("Player ship initialized")
    
        return success

    def dock_at_location(self, location_id):
        """Dock at a location from space mode - modified to go to cabin first, 3/8/25"""
        print(f"Docking at {location_id}")
    
        # First enter the ship cabin
        success = self.enter_ship_cabin()
    
        # Store the destination for when player uses the exit
        self.docked_location = location_id
    
        return success

    def process_ship_cabin_exit(self):
        """Handle exits from the ship cabin, 3/9/25"""
        print("Processing ship cabin exit")
    
        # Always show travel menu when exiting ship cabin
        self.show_travel_options()
        return True

    def process_helm_interaction(self):
        """Handle player interaction with the ship's helm, 3/8/25"""
        print("Interacting with ship helm")
    
        # Check if we're docked
        if hasattr(self, 'docked_location') and self.docked_location:
            # If docked, undock and enter space
            print(f"Undocking from {self.docked_location}")
            self.docked_location = None
            return self.exit_to_space()
        else:
            # If already in space, just enter space mode
            print("Returning to space flight")
            return self.exit_to_space()

    def check_ship_interactions(self):
        """Check for interactions with ship components like the helm, 3/8/24"""
        # Make sure we're in the ship cabin
        if not self.current_level or self.current_level.get("name") != "ship_cabin":
            return False
    
        # Reset helm proximity state
        self.near_helm = False
    
        # Find helm tiles in the map
        helm_positions = []
        for y, row in enumerate(self.current_level.get("layout", [])):
            for x, tile in enumerate(row):
                if tile == 'H':  # Helm tile
                    helm_positions.append((x * TILE_SIZE, y * TILE_SIZE))
    
        if not helm_positions:
            # Search for helm tiles in the map data directly
            for sprite in self.current_level["all_sprites"]:
                if hasattr(sprite, 'tile_type') and sprite.tile_type == 'helm':
                    helm_positions.append((sprite.rect.x, sprite.rect.y))
    
        # Only log if we found positions or it's the first time checking
        if helm_positions or not hasattr(self, '_ship_interactions_logged'):
            self._ship_interactions_logged = True
            #if helm_positions:
                #print(f"Found {len(helm_positions)} helm positions")
    
        # Check if player is near any helm position
        for helm_x, helm_y in helm_positions:
            # Calculate distance
            dx = self.player.rect.centerx - (helm_x + TILE_SIZE // 2)
            dy = self.player.rect.centery - (helm_y + TILE_SIZE // 2)
            distance = math.sqrt(dx**2 + dy**2)
        
            # If close enough and E is pressed, interact with helm
            if distance < TILE_SIZE * 1.5:
                self.near_helm = True
            
                # Only log once when near helm 
                if not hasattr(self, '_near_helm_logged') or not self._near_helm_logged:
                    self._near_helm_logged = True
                    print("Player near helm")
            
                # Handle helm interaction with E key
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    print("E key pressed near helm, processing interaction")
                    return self.process_helm_interaction()
            else:
                # Reset the logged state when not near helm
                if hasattr(self, '_near_helm_logged') and self._near_helm_logged:
                    self._near_helm_logged = False
    
        # Also treat helm tiles as walls to prevent walking through them
        for helm_x, helm_y in helm_positions:
            helm_rect = pygame.Rect(helm_x, helm_y, TILE_SIZE, TILE_SIZE)
            if self.player.rect.colliderect(helm_rect):
                # Push player back
                dx = self.player.rect.centerx - (helm_x + TILE_SIZE // 2)
                dy = self.player.rect.centery - (helm_y + TILE_SIZE // 2)
            
                # Move player in the direction of greatest overlap
                if abs(dx) > abs(dy):
                    if dx > 0:  # Player is to the right of helm
                        self.player.rect.left = helm_rect.right
                    else:  # Player is to the left of helm
                        self.player.rect.right = helm_rect.left
                else:
                    if dy > 0:  # Player is below helm
                        self.player.rect.top = helm_rect.bottom
                    else:  # Player is above helm
                        self.player.rect.bottom = helm_rect.top
    
        return False
    
    def perform_eva(self):
        """Start EVA using the ship design from mvp_ship.csv, 3/9/25"""
        print("Beginning EVA operations")
    
        # Check if we're in ship cabin
        if not self.current_level or self.current_level.get("name") != "ship_cabin":
            print("EVA can only be performed from ship cabin")
            return False
    
        # Create a new "level" for EVA
        self.current_level = {
            "name": "ship_eva",
            "walls": pygame.sprite.Group(),
            "floor": pygame.sprite.Group(),
            "objects": pygame.sprite.Group(),
            "all_sprites": pygame.sprite.Group(),
            "width": SCREEN_WIDTH * 2,
            "height": SCREEN_HEIGHT * 2
        }
    
        # First create a space background
        for _ in range(200):
            star = pygame.sprite.Sprite()
            star.image = pygame.Surface((1, 1))
            brightness = random.randint(100, 255)
            star.image.fill((brightness, brightness, brightness))
            star.rect = star.image.get_rect()
            star.rect.x = random.randint(0, self.current_level["width"])
            star.rect.y = random.randint(0, self.current_level["height"])
            self.current_level["all_sprites"].add(star)
    
        # Load the ship design from CSV
        ship_layout = []
        tile_size = 16  # Size of each tile in pixels
    
        try:
            # Try to load the ship CSV file
            ship_file_path = os.path.join('assets', 'ships', 'mvp_ship.csv')
        
            if os.path.exists(ship_file_path):
                print(f"Loading ship design from {ship_file_path}")
                with open(ship_file_path, 'r') as file:
                    for line in file:
                        # Skip comments and empty lines
                        if line.strip().startswith('#') or not line.strip():
                            continue
                        ship_layout.append(line.strip())
            
                print(f"Loaded ship with {len(ship_layout)} rows")
            else:
                print(f"Ship file not found: {ship_file_path}")
                # Create a default simple ship design
                ship_layout = [
                    "EEEEEEEEE",
                    "EEEHCHTEE",
                    "EEEHHHHHEE",
                    "EEEHPHHHEE",
                    "EEETTTTEE"
                ]
                print("Using default ship layout")
        except Exception as e:
            print(f"Error loading ship design: {e}")
            # Create a default simple ship design
            ship_layout = [
                "EEEEEEEEE",
                "EEEHCHTEE",
                "EEEHHHHHEE",
                "EEEHPHHHEE",
                "EEETTTTEE"
            ]
            print("Using default ship layout after error")
    
        # Determine ship dimensions
        ship_height = len(ship_layout)
        ship_width = max(len(row) for row in ship_layout)
    
        # Create ship exterior image
        ship_img_width = ship_width * tile_size
        ship_img_height = ship_height * tile_size
        ship_image = pygame.Surface((ship_img_width, ship_img_height))
        ship_image.fill((40, 40, 40))  # Dark background for empty space
    
        # Map tiles to colors
        tile_colors = {
            'E': None,           # Empty space - transparent
            'H': (100, 100, 100), # Hull - gray
            'C': (0, 200, 255),   # Cockpit - cyan
            'T': (255, 100, 0),   # Thruster - orange
            'S': (100, 200, 255), # Steering - light blue
            'W': (255, 50, 50),   # Weapon - red
            'P': (180, 180, 30),  # Power core - yellow
            'G': (100, 255, 100), # Shield - green
            'O': (150, 100, 50),  # Cargo - brown
            'X': (255, 50, 255)   # Special - purple
        }
    
        # Draw the ship based on layout
        repair_points = []
    
        for y, row in enumerate(ship_layout):
            for x, tile in enumerate(row):
                if tile in tile_colors and tile_colors[tile]:
                    # Draw this tile on the ship image
                    rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
                    pygame.draw.rect(ship_image, tile_colors[tile], rect)
                    pygame.draw.rect(ship_image, (50, 50, 50), rect, 1)  # Add border
                
                    # Add damage points for certain areas (to enable repair)
                    if tile == 'H' and random.random() < 0.1:  # Random hull damage
                        # Draw damage
                        damage_size = tile_size - 4
                        damage_rect = pygame.Rect(x * tile_size + 2, y * tile_size + 2, damage_size, damage_size)
                        pygame.draw.rect(ship_image, (150, 50, 50), damage_rect)  # Red damage
                    
                        # Create repair point
                        repair_point = pygame.sprite.Sprite()
                        repair_point.image = pygame.Surface((damage_size, damage_size))
                        repair_point.image.fill((150, 50, 50))
                        repair_point.rect = damage_rect.copy()
                        repair_point.repair_type = "hull"
                        repair_point.relative_pos = (x * tile_size + 2, y * tile_size + 2)
                        repair_points.append(repair_point)
                
                    elif tile == 'T':  # Engine damage 
                        if random.random() < 0.3:  # 30% chance for each thruster
                            # Draw damage
                            damage_rect = pygame.Rect(x * tile_size + 2, y * tile_size + 2, tile_size - 4, tile_size - 4)
                            pygame.draw.rect(ship_image, (200, 100, 50), damage_rect)  # Orange damage
                        
                            # Create repair point
                            repair_point = pygame.sprite.Sprite()
                            repair_point.image = pygame.Surface((tile_size - 4, tile_size - 4))
                            repair_point.image.fill((200, 100, 50))
                            repair_point.rect = damage_rect.copy()
                            repair_point.repair_type = "engine"
                            repair_point.relative_pos = (x * tile_size + 2, y * tile_size + 2)
                            repair_points.append(repair_point)
                
                    elif tile == 'W':  # Weapon damage
                        # Draw damage
                        center_x = x * tile_size + tile_size // 2
                        center_y = y * tile_size + tile_size // 2
                        radius = tile_size // 2 - 2
                        pygame.draw.circle(ship_image, (200, 50, 50), (center_x, center_y), radius)
                    
                        # Create repair point
                        repair_point = pygame.sprite.Sprite()
                        repair_point.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(repair_point.image, (200, 50, 50), (radius, radius), radius)
                        repair_point.rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
                        repair_point.repair_type = "weapon"
                        repair_point.relative_pos = (center_x - radius, center_y - radius)
                        repair_points.append(repair_point)
    
        # Make sure we have at least one repair point
        if not repair_points:
            print("No damage detected on ship - adding a hull damage point")
            # Add a single hull damage point
            damage_rect = pygame.Rect(ship_img_width // 2, ship_img_height // 2, tile_size, tile_size)
            pygame.draw.rect(ship_image, (150, 50, 50), damage_rect)
        
            repair_point = pygame.sprite.Sprite()
            repair_point.image = pygame.Surface((tile_size, tile_size))
            repair_point.image.fill((150, 50, 50))
            repair_point.rect = damage_rect.copy()
            repair_point.repair_type = "hull"
            repair_point.relative_pos = (ship_img_width // 2, ship_img_height // 2)
            repair_points.append(repair_point)
    
        # Create the ship sprite
        ship_exterior = pygame.sprite.Sprite()
        ship_exterior.image = ship_image
        ship_exterior.rect = ship_image.get_rect()
    
        # Position the ship in the center of the EVA area
        ship_exterior.rect.centerx = self.current_level["width"] // 2
        ship_exterior.rect.centery = self.current_level["height"] // 2
    
        # Add ship to level sprites
        self.current_level["all_sprites"].add(ship_exterior)
    
        # Add repair points to level and adjust their positions
        for point in repair_points:
            # Adjust positions to be relative to final ship position
            point.rect.x = ship_exterior.rect.x + point.relative_pos[0]
            point.rect.y = ship_exterior.rect.y + point.relative_pos[1]
            point.is_repair_point = True
        
            # Add to level
            self.current_level["objects"].add(point)
            self.current_level["all_sprites"].add(point)
    
        # Place player below the ship
        self.player.rect.centerx = ship_exterior.rect.centerx
        self.player.rect.y = ship_exterior.rect.bottom + 20
    
        # Set player start position
        self.current_level["player_start"] = (self.player.rect.x, self.player.rect.y)
    
        # Update camera to center on player
        self.camera.set_map_size(self.current_level["width"], self.current_level["height"])
    
        print(f"EVA mode activated with {len(repair_points)} repair points")
        print(f"Player positioned at ({self.player.rect.x}, {self.player.rect.y})")
    
        return True

    def check_repair_interaction(self):
        """Check if player is interacting with repair points during EVA, 3/8/25"""
        # Only check in EVA mode
        if not self.current_level or self.current_level.get("name") != "ship_eva":
            return False
    
        # Reset flag
        self.near_repair = False
        self.current_repair_point = None
    
        # Find repair points
        repair_points = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_repair_point')]
    
        if not repair_points:
            print("No repair points found in EVA mode!")
            return False
        
        for point in repair_points:
            # Calculate distance to repair point center
            dx = self.player.rect.centerx - point.rect.centerx
            dy = self.player.rect.centery - point.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
        
            # If close enough to interact
            if distance < TILE_SIZE * 2:
                self.near_repair = True
                self.current_repair_point = point
            
                # Check for E key press
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    print(f"Repairing {point.repair_type}")
                    self.perform_repair(point)
                    return True
            
                # Log only once when near a repair point
                if not hasattr(self, '_near_repair_logged') or not self._near_repair_logged:
                    self._near_repair_logged = True
                    print(f"Player near {point.repair_type} repair point")
            
                break  # Only handle one repair point at a time
    
        # Reset the logged state when not near any repair point
        if hasattr(self, '_near_repair_logged') and self._near_repair_logged and not self.near_repair:
            self._near_repair_logged = False
    
        return False

    def perform_repair(self, repair_point):
        """Perform repairs on a ship component, 3/8/25"""
        repair_type = repair_point.repair_type
    
        # Find the ship sprite (should be the first non-star sprite in all_sprites)
        ship_sprite = None
        for sprite in self.current_level["all_sprites"]:
            if hasattr(sprite, 'image') and sprite.image.get_width() > 10:  # Skip star sprites
                ship_sprite = sprite
                break
    
        if not ship_sprite:
            print("Error: Ship sprite not found for repair!")
            return
    
        print(f"Repairing {repair_type} on ship")
    
        if repair_type == "hull":
            # Visual feedback - color change to repair the damage
            pygame.draw.rect(ship_sprite.image, 
                            (100, 100, 100),  # Restore to hull color
                            (repair_point.rect.x - ship_sprite.rect.x,
                             repair_point.rect.y - ship_sprite.rect.y,
                             repair_point.rect.width,
                            repair_point.rect.height))
        
            # Remove this repair point
            self.current_level["objects"].remove(repair_point)
            self.current_level["all_sprites"].remove(repair_point)
            print("Hull damage repaired!")
    
        elif repair_type == "engine":
            # Visual feedback for engine repair
            pygame.draw.rect(ship_sprite.image, 
                            (100, 100, 100),  # Restore to hull color
                            (repair_point.rect.x - ship_sprite.rect.x,
                             repair_point.rect.y - ship_sprite.rect.y,
                             repair_point.rect.width,
                            repair_point.rect.height))
        
            # Remove this repair point
            self.current_level["objects"].remove(repair_point)
            self.current_level["all_sprites"].remove(repair_point)
            print("Engine repaired!")
    
        elif repair_type == "weapon":
            # Calculate center of the weapon damage point relative to ship
            center_x = repair_point.rect.centerx - ship_sprite.rect.x
            center_y = repair_point.rect.centery - ship_sprite.rect.y
            radius = repair_point.rect.width // 2
        
            # Visual feedback for weapon repair
            pygame.draw.circle(ship_sprite.image, 
                              (100, 100, 100),  # Restore to hull color
                              (center_x, center_y),
                              radius)
        
            # Remove this repair point
            self.current_level["objects"].remove(repair_point)
            self.current_level["all_sprites"].remove(repair_point)
            print("Weapon system repaired!")
    
        # Check if all repairs are done
        repair_points = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_repair_point')]
        if not repair_points:
            print("All repairs completed!")
            # Maybe show message or add reward?

    def end_eva(self):
        """End EVA and return to ship cabin, 3/9/25"""
        print("Ending EVA and returning to ship cabin")
    
        # Clear repair-related flags 
        self.near_repair = False
        self.current_repair_point = None
    
        # Set game state back to OVERWORLD
        self.game_state = GameState.OVERWORLD
    
        # Return to ship cabin
        success = self.enter_ship_cabin()
        print(f"Return to ship cabin {'succeeded' if success else 'failed'}")
        return success

    def add_save_system(self):
        """Add the save system to the game, 3/9/25"""
        self.save_system = SaveSystem(self)
    
        # Track visited locations
        if not hasattr(self, 'visited_locations'):
            self.visited_locations = []
    
        # Add the current location to visited if not already there
        if self.current_level and "name" in self.current_level:
            location_id = self.current_level["name"]
            if location_id not in self.visited_locations:
                self.visited_locations.append(location_id)

    def update_save_load_menus(self):
        """Initialize or update the save/load menu system, 3/9/25"""
        if not hasattr(self, 'save_load_menu'):
            self.save_load_menu = SaveLoadMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    
        # Refresh save list when entering menu
        if self.game_state in [GameState.SAVE_MENU, GameState.LOAD_MENU]:
            if not hasattr(self, '_last_menu_state') or self._last_menu_state != self.game_state:
                self.save_load_menu.refresh_save_list(self)
                self._last_menu_state = self.game_state
                
    def initialize_merchant_system(self):
        """Initialize or get the merchant system, 3/9/25"""
        if not hasattr(self, 'merchant_system'):
            self.merchant_system = MerchantSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.merchant_system.game = self
    
        return self.merchant_system

    def enter_merchant_mode(self):
        """Enter merchant trading mode"""
        if self.current_level and "name" in self.current_level:
            self.game_state = GameState.MERCHANT
        
            # Initialize merchant if needed
            self.initialize_merchant_system()
        
            return True
    
        return False
                
    def draw_merchant(self, screen):
        """Draw the merchant interface if active"""
        if self.game_state == GameState.MERCHANT:
            # First draw the game underneath
            if self.current_level and "all_sprites" in self.current_level:
                for sprite in self.current_level["all_sprites"]:
                    cam_pos = self.camera.apply(sprite)
                    screen.blit(sprite.image, cam_pos)
            
                # Draw NPCs
                for npc in self.npcs:
                    cam_pos = self.camera.apply(npc)
                    screen.blit(npc.image, cam_pos)
            
                # Draw player
                cam_pos = self.camera.apply(self.player)
                screen.blit(self.player.image, cam_pos)
        
            # Then draw the merchant interface
            if hasattr(self, 'merchant_system'):
                self.merchant_system.draw(screen, self)
    
    def draw_weapon_visual(self, screen):
        """Draw weapon visual effects, 3/11/25"""
        if hasattr(self, 'weapon_visual') and self.weapon_visual:
            # Draw the laser line
            if self.weapon_visual['current_frame'] < self.weapon_visual['duration']:
                # Calculate screen positions by applying camera offset from space travel
                start_x = self.weapon_visual['start'][0] - self.space_travel.camera_offset[0]
                start_y = self.weapon_visual['start'][1] - self.space_travel.camera_offset[1]
                end_x = self.weapon_visual['end'][0] - self.space_travel.camera_offset[0]
                end_y = self.weapon_visual['end'][1] - self.space_travel.camera_offset[1]
            
                # Draw the laser
                pygame.draw.line(
                    screen,
                    self.weapon_visual['color'],
                    (start_x, start_y),
                    (end_x, end_y),
                    self.weapon_visual['width']
                )
            
                # Add some glow effect at the end point
                pygame.draw.circle(
                    screen,
                    self.weapon_visual['color'],
                    (int(end_x), int(end_y)),
                    5
                )
            
                # Increment frame counter
                self.weapon_visual['current_frame'] += 1
            else:
                # Effect duration finished
                self.weapon_visual = None
            
    def fire_ship_weapon(self):
        """Fire the ship's weapon at asteroids, 3/12/25"""
        # Check if the space travel system has asteroid field and fire_weapon method
        if not hasattr(self.space_travel, 'asteroid_field') or not hasattr(self.space_travel, 'fire_weapon'):
            print("Weapon systems not available")
            return False
    
        # Get ship position and angle
        ship_x = self.space_travel.ship_pos[0]
        ship_y = self.space_travel.ship_pos[1]
        ship_angle = self.space_travel.ship_angle
    
        # Get weapon damage based on upgrades
        base_damage = 20
        weapon_level = getattr(self, 'ship_upgrades', {}).get('weapon', 0)
        damage_multiplier = 1.0 + (weapon_level * 0.3)  # 30% damage increase per level
        total_damage = base_damage * damage_multiplier
    
        # Add cooldown check to prevent rapid-fire
        current_time = pygame.time.get_ticks()
        if hasattr(self, 'last_weapon_fire_time') and current_time - self.last_weapon_fire_time < 250:
            # Weapon on cooldown
            return False
    
        # Store the time of this weapon fire
        self.last_weapon_fire_time = current_time
    
        # Visual feedback - create a laser effect
        self.create_weapon_visual(ship_x, ship_y, ship_angle)
    
        # Call the fire weapon method
        destroyed_asteroids = self.space_travel.fire_weapon(ship_x, ship_y, ship_angle)
    
        # Process results
        if destroyed_asteroids:
            # Play sound effect (if you have sound system implemented)
            # self.play_sound("asteroid_explosion")
        
            # Optional: Display some feedback about destroyed asteroids
            print(f"Destroyed {len(destroyed_asteroids)} asteroids!")
        
            return True
    
        return False

    def create_weapon_visual(self, ship_x, ship_y, ship_angle):
        """Create a visual effect for weapon firing, 3/12/25"""
        import math
    
        # Calculate the direction vector based on ship angle
        angle_rad = math.radians(ship_angle)
        dir_x = math.sin(angle_rad)
        dir_y = -math.cos(angle_rad)
    
        # Calculate laser endpoint
        laser_length = 300  # How far the laser extends
        end_x = ship_x + dir_x * laser_length
        end_y = ship_y + dir_y * laser_length
    
        # Store the laser effect data to be drawn in the next frame
        self.weapon_visual = {
            'start': (ship_x, ship_y),
            'end': (end_x, end_y),
            'color': (0, 255, 0),  # Green laser
            'width': 3,
            'duration': 5,  # Frames the laser will be visible
            'current_frame': 0
        }
                
    #debug stuff below#

    def test_game_states(self):
        """Test function to verify game state transitions work correctly 3/4/25"""
        print("\n--- RUNNING GAME STATE TEST ---")
    
        # Get the current state
        old_state = self.game_state
        print(f"Current game state: {self.game_state}")
    
        # Try changing to each state and rendering a test screen
        for state in [GameState.MAIN_MENU, GameState.OVERWORLD, GameState.DIALOGUE, 
                  GameState.INVENTORY, GameState.TRAVEL_MENU, GameState.SPACE_TRAVEL]:
        
            # Skip current state
            if state == old_state:
                continue
            
            print(f"Testing transition to state: {state}")
        
            # Set the state
            self.game_state = state
        
            # Draw a test screen for this state
            self._draw_test_screen(f"TEST: {state}")
        
            # Give a moment to see it
            pygame.time.delay(1000)
    
        # Restore original state
        print(f"Restoring original state: {old_state}")
        self.game_state = old_state
    
        print("--- GAME STATE TEST COMPLETE ---\n")

    def _draw_test_screen(self, message):
        """Draw a simple test screen with message 3/4/25"""
        # Get the screen surface
        screen = pygame.display.get_surface()
    
        # Fill with a color based on hash of the message (for variety)
        color_seed = sum(ord(c) for c in message)
        color = ((color_seed * 123) % 255, (color_seed * 45) % 255, (color_seed * 67) % 255)
        screen.fill(color)
    
        # Draw the message
        font = pygame.font.Font(None, 48)
        text = font.render(message, True, (255, 255, 255))
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, 
                           screen.get_height() // 2 - text.get_height() // 2))
    
        # Update the display
        pygame.display.flip()
        print(f"Drew test screen for: {message}")

    def check_merchant_interaction(self):
        """Check if player is interacting with a merchant NPC, 3/11/25"""
        # Make sure we're in the right game state and have NPCs
        if self.game_state != GameState.OVERWORLD or not hasattr(self, 'npcs'):
            return False
    
        # Get player position
        player_x, player_y = self.player.rect.x, self.player.rect.y
    
        # Check each NPC
        for npc in self.npcs:
            # Check if this NPC is a merchant (has shop inventory)
            is_merchant = False
        
            # Check if NPC has shop attribute or shop inventory
            if hasattr(npc, 'has_shop') and npc.has_shop:
                is_merchant = True
            elif hasattr(npc, 'shop_inventory') and npc.shop_inventory:
                is_merchant = True
        
            # Special case - hardcoded merchants for testing
            if npc.name in ["Township Merchant", "Leo", "Ruby"]:
                is_merchant = True
        
            # If NPC is a merchant and player is close enough
            if is_merchant:
                # Calculate distance to NPC
                npc_x, npc_y = npc.rect.x, npc.rect.y
                dx = player_x - npc_x
                dy = player_y - npc_y
                distance = math.sqrt(dx**2 + dy**2)
            
                # If player is close enough to interact
                if distance < TILE_SIZE * 2:
                    # Check for T key press
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_t]:
                        print(f"Interacting with merchant: {npc.name}")
                        self.enter_merchant_mode()
                        return True
                
                    # Display prompt even if E is not pressed
                    #self.draw_merchant_prompt(npc.name)
                    return False
    
        return False

    def update_merchant_menu(self, dt):
        """Update the merchant menu state, 3/11/25"""
        if self.game_state != GameState.MERCHANT:
            return
    
        # Initialize merchant system if needed
        if not hasattr(self, 'merchant_system'):
            self.merchant_system = MerchantSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.merchant_system.game = self  # Give merchant access to game state
    
        # Check for escape key to exit merchant menu
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.game_state = GameState.OVERWORLD
            print("Exiting merchant menu")

    def handle_merchant_events(self, event):
        """Handle events for the merchant menu, 3/11/25"""
        if self.game_state != GameState.MERCHANT:
            return False
    
        # Pass the event to the merchant system
        if hasattr(self, 'merchant_system'):
            return self.merchant_system.handle_event(event, self)
    
        return False


def main():
    """Main game loop, 3/9/25"""
    # Create the game
    game = AsteroidFrontier()
    
    # Add save system
    #game.add_save_system()
    
    # Initialize gameplay systems
    game.initialize_systems()

    # Add test key: Press Y to run game state test
    print("Press Y to run game state test")
    
    # Game loop
    running = True
    clock = pygame.time.Clock()
    while running:
        # Get delta time
        dt = clock.tick(FPS) / 1000.0
        
         # Handle events
        event_result = game.handle_events()
        if event_result is False:  # Check if event handling requests exit
            running = False
        
        # Update game state
        game.update(dt)
        
        # Draw everything
        game.draw()
        
        # Ensure the display is updated
        pygame.display.flip()
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()