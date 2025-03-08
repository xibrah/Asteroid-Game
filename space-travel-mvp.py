import pygame
import math
import random

# Space Travel MVP
# This is a standalone module that can be integrated into your main game

class SpaceTravel:
    def __init__(self, screen_width, screen_height):
        # Display dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Ship properties
        self.ship_pos = [screen_width // 2, screen_height // 2]  # Center of screen
        self.ship_angle = 0  # Facing up
        self.ship_velocity = [0, 0]
        self.rotation_speed = 3  # Degrees per frame
        self.thrust_power = 0.1
        self.max_speed = 5
        self.friction = 0.98  # Slows ship gradually
        
        # Background stars
        self.stars = []
        self.generate_stars(150)  # Generate 150 stars
        
        # Locations 
        self.locations = {}
        
        # Camera properties (camera is centered on ship)
        self.camera_offset = [0, 0]
        
        # Track if we're near a location
        self.near_location = None

    def generate_stars(self, count):
        """Generate random stars for the background"""
        for _ in range(count):
            # Stars are positioned in world space
            x = random.randint(-5000, 5000)
            y = random.randint(-5000, 5000)
            size = random.randint(1, 3)
            brightness = random.randint(100, 255)
            self.stars.append({
                'pos': [x, y],
                'size': size,
                'color': (brightness, brightness, brightness)
            })
    
    def add_location(self, location_id, name, x, y, color=(200, 200, 200)):
        """Add a location that can be visited"""
        self.locations[location_id] = {
            'name': name,
            'pos': [x, y],
            'color': color,
            'radius': 20  # Size of location marker
        }
    
    def update(self, keys, dt):
        """Update ship position and check for nearby locations"""
        # Handle rotation
        if keys[pygame.K_LEFT]:
            self.ship_angle = (self.ship_angle + self.rotation_speed) % 360
        if keys[pygame.K_RIGHT]:
            self.ship_angle = (self.ship_angle - self.rotation_speed) % 360
        
        # Handle thrust
        if keys[pygame.K_UP]:
            # Convert angle to radians
            angle_rad = math.radians(self.ship_angle)
            
            # Calculate thrust vector
            thrust_x = -math.sin(angle_rad) * self.thrust_power
            thrust_y = -math.cos(angle_rad) * self.thrust_power
            
            # Apply thrust to velocity
            self.ship_velocity[0] += thrust_x
            self.ship_velocity[1] += thrust_y
            
            # Limit max speed
            speed = math.sqrt(self.ship_velocity[0]**2 + self.ship_velocity[1]**2)
            if speed > self.max_speed:
                self.ship_velocity[0] = (self.ship_velocity[0] / speed) * self.max_speed
                self.ship_velocity[1] = (self.ship_velocity[1] / speed) * self.max_speed
        
        # Apply friction to gradually slow down
        self.ship_velocity[0] *= self.friction
        self.ship_velocity[1] *= self.friction
        
        # Update ship position
        self.ship_pos[0] += self.ship_velocity[0]
        self.ship_pos[1] += self.ship_velocity[1]
        
        # Update camera to follow ship
        self.camera_offset[0] = self.ship_pos[0] - self.screen_width // 2
        self.camera_offset[1] = self.ship_pos[1] - self.screen_height // 2
        
        # Check for nearby locations
        self.near_location = None
        for loc_id, location in self.locations.items():
            dx = self.ship_pos[0] - location['pos'][0]
            dy = self.ship_pos[1] - location['pos'][1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 50:  # Close enough to dock
                self.near_location = loc_id
                break
    
    def draw(self, screen):
        """Draw the space view"""
        # Fill with black
        screen.fill((0, 0, 0))
        
        # Draw stars
        for star in self.stars:
            # Convert world position to screen position
            screen_x = int(star['pos'][0] - self.camera_offset[0])
            screen_y = int(star['pos'][1] - self.camera_offset[1])
            
            # Only draw if on screen
            if (0 <= screen_x < self.screen_width and 
                0 <= screen_y < self.screen_height):
                pygame.draw.circle(screen, star['color'], (screen_x, screen_y), star['size'])
        
        # Draw locations
        for loc_id, location in self.locations.items():
            # Convert world position to screen position
            screen_x = int(location['pos'][0] - self.camera_offset[0])
            screen_y = int(location['pos'][1] - self.camera_offset[1])
            
            # Only draw if on or near screen
            if (-100 <= screen_x < self.screen_width + 100 and 
                -100 <= screen_y < self.screen_height + 100):
                # Draw location marker
                pygame.draw.circle(screen, location['color'], (screen_x, screen_y), location['radius'])
                
                # Draw location name
                font = pygame.font.Font(None, 24)
                text = font.render(location['name'], True, (255, 255, 255))
                screen.blit(text, (screen_x - text.get_width() // 2, screen_y + 30))
        
        # Draw ship at center of screen
        ship_points = [
            (self.screen_width // 2, self.screen_height // 2 - 15),  # Nose
            (self.screen_width // 2 - 10, self.screen_height // 2 + 10),  # Left wing
            (self.screen_width // 2, self.screen_height // 2 + 5),  # Back middle
            (self.screen_width // 2 + 10, self.screen_height // 2 + 10)   # Right wing
        ]
        
        # Rotate ship points
        center = (self.screen_width // 2, self.screen_height // 2)
        rotated_points = []
        for point in ship_points:
            # Translate point to origin
            x = point[0] - center[0]
            y = point[1] - center[1]
            
            # Rotate
            angle_rad = math.radians(self.ship_angle)
            rot_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
            rot_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
            
            # Translate back
            rotated_points.append((rot_x + center[0], rot_y + center[1]))
        
        # Draw ship
        pygame.draw.polygon(screen, (0, 200, 255), rotated_points)
        
        # Draw engine flame if thrusting
        if pygame.key.get_pressed()[pygame.K_UP]:
            # Calculate flame position based on ship angle
            angle_rad = math.radians(self.ship_angle)
            flame_center_x = center[0] + math.sin(angle_rad) * 5
            flame_center_y = center[1] + math.cos(angle_rad) * 5
            
            flame_points = [
                (flame_center_x, flame_center_y),
                (flame_center_x - 5 * math.cos(angle_rad) - 5 * math.sin(angle_rad), 
                flame_center_y - 5 * math.sin(angle_rad) + 5 * math.cos(angle_rad)),
                (flame_center_x + random.randint(5, 10) * math.sin(angle_rad),
                flame_center_y + random.randint(5, 10) * math.cos(angle_rad)),
                (flame_center_x - 5 * math.cos(angle_rad) + 5 * math.sin(angle_rad),
                flame_center_y - 5 * math.sin(angle_rad) - 5 * math.cos(angle_rad))
            ]
            pygame.draw.polygon(screen, (255, 165, 0), flame_points)
        
        # Draw HUD
        self.draw_hud(screen)
        
    def draw_hud(self, screen):
        """Draw heads-up display with controls and info"""
        # Draw location proximity alert
        if self.near_location:
            location = self.locations[self.near_location]
            font = pygame.font.Font(None, 32)
            text = font.render(f"Press E to dock at {location['name']}", True, (0, 255, 0))
            screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 50))
        
        # Draw controls info
        font = pygame.font.Font(None, 24)
        controls = font.render("Arrow Keys: Steer/Thrust | ESC: Exit Space", True, (200, 200, 200))
        screen.blit(controls, (20, self.screen_height - 30))
        
        # Draw speed indicator
        speed = math.sqrt(self.ship_velocity[0]**2 + self.ship_velocity[1]**2)
        speed_percent = int((speed / self.max_speed) * 100)
        speed_text = font.render(f"Speed: {speed_percent}%", True, (255, 255, 255))
        screen.blit(speed_text, (20, 20))


# Standalone test function
def test_space_travel():
    """Run the space travel system as a standalone test"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Space Travel MVP")
    clock = pygame.time.Clock()
    
    # Create space travel system
    space = SpaceTravel(800, 600)
    
    # Add some test locations
    space.add_location("station1", "Alpha Station", 500, 300, (0, 150, 255))
    space.add_location("planet1", "New Terra", -800, -600, (0, 200, 100))
    space.add_location("station2", "Mining Outpost", 1200, -400, (200, 100, 0))
    space.add_location("asteroid", "Ceres Belt", -300, 1000, (150, 150, 150))
    
    running = True
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Add dock functionality for testing
                if event.key == pygame.K_e and space.near_location:
                    print(f"Docking at {space.locations[space.near_location]['name']}")
        
        # Update
        keys = pygame.key.get_pressed()
        space.update(keys, 1/60)  # Assuming 60fps
        
        # Draw
        space.draw(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

# Run the test if this file is executed directly
if __name__ == "__main__":
    test_space_travel()
