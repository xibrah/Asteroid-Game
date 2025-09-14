"""
Enhanced AI Dialogue System for Asteroid Frontier RPG

Provides open-ended text input conversations with AI characters
that can trigger game mechanics like merchant systems, quests, etc.
"""

import pygame
import pygame_gui
from ai_bridge import get_ai_bridge
from game_logger import log_ai_interaction
import re

class EnhancedAIDialogue:
    """
    Open-ended AI dialogue system with text input and action parsing.

    Replaces choice-based dialogue with natural language conversations
    that can trigger game mechanics based on AI responses.
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # UI Manager for text input
        self.ui_manager = pygame_gui.UIManager((screen_width, screen_height))

        # Dialogue state
        self.active_ai_character = None
        self.conversation_history = []
        self.is_active = False

        # UI elements
        self.dialogue_panel = None
        self.text_input = None
        self.response_display = None
        self.history_display = None

        # Fonts
        self.font = pygame.font.Font(None, 24)
        self.name_font = pygame.font.Font(None, 32)

        # AI Bridge
        self.ai_bridge = get_ai_bridge()

        # Action parsing patterns
        self.action_patterns = {
            'show_shop': [
                r'(?i).*(?:show|see|view|check).*(?:menu|shop|wares|goods|items|inventory|store)',
                r'(?i).*(?:what|what\'s).*(?:for sale|available|selling)',
                r'(?i).*(?:open|access).*(?:shop|store|merchant)',
                r'(?i).*(?:browse|look at).*(?:inventory|stock|goods)'
            ],
            'quest_offer': [
                r'(?i).*(?:job|work|quest|task|mission|help).*(?:available|need|want|looking)',
                r'(?i).*(?:anything|something).*(?:to do|help with)',
                r'(?i).*(?:work for you|help you out)'
            ],
            'location_info': [
                r'(?i).*(?:where|how to get to|directions to).*',
                r'(?i).*(?:tell me about|info about|information on).*(?:place|location|area)'
            ]
        }

    def start_conversation(self, ai_character, player):
        """Start an open-ended conversation with an AI character"""
        self.active_ai_character = ai_character
        self.player = player
        self.is_active = True
        self.conversation_history = []

        # Create UI elements
        self._create_dialogue_ui()

        # Get initial AI greeting
        initial_response = ai_character.talk_to_player(player.name)
        self._add_to_conversation("AI", ai_character.name, initial_response)

        log_ai_interaction(ai_character.name, player.name, "[conversation started]", initial_response)

        print(f"🤖 Started enhanced AI conversation with {ai_character.name}")

    def _create_dialogue_ui(self):
        """Create the UI elements for enhanced dialogue"""
        # Main dialogue panel
        panel_width = self.screen_width - 100
        panel_height = 400
        panel_x = 50
        panel_y = self.screen_height - panel_height - 50

        self.dialogue_panel = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # Conversation history display area
        history_height = 250
        self.history_area = pygame.Rect(
            panel_x + 20,
            panel_y + 40,
            panel_width - 40,
            history_height
        )

        # Text input field
        input_width = panel_width - 120
        input_height = 40
        input_x = panel_x + 20
        input_y = panel_y + panel_height - 60

        self.text_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(input_x, input_y, input_width, input_height),
            manager=self.ui_manager,
            placeholder_text="Type your message to " + (self.active_ai_character.name if self.active_ai_character else "AI") + "..."
        )

        # Send button
        button_width = 80
        button_x = input_x + input_width + 10

        self.send_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(button_x, input_y, button_width, input_height),
            text='Send',
            manager=self.ui_manager
        )

        # Close button
        close_x = panel_x + panel_width - 80
        close_y = panel_y + 10

        self.close_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(close_x, close_y, 60, 30),
            text='Close',
            manager=self.ui_manager
        )

    def _add_to_conversation(self, speaker_type, speaker_name, message):
        """Add a message to the conversation history"""
        self.conversation_history.append({
            'type': speaker_type,  # 'Player' or 'AI'
            'name': speaker_name,
            'message': message,
            'timestamp': pygame.time.get_ticks()
        })

        # Keep history manageable
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

    def handle_event(self, event):
        """Handle events for the enhanced dialogue system"""
        if not self.is_active:
            return False

        # Handle UI events
        self.ui_manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.send_button:
                self._send_message()
                return True
            elif event.ui_element == self.close_button:
                self.end_conversation()
                return True

        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.text_input:
                self._send_message()
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.end_conversation()
                return True
            elif event.key == pygame.K_RETURN and not self.text_input.is_focused:
                # Focus text input when Enter is pressed
                self.text_input.focus()
                return True

        return False

    def _send_message(self):
        """Send player's message to AI and get response"""
        if not self.text_input.get_text().strip():
            return

        player_message = self.text_input.get_text().strip()
        self.text_input.set_text("")

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

        # Check player message for action patterns
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, player_message):
                    actions.append({
                        'type': action_type,
                        'trigger': 'player_request',
                        'message': player_message
                    })
                    break

        # Check AI response for action indicators
        ai_lower = ai_response.lower()

        if any(phrase in ai_lower for phrase in ['here\'s my menu', 'let me show you', 'take a look at', 'here\'s what i have']):
            actions.append({
                'type': 'show_shop',
                'trigger': 'ai_offer',
                'message': ai_response
            })

        if any(phrase in ai_lower for phrase in ['i have a job', 'need help with', 'task for you', 'mission available']):
            actions.append({
                'type': 'quest_offer',
                'trigger': 'ai_offer',
                'message': ai_response
            })

        return actions

    def _execute_actions(self, actions):
        """Execute parsed actions"""
        for action in actions:
            if action['type'] == 'show_shop':
                self._trigger_merchant_gui()
            elif action['type'] == 'quest_offer':
                self._trigger_quest_system()
            elif action['type'] == 'location_info':
                self._show_location_info()

            print(f"🎮 Triggered action: {action['type']} from {action['trigger']}")

    def _trigger_merchant_gui(self):
        """Trigger the merchant GUI"""
        # This will need to interface with the game's merchant system
        print(f"🛒 Opening merchant GUI for {self.active_ai_character.name}")
        # TODO: Interface with MerchantSystem
        # self.game.merchant_system.open_shop(self.active_ai_character)

    def _trigger_quest_system(self):
        """Trigger the quest system"""
        print(f"📋 Opening quest system for {self.active_ai_character.name}")
        # TODO: Interface with QuestManager

    def _show_location_info(self):
        """Show location information"""
        print(f"🗺️ Showing location info")
        # TODO: Interface with map/location system

    def update(self, time_delta):
        """Update the dialogue system"""
        if self.is_active:
            self.ui_manager.update(time_delta)

    def draw(self, surface):
        """Draw the enhanced dialogue interface"""
        if not self.is_active:
            return

        # Draw main dialogue panel
        pygame.draw.rect(surface, (20, 20, 40), self.dialogue_panel)
        pygame.draw.rect(surface, (100, 100, 150), self.dialogue_panel, 3)

        # Draw character name
        if self.active_ai_character:
            name_text = self.name_font.render(
                f"Conversation with {self.active_ai_character.name}",
                True, (255, 255, 255)
            )
            surface.blit(name_text, (self.dialogue_panel.x + 20, self.dialogue_panel.y + 10))

        # Draw conversation history
        self._draw_conversation_history(surface)

        # Draw UI elements
        self.ui_manager.draw_ui(surface)

    def _draw_conversation_history(self, surface):
        """Draw the conversation history"""
        if not self.conversation_history:
            return

        y_offset = 0
        line_height = 25
        max_lines = 8

        # Draw recent messages (last max_lines)
        recent_messages = self.conversation_history[-max_lines:]

        for msg in recent_messages:
            if y_offset >= self.history_area.height - line_height:
                break

            # Color based on speaker
            color = (150, 255, 150) if msg['type'] == 'Player' else (255, 200, 100)

            # Wrap long messages
            text = f"{msg['name']}: {msg['message']}"
            wrapped_lines = self._wrap_text(text, self.history_area.width - 20)

            for line in wrapped_lines:
                if y_offset >= self.history_area.height - line_height:
                    break

                text_surface = self.font.render(line, True, color)
                surface.blit(text_surface, (
                    self.history_area.x + 10,
                    self.history_area.y + y_offset
                ))
                y_offset += line_height

    def _wrap_text(self, text, max_width):
        """Wrap text to fit within width"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.font.size(test_line)[0] <= max_width:
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

        # Clean up UI elements
        if self.text_input:
            self.text_input.kill()
        if self.send_button:
            self.send_button.kill()
        if self.close_button:
            self.close_button.kill()

        print("🤖 Enhanced AI conversation ended")

    def is_conversation_active(self):
        """Check if a conversation is currently active"""
        return self.is_active