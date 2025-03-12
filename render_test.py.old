import pygame
import sys

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Render Test")
clock = pygame.time.Clock()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            running = False
    
    # Clear screen with blue
    screen.fill((0, 0, 100))
    
    # Draw a yellow circle
    pygame.draw.circle(screen, (255, 255, 0), (400, 300), 100)
    
    # Draw text
    font = pygame.font.Font(None, 48)
    text = font.render("RENDER TEST", True, (255, 255, 255))
    screen.blit(text, (300, 250))
    
    # Update display
    pygame.display.flip()
    
    # Cap framerate
    clock.tick(60)

pygame.quit()
sys.exit()