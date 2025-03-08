import pygame
import sys

# Initialize pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Minimal Pygame Test")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Main game loop
running = True
while running:
    # Print a marker to show the loop is running
    print("Loop iteration")
    
    # Process events
    for event in pygame.event.get():
        print(f"Event: {event}")
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            print(f"Key pressed: {event.key}")
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Fill the screen with a color
    screen.fill(BLACK)
    
    # Draw a circle in the center
    pygame.draw.circle(screen, RED, (320, 240), 50)
    
    # Draw some text
    font = pygame.font.Font(None, 36)
    text = font.render("Press any key (ESC to quit)", True, WHITE)
    screen.blit(text, (170, 100))
    
    # Update the display
    pygame.display.flip()
    
    # Cap the frame rate
    pygame.time.delay(100)  # Add a small delay to see outputs

# Clean up
pygame.quit()
print("Program ended normally")
sys.exit()
