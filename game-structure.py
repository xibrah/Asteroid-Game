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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.MAIN_MENU:
                        return False
                    else:
                        self.state = GameState.MAIN_MENU
                        
                if self.state == GameState.DIALOGUE:
                    if event.key == pygame.K_SPACE:
                        self.dialogue_index += 1
                        if self.dialogue_index >= len(self.current_dialogue):
                            self.state = GameState.OVERWORLD
                            self.current_dialogue = None
                            self.dialogue_index = 0
                
                if event.key == pygame.K_e:
                    # Check for NPC interaction
                    for npc in self.npcs:
                        if pygame.sprite.collide_rect(self.player, npc):
                            self.state = GameState.DIALOGUE
                            self.current_dialogue = npc.dialogue
                            self.dialogue_speaker = npc.name
                            self.dialogue_index = 0
                            
                if self.state == GameState.MAIN_MENU and event.key == pygame.K_RETURN:
                    self.state = GameState.OVERWORLD
        
        return True
    
    def update(self):
        if self.state == GameState.OVERWORLD:
            keys = pygame.key.get_pressed()
            self.player.update(keys)
    
    def draw(self):
        screen.fill(SPACE_BG)
        
        if self.state == GameState.MAIN_MENU:
            self.draw_main_menu()
        elif self.state == GameState.OVERWORLD:
            self.all_sprites.draw(screen)
            self.draw_ui()
        elif self.state == GameState.DIALOGUE:
            self.all_sprites.draw(screen)
            self.draw_dialogue()
            
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
        font = pygame.font.Font(None, 24)
        health_text = font.render(f"Health: {self.player.health}", True, WHITE)
        money_text = font.render(f"Credits: {self.player.money}", True, WHITE)
        
        screen.blit(health_text, (10, 10))
        screen.blit(money_text, (10, 40))
        
        # Interaction prompt
        for npc in self.npcs:
            if pygame.sprite.collide_rect(self.player, npc):
                prompt = font.render("Press E to talk", True, WHITE)
                screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT - 50))
    
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
