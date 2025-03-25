import os
import csv
import math
from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject

class MapLoader(DirectObject):
    """Handles loading and rendering map data from CSV files"""
    
    def __init__(self, base, render_node):
        """Initialize the map loader
        
        Args:
            base: The ShowBase instance
            render_node: The parent node to attach map elements to
        """
        self.base = base
        self.render_node = render_node
        
        # Map data
        self.tile_size = 1.0  # Size of each tile in 3D units
        self.current_map = None
        self.map_data = []
        self.map_width = 0
        self.map_height = 0
        
        # Create a node to hold all map elements
        self.map_root = render_node.attachNewNode("map_root")
        
        # Map elements by type
        self.walls = []
        self.floors = []
        self.doors = []
        self.npcs = {}  # Dictionary of NPC positions: {id: (x, y)}
        self.objects = []
        self.exits = []
        
        # Create material for walls
        self.wall_material = Material()
        self.wall_material.setAmbient((0.2, 0.2, 0.2, 1))
        self.wall_material.setDiffuse((0.8, 0.8, 0.8, 1))
        
        # Dictionary mapping CSV characters to tile creation functions
        self.tile_creators = {
            'W': self.create_wall,
            'F': self.create_floor,
            'D': self.create_door,
            'T': self.create_table,
            'C': self.create_chair,
            'B': self.create_bed,
            'S': self.create_storage,
            'V': self.create_viewport,
            'H': self.create_hangar,
            'E': self.create_exit,
            '@': self.mark_player_start,
            # Add more tile types as needed
        }
        
        # Dictionary for numeric NPC references
        for i in range(1, 10):
            self.tile_creators[str(i)] = lambda x, y, npc_id=i: self.mark_npc_position(x, y, npc_id)
    
    def load_map(self, map_file):
        """Load a map from a CSV file
        
        Args:
            map_file: Path to the CSV map file
        
        Returns:
            True if map loaded successfully, False otherwise
        """
        self.clear_map()  # Clear any existing map
        
        # Check if file exists
        if not os.path.exists(map_file):
            print(f"Map file not found: {map_file}")
            return False
        
        try:
            # Parse map data
            self.map_data = []
            player_start = None
            
            with open(map_file, 'r') as file:
                for line in file:
                    # Skip comments and empty lines
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Add line to map data
                    self.map_data.append(line)
            
            # Set map dimensions
            self.map_height = len(self.map_data)
            self.map_width = max(len(row) for row in self.map_data)
            
            # Process each tile
            for y, row in enumerate(self.map_data):
                for x, char in enumerate(row):
                    # Skip empty cells
                    if x >= len(row) or char == ' ':
                        continue
                    
                    # Get the appropriate tile creation function
                    create_func = self.tile_creators.get(char)
                    if create_func:
                        create_func(x, y)
            
            # Set up ambient lighting
            ambient_light = AmbientLight("ambient")
            ambient_light.setColor((0.4, 0.4, 0.4, 1))
            ambient_node = self.map_root.attachNewNode(ambient_light)
            self.map_root.setLight(ambient_node)
            
            # Add a directional light
            directional_light = DirectionalLight("directional")
            directional_light.setColor((0.7, 0.7, 0.7, 1))
            directional_light.setDirection((0, -1, -1))  # Coming from above and behind
            directional_node = self.map_root.attachNewNode(directional_light)
            self.map_root.setLight(directional_node)
            
            print(f"Map loaded: {map_file}")
            print(f"  Dimensions: {self.map_width}x{self.map_height}")
            print(f"  Walls: {len(self.walls)}")
            print(f"  Floors: {len(self.floors)}")
            print(f"  Doors: {len(self.doors)}")
            print(f"  NPCs: {len(self.npcs)}")
            
            self.current_map = map_file
            return True
            
        except Exception as e:
            print(f"Error loading map {map_file}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def clear_map(self):
        """Clear the current map from the scene"""
        self.map_root.removeNode()
        self.map_root = self.render_node.attachNewNode("map_root")
        
        # Reset map data
        self.map_data = []
        self.walls = []
        self.floors = []
        self.doors = []
        self.npcs = {}
        self.objects = []
        self.exits = []
        
        self.current_map = None
    
    def create_wall(self, x, y):
        """Create a wall at the specified position"""
        # Create a simple cube for the wall
        wall = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple cube
        if wall is None:
            cm = CardMaker("wall_cube")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            wall = NodePath("wall")
            
            # Create the six faces of a cube
            for i, (h, p) in enumerate([(0, 0), (180, 0), (90, 0), (270, 0), (0, 90), (0, -90)]):
                face = wall.attachNewNode(cm.generate())
                face.setHpr(h, p, 0)
                face.setPos(0, -0.5 if i < 2 else 0, 0)
            
        # Position the wall
        wall.setPos(x * self.tile_size, y * self.tile_size, 0.5)
        wall.setScale(self.tile_size, self.tile_size, self.tile_size)
        
        # Set appearance
        wall.setColor(0.7, 0.7, 0.7, 1)  # Gray color
        wall.setMaterial(self.wall_material)
        
        # Attach to the map
        wall.reparentTo(self.map_root)
        wall.setTag("type", "wall")
        wall.setTag("grid_x", str(x))
        wall.setTag("grid_y", str(y))
        
        self.walls.append(wall)
        return wall
    
    def create_floor(self, x, y):
        """Create a floor tile at the specified position"""
        # Create a simple card for the floor
        floor = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple plane
        if exit_node is None:
            cm = CardMaker("exit")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            exit_node = self.map_root.attachNewNode(cm.generate())
            exit_node.setP(-90)  # Rotate to be horizontal
        
        # Position the exit
        exit_node.setPos(x * self.tile_size, y * self.tile_size, 0.05)  # Slightly above floor
        exit_node.setScale(self.tile_size, self.tile_size, 0.1)
        
        # Set appearance - make it green and pulsing
        exit_node.setColor(0, 1, 0, 0.7)  # Semi-transparent green
        exit_node.setTransparency(TransparencyAttrib.MAlpha)
        
        # Create a pulsing effect
        pulse = exit_node.colorScaleInterval(1.5, (1, 1, 1, 0.4), (1, 1, 1, 0.8))
        pulse.loop()
        
        # Attach to the map
        exit_node.reparentTo(self.map_root)
        exit_node.setTag("type", "exit")
        exit_node.setTag("grid_x", str(x))
        exit_node.setTag("grid_y", str(y))
        
        self.exits.append(exit_node)
        return exit_node
    
    def mark_player_start(self, x, y):
        """Mark the player's starting position"""
        # Create a floor tile first
        self.create_floor(x, y)
        
        # Store the starting position
        self.player_start = (x * self.tile_size, y * self.tile_size, 0)
        
        # Create a temporary visual indicator
        marker = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple marker
        if marker is None:
            cm = CardMaker("start_marker")
            cm.setFrame(-0.2, 0.2, -0.2, 0.2)
            marker = self.map_root.attachNewNode(cm.generate())
            marker.setP(-90)  # Rotate to be horizontal
        
        # Position the marker
        marker.setPos(x * self.tile_size, y * self.tile_size, 0.1)
        marker.setScale(0.4, 0.4, 0.1)
        
        # Set appearance
        marker.setColor(0, 1, 0, 0.5)  # Semi-transparent green
        marker.setTransparency(TransparencyAttrib.MAlpha)
        
        # The marker is temporary and not used for collision
        marker.setTag("type", "start_marker")
        
        return marker
    
    def mark_npc_position(self, x, y, npc_id):
        """Mark an NPC position on the map"""
        # Create a floor tile first
        self.create_floor(x, y)
        
        # Store the NPC position
        self.npcs[npc_id] = (x * self.tile_size, y * self.tile_size, 0)
        
        # Create a temporary visual indicator
        marker = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple marker
        if marker is None:
            cm = CardMaker("npc_marker")
            cm.setFrame(-0.2, 0.2, -0.2, 0.2)
            marker = self.map_root.attachNewNode(cm.generate())
            marker.setP(-90)  # Rotate to be horizontal
        
        # Position the marker
        marker.setPos(x * self.tile_size, y * self.tile_size, 0.1)
        marker.setScale(0.4, 0.4, 0.1)
        
        # Set appearance - different colors for different NPCs
        colors = [(1, 0, 0, 0.5), (0, 0, 1, 0.5), (1, 1, 0, 0.5), 
                 (1, 0, 1, 0.5), (0, 1, 1, 0.5), (1, 0.5, 0, 0.5),
                 (0.5, 0, 1, 0.5), (0, 1, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)]
        marker.setColor(colors[(npc_id-1) % len(colors)])
        marker.setTransparency(TransparencyAttrib.MAlpha)
        
        # The marker is temporary and not used for collision
        marker.setTag("type", "npc_marker")
        marker.setTag("npc_id", str(npc_id))
        
        return marker
    
    def get_player_start(self):
        """Get the player's starting position"""
        # Return the player's starting position if available, otherwise use a default
        if hasattr(self, 'player_start'):
            return self.player_start
        
        # Default to the center of the map if no start position is defined
        return (self.map_width * self.tile_size / 2, self.map_height * self.tile_size / 2, 0)
    
    def get_npc_position(self, npc_id):
        """Get the position for a specific NPC"""
        return self.npcs.get(npc_id, (0, 0, 0))
    
    def get_world_position(self, grid_x, grid_y):
        """Convert grid coordinates to world coordinates"""
        return (grid_x * self.tile_size, grid_y * self.tile_size, 0)
    
    def get_grid_position(self, world_x, world_y):
        """Convert world coordinates to grid coordinates"""
        grid_x = int(world_x / self.tile_size)
        grid_y = int(world_y / self.tile_size)
        return (grid_x, grid_y)
    
    def is_valid_position(self, world_x, world_y):
        """Check if a world position is valid (not inside a wall)"""
        grid_x, grid_y = self.get_grid_position(world_x, world_y)
        
        # Check bounds
        if grid_x < 0 or grid_y < 0 or grid_y >= len(self.map_data):
            return False
        
        # Check if position is in a wall
        if grid_y < len(self.map_data) and grid_x < len(self.map_data[grid_y]):
            tile_type = self.map_data[grid_y][grid_x]
            return tile_type != 'W'  # Not a wall
        
        return False
    
    def get_near_exit(self, world_x, world_y, radius=1.5):
        """Check if player is near an exit"""
        for exit_node in self.exits:
            exit_x = float(exit_node.getTag("grid_x")) * self.tile_size
            exit_y = float(exit_node.getTag("grid_y")) * self.tile_size
            
            # Calculate distance
            dx = world_x - exit_x
            dy = world_y - exit_y
            distance = (dx**2 + dy**2)**0.5
            
            if distance <= radius * self.tile_size:
                return exit_node
        
        return None
        if floor is None:
            cm = CardMaker("floor_tile")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            floor = self.map_root.attachNewNode(cm.generate())
            floor.setP(-90)  # Rotate to be horizontal
        
        # Position the floor
        floor.setPos(x * self.tile_size, y * self.tile_size, 0)
        floor.setScale(self.tile_size, self.tile_size, 0.1)  # Thin in Z axis
        
        # Set appearance
        floor.setColor(0.3, 0.3, 0.3, 1)  # Dark gray
        
        # Attach to the map
        floor.reparentTo(self.map_root)
        floor.setTag("type", "floor")
        
        self.floors.append(floor)
        return floor
    
    def create_door(self, x, y):
        """Create a door at the specified position"""
        # Create a simple card for the door
        door = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple plane
        if door is None:
            cm = CardMaker("door")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            door = NodePath("door")
            
            # Create front and back faces
            front = door.attachNewNode(cm.generate())
            front.setZ(0.01)  # Slight offset to prevent z-fighting
            
            back = door.attachNewNode(cm.generate())
            back.setH(180)
            back.setZ(-0.01)
        
        # Position the door
        door.setPos(x * self.tile_size, y * self.tile_size, 0.5)
        door.setScale(self.tile_size, 0.1, self.tile_size)  # Thin in Y axis
        
        # Set appearance
        door.setColor(0.6, 0.3, 0.1, 1)  # Brown color
        
        # Attach to the map
        door.reparentTo(self.map_root)
        door.setTag("type", "door")
        
        self.doors.append(door)
        return door
    
    def create_table(self, x, y):
        """Create a table at the specified position"""
        # For now, use a simple box with appropriate dimensions
        table = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple box
        if table is None:
            cm = CardMaker("table_top")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            table = NodePath("table")
            
            # Create the six faces of a box
            for i, (h, p) in enumerate([(0, 0), (180, 0), (90, 0), (270, 0), (0, 90), (0, -90)]):
                face = table.attachNewNode(cm.generate())
                face.setHpr(h, p, 0)
                face.setPos(0, -0.5 if i < 2 else 0, 0)
        
        # Position the table
        table.setPos(x * self.tile_size, y * self.tile_size, 0.3)
        table.setScale(self.tile_size * 0.8, self.tile_size * 0.8, 0.3)  # Lower height
        
        # Set appearance
        table.setColor(0.6, 0.4, 0.2, 1)  # Wood color
        
        # Attach to the map
        table.reparentTo(self.map_root)
        table.setTag("type", "furniture")
        
        self.objects.append(table)
        return table
    
    def create_chair(self, x, y):
        """Create a chair at the specified position"""
        # Simple placeholder for now
        chair = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple box
        if chair is None:
            cm = CardMaker("chair_seat")
            cm.setFrame(-0.3, 0.3, -0.3, 0.3)
            chair = NodePath("chair")
            
            # Create seat
            seat = chair.attachNewNode(cm.generate())
            seat.setP(-90)
            seat.setZ(0.2)
            
            # Create back
            back_cm = CardMaker("chair_back")
            back_cm.setFrame(-0.3, 0.3, 0, 0.5)
            back = chair.attachNewNode(back_cm.generate())
            back.setY(-0.3)
        
        # Position the chair
        chair.setPos(x * self.tile_size, y * self.tile_size, 0.2)
        chair.setScale(0.6, 0.6, 0.6)
        
        # Set appearance
        chair.setColor(0.6, 0.3, 0.1, 1)  # Brown color
        
        # Attach to the map
        chair.reparentTo(self.map_root)
        chair.setTag("type", "furniture")
        
        self.objects.append(chair)
        return chair
    
    def create_bed(self, x, y):
        """Create a bed at the specified position"""
        # Simple placeholder for a bed
        bed = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple box
        if bed is None:
            cm = CardMaker("bed")
            cm.setFrame(-0.5, 0.5, -1, 1)  # Longer in Y direction
            bed = NodePath("bed")
            
            # Create top and sides
            top = bed.attachNewNode(cm.generate())
            top.setP(-90)
            top.setZ(0.2)
            
            # Create headboard
            headboard_cm = CardMaker("headboard")
            headboard_cm.setFrame(-0.5, 0.5, 0, 0.5)
            headboard = bed.attachNewNode(headboard_cm.generate())
            headboard.setY(-1)
        
        # Position the bed
        bed.setPos(x * self.tile_size, y * self.tile_size, 0.2)
        bed.setScale(self.tile_size * 0.9, self.tile_size * 0.9, 0.4)
        
        # Set appearance
        bed.setColor(0.5, 0.3, 0.7, 1)  # Purple bedding
        
        # Attach to the map
        bed.reparentTo(self.map_root)
        bed.setTag("type", "furniture")
        
        self.objects.append(bed)
        return bed
    
    def create_storage(self, x, y):
        """Create a storage container at the specified position"""
        # Simple placeholder for storage
        storage = self.base.loader.loadModel("models/box")
        
        # Position the storage container
        storage.setPos(x * self.tile_size, y * self.tile_size, 0.4)
        storage.setScale(0.7, 0.7, 0.8)
        
        # Set appearance
        storage.setColor(0.4, 0.4, 0.6, 1)  # Bluish-gray
        
        # Attach to the map
        storage.reparentTo(self.map_root)
        storage.setTag("type", "storage")
        
        self.objects.append(storage)
        return storage
    
    def create_viewport(self, x, y):
        """Create a viewport/window at the specified position"""
        # Check if this should be a wall with a window
        # For now, create a transparent blue panel
        viewport = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple plane
        if viewport is None:
            cm = CardMaker("viewport")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            viewport = NodePath("viewport")
            
            # Create front and back faces
            front = viewport.attachNewNode(cm.generate())
            back = viewport.attachNewNode(cm.generate())
            back.setH(180)
        
        # Position the viewport
        viewport.setPos(x * self.tile_size, y * self.tile_size, 0.5)
        viewport.setScale(self.tile_size, 0.1, self.tile_size)
        
        # Set appearance
        viewport.setColor(0.3, 0.6, 1.0, 0.4)  # Transparent blue
        viewport.setTransparency(TransparencyAttrib.MAlpha)
        
        # Attach to the map
        viewport.reparentTo(self.map_root)
        viewport.setTag("type", "viewport")
        
        self.objects.append(viewport)
        return viewport
    
    def create_hangar(self, x, y):
        """Create a hangar/dock area at the specified position"""
        # For now, just a differently colored floor
        hangar = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple plane
        if hangar is None:
            cm = CardMaker("hangar_floor")
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            hangar = self.map_root.attachNewNode(cm.generate())
            hangar.setP(-90)  # Rotate to be horizontal
        
        # Position the hangar
        hangar.setPos(x * self.tile_size, y * self.tile_size, 0.01)  # Slightly above floor
        hangar.setScale(self.tile_size, self.tile_size, 0.1)
        
        # Set appearance
        hangar.setColor(0.1, 0.2, 0.3, 1)  # Dark blue-gray
        
        # Attach to the map
        hangar.reparentTo(self.map_root)
        hangar.setTag("type", "hangar")
        
        self.objects.append(hangar)
        return hangar
    
    def create_exit(self, x, y):
        """Create an exit at the specified position"""
        # Create a visual indicator for an exit
        exit_node = self.base.loader.loadModel("models/box")
        
        # If the model isn't available, create a simple plane