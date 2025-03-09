# Asteroid Frontier RPG
# Main Game Structure

import pygame
import sys
import os

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
SPACE_BG = (5, 5, 20)  # Deep space background color

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Asteroid Frontier")
clock = pygame.time.Clock()

# Load images
def load_image(name, colorkey=None, scale=1):
    fullname = os.path.join('assets', 'images', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print(f"Cannot load image: {name}")
        raise SystemExit(message)
    
    image = image.convert_alpha()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    if scale != 1:
        image = pygame.transform.scale(image, 
                                     (int(image.get_width() * scale), 
                                      int(image.get_height() * scale)))
    return image

# Game states
class GameState:
    MAIN_MENU = 0
    OVERWORLD = 1
    TOWN = 2
    DUNGEON = 3
    DIALOGUE = 4
    INVENTORY = 5
    GAME_OVER = 6
    SPACE_TRAVEL = 7
    TRAVEL_MENU = 8
    SAVE_MENU = 9
    LOAD_MENU = 10
    MERCHANT = 11

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Placeholder for player image - you'll need to create or find sprite assets
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(BLUE)  # Temporary blue square for the player
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 4
        self.health = 100
        self.money = 0
        
    def update(self, keys):
        # Handle player movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
            
        # Keep player on screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

class NPC(pygame.sprite.Sprite):
    def __init__(self, x, y, name, dialogue):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(RED)  # Temporary red square for NPCs
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.name = name
        self.dialogue = dialogue

class Game:
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        
        # Add some sample NPCs
        self.npcs = pygame.sprite.Group()
        npc1 = NPC(200, 200, "Stella", ["Hello, traveler!", "Welcome to Psyche Township."])
        npc2 = NPC(600, 400, "Gus", ["I'm the mayor here.", "Things have been tense since the Earth garrison arrived."])
        self.npcs.add(npc1, npc2)
        self.all_sprites.add(npc1, npc2)
        
        self.current_dialogue = None
        self.dialogue_index = 0
        
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
            
                if event.key == pygame.K_t and self.game_state == GameState.OVERWORLD:
                    # 'T' key to manually show travel menu (for testing)
                    self.show_travel_options()
            
                if self.dialogue_manager.is_dialogue_active():
                    self.dialogue_manager.handle_key(event.key)
            
                if self.game_state == GameState.TRAVEL_MENU:
                    self.handle_travel_menu_events(event)
            
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
        
            # Check for exit collision
            self.check_exit_collision()
        
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
    
        elif self.game_state == GameState.OVERWORLD or self.game_state == GameState.DIALOGUE:
            # Draw level
            if self.current_level:
                self.current_level["all_sprites"].draw(screen)
        
            # Draw NPCs
            self.npcs.draw(screen)
        
            # Draw player
            screen.blit(self.player.image, self.player.rect)
        
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
    
        elif self.game_state == GameState.SPACE_TRAVEL:
            # Draw space travel screen
            self.space_travel.draw(screen)
    
        elif self.game_state == GameState.TRAVEL_MENU:
            # Draw the background
            if self.current_level:
                self.current_level["all_sprites"].draw(screen)
            self.npcs.draw(screen)
            screen.blit(self.player.image, self.player.rect)
        
            # Draw the travel menu
            self.draw_travel_menu()
    
        pygame.display.flip()
    
    def draw_main_menu(self):
        title_font = pygame.font.Font(None, 64)
        option_font = pygame.font.Font(None, 32)
        
        title = title_font.render("Asteroid Frontier", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        
        start = option_font.render("Press ENTER to Start", True, WHITE)
        start_rect = start.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        quit_text = option_font.render("Press ESC to Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        
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
        location_name = self.current_level['name'].replace("_", " ").title()
        location_text = font.render(f"Location: {location_name}", True, WHITE)
        screen.blit(location_text, (SCREEN_WIDTH - location_text.get_width() - 10, 10))
    
        # Controls hint
        controls = font.render("I: Inventory | M: Map | Q: Quests | E: Interact | T: Travel", True, WHITE)
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, SCREEN_HEIGHT - 30))
    
        # Exit hint - only show if player is near an exit
        is_near_exit = False
        exits = [obj for obj in self.current_level["objects"] if hasattr(obj, 'is_exit')]
    
        for exit_tile in exits:
            distance = ((self.player.rect.centerx - exit_tile.rect.centerx)**2 + 
                      (self.player.rect.centery - exit_tile.rect.centery)**2)**0.5
            if distance < TILE_SIZE * 3:  # Within 3 tiles
                is_near_exit = True
                break
    
        if is_near_exit:
            exit_text = font.render("Press T to travel to a new location", True, (0, 255, 0))
            screen.blit(exit_text, (SCREEN_WIDTH//2 - exit_text.get_width()//2, SCREEN_HEIGHT - 60))
    
    def draw_dialogue(self):
        if not self.current_dialogue:
            return
            
        # Draw dialogue box
        dialogue_box = pygame.Rect(50, SCREEN_HEIGHT - 200, SCREEN_WIDTH - 100, 150)
        pygame.draw.rect(screen, BLACK, dialogue_box)
        pygame.draw.rect(screen, WHITE, dialogue_box, 2)
        
        # Draw speaker name
        name_font = pygame.font.Font(None, 28)
        name_text = name_font.render(self.dialogue_speaker, True, WHITE)
        screen.blit(name_text, (dialogue_box.x + 20, dialogue_box.y + 15))
        
        # Draw dialogue text
        if self.dialogue_index < len(self.current_dialogue):
            dialogue_font = pygame.font.Font(None, 24)
            dialogue_text = dialogue_font.render(self.current_dialogue[self.dialogue_index], True, WHITE)
            screen.blit(dialogue_text, (dialogue_box.x + 20, dialogue_box.y + 50))
            
            # Draw continue prompt
            prompt = dialogue_font.render("Press SPACE to continue", True, WHITE)
            screen.blit(prompt, (dialogue_box.right - prompt.get_width() - 20, dialogue_box.bottom - 30))

def main():
    game = Game()
    running = True
    
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
