import pygame
import sys
import os
import random
import math
import json

# Import game modules
from game_structure import GameState, Player
from map_system import Level, Tile, Camera
from character_system import Character, Player as PlayerCharacter, NPC as NPCCharacter
from dialogue_quest_system import DialogueManager, QuestManager, Quest
from item_inventory import Inventory, ItemFactory
from space_travel_system import SystemMap, Location
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

# Set up the display - pure Pygame, no OpenGL
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

class AsteroidFrontier:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.game_state = GameState.MAIN_MENU
        self.player = PlayerCharacter("New_Droid", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)
        
        # Set up camera
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
    
        # Game flags
        self.show_inventory = False
        self.show_map = False
        self.show_quest_log = False

        # Initialize resource tracking
        self.collected_resources = {}
    
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
            with open(os.path.join('assets', 'dialogues', 'npcs.json'), 'r') as file:
                data = json.load(file)
            
            npcs_data = data.get("npcs", [])
            location_npcs = pygame.sprite.Group()
        
            # Find NPCs for this location
            for npc_data in npcs_data:
                position = npc_data.get("position", {})
                if position.get("location") == location_id:
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
                        quest = Quest(quest_ids[0], f"{npc.name}'s Task", 
                                   "Help with an important task.", ["Complete the objective"])
                        quest.credit_reward = 100
                        quest.xp_reward = 50
                        npc.quest = quest
                
                    # Set full dialogue data for proper conversations
                    npc.full_dialogue = dialogue_data
                
                    # Add to group
                    location_npcs.add(npc)
                    print(f"Loaded NPC from JSON: {npc.name}")
        
            return location_npcs
    
        except Exception as e:
            print(f"Error loading NPCs from JSON: {e}")
            return pygame.sprite.Group()

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

    def create_system_map(self):
        """Create the solar system map with locations in realistic orbital patterns"""
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
    
        # Add orbital rings to the map
        system_map.orbital_rings = [150, 250, 350, 450, 650, 850, 1000]
    
        # Add connections between locations
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
        """Get color based on faction"""
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
        
        return locations
    
    def load_location(self, location_id):
        """Load a specific location's map and NPCs"""
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
            self.create_default_level()
            return False  # Still return False to indicate failure
    
    def create_default_level(self):
        """Create a simple default level as fallback"""
        print("Creating default level")
        
        # Create a simple level with a room
        level = Level("default", None, SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
        self.current_level = level.get_data()
        self.npcs = pygame.sprite.Group()
        
        # Place player in center
        self.player.rect.x = SCREEN_WIDTH // 2
        self.player.rect.y = SCREEN_HEIGHT // 2
        
        # Update camera
        self.camera.set_map_size(self.current_level["width"], self.current_level["height"])
    
    def check_exit_collision(self):
        """Check if player is colliding with an exit tile"""
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
            distance = math.sqrt(dx**2 + dy**2)
        
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
        """Process game events"""
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
                # Handle merchant events if in merchant mode
                if self.game_state == GameState.MERCHANT:
                    if hasattr(self, 'merchant_system') and self.merchant_system.handle_event(event, self):
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
                                else:
                                    print(f"Invalid selection index: {index}")
                        except Exception as e:
                            print(f"ERROR in travel menu handling: {e}")
                            self.game_state = GameState.OVERWORLD  # Recover gracefully
            
                    # Open menu with Q key
                    if event.key == pygame.K_q and self.game_state == GameState.OVERWORLD:
                        self.show_inventory = not self.show_inventory
                        if self.show_inventory:
                            self.active_tab = 0  # Items tab
                            self.show_map = False
                            self.show_quest_log = False
                        return True
            
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
        """Update game state"""
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