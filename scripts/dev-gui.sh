#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse command line arguments
MODE="run"
EXTRA_ARGS=()
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            MODE="check"
            shift
            ;;
        --help)
            MODE="help"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

# Display help
show_help() {
    echo -e "${BLUE}GPU OC GUI Development Runner${NC}"
    echo ""
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --check         Validate setup without running"
    echo "  --verbose       Enable verbose output (warnings, tracebacks)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")              # Run the GUI"
    echo "  $(basename "$0") --check      # Verify prerequisites"
    echo "  $(basename "$0") --verbose    # Verbose output"
}

# Check prerequisites
check_setup() {
    echo -e "${BLUE}=== Development Environment Check ===${NC}"
    
    local all_good=true
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓ Python 3${NC} ($py_version)"
    else
        echo -e "${RED}✗ Python 3 not found${NC}"
        all_good=false
    fi
    
    # Check venv
    if [ -d "$DIR/.venv" ]; then
        echo -e "${GREEN}✓ Virtual environment${NC} exists"
    else
        echo -e "${YELLOW}⚠ Virtual environment${NC} not found (will be created)"
    fi
    
    # Check PyQt6
    if python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
        echo -e "${GREEN}✓ PyQt6${NC} installed"
    else
        echo -e "${YELLOW}⚠ PyQt6${NC} not found (needed for GUI)"
    fi
    
    # Check IPC socket
    if [ -S /tmp/gpu-oc.sock ]; then
        echo -e "${GREEN}✓ GPU OC service${NC} is running (IPC socket active)"
    else
        echo -e "${YELLOW}⚠ GPU OC service${NC} not running (GUI will show connection error)"
    fi
    
    echo ""
    
    if [ "$all_good" = true ]; then
        echo -e "${GREEN}✓ Setup looks good!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some issues found (may still work for testing)${NC}"
        return 0
    fi
}

# Setup virtual environment
setup_venv() {
    if [ ! -d "$DIR/.venv" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python3 -m venv "$DIR/.venv"
        "$DIR/.venv/bin/pip" install -q -U pip
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    echo -e "${BLUE}Installing dependencies...${NC}"
    "$DIR/.venv/bin/pip" install -q -e "$DIR"
    
    # Install PyQt6
    if ! "$DIR/.venv/bin/pip" show PyQt6 &> /dev/null 2>&1; then
        echo -e "${BLUE}Installing PyQt6...${NC}"
        "$DIR/.venv/bin/pip" install -q PyQt6
    fi
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Main execution
case $MODE in
    help)
        show_help
        exit 0
        ;;
    check)
        check_setup
        exit 0
        ;;
    run)
        setup_venv
        echo -e "${GREEN}Launching GPU OC GUI...${NC}"
        
        if [ "$VERBOSE" = true ]; then
            echo -e "${BLUE}(Verbose mode enabled)${NC}"
            cd "$DIR"
            exec "$DIR/.venv/bin/python" -W all -u -m gpu_oc.ui.app "${EXTRA_ARGS[@]}"
        else
            cd "$DIR"
            exec "$DIR/.venv/bin/python" -m gpu_oc.ui.app "${EXTRA_ARGS[@]}"
        fi
        ;;
esac
