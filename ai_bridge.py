"""
AI Bridge for Asteroid Frontier RPG

Connects the beautiful RPG client to Ruby and CV's AI consciousness
running in the TextMMO server. This allows the visual game to leverage
the sophisticated AI personalities and behaviors.
"""

import requests
import json
import logging
from typing import Optional, Dict, Any
from threading import Lock

logger = logging.getLogger(__name__)

class AIBridge:
    """
    Bridge between the beautiful RPG and the AI consciousness server.

    This class manages communication with Ruby and CV's AI systems,
    allowing their sophisticated personalities to drive interactions
    in the visual environment.
    """

    def __init__(self, server_host="localhost", server_port=8889):
        self.server_url = f"http://{server_host}:{server_port}"
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout
        self._connection_lock = Lock()
        self._connected = False

        # Cache for AI responses to avoid spam
        self._response_cache = {}
        self._last_interaction_time = {}

    def connect(self) -> bool:
        """Test connection to AI server"""
        with self._connection_lock:
            try:
                response = self.session.get(f"{self.server_url}/api/status")
                if response.status_code == 200:
                    self._connected = True
                    logger.info("Connected to AI consciousness server")
                    return True
            except requests.RequestException as e:
                logger.warning(f"AI server not available: {e}")
                self._connected = False
                return False

        return False

    def is_connected(self) -> bool:
        """Check if connected to AI server"""
        return self._connected

    def talk_to_ruby(self, player_name: str, message: str = None) -> Optional[str]:
        """
        Have a conversation with Ruby's AI consciousness.

        Args:
            player_name: Name of the player talking to Ruby
            message: What the player said (None for just greeting)

        Returns:
            Ruby's response based on her AI consciousness
        """
        if not self._connected and not self.connect():
            # Fallback to static dialogue if AI server unavailable
            return self._get_fallback_ruby_dialogue(player_name, message)

        try:
            payload = {
                "agent": "ruby",
                "player": player_name,
                "action": "talk",
                "message": message or "",
                "location": "rusty_rocket"
            }

            response = self.session.post(
                f"{self.server_url}/api/interact",
                json=payload,
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")

                # Ruby's AI consciousness is working!
                if ai_response:
                    logger.info(f"Ruby AI responded: {ai_response[:50]}...")
                    return ai_response

        except requests.RequestException as e:
            logger.error(f"Failed to communicate with Ruby AI: {e}")

        # Fallback to static dialogue
        return self._get_fallback_ruby_dialogue(player_name, message)

    def talk_to_cv(self, player_name: str, message: str = None) -> Optional[str]:
        """
        Have a conversation with CV's AI consciousness.

        Args:
            player_name: Name of the player talking to CV
            message: What the player said (None for just greeting)

        Returns:
            CV's response based on his AI consciousness
        """
        if not self._connected and not self.connect():
            return self._get_fallback_cv_dialogue(player_name, message)

        try:
            payload = {
                "agent": "cv",
                "player": player_name,
                "action": "talk",
                "message": message or "",
                "location": "rusty_rocket"
            }

            response = self.session.post(
                f"{self.server_url}/api/interact",
                json=payload,
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")

                if ai_response:
                    logger.info(f"CV AI responded: {ai_response[:50]}...")
                    return ai_response

        except requests.RequestException as e:
            logger.error(f"Failed to communicate with CV AI: {e}")

        return self._get_fallback_cv_dialogue(player_name, message)

    def get_ai_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status information about an AI agent"""
        if not self._connected and not self.connect():
            return {}

        try:
            response = self.session.get(f"{self.server_url}/api/agent/{agent_name}/status")
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass

        return {}

    def notify_player_action(self, player_name: str, action: str, location: str):
        """Notify AI agents about player actions"""
        if not self._connected:
            return

        try:
            payload = {
                "player": player_name,
                "action": action,
                "location": location
            }

            self.session.post(
                f"{self.server_url}/api/notify",
                json=payload,
                timeout=1  # Quick notification
            )
        except requests.RequestException:
            pass  # Non-critical

    def _get_fallback_ruby_dialogue(self, player_name: str, message: str) -> str:
        """
        Fallback Ruby dialogue when AI server is unavailable.

        Uses Ruby's established personality but without the
        sophisticated consciousness behaviors.
        """
        fallback_responses = [
            f"Welcome to The Rusty Rocket, {player_name}! What can I do for you?",
            "This is neutral ground - a place to relax and forget your troubles.",
            "I've got synthhol, real alcohol, and all the information you can handle.",
            "The Rusty Rocket's been serving the Belt for over a century.",
            "I keep this place running in honor of Captain Lucky's memory.",
            "Looking for anything particular, or just here to enjoy the atmosphere?"
        ]

        # Simple message-based responses
        if message:
            message_lower = message.lower()
            if any(word in message_lower for word in ["drink", "alcohol", "synthhol"]):
                return "I've got premium synthhol and some real alcohol that just came in. What's your preference?"
            elif any(word in message_lower for word in ["information", "news", "intel"]):
                return "Information is my specialty. I hear things from all over the system. What kind of intel are you looking for?"
            elif any(word in message_lower for word in ["business", "credits", "deal"]):
                return "Business is good when the Belt stays independent. I've got some opportunities for the right person."
            elif any(word in message_lower for word in ["hello", "hi", "greeting"]):
                return f"Good to see you, {player_name}. The Rusty Rocket's always open to friends."

        # Random fallback
        import random
        return random.choice(fallback_responses)

    def _get_fallback_cv_dialogue(self, player_name: str, message: str) -> str:
        """
        Fallback CV dialogue when AI server is unavailable.
        """
        fallback_responses = [
            f"Looking for news, {player_name}? I've got stories from all over the system.",
            "Don't believe everything you hear from the official Earth channels.",
            "The truth is always more complicated than the headlines suggest.",
            "I'm working on an investigation about corporate activity in the Belt.",
            "Independent journalism is the only way to get the real story.",
            "Got any information worth reporting? I protect my sources."
        ]

        if message:
            message_lower = message.lower()
            if any(word in message_lower for word in ["news", "story", "information"]):
                return "I'm always looking for reliable sources. What have you seen in your travels?"
            elif any(word in message_lower for word in ["corporate", "earth", "mars"]):
                return "Corporate influence in the Belt is my main beat. Any insider information?"
            elif any(word in message_lower for word in ["truth", "investigate"]):
                return "The truth has a way of surfacing eventually. Sometimes it just needs help."

        import random
        return random.choice(fallback_responses)

# Global AI bridge instance
ai_bridge = AIBridge()

def get_ai_bridge() -> AIBridge:
    """Get the global AI bridge instance"""
    return ai_bridge