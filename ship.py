import pygame
import csv
import os
import math

class Ship:
    def __init__(self, layout_file="mvp_ship.csv"):
        self.layout = []
        self.tiles = {}
        self.width = 0
        self.height = 0
        self.tile_size = 16  # Size of each tile in pixels
        
        # Ship properties calculated from tiles
        self.thrust_power = 0.0
        self.rotation_speed = 0.0
        self.max_speed = 0.0
        self.hull_strength = 0
        self.shield_strength = 0
        self.cargo_capacity = 0
        
        # Colors for different tile types
        self.tile_colors = {
            'E': None,           # Empty space - transparent
            'H': (150, 150, 150), # Hull - gray
            'C': (0, 255, 255),   # Cockpit - cyan
            'T': (255, 100, 0),   # Thruster - orange
            'S': (100, 200, 255), # Steering - light blue
            'W': (255, 50, 50),   # Weapon - red
            'P': (255, 255, 100), # Power core - yellow
            'G': (100, 255, 100), # Shield - green
            'O': (150, 100, 50),  # Cargo - brown
            'X': (255, 50, 255)   # Special - purple
        }
        
        # Load the ship layout
        self.load_layout(layout_file)
        
        # Calculate ship properties based on the layout
        self.calculate_ship_properties()
        
        # Create the ship surface
        self.create_ship_surface()
    
    def load_layout(self, layout_file):
        """Load the ship layout from a CSV file"""
        try:
            filepath = os.path.join('assets', 'ships', layout_file)
            
            # Create temporary layout
            temp_layout = []
            
            with open(filepath, 'r') as file:
                for line in file:
                    # Skip comments and empty lines
                    if line.strip().startswith('#') or not line.strip():
                        continue
                        
                    # Add the row to our layout
                    temp_layout.append(line.strip())
            
            # Find the dimensions
            if temp_layout:
                self.height = len(temp_layout)
                self.width = max(len(row) for row in temp_layout)
                
                # Create a standardized layout with equal row lengths
                for row in temp_layout:
                    padded_row = row.ljust(self.width, 'E')
                    self.layout.append(padded_row)
                    
                print(f"Loaded ship layout: {self.width}x{self.height}")
            else:
                print("Warning: No layout data found in file")
                
        except FileNotFoundError:
            print(f"Error: Ship layout file '{layout_file}' not found")
            # Create a simple default ship
            self.layout = [
                "EEHEE",
                "EHCHE",
                "EHPHE",
                "EHTHE"
            ]
            self.width = 5
            self.height = 4
            print("Using default ship layout instead")
            
        # Count all tile types
        for row in self.layout:
            for tile_type in row:
                if tile_type not in self.tiles:
                    self.tiles[tile_type] = 0
                self.tiles[tile_type] += 1
                
        print(f"Ship tile counts: {self.tiles}")
    
    def calculate_ship_properties(self):
        """Calculate ship properties based on the layout"""
        # Base values
        self.thrust_power = 0.05
        self.rotation_speed = 2
        self.max_speed = 3
        self.hull_strength = 10
        
        # Add bonuses based on tiles
        if 'T' in self.tiles:  # Thrusters
            self.thrust_power += 0.02 * self.tiles['T']
            self.max_speed += 0.5 * self.tiles['T']
            
        if 'S' in self.tiles:  # Steering thrusters
            self.rotation_speed += 0.5 * self.tiles['S']
            
        if 'H' in self.tiles:  # Hull tiles
            self.hull_strength += self.tiles['H']
            
        if 'G' in self.tiles:  # Shield generator
            self.shield_strength = 5 * self.tiles['G']
            
        if 'O' in self.tiles:  # Cargo hold
            self.cargo_capacity = 100 * self.tiles['O']
            
        if 'P' in self.tiles:  # Power core boosts everything
            power_bonus = 1.0 + (0.1 * self.tiles['P'])
            self.thrust_power *= power_bonus
            self.max_speed *= power_bonus
            self.rotation_speed *= power_bonus
            if self.shield_strength > 0:
                self.shield_strength *= power_bonus
        
        print(f"Ship properties calculated:")
        print(f"  Thrust: {self.thrust_power:.2f}")
        print(f"  Max Speed: {self.max_speed:.2f}")
        print(f"  Rotation: {self.rotation_speed:.2f}")
        print(f"  Hull: {self.hull_strength}")
        print(f"  Shield: {self.shield_strength:.2f}")
        print(f"  Cargo: {self.cargo_capacity}")
    
    def create_ship_surface(self):
        """Create the ship surface based on the layout"""
        # Create surface with per-pixel alpha
        self.surface = pygame.Surface((self.width * self.tile_size, 
                                       self.height * self.tile_size), 
                                      pygame.SRCALPHA)
        
        # Draw each tile
        for y, row in enumerate(self.layout):
            for x, tile_type in enumerate(row):
                if tile_type in self.tile_colors and self.tile_colors[tile_type]:
                    rect = pygame.Rect(x * self.tile_size, y * self.tile_size,
                                      self.tile_size, self.tile_size)
                    pygame.draw.rect(self.surface, self.tile_colors[tile_type], rect)
                    # Add a slight border
                    pygame.draw.rect(self.surface, (50, 50, 50), rect, 1)
    
    def draw(self, screen, center_x, center_y, angle=0):
        """Draw the ship at the specified position and rotation"""
        # Create a rotated copy of the ship surface
        rotated_surface = pygame.transform.rotate(self.surface, -angle)
        
        # Get the new rect for the rotated surface
        rotated_rect = rotated_surface.get_rect()
        rotated_rect.center = (center_x, center_y)
        
        # Draw the rotated ship
        screen.blit(rotated_surface, rotated_rect)
        
        # Debugging: Draw center point
        pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), 2)
    
    def get_thrust_points(self):
        """Get the positions of thrusters for flame effects"""
        thrust_points = []
        
        # Find all thruster tiles
        for y, row in enumerate(self.layout):
            for x, tile_type in enumerate(row):
                if tile_type == 'T':
                    # Calculate center position of this tile
                    center_x = (x + 0.5) * self.tile_size
                    center_y = (y + 0.5) * self.tile_size
                    thrust_points.append((center_x, center_y))
        
        return thrust_points
    
    def get_cockpit_position(self):
        """Get the position of the cockpit/helm"""
        for y, row in enumerate(self.layout):
            for x, tile_type in enumerate(row):
                if tile_type == 'C':
                    # Return the center position of this tile
                    return ((x + 0.5) * self.tile_size, (y + 0.5) * self.tile_size)
        
        # If no cockpit found, use center of ship
        return (self.width * self.tile_size / 2, self.height * self.tile_size / 2)
        
    def apply_damage(self, amount):
        """Apply damage to the ship"""
        # First reduce shields if available
        if self.shield_strength > 0:
            if amount <= self.shield_strength:
                self.shield_strength -= amount
                amount = 0
            else:
                amount -= self.shield_strength
                self.shield_strength = 0
        
        # Then reduce hull
        self.hull_strength -= amount
        
        # Return True if ship is still intact
        return self.hull_strength > 0
