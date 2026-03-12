#!/bin/bash
# =============================================================================
# Flight Host Setup Script for Raspberry Pi 4/5
# =============================================================================
# This script sets up the Raspberry Pi as a headless SITL flight host
# for the voice-controlled drone swarm system.
#
# Usage: ./setup_flight_host.sh
# =============================================================================

set -e

echo "=============================================="
echo "  Voice-Controlled Drone - Flight Host Setup"
echo "=============================================="

# Update system
echo "[1/6] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "[2/6] Installing required packages..."
sudo apt install -y \
    git \
    python3-pip \
    python3-dev \
    python3-opencv \
    tmux \
    xvfb \
    screen \
    build-essential \
    ccache \
    g++ \
    gawk \
    libxml2-dev \
    libxslt1-dev

# Install Python packages
echo "[3/6] Installing Python packages..."
pip3 install --user \
    pymavlink \
    MAVProxy \
    dronekit \
    numpy

# Clone ArduPilot (if not already present)
echo "[4/6] Setting up ArduPilot..."
if [ ! -d "$HOME/ardupilot" ]; then
    cd ~
    git clone https://github.com/ArduPilot/ardupilot.git
    cd ardupilot
    git submodule update --init --recursive
    
    # Install ArduPilot prerequisites
    Tools/environment_install/install-prereqs-ubuntu.sh -y
else
    echo "ArduPilot already installed, updating..."
    cd ~/ardupilot
    git pull
    git submodule update --init --recursive
fi

# Create swarm configuration directory
echo "[5/6] Creating configuration files..."
mkdir -p ~/swarm_configs

# Create swarm layout file (2 columns x 4 rows)
cat > ~/swarm_2cols_4rows_topdown.txt << 'EOF'
# Swarm Layout: 2 columns x 4 rows
# Format: SYSID, X_OFFSET, Y_OFFSET
1,0,0
2,0,5
3,5,0
4,5,5
5,10,0
6,10,5
7,15,0
8,15,5
EOF

# Create formation script
cat > ~/swarm_formation.txt << 'EOF'
vehicle 1
mode GUIDED
guided 20 0 10
vehicle 2
mode GUIDED
guided 20 10 10
vehicle 3
mode GUIDED
guided 20 -10 10
vehicle 4
mode GUIDED
guided 30 0 10
vehicle 5
mode GUIDED
guided 30 10 10
vehicle 6
mode GUIDED
guided 30 -10 10
vehicle 7
mode GUIDED
guided 40 0 10
vehicle 8
mode GUIDED
guided 40 10 10
EOF

# Create startup script
cat > ~/start_swarm.sh << 'EOF'
#!/bin/bash
# Start 8-drone swarm simulation

# Get Mac IP (modify as needed)
MAC_IP="${1:-192.168.0.82}"

echo "Starting swarm simulation..."
echo "Telemetry will be sent to: $MAC_IP"

cd ~/ardupilot/ArduCopter

# Start in tmux session
tmux new-session -d -s swarm

# Run sim_vehicle with swarm configuration
tmux send-keys -t swarm "sim_vehicle.py -v Copter -f quad -w --no-rebuild \
  --count 8 --auto-sysid --location RUNWAYSTART \
  --swarm ~/swarm_2cols_4rows_topdown.txt --mcast \
  --out=udp:${MAC_IP}:14550" Enter

echo "Swarm started in tmux session 'swarm'"
echo "Use 'tmux attach -t swarm' to view console"
EOF

chmod +x ~/start_swarm.sh

# Add to PATH
echo "[6/6] Configuring environment..."
if ! grep -q "ardupilot" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# ArduPilot paths" >> ~/.bashrc
    echo "export PATH=\$PATH:\$HOME/ardupilot/Tools/autotest" >> ~/.bashrc
    echo "export PATH=\$PATH:\$HOME/.local/bin" >> ~/.bashrc
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Reboot: sudo reboot"
echo "  2. Start swarm: ~/start_swarm.sh <MAC_IP>"
echo "  3. Attach to session: tmux attach -t swarm"
echo ""
echo "MAVProxy commands:"
echo "  module load swarm"
echo "  alllinks mode GUIDED"
echo "  alllinks arm throttle"
echo "  alllinks takeoff 10"
echo ""
