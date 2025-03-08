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

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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
os.makedirs('save', exist_ok=True)

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

        # Current level/map
        self.current_level = None
        
        # Create locations
        self.locations = self.create_locations()
        
        # Load initial location
        self.load_location("psyche_township")
        self.near_exit = False  # Track if player is near an exit
        
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
        """Load a map from a text file"""
        # At the beginning of the function
        print(f"Attempting to load map file: {map_file}")
        try:
            # Determine path for the map file
            map_path = os.path.join('assets', 'maps', map_file)
            print(f"Looking for map at: {map_path}")
        
            # Check if file exists
            if not os.path.exists(map_path):
                print(f"Map file not found: {map_path}")
                print(f"Falling back to test level")
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
                            exit_tile.image.fill((0, 255, 0))  # Bright green for visibility, was:(tile_colors['E'])
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
            level["width"] = map_width
            level["height"] = map_height
        
            # Update camera with map size
            self.camera.set_map_size(map_width, map_height)
        
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
        """Load a specific location's map and NPCs"""
        print(f"Loading location: {location_id}")
    
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
    
        # Place player at starting position
        # Use multiple safety checks to ensure we don't crash or get stuck 3/4/25
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
            # Your existing code for loading NPCs from map positions...
            # Create NPCs
            if "npc_positions" in self.current_level:
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
                    # Add more for other locations
                }
    
                # Create NPCs based on the map positions
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

        self.items = pygame.sprite.Group()
    
        return True
    
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
        """Check if player is colliding with an exit tile 3/4/25"""
        # Make sure we have the objects sprite group
        if "objects" not in self.current_level or not self.current_level["objects"]:
            print("No objects group in level")
            return False
    
        # Get all exit objects
        exits = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_exit')]
    
        if not exits:
            # Only print this in debug mode to avoid console spam
            # print("No exit tiles in this level!")
            self.near_exit = False
            return False
    
        # Check each exit tile
        for exit_tile in exits:
            # Calculate distance to exit
            dx = self.player.rect.centerx - exit_tile.rect.centerx
            dy = self.player.rect.centery - exit_tile.rect.centery
            distance = (dx**2 + dy**2)**0.5
        
            # If within interaction range
            if distance < TILE_SIZE * 1.5:  # More forgiving distance check
                self.near_exit = True
            
                # Only show travel menu if T key is pressed
                keys = pygame.key.get_pressed()
                if keys[pygame.K_t]:
                    # Important: only handle the key press in one place!
                    # Either here OR in the key event handler, not both
                    print("T key pressed, showing travel menu")
                    self.show_travel_options()
                    return True
            
                # Display hint even if T is not pressed
                return False
    
        # Not near any exit
        self.near_exit = False
        return False

    def handle_events(self):
        """Process game events, space mvp 3/7/25"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
            if event.type == pygame.KEYDOWN:
                 
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
        """Update game state 3/4/25"""
        """Update game state space mvp 3/7/25"""
        if self.game_state == GameState.SPACE_TRAVEL:
            # Update space travel
            keys = pygame.key.get_pressed()
            self.space_travel.update(keys, dt)
        
            # Check if player is trying to dock
            if keys[pygame.K_e] and self.space_travel.near_location:
                location_id = self.space_travel.near_location
                self.dock_at_location(location_id)
    
        elif self.game_state == GameState.OVERWORLD:
            # Update player
            keys = pygame.key.get_pressed()
            self.player.update(keys, dt, self.current_level["walls"] if self.current_level else None)
            
            # Update NPCs
            self.npcs.update(dt, self.player)

            # Check for exit collision
            self.check_exit_collision()

            # Handle T key only if near exit
            if self.near_exit and keys[pygame.K_t]:
                    self.show_travel_options()
            
            # Check for NPC interaction via E key
            if keys[pygame.K_e]:
                for npc in self.npcs:
                    if pygame.sprite.collide_rect(self.player, npc):
                        self.dialogue_manager.start_dialogue(npc, self.player)
                        self.game_state = GameState.DIALOGUE
                        break
        
        elif self.game_state == GameState.DIALOGUE:
            # Even in dialogue mode, we should continue to update the background elements
            # This ensures the game doesn't freeze
            self.npcs.update(dt, None)  # Update NPCs but don't pass player to avoid interactions
     
            # Check if dialogue has ended
            if not self.dialogue_manager.is_dialogue_active():
                self.game_state = GameState.OVERWORLD

            elif self.game_state == GameState.TRAVEL_MENU:
            # You can add travel menu updates here if needed
            # This could include animating options, updating highlights, etc.
                pass

    def show_travel_options(self):
        """Show available travel destinations"""
        self.game_state = GameState.TRAVEL_MENU
        self.travel_options = self.get_available_destinations()
        print(f"Travel options: {self.travel_options}")  # Debug

    def get_available_destinations(self):
        """Get a list of locations the player can travel to from the current location 3/4/25"""
        valid_destinations = []
    
        # Get current location ID
        current_location_id = self.current_level['name'] if self.current_level else None
        if not current_location_id:
            print("Warning: No current location found")
            return valid_destinations
    
        print(f"Finding destinations from: {current_location_id}")
    
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
                    
                        if os.path.exists(map_path):
                            valid_destinations.append(connected_id)
                            print(f"Valid destination found: {connected_id} (map: {map_file})")
                        else:
                            print(f"Warning: Map file not found for {connected_id}: {map_path}")
        else:
            # Use hardcoded connections if not found in data
            default_connections = {
                "psyche_township": ["shipyard_station"],
                "shipyard_station": ["psyche_township", "space"],
                "rusty_rocket": ["ceres_port"],
                "ceres_port": ["rusty_rocket", "space"],
                "pallas_wardenhouse": ["the_core_museum", "space"],
                "the_core_museum": ["pallas_wardenhouse"]
            }
        
            # Check the default connections (only add ones that exist)
            if current_location_id in default_connections:
                for dest_id in default_connections[current_location_id]:
                    # Verify map file exists
                    map_file = f"{dest_id}.csv"
                    map_path = os.path.join('assets', 'maps', map_file)
                
                    if os.path.exists(map_path):
                        valid_destinations.append(dest_id)
                        print(f"Valid default destination: {dest_id}")
    
        # If no valid destinations found, provide a safe default to avoid getting stuck
        if not valid_destinations and current_location_id != "psyche_township":
            # Always allow returning to psyche_township as a failsafe
            valid_destinations.append("psyche_township")
            print("No valid destinations found - adding psyche_township as failsafe")

        # Almost all locations should be able to access space
        if "space" not in valid_destinations:
            valid_destinations.append("space")
    
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
        """Travel to a new location, 3/7/25"""
        print(f"Attempting to travel to {location_id}")
    
        try:
            # Special handling for space
            if location_id == "space":
                print("Destination is space, calling enter_space()")
                success = self.enter_space()
                return success
        
            # Verify this is a valid destination
            available_destinations = self.get_available_destinations()
            if location_id not in available_destinations:
                print(f"Error: {location_id} is not a valid destination")
                return False
        
            # In a full implementation, you might show a travel animation or cutscene
            # For now, just load the new location directly
            success = self.load_location(location_id)
        
            if success:
                # Reset game state explicitly
                self.game_state = GameState.OVERWORLD
                print(f"Successfully traveled to {location_id}")
                return True
            else:
                print(f"Failed to travel to {location_id}")
                # Stay in overworld if travel failed
                return False
            
        except Exception as e:
            print(f"ERROR in travel_to_location: {e}")
            # Recover gracefully
            self.game_state = GameState.OVERWORLD
            return False
        
    def draw(self):
        """Render the game, space mvp 3/7/25"""
        screen.fill(SPACE_BG)

        if self.game_state == GameState.SPACE_TRAVEL:
            # Draw space travel
            self.space_travel.draw(screen)
        
        elif self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
    
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
    
        elif self.game_state == GameState.SPACE_TRAVEL:
            # Add this debug print
            print("Drawing space travel from main draw method")
            # Draw space travel screen
            self.space_travel.draw(screen)
    
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
        """Draw UI elements"""
        font = pygame.font.Font(None, 24)
        
        # Health bar
        health_text = font.render(f"Health: {self.player.health}/{self.player.max_health}", True, WHITE)
        screen.blit(health_text, (10, 10))
        
        # Credits
        money_text = font.render(f"Credits: {self.player.credits}", True, WHITE)
        screen.blit(money_text, (10, 40))
        
        # Current location
        location_text = font.render(f"Location: {self.current_level['name'] if self.current_level else 'Unknown'}", True, WHITE)
        screen.blit(location_text, (SCREEN_WIDTH - location_text.get_width() - 10, 10))
        
        # Exit hint - only show if player is near an exit
        if self.near_exit:
            exit_text = font.render("Press T to travel to a new location", True, (0, 255, 0))
            screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT - 60))
    
        
        # Controls hint
        controls = font.render("I: Inventory | M: Map | Q: Quests | E: Interact", True, WHITE)
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
        """Update space travel game state 3/4/25"""
        if self.game_state != GameState.SPACE_TRAVEL:
            return

        # Debug
        print("Updating space travel...")
    
        # Update player ship
        keys = pygame.key.get_pressed()
        self.player_ship.update(keys, dt)
    
        # Check for docking with locations
        for loc_id, location in self.space_map.locations.items():
            # Calculate distance between ship and location
            dx = self.player_ship.x - location['position'][0]
            dy = self.player_ship.y - location['position'][1]
            distance = math.sqrt(dx*dx + dy*dy)
        
            # If close enough, show docking prompt
            if distance < 30:
                self.near_location = loc_id
            
                # If E key pressed, dock at location
                if keys[pygame.K_e]:
                    self.dock_at_location(loc_id)
                    return
        
        # Not near any location
        self.near_location = None
    
        # Handle returning to system map view
        if keys[pygame.K_m]:
            self.show_map = True
    
        # Update camera to follow player ship
        self.camera_pos = (
            int(self.player_ship.x - SCREEN_WIDTH // 2),
            int(self.player_ship.y - SCREEN_HEIGHT // 2)
    )

    def dock_at_location(self, location_id):
        """Dock the ship at a location and transition to that level 3/4/25"""
        print(f"Docking at {location_id}")
    
        # Ensure this is a valid location
        if location_id not in self.space_map.locations:
            print(f"Error: Invalid location ID {location_id}")
            return
    
        # Load the location
        success = self.load_location(location_id)
    
        if success:
            # Reset game state
            self.game_state = GameState.OVERWORLD
            print(f"Successfully docked at {location_id}")
        else:
            print(f"Failed to dock at {location_id}")

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

    def dock_at_location(self, location_id):
        """Dock at a location from space mode"""
        print(f"Docking at {location_id}")
    
        # Exit space mode
        self.in_space_mode = False
    
        # Load the selected location
        success = self.load_location(location_id)
    
        if success:
            # Change game state
            self.game_state = GameState.OVERWORLD
            print(f"Successfully docked at {location_id}")
            return True
        else:
            print(f"Failed to dock at {location_id}")
            # Stay in space mode if loading failed
            self.game_state = GameState.SPACE_TRAVEL
            return False

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

def main():
    """Main game loop, 3/7/25"""
    # Create the game
    game = AsteroidFrontier()
    
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