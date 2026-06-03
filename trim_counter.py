#!/usr/bin/env python3
"""
trim_counter.py — Storage-cap manager for the Particle Plus 7000.

The device stores up to ~45,000 records in a circular buffer.  When wifi is
lost the counter keeps recording, so the buffer can fill up unattended.
This script keeps the on-device count below CAP by flushing new records to
the archive CSV and then erasing device memory.

  Run manually:    python3 trim_counter.py
  Check only:      python3 trim_counter.py --check
  Force flush+erase regardless of count: python3 trim_counter.py --force

Designed to be called independently or from particle_plus.py --trim.
Only device memory is erased; the CSV archive is never touched.
"""

import argparse
import csv
import os
import struct
import time
from datetime import datetime

from pymodbus.client import ModbusTcpClient

# ─── CONFIG ───────────────────────────────────────────────────────────────────

COUNTER_IP   = '10.66.66.68'
PORT         = 502
OUTPUT_CSV   = '/home/rraut/particle_plus/data/measurements.csv'

CAP          = 10_000   # erase threshold; device max ~45,000
                        # 10k leaves ~35k free slots → weeks of offline buffer

# ──────────────────────────────────────────────────────────────────────────────


def log(msg, level='INFO'):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}"
    print(line)


# ─── DECODERS (same register protocol as particle_plus.py) ────────────────────

def decode_u32(registers):
    return (registers[1] << 16) | registers[0]

def decode_i32(registers):
    raw = (registers[1] << 16) | registers[0]
    return raw - 0x100000000 if raw >= 0x80000000 else raw

def decode_float(registers):
    raw = struct.pack('>HH', registers[1], registers[0])
    return struct.unpack('>f', raw)[0]

def decode_string(registers):
    result = ''
    for reg in registers:
        high = (reg >> 8) & 0xFF
        low  =  reg       & 0xFF
        if high == 0:
            break
        result += chr(high)
        if low == 0:
            break
        result += chr(low)
    return result.strip()

def encode_i32(value):
    unsigned = value & 0xFFFFFFFF
    return [unsigned & 0xFFFF, (unsigned >> 16) & 0xFFFF]


# ─── MODBUS HELPERS ───────────────────────────────────────────────────────────

def connect():
    client = ModbusTcpClient(COUNTER_IP, port=PORT, timeout=5)
    if not client.connect():
        log(f"Connection to {COUNTER_IP}:{PORT} failed", 'ERROR')
        return None
    log(f"Connected to {COUNTER_IP}:{PORT}")
    return client


def get_record_count(client):
    r = client.read_holding_registers(address=8000, count=2)
    if r.isError():
        return 0
    return decode_u32(r.registers)


def latch_record(client, record_number):
    client.write_registers(address=8002, values=encode_i32(record_number))
    time.sleep(0.3)


def read_latched_record(client):
    """Read all fields from the currently-latched record. Returns dict or None."""
    data = {}

    r = client.read_holding_registers(address=9000, count=2)
    if r.isError():
        return None
    rec_num = decode_i32(r.registers)
    if rec_num == -1:
        return None
    data['record_number'] = rec_num

    r = client.read_holding_registers(address=9002, count=11)
    data['date'] = decode_string(r.registers) if not r.isError() else ''

    r = client.read_holding_registers(address=9013, count=9)
    data['time'] = decode_string(r.registers) if not r.isError() else ''

    r = client.read_holding_registers(address=9022, count=21)
    data['location'] = decode_string(r.registers) if not r.isError() else ''

    r = client.read_holding_registers(address=9074, count=2)
    data['sample_duration_s'] = round(decode_float(r.registers), 2) if not r.isError() else None

    r = client.read_holding_registers(address=9076, count=2)
    data['flow_CFM'] = round(decode_float(r.registers), 4) if not r.isError() else None

    r = client.read_holding_registers(address=9078, count=1)
    if not r.isError():
        bits = r.registers[0]
        data['status_laser_ok'] = bool(bits & 0x0001)
        data['status_flow_ok']  = bool(bits & 0x0002)
        data['status_temp_ok']  = bool(bits & 0x0004)
        data['status_rh_ok']    = bool(bits & 0x0008)

    r = client.read_holding_registers(address=9079, count=1)
    if not r.isError():
        raw = r.registers[0]
        data['temp_C'] = None if raw >= 998 else round(raw * 0.1, 1)
    else:
        data['temp_C'] = None

    r = client.read_holding_registers(address=9080, count=1)
    if not r.isError():
        raw = r.registers[0]
        data['RH_pct'] = None if raw <= 1 else raw
    else:
        data['RH_pct'] = None

    for i in range(6):
        off = i * 2
        ch  = f'ch{i+1}'
        for base, key in [
            (10100, f'{ch}_size_um'),
            (10300, f'{ch}_diff_counts'),
            (10500, f'{ch}_diff_ft3'),
            (10700, f'{ch}_diff_m3'),
            (10900, f'{ch}_diff_mass_ugm3'),
            (11500, f'{ch}_sum_m3'),
        ]:
            r = client.read_holding_registers(address=base + off, count=2)
            if not r.isError():
                val = decode_float(r.registers)
                data[key] = round(val, 4 if 'mass' in key else (3 if 'size' in key else 2))
            else:
                data[key] = None

    data['sync_time'] = datetime.now().isoformat()
    return data


def get_last_saved_record(csv_path):
    """Return the highest record_number already written to the CSV."""
    last = 0
    if not os.path.exists(csv_path):
        return last
    with open(csv_path, 'r') as f:
        for row in csv.DictReader(f):
            try:
                n = int(float(row.get('record_number', 0) or 0))
                if n > last:
                    last = n
            except (ValueError, TypeError):
                pass
    return last


def save_to_csv(records, csv_path):
    """Append records to CSV, writing header if file is new. Returns count saved."""
    if not records:
        return 0
    file_exists = os.path.exists(csv_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
    return len(records)


def erase_counter(client):
    """Write the erase magic value. Returns True if counter reaches 0 records."""
    log("Erasing counter memory (reg 8004 ← 0x9559)...")
    client.write_registers(address=8004, values=[0x9559])
    time.sleep(3)
    remaining = get_record_count(client)
    log(f"Records remaining after erase: {remaining}")
    return remaining == 0


# ─── CORE LOGIC ───────────────────────────────────────────────────────────────

def flush_new_records(client):
    """
    Sync only records not yet in the CSV archive.
    Returns (n_saved, had_failures) tuple.
    """
    total      = get_record_count(client)
    last_saved = get_last_saved_record(OUTPUT_CSV)
    log(f"Counter: {total} records total, CSV has up to record {last_saved}")

    if last_saved >= total:
        log("CSV is already up to date — nothing to flush")
        return 0, False

    start  = last_saved + 1
    n_new  = total - last_saved
    log(f"Flushing {n_new} new records ({start}–{total}) → {OUTPUT_CSV}")

    records  = []
    failures = []

    for i in range(start, total + 1):
        try:
            latch_record(client, i)
            data = read_latched_record(client)
            if data:
                records.append(data)
                log(f"  [{i:4d}/{total}] date={data.get('date','')}  "
                    f"time={data.get('time','')}  "
                    f"temp={data.get('temp_C','?')}C  "
                    f"ch1={data.get('ch1_diff_m3','?')}/m³")
            else:
                failures.append(i)
                log(f"  [{i:4d}/{total}] empty/invalid — skipped", 'WARN')
        except Exception as exc:
            failures.append(i)
            log(f"  [{i:4d}/{total}] error: {exc}", 'ERROR')

    n_saved = save_to_csv(records, OUTPUT_CSV)
    log(f"Flush complete: {n_saved} records saved, {len(failures)} failures")

    if failures:
        log(f"Failed record numbers: {failures}", 'WARN')

    return n_saved, bool(failures)


def trim_if_full(cap=CAP, force=False):
    """
    Main entry point.
    - Connects to the counter.
    - If record count > cap (or force=True): flush new records then erase.
    - Never erases if flush had any failures (safety first).
    Returns True on success or if no action was needed.
    """
    client = connect()
    if client is None:
        return False

    try:
        count = get_record_count(client)
        log(f"Counter has {count} records  (cap={cap})")

        if not force and count <= cap:
            log("Below cap — no trim needed")
            return True

        if force:
            log("--force flag: trimming regardless of count")
        else:
            log(f"{count} > {cap} — flushing then erasing")

        n_saved, had_failures = flush_new_records(client)

        if had_failures:
            log("Skipping erase: flush had failures — re-run to retry", 'WARN')
            return False

        ok = erase_counter(client)
        if ok:
            log(f"Trim complete: flushed {n_saved} new records, counter reset to 0")
        else:
            log("Erase command sent but counter may not be fully cleared", 'WARN')
        return ok

    finally:
        client.close()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Trim Particle Plus 7000 storage: flush new records then erase if above cap')
    parser.add_argument('--check', action='store_true',
                        help='Report record count only — no flush or erase')
    parser.add_argument('--force', action='store_true',
                        help=f'Flush + erase regardless of count (ignores cap={CAP})')
    parser.add_argument('--cap', type=int, default=CAP,
                        help=f'Override cap threshold (default: {CAP})')
    args = parser.parse_args()

    print(f"trim_counter.py  |  target={COUNTER_IP}:{PORT}  |  cap={args.cap}")
    print(f"  archive → {OUTPUT_CSV}")
    print()

    if args.check:
        client = connect()
        if client:
            count = get_record_count(client)
            client.close()
            log(f"Record count: {count}  (cap={args.cap}, {'OVER' if count > args.cap else 'OK'})")
        return

    trim_if_full(cap=args.cap, force=args.force)


if __name__ == '__main__':
    main()
