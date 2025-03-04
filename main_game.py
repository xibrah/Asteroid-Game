# Asteroid Frontier RPG
# Main Game

import pygame
import sys
import os
import random
import json

# Import game modules
# In a real project, these would be separate files
from game_structure import Game, GameState, Player, NPC
from map_system import Map, Camera, Level, Tile
from character_system import Character, Player as PlayerCharacter, NPC as NPCCharacter
from dialogue_quest_system import DialogueManager, QuestManager, Quest
from item_inventory import Inventory, ItemFactory
from space_travel_system import SystemMap, Location, SpaceTravel
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


class AsteroidFrontier:
    def __init__(self):
        self.game_state = GameState.MAIN_MENU
        self.player = PlayerCharacter("Dex", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)
        
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
        self.space_travel = SpaceTravel(self.system_map, self.player)
        
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
        if hasattr(self, 'player') and hasattr(self.current_level, 'player_start'):
            self.player.rect.x, self.player.rect.y = self.current_level["player_start"]

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
    
                # Clear any existing NPCs
                #self.npcs = pygame.sprite.Group()
    
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
        """Check if player is colliding with an exit tile"""
        
       # Make sure we have the objects sprite group
        if "objects" not in self.current_level or not self.current_level["objects"]:
            print("No objects group in level")
            return False
        
        # Get all exit objects
        exits = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_exit')]
    
        # Debug info
        #debug:print(f"Number of exit tiles found: {len(exits)}")
        if not exits:
             print("No exit tiles in this level!")
             return False
    
        # Check each exit tile
        for i, exit_tile in enumerate(exits):
            # Calculate distance to exit
            dx = self.player.rect.centerx - exit_tile.rect.centerx
            dy = self.player.rect.centery - exit_tile.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            #debug:print(f"Exit tile {i}: Distance = {distance}, Position = ({exit_tile.rect.x}, {exit_tile.rect.y})")
        
            # If within interaction range
            if distance < TILE_SIZE * 1.5:  # More forgiving distance check
                #print(f"Player is near exit tile {i}!")
                self.near_exit = True

                # If T key is pressed, show travel menu
                keys = pygame.key.get_pressed()
                if keys[pygame.K_t]:
                    print("T key pressed, showing travel menu")
                    self.show_travel_options()
                    return True
            
                # Display hint even if T is not pressed
                #self.near_exit = True
                return False
    
        # Not near any exit
        self.near_exit = False
        return False

    def handle_events(self):
        """Process game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == GameState.MAIN_MENU:
                        return False
                    elif self.game_state == GameState.TRAVEL_MENU:
                        self.game_state = GameState.OVERWORLD
                    else:
                        self.game_state = GameState.MAIN_MENU
                
                if event.key == pygame.K_i:
                    self.show_inventory = not self.show_inventory
                
                if event.key == pygame.K_m:
                    self.show_map = not self.show_map
                
                if event.key == pygame.K_q:
                    self.show_quest_log = not self.show_quest_log
                
                if event.key == pygame.K_e:
                    for npc in self.npcs:
                        if pygame.sprite.collide_rect(self.player, npc):
                            self.dialogue_manager.start_dialogue(npc, self.player)
                            self.game_state = GameState.DIALOGUE
                            break
                
                # Handle travel menu key presses
                if self.game_state == GameState.TRAVEL_MENU:
                    # Number keys 1-9 for selecting destinations
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        if index < len(self.travel_options):
                            destination = self.travel_options[index]
                            self.travel_to_location(destination)
                    # Continue processing events even when handling travel menu

                if self.dialogue_manager.is_dialogue_active():
                    self.dialogue_manager.handle_key(event.key)

                if self.game_state == GameState.MAIN_MENU and event.key == pygame.K_RETURN:
                    self.game_state = GameState.OVERWORLD
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.dialogue_manager.is_dialogue_active():
                        self.dialogue_manager.handle_click(event.pos)
                    elif self.game_state == GameState.OVERWORLD:
                        # Check for NPC interaction if we're close enough
                        mouse_pos = pygame.mouse.get_pos()
                    
                        for npc in self.npcs:
                            # Get the NPC position with camera offset
                            npc_rect = self.camera.apply(npc)
                        
                            # Check if mouse is over the NPC
                            if npc_rect.collidepoint(mouse_pos):
                                # Also check if player is close enough
                                if pygame.sprite.collide_rect(self.player, npc):
                                    self.dialogue_manager.start_dialogue(npc, self.player)
                                    self.game_state = GameState.DIALOGUE
                                    break
        
        return True
    
    def update(self, dt):
        """Update game state"""
        if self.game_state == GameState.OVERWORLD:
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
        
        elif self.game_state == GameState.SPACE_TRAVEL:
            # Update space travel
            self.space_travel.update(dt)
            
            if self.space_travel.travel_state == "idle":
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
        """Get a list of locations the player can travel to from the current location"""
        # For debugging, always return some options
        debug_destinations = ["psyche_township", "rusty_rocket", "shipyard_station"]
    
        # Your existing implementation
        current_location_id = self.current_level['name']
    
        # Find current location in data
        current_location = None
        for loc in self.locations_data:
            if loc.get('id') == current_location_id:
                current_location = loc
                break
    
        # If not in data, use a default set
        if not current_location or 'connected_locations' not in current_location:
            # Default connections based on the Asteroid Frontier universe
            default_connections = {
                "psyche_township": ["shipyard_station", "space"],
                "shipyard_station": ["psyche_township", "space"],
                "rusty_rocket": ["ceres_port"],
                "ceres_port": ["rusty_rocket", "space"],
                "pallas_wardenhouse": ["the_core_museum", "space"],
                "the_core_museum": ["pallas_wardenhouse"]
            }
        
            return default_connections.get(current_location_id, debug_destinations)
    
        # Return connections from data
        return list(current_location.get('connected_locations', {}).keys())

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
        """Travel to a new location"""
        print(f"Traveling to {location_id}")
    
        # In a full implementation, you might show a travel animation or cutscene
        # For now, just load the new location directly
        success = self.load_location(location_id)
    
        if success:
            # Reset game state
            self.game_state = GameState.OVERWORLD
            print(f"Successfully traveled to {location_id}")
        else:
            print(f"Failed to travel to {location_id}")
            # Stay in travel menu if travel failed
        
    def draw(self):
        """Render the game"""
        screen.fill(SPACE_BG)
        
        if self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
    
        elif self.game_state in [GameState.OVERWORLD, GameState.DIALOGUE, GameState.TRAVEL_MENU]:
            # Update camera to follow player
            self.camera.update(self.player)
        
            # Draw level with camera offset
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
        """Draw the travel menu"""
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
        
            option_text = option_font.render(f"{i+1}. {display_name}", True, (200, 200, 200))
            screen.blit(option_text, (panel_rect.x + 50, y_offset))
            y_offset += 30
    
        # Draw instructions
        instructions = option_font.render("Press number to select, T to cancel", True, (150, 150, 150))
        screen.blit(instructions, (panel_rect.centerx - instructions.get_width()//2, panel_rect.bottom - 40))



def main():
    # Create the game
    game = AsteroidFrontier()
    
    # Game loop
    running = True
    while running:
        # Get delta time
        dt = clock.tick(FPS) / 1000.0
        
        # Handle events
        running = game.handle_events()
        
        # Update game state
        game.update(dt)
        
        # Draw everything
        game.draw()
    
    # Clean up
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
