# Asteroid Frontier RPG
# Main Game

import pygame
import sys
import os

# Import game modules
# In a real project, these would be separate files
from game_structure import Game, GameState, Player, NPC
from map_system import Map, Camera, Level, Tile
from character_system import Character, Player as PlayerCharacter, NPC as NPCCharacter
from dialogue_quest_system import DialogueManager, QuestManager, Quest
from item_inventory import Inventory, ItemFactory
from space_travel_system import SystemMap, Location, SpaceTravel

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
        self.player = PlayerCharacter("Leo", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)
        
        # Create game systems
        self.dialogue_manager = DialogueManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.quest_manager = QuestManager()
        
        # Create solar system map
        self.system_map = self.create_system_map()
        self.space_travel = SpaceTravel(self.system_map, self.player)
        
        # Current level/map
        self.current_level = None
        
        # Create locations
        self.locations = self.create_locations()
        
        # Load initial location
        self.load_location("psyche_township")
        
        # UI elements
        self.font = pygame.font.Font(None, 24)
        
        # Game flags
        self.show_inventory = False
        self.show_map = False
        self.show_quest_log = False
    
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