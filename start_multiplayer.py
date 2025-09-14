#!/usr/bin/env python3
"""
Startup script for Multiplayer Asteroid Frontier

This script helps start both the server and RPG client for testing.
"""

import os
import sys
import subprocess
import time
import threading
import requests
import socket

def is_server_running():
    """Check if the server is already running"""
    try:
        # Check if HTTP API is responding
        response = requests.get("http://localhost:8889/api/status", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass

    # Also check if ports are in use
    for port in [8888, 8889]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                sock.close()
                return True
        except:
            pass
        finally:
            sock.close()

    return False

def start_server():
    """Start the TextMMO server in a separate process"""
    print("Starting TextMMO server...")
    try:
        # Change to TextMMO directory
        server_dir = "../AsteroidFrontier_TextMMO"
        if not os.path.exists(server_dir):
            print(f"Error: TextMMO directory not found at {server_dir}")
            return False

        # Start server
        process = subprocess.Popen([
            sys.executable, "run.py", "server"
        ], cwd=server_dir)

        # Give server time to start
        time.sleep(3)

        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            print("❌ Server failed to start")
            return False

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def start_rpg_client():
    """Start the RPG client"""
    print("Starting RPG client...")
    try:
        # Give server a moment to be ready
        time.sleep(1)

        # Start RPG client
        subprocess.run([sys.executable, "multiplayer_rpg.py"])

    except Exception as e:
        print(f"❌ Error starting RPG client: {e}")

def main():
    """Main startup function"""
    print("=" * 50)
    print("Asteroid Frontier - Multiplayer Setup")
    print("=" * 50)

    # Check if we can find the required files
    required_files = [
        "multiplayer_rpg.py",
        "network_client.py",
        "../AsteroidFrontier_TextMMO/run.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\nPlease ensure all files are in place before running.")
        return

    print("✅ All required files found")

    # Check if server is already running
    server_process = None
    if is_server_running():
        print("✅ Server is already running - connecting to existing server")
    else:
        # Start server
        server_process = start_server()
        if not server_process:
            print("❌ Failed to start server. Cannot continue.")
            return

    try:
        # Start RPG client
        print("\nStarting RPG client...")
        print("📝 Instructions:")
        print("   1. Enter a username when prompted")
        print("   2. Use WASD to move around")
        print("   3. Press Enter to chat")
        print("   4. Press T to talk to Ruby")
        print("   5. Press Space to look around")
        print("\n🚀 Starting game...")

        start_rpg_client()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        # Clean up server process (only if we started it)
        if server_process:
            print("🔄 Stopping server...")
            server_process.terminate()
            server_process.wait(timeout=5)
            print("✅ Server stopped")
        else:
            print("ℹ️ Server was already running - leaving it running")

if __name__ == "__main__":
    main()