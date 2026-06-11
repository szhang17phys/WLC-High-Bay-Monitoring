#!/usr/bin/env python3
"""
data_manager.py — Dataset lifecycle management for WLC-High-Bay particle monitoring.

Three datasets:
  measurement_archive.csv — ALL synced records ever, local only (gitignored).
                            Never pruned; the complete permanent record.
  live.csv                — Last 30 days of synced particle measurements.
                            Rebuilt from archive after every sync. Pushed to GitHub
                            for display and download.
  env_live.csv            — 10-second live env snapshots (temp/RH).
                            Trimmed to 30 days. Pushed to GitHub.

Called from particle_plus.py after each sync and at startup.
Bug fixes for counter-erase sync tracking live in particle_plus.py;
this module handles only dataset management logic.
"""

import csv
import json
import os
import shutil
from datetime import datetime, timedelta


LIVE_DAYS = 30


# ─── SYNC STATE ───────────────────────────────────────────────────────────────
# The counter resets record numbers to 1 after an erase.  We track the last
# successfully synced record number in a small JSON file so mode_sync can
# detect the reset and restart from record 1 instead of skipping new data.

def get_last_synced(state_path):
    """Return last synced record number from state file, or 0 if absent/corrupt."""
    if not os.path.exists(state_path):
        return 0
    try:
        with open(state_path) as f:
            return int(json.load(f).get('last_synced', 0))
    except (json.JSONDecodeError, ValueError, KeyError, OSError):
        return 0


def set_last_synced(state_path, n):
    """Persist last synced record number to state file."""
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path) as f:
                state = json.load(f)
        except Exception:
            pass
    state['last_synced'] = n
    state['updated'] = datetime.now().isoformat()
    with open(state_path, 'w') as f:
        json.dump(state, f)


def reset_sync_state(state_path):
    """Reset last_synced to 0 after a counter erase so the next sync starts from record 1."""
    with open(state_path, 'w') as f:
        json.dump({'last_synced': 0, 'erased': datetime.now().isoformat()}, f)


# ─── TIMESTAMP PARSING ────────────────────────────────────────────────────────

def _parse_row_ts(row):
    """Return datetime for a data row using counter date/time, then sync/snapshot fallback."""
    d = row.get('date', '').strip()
    t = row.get('time', '').strip()
    if d and t:
        try:
            return datetime.strptime(f"{d} {t}", '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    for key in ('sync_time', 'snapshot_time'):
        val = row.get(key, '').strip()
        if val:
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                pass
    return None


# ─── LIVE CSV (30-day particle window) ────────────────────────────────────────

def rebuild_live_csv(archive_path, live_path, days=LIVE_DAYS):
    """
    Rewrite live.csv as the last `days` days of records from measurement_archive.csv.
    Called after every sync so live.csv is always a fresh 30-day rolling window.
    Returns count of rows written.
    """
    cutoff = datetime.now() - timedelta(days=days)
    rows = []
    fieldnames = None
    if os.path.exists(archive_path):
        with open(archive_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                dt = _parse_row_ts(row)
                if dt is None or dt >= cutoff:
                    rows.append(row)
    if not rows or fieldnames is None:
        return 0
    with open(live_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ─── ENV SNAPSHOT TRIMMING ────────────────────────────────────────────────────

def trim_env_csv(env_path, days=LIVE_DAYS):
    """
    Remove rows older than `days` days from the env snapshot CSV (in-place rewrite).
    Called periodically from mode_live to prevent unbounded growth.
    Returns count of rows kept.
    """
    if not os.path.exists(env_path):
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    rows = []
    fieldnames = None
    with open(env_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            # DictReader puts extra (beyond-header) columns under key None — strip them
            row.pop(None, None)
            dt = _parse_row_ts(row)
            if dt is None or dt >= cutoff:
                rows.append(row)
    if fieldnames is None:
        return 0
    # Fieldnames list itself may contain None if header had trailing comma — remove it
    clean_fieldnames = [f for f in fieldnames if f is not None]
    with open(env_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=clean_fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ─── MIGRATION ────────────────────────────────────────────────────────────────

def migrate_old_files(data_dir):
    """
    One-time migration from legacy file names to the new naming scheme.
    Safe to call at every startup — only copies if the destination doesn't exist.

      measurements.csv  →  measurement_archive.csv  (all particle data, local)
      live.csv          →  env_live.csv              (10s env snapshots)
    """
    _safe_copy(
        os.path.join(data_dir, 'measurements.csv'),
        os.path.join(data_dir, 'measurement_archive.csv'),
    )
    _safe_copy(
        os.path.join(data_dir, 'live.csv'),
        os.path.join(data_dir, 'env_live.csv'),
    )


def migrate_archive_dir(data_dir, archive_dir):
    """
    One-time copy of the permanent archive (+ its sync-state file) from the
    repo-local data/ dir into the shared project space. Safe to call at every
    startup — only copies files the destination doesn't have yet. The
    originals are left behind in data/ as a backup (gitignored, never read
    again once the project-space copies exist).
    """
    if os.path.abspath(archive_dir) == os.path.abspath(data_dir):
        return
    for name in ('measurement_archive.csv', 'counter_state.json'):
        _safe_copy(os.path.join(data_dir, name),
                   os.path.join(archive_dir, name))


def _safe_copy(src, dst):
    """Copy src → dst only if src exists and dst does not."""
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)
