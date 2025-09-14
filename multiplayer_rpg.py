#!/usr/bin/env python3
"""
Multiplayer Asteroid Frontier RPG

Connects the Pygame RPG client to the TextMMO server for true multiplayer experience.
This replaces the standalone RPG with a networked version.
"""

import pygame
import sys
import os
import json
import logging
from typing import Dict, List, Optional

# Import existing RPG systems
from game_structure import GameState, load_image
from character_system import Character, Player as PlayerCharacter
from dialogue_quest_system import DialogueManager
from map_system import Level, Camera, Map
from item_inventory import Inventory, ItemFactory
from network_client import RPGNetworkManager

# Import some constants from the original game
from game_structure import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, WHITE, SPACE_BG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiplayerRPG:
    """
    Main multiplayer RPG class that connects to the TextMMO server.
    Combines the visual Pygame interface with networked multiplayer.
    """

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Asteroid Frontier - Multiplayer")
        self.clock = pygame.time.Clock()

        # Game state
        self.running = True
        self.connected = False
        self.username = ""

        # Local game state (synchronized with server)
        self.player_data = {}
        self.world_state = {}

        # Create RPG player character
        self.player = PlayerCharacter("Player", x=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2)

        # Initialize inventory and game systems
        self.inventory = Inventory(capacity=20)

        # Current location and level for rendering
        self.current_level = None
        self.current_map = None
        self.sprites = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()

        # Load initial map (Rusty Rocket)
        self.load_map("rusty_rocket.csv")
        self.other_players = {}
        self.chat_messages = []

        # UI elements
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.chat_font = pygame.font.Font(None, 20)

        # Network manager
        self.network = RPGNetworkManager(self)

        # Game screens
        self.current_screen = "login"  # login, connecting, game
        self.login_input = ""

        # Game rendering
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.dialogue_manager = DialogueManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Chat system
        self.chat_visible = True
        self.chat_input = ""
        self.chat_input_active = False
        self.max_chat_messages = 10

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        # Cleanup
        if self.connected:
            self.network.disconnect()
        pygame.quit()

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.current_screen == "login":
                    self.handle_login_input(event)
                elif self.current_screen == "game":
                    self.handle_game_input(event)

    def handle_login_input(self, event):
        """Handle login screen input"""
        if event.key == pygame.K_RETURN:
            if len(self.login_input.strip()) >= 2:
                self.username = self.login_input.strip()
                self.attempt_connection()
        elif event.key == pygame.K_BACKSPACE:
            self.login_input = self.login_input[:-1]
        else:
            if len(self.login_input) < 20 and event.unicode.isprintable():
                self.login_input += event.unicode

    def handle_game_input(self, event):
        """Handle in-game input"""
        if event.key == pygame.K_RETURN:
            if self.chat_input_active:
                # Send chat message
                if self.chat_input.strip():
                    self.network.say_message(self.chat_input.strip())
                    self.chat_input = ""
                self.chat_input_active = False
            else:
                # Start chat input
                self.chat_input_active = True
        elif event.key == pygame.K_ESCAPE:
            self.chat_input_active = False
            self.chat_input = ""
        elif self.chat_input_active:
            # Handle chat input
            if event.key == pygame.K_BACKSPACE:
                self.chat_input = self.chat_input[:-1]
            else:
                if len(self.chat_input) < 100 and event.unicode.isprintable():
                    self.chat_input += event.unicode
        else:
            # Handle game movement and actions
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                self.network.move_to_location("north")
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                self.network.move_to_location("south")
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                self.network.move_to_location("west")
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                self.network.move_to_location("east")
            elif event.key == pygame.K_SPACE:
                # Look around
                self.network.client.send_message("player_action", {
                    "action": "look"
                })
            elif event.key == pygame.K_t:
                # Talk to NPCs (for now, try talking to Ruby)
                self.network.talk_to_npc("ruby")

    def attempt_connection(self):
        """Try to connect to the server"""
        self.current_screen = "connecting"
        success = self.network.connect(self.username)

        if success:
            self.connected = True
            self.current_screen = "game"
            logger.info(f"Connected as {self.username}")
        else:
            self.current_screen = "login"
            self.login_input = ""
            logger.error("Failed to connect to server")

    def update(self):
        """Update game state"""
        if self.connected:
            # Process network messages
            self.network.update()

            # Handle smooth movement for visual feedback
            if self.current_screen == "game":
                self.handle_movement()
                # Update camera to follow player
                self.camera.update(self.player)

    def handle_movement(self):
        """Handle smooth local movement with WASD keys"""
        keys = pygame.key.get_pressed()
        move_speed = 200  # pixels per second
        dt = self.clock.get_time() / 1000.0  # delta time in seconds

        moved = False

        # Only move if chat input is not active
        if not self.chat_input_active:
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.player.rect.y -= move_speed * dt
                moved = True
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.player.rect.y += move_speed * dt
                moved = True
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.player.rect.x -= move_speed * dt
                moved = True
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.player.rect.x += move_speed * dt
                moved = True

            # Keep player within reasonable bounds
            world_rect = pygame.Rect(0, 0, SCREEN_WIDTH - 300, SCREEN_HEIGHT)
            if self.player.rect.left < 0:
                self.player.rect.left = 0
            if self.player.rect.right > world_rect.width:
                self.player.rect.right = world_rect.width
            if self.player.rect.top < 0:
                self.player.rect.top = 0
            if self.player.rect.bottom > world_rect.height:
                self.player.rect.bottom = world_rect.height

    def render(self):
        """Render the current screen"""
        self.screen.fill(SPACE_BG)

        if self.current_screen == "login":
            self.render_login_screen()
        elif self.current_screen == "connecting":
            self.render_connecting_screen()
        elif self.current_screen == "game":
            self.render_game_screen()

        pygame.display.flip()

    def render_login_screen(self):
        """Render login screen"""
        # Title
        title = self.font.render("Asteroid Frontier - Multiplayer", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # Username prompt
        prompt = self.small_font.render("Enter username:", True, WHITE)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(prompt, prompt_rect)

        # Username input
        input_text = self.small_font.render(self.login_input + "_", True, WHITE)
        input_rect = input_text.get_rect(center=(SCREEN_WIDTH // 2, 330))
        self.screen.blit(input_text, input_rect)

        # Instructions
        instruction = self.small_font.render("Press Enter to connect", True, WHITE)
        instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(instruction, instruction_rect)

    def render_connecting_screen(self):
        """Render connecting screen"""
        connecting = self.font.render("Connecting to server...", True, WHITE)
        connecting_rect = connecting.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(connecting, connecting_rect)

    def render_game_screen(self):
        """Render main game screen with RPG-style graphics"""
        # Clear screen with space background
        self.screen.fill(SPACE_BG)

        # Game world area (main RPG view)
        world_rect = pygame.Rect(0, 0, SCREEN_WIDTH - 300, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, SPACE_BG, world_rect)

        # Render the current level/location
        self.render_rpg_world(world_rect)

        # Render player character
        self.render_player()

        # Render other players and NPCs
        self.render_other_entities()

        # UI panel
        ui_rect = pygame.Rect(SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (10, 10, 20), ui_rect)
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH - 300, 0), (SCREEN_WIDTH - 300, SCREEN_HEIGHT))

        # Render RPG UI elements
        self.render_rpg_ui(ui_rect)
        self.render_chat(ui_rect)
        self.render_controls(ui_rect)

    def render_location(self, rect):
        """Render the current location"""
        if not self.world_state.get("current_location"):
            return

        location = self.world_state["current_location"]

        # Location name
        name_text = self.font.render(location.get("name", "Unknown Location"), True, WHITE)
        self.screen.blit(name_text, (rect.x + 10, rect.y + 10))

        # Location description (wrapped text)
        description = location.get("description", "")
        self.render_wrapped_text(description, rect.x + 10, rect.y + 50, rect.width - 20, self.small_font, WHITE)

        # Characters in location
        characters = location.get("characters", [])
        if characters:
            char_y = rect.y + 200
            char_text = self.small_font.render("Characters here:", True, WHITE)
            self.screen.blit(char_text, (rect.x + 10, char_y))
            for i, char in enumerate(characters):
                char_name = self.small_font.render(f"  {char}", True, (200, 200, 255))
                self.screen.blit(char_name, (rect.x + 20, char_y + 20 + i * 20))

        # Other players
        if self.other_players:
            player_y = rect.y + 300
            players_text = self.small_font.render("Other players:", True, WHITE)
            self.screen.blit(players_text, (rect.x + 10, player_y))
            for i, player in enumerate(self.other_players):
                player_name = self.small_font.render(f"  {player.get('name', 'Unknown')}", True, (255, 200, 200))
                self.screen.blit(player_name, (rect.x + 20, player_y + 20 + i * 20))

    def render_player_info(self, rect):
        """Render player information"""
        y = rect.y + 10

        # Player name
        name = self.small_font.render(f"Player: {self.username}", True, WHITE)
        self.screen.blit(name, (rect.x + 10, y))
        y += 25

        # Player stats
        if self.player_data:
            level_text = self.small_font.render(f"Level: {self.player_data.get('level', 1)}", True, WHITE)
            self.screen.blit(level_text, (rect.x + 10, y))
            y += 20

            health_text = self.small_font.render(f"Health: {self.player_data.get('health', 100)}", True, WHITE)
            self.screen.blit(health_text, (rect.x + 10, y))
            y += 20

            credits_text = self.small_font.render(f"Credits: {self.player_data.get('credits', 1000)}", True, WHITE)
            self.screen.blit(credits_text, (rect.x + 10, y))

    def render_chat(self, rect):
        """Render chat messages"""
        chat_y = rect.y + rect.height - 200

        # Chat header
        chat_header = self.small_font.render("Chat:", True, WHITE)
        self.screen.blit(chat_header, (rect.x + 10, chat_y - 25))

        # Chat messages
        for i, (speaker, message) in enumerate(self.chat_messages[-self.max_chat_messages:]):
            color = (200, 255, 200) if speaker != self.username else (255, 255, 200)
            msg_text = f"{speaker}: {message}"
            if len(msg_text) > 35:
                msg_text = msg_text[:32] + "..."
            chat_line = self.chat_font.render(msg_text, True, color)
            self.screen.blit(chat_line, (rect.x + 10, chat_y + i * 15))

        # Chat input
        if self.chat_input_active:
            input_prompt = self.chat_font.render(f"Say: {self.chat_input}_", True, WHITE)
            self.screen.blit(input_prompt, (rect.x + 10, chat_y + 150))

    def render_controls(self, rect):
        """Render control instructions"""
        controls_y = rect.y + rect.height - 100

        controls = [
            "Controls:",
            "WASD - Move",
            "Space - Look",
            "T - Talk to Ruby",
            "Enter - Chat"
        ]

        for i, control in enumerate(controls):
            color = WHITE if i == 0 else (180, 180, 180)
            control_text = self.chat_font.render(control, True, color)
            self.screen.blit(control_text, (rect.x + 10, controls_y + i * 15))

    def render_wrapped_text(self, text, x, y, max_width, font, color):
        """Render text with word wrapping"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        for i, line in enumerate(lines):
            line_text = font.render(line, True, color)
            self.screen.blit(line_text, (x, y + i * font.get_height()))

    def render_rpg_world(self, rect):
        """Render the RPG world view with actual map tiles"""
        if self.current_map:
            # Render all map sprites with camera offset
            for sprite_group in [self.current_map.floor_tiles, self.current_map.walls,
                               self.current_map.objects, self.current_map.doors]:
                for sprite in sprite_group:
                    # Apply camera offset
                    screen_pos = self.camera.apply(sprite)
                    if screen_pos.colliderect(rect):
                        self.screen.blit(sprite.image, screen_pos)
        else:
            # Fallback to simple floor color if no map loaded
            floor_color = (40, 40, 50)
            pygame.draw.rect(self.screen, floor_color, rect)

        # Render location name in top-left
        if self.world_state.get("current_location"):
            location = self.world_state["current_location"]
            name_text = self.font.render(location.get("name", "Unknown Location"), True, WHITE)
            self.screen.blit(name_text, (rect.x + 10, rect.y + 10))

    def render_player(self):
        """Render the player character"""
        # Apply camera offset to player position
        screen_x = self.player.rect.x + self.camera.camera.x
        screen_y = self.player.rect.y + self.camera.camera.y

        # Only render if player is on screen
        if (0 <= screen_x < SCREEN_WIDTH - 300 and 0 <= screen_y < SCREEN_HEIGHT):
            # Draw player as a blue circle for now
            # Later we'll use actual sprites
            pygame.draw.circle(self.screen, (0, 100, 255),
                             (int(screen_x + 16), int(screen_y + 16)), 16)

            # Draw username above player
            if self.username:
                name_text = self.small_font.render(self.username, True, WHITE)
                name_rect = name_text.get_rect(center=(screen_x + 16, screen_y - 10))
                self.screen.blit(name_text, name_rect)

    def render_other_entities(self):
        """Render other players and NPCs"""
        # Render NPCs (Ruby, CV, etc.)
        if self.world_state.get("npcs"):
            for npc_name, npc_data in self.world_state["npcs"].items():
                # Draw NPCs as red circles
                npc_x = npc_data.get("x", 0) + self.camera.camera.x
                npc_y = npc_data.get("y", 0) + self.camera.camera.y

                if (0 <= npc_x < SCREEN_WIDTH - 300 and 0 <= npc_y < SCREEN_HEIGHT):
                    pygame.draw.circle(self.screen, (255, 50, 50),
                                     (int(npc_x + 16), int(npc_y + 16)), 16)

                    # Draw NPC name
                    name_text = self.small_font.render(npc_name, True, WHITE)
                    name_rect = name_text.get_rect(center=(npc_x + 16, npc_y - 10))
                    self.screen.blit(name_text, name_rect)

        # Render other players
        if self.world_state.get("other_players"):
            for player_name, player_data in self.world_state["other_players"].items():
                # Draw other players as green circles
                player_x = player_data.get("x", 0) + self.camera.camera.x
                player_y = player_data.get("y", 0) + self.camera.camera.y

                if (0 <= player_x < SCREEN_WIDTH - 300 and 0 <= player_y < SCREEN_HEIGHT):
                    pygame.draw.circle(self.screen, (50, 255, 50),
                                     (int(player_x + 16), int(player_y + 16)), 16)

                    # Draw player name
                    name_text = self.small_font.render(player_name, True, WHITE)
                    name_rect = name_text.get_rect(center=(player_x + 16, player_y - 10))
                    self.screen.blit(name_text, name_rect)

    def render_rpg_ui(self, rect):
        """Render RPG-style UI elements"""
        y_offset = 10

        # Player stats
        stats_title = self.font.render("Player Status", True, WHITE)
        self.screen.blit(stats_title, (rect.x + 10, y_offset))
        y_offset += 40

        # Health/Status (placeholder)
        health_text = self.small_font.render(f"Health: 100/100", True, WHITE)
        self.screen.blit(health_text, (rect.x + 10, y_offset))
        y_offset += 25

        credits_text = self.small_font.render(f"Credits: {self.player_data.get('credits', 0)}", True, WHITE)
        self.screen.blit(credits_text, (rect.x + 10, y_offset))
        y_offset += 40

        # Location info
        location_title = self.font.render("Location", True, WHITE)
        self.screen.blit(location_title, (rect.x + 10, y_offset))
        y_offset += 25

        if self.world_state.get("current_location"):
            location = self.world_state["current_location"]
            # Render location description (wrapped)
            desc = location.get("description", "")[:100] + "..." if len(location.get("description", "")) > 100 else location.get("description", "")
            self.render_wrapped_text(desc, rect.x + 10, y_offset, rect.width - 20, self.small_font, WHITE)
            y_offset += 80

        # Inventory preview
        inv_title = self.font.render("Inventory", True, WHITE)
        self.screen.blit(inv_title, (rect.x + 10, y_offset))
        y_offset += 25

        # Show first few inventory items
        items = self.player_data.get("inventory", [])
        for i, item in enumerate(items[:5]):
            item_text = self.small_font.render(f"• {item}", True, WHITE)
            self.screen.blit(item_text, (rect.x + 10, y_offset))
            y_offset += 20

    def render_chat(self, rect):
        """Render chat messages"""
        # Chat area at bottom of UI panel
        chat_rect = pygame.Rect(rect.x + 5, rect.y + rect.height - 200, rect.width - 10, 180)
        pygame.draw.rect(self.screen, (20, 20, 30), chat_rect)
        pygame.draw.rect(self.screen, WHITE, chat_rect, 1)

        # Chat title
        chat_title = self.small_font.render("Chat", True, WHITE)
        self.screen.blit(chat_title, (chat_rect.x + 5, chat_rect.y + 5))

        # Render recent chat messages
        y_pos = chat_rect.y + 25
        for i, (speaker, message) in enumerate(self.chat_messages[-6:]):  # Show last 6 messages
            # Truncate long messages
            if len(message) > 30:
                message = message[:27] + "..."

            chat_line = f"{speaker}: {message}"
            chat_text = self.chat_font.render(chat_line, True, WHITE)
            self.screen.blit(chat_text, (chat_rect.x + 5, y_pos))
            y_pos += 20

        # Chat input field if active
        if self.chat_input_active:
            input_rect = pygame.Rect(chat_rect.x + 5, chat_rect.y + chat_rect.height - 25, chat_rect.width - 10, 20)
            pygame.draw.rect(self.screen, (30, 30, 40), input_rect)
            pygame.draw.rect(self.screen, WHITE, input_rect, 1)

            input_text = f"Say: {self.chat_input}_"
            input_surface = self.chat_font.render(input_text, True, WHITE)
            self.screen.blit(input_surface, (input_rect.x + 3, input_rect.y + 2))

    def render_controls(self, rect):
        """Render control instructions"""
        controls_y = rect.y + rect.height - 220

        controls_title = self.small_font.render("Controls:", True, WHITE)
        self.screen.blit(controls_title, (rect.x + 10, controls_y))

        controls = [
            "WASD: Move",
            "Enter: Chat",
            "T: Talk to NPC",
            "Space: Look"
        ]

        for i, control in enumerate(controls):
            control_text = self.chat_font.render(control, True, (180, 180, 180))
            self.screen.blit(control_text, (rect.x + 10, controls_y + 20 + i * 15))

    # Network callback methods
    def update_world_state(self, world_state):
        """Called when world state is updated from server"""
        self.world_state = world_state

    def update_player_state(self, player_data):
        """Called when player state is updated from server"""
        self.player_data = player_data

    def add_chat_message(self, speaker, message):
        """Add a chat message to the display"""
        self.chat_messages.append((speaker, message))
        if len(self.chat_messages) > 50:  # Keep chat history reasonable
            self.chat_messages = self.chat_messages[-50:]

    def add_system_message(self, message):
        """Add a system message"""
        self.add_chat_message("System", message)

    def start_dialogue(self, character_name, dialogue_text):
        """Start a dialogue with an NPC"""
        # For now, show dialogue in chat and also trigger visual dialogue
        self.add_chat_message(character_name, dialogue_text)

        # TODO: Integrate with visual DialogueManager for full dialogue system
        # For MVP, just show it prominently in chat
        logger.info(f"Started dialogue with {character_name}: {dialogue_text}")

    def load_map(self, map_filename):
        """Load a map file for rendering"""
        try:
            self.current_map = Map(map_filename, 32)  # 32 pixel tiles

            # Set player position to map's starting position or default
            if hasattr(self.current_map, 'start_x') and hasattr(self.current_map, 'start_y'):
                self.player.rect.x = self.current_map.start_x
                self.player.rect.y = self.current_map.start_y
            else:
                # Default to center of map
                self.player.rect.x = 13 * 32  # Column 13 (@ position in map)
                self.player.rect.y = 27 * 32  # Row 27 (@ position in map)

            logger.info(f"Loaded map: {map_filename}")

        except Exception as e:
            logger.error(f"Failed to load map {map_filename}: {e}")
            self.current_map = None


def main():
    """Main entry point"""
    try:
        game = MultiplayerRPG()
        game.run()
    except Exception as e:
        logger.error(f"Game error: {e}")
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()