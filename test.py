import os
import subprocess
import speech_recognition as sr
import time
import sys
import json
import math
import collections
import collections.abc

# --- DRONEKIT/PYTHON 3.10+ COMPATIBILITY PATCH ---
if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    collections.MutableMapping = collections.abc.MutableMapping
else:
    try:
        collections.MutableMapping = collections.abc.MutableMapping
    except AttributeError:
        pass

# --- CONFIGURATION ---
PI_SSH = "neon_byte@192.168.0.194"
TMUX_TARGET = "swarm"  # Targets the active window in session 'swarm'
DEFAULT_ALT = 10
WAYPOINTS_FILE = "waypoints.json"

# --- GEOGRAPHIC UTILITIES ---

def get_offset_from_home(home_loc, target_loc):
    """
    Returns (North, East) offset in meters from home_loc to target_loc.
    """
    radius = 6378137.0  # Earth radius
    dLat = math.radians(target_loc['lat'] - home_loc['lat'])
    dLon = math.radians(target_loc['lon'] - home_loc['lon'])
    lat1 = math.radians(home_loc['lat'])

    north = dLat * radius
    east = dLon * radius * math.cos(lat1)

    return round(north, 1), round(east, 1)

# --- BASIC UTILITIES ---

def speak(text: str) -> None:
    print(f"\n[SWARM COMMANDER]: {text}")
    os.system(f"say '{text}'")

def ssh_tmux_send(cmd: str) -> None:
    """
    Send a command string into the tmux pane running MAVProxy on the Pi.
    """
    remote_cmd = (
        f"tmux send-keys -t {TMUX_TARGET} -l \"{cmd}\"; "
        f"tmux send-keys -t {TMUX_TARGET} Enter"
    )
    try:
        subprocess.run(["ssh", PI_SSH, remote_cmd], check=False)
    except Exception as e:
        print(f"SSH Error: {e}")

# --- HIGH-LEVEL ACTIONS ---

def prepare_swarm_module() -> None:
    ssh_tmux_send("module load swarm")
    time.sleep(1.0)

def swarm_takeoff(alt: float = DEFAULT_ALT) -> None:
    speak(f"Taking off all drones to {alt} meters.")
    ssh_tmux_send("alllinks mode GUIDED")
    time.sleep(0.5)
    ssh_tmux_send("alllinks arm throttle")
    time.sleep(1.0)
    ssh_tmux_send(f"alllinks takeoff {alt}")

def swarm_land() -> None:
    speak("Command received. All drones landing.")
    ssh_tmux_send("alllinks mode LAND")

def swarm_rtl() -> None:
    speak("Returning all drones to launch.")
    ssh_tmux_send("alllinks mode RTL")

def swarm_brake() -> None:
    speak("Emergency brake engaged.")
    ssh_tmux_send("alllinks mode BRAKE")

def swarm_formation() -> None:
    """
    Triggers the formation macro file on the Pi.
    Does NOT send individual vehicle commands to avoid flooding.
    """
    speak("Executing spread formation.")
    # This single command runs the file you verified on the Pi
    ssh_tmux_send("script /home/neon_byte/swarm_formation.txt")

def go_to_waypoint(wp_name: str) -> None:
    try:
        with open(WAYPOINTS_FILE, 'r') as f:
            wps = json.load(f)

        if wp_name.upper() not in wps:
            speak(f"Waypoint {wp_name} not found.")
            return

        if "HOME" not in wps:
            speak("Error: HOME location not defined in waypoints file.")
            return

        home = wps["HOME"]
        target = wps[wp_name.upper()]

        north, east = get_offset_from_home(home, target)
        alt = target.get("alt", 10)

        speak(f"Moving swarm to {wp_name}.")
        ssh_tmux_send(f"alllinks guided {north} {east} {alt}")

    except Exception as e:
        print(f"Waypoint Error: {e}")
        speak("Failed to execute waypoint command.")

# --- MAIN LOOP ---

def main() -> None:
    r = sr.Recognizer()
    mic = sr.Microphone()

    speak("Connecting to swarm.")
    prepare_swarm_module()

    with mic as source:
        print("Calibrating...")
        r.adjust_for_ambient_noise(source, duration=1.0)

    speak("Ready.")

    while True:
        try:
            with mic as source:
                print("\nListening...")
                audio = r.listen(source, phrase_time_limit=5)

            cmd = r.recognize_google(audio).lower()
            print(f"Heard: {cmd}")

            if "take off" in cmd:
                swarm_takeoff()
            elif "land" in cmd:
                swarm_land()
            elif "return" in cmd or "home" in cmd:
                # Use RTL or go to HOME waypoint depending on preference
                swarm_rtl()
            elif "hold" in cmd or "stop" in cmd:
                swarm_brake()

            # Triggers the file-based formation (Fixed)
            elif "formation" in cmd or "spread" in cmd:
                swarm_formation()

            # Waypoint commands
            elif "alpha" in cmd:
                go_to_waypoint("ALPHA")
            elif "bravo" in cmd:
                go_to_waypoint("BRAVO")

            elif "exit" in cmd:
                break

        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()