#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GPU OC Installation ===${NC}"

# Check if running as root for file operations
if [[ "$EUID" -ne 0 ]]; then 
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Verify NVIDIA drivers are installed
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: NVIDIA drivers not found. Please install NVIDIA drivers first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ NVIDIA drivers detected${NC}"

# Check if watchdog device is available
if [[ ! -e /dev/watchdog ]]; then
    echo -e "${YELLOW}Warning: /dev/watchdog not found. Hardware watchdog recovery may not work.${NC}"
    echo -e "${YELLOW}  To enable watchdog, check your BIOS settings for hardware watchdog support.${NC}"
fi

# Create installation directory
mkdir -p /opt/gpu-oc
cp -r . /opt/gpu-oc

cd /opt/gpu-oc

echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv .venv
.venv/bin/pip install -q -e .

# Install GUI dependencies (optional)
echo -e "${GREEN}Installing GUI dependencies...${NC}"
.venv/bin/pip install -q PyQt6 || echo -e "${YELLOW}Warning: Failed to install PyQt6 (GUI will not work)${NC}"

echo -e "${GREEN}✓ Virtual environment created and dependencies installed${NC}"

# Ensure config directory exists
mkdir -p /opt/gpu-oc/config

# Check if config.toml exists
if [[ ! -f /opt/gpu-oc/config/config.toml ]]; then
    if [[ -f /opt/gpu-oc/config/config.toml.example ]]; then
        echo -e "${YELLOW}Warning: config.toml not found${NC}"
        echo -e "${YELLOW}Copying config.toml.example to config.toml${NC}"
        cp /opt/gpu-oc/config/config.toml.example /opt/gpu-oc/config/config.toml
        echo -e "${YELLOW}⚠ IMPORTANT: Edit /opt/gpu-oc/config/config.toml with your GPU settings before starting the service!${NC}"
    else
        echo -e "${RED}Error: Neither config.toml nor config.toml.example found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ config.toml found${NC}"
fi

# Copy systemd service file
cp systemd/gpu-oc.service /etc/systemd/system/
chmod 644 /etc/systemd/system/gpu-oc.service

# Install desktop launcher (optional GUI)
if [[ -f gpu-oc.desktop ]]; then
    echo -e "${GREEN}Installing desktop launcher...${NC}"
    cp gpu-oc.desktop /usr/share/applications/
    chmod 644 /usr/share/applications/gpu-oc.desktop
    echo -e "${GREEN}✓ Desktop launcher installed${NC}"
fi

echo -e "${GREEN}Registering systemd service...${NC}"
systemctl daemon-reload
systemctl enable gpu-oc

echo -e "${GREEN}=== Installation Complete ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review and configure GPU settings:"
echo "   sudo nano /opt/gpu-oc/config/config.toml"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start gpu-oc"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status gpu-oc"
echo "   sudo journalctl -u gpu-oc -f"
echo ""
echo "4. (Optional) Launch the desktop GUI:"
echo "   /opt/gpu-oc/scripts/gui.sh"
echo "   Or search for 'GPU OC Controller' in your application menu"
echo "   sudo journalctl -u gpu-oc -f"
echo ""
echo -e "${YELLOW}WARNING: Incorrect OC settings can damage your GPU!${NC}"
echo "Always test with conservative settings first."