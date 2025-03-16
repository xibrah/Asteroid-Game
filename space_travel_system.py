# Asteroid Frontier RPG
# Space Travel System

import pygame
import math
import random

class Location:
    def __init__(self, name, description, map_file, position=(0, 0), faction=None):
        self.name = name
        self.description = description
        self.map_file = map_file
        self.position = position  # (x, y) coordinates in the system map
        self.faction = faction  # Controlling faction, if any
        self.travel_cost = 0  # Base cost to travel here
        self.danger_level = 0  # 0-10, affects chance of random encounters
        self.available_quests = []
        self.available_services = []  # "shop", "repair", "fuel", etc.
        self.connected_locations = {}  # {location_id: distance}
    
    def add_connection(self, location_id, distance):
        """Add a connected location that can be traveled to directly"""
        self.connected_locations[location_id] = distance


class SystemMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.locations = {}  # {location_id: Location}
        self.background = None
        self.player_location = None
        self.font = pygame.font.Font(None, 24)
    
    def add_location(self, location_id, location):
        """Add a location to the system map"""
        self.locations[location_id] = location
    
    def set_player_location(self, location_id):
        """Set the player's current location"""
        if location_id in self.locations:
            self.player_location = location_id
            return True
        return False
    
    def get_travel_options(self):
        """Get locations the player can travel to from current location"""
        if not self.player_location or self.player_location not in self.locations:
            return {}
        
        current_location = self.locations[self.player_location]
        options = {}
        
        for connected_id, distance in current_location.connected_locations.items():
            if connected_id in self.locations:
                options[connected_id] = {
                    "location": self.locations[connected_id],
                    "distance": distance,
                    "cost": self._calculate_travel_cost(distance, self.locations[connected_id])
                }
        
        return options
    
    def travel_to(self, location_id):
        """Travel to a new location if it's connected to current location"""
        if not self.player_location:
            # First-time initialization
            return self.set_player_location(location_id)
        
        travel_options = self.get_travel_options()
        if location_id in travel_options:
            self.player_location = location_id
            return True
        
        return False
    
    def _calculate_travel_cost(self, distance, destination):
        """Calculate the cost to travel to a destination"""
        base_cost = distance * 10  # 10 credits per distance unit
        return base_cost + destination.travel_cost
    
    def draw(self, screen, offset=(0, 0), scale=1.0):
        """Draw the system map on the screen, 3/16/25"""
        # Draw background if available
        if self.background:
            scaled_bg = pygame.transform.scale(self.background, 
                                              (int(self.width * scale), int(self.height * scale)))
            screen.blit(scaled_bg, offset)
        else:
            # Create a space background
            bg_rect = pygame.Rect(offset[0], offset[1], self.width * scale, self.height * scale)
            pygame.draw.rect(screen, (5, 5, 20), bg_rect)
    
        # Draw orbital rings if defined
        center_x = offset[0] + (self.width/2) * scale
        center_y = offset[1] + (self.height/2) * scale
    
        if hasattr(self, 'orbital_rings'):
            for radius in self.orbital_rings:
                # Draw as a dotted circle
                scaled_radius = radius * scale
                points = 72  # number of points to approximate the circle
                for i in range(points):
                    if i % 3 == 0:  # Skip every third point for dotted effect
                        continue
                    angle = 2 * math.pi * i / points
                    x1 = center_x + scaled_radius * math.cos(angle)
                    y1 = center_y + scaled_radius * math.sin(angle)
                
                    # Draw a small point or line segment
                    pygame.draw.circle(screen, (50, 50, 80), (int(x1), int(y1)), 1)
    
        # Draw the sun at the center
        pygame.draw.circle(screen, (255, 255, 100), (int(center_x), int(center_y)), int(15 * scale))
        pygame.draw.circle(screen, (255, 200, 0), (int(center_x), int(center_y)), int(10 * scale))
    
        # Draw connections between locations
        for loc_id, location in self.locations.items():
            loc_pos = (offset[0] + location.position[0] * scale, 
                     offset[1] + location.position[1] * scale)
        
            for connected_id in location.connected_locations:
                if connected_id in self.locations:
                    connected_loc = self.locations[connected_id]
                    connected_pos = (offset[0] + connected_loc.position[0] * scale,
                                   offset[1] + connected_loc.position[1] * scale)
                
                    # Draw line between locations
                    pygame.draw.line(screen, (40, 40, 70), loc_pos, connected_pos, 1)
    
        # Draw locations
        for loc_id, location in self.locations.items():
            loc_pos = (offset[0] + location.position[0] * scale, 
                     offset[1] + location.position[1] * scale)
        
            # Determine location color based on faction
            color = (200, 200, 200)  # Default gray
            if location.faction == "earth":
                color = (0, 100, 255)  # Blue for Earth
            elif location.faction == "mars":
                color = (255, 100, 0)  # Red-orange for Mars
            elif location.faction == "pallas":
                color = (150, 0, 150)  # Purple for Pallas
        
            # Draw location circle - highlight current location
            radius = 8 if loc_id == self.player_location else 5
            pygame.draw.circle(screen, color, loc_pos, int(radius * scale))
        
            # Add a pulsing highlight for the current location
            if loc_id == self.player_location:
                pulse = (pygame.time.get_ticks() % 1000) / 1000.0
                pulse_radius = (8 + 4 * pulse) * scale
                pygame.draw.circle(screen, color, loc_pos, int(pulse_radius), 1)
        
            # Draw location name with shadow for better visibility
            name_text = self.font.render(location.name, True, (255, 255, 255))
            shadow_text = self.font.render(location.name, True, (0, 0, 0))
        
            # Offset based on map section to prevent overlap
            name_offset_y = 10
            if location.position[1] > self.height/2:
                name_offset_y = -25  # Above the circle if in lower half
            
            screen.blit(shadow_text, (loc_pos[0] - name_text.get_width() // 2 + 1, 
                                    loc_pos[1] + name_offset_y + 1))
            screen.blit(name_text, (loc_pos[0] - name_text.get_width() // 2, 
                                  loc_pos[1] + name_offset_y))


class SpaceTravel:
    def __init__(self, system_map, player):
        self.system_map = system_map
        self.player = player
        self.travel_state = "idle"  # "idle", "traveling", "encounter"
        self.travel_progress = 0.0  # 0.0 to 1.0
        self.travel_speed = 0.05  # Progress increment per update
        self.destination = None
        self.origin = None
        self.travel_events = []
        
        # For visual effect during travel
        self.stars = []
        for _ in range(100):
            self.stars.append([
                random.randint(0, 800),  # x
                random.randint(0, 600),  # y
                random.random() + 0.5    # speed
            ])
    
    def start_travel(self, destination_id):
        """Start traveling to a new location"""
        if self.travel_state != "idle":
            return False
        
        travel_options = self.system_map.get_travel_options()
        if destination_id not in travel_options:
            return False
        
        travel_info = travel_options[destination_id]
        travel_cost = travel_info["cost"]
        
        # Check if player can afford travel
        if self.player.credits < travel_cost:
            return False
        
        # Deduct credits
        self.player.credits -= travel_cost
        
        # Start travel
        self.travel_state = "traveling"
        self.travel_progress = 0.0
        self.destination = destination_id
        self.origin = self.system_map.player_location
        
        # Generate random events based on distance and danger
        self._generate_travel_events(travel_info["distance"], 
                                    self.system_map.locations[destination_id].danger_level)
        
        return True
    
    def update(self, dt):
        """Update travel progress and handle events"""
        if self.travel_state == "idle":
            return
        
        if self.travel_state == "traveling":
            self.travel_progress += self.travel_speed * dt
            
            # Update visual effect
            for star in self.stars:
                star[0] -= star[2] * 20 * dt
                if star[0] < 0:
                    star[0] = 800
                    star[1] = random.randint(0, 600)
            
            # Check for events at certain progress points
            for event in self.travel_events[:]:
                if event["progress"] <= self.travel_progress:
                    self.travel_events.remove(event)
                    self._handle_travel_event(event)
            
            # Check if travel is complete
            if self.travel_progress >= 1.0:
                self.complete_travel()
        
        elif self.travel_state == "encounter":
            # Handle encounter state
            # This would be implemented based on your encounter system
            pass
    
    def complete_travel(self):
        """Complete travel and arrive at destination"""
        if self.destination:
            self.system_map.set_player_location(self.destination)
            self.travel_state = "idle"
            self.destination = None
            self.origin = None
            self.travel_events = []
    
    def cancel_travel(self):
        """Cancel travel and return to origin"""
        if self.origin:
            self.system_map.set_player_location(self.origin)
            self.travel_state = "idle"
            self.destination = None
            self.origin = None
            self.travel_events = []
    
    def _generate_travel_events(self, distance, danger_level):
        """Generate random events during travel"""
        self.travel_events = []
        
        # Number of potential events based on distance and danger
        num_events = int(distance / 20) + int(danger_level / 2)
        
        for _ in range(num_events):
            # Only generate an event if random check passes
            if random.random() < 0.3 + (danger_level / 20):
                progress = random.uniform(0.2, 0.9)
                event_type = self._get_random_event_type(danger_level)
                
                self.travel_events.append({
                    "progress": progress,
                    "type": event_type,
                    "handled": False
                })
        
        # Sort events by progress
        self.travel_events.sort(key=lambda x: x["progress"])
    
    def _get_random_event_type(self, danger_level):
        """Get a random event type based on danger level"""
        possible_events = ["asteroid_field", "space_debris", "radiation_cloud"]
        
        if danger_level > 3:
            possible_events.extend(["pirate_encounter", "ship_malfunction"])
        
        if danger_level > 6:
            possible_events.extend(["syndicate_patrol", "military_inspection"])
        
        return random.choice(possible_events)
    
    def _handle_travel_event(self, event):
        """Handle a travel event"""
        event_type = event["type"]
        
        if event_type in ["pirate_encounter", "syndicate_patrol", "military_inspection"]:
            # These events pause travel for an encounter
            self.travel_state = "encounter"
            # Additional encounter handling would go here
        
        # Other events might just have effects without pausing
        elif event_type == "asteroid_field":
            # Maybe damage the ship or require a skill check
            pass
        elif event_type == "space_debris":
            # Minor obstacle
            pass
        elif event_type == "radiation_cloud":
            # Could affect player health
            pass
        elif event_type == "ship_malfunction":
            # Could require resources to fix
            pass
    
    def draw(self, screen):
        """Draw travel screen and progress"""
        if self.travel_state == "idle":
            return
        
        # Draw space background
        screen.fill((5, 5, 20))
        
        # Draw moving stars
        for star in self.stars:
            brightness = int(star[2] * 200)
            pygame.draw.circle(screen, (brightness, brightness, brightness), 
                              (int(star[0]), int(star[1])), 
                              1 if star[2] < 1 else 2)
        
        # Draw travel information
        if self.destination and self.destination in self.system_map.locations:
            dest_name = self.system_map.locations[self.destination].name
            font = pygame.font.Font(None, 32)
            text = font.render(f"Traveling to {dest_name}...", True, (255, 255, 255))
            screen.blit(text, (400 - text.get_width() // 2, 50))
        
        # Draw progress bar
        bar_width = 400
        bar_height = 20
        bar_x = 400 - bar_width // 2
        bar_y = 100
        
        # Background bar
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Progress bar
        progress_width = int(bar_width * self.travel_progress)
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, progress_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)


# Example usage:
# system_map = SystemMap(1000, 1000)
# 
# # Add locations
# psyche = Location("Psyche", "Mining colony and shipyard", "psyche_map.csv", position=(500, 300), faction="mars")
# ceres = Location("Ceres", "Major trading hub", "ceres_map.csv", position=(300, 200), faction="earth")
# pallas = Location("Pallas", "Syndicate stronghold", "pallas_map.csv", position=(700, 400), faction="pallas")
# vesta = Location("Vesta", "Mining outpost", "vesta_map.csv", position=(400, 500), faction="earth")
# 
# # Add connections
# psyche.add_connection("ceres", 200)
# psyche.add_connection("pallas", 250)
# psyche.add_connection("vesta", 150)
# ceres.add_connection("psyche", 200)
# ceres.add_connection("vesta", 180)
# pallas.add_connection("psyche", 250)
# vesta.add_connection("psyche", 150)
# vesta.add_connection("ceres", 180)
# 
# # Add locations to map
# system_map.add_location("psyche", psyche)
# system_map.add_location("ceres", ceres)
# system_map.add_location("pallas", pallas)
# system_map.add_location("vesta", vesta)
# 
# # Set player location
# system_map.set_player_location("psyche")
# 
# # Create space travel system
# space_travel = SpaceTravel(system_map, player)
