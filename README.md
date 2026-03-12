# Voice-Controlled Drone Swarm System

A scalable, voice-driven autonomy framework for UAVs implementing a **Split-Node Architecture** that enables natural language control of drone swarms on edge hardware.

## System Overview

This project implements an "eyes-up" human-swarm interaction paradigm, allowing operators to control up to 8 autonomous drone agents using voice commands, shifting focus from low-level piloting to high-level mission command.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VOICE-CONTROLLED DRONE SWARM                         │
│                         Split-Node Architecture                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────┐    SSH/UDP     ┌─────────────────────────────────┐
│      GROUND STATION (Mac)       │◄──────────────►│    FLIGHT HOST (Raspberry Pi)   │
│   Semantic Authority Node       │                │    Headless Physics Cluster     │
├─────────────────────────────────┤                ├─────────────────────────────────┤
│ • Voice Capture (PyAudio)       │                │ • ArduCopter SITL (8 agents)    │
│ • Speech Recognition (Google)   │                │ • MAVProxy Console              │
│ • Semantic Intent Processing    │                │ • Xvfb Virtual Display          │
│ • QGroundControl Visualization  │                │ • tmux Session Management       │
│ • Command Serialization         │                │ • EKF State Estimation          │
└─────────────────────────────────┘                └─────────────────────────────────┘
```

## Architecture Components

### 1. Ground Station (MacBook)
- **Voice Processing Pipeline**: Captures operator speech and converts to text
- **Semantic Intent Extraction**: Maps natural language to drone commands
- **Telemetry Visualization**: QGroundControl displays real-time swarm state
- **Command Injection**: Sends commands via encrypted SSH tunnel

### 2. Flight Host (Raspberry Pi 4/5)
- **Headless SITL Cluster**: Runs 8 concurrent ArduCopter simulations
- **Physics Engine**: Computes rigid-body dynamics and state estimation
- **MAVProxy**: Handles MAVLink communication and command routing
- **Session Persistence**: tmux maintains swarm state during network disruptions

## Quick Start

### Prerequisites

**On Mac (Ground Station):**
```bash
brew install portaudio
pip3 install pyaudio SpeechRecognition dronekit
```

**On Raspberry Pi (Flight Host):**
```bash
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
```

### Running the System

**1. Start Swarm Simulation on Pi:**
```bash
tmux new -s swarm
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v Copter -f quad -w --no-rebuild \
  --count 8 --auto-sysid --location RUNWAYSTART \
  --swarm ~/swarm_2cols_4rows_topdown.txt --mcast \
  --out=udp:192.168.0.82:14550
```

**2. Start Voice Controller on Mac:**
```bash
python3 voice_controller.py
```

**3. Open QGroundControl** to visualize the swarm

## Voice Commands

| Command | Action |
|---------|--------|
| "Take off" | Arms and lifts all drones to default altitude |
| "Land" | Initiates landing sequence for all drones |
| "Return home" | RTL mode - returns all drones to launch point |
| "Hold" / "Stop" | Emergency brake - stops all movement |
| "Formation" / "Spread" | Executes predefined formation pattern |
| "Alpha" / "Bravo" | Navigate to named waypoints |
| "Exit" | Terminates voice controller |

## Project Structure

```
voice-controlled-drone/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed system architecture
├── requirements.txt             # Python dependencies
├── config/
│   ├── waypoints.json          # GPS waypoint definitions
│   └── swarm_config.yaml       # Swarm configuration
├── src/
│   ├── voice_controller.py     # Main voice control application
│   ├── speech_processor.py     # Speech recognition module
│   ├── command_mapper.py       # Intent to command mapping
│   ├── ssh_commander.py        # SSH tunnel management
│   └── formations.py           # Formation matrix definitions
├── raspberry_pi/
│   ├── setup_flight_host.sh    # Pi setup script
│   ├── swarm_formation.txt     # MAVProxy formation script
│   └── start_swarm.sh          # Swarm startup script
└── docs/
    ├── system_diagram.md       # Visual architecture diagrams
    └── api_reference.md        # Command API documentation
```

## Hardware Requirements

| Component | Specification |
|-----------|--------------|
| Ground Station | MacBook with microphone |
| Flight Host | Raspberry Pi 4/5 (4GB+ RAM) |
| Flight Controller | Pixhawk 2.4.8 (for physical drone) |
| Network | WiFi connection between Mac and Pi |

## Network Configuration

```
Mac (Ground Station)          Raspberry Pi (Flight Host)
192.168.0.82                  192.168.0.194
     │                              │
     │◄────── UDP:14550 ───────────►│  (Telemetry)
     │◄────── UDP:14551 ───────────►│  (MAVLink)
     │─────── SSH:22 ──────────────►│  (Commands)
```

## License

MIT License - See LICENSE file for details.

## References

Based on the research paper: "Scalable Voice-controlled Drone Autonomy: From Edge-Deployed Single Agents to Distributed HITL Swarm Simulations"
