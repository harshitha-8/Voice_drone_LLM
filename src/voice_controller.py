#!/usr/bin/env python3
"""
Voice-Controlled Drone Swarm Controller
========================================
Main application for voice-driven UAV swarm control using Split-Node architecture.

This module implements the Ground Station semantic authority, capturing voice commands
and injecting them into the Flight Host via encrypted SSH tunnel.
"""

import os
import sys
import json
import math
import time
import collections
import collections.abc
import subprocess
import speech_recognition as sr
from typing import Optional, Tuple, Dict, Any

# DroneKit/Python 3.10+ compatibility patch
if sys.version_info >= (3, 10):
    collections.MutableMapping = collections.abc.MutableMapping


class SwarmConfig:
    """Configuration for swarm control system."""
    
    PI_SSH = "neon_byte@192.168.0.194"
    TMUX_TARGET = "swarm"
    DEFAULT_ALT = 10
    WAYPOINTS_FILE = "config/waypoints.json"
    PHRASE_TIME_LIMIT = 5
    NOISE_CALIBRATION_DURATION = 1.0


class GeoUtils:
    """Geographic utility functions for coordinate calculations."""
    
    EARTH_RADIUS = 6378137.0  # meters
    
    @staticmethod
    def get_offset_from_home(home_loc: Dict, target_loc: Dict) -> Tuple[float, float]:
        """
        Calculate North/East offset in meters from home to target location.
        
        Args:
            home_loc: Dict with 'lat', 'lon' keys (home position)
            target_loc: Dict with 'lat', 'lon' keys (target position)
            
        Returns:
            Tuple of (north_offset, east_offset) in meters
        """
        d_lat = math.radians(target_loc['lat'] - home_loc['lat'])
        d_lon = math.radians(target_loc['lon'] - home_loc['lon'])
        lat1 = math.radians(home_loc['lat'])
        
        north = d_lat * GeoUtils.EARTH_RADIUS
        east = d_lon * GeoUtils.EARTH_RADIUS * math.cos(lat1)
        
        return round(north, 1), round(east, 1)


class AudioFeedback:
    """Audio feedback system for operator communication."""
    
    @staticmethod
    def speak(text: str) -> None:
        """Announce text via text-to-speech and console."""
        print(f"\n[SWARM COMMANDER]: {text}")
        os.system(f"say '{text}'")


class SSHCommander:
    """SSH tunnel management for remote command injection."""
    
    def __init__(self, ssh_target: str, tmux_session: str):
        self.ssh_target = ssh_target
        self.tmux_session = tmux_session
    
    def send_command(self, cmd: str) -> bool:
        """
        Inject command into remote tmux session via SSH.
        
        Args:
            cmd: MAVProxy command string to execute
            
        Returns:
            True if command sent successfully, False otherwise
        """
        remote_cmd = (
            f"tmux send-keys -t {self.tmux_session} -l \"{cmd}\"; "
            f"tmux send-keys -t {self.tmux_session} Enter"
        )
        try:
            result = subprocess.run(
                ["ssh", self.ssh_target, remote_cmd],
                check=False,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("[ERROR] SSH command timed out")
            return False
        except Exception as e:
            print(f"[ERROR] SSH Error: {e}")
            return False


class SwarmController:
    """High-level swarm control operations."""
    
    def __init__(self, commander: SSHCommander, config: SwarmConfig):
        self.commander = commander
        self.config = config
        self.waypoints = self._load_waypoints()
    
    def _load_waypoints(self) -> Dict[str, Any]:
        """Load waypoint definitions from JSON file."""
        try:
            # Try multiple paths
            paths = [
                self.config.WAYPOINTS_FILE,
                "waypoints.json",
                os.path.join(os.path.dirname(__file__), "..", "config", "waypoints.json"),
                os.path.join(os.path.dirname(__file__), "..", "waypoints.json")
            ]
            for path in paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            print("[WARNING] Waypoints file not found")
            return {}
        except Exception as e:
            print(f"[WARNING] Failed to load waypoints: {e}")
            return {}
    
    def prepare_swarm_module(self) -> None:
        """Load the swarm module in MAVProxy."""
        self.commander.send_command("module load swarm")
        time.sleep(1.0)
    
    def takeoff(self, alt: float = None) -> None:
        """Execute swarm takeoff sequence."""
        alt = alt or self.config.DEFAULT_ALT
        AudioFeedback.speak(f"Taking off all drones to {alt} meters.")
        self.commander.send_command("alllinks mode GUIDED")
        time.sleep(0.5)
        self.commander.send_command("alllinks arm throttle")
        time.sleep(1.0)
        self.commander.send_command(f"alllinks takeoff {alt}")
    
    def land(self) -> None:
        """Execute swarm landing."""
        AudioFeedback.speak("Command received. All drones landing.")
        self.commander.send_command("alllinks mode LAND")
    
    def return_to_launch(self) -> None:
        """Return all drones to launch position."""
        AudioFeedback.speak("Returning all drones to launch.")
        self.commander.send_command("alllinks mode RTL")
    
    def emergency_brake(self) -> None:
        """Emergency stop all drones."""
        AudioFeedback.speak("Emergency brake engaged.")
        self.commander.send_command("alllinks mode BRAKE")
    
    def execute_formation(self) -> None:
        """Execute predefined formation pattern."""
        AudioFeedback.speak("Executing spread formation.")
        self.commander.send_command("script /home/neon_byte/swarm_formation.txt")
    
    def go_to_waypoint(self, wp_name: str) -> None:
        """Navigate swarm to named waypoint."""
        wp_key = wp_name.upper()
        
        if wp_key not in self.waypoints:
            AudioFeedback.speak(f"Waypoint {wp_name} not found.")
            return
        
        if "HOME" not in self.waypoints:
            AudioFeedback.speak("Error: HOME location not defined.")
            return
        
        home = self.waypoints["HOME"]
        target = self.waypoints[wp_key]
        
        north, east = GeoUtils.get_offset_from_home(home, target)
        alt = target.get("alt", self.config.DEFAULT_ALT)
        
        AudioFeedback.speak(f"Moving swarm to {wp_name}.")
        self.commander.send_command(f"alllinks guided {north} {east} {alt}")
    
    def send_individual_commands(self, commands: list) -> None:
        """Send individual vehicle commands for custom formations."""
        for cmd in commands:
            self.commander.send_command(cmd)
            time.sleep(0.3)


class VoiceRecognizer:
    """Voice recognition and command parsing."""
    
    COMMAND_MAP = {
        "take off": "takeoff",
        "takeoff": "takeoff",
        "land": "land",
        "landing": "land",
        "return": "rtl",
        "home": "rtl",
        "return home": "rtl",
        "hold": "brake",
        "stop": "brake",
        "brake": "brake",
        "formation": "formation",
        "spread": "formation",
        "alpha": "waypoint_alpha",
        "bravo": "waypoint_bravo",
        "exit": "exit",
        "quit": "exit"
    }
    
    def __init__(self, config: SwarmConfig):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
    
    def calibrate(self) -> None:
        """Calibrate for ambient noise."""
        with self.microphone as source:
            print("Calibrating for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(
                source, 
                duration=self.config.NOISE_CALIBRATION_DURATION
            )
    
    def listen(self) -> Optional[str]:
        """Listen for voice command and return recognized text."""
        try:
            with self.microphone as source:
                print("\nListening...")
                audio = self.recognizer.listen(
                    source, 
                    phrase_time_limit=self.config.PHRASE_TIME_LIMIT
                )
            
            text = self.recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
            return text
            
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[ERROR] Speech recognition service error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Recognition error: {e}")
            return None
    
    def parse_command(self, text: str) -> Optional[str]:
        """Parse recognized text into command identifier."""
        if not text:
            return None
        
        for phrase, command in self.COMMAND_MAP.items():
            if phrase in text:
                return command
        
        return None


class SwarmApplication:
    """Main application orchestrating all components."""
    
    def __init__(self):
        self.config = SwarmConfig()
        self.commander = SSHCommander(
            self.config.PI_SSH, 
            self.config.TMUX_TARGET
        )
        self.controller = SwarmController(self.commander, self.config)
        self.voice = VoiceRecognizer(self.config)
    
    def execute_command(self, command: str) -> bool:
        """Execute parsed command. Returns False to exit."""
        command_handlers = {
            "takeoff": self.controller.takeoff,
            "land": self.controller.land,
            "rtl": self.controller.return_to_launch,
            "brake": self.controller.emergency_brake,
            "formation": self.controller.execute_formation,
            "waypoint_alpha": lambda: self.controller.go_to_waypoint("ALPHA"),
            "waypoint_bravo": lambda: self.controller.go_to_waypoint("BRAVO"),
        }
        
        if command == "exit":
            AudioFeedback.speak("Shutting down voice controller.")
            return False
        
        handler = command_handlers.get(command)
        if handler:
            handler()
        
        return True
    
    def run(self) -> None:
        """Main application loop."""
        AudioFeedback.speak("Connecting to swarm.")
        self.controller.prepare_swarm_module()
        
        self.voice.calibrate()
        AudioFeedback.speak("Ready for voice commands.")
        
        running = True
        while running:
            text = self.voice.listen()
            if text:
                command = self.voice.parse_command(text)
                if command:
                    running = self.execute_command(command)


def main():
    """Entry point for voice controller application."""
    app = SwarmApplication()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    except Exception as e:
        print(f"[ERROR] Application error: {e}")
        raise


if __name__ == "__main__":
    main()
