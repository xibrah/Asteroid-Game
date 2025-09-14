"""
Simple Text Dialogue System for AI Conversations

Provides open-ended text input without requiring pygame_gui
"""

import pygame
import pygame.freetype
from ai_bridge import get_ai_bridge
from game_logger import log_ai_interaction
import re

class SimpleTextDialogue:
    """
    Simple text-based dialogue system for AI conversations.
    Uses basic pygame for text input and display.
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Dialogue state
        self.active_ai_character = None
        self.conversation_history = []
        self.is_active = False
        self.current_input = ""

        # Fonts
        try:
            pygame.freetype.init()
            self.font = pygame.freetype.Font(None, 20)
            self.name_font = pygame.freetype.Font(None, 24)
        except:
            self.font = pygame.font.Font(None, 20)
            self.name_font = pygame.font.Font(None, 24)

        # UI styling
        self.bg_color = (20, 20, 40)
        self.border_color = (100, 100, 150)
        self.text_color = (255, 255, 255)
        self.player_color = (150, 255, 150)
        self.ai_color = (255, 200, 100)
        self.input_color = (50, 50, 80)

        # AI Bridge
        self.ai_bridge = get_ai_bridge()

        # Input state
        self.input_active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def start_conversation(self, ai_character, player, game=None):
        """Start an open-ended conversation with an AI character"""
        self.active_ai_character = ai_character
        self.player = player
        self.game = game  # Reference to main game for triggering actions
        self.is_active = True
        self.conversation_history = []
        self.current_input = ""
        self.input_active = True

        # Get initial AI greeting
        initial_response = ai_character.talk_to_player(player.name)
        self._add_to_conversation("AI", ai_character.name, initial_response)

        log_ai_interaction(ai_character.name, player.name, "[conversation started]", initial_response)

        print(f"🤖 Started simple text conversation with {ai_character.name}")

    def _add_to_conversation(self, speaker_type, speaker_name, message):
        """Add a message to the conversation history"""
        self.conversation_history.append({
            'type': speaker_type,  # 'Player' or 'AI'
            'name': speaker_name,
            'message': message,
            'timestamp': pygame.time.get_ticks()
        })

        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)

    def handle_event(self, event):
        """Handle events for the dialogue system"""
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.end_conversation()
                return True

            elif event.key == pygame.K_RETURN:
                if self.current_input.strip():
                    self._send_message()
                return True

            elif event.key == pygame.K_BACKSPACE:
                if self.current_input:
                    self.current_input = self.current_input[:-1]
                return True

            elif event.unicode and len(self.current_input) < 200:
                # Add character to input
                if event.unicode.isprintable():
                    self.current_input += event.unicode
                return True

        return False

    def _send_message(self):
        """Send player's message to AI and get response"""
        player_message = self.current_input.strip()
        self.current_input = ""

        # Add player message to history
        self._add_to_conversation("Player", self.player.name, player_message)

        # Get AI response
        if self.active_ai_character:
            ai_response = self.active_ai_character.talk_to_player(self.player.name, player_message)
            self._add_to_conversation("AI", self.active_ai_character.name, ai_response)

            # Log the interaction
            log_ai_interaction(self.active_ai_character.name, self.player.name, player_message, ai_response)

            # Parse for actions
            actions = self._parse_for_actions(player_message, ai_response)
            if actions:
                self._execute_actions(actions)

    def _parse_for_actions(self, player_message, ai_response):
        """Parse player message and AI response for actionable commands"""
        actions = []

        player_lower = player_message.lower()
        ai_lower = ai_response.lower()

        # Shop/merchant requests
        shop_triggers = ['menu', 'shop', 'buy', 'sell', 'wares', 'goods', 'inventory', 'what do you have', 'for sale', 'store']
        if any(trigger in player_lower for trigger in shop_triggers):
            actions.append({'type': 'show_shop', 'trigger': 'player_request'})

        # AI offering to show shop
        if any(phrase in ai_lower for phrase in ['let me show you my menu', 'here\'s what i have', 'take a look at']):
            actions.append({'type': 'show_shop', 'trigger': 'ai_offer'})

        # Quest/work requests
        quest_triggers = ['job', 'work', 'quest', 'task', 'mission', 'favor', 'help']
        if any(trigger in player_lower for trigger in quest_triggers):
            actions.append({'type': 'quest_offer', 'trigger': 'player_request'})

        return actions

    def _execute_actions(self, actions):
        """Execute parsed actions"""
        for action in actions:
            if action['type'] == 'show_shop':
                self._trigger_merchant_gui()
            elif action['type'] == 'quest_offer':
                self._trigger_quest_system()

            print(f"🎮 Triggered action: {action['type']} from {action['trigger']}")

    def _trigger_merchant_gui(self):
        """Trigger the merchant GUI"""
        if self.game and hasattr(self.game, 'merchant_system'):
            print(f"🛒 Opening merchant GUI for {self.active_ai_character.name}")
            # Set up merchant interaction
            self.game.merchant_system.current_merchant = self.active_ai_character
            # Switch to merchant game state
            from game_structure import GameState
            self.game.game_state = GameState.MERCHANT
            # Close dialogue to show shop
            self.is_active = False
        else:
            print(f"🛒 Merchant system not available")

    def _trigger_quest_system(self):
        """Trigger the quest system"""
        print(f"📋 Quest system integration not yet implemented")

    def update(self, dt):
        """Update the dialogue system"""
        if self.is_active:
            # Update cursor blink
            self.cursor_timer += dt * 1000  # Convert to milliseconds
            if self.cursor_timer > 500:  # Blink every 500ms
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0

    def draw(self, surface):
        """Draw the simple text dialogue interface"""
        if not self.is_active:
            return

        # Calculate dialogue panel dimensions
        panel_width = self.screen_width - 100
        panel_height = 400
        panel_x = 50
        panel_y = self.screen_height - panel_height - 50

        # Draw main dialogue panel
        dialogue_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, self.bg_color, dialogue_rect)
        pygame.draw.rect(surface, self.border_color, dialogue_rect, 3)

        # Draw character name
        if self.active_ai_character:
            name_text = f"🤖 Conversation with {self.active_ai_character.name}"
            self._draw_text(surface, name_text, panel_x + 20, panel_y + 10, self.name_font, (255, 255, 255))

        # Draw conversation history
        history_y = panel_y + 40
        history_height = 280
        self._draw_conversation_history(surface, panel_x + 20, history_y, panel_width - 40, history_height)

        # Draw input area
        input_y = panel_y + panel_height - 60
        self._draw_input_area(surface, panel_x + 20, input_y, panel_width - 40, 40)

        # Draw instructions
        instructions = "Type your message and press Enter. Press Esc to close."
        self._draw_text(surface, instructions, panel_x + 20, panel_y + panel_height - 20, self.font, (180, 180, 180))

    def _draw_conversation_history(self, surface, x, y, width, height):
        """Draw the conversation history"""
        if not self.conversation_history:
            return

        line_height = 25
        max_lines = height // line_height
        y_offset = 0

        # Show recent messages that fit in the area
        visible_messages = []
        for msg in reversed(self.conversation_history):
            # Wrap long messages
            text = f"{msg['name']}: {msg['message']}"
            wrapped_lines = self._wrap_text(text, width - 20)

            for line in reversed(wrapped_lines):
                visible_messages.insert(0, {
                    'line': line,
                    'type': msg['type']
                })

                if len(visible_messages) >= max_lines:
                    break

            if len(visible_messages) >= max_lines:
                break

        # Draw messages
        for i, msg in enumerate(visible_messages):
            if i >= max_lines:
                break

            color = self.player_color if msg['type'] == 'Player' else self.ai_color
            self._draw_text(surface, msg['line'], x + 10, y + i * line_height, self.font, color)

    def _draw_input_area(self, surface, x, y, width, height):
        """Draw the text input area"""
        # Input box
        input_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.input_color, input_rect)
        pygame.draw.rect(surface, self.border_color, input_rect, 2)

        # Input text
        display_text = self.current_input
        if self.cursor_visible:
            display_text += "|"

        self._draw_text(surface, display_text, x + 10, y + 10, self.font, self.text_color)

        # Prompt
        prompt = "You: "
        self._draw_text(surface, prompt, x + 10, y - 20, self.font, self.player_color)

    def _draw_text(self, surface, text, x, y, font, color):
        """Draw text using available font system"""
        try:
            # Try freetype first
            if hasattr(font, 'render'):
                text_surface, _ = font.render(text, color)
                surface.blit(text_surface, (x, y))
            else:
                # Fall back to regular pygame font
                text_surface = font.render(text, True, color)
                surface.blit(text_surface, (x, y))
        except:
            # Ultimate fallback
            if hasattr(pygame.font, 'Font'):
                fallback_font = pygame.font.Font(None, 20)
                text_surface = fallback_font.render(text, True, color)
                surface.blit(text_surface, (x, y))

    def _wrap_text(self, text, max_width):
        """Wrap text to fit within width"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            # Estimate width (rough approximation)
            test_line = ' '.join(current_line + [word])
            if len(test_line) * 10 <= max_width:  # Rough character width estimation
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def end_conversation(self):
        """End the current conversation"""
        self.is_active = False
        self.active_ai_character = None
        self.input_active = False
        self.current_input = ""

        print("🤖 Simple text conversation ended")

    def is_conversation_active(self):
        """Check if a conversation is currently active"""
        return self.is_active