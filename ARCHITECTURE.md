# System Architecture Documentation

## End-to-End Voice-Controlled Drone Swarm Architecture

This document provides a comprehensive technical overview of the Split-Node distributed architecture for voice-controlled UAV swarm operations.

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              VOICE-CONTROLLED DRONE SWARM                               │
│                            Split-Node Distributed Topology                              │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    OPERATOR
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Voice Input    │
                              │  (Microphone)   │
                              └────────┬────────┘
                                       │
═══════════════════════════════════════╪═══════════════════════════════════════════════════
                                       │
┌──────────────────────────────────────┼──────────────────────────────────────────────────┐
│                           GROUND STATION (MacBook)                                      │
│                            Semantic Authority Node                                      │
│  ┌───────────────────────────────────┼───────────────────────────────────────────────┐  │
│  │                                   ▼                                               │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐               │  │
│  │  │  Audio Capture  │───►│ Speech-to-Text  │───►│ Intent Parser   │               │  │
│  │  │    (PyAudio)    │    │ (Google ASR)    │    │ (Semantic Map)  │               │  │
│  │  └─────────────────┘    └─────────────────┘    └────────┬────────┘               │  │
│  │                                                         │                         │  │
│  │                                                         ▼                         │  │
│  │                                              ┌─────────────────────┐              │  │
│  │                                              │  Command Generator  │              │  │
│  │                                              │  (Formation Matrix) │              │  │
│  │                                              └──────────┬──────────┘              │  │
│  │                                                         │                         │  │
│  │  ┌─────────────────┐                                    │                         │  │
│  │  │ QGroundControl  │◄───── UDP Telemetry ───────────────┼─────────────────────┐   │  │
│  │  │  (Visualization)│                                    │                     │   │  │
│  │  └─────────────────┘                                    │                     │   │  │
│  └─────────────────────────────────────────────────────────┼─────────────────────┼───┘  │
└────────────────────────────────────────────────────────────┼─────────────────────┼──────┘
                                                             │                     │
                                          SSH Tunnel         │                     │
                                        (Encrypted)          │                     │
                                                             ▼                     │
═══════════════════════════════════════════════════════════════════════════════════════════
                                                             │                     │
┌────────────────────────────────────────────────────────────┼─────────────────────┼──────┐
│                          FLIGHT HOST (Raspberry Pi 4/5)    │                     │      │
│                           Headless Physics Cluster         │                     │      │
│  ┌─────────────────────────────────────────────────────────┼─────────────────────┼───┐  │
│  │                                                         ▼                     │   │  │
│  │  ┌─────────────────────────────────────────────────────────┐                  │   │  │
│  │  │                    tmux Session: swarm                  │                  │   │  │
│  │  │  ┌───────────────────────────────────────────────────┐  │                  │   │  │
│  │  │  │                   MAVProxy Console                │  │                  │   │  │
│  │  │  │  • Command Injection Point                        │  │                  │   │  │
│  │  │  │  • Swarm Module Loaded                            │  │                  │   │  │
│  │  │  │  • alllinks Command Router                        │  │                  │   │  │
│  │  │  └───────────────────────────────────────────────────┘  │                  │   │  │
│  │  └─────────────────────────────────────────────────────────┘                  │   │  │
│  │                              │                                                │   │  │
│  │                              ▼                                                │   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │   │  │
│  │  │                     Xvfb Virtual Display Server                         │  │   │  │
│  │  │                   (Headless Graphics Emulation)                         │  │   │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │   │  │
│  │                              │                                                │   │  │
│  │          ┌───────────────────┼───────────────────┐                            │   │  │
│  │          ▼                   ▼                   ▼                            │   │  │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                      │   │  │
│  │  │  SITL #1-2  │     │  SITL #3-4  │     │  SITL #5-8  │                      │   │  │
│  │  │ ArduCopter  │     │ ArduCopter  │     │ ArduCopter  │                      │   │  │
│  │  │   Agents    │     │   Agents    │     │   Agents    │                      │   │  │
│  │  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                      │   │  │
│  │         │                   │                   │                             │   │  │
│  │         └───────────────────┼───────────────────┘                             │   │  │
│  │                             │                                                 │   │  │
│  │                             ▼                                                 │   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │   │  │
│  │  │                      Physics & State Estimation                         │  │   │  │
│  │  │  • Rigid-Body Dynamics    • EKF State Estimation                        │──┼───┘   │
│  │  │  • PID Control Loops      • Telemetry Generation                        │  │      │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │      │
│  └───────────────────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATA FLOW PIPELINE                                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘

PHASE 1: VOICE CAPTURE & RECOGNITION
══════════════════════════════════════════════════════════════════════════════════════════

    Operator Voice          Audio Stream           Raw Text
         │                      │                     │
         ▼                      ▼                     ▼
    ┌─────────┐           ┌──────────┐          ┌──────────┐
    │ Mic In  │──────────►│ PyAudio  │─────────►│ Google   │
    │         │           │ Buffer   │          │ ASR API  │
    └─────────┘           └──────────┘          └────┬─────┘
                                                     │
                                                     ▼
                                              "take off all"

PHASE 2: SEMANTIC INTENT EXTRACTION
══════════════════════════════════════════════════════════════════════════════════════════

    Raw Text                Intent Match           Command Type
         │                      │                     │
         ▼                      ▼                     ▼
    ┌──────────┐          ┌──────────────┐      ┌──────────────┐
    │ "take    │─────────►│ Keyword      │─────►│ TAKEOFF      │
    │  off"    │          │ Matching     │      │ Command      │
    └──────────┘          └──────────────┘      └──────┬───────┘
                                                       │
    ┌──────────────────────────────────────────────────┘
    │
    │   COMMAND MAPPING TABLE
    │   ┌────────────────┬─────────────────────────────────┐
    │   │ Voice Pattern  │ MAVProxy Command                │
    │   ├────────────────┼─────────────────────────────────┤
    │   │ "take off"     │ alllinks mode GUIDED            │
    │   │                │ alllinks arm throttle           │
    │   │                │ alllinks takeoff {alt}          │
    │   ├────────────────┼─────────────────────────────────┤
    │   │ "land"         │ alllinks mode LAND              │
    │   ├────────────────┼─────────────────────────────────┤
    │   │ "return home"  │ alllinks mode RTL               │
    │   ├────────────────┼─────────────────────────────────┤
    │   │ "hold/stop"    │ alllinks mode BRAKE             │
    │   ├────────────────┼─────────────────────────────────┤
    │   │ "formation"    │ script swarm_formation.txt      │
    │   └────────────────┴─────────────────────────────────┘

PHASE 3: SECURE COMMAND INJECTION
══════════════════════════════════════════════════════════════════════════════════════════

    MAVProxy Command        SSH Tunnel            tmux Injection
         │                      │                     │
         ▼                      ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │ "alllinks    │─────►│ ssh neon_    │─────►│ tmux send-   │
    │  mode GUIDED"│      │ byte@pi      │      │ keys -t swarm│
    └──────────────┘      └──────────────┘      └──────┬───────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │  MAVProxy    │
                                              │  Console     │
                                              └──────────────┘

PHASE 4: SWARM EXECUTION & TELEMETRY
══════════════════════════════════════════════════════════════════════════════════════════

    MAVProxy                 SITL Agents          Telemetry
         │                      │                     │
         ▼                      ▼                     ▼
    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │ Command      │─────►│ Vehicle 1-8  │─────►│ UDP Multicast│
    │ Router       │      │ State Update │      │ :14550       │
    └──────────────┘      └──────────────┘      └──────┬───────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │QGroundControl│
                                              │ Visualization│
                                              └──────────────┘
```

---

## 3. Component Architecture

### 3.1 Voice Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          VOICE PROCESSING PIPELINE                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   STAGE 1   │    │   STAGE 2   │    │   STAGE 3   │    │   STAGE 4   │    │   STAGE 5   │
│   Capture   │───►│   Denoise   │───►│  Recognize  │───►│   Parse     │───►│   Execute   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PyAudio     │    │ Ambient     │    │ Google      │    │ Keyword     │    │ SSH/tmux    │
│ Microphone  │    │ Noise       │    │ Speech      │    │ Matching    │    │ Command     │
│ Input       │    │ Calibration │    │ Recognition │    │ Engine      │    │ Injection   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

Performance Metrics:
• Recognition Accuracy: ~90%
• End-to-End Latency: <1 second
• Command Injection Latency: <15ms
```

### 3.2 Swarm Control Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           SWARM CONTROL ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │    MAVProxy         │
                              │    (Swarm Module)   │
                              └──────────┬──────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
            │   alllinks    │    │   vehicle N   │    │   script      │
            │   (Broadcast) │    │   (Unicast)   │    │   (Macro)     │
            └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
                    │                    │                    │
    ┌───────────────┼───────────────┐    │    ┌───────────────┼───────────────┐
    │               │               │    │    │               │               │
    ▼               ▼               ▼    ▼    ▼               ▼               ▼
┌───────┐       ┌───────┐       ┌───────┐ ┌───────┐       ┌───────┐       ┌───────┐
│ UAV 1 │       │ UAV 2 │       │ UAV 3 │ │ UAV 4 │       │ UAV 5 │  ...  │ UAV 8 │
│SYSID=1│       │SYSID=2│       │SYSID=3│ │SYSID=4│       │SYSID=5│       │SYSID=8│
└───────┘       └───────┘       └───────┘ └───────┘       └───────┘       └───────┘
```

### 3.3 Formation Control System

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          FORMATION CONTROL SYSTEM                                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘

Voice Command: "Spread Formation"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         FORMATION MATRIX COMPUTATION                                    │
│                                                                                         │
│   Formation: 2 Columns × 4 Rows (8 UAVs)                                               │
│                                                                                         │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│   │                           North (meters)                                        │  │
│   │                                 ▲                                               │  │
│   │                                 │                                               │  │
│   │                    40 ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                        │  │
│   │                                 │        [UAV7]  [UAV8]                         │  │
│   │                    30 ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                        │  │
│   │                                 │        [UAV4]  [UAV5]  [UAV6]                 │  │
│   │                    20 ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                        │  │
│   │                                 │        [UAV1]  [UAV2]  [UAV3]                 │  │
│   │                    10 ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─                        │  │
│   │                                 │                                               │  │
│   │     ◄──────────────────────────────────────────────────────────────────────►   │  │
│   │    -10          0          10         East (meters)                             │  │
│   └─────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                         │
│   Target Positions (North, East, Alt):                                                 │
│   • UAV 1: (20,  0, 10)    • UAV 5: (30, 10, 10)                                       │
│   • UAV 2: (20, 10, 10)    • UAV 6: (30,-10, 10)                                       │
│   • UAV 3: (20,-10, 10)    • UAV 7: (40,  0, 10)                                       │
│   • UAV 4: (30,  0, 10)    • UAV 8: (40, 10, 10)                                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Network Topology

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              NETWORK TOPOLOGY                                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐                    ┌─────────────────────────────┐
│      GROUND STATION         │                    │        FLIGHT HOST          │
│      (MacBook Air)          │                    │      (Raspberry Pi 4)       │
│      192.168.0.82           │                    │      192.168.0.194          │
├─────────────────────────────┤                    ├─────────────────────────────┤
│                             │                    │                             │
│  ┌───────────────────────┐  │                    │  ┌───────────────────────┐  │
│  │   Voice Controller    │  │   SSH:22           │  │   tmux: swarm         │  │
│  │   (Python Runtime)    │──┼───────────────────►│  │   MAVProxy Console    │  │
│  └───────────────────────┘  │   Command Inject   │  └───────────────────────┘  │
│                             │                    │             │               │
│  ┌───────────────────────┐  │                    │             ▼               │
│  │   QGroundControl      │  │   UDP:14550        │  ┌───────────────────────┐  │
│  │   (GCS Application)   │◄─┼────────────────────┼──│   SITL Instances      │  │
│  └───────────────────────┘  │   Telemetry        │  │   (8 × ArduCopter)    │  │
│                             │                    │  └───────────────────────┘  │
│  ┌───────────────────────┐  │                    │                             │
│  │   Gazebo GUI          │  │   UDP:14551        │  ┌───────────────────────┐  │
│  │   (3D Visualization)  │◄─┼────────────────────┼──│   Physics Engine      │  │
│  └───────────────────────┘  │   MAVLink          │  │   (Xvfb Headless)     │  │
│                             │                    │  └───────────────────────┘  │
└─────────────────────────────┘                    └─────────────────────────────┘

Protocol Summary:
┌──────────────┬───────────────┬────────────────────────────────────────────────────────┐
│ Protocol     │ Port          │ Purpose                                                │
├──────────────┼───────────────┼────────────────────────────────────────────────────────┤
│ SSH          │ 22            │ Encrypted command injection via tmux                   │
│ UDP          │ 14550         │ MAVLink telemetry to QGroundControl                    │
│ UDP          │ 14551         │ MAVLink messages for additional GCS/tools              │
│ UDP Multicast│ 239.255.x.x   │ Inter-agent communication (SITL swarm)                 │
└──────────────┴───────────────┴────────────────────────────────────────────────────────┘
```

---

## 5. Control Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    ALGORITHM: AI-Driven Distributed Swarm Control                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘

INPUTS:
  • Vm: Operator voice input
  • N = 8: Swarm size
  • G: Ground Station
  • H: Flight Host

OUTPUT:
  • St+1: Updated swarm formation state

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE I: Semantic Intent Extraction (Ground Station)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   1. Capture audio stream Vm                                                            │
│   2. Traw ← SpeechToText(Vm)                                                            │
│   3. Isemantic ← KeywordMatch(Traw)                                                     │
│   4. IF Isemantic is valid formation THEN                                               │
│        Mtarget ← ComputeFormationMatrix(Isemantic, N)                                   │
│        Jcmd ← SerializeToJSON(Mtarget)                                                  │
│      ELSE                                                                               │
│        RETURN "Invalid command intent"                                                  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE II: Secure Command Injection                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   5. Establish SSH tunnel from G to H                                                   │
│   6. Inject Jcmd into active MAVProxy console via tmux                                  │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE III: Headless Execution (Flight Host)                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   7. FOR each agent i ∈ {1, ..., N} DO                                                  │
│        Pi_current ← EKFi (Extended Kalman Filter state)                                 │
│        Pi_target ← ExtractTarget(Jcmd, i)                                               │
│        Ui ← PID(Pi_target - Pi_current)                                                 │
│        Update physics of SITL agent i                                                   │
│      END FOR                                                                            │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE IV: Telemetry Aggregation                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   8. Broadcast swarm telemetry via UDP multicast to G                                   │
│   9. Update visualization in QGroundControl                                             │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

PID Control Equation:
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   u(t) = Kp·e(t) + Ki·∫e(t)dt + Kd·(de(t)/dt)                                          │
│                                                                                         │
│   Where:                                                                                │
│   • u(t) = Control output (motor commands)                                              │
│   • e(t) = Position error (target - current)                                            │
│   • Kp, Ki, Kd = Proportional, Integral, Derivative gains                               │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Physical Hardware Integration

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL DRONE HARDWARE STACK                                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              QUADCOPTER ASSEMBLY                                        │
│                                                                                         │
│                                    ┌─────────┐                                          │
│                                    │  Motor  │                                          │
│                                    │   M1    │                                          │
│                                    └────┬────┘                                          │
│                                         │                                               │
│                    ┌─────────┐    ┌─────┴─────┐    ┌─────────┐                         │
│                    │  Motor  │────│   FRAME   │────│  Motor  │                         │
│                    │   M4    │    │           │    │   M2    │                         │
│                    └─────────┘    │ ┌───────┐ │    └─────────┘                         │
│                                   │ │PIXHAWK│ │                                         │
│                                   │ │2.4.8  │ │                                         │
│                                   │ └───┬───┘ │                                         │
│                                   │     │     │                                         │
│                                   │ ┌───┴───┐ │                                         │
│                                   │ │  RPi  │ │                                         │
│                                   │ │  4/5  │ │                                         │
│                                   │ └───────┘ │                                         │
│                                   └─────┬─────┘                                         │
│                                         │                                               │
│                                    ┌────┴────┐                                          │
│                                    │  Motor  │                                          │
│                                    │   M3    │                                          │
│                                    └─────────┘                                          │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

Hardware Communication:
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│   ┌──────────────┐     Serial/UART      ┌──────────────┐     PWM        ┌──────────┐  │
│   │ Raspberry Pi │────────────────────►│   Pixhawk    │──────────────►│  Motors  │  │
│   │   (Companion)│     MAVLink          │ (Autopilot)  │     Signals    │  (ESCs)  │  │
│   └──────────────┘                      └──────────────┘                └──────────┘  │
│         │                                     │                                        │
│         │ WiFi                                │ I2C/SPI                                │
│         ▼                                     ▼                                        │
│   ┌──────────────┐                      ┌──────────────┐                              │
│   │Ground Station│                      │   Sensors    │                              │
│   │   (Remote)   │                      │ GPS/IMU/Baro │                              │
│   └──────────────┘                      └──────────────┘                              │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Software Stack

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              SOFTWARE STACK                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘

GROUND STATION (MacBook)                    FLIGHT HOST (Raspberry Pi)
┌─────────────────────────────┐            ┌─────────────────────────────┐
│ APPLICATION LAYER           │            │ APPLICATION LAYER           │
├─────────────────────────────┤            ├─────────────────────────────┤
│ • voice_controller.py       │            │ • sim_vehicle.py            │
│ • QGroundControl            │            │ • MAVProxy                  │
│ • Gazebo (optional)         │            │ • swarm_formation.txt       │
├─────────────────────────────┤            ├─────────────────────────────┤
│ MIDDLEWARE LAYER            │            │ MIDDLEWARE LAYER            │
├─────────────────────────────┤            ├─────────────────────────────┤
│ • SpeechRecognition         │            │ • ArduCopter SITL           │
│ • DroneKit-Python           │            │ • Xvfb                      │
│ • PyAudio                   │            │ • tmux                      │
├─────────────────────────────┤            ├─────────────────────────────┤
│ COMMUNICATION LAYER         │            │ COMMUNICATION LAYER         │
├─────────────────────────────┤            ├─────────────────────────────┤
│ • SSH Client                │            │ • SSH Server (OpenSSH)      │
│ • UDP Socket                │            │ • UDP Multicast             │
│ • MAVLink Protocol          │            │ • MAVLink Protocol          │
├─────────────────────────────┤            ├─────────────────────────────┤
│ OPERATING SYSTEM            │            │ OPERATING SYSTEM            │
├─────────────────────────────┤            ├─────────────────────────────┤
│ • macOS                     │            │ • Raspberry Pi OS (64-bit)  │
│ • Python 3.10+              │            │ • Python 3.9+               │
└─────────────────────────────┘            └─────────────────────────────┘
```

---

## 8. Gazebo Integration (Optional 3D Visualization)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         GAZEBO SIMULATION INTEGRATION                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘

Terminal 1 (Mac):                          Terminal 2 (Mac):
┌─────────────────────────────┐            ┌─────────────────────────────┐
│ # Start Gazebo Server       │            │ # Start Gazebo GUI          │
│ export GZ_SIM_SYSTEM_       │            │                             │
│   PLUGIN_PATH=$HOME/        │            │ gz sim -g                   │
│   ardupilot_gazebo/build    │            │                             │
│                             │            │                             │
│ export GZ_SIM_RESOURCE_     │            │                             │
│   PATH=$HOME/ardupilot_     │            │                             │
│   gazebo/models:$HOME/      │            │                             │
│   ardupilot_gazebo/worlds   │            │                             │
│                             │            │                             │
│ gz sim -s -v4 iris_runway.  │            │                             │
│   sdf                       │            │                             │
└─────────────────────────────┘            └─────────────────────────────┘
         │                                           │
         └───────────────────┬───────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   3D Rendered   │
                    │   Drone Swarm   │
                    │   Visualization │
                    └─────────────────┘
```

---

## 9. Performance Metrics

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            PERFORMANCE METRICS                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Metric                     │ Value                                                       │
├────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Voice Recognition Accuracy │ ~90%                                                        │
│ End-to-End Latency         │ <1 second                                                   │
│ SSH Command Injection      │ <15 ms                                                      │
│ Concurrent SITL Agents     │ 8 (on Raspberry Pi 5)                                       │
│ Telemetry Update Rate      │ 10 Hz (configurable)                                        │
│ Network Resilience         │ Continues operation during temporary disconnection          │
└────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 10. Security Considerations

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY ARCHITECTURE                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ENCRYPTED COMMAND CHANNEL                                                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│   Ground Station                        Flight Host                                     │
│   ┌─────────────┐                       ┌─────────────┐                                │
│   │ SSH Client  │───────────────────────│ SSH Server  │                                │
│   │ (Ed25519)   │   Encrypted Tunnel    │ (OpenSSH)   │                                │
│   └─────────────┘                       └─────────────┘                                │
│                                                                                         │
│   Key-Based Authentication:                                                             │
│   • Public Key:  ~/.ssh/id_ed25519.pub (on Pi authorized_keys)                         │
│   • Private Key: ~/.ssh/id_ed25519 (on Mac, never shared)                              │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘

Security Best Practices:
• SSH key authentication (no passwords)
• MAVLink message signing (optional)
• Network isolation (dedicated WiFi)
• Firewall rules on Flight Host
```

---

## Summary

This Split-Node architecture enables:

1. **Natural Language Control**: Voice commands translated to drone actions
2. **Scalable Swarm Simulation**: 8 concurrent agents on edge hardware
3. **Low Latency**: <1 second end-to-end response time
4. **Network Resilience**: Continues operation during disconnections
5. **Secure Communication**: Encrypted SSH tunnel for commands
6. **Real-Time Visualization**: QGroundControl telemetry display

The "eyes-up" paradigm shifts operator focus from low-level piloting to high-level mission command, enabling intuitive human-swarm interaction for precision agriculture and related applications.
