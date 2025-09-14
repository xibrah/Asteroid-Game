"""
AI Character System for Asteroid Frontier RPG

Creates NPCs powered by the AI consciousness from the TextMMO server.
These characters have persistent memories, business motivations, and
dynamic responses based on their AI personalities.
"""

from character_system import NPC
from ai_bridge import get_ai_bridge
import logging
import asyncio
import threading
from typing import Optional, List

logger = logging.getLogger(__name__)

class AICharacter(NPC):
    """
    An NPC powered by AI consciousness from the TextMMO server.

    This character can:
    - Remember past conversations
    - Have business motivations (like Ruby needing revenue)
    - React dynamically to player actions
    - Develop relationships over time
    """

    def __init__(self, name, ai_agent_name, sprite_sheet=None, x=0, y=0, dialogue=None, quest=None):
        """
        Initialize an AI-powered character.

        Args:
            name: Display name of the character
            ai_agent_name: Name of the AI agent on the server (e.g., "ruby", "cv")
            sprite_sheet: Visual sprite for the character
            x, y: Position in the world
            dialogue: Fallback dialogue if AI is unavailable
            quest: Associated quest if any
        """
        super().__init__(name, sprite_sheet, x, y, dialogue, quest)

        self.ai_agent_name = ai_agent_name.lower()
        self.ai_bridge = get_ai_bridge()
        self.conversation_history = []

        # AI-specific properties
        self.ai_mood = "neutral"
        self.business_status = "unknown"
        self.last_response = ""
        self.is_ai_connected = False

        # Check AI connection on creation
        self.check_ai_connection()

    def check_ai_connection(self):
        """Check if AI consciousness is available"""
        self.is_ai_connected = self.ai_bridge.connect()
        if self.is_ai_connected:
            logger.info(f"{self.name} AI consciousness is available")
        else:
            logger.warning(f"{self.name} falling back to static dialogue")

    def get_ai_response(self, player_name: str, message: str = None) -> str:
        """
        Get a response from the AI consciousness.

        This method handles the synchronous nature of the game
        while making async calls to the AI server.
        """
        try:
            if self.ai_agent_name == "ruby":
                response = self.ai_bridge.talk_to_ruby(player_name, message)
            elif self.ai_agent_name == "cv":
                response = self.ai_bridge.talk_to_cv(player_name, message)
            else:
                response = None

            if response:
                self.last_response = response
                self.conversation_history.append({
                    "player": player_name,
                    "message": message or "[greeting]",
                    "response": response
                })

                # Update AI status
                status = self.ai_bridge.get_ai_status(self.ai_agent_name)
                self.ai_mood = status.get("mood", "neutral")
                self.business_status = status.get("business_status", "unknown")

                return response
            else:
                # Fallback to static dialogue
                return self._get_fallback_response(player_name, message)

        except Exception as e:
            logger.error(f"Error getting AI response from {self.name}: {e}")
            return self._get_fallback_response(player_name, message)

    def _get_fallback_response(self, player_name: str, message: str) -> str:
        """Fallback to static dialogue when AI is unavailable"""
        if self.dialogue and len(self.dialogue) > 0:
            import random
            return random.choice(self.dialogue)
        else:
            return f"Hello, {player_name}!"

    def talk_to_player(self, player_name: str, message: str = None) -> str:
        """
        Main interface for player conversations.

        This method is called by the dialogue system when a player
        interacts with this AI character.
        """
        # Notify the AI about the player's presence
        if self.is_ai_connected:
            self.ai_bridge.notify_player_action(
                player_name,
                f"talk {message}" if message else "interact",
                "rusty_rocket"
            )

        # Get the AI's response
        response = self.get_ai_response(player_name, message)

        return response

    def get_status_info(self) -> dict:
        """Get current AI status information"""
        return {
            "name": self.name,
            "ai_agent": self.ai_agent_name,
            "connected": self.is_ai_connected,
            "mood": self.ai_mood,
            "business_status": self.business_status,
            "conversations": len(self.conversation_history),
            "last_response_length": len(self.last_response)
        }

    def update_ai_connection(self):
        """Update AI connection status (call periodically)"""
        if not self.is_ai_connected:
            self.check_ai_connection()

# Factory functions for creating specific AI characters

def create_ruby_character(x=320, y=96) -> AICharacter:
    """
    Create Ruby, the AI bar proprietor.

    Ruby has sophisticated business motivations and remembers
    every customer interaction for relationship building.
    """
    fallback_dialogue = [
        "Welcome to The Rusty Rocket! What can I do for you?",
        "This is neutral ground - a place to relax and forget your troubles.",
        "I've got synthhol, real alcohol, and information for the right price.",
        "The Rusty Rocket's been serving the Belt for over a century.",
        "Business is good when the Belt stays independent."
    ]

    ruby = AICharacter(
        name="Ruby",
        ai_agent_name="ruby",
        sprite_sheet=None,  # Will use existing Ruby sprite
        x=x,
        y=y,
        dialogue=fallback_dialogue
    )

    # Set Ruby's business properties
    ruby.has_shop = True
    ruby.shop_inventory = ["drink_whiskey", "drink_martian_ale", "room_standard"]
    ruby.faction = "independent"

    return ruby

def create_cv_character(x=768, y=416) -> AICharacter:
    """
    Create CV, the AI journalist.

    CV investigates player activities and builds relationships
    to develop sources for his news stories.
    """
    fallback_dialogue = [
        "Looking for news? I've got stories from all over the system.",
        "Don't believe everything you hear from official Earth channels.",
        "The truth is always more complicated than it appears.",
        "I'm investigating corporate activity in the Belt.",
        "Got any information worth reporting? I protect my sources.",
        "Independent journalism is the only way to get the real story."
    ]

    cv = AICharacter(
        name="CV",
        ai_agent_name="cv",
        sprite_sheet=None,  # Will use existing CV sprite
        x=x,
        y=y,
        dialogue=fallback_dialogue
    )

    cv.faction = "independent"

    return cv

# Global registry of AI characters
_ai_characters = {}

def register_ai_character(location: str, character: AICharacter):
    """Register an AI character for a specific location"""
    if location not in _ai_characters:
        _ai_characters[location] = []
    _ai_characters[location].append(character)

def get_ai_characters(location: str) -> List[AICharacter]:
    """Get all AI characters for a location"""
    return _ai_characters.get(location, [])

def update_all_ai_connections():
    """Update AI connections for all characters"""
    for location, characters in _ai_characters.items():
        for character in characters:
            character.update_ai_connection()

# Initialize Rusty Rocket AI characters
def setup_rusty_rocket_ai():
    """Setup AI characters for the Rusty Rocket"""
    ruby = create_ruby_character()
    cv = create_cv_character()

    register_ai_character("rusty_rocket", ruby)
    register_ai_character("rusty_rocket", cv)

    logger.info("Rusty Rocket AI consciousness initialized")

    return {"ruby": ruby, "cv": cv}