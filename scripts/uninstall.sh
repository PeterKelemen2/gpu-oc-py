#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVICE_NAME="gpu-oc.service"
INSTALL_DIR="/opt/gpu-oc"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo -e "${GREEN}=== GPU OC Uninstallation ===${NC}"

# Check if running as root
if [[ "$EUID" -ne 0 ]]; then 
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Confirmation prompt
echo -e "${YELLOW}This will:${NC}"
echo "  • Stop the gpu-oc service"
echo "  • Disable autostart"
echo "  • Remove /etc/systemd/system/gpu-oc.service"
echo "  • Delete all files in $INSTALL_DIR"
echo ""
read -p "Continue with uninstallation? (yes/no): " -r response
if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop the service if it's running
if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null || true; then
        echo -e "${GREEN}Stopping $SERVICE_NAME...${NC}"
        systemctl stop "$SERVICE_NAME" || true
    fi

    # Disable the service
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null || true; then
        echo -e "${GREEN}Disabling $SERVICE_NAME...${NC}"
        systemctl disable "$SERVICE_NAME" || true
    fi
else
    echo -e "${YELLOW}Warning: systemctl not found, skipping service management${NC}"
fi

# Remove systemd service file
if [ -f "$SERVICE_PATH" ]; then
    echo -e "${GREEN}Removing systemd unit $SERVICE_PATH...${NC}"
    rm -f "$SERVICE_PATH"
    echo -e "${GREEN}✓ Service file removed${NC}"
fi

# Reload systemd daemon
if command -v systemctl >/dev/null 2>&1; then
    echo -e "${GREEN}Reloading systemd daemon...${NC}"
    systemctl daemon-reload
    systemctl reset-failed || true
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${GREEN}Removing installation directory $INSTALL_DIR...${NC}"
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✓ Installation directory removed${NC}"
fi

echo ""
echo -e "${GREEN}=== Uninstallation Complete ===${NC}"
echo "The GPU OC service has been cleanly removed from your system."
