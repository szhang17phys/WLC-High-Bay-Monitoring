#!/bin/bash
# WLC High Bay Monitoring - Setup Script
# Automated setup for new installations

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     WLC High Bay Particle Monitoring - Setup Script              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Check Python version ─────────────────────────────────────────────

echo -e "${BLUE}[1/7] Checking Python version...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found!${NC}"
    echo "Please install Python 3.8 or newer and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo -e "${RED}✗ Python 3.8+ required (found: $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# ─── Step 2: Install Python dependencies ──────────────────────────────────────

echo -e "${BLUE}[2/7] Installing Python dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."

    # Try regular pip install first
    if python3 -m pip install -r requirements.txt --quiet 2>/dev/null; then
        echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
    else
        # Try with --user flag if system install fails
        echo -e "${YELLOW}⚠ System install failed, trying --user install...${NC}"
        if python3 -m pip install --user -r requirements.txt --quiet 2>/dev/null; then
            echo -e "${GREEN}✓ Dependencies installed (user mode)${NC}"
        else
            echo -e "${YELLOW}⚠ Automated install failed${NC}"
            echo "Please install manually:"
            echo "  pip3 install pymodbus>=3.5 pyyaml>=6.0"
            echo "Or:"
            echo "  pip3 install --user pymodbus>=3.5 pyyaml>=6.0"
            echo ""
            read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
        fi
    fi
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

echo ""

# ─── Step 3: Get counter IP address ───────────────────────────────────────────

echo -e "${BLUE}[3/7] Configuring particle counter connection...${NC}"
echo ""

read -p "Enter particle counter IP address [default: 10.66.66.68]: " COUNTER_IP
COUNTER_IP=${COUNTER_IP:-10.66.66.68}

read -p "Enter Modbus port [default: 502]: " COUNTER_PORT
COUNTER_PORT=${COUNTER_PORT:-502}

read -p "Enter counter admin password (leave empty if none): " COUNTER_PASSWORD

echo ""
echo -e "${GREEN}✓ Counter configuration:${NC}"
echo "  IP: $COUNTER_IP"
echo "  Port: $COUNTER_PORT"
echo ""

# ─── Step 4: Test counter connectivity ────────────────────────────────────────

echo -e "${BLUE}[4/7] Testing counter connectivity...${NC}"

# Create a temporary test script
cat > /tmp/test_counter_$$.py << 'EOF'
import sys
from pymodbus.client import ModbusTcpClient

counter_ip = sys.argv[1]
counter_port = int(sys.argv[2])

try:
    client = ModbusTcpClient(counter_ip, port=counter_port, timeout=5)
    if client.connect():
        print("SUCCESS")
        client.close()
    else:
        print("FAILED")
except Exception as e:
    print(f"ERROR: {e}")
EOF

TEST_RESULT=$(python3 /tmp/test_counter_$$.py "$COUNTER_IP" "$COUNTER_PORT" 2>&1)
rm -f /tmp/test_counter_$$.py

if [[ "$TEST_RESULT" == "SUCCESS" ]]; then
    echo -e "${GREEN}✓ Successfully connected to counter at $COUNTER_IP:$COUNTER_PORT${NC}"
else
    echo -e "${YELLOW}⚠ Could not connect to counter: $TEST_RESULT${NC}"
    echo "The counter may be offline or unreachable."
    echo "You can still continue setup and test connectivity later."
    echo ""
    read -p "Continue anyway? [Y/n]: " CONTINUE
    CONTINUE=${CONTINUE:-Y}
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

echo ""

# ─── Step 5: Create configuration file ────────────────────────────────────────

echo -e "${BLUE}[5/7] Creating configuration file...${NC}"
echo ""

read -p "Do you want to enable GitHub Pages auto-push? [y/N]: " ENABLE_GITHUB
ENABLE_GITHUB=${ENABLE_GITHUB:-N}

if [[ "$ENABLE_GITHUB" =~ ^[Yy]$ ]]; then
    GITHUB_ENABLED="true"
    echo -e "${YELLOW}⚠ GitHub push enabled${NC}"
    echo "Make sure you have:"
    echo "  1. Forked this repo to your GitHub account"
    echo "  2. Set up SSH key or token for git push"
    echo "  3. Enabled GitHub Pages in repo settings"
else
    GITHUB_ENABLED="false"
    echo -e "${GREEN}✓ GitHub push disabled (monitoring only)${NC}"
fi

# Get project data directory
echo ""
echo "The system needs a directory to store the permanent data archive."
echo "Options:"
echo "  1. System directory (e.g., /project/dune/slow_control/particle_plus)"
echo "  2. User home directory (e.g., ~/particle_data)"
echo "  3. Local repo directory (./data - simplest, always works)"
echo ""
read -p "Choose option [1/2/3, default: 3]: " DIR_CHOICE
DIR_CHOICE=${DIR_CHOICE:-3}

case $DIR_CHOICE in
    1)
        read -p "Enter system directory path: " PROJECT_DIR
        ;;
    2)
        PROJECT_DIR="$HOME/particle_data"
        echo "Using: $PROJECT_DIR"
        ;;
    3)
        PROJECT_DIR="./data"
        echo "Using: $PROJECT_DIR (local repo directory)"
        ;;
    *)
        PROJECT_DIR="./data"
        echo "Invalid choice, using: $PROJECT_DIR"
        ;;
esac

# Create config.local.yaml
cat > config.local.yaml << EOF
# Local configuration - created by setup.sh
# This file is gitignored (your personal settings)

counter:
  ip: '$COUNTER_IP'
  port: $COUNTER_PORT
  password: '$COUNTER_PASSWORD'

paths:
  project_data_dir: '$PROJECT_DIR'

github:
  enabled: $GITHUB_ENABLED

# Other settings inherited from config.yaml
EOF

echo -e "${GREEN}✓ Created config.local.yaml${NC}"
echo ""

# ─── Step 6: Create necessary directories ─────────────────────────────────────

echo -e "${BLUE}[6/7] Creating data directories...${NC}"

# Always create local data directory (fallback)
mkdir -p data
echo -e "${GREEN}✓ Created data/ directory (fallback)${NC}"

# Handle project data directory creation with smart fallback
if [ "$PROJECT_DIR" = "./data" ]; then
    # User chose local directory - already created
    echo -e "${GREEN}✓ Using local data/ directory (already created)${NC}"
    ACTUAL_ARCHIVE_DIR="$PROJECT_DIR"
elif mkdir -p "$PROJECT_DIR" 2>/dev/null; then
    # Successfully created
    echo -e "${GREEN}✓ Created $PROJECT_DIR${NC}"
    ACTUAL_ARCHIVE_DIR="$PROJECT_DIR"
else
    # Failed to create - offer sudo option
    echo -e "${YELLOW}⚠ Could not create $PROJECT_DIR (permission denied)${NC}"
    echo ""
    echo "Options:"
    echo "  1. Try with sudo (requires admin password)"
    echo "  2. Use ~/particle_data instead (your home directory)"
    echo "  3. Use ./data instead (local repo directory)"
    echo ""
    read -p "Choose option [1/2/3, default: 3]: " FALLBACK_CHOICE
    FALLBACK_CHOICE=${FALLBACK_CHOICE:-3}

    case $FALLBACK_CHOICE in
        1)
            echo "Attempting to create directory with sudo..."
            if sudo mkdir -p "$PROJECT_DIR" 2>/dev/null; then
                sudo chown $USER:$(id -gn) "$PROJECT_DIR"
                echo -e "${GREEN}✓ Created $PROJECT_DIR with sudo${NC}"
                ACTUAL_ARCHIVE_DIR="$PROJECT_DIR"
            else
                echo -e "${RED}✗ sudo creation failed${NC}"
                echo "Falling back to local data/ directory"
                ACTUAL_ARCHIVE_DIR="./data"
                PROJECT_DIR="./data"
            fi
            ;;
        2)
            PROJECT_DIR="$HOME/particle_data"
            mkdir -p "$PROJECT_DIR"
            echo -e "${GREEN}✓ Using $PROJECT_DIR${NC}"
            ACTUAL_ARCHIVE_DIR="$PROJECT_DIR"
            ;;
        3)
            PROJECT_DIR="./data"
            echo -e "${GREEN}✓ Using local data/ directory${NC}"
            ACTUAL_ARCHIVE_DIR="./data"
            ;;
        *)
            PROJECT_DIR="./data"
            echo -e "${GREEN}✓ Using local data/ directory${NC}"
            ACTUAL_ARCHIVE_DIR="./data"
            ;;
    esac
fi

echo ""

# ─── Step 7: Test the installation ────────────────────────────────────────────

echo -e "${BLUE}[7/7] Testing installation...${NC}"

# Test if particle_plus.py can be imported
if python3 -c "import particle_plus" 2>/dev/null; then
    echo -e "${GREEN}✓ particle_plus.py loads successfully${NC}"
else
    echo -e "${RED}✗ Failed to load particle_plus.py${NC}"
    echo "Please check the error messages above."
    exit 1
fi

echo ""

# ─── Summary ───────────────────────────────────────────────────────────────────

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✓ SETUP COMPLETE!                              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Configuration Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Counter IP:       $COUNTER_IP:$COUNTER_PORT"
echo "GitHub push:      $GITHUB_ENABLED"
echo "Data directory:   data/"
echo "Archive directory: $PROJECT_DIR"
echo "Config file:      config.local.yaml"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "$TEST_RESULT" == "SUCCESS" ]]; then
    echo -e "${GREEN}1. Your counter is online and reachable!${NC}"
    echo ""
    echo "2. Start monitoring with:"
    echo -e "   ${YELLOW}python3 particle_plus.py --all${NC}"
    echo ""
    echo "   Or run in background (tmux/screen):"
    echo -e "   ${YELLOW}tmux new -s particle${NC}"
    echo -e "   ${YELLOW}python3 particle_plus.py --all${NC}"
    echo -e "   ${YELLOW}# Press Ctrl+B, D to detach${NC}"
else
    echo -e "${YELLOW}1. Counter is not reachable yet${NC}"
    echo "   Make sure the counter is:"
    echo "     • Powered on"
    echo "     • Connected to network"
    echo "     • Accessible from this machine"
    echo ""
    echo "2. Test connectivity:"
    echo -e "   ${YELLOW}python3 test.py${NC}"
    echo ""
    echo "3. Once connected, start monitoring:"
    echo -e "   ${YELLOW}python3 particle_plus.py --all${NC}"
fi

echo ""
echo "3. View local dashboard:"
echo -e "   ${YELLOW}python3 local_serve.py --port 8800${NC}"
echo "   Then open http://localhost:8800"
echo ""

if [[ "$GITHUB_ENABLED" == "true" ]]; then
    echo -e "${YELLOW}4. GitHub push is ENABLED${NC}"
    echo "   • Make sure git is configured:"
    echo -e "     ${YELLOW}git config user.name \"Your Name\"${NC}"
    echo -e "     ${YELLOW}git config user.email \"your@email.com\"${NC}"
    echo "   • Set up SSH key or personal access token"
    echo "   • Test push access:"
    echo -e "     ${YELLOW}git push origin main${NC}"
else
    echo -e "${GREEN}4. GitHub push is DISABLED (monitoring only)${NC}"
    echo "   To enable later, edit config.local.yaml:"
    echo "     github:"
    echo "       enabled: true"
fi

echo ""
echo "Documentation:"
echo "  • README.md - Full documentation"
echo "  • GITHUB_PUSH_SETUP.md - GitHub configuration guide"
echo "  • config.yaml - Configuration reference"
echo ""
echo -e "${GREEN}Happy monitoring! 🎉${NC}"
echo ""
