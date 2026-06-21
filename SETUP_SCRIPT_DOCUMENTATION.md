# setup.sh - Automated Installation Script

## Purpose

The `setup.sh` script automates the entire installation process for new users, making it possible to go from "git clone" to "running monitoring" in just a few minutes.

---

## What It Does

### 7-Step Installation Process:

1. **Check Python Version**
   - Verifies Python 3.8+ is installed
   - Exits with error if version is too old

2. **Install Dependencies**
   - Installs pymodbus and pyyaml from requirements.txt
   - Tries system install first
   - Falls back to --user install if needed
   - Continues even if install fails (with warning)

3. **Configure Counter Connection**
   - Prompts for counter IP (default: 10.66.66.68)
   - Prompts for Modbus port (default: 502)
   - Prompts for admin password (optional)

4. **Test Counter Connectivity**
   - Attempts to connect to the counter
   - Reports success or failure
   - Allows continuing even if offline (for pre-deployment setup)

5. **Create Configuration File**
   - Prompts: Enable GitHub Pages push? (default: No)
   - Prompts: Project data directory path
   - Creates `config.local.yaml` with settings
   - GitHub push is **DISABLED by default** (safe!)

6. **Create Directories**
   - Creates `data/` directory
   - Attempts to create project data directory
   - Continues if project directory creation fails

7. **Test Installation**
   - Verifies particle_plus.py can be imported
   - Reports success or failure

---

## Usage

### Basic Usage (Recommended)

```bash
# Clone the repository
git clone https://github.com/Rohit-Raut/WLC-High-Bay-Monitoring.git
cd WLC-High-Bay-Monitoring

# Run setup script
chmod +x setup.sh
./setup.sh
```

### What You'll Be Asked

1. **Counter IP address** - Enter your counter's IP or press Enter for default (10.66.66.68)
2. **Modbus port** - Press Enter for default (502)
3. **Admin password** - Press Enter if no password set
4. **Enable GitHub push?** - Press Enter for No (monitoring only - safe default)
5. **Project data directory** - Press Enter for default path

### Example Session

```
╔═══════════════════════════════════════════════════════════════════╗
║     WLC High Bay Particle Monitoring - Setup Script              ║
╚═══════════════════════════════════════════════════════════════════╝

[1/7] Checking Python version...
✓ Python 3.10 found

[2/7] Installing Python dependencies...
Installing from requirements.txt...
✓ Dependencies installed successfully

[3/7] Configuring particle counter connection...

Enter particle counter IP address [default: 10.66.66.68]: 192.168.1.100
Enter Modbus port [default: 502]: 
Enter counter admin password (leave empty if none): 

✓ Counter configuration:
  IP: 192.168.1.100
  Port: 502

[4/7] Testing counter connectivity...
✓ Successfully connected to counter at 192.168.1.100:502

[5/7] Creating configuration file...

Do you want to enable GitHub Pages auto-push? [y/N]: n
✓ GitHub push disabled (monitoring only)
Enter project data directory [default: /project/dune/slow_control/particle_plus]: 
✓ Created config.local.yaml

[6/7] Creating data directories...
✓ Created data/ directory
✓ Created /project/dune/slow_control/particle_plus

[7/7] Testing installation...
✓ particle_plus.py loads successfully

╔═══════════════════════════════════════════════════════════════════╗
║                    ✓ SETUP COMPLETE!                              ║
╚═══════════════════════════════════════════════════════════════════╝

Configuration Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Counter IP:       192.168.1.100:502
GitHub push:      false
Data directory:   data/
Archive directory: /project/dune/slow_control/particle_plus
Config file:      config.local.yaml

Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Your counter is online and reachable!

2. Start monitoring with:
   python3 particle_plus.py --all

   Or run in background (tmux/screen):
   tmux new -s particle
   python3 particle_plus.py --all
   # Press Ctrl+B, D to detach

3. View local dashboard:
   python3 local_serve.py --port 8800
   Then open http://localhost:8800

4. GitHub push is DISABLED (monitoring only)
   To enable later, edit config.local.yaml:
     github:
       enabled: true

Happy monitoring! 🎉
```

---

## What Gets Created

After running setup.sh, you'll have:

### Files Created:
- `config.local.yaml` - Your local configuration (gitignored)

### Directories Created:
- `data/` - Local data storage
- Project data directory (if specified and permissions allow)

### Dependencies Installed:
- `pymodbus>=3.5` - Modbus TCP communication
- `pyyaml>=6.0` - Configuration file support

---

## Safety Features

### 1. GitHub Push Disabled by Default
- **Never** enables GitHub push without explicit user consent
- Defaults to "No" when asked
- Safe for universities forking the repo

### 2. Connectivity Test
- Tests counter connection before finishing
- Allows continuing even if offline (for pre-deployment)
- Clear error messages if connection fails

### 3. Graceful Degradation
- Continues even if pip install fails (with instructions)
- Continues even if project directory can't be created
- Allows proceeding if counter is offline

### 4. Input Validation
- All inputs have sensible defaults
- Port numbers validated as integers
- No destructive operations

---

## Troubleshooting

### Python Version Too Old

```
✗ Python 3.8+ required (found: 3.7)
```

**Solution:** Install Python 3.8 or newer:
```bash
# Ubuntu/Debian
sudo apt install python3.10

# macOS
brew install python@3.10
```

### Dependency Install Fails

```
⚠ Automated install failed
Please install manually:
  pip3 install pymodbus>=3.5 pyyaml>=6.0
```

**Solution:** Install manually:
```bash
pip3 install --user pymodbus pyyaml
# or
sudo pip3 install pymodbus pyyaml
```

### Counter Not Reachable

```
⚠ Could not connect to counter
```

**Possible causes:**
1. Counter is powered off
2. Wrong IP address
3. Network firewall blocking port 502
4. Counter on different network segment

**Solution:** 
- Verify counter IP and network connectivity
- The script allows continuing anyway
- Test later with: `python3 test.py`

### Permission Denied (Project Directory)

```
⚠ Could not create /project/dune/slow_control/particle_plus (permission denied)
  Archive will be stored in local data/ directory instead.
```

**This is normal!** The script continues using the local data/ directory.

**To fix:** Create directory with sudo:
```bash
sudo mkdir -p /project/dune/slow_control/particle_plus
sudo chown $USER /project/dune/slow_control/particle_plus
./setup.sh  # Run again
```

### particle_plus.py Import Failed

```
✗ Failed to load particle_plus.py
```

**Solution:**
1. Check that you're in the correct directory
2. Check that requirements are installed: `python3 -c "import pymodbus; import yaml"`
3. Check for syntax errors in particle_plus.py

---

## Advanced Usage

### Unattended Installation (Automation)

For automated deployment, you can pre-answer prompts:

```bash
./setup.sh << EOF
192.168.1.100
502

n
/custom/data/path
EOF
```

### Skip Connectivity Test

The script allows continuing even if counter is offline, making it suitable for:
- Pre-deployment configuration
- Offline testing
- CI/CD pipelines

### Custom Config After Setup

After running setup.sh, you can manually edit `config.local.yaml`:

```yaml
counter:
  ip: '192.168.1.100'
  port: 502

sampling:
  sample_time_s: 120    # 2-minute samples
  hold_time_s: 600      # 10-minute intervals

github:
  enabled: true         # Enable GitHub push
  push_interval_s: 600  # Push every 10 minutes
```

---

## Comparison: setup.sh vs Manual Setup

| Task | With setup.sh | Manual |
|------|---------------|--------|
| Install dependencies | Automatic | `pip3 install -r requirements.txt` |
| Create config file | Interactive prompts | Copy & edit config.yaml |
| Test connectivity | Automatic | Run test.py manually |
| Create directories | Automatic | `mkdir -p data/` |
| Verify installation | Automatic | Test imports manually |
| **Total time** | **~2 minutes** | **~10-15 minutes** |

---

## For Developers

### Testing the Script

```bash
# Test with defaults (dry run)
./setup.sh

# Test with custom values
./setup.sh << EOF
10.1.2.3
502
mypassword
y
/tmp/test_data
EOF
```

### Modifying the Script

The script is organized in 7 clear sections. Each section:
- Has a clear echo header (e.g., "[3/7] Configuring...")
- Performs one logical task
- Provides clear success/failure feedback
- Allows continuing on non-fatal errors

To add a new step:
1. Add section header
2. Perform the task
3. Report success/failure
4. Update final summary if needed

---

## Security Considerations

### What the Script Does:
- ✅ Reads user input
- ✅ Creates configuration files
- ✅ Creates directories
- ✅ Installs Python packages (pymodbus, pyyaml)
- ✅ Tests network connectivity to counter

### What the Script Does NOT Do:
- ❌ Modify system files
- ❌ Require root/sudo
- ❌ Make network changes
- ❌ Enable services
- ❌ Modify firewall rules
- ❌ Access sensitive data

**GitHub push is DISABLED by default** - script explicitly asks before enabling.

---

## See Also

- [README.md](README.md) - Main documentation
- [GITHUB_PUSH_SETUP.md](GITHUB_PUSH_SETUP.md) - GitHub configuration
- [config.yaml](config.yaml) - Configuration reference
- [requirements.txt](requirements.txt) - Python dependencies
