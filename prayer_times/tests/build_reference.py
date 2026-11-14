#!/usr/bin/env python3
"""Builds a native C++ reference from the clock's REAL prayer.cpp math and compiles it.

Usage: build_reference.py /path/to/clock_esp_400/src/prayer.cpp /path/to/output_binary

The math is cut out of prayer.cpp verbatim (the degree macros, julian, getSunPosition,
and the non-web part of get_prayer_times), so the reference cannot drift from the clock.
Only a few Arduino helpers (radians, degrees, abs) are supplied here.
"""
import subprocess
import sys

src_path, out_path = sys.argv[1], sys.argv[2]
lines = open(src_path, encoding="utf-8").read().split("\n")


def find(text, start=0):
    for i in range(start, len(lines)):
        if text in lines[i]:
            return i
    raise SystemExit("marker not found in prayer.cpp: " + text)


a = find("Degree-Based Math Functions")
b = find("void get_prayer_times(")
c = find("uint8_t method = prayer_method;", b)
d = find("// ==================== Interface", c)
head = "\n".join(lines[a:b])
body = "\n".join(lines[c:d])        # ends with the closing brace of get_prayer_times

shim = r'''
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define DEG_TO_RAD 0.017453292519943295769236907684886
#define RAD_TO_DEG 57.295779513082320876798154814105
#define radians(deg) ((deg)*DEG_TO_RAD)
#define degrees(rad) ((rad)*RAD_TO_DEG)
#define abs(x) ((x)>0?(x):-(x))
#define PR_IDX_FAJR 0
#define PR_IDX_SUNRISE 1
#define PR_IDX_NOON 2
#define PR_IDX_ASR 3
#define PR_IDX_MAGHRIB 4
#define PR_IDX_ISHA 5
#define PR_NUM_PRAYERS 6
#define METHOD_UM_QURA 0
#define METHOD_EGYPT 5
#define METHOD_WEB 99
'''

main = r'''
// output: date idx hr mn secs raw   (hr/mn like float_to_hrmin, secs like float_to_time)
int main(int argc, char **argv) {
  if (argc < 8) return 2;
  float lat = atof(argv[1]), lon = atof(argv[2]), tz = atof(argv[3]);
  prayer_method = atoi(argv[4]);
  int y = atoi(argv[5]), m = atoi(argv[6]), days = atoi(argv[7]);
  static const int mdays[] = {31,28,31,30,31,30,31,31,30,31,30,31};
  int d = 1;
  for (int n = 0; n < days; n++) {
    int mydate[3] = {y, m, d};
    float loc[3] = {lat, lon, tz};
    float t[PR_NUM_PRAYERS];
    get_prayer_times_core(t, mydate, loc);
    for (int i = 0; i < PR_NUM_PRAYERS; i++) {
      float p = t[i];
      uint8_t hr = (uint8_t)p;
      uint8_t mn = (p - hr) * 60;
      uint32_t secs = (uint32_t)(p * 3600);
      printf("%04d-%02d-%02d %d %d %d %u %.9g\n", y, m, d, i, hr, mn, secs, p);
    }
    int dim = mdays[m-1] + ((m == 2 && ((y%4==0 && y%100!=0) || y%400==0)) ? 1 : 0);
    if (++d > dim) { d = 1; if (++m > 12) { m = 1; y++; } }
  }
  return 0;
}
'''

code = (shim + "\n" + head + "\n\n"
        "void get_prayer_times_core(float *praytimes, int *mydate, float *loc) {\n"
        "  uint8_t method = prayer_method;\n"
        + body.split("uint8_t method = prayer_method;", 1)[1] + "\n" + main)
cpp = out_path + ".cpp"
open(cpp, "w").write(code)
subprocess.check_call(["g++", "-O2", "-ffp-contract=off", "-w", "-o", out_path, cpp])
print("built", out_path)
