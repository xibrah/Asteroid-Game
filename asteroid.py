import random
import math
import pygame

class Resource:
    """Class for resources that can be collected from asteroids"""
    def __init__(self, name, value, rarity=1.0, color=(200, 200, 200)):
        self.name = name
        self.value = value  # Base value in credits
        self.rarity = rarity  # How rare this resource is (1.0 = common, >1.0 = rarer)
        self.color = color
        
    def __str__(self):
        return self.name

class ResourceRegistry:
    """Registry of all available resources in the game"""
    def __init__(self):
        self.resources = {}
        self.initialize_resources()
    
    def initialize_resources(self):
        """Set up all basic resources"""
        # Basic metals
        self.add_resource("iron", "Iron", 10, 1.0, (120, 120, 120))
        self.add_resource("copper", "Copper", 15, 1.2, (184, 115, 51))
        self.add_resource("titanium", "Titanium", 25, 1.5, (190, 190, 195))
        
        # Precious metals
        self.add_resource("gold", "Gold", 50, 2.0, (255, 215, 0))
        self.add_resource("platinum", "Platinum", 75, 2.5, (229, 228, 226))
        
        # Rare elements
        self.add_resource("uranium", "Uranium", 100, 3.0, (0, 255, 50))
        self.add_resource("neodymium", "Neodymium", 120, 3.5, (43, 49, 135))
        
        # Exotic materials
        self.add_resource("alien_alloy", "Alien Alloy", 200, 5.0, (0, 255, 255))
        self.add_resource("dark_matter", "Dark Matter", 500, 10.0, (128, 0, 128))
    
    def add_resource(self, resource_id, name, value, rarity=1.0, color=(200, 200, 200)):
        """Add a resource to the registry"""
        self.resources[resource_id] = Resource(name, value, rarity, color)
    
    def get_resource(self, resource_id):
        """Get a resource by ID"""
        return self.resources.get(resource_id)
    
    def get_random_resource(self, min_rarity=1.0, max_rarity=10.0):
        """Get a random resource within a rarity range"""
        # Filter resources by rarity
        possible_resources = [r for r in self.resources.values() 
                             if min_rarity <= r.rarity <= max_rarity]
        
        if not possible_resources:
            # Fallback to iron if no resources match
            return self.resources.get("iron")
        
        # Weight by inverse of rarity (so common resources are more likely)
        weights = [1.0 / resource.rarity for resource in possible_resources]
        total_weight = sum(weights)
        
        # Normalize weights
        weights = [w / total_weight for w in weights]
        
        # Choose resource
        roll = random.random()
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if roll <= cumulative:
                return possible_resources[i]
        
        # Shouldn't reach here, but just in case
        return possible_resources[0]

class Asteroid:
    """Class for asteroids that can be mined for resources"""
    def __init__(self, x, y, size=None, resource_registry=None):
        # Position and movement
        self.x = x
        self.y = y
        self.size = size if size else random.randint(20, 60)
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-1, 1)
        
        # Velocity
        self.velocity_x = random.uniform(-0.5, 0.5)
        self.velocity_y = random.uniform(-0.5, 0.5)
        
        # Resources and health
        self.max_health = self.size * 2  # Bigger asteroids take more hits
        self.health = self.max_health
        
        # Determine resources based on size
        self.resource_registry = resource_registry
        self.resources = self.generate_resources()
        
        # Create the asteroid shape
        self.vertices = self.generate_shape()
        self.create_image()
        
        # Collision detection
        self.rect = pygame.Rect(x - self.size, y - self.size, self.size * 2, self.size * 2)
    
    def generate_shape(self):
        """Generate a random asteroid shape using vertices"""
        num_vertices = random.randint(6, 12)
        vertices = []
        
        for i in range(num_vertices):
            angle = math.radians(i * (360 / num_vertices))
            # Vary the distance from center to create irregular shape
            distance = random.uniform(0.8, 1.2) * self.size
            x = math.cos(angle) * distance
            y = math.sin(angle) * distance
            vertices.append((x, y))
        
        return vertices
    
    def create_image(self):
        """Create the asteroid's image surface"""
        # Create surface with transparency
        self.image = pygame.Surface((self.size * 2 + 4, self.size * 2 + 4), pygame.SRCALPHA)
        
        # Get base color from primary resource
        if self.resources and len(self.resources) > 0:
            primary_resource = max(self.resources.items(), key=lambda x: x[1])[0]
            if self.resource_registry:
                resource = self.resource_registry.get_resource(primary_resource)
                if resource:
                    base_color = resource.color
                else:
                    base_color = (100, 100, 100)  # Default gray
            else:
                base_color = (100, 100, 100)  # Default gray
        else:
            base_color = (100, 100, 100)  # Default gray
        
        # Apply some variation to the color
        r = max(0, min(255, base_color[0] + random.randint(-20, 20)))
        g = max(0, min(255, base_color[1] + random.randint(-20, 20)))
        b = max(0, min(255, base_color[2] + random.randint(-20, 20)))
        asteroid_color = (r, g, b)
        
        # Draw the asteroid shape
        center = (self.size + 2, self.size + 2)
        transformed_vertices = []
        for x, y in self.vertices:
            transformed_vertices.append((center[0] + x, center[1] + y))
        
        # Fill and outline
        pygame.draw.polygon(self.image, asteroid_color, transformed_vertices)
        pygame.draw.polygon(self.image, (50, 50, 50), transformed_vertices, 2)
        
        # Add some crater details
        num_craters = random.randint(1, 3 + self.size // 20)
        for _ in range(num_craters):
            crater_x = random.randint(center[0] - self.size + 10, center[0] + self.size - 10)
            crater_y = random.randint(center[1] - self.size + 10, center[1] + self.size - 10)
            crater_radius = random.randint(3, max(4, self.size // 8))
            
            # Slightly darker color for craters
            crater_color = (max(0, r - 30), max(0, g - 30), max(0, b - 30))
            pygame.draw.circle(self.image, crater_color, (crater_x, crater_y), crater_radius)
            pygame.draw.circle(self.image, (50, 50, 50), (crater_x, crater_y), crater_radius, 1)
    
    def generate_resources(self):
        """Generate resources contained in this asteroid"""
        resources = {}
    
        # Force some basic resources to ensure drops
        resources["iron"] = random.randint(5, 10)
        resources["copper"] = random.randint(3, 8)
    
        # Add a chance for rarer resources
        if random.random() < 0.3:  # 30% chance
            resources["gold"] = random.randint(1, 5)
    
        if random.random() < 0.2:  # 20% chance
            resources["uranium"] = random.randint(1, 3)
    
        # Debug
        print(f"Asteroid will drop: {resources}")
    
        return resources
    
    def update(self, dt):
        """Update asteroid position and rotation"""
        # Move the asteroid
        self.x += self.velocity_x * dt * 60  # Scale by delta time
        self.y += self.velocity_y * dt * 60
        
        # Update rectangle for collision detection
        self.rect.x = self.x - self.size
        self.rect.y = self.y - self.size
        
        # Rotate the asteroid
        self.rotation += self.rotation_speed * dt * 60
        if self.rotation >= 360:
            self.rotation -= 360
        if self.rotation < 0:
            self.rotation += 360
    
    def take_damage(self, damage):
        """Apply damage to the asteroid"""
        self.health -= damage
        return self.health <= 0
    
    def spawn_resource_particles(self):
        """Create resource particles when the asteroid is destroyed"""
        particles = []
        
        # Create particles for each resource
        for resource_name, amount in self.resources.items():
            resource = self.resource_registry.get_resource(resource_name)
            if not resource:
                continue
                
            # Create particles based on amount
            for _ in range(min(amount, 5)):  # Limit to 5 particles per resource type
                speed = random.uniform(0.5, 2.0)
                angle = random.uniform(0, math.pi * 2)
                
                particle = ResourceParticle(
                    self.x, self.y,
                    speed * math.cos(angle),
                    speed * math.sin(angle),
                    resource_name,
                    resource.color,
                    amount // min(amount, 5)  # Distribute amount among particles
                )
                particles.append(particle)
        
        # Debug
        print(f"Created {len(particles)} resource particles")

        return particles
    
    def draw(self, screen, camera_offset):
        """Draw the asteroid on the screen"""
        # Create a copy of the image to rotate
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_rect = rotated_image.get_rect(center=(self.x - camera_offset[0], self.y - camera_offset[1]))
        
        # Draw the rotated image
        screen.blit(rotated_image, rotated_rect)
        
        # Draw health bar for damaged asteroids (if below 90% health)
        if self.health < self.max_health * 0.9:
            health_percent = self.health / self.max_health
            bar_width = self.size * 2
            health_width = bar_width * health_percent
            
            bar_x = self.x - camera_offset[0] - bar_width // 2
            bar_y = self.y - camera_offset[1] - self.size - 10
            
            # Background bar
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, 5))
            
            # Health bar
            if health_percent > 0.6:
                color = (0, 255, 0)  # Green
            elif health_percent > 0.3:
                color = (255, 255, 0)  # Yellow
            else:
                color = (255, 0, 0)  # Red
                
            pygame.draw.rect(screen, color, (bar_x, bar_y, health_width, 5))

class ResourceParticle:
    """Class for resource particles that can be collected"""
    def __init__(self, x, y, vel_x, vel_y, resource_name, color, amount=1):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.resource_name = resource_name
        self.color = color
        self.amount = amount
        self.size = 6 + amount  # Size based on amount
        self.max_size = self.size
        self.collected = False
        self.lifespan = 600  # 10 seconds at 60fps
        self.age = 0
        
        # Create particle image
        self.create_image()
        
        # Collision rectangle
        self.rect = pygame.Rect(
            self.x - self.size // 2, 
            self.y - self.size // 2, 
            self.size, 
            self.size
        )
    
    def create_image(self):
        """Create the particle image"""
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Draw a glowing resource particle
        pygame.draw.circle(self.image, self.color, (self.size // 2, self.size // 2), self.size // 2)
        
        # Add a highlight
        highlight_color = (min(255, self.color[0] + 50), 
                          min(255, self.color[1] + 50), 
                          min(255, self.color[2] + 50))
        pygame.draw.circle(self.image, highlight_color, 
                         (self.size // 2 - 1, self.size // 2 - 1), 
                         self.size // 4)
    
    def update(self, dt):
        """Update particle position and lifespan"""
        # Move particle
        self.x += self.vel_x * dt * 60
        self.y += self.vel_y * dt * 60
        
        # Slow down over time
        self.vel_x *= 0.99
        self.vel_y *= 0.99
        
        # Update rectangle
        self.rect.x = self.x - self.size // 2
        self.rect.y = self.y - self.size // 2
        
        # Age the particle
        self.age += dt * 60
        
        # Particles slowly shrink as they age
        if self.age > self.lifespan * 0.7:  # Start shrinking after 70% of lifespan
            life_remaining = 1.0 - (self.age - (self.lifespan * 0.7)) / (self.lifespan * 0.3)
            self.size = max(1, int(self.max_size * life_remaining))
            self.create_image()  # Recreate image with new size
        
        # Return True if particle should be removed
        return self.age >= self.lifespan or self.collected
    
    def collect(self):
        """Mark the particle as collected"""
        self.collected = True
    
    def draw(self, screen, camera_offset):
        """Draw the resource particle"""
        # Add a pulsing glow effect
        pulse = abs(math.sin(self.age / 30)) * 0.3 + 0.7  # Value between 0.7 and 1.0
        
        # Scale image for pulsing effect
        scaled_size = int(self.size * pulse)
        if scaled_size < 1:
            scaled_size = 1
            
        scaled_image = pygame.transform.scale(self.image, (scaled_size, scaled_size))
        
        # Center position accounting for scaling
        center_x = self.x - camera_offset[0]
        center_y = self.y - camera_offset[1]
        pos_x = center_x - scaled_size // 2
        pos_y = center_y - scaled_size // 2
        
        # Draw particle
        screen.blit(scaled_image, (pos_x, pos_y))

class AsteroidField:
    """Manager for multiple asteroids and resource particles"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.asteroids = []
        self.resource_particles = []
        self.resource_registry = ResourceRegistry()
        
        # Track collected resources
        self.collected_resources = {}
        
        # Initialize asteroid field
        self.spawn_initial_asteroids()
    
    def spawn_initial_asteroids(self, count=15):
        """Spawn initial asteroids in the field"""
        for _ in range(count):
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            asteroid = Asteroid(x, y, None, self.resource_registry)
            self.asteroids.append(asteroid)
    
    def update(self, dt, player_x, player_y, view_width, view_height):
        """Update all asteroids and resource particles"""
        # Update asteroids
        for asteroid in self.asteroids[:]:
            asteroid.update(dt)
            
            # Remove asteroids that go too far off screen
            if (asteroid.x < -self.width/2 or asteroid.x > self.width*1.5 or
                asteroid.y < -self.height/2 or asteroid.y > self.height*1.5):
                self.asteroids.remove(asteroid)
        
        # Update resource particles
        for particle in self.resource_particles[:]:
            if particle.update(dt):
                self.resource_particles.remove(particle)
        
        if len(self.asteroids) == 0:
            print("No asteroids in field, generating some...")
            # Force spawn some asteroids near the player
            for _ in range(5):
                x = player_x + random.randint(-500, 500)
                y = player_y + random.randint(-500, 500)
                size = random.randint(30, 60)
                asteroid = Asteroid(x, y, size, self.resource_registry)
                self.asteroids.append(asteroid)
                print(f"Created asteroid at ({x}, {y}) with size {size}")
        else:
            #print(f"Asteroid count: {len(self.asteroids)}")
            # Spawn new asteroids if needed
            self.maintain_asteroid_count(player_x, player_y, view_width, view_height)
    
    def maintain_asteroid_count(self, player_x, player_y, view_width, view_height, target_count=15):
        """Ensure there are enough asteroids in the field"""
        if len(self.asteroids) < target_count:
            # Calculate spawn zones outside the visible area but not too far
            margin = 200  # How far outside the viewport to spawn
            
            # Define spawn areas (top, right, bottom, left)
            spawn_areas = [
                # Top
                (player_x - view_width/2 - margin, player_x + view_width/2 + margin,
                 player_y - view_height/2 - margin, player_y - view_height/2),
                # Right
                (player_x + view_width/2, player_x + view_width/2 + margin,
                 player_y - view_height/2 - margin, player_y + view_height/2 + margin),
                # Bottom
                (player_x - view_width/2 - margin, player_x + view_width/2 + margin,
                 player_y + view_height/2, player_y + view_height/2 + margin),
                # Left
                (player_x - view_width/2 - margin, player_x - view_width/2,
                 player_y - view_height/2 - margin, player_y + view_height/2 + margin)
            ]
            
            # Number of asteroids to spawn
            spawn_count = target_count - len(self.asteroids)
            
            for _ in range(spawn_count):
                # Choose a random spawn area
                area = random.choice(spawn_areas)
                
                # Generate position
                x = random.uniform(area[0], area[1])
                y = random.uniform(area[2], area[3])
                
                # Create asteroid that drifts toward the player (but not directly)
                asteroid = Asteroid(x, y, None, self.resource_registry)
                
                # Adjust velocity to drift toward player
                angle_to_player = math.atan2(player_y - y, player_x - x)
                randomized_angle = angle_to_player + random.uniform(-0.5, 0.5)
                speed = random.uniform(0.2, 0.7)
                
                asteroid.velocity_x = math.cos(randomized_angle) * speed
                asteroid.velocity_y = math.sin(randomized_angle) * speed
                
                self.asteroids.append(asteroid)
    
    def handle_weapon_hit(self, x, y, radius=10, damage=20):
        """Handle a weapon hitting asteroids"""
        destroyed_asteroids = []
        
        for asteroid in self.asteroids[:]:
            # Check if hit is within asteroid's radius
            dx = asteroid.x - x
            dy = asteroid.y - y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < asteroid.size + radius:
                # Apply damage based on proximity (more damage when closer to center)
                proximity_factor = 1.0 - min(1.0, distance / (asteroid.size + radius))
                hit_damage = damage * proximity_factor
                
                if asteroid.take_damage(hit_damage):
                    # Asteroid destroyed
                    destroyed_asteroids.append(asteroid)
                    
                    # Spawn resource particles
                    new_particles = asteroid.spawn_resource_particles()
                    self.resource_particles.extend(new_particles)
                    
                    # Remove from asteroid list
                    self.asteroids.remove(asteroid)
        
        return destroyed_asteroids
    
    def check_player_collision(self, player_x, player_y, player_radius):
        """Check if player collides with asteroids"""
        for asteroid in self.asteroids:
            dx = asteroid.x - player_x
            dy = asteroid.y - player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < asteroid.size + player_radius:
                return asteroid
        
        return None
    
    def collect_resources(self, player_x, player_y, collection_radius=50, player_inventory=None, cargo_capacity=100):
        """Collect resource particles near the player"""
        collected = []

        # Get current cargo usage
        current_cargo_usage = sum(self.collected_resources.values())
    
        # Calculate available space
        available_space = max(0, cargo_capacity - current_cargo_usage)
    
        if available_space <= 0:
            # Cargo full - can't collect any more
            return []

        # Debug
        particle_count_before = len(self.resource_particles)

        for particle in self.resource_particles[:]:  # Use a copy for safe modification
            if particle.collected:
                continue
                
            dx = particle.x - player_x
            dy = particle.y - player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < collection_radius:
                # Move particle toward player
                speed = 5.0
                angle = math.atan2(player_y - particle.y, player_x - particle.x)
                particle.vel_x = math.cos(angle) * speed
                particle.vel_y = math.sin(angle) * speed
                
                # Check if particle reaches player
                if distance < 15: # Smaller distance for actual collection
                    # Check if we have space for this resource
                    if particle.amount <= available_space:
                        # Mark as collected
                        particle.collected = True
                    
                        # Add to collected resources
                        if particle.resource_name in self.collected_resources:
                            self.collected_resources[particle.resource_name] += particle.amount
                        else:
                            self.collected_resources[particle.resource_name] = particle.amount
                        
                        # Update available space
                        available_space -= particle.amount

                        # Add to player inventory if provided
                        if player_inventory is not None:
                        # This would depend on your inventory implementation
                        # Code to add to inventory would go here
                            pass

                        collected.append((particle.resource_name, particle.amount))
                        print(f"Resource collected: {particle.resource_name} x{particle.amount}")
                
                        # Remove the particle
                        self.resource_particles.remove(particle)
                    else:
                        # Not enough space - don't collect
                        print(f"Cargo full - can't collect {particle.amount} units of {particle.resource_name}")
                    
                        # Optional: Display a message to the player
                        self.cargo_full_message = True
                    
                        # Don't try to collect any more resources
                        break
        return collected
    
    def draw(self, screen, camera_offset):
        """Draw all asteroids and resource particles, 3/12/25"""
        # Debug info
        #print(f"Camera offset: {camera_offset}")
    
        # Draw a reference grid at world origin
        origin_x = 0 - camera_offset[0]
        origin_y = 0 - camera_offset[1]
        pygame.draw.line(screen, (255, 0, 0), (origin_x, origin_y-100), (origin_x, origin_y+100), 3)
        pygame.draw.line(screen, (255, 0, 0), (origin_x-100, origin_y), (origin_x+100, origin_y), 3)
    
        # Draw asteroids as simple colored circles for testing
        for asteroid in self.asteroids:
            # Calculate screen position
            screen_x = int(asteroid.x - camera_offset[0])
            screen_y = int(asteroid.y - camera_offset[1])
        
            # Check if on or near screen
            if (-asteroid.size <= screen_x <= screen.get_width() + asteroid.size and
                -asteroid.size <= screen_y <= screen.get_height() + asteroid.size):
            
                # Draw bright outline for visibility
                pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), asteroid.size, 3)
            
                # Add text label for easier identification
                font = pygame.font.Font(None, 20)
                label = font.render(f"Asteroid", True, (255, 255, 0))
                screen.blit(label, (screen_x - label.get_width()//2, screen_y - label.get_height()//2))
            
                # Try to draw the actual asteroid image too
                if hasattr(asteroid, 'image'):
                    try:
                        screen.blit(asteroid.image, (screen_x - asteroid.size, screen_y - asteroid.size))
                    except Exception as e:
                        print(f"Error drawing asteroid image: {e}")
    
        # Draw resource particles
        for particle in self.resource_particles:
            # Calculate screen position
            screen_x = int(particle.x - camera_offset[0])
            screen_y = int(particle.y - camera_offset[1])
        
            # Check if on screen
            if (0 <= screen_x <= screen.get_width() and
                0 <= screen_y <= screen.get_height()):
            
                # Draw as a bright circle
                pygame.draw.circle(screen, (0, 255, 0), (screen_x, screen_y), 5)
    
    def get_collected_resources(self):
        """Get dictionary of collected resources"""
        return self.collected_resources.copy()