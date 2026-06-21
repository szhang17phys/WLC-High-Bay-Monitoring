# Testing setup.sh

## Quick Test (Default Values)

```bash
./setup.sh

# When prompted, just press Enter for all defaults:
# - Counter IP: 10.66.66.68 (press Enter)
# - Port: 502 (press Enter)
# - Password: (press Enter - empty)
# - GitHub push: N (press Enter - disabled)
# - Project dir: (press Enter - default)
```

## Expected Output

```
╔═══════════════════════════════════════════════════════════════════╗
║     WLC High Bay Particle Monitoring - Setup Script              ║
╚═══════════════════════════════════════════════════════════════════╝

[1/7] Checking Python version...
✓ Python 3.X found

[2/7] Installing Python dependencies...
✓ Dependencies installed successfully

[3/7] Configuring particle counter connection...
(prompts for IP, port, password)

[4/7] Testing counter connectivity...
⚠ Could not connect to counter (normal if counter offline)

[5/7] Creating configuration file...
✓ Created config.local.yaml

[6/7] Creating data directories...
✓ Created data/ directory

[7/7] Testing installation...
✓ particle_plus.py loads successfully

╔═══════════════════════════════════════════════════════════════════╗
║                    ✓ SETUP COMPLETE!                              ║
╚═══════════════════════════════════════════════════════════════════╝
```

## What It Creates

- `config.local.yaml` - Your local configuration
- `data/` directory - For local data storage
- Optionally: project data directory

## After Setup

Run monitoring:
```bash
python3 particle_plus.py --all
```

Or test with a single sync:
```bash
python3 particle_plus.py --sync
```
