#!/bin/bash
# =============================================================================
# Swarm Startup Script
# =============================================================================
# Starts the 8-drone SITL swarm simulation on Raspberry Pi
#
# Usage: ./start_swarm.sh [MAC_IP]
# Example: ./start_swarm.sh 192.168.0.82
# =============================================================================

# Default Mac IP address (Ground Station)
MAC_IP="${1:-192.168.0.82}"

echo "=============================================="
echo "  Starting Drone Swarm Simulation"
echo "=============================================="
echo "Ground Station IP: $MAC_IP"
echo ""

# Check if tmux session already exists
if tmux has-session -t swarm 2>/dev/null; then
    echo "[WARNING] Swarm session already exists!"
    echo "To kill existing session: tmux kill-session -t swarm"
    echo "To attach to session: tmux attach -t swarm"
    exit 1
fi

# Navigate to ArduCopter directory
cd ~/ardupilot/ArduCopter || {
    echo "[ERROR] ArduPilot not found at ~/ardupilot"
    exit 1
}

# Create new tmux session
echo "Creating tmux session 'swarm'..."
tmux new-session -d -s swarm

# Start the simulation
echo "Launching 8 SITL instances..."
tmux send-keys -t swarm "sim_vehicle.py -v Copter -f quad -w --no-rebuild \
  --count 8 --auto-sysid --location RUNWAYSTART \
  --swarm ~/swarm_2cols_4rows_topdown.txt --mcast \
  --out=udp:${MAC_IP}:14550 \
  --out=udp:${MAC_IP}:14551" Enter

echo ""
echo "=============================================="
echo "  Swarm Started Successfully"
echo "=============================================="
echo ""
echo "Commands:"
echo "  Attach to session:  tmux attach -t swarm"
echo "  List sessions:      tmux ls"
echo "  Kill session:       tmux kill-session -t swarm"
echo ""
echo "MAVProxy Quick Reference:"
echo "  module load swarm       - Load swarm module"
echo "  alllinks mode GUIDED    - Set all to GUIDED mode"
echo "  alllinks arm throttle   - Arm all vehicles"
echo "  alllinks takeoff 10     - Takeoff to 10m"
echo "  alllinks mode RTL       - Return to launch"
echo ""
echo "Telemetry streaming to: udp://${MAC_IP}:14550"
echo ""
