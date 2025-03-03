import pygame

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = 0
        self.map_height = 0
        
    def set_map_size(self, map_width, map_height):
        """Set the size of the map to properly constrain the camera"""
        self.map_width = map_width
        self.map_height = map_height
        
    def apply(self, entity):
        """Return a rect with camera offset applied"""
        if hasattr(entity, 'rect'):
            new_rect = entity.rect.copy()
            new_rect.x += self.camera.x
            new_rect.y += self.camera.y
            return new_rect
        elif isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        else:
            return entity
        
    def update(self, target):
        """Update camera position to track target (usually the player)"""
        # Calculate camera offset to center the target
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        
        # Limit the camera so we don't see beyond the map edges
        if self.map_width > 0:
            x = min(0, x)  # left limit
            x = max(-(self.map_width - self.width), x)  # right limit
            
        if self.map_height > 0:
            y = min(0, y)  # top limit
            y = max(-(self.map_height - self.height), y)  # bottom limit
        
        # Update camera position
        self.camera = pygame.Rect(x, y, self.width, self.height)