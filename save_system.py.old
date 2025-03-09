import json
import os
import datetime
import pygame
from pathlib import Path



class SaveSystem:
    def __init__(self, game):
        """Initialize the save system with reference to the main game"""
        self.game = game
        self.save_folder = 'saves'
        
        # Create saves directory if it doesn't exist
        Path(self.save_folder).mkdir(exist_ok=True)
    
    def create_save_data(self):
        """Create a dictionary containing all game state data to be saved"""
        save_data = {
            # Meta information
            "meta": {
                "version": "0.1",
                "timestamp": datetime.datetime.now().isoformat(),
                "save_name": f"save_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            },
            
            # Player data
            "player": {
                "position": {
                    "x": self.game.player.rect.x,
                    "y": self.game.player.rect.y
                },
                "health": self.game.player.health,
                "max_health": getattr(self.game.player, 'max_health', 100),
                "credits": getattr(self.game.player, 'credits', 0),
                # Add other player attributes here
            },
            
            # Current location
            "current_location": {
                "id": self.game.current_level.get("name", "psyche_township") if self.game.current_level else "psyche_township",
                "docked_location": getattr(self.game, 'docked_location', None)
            },
            
            # Ship data
            "ship": {
                # Get ship attributes from space travel if it exists
                "hull_strength": getattr(self.game.space_travel, 'ship', {}).hull_strength if hasattr(self.game, 'space_travel') and hasattr(self.game.space_travel, 'ship') else 100,
                "shield_strength": getattr(self.game.space_travel, 'ship', {}).shield_strength if hasattr(self.game, 'space_travel') and hasattr(self.game.space_travel, 'ship') else 0,
                "thrust_power": getattr(self.game.space_travel, 'thrust_power', 0.1) if hasattr(self.game, 'space_travel') else 0.1,
                "rotation_speed": getattr(self.game.space_travel, 'rotation_speed', 3) if hasattr(self.game, 'space_travel') else 3,
                "max_speed": getattr(self.game.space_travel, 'max_speed', 5) if hasattr(self.game, 'space_travel') else 5,
                # Add other ship attributes
            },
            
            # Inventory (simplified for now)
            "inventory": {
                "credits": getattr(self.game.player, 'credits', 0),
                "items": [] # We'll expand this
            },
            
            # Game state flags 
            "game_flags": {
                # You can add any flags or variables that track game progress
                "tutorial_completed": getattr(self.game, 'tutorial_completed', False),
                # Add other flags
            },
            
            # Visited locations
            "visited_locations": getattr(self.game, 'visited_locations', []),
            
            # Space resources collected (for future)
            "resources": {
                "metal": 0,
                "crystal": 0,
                "fuel": 0,
                # Add other resources
            }
        }
        
        return save_data

    def save_game(self, save_name=None):
        """Save the current game state to a file"""
        # Create the save data
        save_data = self.create_save_data()
        
        # Use provided save name or generate one
        if save_name:
            save_data["meta"]["save_name"] = save_name
        
        # Generate filename
        filename = f"{save_data['meta']['save_name']}.json"
        save_path = os.path.join(self.save_folder, filename)
        
        try:
            # Write to file
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"Game saved successfully to {save_path}")
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game(self, filename):
        """Load a game state from a file"""
        save_path = os.path.join(self.save_folder, filename)
        
        if not os.path.exists(save_path):
            print(f"Save file not found: {save_path}")
            return False
        
        try:
            # Read the save file
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Apply the loaded data to restore game state
            self.apply_save_data(save_data)
            
            print(f"Game loaded successfully from {save_path}")
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False

    def apply_save_data(self, save_data):
        """Apply loaded save data to the game state"""
        # Restore player data
        if "player" in save_data:
            # Position
            if "position" in save_data["player"]:
                self.game.player.rect.x = save_data["player"]["position"]["x"]
                self.game.player.rect.y = save_data["player"]["position"]["y"]
            
            # Stats
            self.game.player.health = save_data["player"].get("health", 100)
            if hasattr(self.game.player, 'max_health'):
                self.game.player.max_health = save_data["player"].get("max_health", 100)
            
            # Money
            if hasattr(self.game.player, 'credits'):
                self.game.player.credits = save_data["player"].get("credits", 0)
        
        # Restore current location
        if "current_location" in save_data:
            location_id = save_data["current_location"]["id"]
            
            # Set docked location if applicable
            if "docked_location" in save_data["current_location"] and save_data["current_location"]["docked_location"]:
                self.game.docked_location = save_data["current_location"]["docked_location"]
            
            # Load the location
            self.game.load_location(location_id)
        
        # Restore ship data if space travel exists
        if "ship" in save_data and hasattr(self.game, 'space_travel') and hasattr(self.game.space_travel, 'ship'):
            # Ship stats
            self.game.space_travel.ship.hull_strength = save_data["ship"].get("hull_strength", 100)
            self.game.space_travel.ship.shield_strength = save_data["ship"].get("shield_strength", 0)
            
            # Movement properties
            self.game.space_travel.thrust_power = save_data["ship"].get("thrust_power", 0.1)
            self.game.space_travel.rotation_speed = save_data["ship"].get("rotation_speed", 3)
            self.game.space_travel.max_speed = save_data["ship"].get("max_speed", 5)
        
        # Restore game flags
        if "game_flags" in save_data:
            for flag, value in save_data["game_flags"].items():
                setattr(self.game, flag, value)
        
        # Restore visited locations
        if "visited_locations" in save_data:
            self.game.visited_locations = save_data["visited_locations"]
        
        # Set game state to OVERWORLD after loading
        self.game.game_state = GameState.OVERWORLD

    def get_available_saves(self):
        """Get a list of available save files"""
        saves = []
        
        # Check each file in the saves directory
        for filename in os.listdir(self.save_folder):
            if filename.endswith('.json'):
                try:
                    # Read basic metadata
                    save_path = os.path.join(self.save_folder, filename)
                    with open(save_path, 'r') as f:
                        save_data = json.load(f)
                    
                    # Extract useful info
                    save_info = {
                        "filename": filename,
                        "save_name": save_data["meta"].get("save_name", filename),
                        "timestamp": save_data["meta"].get("timestamp", "Unknown"),
                        "location": save_data["current_location"].get("id", "Unknown"),
                        "credits": save_data["player"].get("credits", 0)
                    }
                    
                    saves.append(save_info)
                except:
                    # If there's an error reading the file, just use the filename
                    saves.append({
                        "filename": filename,
                        "save_name": filename,
                        "timestamp": "Error reading save",
                        "location": "Unknown",
                        "credits": 0
                    })
        
        # Sort by timestamp (newest first)
        saves.sort(key=lambda x: x["timestamp"], reverse=True)
        return saves

    def quick_save(self):
        """Perform a quick save"""
        save_name = "quicksave"
        return self.save_game(save_name)

    def quick_load(self):
        """Load the most recent quicksave"""
        saves = self.get_available_saves()
        
        # Find quicksave files
        quicksaves = [save for save in saves if save["save_name"] == "quicksave"]
        
        if quicksaves:
            # Sort by timestamp and load the most recent
            quicksaves.sort(key=lambda x: x["timestamp"], reverse=True)
            return self.load_game(quicksaves[0]["filename"])
        else:
            print("No quicksave found")
            return False

# Example method to add to your main game class to use the save system
def add_save_system(self):
    """Add the save system to the game"""
    self.save_system = SaveSystem(self)
    
    # Track visited locations
    if not hasattr(self, 'visited_locations'):
        self.visited_locations = []
    
    # Add the current location to visited if not already there
    if self.current_level and "name" in self.current_level:
        location_id = self.current_level["name"]
        if location_id not in self.visited_locations:
            self.visited_locations.append(location_id)

# Extend handle_events to include save/load hotkeys
def handle_save_load_events(self, event):
    """Handle save/load keyboard shortcuts"""
    if event.type == pygame.KEYDOWN:
        # F5 for quicksave
        if event.key == pygame.K_F5:
            self.save_system.quick_save()
            
        # F9 for quickload
        elif event.key == pygame.K_F9:
            self.save_system.quick_load()
            
        # F6 to show save menu
        elif event.key == pygame.K_F6:
            self.game_state = GameState.SAVE_MENU
            
        # F7 to show load menu
        elif event.key == pygame.K_F7:
            self.game_state = GameState.LOAD_MENU



class SaveLoadMenu:
    def __init__(self, screen_width, screen_height):
        """Initialize the save/load menu system"""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 24)
        
        # Menu state
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 8
        self.save_items = []
        
        # Input for new save name
        self.input_active = False
        self.input_text = ""
        self.max_input_length = 20
    
    def handle_event(self, event, game):
        """Handle events for the save/load menu"""
        if event.type == pygame.KEYDOWN:
            # Cancel menu with Escape
            if event.key == pygame.K_ESCAPE:
                game.game_state = GameState.OVERWORLD
                return True
            
            # Input handling for save name
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    # Save with current name
                    if self.input_text:
                        game.save_system.save_game(self.input_text)
                        self.input_active = False
                        self.input_text = ""
                        self.refresh_save_list(game)
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    # Add character if it's valid and not too long
                    if event.unicode.isprintable() and len(self.input_text) < self.max_input_length:
                        self.input_text += event.unicode
                return True
            
            # Navigation
            if event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
                # Scroll up if needed
                if self.selected_index < self.scroll_offset:
                    self.scroll_offset = self.selected_index
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.save_items) - 1, self.selected_index + 1) if self.save_items else 0
                # Scroll down if needed
                if self.selected_index >= self.scroll_offset + self.max_visible_items:
                    self.scroll_offset = self.selected_index - self.max_visible_items + 1
            
            # Perform action on selection
            elif event.key == pygame.K_RETURN:
                if game.game_state == GameState.SAVE_MENU:
                    # If "New Save" is selected
                    if self.selected_index == 0:
                        self.input_active = True
                        self.input_text = ""
                    else:
                        # Overwrite existing save
                        selected_save = self.save_items[self.selected_index - 1]  # -1 because "New Save" is at index 0
                        game.save_system.save_game(selected_save["save_name"])
                        self.refresh_save_list(game)
                
                elif game.game_state == GameState.LOAD_MENU and self.save_items:
                    # Load selected save
                    selected_save = self.save_items[self.selected_index]
                    game.save_system.load_game(selected_save["filename"])
                    game.game_state = GameState.OVERWORLD
        
        return True
    
    def refresh_save_list(self, game):
        """Refresh the list of save files"""
        self.save_items = game.save_system.get_available_saves()
    
        # Get the current game state value
        is_save_menu = game.game_state == 9  # 9 is SAVE_MENU
    
        # Reset selection if out of bounds
        if self.selected_index >= len(self.save_items) + (1 if is_save_menu else 0):
            self.selected_index = 0
            self.scroll_offset = 0
    
    def draw(self, screen, game):
        """Draw the save/load menu"""
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with alpha
        screen.blit(overlay, (0, 0))
        
        # Draw menu panel
        panel_width = self.screen_width - 200
        panel_height = self.screen_height - 150
        panel_rect = pygame.Rect(100, 75, panel_width, panel_height)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect)
        pygame.draw.rect(screen, (200, 200, 200), panel_rect, 2)
        
        # Draw title
        if game.game_state == GameState.SAVE_MENU:
            title = self.font_large.render("Save Game", True, (255, 255, 255))
        else:  # LOAD_MENU
            title = self.font_large.render("Load Game", True, (255, 255, 255))
        
        screen.blit(title, (panel_rect.centerx - title.get_width() // 2, panel_rect.y + 20))
        
        # Draw save items
        item_y = panel_rect.y + 80
        
        # For save menu, add "New Save" option at the top
        if game.game_state == GameState.SAVE_MENU:
            # Highlight if selected
            if self.selected_index == 0:
                new_save_rect = pygame.Rect(panel_rect.x + 20, item_y - 5, panel_width - 40, 40)
                pygame.draw.rect(screen, (70, 70, 100), new_save_rect)
            
            new_save_text = self.font.render("Create New Save", True, (255, 255, 255))
            screen.blit(new_save_text, (panel_rect.x + 30, item_y))
            item_y += 50
        
        # Display active saves with scrolling
        visible_saves = self.save_items[self.scroll_offset:self.scroll_offset + self.max_visible_items]
        
        for i, save in enumerate(visible_saves):
            # Calculate actual index in the full list
            actual_index = i + self.scroll_offset
            
            # Adjust for "New Save" option in save menu
            selection_index = actual_index + 1 if game.game_state == GameState.SAVE_MENU else actual_index
            
            # Highlight if selected
            if self.selected_index == selection_index:
                save_rect = pygame.Rect(panel_rect.x + 20, item_y - 5, panel_width - 40, 50)
                pygame.draw.rect(screen, (70, 70, 100), save_rect)
            
            # Format date/time from timestamp
            try:
                dt = datetime.datetime.fromisoformat(save["timestamp"])
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_str = save["timestamp"]
            
            # Draw save info
            save_name = self.font.render(save["save_name"], True, (255, 255, 255))
            details = self.font_small.render(
                f"Location: {save['location'].replace('_', ' ').title()} | Credits: {save['credits']} | {timestamp_str}", 
                True, (200, 200, 200)
            )
            
            screen.blit(save_name, (panel_rect.x + 30, item_y))
            screen.blit(details, (panel_rect.x + 30, item_y + 25))
            
            item_y += 60
        
        # Draw scroll indicators if needed
        if self.scroll_offset > 0:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (panel_rect.centerx - 10, panel_rect.y + 60),
                (panel_rect.centerx + 10, panel_rect.y + 60),
                (panel_rect.centerx, panel_rect.y + 50)
            ])
        
        max_offset = max(0, len(self.save_items) - self.max_visible_items)
        if self.scroll_offset < max_offset:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (panel_rect.centerx - 10, panel_rect.bottom - 20),
                (panel_rect.centerx + 10, panel_rect.bottom - 20),
                (panel_rect.centerx, panel_rect.bottom - 10)
            ])
        
        # Draw save name input if active
        if self.input_active:
            input_rect = pygame.Rect(panel_rect.x + 100, panel_rect.centery, 400, 40)
            pygame.draw.rect(screen, (30, 30, 30), input_rect)
            pygame.draw.rect(screen, (150, 150, 150), input_rect, 2)
            
            prompt = self.font.render("Enter save name:", True, (255, 255, 255))
            screen.blit(prompt, (input_rect.x - 90, input_rect.y + 10))
            
            input_surface = self.font.render(self.input_text, True, (255, 255, 255))
            screen.blit(input_surface, (input_rect.x + 10, input_rect.y + 10))
            
            # Draw blinking cursor
            if pygame.time.get_ticks() % 1000 < 500:
                cursor_x = input_rect.x + 10 + input_surface.get_width()
                pygame.draw.line(screen, (255, 255, 255), 
                               (cursor_x, input_rect.y + 5), 
                               (cursor_x, input_rect.y + 35), 2)
        
        # Draw controls hint
        if not self.input_active:
            controls = self.font_small.render(
                "↑/↓: Navigate | Enter: Select | Esc: Cancel", 
                True, (200, 200, 200)
            )
            screen.blit(controls, (panel_rect.centerx - controls.get_width() // 2, panel_rect.bottom - 30))