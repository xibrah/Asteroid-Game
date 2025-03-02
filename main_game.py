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
        if location_id not in self.locations:
            print(f"Error: Location {location_id} not found")
            return False
        
        location_data = self.locations[location_id]
        
        # Create a basic map for now (in a real game, would load from file)
        self.current_level = self.create_test_level(location_id)
        
        # Create NPCs
        self.npcs = pygame.sprite.Group()
        for npc_data in location_data["npcs"]:
            npc = NPCCharacter(npc_data["name"], x=npc_data["x"] * TILE_SIZE, y=npc_data["y"] * TILE_SIZE, 
                               dialogue=npc_data["dialogue"])
            
            # Add quest if available
            if npc_data["quest"]:
                quest_data = npc_data["quest"]
                quest = Quest(quest_data["id"], quest_data["title"], quest_data["description"], 
                              quest_data["objectives"])
                quest.credit_reward = quest_data["reward_credits"]
                quest.xp_reward = quest_data["reward_xp"]
                npc.quest = quest
            
            self.npcs.add(npc)
        
        # Create items
        self.items = pygame.sprite.Group()
        # In a real game, you'd load items here
        
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
    
    def handle_events(self):
        """Process game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == GameState.MAIN_MENU:
                        return False
                    else:
                        self.game_state = GameState.MAIN_MENU
                
                if event.key == pygame.K_i:
                    self.show_inventory = not self.show_inventory
                
                if event.key == pygame.K_m:
                    self.show_map = not self.show_map
                
                if event.key == pygame.K_q:
                    self.show_quest_log = not self.show_quest_log
                
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
                        for npc in self.npcs:
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
            
            # Check for NPC interaction via E key
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
            self.space_travel.update(dt)
            
            if self.space_travel.travel_state == "idle":
                self.game_state = GameState.OVERWORLD
    
    def draw(self):
        """Render the game"""
        screen.fill(SPACE_BG)
        
        if self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
        
        elif self.game_state == GameState.OVERWORLD:
            # Draw level
            if self.current_level:
                self.current_level["all_sprites"].draw(screen)
            
            # Draw NPCs
            self.npcs.draw(screen)
            
            # Draw player
            screen.blit(self.player.image, self.player.rect)
            
            # Draw UI elements
            self.draw_ui()
            
            # Draw dialogue if active
            if self.dialogue_manager.is_dialogue_active():
                self.dialogue_manager.draw(screen)
            
            # Draw inventory if shown
            if self.show_inventory:
                self.draw_inventory()
            
            # Draw map if shown
            if self.show_map:
                self.draw_map()
            
            # Draw quest log if shown
            if self.show_quest_log:
                self.draw_quest_log()
        
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
            x = pygame.random.randint(0, SCREEN_WIDTH)
            y = pygame.random.randint(0, SCREEN_HEIGHT)
            size = pygame.random.randint(1, 3)
            brightness = pygame.random.randint(50, 255)
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
