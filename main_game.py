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
from map_system import Map, Camera, Level, Tile, Camera
from character_system import Character, Player as PlayerCharacter, NPC as NPCCharacter
from dialogue_quest_system import DialogueManager, QuestManager, Quest
from item_inventory import Inventory, ItemFactory
from space_travel_system import SystemMap, Location
from space_travel import SpaceTravel, AsteroidField
from camera import Camera
from save_system import SaveSystem, SaveLoadMenu
from merchant_system import MerchantSystem
from pygame.locals import * # For OpenGL constants
from OpenGL.GL import *  # This imports all OpenGL functions
from opengl_integration import (initialize_3d, toggle_3d_view, 
                             update_3d_view, draw_3d_view)
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
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF|OPENGL)
# Create a 2D surface for regular Pygame drawing
pygame_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
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

class AsteroidFrontier:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.game_state = GameState.MAIN_MENU
        self.player = PlayerCharacter("New_Droid", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)
        
        # Set a flag to track if we're using OpenGL or regular pygame
        self.using_opengl = True
        
        # Create a 2D surface for regular Pygame drawing
        self.pygame_surface = pygame.Surface((self.screen_width, self.screen_height))
        
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
        
         # Menu system
        self.active_tab = 0  # 0: Items, 1: Self, 2: Map, 3: Quests
        self.menu_open = False  # Track if the menu is open
    
        # Game state for menu
        self.game_states = GameState()  # If you're using an enum or constants class
        
        # Game flags
        self.show_inventory = False
        self.show_map = False
        self.show_quest_log = False

        # Initialize spaceship attributes
        self.space_map = None  # Will be created when needed
        self.player_ship = None
        self.camera_pos = (0, 0)
        self.near_location = None

        # Initialize resource tracking
        self.collected_resources = {}

        # Add first-person view flag and raycaster
        #self.first_person_view = False
        #self.raycaster = Raycaster(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Add first-person controls
        self.fp_forward = False
        self.fp_backward = False
        self.fp_strafe_left = False
        self.fp_strafe_right = False
        self.fp_turn_left = False
        self.fp_turn_right = False
   
    def setup_basic_opengl(self):
        """Set up basic OpenGL for 2D rendering"""
        glViewport(0, 0, self.screen_width, self.screen_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.screen_width, self.screen_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
    
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

    def initialize_systems(self):
        """Initialize all game systems, 3/11/25"""
        print("Initializing game systems...")
    
        # Initialize OpenGL engine when game starts
        initialize_3d(self)
        
        # Initialize space travel system
        if not hasattr(self, 'space_travel') or self.space_travel is None:
            from space_travel import SpaceTravel
            self.space_travel = SpaceTravel(SCREEN_WIDTH, SCREEN_HEIGHT)
        
             # Apply ship upgrades if any exist
            if hasattr(self, 'ship_upgrades'):
                # Apply cargo upgrade
                if 'cargo' in self.ship_upgrades:
                    cargo_level = self.ship_upgrades['cargo']
                    # Set cargo capacity based on level
                    cargo_capacity = 100 * (cargo_level + 1)  # Level 0 = 100, Level 1 = 200, etc.
                    self.space_travel.ship.cargo_capacity = cargo_capacity
                    print(f"Applied cargo upgrade level {cargo_level}: Capacity {cargo_capacity}")
            
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
        """Create the solar system map with locations in realistic orbital patterns, 3/16/25"""
        system_map = SystemMap(2000, 2000)
    
        # Map center point (Sun position)
        center_x, center_y = 1000, 1000
    
        # Locations with radial orbital positions
        # Format: id, name, faction, orbital_radius, angle_degrees
        locations = [
            # Inner system
            {"id": "mercury", "name": "Mercury", "faction": "earth", "radius": 150, "angle": 30},
            {"id": "venus", "name": "Venus", "faction": "earth", "radius": 250, "angle": 135},
            {"id": "earth", "name": "Earth", "faction": "earth", "radius": 350, "angle": 210},
            {"id": "luna", "name": "Luna", "faction": "earth", "radius": 380, "angle": 225},
            {"id": "mars", "name": "Mars", "faction": "mars", "radius": 450, "angle": 315},
        
            # Asteroid Belt (at various angles to show belt distribution)
            {"id": "ceres", "name": "Ceres", "faction": "earth", "radius": 650, "angle": 45},
            {"id": "vesta", "name": "Vesta", "faction": "earth", "radius": 600, "angle": 160},
            {"id": "psyche", "name": "Psyche", "faction": "mars", "radius": 680, "angle": 270},
            {"id": "pallas", "name": "Pallas", "faction": "pallas", "radius": 710, "angle": 330},
        
            # Outer system
            {"id": "jupiter", "name": "Jupiter", "faction": "independent", "radius": 850, "angle": 80},
            {"id": "saturn", "name": "Saturn", "faction": "independent", "radius": 1000, "angle": 200},
        
            # Special locations
            {"id": "rusty_rocket", "name": "Rusty Rocket", "faction": "independent", "radius": 640, "angle": 50}
        ]
    
        # Store the locations for space travel use
        self.map_locations = {}
    
        # Add locations to map
        for loc in locations:
            # Calculate cartesian coordinates from orbital parameters
            angle_rad = math.radians(loc["angle"])
            x = center_x + loc["radius"] * math.cos(angle_rad)
            y = center_y + loc["radius"] * math.sin(angle_rad)
        
            location = Location(loc["name"], f"{loc['name']} - {loc['faction']} control", 
                              f"{loc['id']}_map.csv", position=(x, y), faction=loc["faction"])
        
            system_map.add_location(loc["id"], location)
        
            # Store reference for space travel - scale up coordinates for the space mode
            self.map_locations[loc["id"]] = {
                "name": loc["name"],
                "pos": [x * 6, y * 6],  # Scale up for space travel
                "color": self.get_faction_color(loc["faction"]),
                "faction": loc["faction"],
                "radius": loc["radius"],  # Store orbital data for possible animations
                "angle": loc["angle"]
            }
    
        # Add orbital rings to the map (will need to implement in SystemMap.draw)
        system_map.orbital_rings = [150, 250, 350, 450, 650, 850, 1000]
    
        # Add connections between locations (focusing on realistic travel paths)
        # A ship would typically travel along orbital paths rather than directly
        for loc_id, connections in {
            # Inner system connections
            "earth": ["luna", "mars", "venus"],
            "luna": ["earth"],
            "mars": ["earth", "psyche", "ceres"],
        
            # Asteroid belt connections
            "ceres": ["mars", "vesta", "psyche", "rusty_rocket"],
            "psyche": ["mars", "pallas", "vesta", "ceres"],
            "vesta": ["ceres", "psyche"],
            "pallas": ["psyche"],
        
            # Special location connections
            "rusty_rocket": ["ceres"],
        
            # Outer system connections
            "jupiter": ["saturn"],
            "saturn": ["jupiter"]
        }.items():
            location = system_map.locations.get(loc_id)
            if location:
                for conn in connections:
                    dest = system_map.locations.get(conn)
                    if dest:
                        # Calculate distance based on positions
                        dx = location.position[0] - dest.position[0]
                        dy = location.position[1] - dest.position[1]
                        distance = int(math.sqrt(dx*dx + dy*dy))
                        location.add_connection(conn, distance)
    
        # Set player location - start at Earth, Luna, or Mars
        system_map.set_player_location("mars")
    
        return system_map
    
    def get_faction_color(self, faction):
        """Get color based on faction, 3/16/25"""
        if faction == "earth":
            return (0, 100, 255)  # Blue for Earth
        elif faction == "mars":
            return (255, 100, 0)  # Red-orange for Mars
        elif faction == "pallas":
            return (150, 0, 150)  # Purple for Pallas
        else:
            return (200, 200, 200)  # Default gray for neutrals

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
        """Load a specific location's map and NPCs, 3/14/25"""
        print(f"Loading location: {location_id}")
    
        try:
            # Special handling for ship cabin
            if location_id == "ship_cabin":
                # Load the ship cabin map file
                map_file = "mvp_ship_cabin.csv"
                level = Level(location_id, map_file, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
                self.current_level = level.get_data()
            else:
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
            
                # Load map using Level class
                level = Level(location_id, map_file, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
                self.current_level = level.get_data()
        
            # Place player at starting position
            if hasattr(self, 'player') and "player_start" in self.current_level:
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

            # Load NPCs from JSON
            self.npcs = self.load_npcs_from_json(location_id)
        
            # Update camera with map size
            self.camera.set_map_size(self.current_level["width"], self.current_level["height"])
        
            return True
        
        except Exception as e:
            print(f"ERROR in load_location: {e}")
            # Create emergency fallback level
            level = Level(location_id, None, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
            self.current_level = level.get_data()
            self.npcs = pygame.sprite.Group()  # Empty NPCs
            return False  # Still return False to indicate failure
    
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
            
                # Only show travel menu if E key is pressed
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    # Special handling for ship cabin
                    if self.current_level and self.current_level.get("name") == "ship_cabin":
                        print("Exit from ship cabin detected")
                        self.process_ship_cabin_exit()
                        return True
                    else:
                        # Regular travel for other locations
                        print("E key pressed, showing travel menu")
                        self.show_travel_options()
                        return True
            
                # Display hint even if E is not pressed
                return False
    
        # Not near any exit
        self.near_exit = False
        return False

    def handle_events(self):
        """Process game events, fancy map 3/16/25"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
            # First check if we're in any menu mode
            menu_open = self.show_inventory or self.show_map or self.show_quest_log
        
            if menu_open:
                # Handle menu navigation events
                if event.type == pygame.KEYDOWN:
                    # Tab key or number keys for switching tabs
                    if event.key == pygame.K_TAB:
                        self.active_tab = (self.active_tab + 1) % 4
                        # Update flags based on active tab
                        self.show_inventory = (self.active_tab in [0, 1])  # Items or Self
                        self.show_map = (self.active_tab == 2)
                        self.show_quest_log = (self.active_tab == 3)
                        return True
                    elif pygame.K_1 <= event.key <= pygame.K_4:
                        self.active_tab = event.key - pygame.K_1
                        self.show_inventory = (self.active_tab in [0, 1])
                        self.show_map = (self.active_tab == 2)
                        self.show_quest_log = (self.active_tab == 3)
                        return True
                
                    # Q to close menu
                    elif event.key == pygame.K_q:
                        self.show_inventory = False
                        self.show_map = False
                        self.show_quest_log = False
                        return True
                
                    # Map navigation with arrow keys - only when on map tab
                    elif self.show_map and self.active_tab == 2:
                        # Initialize map_offset if it doesn't exist
                        if not hasattr(self, 'map_offset'):
                            self.map_offset = [0, 0]
                    
                        # Move map with arrow keys
                        if event.key == pygame.K_LEFT:
                            self.map_offset[0] += 50  # Move map right (view left)
                            return True
                        elif event.key == pygame.K_RIGHT:
                            self.map_offset[0] -= 50  # Move map left (view right)
                            return True
                        elif event.key == pygame.K_UP:
                            self.map_offset[1] += 50  # Move map down (view up)
                            return True
                        elif event.key == pygame.K_DOWN:
                            self.map_offset[1] -= 50  # Move map up (view down)
                            return True
                        elif event.key == pygame.K_HOME:
                            # Reset map position
                            self.map_offset = [0, 0]
                            return True
        
            # Regular event handling for game when menu is not open
            if not menu_open:
                        
                # Add 3D view toggle with V key
                if event.type == pygame.KEYDOWN and event.key == pygame.K_v:
                    toggle_3d_view(self)

                # Add 3D control handling
                if self.game_state == GameState.FIRST_PERSON_3D:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_w:
                            self.fp_forward = True
                        elif event.key == pygame.K_s:
                            self.fp_backward = True
                        elif event.key == pygame.K_a:
                            self.fp_strafe_left = True
                        elif event.key == pygame.K_d:
                            self.fp_strafe_right = True
                        elif event.key == pygame.K_LEFT:
                            self.fp_turn_left = True
                        elif event.key == pygame.K_RIGHT:
                            self.fp_turn_right = True
    
                    elif event.type == pygame.KEYUP:
                        if event.key == pygame.K_w:
                            self.fp_forward = False
                        elif event.key == pygame.K_s:
                            self.fp_backward = False
                        elif event.key == pygame.K_a:
                            self.fp_strafe_left = False
                        elif event.key == pygame.K_d:
                            self.fp_strafe_right = False
                        elif event.key == pygame.K_LEFT:
                            self.fp_turn_left = False
                        elif event.key == pygame.K_RIGHT:
                            self.fp_turn_right = False
                
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
                    # Regular event handling (from your existing code)
                    if event.type == pygame.KEYDOWN:
                        # Open menu with Q key
                        if event.key == pygame.K_q and self.game_state == GameState.OVERWORLD:
                            self.show_inventory = not self.show_inventory
                            if self.show_inventory:
                                self.active_tab = 0  # Items tab
                                self.show_map = False
                                self.show_quest_log = False
                            return True
            
                    # ... your other event handling ...
            
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
        # 3D mode update call at the beginning
        if self.game_state == GameState.FIRST_PERSON_3D:
            update_3d_view(self, dt)
            return
        
        if self.game_state == GameState.OVERWORLD:
            # Update player (only if menu is not open)
            keys = pygame.key.get_pressed()
        
            # Check if any UI menu is open before processing movement input
            menu_open = self.show_inventory or self.show_map or self.show_quest_log
        
            if not menu_open:
                # Only update player position if no menu is open
                if self.current_level and "walls" in self.current_level:
                    self.player.update(keys, dt, self.current_level["walls"])
                else:
                    # Fallback if no current level or walls
                    self.player.update(keys, dt, None)
            else:
                # Handle map navigation if map tab is open and arrow keys are pressed
                if self.show_map and self.active_tab == 2:  # Map tab is active
                    # Initialize map_offset if it doesn't exist
                    if not hasattr(self, 'map_offset'):
                        self.map_offset = [0, 0]
                
                    # Move map with arrow keys
                    if keys[pygame.K_LEFT]:
                        self.map_offset[0] += 20  # Move map right (view left)
                    if keys[pygame.K_RIGHT]:
                        self.map_offset[0] -= 20  # Move map left (view right)
                    if keys[pygame.K_UP]:
                        self.map_offset[1] += 20  # Move map down (view up)
                    if keys[pygame.K_DOWN]:
                        self.map_offset[1] -= 20  # Move map up (view down)
                    if keys[pygame.K_HOME]:
                        # Reset map position
                        self.map_offset = [0, 0]
        
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
            
             # Handle weapon firing with spacebar
            if keys[pygame.K_SPACE]:
                # Check if space travel system exists
                if hasattr(self, 'space_travel') and hasattr(self.space_travel, 'fire_weapon'):
                    # Get ship position and angle
                    ship_x = self.space_travel.ship_pos[0]
                    ship_y = self.space_travel.ship_pos[1]
                    ship_angle = self.space_travel.ship_angle
                
                    # Fire weapon
                    self.space_travel.fire_weapon(ship_x, ship_y, ship_angle)
            
            # Pass the player's inventory to space travel
            if hasattr(self.player, 'inventory'):
                self.space_travel.update(keys, dt, self.player.inventory)
            else:
                self.space_travel.update(keys, dt)
        
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
        """Render the game, Overmenu 3/16/25"""
         # Always clear the screen at the beginning of each frame
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 3D mode has its own drawing path
        if self.game_state == GameState.FIRST_PERSON_3D:
            draw_3d_view(self)
        
        else:
            # For 2D mode, always start fresh with a 2D setup
            self.setup_basic_opengl()
        
            # Clear the pygame surface
            self.pygame_surface.fill(SPACE_BG)

            # Render to the pygame surface based on game state
            if self.game_state == GameState.MAIN_MENU:
                self.draw_main_menu_to_surface(self.pygame_surface)
            
            elif self.game_state in [GameState.OVERWORLD, GameState.DIALOGUE, GameState.TRAVEL_MENU, GameState.MERCHANT]:
            # Draw your overworld content to the surface
                self.draw_overworld_to_surface(self.pygame_surface)

            if self.game_state == GameState.MAIN_MENU:
                self.draw_main_menu_to_surface(self.pygame_surface)
            
            elif self.game_state == GameState.MERCHANT:
                self.draw_merchant(self.pygame_surface)
            
            elif self.game_state == GameState.SPACE_TRAVEL:
                self.space_travel.draw(self.pygame_surface)
            
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
        
                # Draw the menu if any menu view is active
                if self.show_inventory or self.show_map or self.show_quest_log:
                    self.draw_menu_screen_to_surface(self.pygame_surface)
        
                # Draw travel menu if in that state
                if self.game_state == GameState.TRAVEL_MENU:
                    self.draw_travel_menu()
                
                # Draw merchant interface
                if self.game_state == GameState.MERCHANT:
                    # Then draw the merchant interface
                    self.merchant_system.draw(screen, self)
            
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
        
            # Convert the surface to a texture and display it
            self.blit_surface_to_screen()

        # Proceed to Next Frame
        pygame.display.flip()
    
    def blit_surface_to_screen(self):
        """Simple method to draw the pygame surface as a texture"""
        data = pygame.image.tostring(self.pygame_surface, 'RGBA')
    
        # Create texture
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.screen_width, self.screen_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    
        # Draw a full-screen quad
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(self.screen_width, 0)
        glTexCoord2f(1, 1); glVertex2f(self.screen_width, self.screen_height)
        glTexCoord2f(0, 1); glVertex2f(0, self.screen_height)
        glEnd()
    
        # Clean up the texture (important!)
        glDeleteTextures(1, [texture])

    def draw_main_menu_to_surface(self, surface):
        """draw_main_menu code but drawing to the passed surface"""
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
            pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)
        
        surface.blit(title, title_rect)
        surface.blit(start, start_rect)
        surface.blit(quit_text, quit_rect)
    
    def draw_ui(self, surface=None):
        """Draw UI elements with ship-specific prompts, 3/8/25"""
        target = surface if surface is not None else screen
        font = pygame.font.Font(None, 24)
    
        # Health bar
        health_text = font.render(f"Health: {self.player.health}/{self.player.max_health}", True, WHITE)
        target.blit(health_text, (10, 10))
    
        # Credits
        money_text = font.render(f"Credits: {self.player.credits}", True, WHITE)
        target.blit(money_text, (10, 40))
    
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
        target.blit(location_text, (SCREEN_WIDTH - location_text.get_width() - 10, 10))
    
        # Repair prompt for EVA
        if hasattr(self, 'near_repair') and self.near_repair and hasattr(self, 'current_repair_point'):
            repair_type = self.current_repair_point.repair_type.title()
            repair_text = font.render(f"Press E to repair {repair_type} System", True, (0, 255, 0))
            target.blit(repair_text, (SCREEN_WIDTH//2 - repair_text.get_width()//2, SCREEN_HEIGHT - 90))
        
            hint_text = font.render("(ESC to return to ship)", True, (200, 200, 200))
            target.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, SCREEN_HEIGHT - 60))
        
        # Exit hint - only show if player is near an exit
        if self.near_exit:
            exit_text = None
            if self.current_level and self.current_level.get("name") == "ship_cabin":
                if hasattr(self, 'docked_location') and self.docked_location:
                    exit_text = font.render(f"Press E to disembark to {self.docked_location.replace('_', ' ').title()}", True, (0, 255, 0))
                else:
                    exit_text = font.render("Press E to perform EVA", True, (0, 255, 0))
            else:
                exit_text = font.render("Press E to travel to a new location", True, (0, 255, 0))
            
            if exit_text:
                target.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT - 60))
    
        # Helm interaction prompt
        if hasattr(self, 'near_helm') and self.near_helm:
            helm_text = None
            if hasattr(self, 'docked_location') and self.docked_location:
                helm_text = font.render(f"Press E to undock and launch into space", True, (0, 255, 255))
            else:
                helm_text = font.render("Press E to return to space flight", True, (0, 255, 255))
            
            if helm_text:
                target.blit(helm_text, (SCREEN_WIDTH//2 - helm_text.get_width()//2, SCREEN_HEIGHT - 90))
    
        # Controls hint
        controls = font.render("Q: Menu | E: Interact | T: Trade", True, WHITE)
        target.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, SCREEN_HEIGHT - 30))
    
    def draw_menu_screen(self, surface):
        """Draw the unified tabbed menu screen, 3/16/25"""
        # Create the main panel
        panel_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
        pygame.draw.rect(screen, (0, 0, 0), panel_rect)
        pygame.draw.rect(screen, WHITE, panel_rect, 2)
    
        # Define tabs
        tab_y = panel_rect.y + 10
        tab_height = 40
        tab_width = panel_rect.width // 4
    
        tabs = ["Items", "Self", "Map", "Quests"]
    
        # Draw tabs
        for i, tab_name in enumerate(tabs):
            tab_rect = pygame.Rect(panel_rect.x + i * tab_width, tab_y, tab_width, tab_height)
        
            # Highlight active tab
            if i == self.active_tab:
                pygame.draw.rect(screen, (70, 70, 100), tab_rect)
            else:
                pygame.draw.rect(screen, (30, 30, 50), tab_rect)
            
            pygame.draw.rect(screen, WHITE, tab_rect, 1)
        
            # Tab text
            tab_font = pygame.font.Font(None, 28)
            tab_text = tab_font.render(tab_name, True, WHITE)
            surface.blit(tab_text, (tab_rect.centerx - tab_text.get_width()//2, 
                                 tab_rect.centery - tab_text.get_height()//2))
    
        # Draw content area
        content_rect = pygame.Rect(panel_rect.x, panel_rect.y + tab_height + 20, 
                                panel_rect.width, panel_rect.height - tab_height - 40)
    
        # Draw appropriate content based on active tab
        if self.active_tab == 0:
            self.draw_items_tab(content_rect)
        elif self.active_tab == 1:
            self.draw_self_tab(content_rect)
        elif self.active_tab == 2:
            self.draw_map_tab(content_rect)
        elif self.active_tab == 3:
            self.draw_quests_tab(content_rect)
    
        # Draw navigation instructions
        nav_font = pygame.font.Font(None, 24)
        nav_text = nav_font.render("Tab/1-4: Switch Tabs | Q: Close Menu", True, (150, 150, 150))
        surface.blit(nav_text, (panel_rect.centerx - nav_text.get_width()//2, panel_rect.bottom - 30))
        
    def draw_items_tab_to_surface(self, surface, content_rect):
        """Draw the items inventory tab, 3/16/25"""
        # Existing inventory drawing code, adjusted to fit in content_rect
    
        item_font = pygame.font.Font(None, 24)
        section_font = pygame.font.Font(None, 28)
    
        # Calculate the dividing line position
        divider_y = content_rect.y + content_rect.height // 2
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, divider_y), 
                    (content_rect.right - 20, divider_y), 2)
    
        # === PLAYER INVENTORY SECTION ===
        player_section = section_font.render("Personal Items", True, (200, 200, 255))
        surface.blit(player_section, (content_rect.x + 20, content_rect.y + 50))
    
        # Show credits
        if hasattr(self.player, 'credits'):
            credits_text = item_font.render(f"Credits: {self.player.credits}", True, (255, 255, 0))
            surface.blit(credits_text, (content_rect.right - credits_text.get_width() - 20, content_rect.y + 50))
    
        # Check if player has inventory attribute
        if hasattr(self.player, 'inventory') and hasattr(self.player.inventory, 'items'):
        # Show actual inventory
            player_items = [item for item in self.player.inventory.items 
                          if not hasattr(item, 'type') or item.type != 'resource']
        
            if len(player_items) > 0:
                y_offset = content_rect.y + 80
            
                for i, item in enumerate(player_items):
                    # Skip if too many items to display
                    if i >= 8:  # Limit items per section
                        more_text = item_font.render(f"... and {len(player_items) - 8} more items", True, WHITE)
                        surface.blit(more_text, (content_rect.x + 20, y_offset))
                        break
                
                    # Get item quantity
                    quantity = getattr(item, 'quantity', 1)
                
                    # Display item with quantity if applicable
                    if quantity > 1:
                        item_text = item_font.render(f"{item.name} x{quantity}", True, WHITE)
                    else:
                        item_text = item_font.render(f"{item.name}", True, WHITE)
                
                    surface.blit(item_text, (content_rect.x + 20, y_offset))
                
                    # Add value if item has value
                    if hasattr(item, 'value') and item.value > 0:
                        value_text = item_font.render(f"{item.value} credits", True, (200, 200, 100))
                        surface.blit(value_text, (content_rect.x + 300, y_offset))
                
                    y_offset += 25
            else:
                # No items
                no_items_text = item_font.render("No personal items", True, WHITE)
                surface.blit(no_items_text, (content_rect.x + 20, content_rect.y + 80))
    
        # === SHIP CARGO SECTION ===
        cargo_section = section_font.render("Ship Cargo", True, (200, 255, 200))
        surface.blit(cargo_section, (content_rect.x + 20, divider_y + 20))
    
        # Get cargo capacity (access directly from space_travel.ship)
        cargo_capacity = 100  # Default
        if hasattr(self, 'space_travel') and hasattr(self.space_travel, 'ship'):
            cargo_capacity = getattr(self.space_travel.ship, 'cargo_capacity', 100)
    
        # Collect ship resources - make sure to get fresh data each time
        ship_resources = {}
        
        # Calculate current cargo usage
        current_cargo = 0
        if ship_resources:
            current_cargo = sum(ship_resources.values())

        # Show cargo capacity with usage
        capacity_text = item_font.render(f"Cargo: {current_cargo}/{cargo_capacity}", True, 
                                       (200, 200, 200) if current_cargo < cargo_capacity else (255, 100, 100))
        surface.blit(capacity_text, (content_rect.right - capacity_text.get_width() - 20, divider_y + 20))
    
        # Get from asteroid_field if it exists
        if hasattr(self, 'space_travel') and hasattr(self.space_travel, 'asteroid_field'):
            ship_resources = self.space_travel.asteroid_field.get_collected_resources()
    
        # Also check player inventory for resource-type items
        if hasattr(self.player, 'inventory') and hasattr(self.player.inventory, 'items'):
            resource_items = [item for item in self.player.inventory.items 
                             if hasattr(item, 'type') and item.type == 'resource']
        
            for item in resource_items:
                resource_name = item.id
                if resource_name in ship_resources:
                    ship_resources[resource_name] += item.quantity
                else:
                    ship_resources[resource_name] = item.quantity
    
        # Display ship resources
        if ship_resources:
            y_offset = divider_y + 50
        
            for i, (resource_name, amount) in enumerate(ship_resources.items()):
                # Skip if too many items to display
                if i >= 8:  # Limit items per section
                    more_text = item_font.render(f"... and {len(ship_resources) - 8} more resources", True, WHITE)
                    surface.blit(more_text, (content_rect.x + 20, y_offset))
                    break
            
                # Format resource name for display
                display_name = resource_name.replace('_', ' ').title()
            
                resource_text = item_font.render(f"{display_name}: {amount}", True, WHITE)
                surface.blit(resource_text, (content_rect.x + 20, y_offset))
            
                # Add estimated value based on merchant system if available
                if hasattr(self, 'merchant_system'):
                    base_value = self.merchant_system.get_resource_price(resource_name, 
                                                                  self.current_level.get("name", "psyche_township"))
                    total_value = base_value * amount
                    value_text = item_font.render(f"{total_value} credits", True, (200, 200, 100))
                    surface.blit(value_text, (content_rect.x + 300, y_offset))
            
                y_offset += 25
        else:
            no_cargo_text = item_font.render("Cargo hold empty", True, WHITE)
            surface.blit(no_cargo_text, (content_rect.x + 20, divider_y + 50))
    
    def draw_self_tab_to_surface(self, surface, content_rect):
        """Draw the character status tab, 3/16/25"""
        section_font = pygame.font.Font(None, 28)
        item_font = pygame.font.Font(None, 24)
    
        # Character Stats Section
        stats_y = content_rect.y
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, stats_y + 30), 
                        (content_rect.right - 20, stats_y + 30), 1)
    
        stats_text = section_font.render("Character Stats", True, (200, 200, 255))
        surface.blit(stats_text, (content_rect.x + 20, stats_y))
    
        # Display stats like health, level, experience
        stats_y += 40
        stats = [
            f"Health: {self.player.health}/{self.player.max_health}",
            f"Level: {getattr(self.player, 'level', 1)}",
            f"Credits: {self.player.credits}"
        ]
    
        # Add experience if available
        if hasattr(self.player, 'experience') and hasattr(self.player, 'experience_to_level'):
            stats.append(f"Experience: {self.player.experience}/{self.player.experience_to_level}")
    
        # Add skill points if available
        if hasattr(self.player, 'skill_points'):
            stats.append(f"Skill Points: {self.player.skill_points}")
    
        for stat in stats:
            stat_text = item_font.render(stat, True, WHITE)
            surface.blit(stat_text, (content_rect.x + 40, stats_y))
            stats_y += 25
    
        # Skills Section
        skills_y = stats_y + 20
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, skills_y), 
                        (content_rect.right - 20, skills_y), 1)
    
        skills_text = section_font.render("Skills", True, (200, 200, 255))
        surface.blit(skills_text, (content_rect.x + 20, skills_y + 10))
    
        # Display skills with levels
        skills_y += 40
        if hasattr(self.player, 'skills'):
            for skill_name, skill_level in self.player.skills.items():
                skill_text = item_font.render(f"{skill_name.capitalize()}: {skill_level}", True, WHITE)
                surface.blit(skill_text, (content_rect.x + 40, skills_y))
                skills_y += 25
    
        # Faction Relations
        faction_y = skills_y + 20
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, faction_y), 
                        (content_rect.right - 20, faction_y), 1)
    
        faction_text = section_font.render("Faction Standing", True, (200, 200, 255))
        surface.blit(faction_text, (content_rect.x + 20, faction_y + 10))
    
        # Display faction relations
        faction_y += 40
        if hasattr(self.player, 'reputation'):
            for faction_name, standing in self.player.reputation.items():
                # Color code based on standing
                if standing >= 50:
                    color = (100, 255, 100)  # Green for allies
                elif standing >= 0:
                    color = (255, 255, 100)  # Yellow for neutral
                else:
                    color = (255, 100, 100)  # Red for enemies
            
                faction_display = faction_name.replace('_', ' ').title()
                faction_text = item_font.render(f"{faction_display}: {standing}", True, color)
                surface.blit(faction_text, (content_rect.x + 40, faction_y))
                faction_y += 25
        
    def draw_map_tab_to_surface(self, surface, content_rect):
        """Draw the map tab with location information, fixed to stay within bounds"""
        section_font = pygame.font.Font(None, 28)
        item_font = pygame.font.Font(None, 24)

        # Title section
        title_y = content_rect.y
        map_title = section_font.render("System Map", True, (200, 200, 255))
        surface.blit(map_title, (content_rect.x + 20, title_y))
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, title_y + 30), 
                        (content_rect.right - 20, title_y + 30), 1)

        # Map instructions
        if self.game_state == GameState.SPACE_TRAVEL:
            instructions = "Current ship position shown in white"
        else:
            instructions = "Arrow keys: Move view | Home: Reset view"

        instr_text = item_font.render(instructions, True, WHITE)
        surface.blit(instr_text, (content_rect.x + 40, title_y + 40))

        # Create a surface for the map area with the exact dimensions needed
        map_area = pygame.Rect(content_rect.x + 20, title_y + 70, 
                             content_rect.width - 40, content_rect.height - 140)
    
        # Create a new surface to draw the map on (this is the key change)
        map_surface = pygame.Surface((map_area.width, map_area.height))
        map_surface.fill((10, 10, 30))  # Dark background for the map
        pygame.draw.rect(map_surface, (100, 100, 150), 
                       (0, 0, map_area.width, map_area.height), 1)  # Border

        # Initialize map_offset if it doesn't exist
        if not hasattr(self, 'map_offset'):
            self.map_offset = [0, 0]

        # Calculate scale and offset for drawing on our surface
        map_scale = min(map_area.width/1000, map_area.height/1000)
    
        # Draw the system map onto our surface
        # Note the offsets are relative to the surface, not the screen
        self.system_map.draw(map_surface, 
                           offset=(10 + self.map_offset[0], 
                                  10 + self.map_offset[1]), 
                           scale=map_scale)

        # If in space mode, draw player's current position on the map surface
        if self.game_state == GameState.SPACE_TRAVEL and hasattr(self, 'space_travel'):
            # Convert from space coordinates to map coordinates
            space_x = self.space_travel.ship_pos[0] / 10
            space_y = self.space_travel.ship_pos[1] / 10
        
            # Convert to surface coordinates including the map offset
            surface_x = 10 + self.map_offset[0] + space_x * map_scale
            surface_y = 10 + self.map_offset[1] + space_y * map_scale
        
            # Make sure coordinates are in view (clip to map surface)
            if (0 <= surface_x <= map_area.width and 
                0 <= surface_y <= map_area.height):
                # Draw player position on the surface
                pygame.draw.circle(map_surface, (255, 255, 255), 
                                 (int(surface_x), int(surface_y)), 5)
                pygame.draw.circle(map_surface, (255, 0, 0), 
                                 (int(surface_x), int(surface_y)), 7, 1)
            
                # Draw a label on the surface
                pos_label = item_font.render("YOUR SHIP", True, (255, 255, 255))
                label_x = max(0, min(map_area.width - pos_label.get_width(), 
                                    int(surface_x) - pos_label.get_width()//2))
                label_y = max(0, min(map_area.height - pos_label.get_height(),
                                    int(surface_y) - 25))
                map_surface.blit(pos_label, (label_x, label_y))

        # Now blit the entire map surface to the surface at the map_area position
        surface.blit(map_surface, map_area.topleft)

        # Locations list at the bottom (keep this as a reference)
        location_list_y = map_area.bottom + 10
        list_title = section_font.render("Locations:", True, (200, 200, 255))
        surface.blit(list_title, (content_rect.x + 20, location_list_y))

        # Draw visible locations in a simpler format
        visible_count = 0
        if hasattr(self, 'system_map') and hasattr(self.system_map, 'locations'):
            # Just show a few key locations at the bottom
            key_locations = ["earth", "mars", "psyche", "ceres", "pallas"]
            locations_shown = []
        
            for loc_id in key_locations:
                if loc_id in self.system_map.locations:
                    locations_shown.append(self.system_map.locations[loc_id])
        
            # Create a horizontal list of key locations
            location_y = location_list_y + 30
            location_x = content_rect.x + 40
            for location in locations_shown:
                if location_x > content_rect.right - 150:
                    # Move to next row if we run out of space
                    location_x = content_rect.x + 40
                    location_y += 40
                    if location_y > content_rect.bottom - 20:
                        break  # No more space
            
                # Draw faction-colored dot
                faction_color = self.get_faction_color(location.faction)
                pygame.draw.circle(surface, faction_color, (location_x, location_y + 8), 5)
            
                # Draw location name
                name_text = item_font.render(location.name, True, WHITE)
                surface.blit(name_text, (location_x + 10, location_y))
            
                location_x += name_text.get_width() + 40  # Space between locations
                visible_count += 1
    
    def draw_quests_tab_to_surface(self, surface, content_rect):
        """Draw the quests tab, 3/16/25"""
        section_font = pygame.font.Font(None, 28)
        item_font = pygame.font.Font(None, 24)
    
        # Title section
        title_y = content_rect.y
        quest_title = section_font.render("Quest Log", True, (200, 200, 255))
        surface.blit(quest_title, (content_rect.x + 20, title_y))
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, title_y + 30), 
                        (content_rect.right - 20, title_y + 30), 1)
    
        # Active Quests Section
        active_y = title_y + 40
        active_text = section_font.render("Active Quests", True, (255, 255, 100))
        surface.blit(active_text, (content_rect.x + 20, active_y))
    
        # Get player's active quests
        active_quests = []
        if hasattr(self.player, 'quests'):
            active_quests = [q for q in self.player.quests if not getattr(q, 'completed', False)]
    
        # Display active quests
        if active_quests:
            quest_y = active_y + 30
            for quest in active_quests:
                # Quest title
                quest_title = item_font.render(quest.title, True, (255, 255, 100))
                surface.blit(quest_title, (content_rect.x + 40, quest_y))
                quest_y += 25
            
                # Quest description
                desc_text = item_font.render(quest.description, True, WHITE)
                surface.blit(desc_text, (content_rect.x + 60, quest_y))
                quest_y += 25
            
                # Quest objectives
                for i, objective in enumerate(quest.objectives):
                    # Check if we have progress data
                    progress = ""
                    if hasattr(quest, 'objective_progress') and i < len(quest.objective_progress):
                        progress = f" ({quest.objective_progress[i]}/{quest.objective_targets[i]})"
                
                    # Color based on completion
                    obj_color = (100, 255, 100) if (hasattr(quest, 'objective_progress') and 
                                                i < len(quest.objective_progress) and 
                                                quest.objective_progress[i] >= quest.objective_targets[i]) else WHITE
                
                    obj_text = item_font.render(f"• {objective}{progress}", True, obj_color)
                    surface.blit(obj_text, (content_rect.x + 60, quest_y))
                    quest_y += 20
            
                quest_y += 15  # Space between quests
        else:
            no_quests = item_font.render("No active quests", True, WHITE)
            surface.blit(no_quests, (content_rect.x + 40, active_y + 30))
    
        # Completed Quests Section
        completed_y = active_y + 200  # Fixed position or calculate based on number of active quests
        pygame.draw.line(surface, WHITE, (content_rect.x + 20, completed_y - 10), 
                        (content_rect.right - 20, completed_y - 10), 1)
    
        completed_text = section_font.render("Completed Quests", True, (100, 255, 100))
        surface.blit(completed_text, (content_rect.x + 20, completed_y))
    
        # Get completed quests
        completed_quests = []
        if hasattr(self.player, 'quests'):
            completed_quests = [q for q in self.player.quests if getattr(q, 'completed', False)]
    
        # Display completed quests (simpler list)
        if completed_quests:
            quest_y = completed_y + 30
            for quest in completed_quests:
                quest_text = item_font.render(f"✓ {quest.title}", True, (100, 255, 100))
                surface.blit(quest_text, (content_rect.x + 40, quest_y))
                quest_y += 25
        else:
            no_completed = item_font.render("No completed quests", True, WHITE)
            surface.blit(no_completed, (content_rect.x + 40, completed_y + 30))

    def draw_travel_menu(self, surface):
        """Draw the travel menu 3/4/25"""
        # Create menu panel
        panel_rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 200)
        pygame.draw.rect(surface, (0, 0, 0), panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)

        # Draw title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Travel to...", True, (255, 255, 255))
        surface.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 20))

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
                pygame.draw.rect(surface, (50, 50, 80), option_rect)
                option_text = option_font.render(f"{i+1}. {display_name}", True, (255, 255, 0))
            else:
                option_text = option_font.render(f"{i+1}. {display_name}", True, (200, 200, 200))
        
            surface.blit(option_text, (panel_rect.x + 50, y_offset))
            y_offset += 30

        # Draw instructions
        instructions = option_font.render("Press number key to select, ESC to cancel", True, (150, 150, 150))
        surface.blit(instructions, (panel_rect.centerx - instructions.get_width()//2, panel_rect.bottom - 40))

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
        """Transition to space mode using map coordinates, 3/16/25"""
        print("Entering space travel mode")
    
        try:
            # Initialize space travel system
            print("Creating SpaceTravel instance")
            self.space_travel = SpaceTravel(SCREEN_WIDTH, SCREEN_HEIGHT)
        
            # Add locations from system map
            print("Adding locations to space travel")
            if hasattr(self, 'map_locations'):
                for loc_id, loc_data in self.map_locations.items():
                    self.space_travel.add_location(
                        loc_id,
                        loc_data["name"],
                        loc_data["pos"][0],  # Use stored x position
                        loc_data["pos"][1],  # Use stored y position
                        loc_data["color"]    # Use faction color
                    )
                    print(f"Added location {loc_id} at {loc_data['pos']}")
            else:
                # Fallback if map_locations not initialized
                for loc in self.locations_data:
                    if loc.get('id') != 'space':  # Skip the space location itself
                        self.space_travel.add_location(
                            loc.get('id'),
                            loc.get('name', 'Unknown'),
                            random.randint(-3000, 3000),  # Random x position
                            random.randint(-3000, 3000),  # Random y position
                            (200, 200, 200)  # Default color
                        )
        
            # Initialize asteroid field if not already done
            if hasattr(self.space_travel, 'asteroid_field'):
                print("Using existing asteroid field")
            else:
                print("Integrating asteroid field")
                self.space_travel.asteroid_field = AsteroidField(10000, 8000)
        
            # Preserve collected resources between space sessions
            if hasattr(self, 'collected_resources'):
                print("Restoring previously collected resources")
                self.space_travel.asteroid_field.collected_resources = self.collected_resources
        
            # Set player position (optional)
            # If docked, place near that location
            if hasattr(self, 'docked_location') and self.docked_location and hasattr(self, 'map_locations'):
                loc_data = self.map_locations.get(self.docked_location)
                if loc_data:
                    self.space_travel.ship_pos[0] = loc_data["pos"][0] + random.randint(-50, 50)
                    self.space_travel.ship_pos[1] = loc_data["pos"][1] + random.randint(-50, 50)
                    print(f"Positioned ship near {self.docked_location}")
        
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
                
    def draw_merchant(self, surface):
        """Draw the merchant interface if active"""
        if self.game_state == GameState.MERCHANT:
            # First draw the game underneath
            if self.current_level and "all_sprites" in self.current_level:
                for sprite in self.current_level["all_sprites"]:
                    cam_pos = self.camera.apply(sprite)
                    surface.blit(sprite.image, cam_pos)
            
                # Draw NPCs
                for npc in self.npcs:
                    cam_pos = self.camera.apply(npc)
                    screen.blit(npc.image, cam_pos)
            
                # Draw player
                cam_pos = self.camera.apply(self.player)
                surface.blit(self.player.image, cam_pos)
        
            # Then draw the merchant interface
            if hasattr(self, 'merchant_system'):
                self.merchant_system.draw(surface, self)
    
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

    def render_2d_surface_to_screen(self):
        """Render the pygame surface to the OpenGL screen"""
        # Make sure we have a surface to render
        if not hasattr(self, 'pygame_surface') or self.pygame_surface is None:
            return
        
        # Save the current OpenGL matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_width, self.screen_height, 0, -1, 1)
    
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
    
        # Disable 3D features
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
        # Convert surface to string data for texture
        tex_data = pygame.image.tostring(self.pygame_surface, "RGBA", 1)
    
        # Create and set up texture
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.screen_width, self.screen_height, 
                   0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
    
        # Draw full-screen quad with the texture
        glEnable(GL_TEXTURE_2D)
        glColor4f(1, 1, 1, 1)  # Full opacity white
    
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
    
        glTexCoord2f(1, 0)
        glVertex2f(self.screen_width, 0)
    
        glTexCoord2f(1, 1)
        glVertex2f(self.screen_width, self.screen_height)
    
        glTexCoord2f(0, 1)
        glVertex2f(0, self.screen_height)
        glEnd()
    
        # Clean up
        glDeleteTextures([texture])
    
        # Restore the previous matrices and states
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
    
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
        # Reset states
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def draw_overworld_to_surface(self, surface):
        """Draw the overworld to a specific surface"""
        # Fill the surface with background
        surface.fill(SPACE_BG)
    
        # Draw level with camera offset
        self.camera.update(self.player)
    
        if self.current_level and "all_sprites" in self.current_level:
            for sprite in self.current_level["all_sprites"]:
                # Calculate position with camera offset
                cam_pos = self.camera.apply(sprite)
                surface.blit(sprite.image, cam_pos)
    
        # Draw NPCs with camera offset
        for npc in self.npcs:
            cam_pos = self.camera.apply(npc)
            surface.blit(npc.image, cam_pos)
    
        # Draw player with camera offset
        cam_pos = self.camera.apply(self.player)
        surface.blit(self.player.image, cam_pos)
    
        # Draw dialogue if active
        if self.dialogue_manager.is_dialogue_active():
            self.dialogue_manager.draw(surface)  # Make sure dialogue_manager.draw accepts a surface parameter
    
        # Draw UI elements if not in dialogue
        if self.game_state != GameState.DIALOGUE:
            self.draw_ui(surface)  # Using the updated draw_ui that accepts a surface
    
        # Draw the menu if any menu view is active
        if self.show_inventory or self.show_map or self.show_quest_log:
            self.draw_menu_screen_to_surface(surface)
    
        # Draw travel menu if in that state
        if self.game_state == GameState.TRAVEL_MENU:
            self.draw_travel_menu_to_surface(surface)

    def draw_menu_screen_to_surface(self, surface):
        """Draw the unified tabbed menu screen to a surface"""
        # Create the main panel
        panel_rect = pygame.Rect(50, 50, self.screen_width - 100, self.screen_height - 100)
        pygame.draw.rect(surface, (0, 0, 0), panel_rect)
        pygame.draw.rect(surface, WHITE, panel_rect, 2)
    
        # Define tabs
        tab_y = panel_rect.y + 10
        tab_height = 40
        tab_width = panel_rect.width // 4
    
        tabs = ["Items", "Self", "Map", "Quests"]
    
        # Draw tabs
        for i, tab_name in enumerate(tabs):
            tab_rect = pygame.Rect(panel_rect.x + i * tab_width, tab_y, tab_width, tab_height)
        
            # Highlight active tab
            if i == self.active_tab:
                pygame.draw.rect(surface, (70, 70, 100), tab_rect)
            else:
                pygame.draw.rect(surface, (30, 30, 50), tab_rect)
            
            pygame.draw.rect(surface, WHITE, tab_rect, 1)
        
            # Tab text
            tab_font = pygame.font.Font(None, 28)
            tab_text = tab_font.render(tab_name, True, WHITE)
            surface.blit(tab_text, (tab_rect.centerx - tab_text.get_width()//2, 
                                 tab_rect.centery - tab_text.get_height()//2))
    
        # Draw content area
        content_rect = pygame.Rect(panel_rect.x, panel_rect.y + tab_height + 20, 
                                panel_rect.width, panel_rect.height - tab_height - 40)
    
        # Draw appropriate content based on active tab
        if self.active_tab == 0:
            self.draw_items_tab_to_surface(surface, content_rect)
        elif self.active_tab == 1:
            self.draw_self_tab_to_surface(surface, content_rect)
        elif self.active_tab == 2:
            self.draw_map_tab_to_surface(surface, content_rect)
        elif self.active_tab == 3:
            self.draw_quests_tab_to_surface(surface, content_rect)
    
        # Draw navigation instructions
        nav_font = pygame.font.Font(None, 24)
        nav_text = nav_font.render("Tab/1-4: Switch Tabs | Q: Close Menu", True, (150, 150, 150))
        surface.blit(nav_text, (panel_rect.centerx - nav_text.get_width()//2, panel_rect.bottom - 30))

    def draw_travel_menu_to_surface(self, surface):
        """Draw the travel menu to a surface"""
        # Create menu panel
        panel_rect = pygame.Rect(100, 100, self.screen_width - 200, self.screen_height - 200)
        pygame.draw.rect(surface, (0, 0, 0), panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)

        # Draw title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Travel to...", True, (255, 255, 255))
        surface.blit(title, (panel_rect.centerx - title.get_width()//2, panel_rect.y + 20))

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
                pygame.draw.rect(surface, (50, 50, 80), option_rect)
                option_text = option_font.render(f"{i+1}. {display_name}", True, (255, 255, 0))
            else:
                option_text = option_font.render(f"{i+1}. {display_name}", True, (200, 200, 200))
        
            surface.blit(option_text, (panel_rect.x + 50, y_offset))
            y_offset += 30

        # Draw instructions
        instructions = option_font.render("Press number key to select, ESC to cancel", True, (150, 150, 150))
        surface.blit(instructions, (panel_rect.centerx - instructions.get_width()//2, panel_rect.bottom - 40))





def main():
    """Main game loop, 3/9/25"""
    # Create the game
    game = AsteroidFrontier()
    
    # Initialize gameplay systems
    game.initialize_systems()
    
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