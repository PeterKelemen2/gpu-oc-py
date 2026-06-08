#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GPU OC GUI Launcher ===${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Check if systemd service is running
if ! systemctl is-active --quiet gpu-oc 2>/dev/null; then
    echo -e "${YELLOW}Warning: GPU OC service is not running${NC}"
    read -p "Start the service now? (yes/no): " -r response || true
    if [[ "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Starting gpu-oc service..."
        sudo systemctl start gpu-oc
        echo -e "${GREEN}✓ Service started${NC}"
        sleep 2
    else
        echo -e "${YELLOW}Note: The GUI can still run, but OC control won't be available${NC}"
    fi
fi

# Check if PyQt6 is installed
if ! python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
    echo -e "${RED}Error: PyQt6 not installed${NC}"
    echo "Install with: pip install PyQt6"
    exit 1
fi

echo -e "${GREEN}Launching GPU OC GUI...${NC}"

# Change to project root and launch the GUI
cd "$PROJECT_ROOT"
exec python3 -m gpu_oc.ui.app

