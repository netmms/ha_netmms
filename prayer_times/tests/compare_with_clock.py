#!/usr/bin/env python3
"""Compares prayer_calc.py with a native build of the clock's own prayer.cpp math.

Usage: compare_with_clock.py /path/to/clock_esp_400/src/prayer.cpp
Checks every day of 2026-2027 for several places and both methods. A mismatch in the
raw float32 value, or in the minute the clock would show, is reported and fails the run.
"""
import math
import os
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import prayer_calc as pc  # noqa: E402

here = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp()
ref = os.path.join(tmp, "ref_prayer")
subprocess.check_call([sys.executable, os.path.join(here, "build_reference.py"), sys.argv[1], ref])

# name, lat, lon, tz (fixed hours, like the clock), method
PLACES = [
    ("Dhahran/KFUPM", 26.2361, 50.0393, 3.0, "um_alqura"),
    ("Dhahran Egyptian", 26.2361, 50.0393, 3.0, "egyptian"),
    ("Jeddah", 21.5433, 39.1728, 3.0, "um_alqura"),
    ("Makkah", 21.4225, 39.8262, 3.0, "um_alqura"),
    ("Cairo", 30.0444, 31.2357, 2.0, "egyptian"),
    ("Istanbul", 41.0082, 28.9784, 3.0, "um_alqura"),
    ("Kuala Lumpur", 3.139, 101.6869, 8.0, "egyptian"),
    ("Tromso (no twilight in summer)", 69.6496, 18.9560, 1.0, "um_alqura"),
]
MCODE = {"um_alqura": 0, "egyptian": 5}
bad = total = 0
for name, lat, lon, tz, method in PLACES:
    for year in (2026, 2027):
        # the reference walks forward from the 1st of the given month: run it month by month
        rows = []
        for month in range(1, 13):
            dim = [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
            rows += subprocess.check_output(
                [ref, repr(lat), repr(lon), repr(tz), str(MCODE[method]), str(year), str(month), str(dim)]
            ).decode().strip().split("\n")
        cache = {}
        for line in rows:
            d, idx, hr, mn, secs, raw = line.split()
            idx = int(idx)
            y, m, dd = (int(x) for x in d.split("-"))
            if (y, m, dd) not in cache:
                cache[(y, m, dd)] = pc.calc_day(y, m, dd, lat, lon, tz, method)
            mine = cache[(y, m, dd)][idx]
            theirs = struct.unpack("f", struct.pack("f", float(raw)))[0]
            total += 1
            same_nan = math.isnan(mine) and math.isnan(theirs)
            if not same_nan and mine != theirs:
                bad += 1
                if bad <= 15:
                    print("RAW MISMATCH", name, d, pc.PRAYER_NAMES[idx], mine, theirs)
                continue
            if not same_nan and not 0 <= mine < 24:
                continue    # extreme latitude: the clock's uint8_t cast is undefined there
            if not same_nan:
                s = pc.to_seconds(mine, True)
                if s != int(hr) * 3600 + int(mn) * 60:
                    bad += 1
                    print("MINUTE MISMATCH", name, d, pc.PRAYER_NAMES[idx], s, hr, mn)
                if pc.to_seconds(mine, False) != int(secs):
                    bad += 1
                    print("SECONDS MISMATCH", name, d, pc.PRAYER_NAMES[idx], secs)
    print("checked %-32s %s" % (name, method))
print("compared %d values, %d mismatches" % (total, bad))
sys.exit(1 if bad else 0)
