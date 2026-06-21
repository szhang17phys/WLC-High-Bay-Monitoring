# GitHub Push Configuration

## 🔒 Safe Default Behavior

**By default, `particle_plus.py` runs in MONITORING ONLY mode:**
- ✅ Samples the particle counter
- ✅ Syncs data to CSV files
- ✅ Generates dashboard HTML locally
- ❌ **Does NOT push to GitHub**

This is intentional for safety:
- New users can run the script without accidentally pushing to someone else's GitHub
- Universities forking this repo won't push to Yale's GitHub Pages
- You can test the system locally before enabling GitHub integration

---

## 🎯 For New Installations (Other Universities)

When you fork/clone this repository:

1. **Just run it - no GitHub configuration needed:**
   ```bash
   python3 particle_plus.py --all
   ```
   Output will show:
   ```
   MODE: --all  (sample + live + dashboard)
     GitHub push: DISABLED (monitoring only)
     To enable: set github.enabled=true in config.local.yaml
   ```

2. **The system will:**
   - ✅ Monitor your particle counter
   - ✅ Save data locally
   - ✅ Generate `index.html` in the repo
   - ❌ NOT push to GitHub (safe!)

3. **To view the dashboard:**
   - Open `index.html` in a browser, or
   - Run `python3 local_serve.py --port 8800`

---

## 🚀 To Enable GitHub Pages (Optional)

**Only do this if you want automatic push to YOUR OWN GitHub Pages.**

### Prerequisites:
1. Fork this repo to your own GitHub account
2. Set up GitHub Pages in your repo settings (branch: `main`)
3. Configure git push access (SSH key or token)

### Steps:

1. **Create `config.local.yaml` in the repo root:**
   ```yaml
   # config.local.yaml
   github:
     enabled: true
   ```

2. **Restart the daemon:**
   ```bash
   python3 particle_plus.py --all
   ```

3. **Verify it's enabled:**
   You should see:
   ```
   MODE: --all  (sample + live + dashboard)
     GitHub push: ENABLED → /your/repo/path
   ```

4. **Check the log:**
   ```bash
   tail -f sync_log.txt
   ```
   You should see periodic messages:
   ```
   [INFO] Dashboard pushed to GitHub Pages
   ```

---

## 📝 Configuration File Priority

The system loads config in this order:

1. **`config.local.yaml`** (highest priority, gitignored)
   - Your personal settings
   - Not tracked in git
   - Perfect for enabling GitHub push

2. **`config.yaml`** (example/defaults)
   - Tracked in git
   - `github.enabled: false` by default
   - Safe for all users

3. **Hardcoded defaults** (fallback)
   - Used if config files don't exist
   - `github.enabled: false` (safe)

---

## 🔧 For Rohit (Yale Setup)

**Your noether setup:**

The repo already has `config.local.yaml` with:
```yaml
github:
  enabled: true
```

So YOUR daemon pushes to GitHub as before. Nothing changes for you.

When you `git pull` the new code, just make sure `config.local.yaml` exists with `enabled: true`.

---

## 🧪 Testing GitHub Push

**Test without actually pushing:**
```bash
# Run in monitoring-only mode (default)
python3 particle_plus.py --dashboard

# You'll see:
# MODE: --dashboard (GitHub push disabled)
#   Generating dashboard HTML locally only
#   To enable GitHub push: set github.enabled=true in config.local.yaml
```

**Test WITH GitHub push (after enabling):**
```bash
# Create config.local.yaml with enabled: true
# Then:
python3 particle_plus.py --dashboard

# You'll see:
# MODE: --dashboard (GitHub push enabled)
# Git: add data/live.csv → OK
# Git: commit → OK
# Git: push → OK
# Dashboard pushed to GitHub Pages
```

---

## ⚠️ Troubleshooting

**"GitHub push disabled" but I want it enabled:**
- Check if `config.local.yaml` exists
- Make sure it has `github.enabled: true`
- Restart `particle_plus.py`

**Git push fails with authentication error:**
- Set up SSH key or personal access token
- Test: `git push origin main` manually
- Make sure your user has write access to the repo

**Still confused?**
- Check the log messages at startup
- Look for "GitHub push: ENABLED" or "DISABLED"
- Read `sync_log.txt` for detailed error messages

---

## 📊 Summary

| Scenario | Config | Behavior |
|----------|--------|----------|
| Fresh clone (no config) | None | ✅ Monitoring only (safe) |
| Default `config.yaml` | `enabled: false` | ✅ Monitoring only (safe) |
| With `config.local.yaml` | `enabled: true` | 🚀 Full GitHub push |
| Rohit's noether | `enabled: true` | 🚀 Full GitHub push |

**The goal:** New users can't accidentally push to someone else's GitHub. GitHub push is opt-in, not default.
