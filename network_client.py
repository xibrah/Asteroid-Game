"""
Network Client for Asteroid Frontier RPG
Connects the Pygame RPG client to the TextMMO server for multiplayer functionality.
"""

import asyncio
import websockets
import json
import threading
import logging
from typing import Optional, Callable, Dict, Any
from queue import Queue

logger = logging.getLogger(__name__)

class NetworkClient:
    """
    Handles WebSocket connection between RPG client and TextMMO server.
    Manages message sending/receiving and state synchronization.
    """

    def __init__(self, server_host: str = "localhost", server_port: int = 8888):
        self.server_host = server_host
        self.server_port = server_port
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        self.username = ""

        # Message queues for thread-safe communication
        self.outgoing_messages = Queue()  # Messages to send to server
        self.incoming_messages = Queue()  # Messages received from server

        # Event loop and thread management
        self.loop = None
        self.network_thread = None
        self.running = False

        # Callbacks for different message types
        self.message_handlers = {}

    def set_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler

    def connect(self, username: str) -> bool:
        """Start network connection in a separate thread"""
        self.username = username
        self.running = True

        try:
            # Start network thread
            self.network_thread = threading.Thread(target=self._run_network_loop)
            self.network_thread.daemon = True
            self.network_thread.start()

            # Wait a moment for connection to establish
            import time
            time.sleep(0.5)

            return self.connected
        except Exception as e:
            logger.error(f"Failed to start network connection: {e}")
            return False

    def disconnect(self):
        """Close network connection"""
        self.running = False
        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.join(timeout=2.0)

    def send_message(self, message_type: str, data: Dict[str, Any] = None):
        """Queue a message to be sent to the server"""
        message = {
            "type": message_type,
            "data": data or {}
        }
        self.outgoing_messages.put(json.dumps(message))

    def get_message(self) -> Optional[Dict[str, Any]]:
        """Get next incoming message (non-blocking)"""
        if not self.incoming_messages.empty():
            try:
                raw_message = self.incoming_messages.get_nowait()
                return json.loads(raw_message)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message: {e}")
        return None

    def process_messages(self):
        """Process all pending messages (call from main game loop)"""
        while True:
            message = self.get_message()
            if message is None:
                break

            message_type = message.get("type")
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](message)
                except Exception as e:
                    logger.error(f"Error handling message {message_type}: {e}")
            else:
                logger.warning(f"No handler for message type: {message_type}")

    def _run_network_loop(self):
        """Run the asyncio event loop in network thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._network_main())
        except Exception as e:
            logger.error(f"Network loop error: {e}")
        finally:
            self.loop.close()

    async def _network_main(self):
        """Main network coroutine"""
        try:
            uri = f"ws://{self.server_host}:{self.server_port}"
            logger.info(f"Connecting to {uri}")

            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.connected = True
                logger.info("Connected to server")

                # Wait for welcome message before sending login
                try:
                    welcome_msg = await websocket.recv()
                    logger.info(f"Received welcome: {welcome_msg}")
                except Exception as e:
                    logger.error(f"Failed to receive welcome message: {e}")

                # Send initial login
                await self._send_login()

                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self._send_loop())
                receive_task = asyncio.create_task(self._receive_loop())

                # Run until disconnection
                await asyncio.gather(send_task, receive_task)

        except Exception as e:
            logger.error(f"Network connection error: {e}")
        finally:
            self.connected = False
            self.websocket = None

    async def _send_login(self):
        """Send login message to server"""
        login_message = {
            "type": "login",
            "data": {
                "username": self.username,
                "client_type": "rpg_client"
            }
        }
        await self.websocket.send(json.dumps(login_message))

    async def _send_loop(self):
        """Send outgoing messages to server"""
        while self.running and self.connected:
            try:
                # Check for outgoing messages
                if not self.outgoing_messages.empty():
                    message = self.outgoing_messages.get_nowait()
                    await self.websocket.send(message)
                else:
                    # Sleep briefly to avoid busy waiting
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Send loop error: {e}")
                break

    async def _receive_loop(self):
        """Receive messages from server"""
        while self.running and self.connected:
            try:
                message = await self.websocket.recv()
                self.incoming_messages.put(message)
            except websockets.exceptions.ConnectionClosed:
                logger.info("Server connection closed")
                break
            except Exception as e:
                logger.error(f"Receive loop error: {e}")
                break

class RPGNetworkManager:
    """
    High-level network manager for RPG client.
    Provides game-specific networking functionality.
    """

    def __init__(self, game_instance):
        self.game = game_instance
        self.client = NetworkClient()
        self.player_data = {}
        self.world_state = {}
        self.other_players = {}

        # Set up message handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up handlers for different message types"""
        self.client.set_message_handler("world_update", self._handle_world_update)
        self.client.set_message_handler("player_update", self._handle_player_update)
        self.client.set_message_handler("chat_message", self._handle_chat_message)
        self.client.set_message_handler("chat", self._handle_chat_message)  # Handle both message types
        self.client.set_message_handler("system_message", self._handle_system_message)
        self.client.set_message_handler("dialogue", self._handle_dialogue)
        self.client.set_message_handler("login_response", self._handle_login_response)

    def connect(self, username: str) -> bool:
        """Connect to server"""
        return self.client.connect(username)

    def disconnect(self):
        """Disconnect from server"""
        self.client.disconnect()

    def update(self):
        """Update network state (call from game loop)"""
        self.client.process_messages()

    # Game action methods
    def move_to_location(self, location_id: str):
        """Request to move to a location"""
        self.client.send_message("player_action", {
            "action": "move",
            "target": location_id
        })

    def talk_to_npc(self, npc_name: str, message: str = None):
        """Talk to an NPC"""
        data = {"action": "talk", "target": npc_name}
        if message:
            data["message"] = message
        self.client.send_message("player_action", data)

    def say_message(self, message: str):
        """Say something in the current location"""
        self.client.send_message("player_action", {
            "action": "say",
            "message": message
        })

    def take_item(self, item_name: str):
        """Take an item"""
        self.client.send_message("player_action", {
            "action": "take",
            "target": item_name
        })

    # Message handlers
    def _handle_world_update(self, message):
        """Handle world state updates from server"""
        data = message.get("data", {})
        self.world_state = data.get("world_state", {})
        self.other_players = data.get("other_players", {})

        # Update game world representation
        if hasattr(self.game, 'update_world_state'):
            self.game.update_world_state(self.world_state)

    def _handle_player_update(self, message):
        """Handle player state updates"""
        data = message.get("data", {})
        self.player_data = data

        # Update game player representation
        if hasattr(self.game, 'update_player_state'):
            self.game.update_player_state(self.player_data)

    def _handle_chat_message(self, message):
        """Handle chat messages"""
        # Handle both nested and top-level message formats
        if "data" in message:
            # Nested format
            data = message.get("data", {})
            speaker = data.get("speaker", "Unknown")
            text = data.get("message", "")
        else:
            # Top-level format (what server actually sends)
            speaker = message.get("speaker", "Unknown")
            text = message.get("content", message.get("message", ""))

        # Add to game chat/dialogue system
        if hasattr(self.game, 'add_chat_message'):
            self.game.add_chat_message(speaker, text)

    def _handle_system_message(self, message):
        """Handle system messages"""
        data = message.get("data", {})
        text = data.get("message", "")

        if hasattr(self.game, 'add_system_message'):
            self.game.add_system_message(text)

    def _handle_login_response(self, message):
        """Handle login response"""
        data = message.get("data", {})
        success = data.get("success", False)

        if success:
            logger.info("Login successful")
            self.player_data = data.get("player_data", {})
        else:
            error = data.get("error", "Unknown error")
            logger.error(f"Login failed: {error}")

    def _handle_dialogue(self, message):
        """Handle dialogue from NPCs"""
        character_name = message.get("character", "Unknown")
        dialogue_text = message.get("message", "")

        logger.info(f"Dialogue from {character_name}: {dialogue_text}")

        # Start dialogue in the game
        if hasattr(self.game, 'start_dialogue'):
            self.game.start_dialogue(character_name, dialogue_text)
        else:
            # Fallback - just add to chat
            self.game.add_chat_message(character_name, dialogue_text)