from panda3d.core import *
from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject
import math

class UI(DirectObject):
    """User interface system for the game"""
    
    def __init__(self, base):
        """Initialize the UI system
        
        Args:
            base: The ShowBase instance
        """
        self.base = base
        
        # Create a node for 2D elements
        self.ui_root = aspect2d.attachNewNode("UI_Root")
        
        # Player stats display
        self.player_stats = self.create_player_stats()
        
        # Interaction prompts
        self.interaction_prompt = self.create_interaction_prompt()
        self.interaction_prompt.hide()
        
        # Messages display
        self.message_display = self.create_message_display()
        self.message_timer = 0
        
        # Controls help
        self.controls_help = self.create_controls_help()
        
        # Add a task to update the UI
        self.base.taskMgr.add(self.update_task, "ui_update_task")
        
        # Listen for events
        self.accept("player_near_exit", self.show_exit_prompt)
        self.accept("player_near_npc", self.show_npc_prompt)
        self.accept("show_message", self.show_message)
    
    def create_player_stats(self):
        """Create UI elements for player stats display"""
        # Container frame
        stats_frame = DirectFrame(
            parent=self.ui_root,
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-0.3, 0.3, -0.1, 0.1),
            pos=(-1.0, 0, 0.9),  # Top-left corner
        )
        
        # Health text
        health_text = DirectLabel(
            parent=stats_frame,
            text="Health: 100/100",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            pos=(-0.25, 0, 0.05),
            text_fg=(1, 1, 1, 1)
        )
        
        # Credits text
        credits_text = DirectLabel(
            parent=stats_frame,
            text="Credits: 100",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            pos=(-0.25, 0, -0.05),
            text_fg=(1, 1, 1, 1)
        )
        
        # Store these for later updates
        stats_frame.health_text = health_text
        stats_frame.credits_text = credits_text
        
        return stats_frame
    
    def create_interaction_prompt(self):
        """Create UI element for interaction prompts"""
        prompt = DirectLabel(
            parent=self.ui_root,
            text="Press E to interact",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0.7),
            pad=(0.5, 0.2),
            pos=(0, 0, -0.7),  # Bottom center
        )
        return prompt
    
    def create_message_display(self):
        """Create UI element for displaying messages"""
        message = DirectLabel(
            parent=self.ui_root,
            text="",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0.7),
            pad=(0.5, 0.2),
            pos=(0, 0, 0.7),  # Top center
        )
        message.hide()
        return message
    
    def create_controls_help(self):
        """Create UI element showing controls"""
        help_text = """
        Controls:
        WASD - Move
        Arrow Keys - Turn
        E - Interact
        1/2/3 - Camera Views
        Tab - Toggle UI
        Esc - Menu
        """
        
        help_frame = DirectFrame(
            parent=self.ui_root,
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-0.3, 0.3, -0.25, 0.25),
            pos=(1.0, 0, -0.7),  # Bottom-right corner
        )
        
        help_label = DirectLabel(
            parent=help_frame,
            text=help_text,
            text_scale=0.04,
            text_align=TextNode.ALeft,
            pos=(-0.25, 0, 0.2),
            text_fg=(1, 1, 1, 1)
        )
        
        return help_frame
    
    def update_task(self, task):
        """Task to update UI elements each frame"""
        # Update message timer
        if self.message_timer > 0:
            dt = globalClock.getDt()
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_display.hide()
        
        return task.cont
    
    def update_player_stats(self, health, max_health, credits):
        """Update the player stats display
        
        Args:
            health: Current player health
            max_health: Maximum player health
            credits: Player credits
        """
        self.player_stats.health_text["text"] = f"Health: {health}/{max_health}"
        self.player_stats.credits_text["text"] = f"Credits: {credits}"
    
    def show_exit_prompt(self, exit_type="location"):
        """Show the interaction prompt for an exit
        
        Args:
            exit_type: Type of exit (location, ship, etc.)
        """
        if exit_type == "location":
            self.interaction_prompt["text"] = "Press E to travel"
        elif exit_type == "ship":
            self.interaction_prompt["text"] = "Press E to board ship"
        else:
            self.interaction_prompt["text"] = "Press E to use exit"
            
        self.interaction_prompt.show()
    
    def show_npc_prompt(self, npc_name):
        """Show the interaction prompt for an NPC
        
        Args:
            npc_name: Name of the NPC
        """
        self.interaction_prompt["text"] = f"Press E to talk to {npc_name}"
        self.interaction_prompt.show()
    
    def hide_interaction_prompt(self):
        """Hide the interaction prompt"""
        self.interaction_prompt.hide()
    
    def show_message(self, message, duration=3.0):
        """Show a message for a specified duration
        
        Args:
            message: Message text to display
            duration: Time in seconds to show the message
        """
        self.message_display["text"] = message
        self.message_display.show()
        self.message_timer = duration
    
    def toggle_ui(self):
        """Toggle visibility of UI elements"""
        if self.ui_root.isHidden():
            self.ui_root.show()
        else:
            self.ui_root.hide()
    
    def show_dialogue(self, npc_name, dialogue_text):
        """Show a dialogue box for NPC conversation
        
        Args:
            npc_name: Name of the speaking NPC
            dialogue_text: Text of the dialogue
        """
        # Create a dialogue box if it doesn't exist
        if not hasattr(self, 'dialogue_box'):
            self.dialogue_box = DirectFrame(
                parent=self.ui_root,
                frameColor=(0, 0, 0, 0.8),
                frameSize=(-0.9, 0.9, -0.3, 0.3),
                pos=(0, 0, -0.4),
                state=DGG.NORMAL,
            )
            
            # NPC name label
            self.npc_name_label = DirectLabel(
                parent=self.dialogue_box,
                text="",
                text_scale=0.06,
                text_align=TextNode.ALeft,
                pos=(-0.85, 0, 0.22),
                text_fg=(1, 0.8, 0.4, 1)  # Gold color for names
            )
            
            # Dialogue text
            self.dialogue_text = DirectLabel(
                parent=self.dialogue_box,
                text="",
                text_scale=0.045,
                text_align=TextNode.ALeft,
                text_wordwrap=30,
                pos=(-0.85, 0, 0.1),
                text_fg=(1, 1, 1, 1)
            )
            
            # Continue prompt
            self.continue_prompt = DirectLabel(
                parent=self.dialogue_box,
                text="Press E to continue",
                text_scale=0.04,
                text_fg=(0.8, 0.8, 0.8, 1),
                pos=(0.7, 0, -0.25)
            )
            
            # Hide by default
            self.dialogue_box.hide()
        
        # Update the dialogue box with new text
        self.npc_name_label["text"] = npc_name
        self.dialogue_text["text"] = dialogue_text
        
        # Show the dialogue box
        self.dialogue_box.show()
    
    def hide_dialogue(self):
        """Hide the dialogue box"""
        if hasattr(self, 'dialogue_box'):
            self.dialogue_box.hide()
    
    def show_travel_menu(self, locations):
        """Show a menu of locations for travel
        
        Args:
            locations: List of dictionaries with location information
                      Each dictionary should have 'id', 'name', and 'description' keys
        """
        # Create a travel menu if it doesn't exist
        if not hasattr(self, 'travel_menu'):
            self.travel_menu = DirectFrame(
                parent=self.ui_root,
                frameColor=(0, 0, 0, 0.9),
                frameSize=(-0.7, 0.7, -0.6, 0.6),
                pos=(0, 0, 0),
                state=DGG.NORMAL,
            )
            
            # Title
            self.travel_title = DirectLabel(
                parent=self.travel_menu,
                text="Travel Destinations",
                text_scale=0.07,
                pos=(0, 0, 0.5),
                text_fg=(1, 1, 1, 1)
            )
            
            # Scrolled frame for location buttons
            self.locations_frame = DirectScrolledFrame(
                parent=self.travel_menu,
                frameSize=(-0.65, 0.65, -0.4, 0.4),
                canvasSize=(-0.6, 0.6, -1.0, 1.0),  # Will be adjusted based on content
                pos=(0, 0, 0),
                scrollBarWidth=0.04,
                verticalScroll_relief=DGG.FLAT,
                verticalScroll_thumb_relief=DGG.FLAT,
                verticalScroll_incButton_relief=DGG.FLAT,
                verticalScroll_decButton_relief=DGG.FLAT,
                horizontalScroll_relief=None  # No horizontal scrollbar
            )
            
            # Close button
            self.close_button = DirectButton(
                parent=self.travel_menu,
                text="Cancel",
                scale=0.05,
                pad=(0.5, 0.2),
                pos=(0, 0, -0.52),
                command=self.hide_travel_menu,
                relief=DGG.FLAT,
                frameColor=(0.3, 0.3, 0.3, 0.7),
                text_fg=(1, 1, 1, 1),
                rolloverSound=None,
                clickSound=None
            )
            
            # Hide by default
            self.travel_menu.hide()
            
            # Store location buttons
            self.location_buttons = []
        
        # Clear existing location buttons
        for button in self.location_buttons:
            button.destroy()
        self.location_buttons = []
        
        # Create a button for each location
        canvas = self.locations_frame.getCanvas()
        for i, location in enumerate(locations):
            y_pos = 0.9 - i * 0.2  # Start from top and move down
            
            button = DirectButton(
                parent=canvas,
                text=location['name'],
                text_scale=0.05,
                text_align=TextNode.ALeft,
                text_pos=(-0.53, 0),
                frameSize=(-0.55, 0.55, -0.08, 0.08),
                pos=(0, 0, y_pos),
                command=self.select_travel_destination,
                extraArgs=[location['id']],
                relief=DGG.FLAT,
                frameColor=(0.2, 0.2, 0.2, 0.7),
                rolloverSound=None,
                clickSound=None
            )
            
            # Add description below the name
            description = DirectLabel(
                parent=button,
                text=location['description'],
                text_scale=0.035,
                text_align=TextNode.ALeft,
                pos=(-0.53, 0, -0.04),
                text_fg=(0.8, 0.8, 0.8, 1)
            )
            
            self.location_buttons.append(button)
        
        # Adjust canvas size based on number of locations
        canvas_height = max(1.0, len(locations) * 0.2 + 0.1)
        self.locations_frame["canvasSize"] = (-0.6, 0.6, -canvas_height, 1.0)
        
        # Show the travel menu
        self.travel_menu.show()
    
    def hide_travel_menu(self):
        """Hide the travel menu"""
        if hasattr(self, 'travel_menu'):
            self.travel_menu.hide()
    
    def select_travel_destination(self, location_id):
        """Handle selection of a travel destination
        
        Args:
            location_id: ID of the selected location
        """
        # Hide the menu
        self.hide_travel_menu()
        
        # Send event with selected location
        messenger.send("travel_selected", [location_id])
