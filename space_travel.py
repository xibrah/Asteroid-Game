import pygame
import math
import random

from asteroid import AsteroidField, ResourceRegistry, Asteroid, ResourceParticle

# Space Travel MVP
class SpaceTravel:
    def __init__(self, screen_width, screen_height):
        # Display dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
         # Initialize the ship
        from ship import Ship
        self.ship = Ship()  # Load default ship or specify a layout file
        
        # Ship properties
        self.ship_pos = [screen_width // 2, screen_height // 2]  # Center of screen
        self.ship_angle = 0  # Facing up
        self.ship_velocity = [0, 0]
        
        # Get movement properties from the ship
        self.rotation_speed = self.ship.rotation_speed
        self.thrust_power = self.ship.thrust_power
        self.max_speed = self.ship.max_speed
        self.friction = 0.98  # Slows ship gradually
        
        # Background stars
        self.stars = []
        self.generate_stars(1500)  # Generate 1500 stars
        
        # Locations 
        self.locations = {}
        
        # Camera properties (camera is centered on ship)
        self.camera_offset = [0, 0]
        
        # Track if we're near a location
        self.near_location = None

        # Initialize asteroid field
        self.asteroid_field = AsteroidField(10000, 8000)
        print("Asteroid field created in SpaceTravel initialization")
        
        # Weapon properties
        self.weapon_damage = 30
        self.weapon_cooldown = 250  # milliseconds
        self.last_weapon_fire = 0

    def generate_stars(self, count):
        """Generate random stars for the background"""
        self.stars = []
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
        print(f"Generated {count} stars for space background")
    
    def add_location(self, location_id, name, x, y, color=(200, 200, 200)):
        """Add a location that can be visited"""
        self.locations[location_id] = {
            'name': name,
            'pos': [x, y],
            'color': color,
            'radius': 20  # Size of location marker
        }
    
    def update(self, keys, dt, player_inventory=None):
        """Update ship position and check for nearby locations"""
        # Handle rotation
        if keys[pygame.K_LEFT]:
            self.ship_angle = (self.ship_angle - self.rotation_speed) % 360
        if keys[pygame.K_RIGHT]:
            self.ship_angle = (self.ship_angle + self.rotation_speed) % 360
        
        # Handle thrust
        if keys[pygame.K_UP]:
            # Convert angle to radians
            angle_rad = math.radians(self.ship_angle)
            
            # Calculate thrust vector
            thrust_x = math.sin(angle_rad) * self.thrust_power
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
        
        # Update asteroid field
        if hasattr(self, 'asteroid_field'):
            self.asteroid_field.update(dt, self.ship_pos[0], self.ship_pos[1], 
                                      self.screen_width, self.screen_height)
            
            # Get cargo capacity from ship
            cargo_capacity = getattr(self.ship, 'cargo_capacity', 100)

            # Collect resources that are near the ship
            collected = self.asteroid_field.collect_resources(
                self.ship_pos[0], self.ship_pos[1], 80, player_inventory, cargo_capacity
            )
    
            # Display cargo full warning if needed
            if hasattr(self.asteroid_field, 'cargo_full_message') and self.asteroid_field.cargo_full_message:
                print("Cargo hold full! Cannot collect more resources.")
                # Reset the message flag so it doesn't spam
                self.asteroid_field.cargo_full_message = False
            
            # Debug - show what was collected
            if collected:
                for resource_name, amount in collected:
                    print(f"Collected {amount} {resource_name}")

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
        """Draw the space view with improved ship rotation handling"""
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
    
        # Draw asteroid field
        if hasattr(self, 'asteroid_field'):
            self.asteroid_field.draw(screen, self.camera_offset)
                
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
    
        # Draw the ship using the tile-based rendering
        self.ship.draw(screen, self.screen_width // 2, self.screen_height // 2, self.ship_angle)
    
        # Draw engine flames if thrusting
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.draw_engine_flames(screen)
    
        # Draw HUD
        self.draw_hud(screen)

    def fire_weapon(self, x, y, angle):
        """Fire weapon in direction of ship angle"""
         # Add simple direct drawing for debugging
        angle_rad = math.radians(angle)
        laser_length = 300
        end_x = x + math.sin(angle_rad) * laser_length
        end_y = y - math.cos(angle_rad) * laser_length
    
        # Get screen positions
        screen_start_x = self.screen_width // 2
        screen_start_y = self.screen_height // 2
        screen_end_x = int(screen_start_x + math.sin(angle_rad) * laser_length)
        screen_end_y = int(screen_start_y - math.cos(angle_rad) * laser_length)
    
        # Direct screen drawing for immediate feedback
        pygame.draw.line(
            pygame.display.get_surface(),
            (255, 0, 0),  # Bright red
            (screen_start_x, screen_start_y),
            (screen_end_x, screen_end_y),
            5  # Thick line
        )
        pygame.display.update()  # Force update
        pygame.time.delay(50)  # Make it visible
    
        # Rest of the method...
        
        # Check cooldown
        current_time = pygame.time.get_ticks()
        if current_time - self.last_weapon_fire < self.weapon_cooldown:
            # Weapon still on cooldown
            return None
        
        # Update last fire time
        self.last_weapon_fire = current_time

        # Check for asteroid hits
        destroyed_asteroids = []
        if hasattr(self, 'asteroid_field'):
            destroyed_asteroids = self.asteroid_field.handle_weapon_hit(end_x, end_y, 15, self.weapon_damage)
            if destroyed_asteroids:
                print(f"Hit {len(destroyed_asteroids)} asteroids!")
        else:
            print("No asteroid field available")
        
        return destroyed_asteroids

    def draw_engine_flames(self, screen):
        """Draw engine flames from the thruster tiles with corrected direction"""
        # Get thruster positions from the ship
        thrust_points = self.ship.get_thrust_points()
    
        # Calculate the position where flames should appear based on ship rotation
        angle_rad = math.radians(self.ship_angle)
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
    
        for base_x, base_y in thrust_points:
            # Rotate the thruster position around the ship center
            # First translate to origin
            rel_x = base_x - self.ship.width * self.ship.tile_size / 2
            rel_y = base_y - self.ship.height * self.ship.tile_size / 2
        
            # Then rotate
            rot_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
            rot_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)
        
            # Translate back to screen position
            flame_base_x = center_x + rot_x
            flame_base_y = center_y + rot_y
        
            # Determine the flame direction based on thruster position relative to center
            # First find what direction this thruster is pointing in the original ship layout
            # Assuming thrusters at the bottom should point down, top point up, etc.
        
            # Find the direction from center to thruster in the original layout
            ship_center_x = self.ship.width * self.ship.tile_size / 2
            ship_center_y = self.ship.height * self.ship.tile_size / 2
            dir_x = base_x - ship_center_x
            dir_y = base_y - ship_center_y
        
            # Normalize the direction
            length = math.sqrt(dir_x**2 + dir_y**2)
            if length > 0:
                dir_x /= length
                dir_y /= length
        
            # Rotate this direction vector by the ship angle
            rot_dir_x = dir_x * math.cos(angle_rad) - dir_y * math.sin(angle_rad)
            rot_dir_y = dir_x * math.sin(angle_rad) + dir_y * math.cos(angle_rad)
        
            # Flame points outward from the thruster in this direction
            flame_length = random.randint(10, 15)
            flame_width = 5
        
            # Create flame points
            flame_points = [
                (flame_base_x, flame_base_y),  # Base of flame
                (flame_base_x + flame_width * rot_dir_y, flame_base_y - flame_width * rot_dir_x),  # Side 1
                (flame_base_x + flame_length * rot_dir_x, flame_base_y + flame_length * rot_dir_y),  # Tip
                (flame_base_x - flame_width * rot_dir_y, flame_base_y + flame_width * rot_dir_x)   # Side 2
            ]
            pygame.draw.polygon(screen, (255, 165, 0), flame_points)
        
            # Inner flame (slightly smaller)
            inner_length = flame_length - 5
            inner_width = flame_width * 0.6
            inner_flame_points = [
                (flame_base_x, flame_base_y),  # Base of inner flame
                (flame_base_x + inner_width * rot_dir_y, flame_base_y - inner_width * rot_dir_x),  # Side 1
                (flame_base_x + inner_length * rot_dir_x, flame_base_y + inner_length * rot_dir_y),  # Tip
                (flame_base_x - inner_width * rot_dir_y, flame_base_y + inner_width * rot_dir_x)   # Side 2
            ]
            pygame.draw.polygon(screen, (255, 255, 0), inner_flame_points)
        
    def draw_hud(self, screen):
        """Draw heads-up display with ship stats and controls"""
        # Draw location proximity alert
        if self.near_location:
            location = self.locations[self.near_location]
            font = pygame.font.Font(None, 32)
            text = font.render(f"Press E to dock at {location['name']}", True, (0, 255, 0))
            screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 50))
   
        # Draw controls info
        font = pygame.font.Font(None, 24)
        controls = font.render("Arrow Keys: Steer/Thrust | SPACE: Fire | ESC: Exit Space", True, (200, 200, 200))
        screen.blit(controls, (20, self.screen_height - 30))
    
        # Draw speed indicator
        speed = math.sqrt(self.ship_velocity[0]**2 + self.ship_velocity[1]**2)
        speed_percent = int((speed / self.max_speed) * 100)
        speed_text = font.render(f"Speed: {speed_percent}%", True, (255, 255, 255))
        screen.blit(speed_text, (20, 20))
    
        # Draw ship stats
        if self.ship.shield_strength > 0:
            shield_text = font.render(f"Shield: {int(self.ship.shield_strength)}", True, (100, 255, 255))
            screen.blit(shield_text, (20, 50))
    
        hull_text = font.render(f"Hull: {self.ship.hull_strength}", True, (150, 150, 255))
        screen.blit(hull_text, (20, 80))
        
        # Draw weapon info
        weapon_text = font.render(f"Weapon: Ready", True, (255, 100, 100))
        if pygame.time.get_ticks() - self.last_weapon_fire < self.weapon_cooldown:
            weapon_text = font.render(f"Weapon: Charging", True, (200, 200, 100))
        screen.blit(weapon_text, (20, 110))
        
        # Draw resource info if we have any
        if hasattr(self, 'asteroid_field'):
            resources = self.asteroid_field.get_collected_resources()
            if resources:
                resource_y = 140
                for resource_name, amount in resources.items():
                    resource_text = font.render(f"{resource_name}: {amount}", True, (100, 255, 100))
                    screen.blit(resource_text, (20, resource_y))
                    resource_y += 25
         # Draw cargo usage if we have an asteroid field
        if hasattr(self, 'asteroid_field'):
            # Calculate current usage
            cargo_usage = sum(self.asteroid_field.collected_resources.values())
            cargo_capacity = getattr(self.ship, 'cargo_capacity', 100)
        
            # Determine color based on fullness
            if cargo_usage >= cargo_capacity:
                cargo_color = (255, 0, 0)  # Red when full
            elif cargo_usage >= cargo_capacity * 0.8:
                cargo_color = (255, 255, 0)  # Yellow when getting full
            else:
                cargo_color = (0, 255, 0)  # Green when plenty of space
        
            # Draw cargo text
            cargo_text = font.render(f"Cargo: {cargo_usage}/{cargo_capacity}", True, cargo_color)
            screen.blit(cargo_text, (20, 140))
        
            # If cargo is full, show warning
            if cargo_usage >= cargo_capacity:
                warning_text = font.render("CARGO HOLD FULL!", True, (255, 0, 0))
                screen.blit(warning_text, (self.screen_width // 2 - warning_text.get_width() // 2, 200))
