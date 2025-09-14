"""
Game Logging System for Asteroid Frontier RPG
Captures crashes, errors, and debug information to help with development
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

def setup_game_logging():
    """Setup comprehensive logging for the game"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Setup main logger
    logger = logging.getLogger('AsteroidFrontier')
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler for all logs
    file_handler = logging.FileHandler(
        log_dir / f"game_{timestamp}.log",
        mode='w',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler for important messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Setup error handler for uncaught exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow KeyboardInterrupt to work normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the full traceback
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"UNCAUGHT EXCEPTION:\n{error_msg}")

        # Also write to crash file
        crash_file = log_dir / f"CRASH_{timestamp}.log"
        with open(crash_file, 'w') as f:
            f.write(f"CRASH REPORT - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n")
            f.write(error_msg)
            f.write("\n" + "=" * 60 + "\n")
            f.write("Game State Information:\n")
            f.write(f"Python Version: {sys.version}\n")
            f.write(f"Working Directory: {os.getcwd()}\n")

        print(f"\n🚨 GAME CRASHED! Crash report saved to: {crash_file}")
        print("Please share this file for debugging assistance.")

    sys.excepthook = exception_handler

    logger.info("🚀 Game logging system initialized")
    logger.info(f"📝 Logs saved to: {log_dir.absolute()}")

    return logger

def log_ai_interaction(character_name, player_name, message, response):
    """Log AI character interactions"""
    logger = logging.getLogger('AsteroidFrontier.AI')
    logger.info(f"🤖 {character_name} <- {player_name}: '{message}'")
    logger.info(f"🤖 {character_name} -> {player_name}: '{response[:100]}{'...' if len(response) > 100 else ''}'")

def log_dialogue_error(error_msg, context=None):
    """Log dialogue system errors"""
    logger = logging.getLogger('AsteroidFrontier.Dialogue')
    logger.error(f"💬 Dialogue Error: {error_msg}")
    if context:
        logger.error(f"💬 Context: {context}")

def log_npc_creation(npc_name, npc_type, location):
    """Log NPC creation"""
    logger = logging.getLogger('AsteroidFrontier.NPCs')
    logger.info(f"👤 Created {npc_type} NPC: {npc_name} at {location}")

def log_game_state_change(from_state, to_state):
    """Log game state transitions"""
    logger = logging.getLogger('AsteroidFrontier.GameState')
    logger.info(f"🎮 State change: {from_state} -> {to_state}")

def log_player_action(player_name, action, location):
    """Log player actions"""
    logger = logging.getLogger('AsteroidFrontier.Player')
    logger.debug(f"🎯 {player_name} action: {action} at {location}")

# Create a simple debug decorator
def debug_method(func):
    """Decorator to log method entry/exit and catch exceptions"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('AsteroidFrontier.Debug')
        method_name = f"{func.__qualname__}"

        try:
            logger.debug(f"🔍 Entering {method_name}")
            result = func(*args, **kwargs)
            logger.debug(f"✅ Completed {method_name}")
            return result
        except Exception as e:
            logger.error(f"❌ Error in {method_name}: {e}")
            logger.error(f"🔍 Full traceback:\n{traceback.format_exc()}")
            raise
    return wrapper

# Global logger instance
game_logger = None

def get_game_logger():
    """Get the global game logger"""
    global game_logger
    if game_logger is None:
        game_logger = setup_game_logging()
    return game_logger