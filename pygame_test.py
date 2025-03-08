def run_diagnostic_test():
    """Standalone diagnostic function to test pygame rendering and input handling"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pygame Diagnostic Test")
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # Font
    font = pygame.font.Font(None, 36)
    
    # States
    MENU_STATE = 0
    SPACE_STATE = 1
    current_state = MENU_STATE
    
    # Menu options
    menu_options = ["Option 1", "Option 2", "Space Mode", "Exit"]
    selected_option = 0
    
    # Space objects
    ship_x, ship_y = 400, 300
    ship_speed = 5
    
    # Main loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                print(f"Key pressed: {event.key}")
                
                # Universal escape handler
                if event.key == pygame.K_ESCAPE:
                    if current_state == SPACE_STATE:
                        current_state = MENU_STATE
                    else:
                        running = False
                
                # Menu state controls
                if current_state == MENU_STATE:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(menu_options)
                    elif event.key == pygame.K_RETURN:
                        if selected_option == 0:
                            print("Option 1 selected")
                        elif selected_option == 1:
                            print("Option 2 selected")
                        elif selected_option == 2:
                            print("Entering Space Mode")
                            current_state = SPACE_STATE
                        elif selected_option == 3:
                            running = False
                
                # Check for number keys 1-4
                if current_state == MENU_STATE and (pygame.K_1 <= event.key <= pygame.K_4):
                    index = event.key - pygame.K_1
                    if index < len(menu_options):
                        print(f"Selected option {index+1}: {menu_options[index]}")
                        if index == 2:
                            current_state = SPACE_STATE
                        elif index == 3:
                            running = False
        
        # Update
        if current_state == SPACE_STATE:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                ship_x -= ship_speed
            if keys[pygame.K_RIGHT]:
                ship_x += ship_speed
            if keys[pygame.K_UP]:
                ship_y -= ship_speed
            if keys[pygame.K_DOWN]:
                ship_y += ship_speed
        
        # Render
        screen.fill(BLACK)
        
        if current_state == MENU_STATE:
            # Draw menu
            title = font.render("Pygame Diagnostic Test", True, WHITE)
            screen.blit(title, (400 - title.get_width() // 2, 50))
            
            for i, option in enumerate(menu_options):
                color = RED if i == selected_option else WHITE
                text = font.render(f"{i+1}. {option}", True, color)
                screen.blit(text, (350, 150 + i * 50))
                
            instructions = font.render("Use arrow keys and Enter or number keys", True, GREEN)
            screen.blit(instructions, (400 - instructions.get_width() // 2, 500))
            
        elif current_state == SPACE_STATE:
            # Draw space background
            for _ in range(100):
                x = random.randint(0, 800)
                y = random.randint(0, 600)
                pygame.draw.circle(screen, WHITE, (x, y), 1)
            
            # Draw ship
            pygame.draw.polygon(screen, GREEN, [
                (ship_x, ship_y - 20),
                (ship_x - 15, ship_y + 10),
                (ship_x + 15, ship_y + 10)
            ])
            
            # Draw instructions
            instruction1 = font.render("Arrow keys to move ship", True, WHITE)
            instruction2 = font.render("ESC to return to menu", True, WHITE)
            screen.blit(instruction1, (10, 10))
            screen.blit(instruction2, (10, 50))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("Diagnostic test completed")

 # Add this at the bottom of your main game file
    if __name__ == "__main__":
        run_diagnostic_test()
