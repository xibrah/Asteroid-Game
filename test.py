from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import csv

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Set up the camera
        self.disableMouse()  # Disable default camera control
        
        # Load a map from CSV
        self.load_map("assets/maps/psyche_township.csv")
        
        # Add player character
        self.player = self.loader.loadModel("models/player")
        self.player.setPos(0, 0, 0)
        self.player.reparentTo(self.render)
        
        # Set up player movement
        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.accept("w", self.set_key, ["w", True])
        self.accept("w-up", self.set_key, ["w", False])
        # Add other key handlers
        
        # Add a task to handle player movement
        self.taskMgr.add(self.update, "update")
        
        # Toggle between 2D and 3D views
        self.accept("v", self.toggle_view)
        self.current_view = "2d"
    
    def load_map(self, csv_file):
        # Read CSV file and create terrain
        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            for y, row in enumerate(csv_reader):
                for x, cell in enumerate(row):
                    if cell == 'W':  # Wall
                        self.create_wall(x, y)
                    # Handle other tile types
    
    def create_wall(self, x, y):
        wall = self.loader.loadModel("models/cube")
        wall.setPos(x, y, 0.5)  # Position in 3D space
        wall.setScale(0.5, 0.5, 1)
        wall.reparentTo(self.render)
    
    def set_key(self, key, value):
        self.keys[key] = value
    
    def update(self, task):
        # Move player based on key presses
        if self.keys["w"]:
            self.player.setY(self.player, 0.1)
        # Handle other movements
        
        return task.cont
    
    def toggle_view(self):
        if self.current_view == "2d":
            # Switch to 3D first-person view
            self.camera.setPos(self.player.getX(), self.player.getY(), 1.0)
            self.camera.reparentTo(self.player)
            self.current_view = "3d"
        else:
            # Switch to 2D top-down view
            self.camera.setPos(0, 0, 20)
            self.camera.lookAt(0, 0, 0)
            self.camera.reparentTo(self.render)
            self.current_view = "2d"

app = MyGame()
app.run()