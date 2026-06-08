#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Check if running as root for GPU/watchdog access
if [[ "$EUID" -ne 0 ]]; then 
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
   echo "GPU control and watchdog require root privileges."
   exit 1
fi

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
        --reload)
            MODE="reload"
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
    echo -e "${BLUE}GPU OC Development Runner${NC}"
    echo ""
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --check         Validate setup without running"
    echo "  --verbose       Enable verbose output (warnings, tracebacks)"
    echo "  --reload        Run with auto-reload on file changes (requires watchdog)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")                # Run the app"
    echo "  $(basename "$0") --check        # Verify prerequisites"
    echo "  $(basename "$0") --verbose      # Verbose output with warnings"
    echo "  $(basename "$0") --reload       # Auto-reload on file changes"
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
    
    # Check NVIDIA drivers
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ NVIDIA drivers${NC} installed"
    else
        echo -e "${YELLOW}⚠ NVIDIA drivers${NC} not detected (needed for GPU control)"
    fi
    
    # Check venv
    if [ -d "$DIR/.venv" ]; then
        echo -e "${GREEN}✓ Virtual environment${NC} exists"
    else
        echo -e "${YELLOW}⚠ Virtual environment${NC} not found (will be created)"
    fi
    
    # Check config
    if [ -f "$DIR/config/config.toml" ]; then
        echo -e "${GREEN}✓ config.toml${NC} exists"
    else
        if [ -f "$DIR/config/config.toml.example" ]; then
            echo -e "${YELLOW}⚠ config.toml${NC} not found (example exists)"
        else
            echo -e "${RED}✗ config.toml and example${NC} not found"
            all_good=false
        fi
    fi
    
    # Check root (for watchdog/GPU access)
    if [ "$EUID" -eq 0 ]; then
        echo -e "${GREEN}✓ Running as root${NC}"
    else
        echo -e "${YELLOW}⚠ Not running as root${NC} (watchdog/GPU access limited)"
    fi
    
    echo ""
    
    if [ "$all_good" = true ]; then
        echo -e "${GREEN}✓ Setup looks good!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some issues found (may still work for basic testing)${NC}"
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
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Ensure config exists
ensure_config() {
    if [ ! -f "$DIR/config/config.toml" ]; then
        if [ -f "$DIR/config/config.toml.example" ]; then
            echo -e "${YELLOW}Copying config.toml.example to config.toml${NC}"
            cp "$DIR/config/config.toml.example" "$DIR/config/config.toml"
            echo -e "${YELLOW}⚠ Edit config/config.toml with your settings before running!${NC}"
        fi
    fi
}

# Run with auto-reload
run_with_reload() {
    # Check for watchdog/reloader
    if ! "$DIR/.venv/bin/pip" show watchfiles &> /dev/null 2>&1; then
        echo -e "${YELLOW}Installing watchfiles for auto-reload...${NC}"
        "$DIR/.venv/bin/pip" install -q watchfiles
    fi
    
    echo -e "${BLUE}Running with auto-reload (Ctrl+C to stop)${NC}"
    echo -e "${YELLOW}Watching for changes in gpu_oc/ directory...${NC}"
    
    export GPU_OC_CONFIG="$DIR/config/config.toml"
    
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}(Verbose mode enabled)${NC}"
        exec "$DIR/.venv/bin/watchfiles" "$DIR/.venv/bin/python" "-W" "all" "-u" "-m" "gpu_oc.app"
    else
        exec "$DIR/.venv/bin/watchfiles" "$DIR/.venv/bin/python" "-m" "gpu_oc.app"
    fi
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
    reload)
        setup_venv
        ensure_config
        run_with_reload
        ;;
    run)
        setup_venv
        ensure_config
        echo -e "${GREEN}Starting GPU OC app...${NC}"
        export GPU_OC_CONFIG="$DIR/config/config.toml"
        
        if [ "$VERBOSE" = true ]; then
            echo -e "${BLUE}(Verbose mode enabled)${NC}"
            exec "$DIR/.venv/bin/python" -W all -u "${EXTRA_ARGS[@]}" -m gpu_oc.app
        else
            exec "$DIR/.venv/bin/python" "${EXTRA_ARGS[@]}" -m gpu_oc.app
        fi
        ;;
esac