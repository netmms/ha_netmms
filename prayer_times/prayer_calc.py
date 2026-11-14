"""Prayer times, calculated exactly like the NETMMS clock firmware (prayer.cpp).

The clock works with 32-bit floats and truncates to the minute when it shows a
time. To get the same minute as the clock, this port rounds to float32 at every
point where prayer.cpp stores a value into a `float`, and it truncates the same
way. Intermediate expressions that the C++ evaluates in double stay in double.

Methods (same as the clock):
  um_alqura  Umm al-Qura (KSA): Fajr 18.5 deg, Isha = Maghrib + 90 min
  egyptian   Egyptian:          Fajr 19.5 deg, Isha 17.5 deg
Asr uses shadow factor 1 (Shafi'i/Maliki/Hanbali), sunrise/maghrib at 0.833 deg.

Command line check:  python3 prayer_calc.py --lat 26.2361 --lon 50.0393 --tz Asia/Riyadh
"""
import math
import struct
from datetime import date, datetime, timedelta

PRAYER_NAMES = ("Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha")  # clock order
NAN = float("nan")


def f32(x):
    """Round to the nearest float32 (what a C++ `float` store does)."""
    try:
        return struct.unpack("f", struct.pack("f", x))[0]
    except OverflowError:
        return math.copysign(math.inf, x)


# ---- degree-based math, as the macros in prayer.cpp (sin(d) = sin(radians(d)) ...)
def _rad(d):
    return d * 0.017453292519943295769236907684886     # Arduino DEG_TO_RAD (double)


def _deg(r):
    return r * 57.295779513082320876798154814105        # Arduino RAD_TO_DEG (double)


def _sin(d):
    return math.sin(_rad(d))


def _cos(d):
    return math.cos(_rad(d))


def _tan(d):
    return math.tan(_rad(d))


def _arcsin(x):
    return _deg(math.asin(x)) if -1.0 <= x <= 1.0 else NAN


def _arccos(x):
    return _deg(math.acos(x)) if -1.0 <= x <= 1.0 else NAN


def _fix(a, mode):
    """static float fix(float a, float mode): everything in float32."""
    a = f32(a)
    mode = f32(mode)
    if math.isnan(a) or math.isinf(a):
        return NAN
    q = f32(a / mode)
    a = f32(a - f32(mode * f32(math.floor(q))))
    return f32(a + mode) if a < 0 else a


def _julian(year, month, day):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year // 100)
    B = 2 - A + math.floor(A // 4)
    jd = (math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1))
          + day + B - 1524.5)
    return f32(jd)                                       # returned as float


def _sun_position(jd):
    """Returns (decl, eqt), both float32, like getSunPosition()."""
    jc = f32((jd - 2451545.0) / 36525.0)
    gmls = _fix(280.46646 + jc * (36000.76983 + jc * 0.0003032), 360.0)
    gmas = f32(357.52911 + jc * (35999.05029 - 0.0001537 * jc))
    eeo = f32(0.016708634 - jc * (0.000042037 + 0.0000001267 * jc))
    sec = f32(_sin(gmas) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
              + _sin(f32(2 * gmas)) * (0.019993 - 0.000101 * jc)
              + _sin(f32(3 * gmas)) * 0.000289)
    sal = f32(f32(gmls + sec) - 0.00569 - 0.00478 * _sin(125.04 - 1934.136 * jc))
    moe = f32(23 + (26 + ((21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813)))) / 60) / 60)
    oc = f32(moe + 0.00256 * _cos(125.04 - 1934.136 * jc))
    decl = f32(_arcsin(_sin(oc) * _sin(sal)))
    g = f32(_tan(f32(oc / 2)) * _tan(f32(oc / 2)))
    eqt = f32(4 * (g * _sin(f32(2 * gmls))
                   - 2 * eeo * _sin(gmas)
                   + f32(f32(4 * eeo) * g) * _sin(gmas) * _cos(f32(2 * gmls))
                   - 0.5 * g * g * _sin(f32(4 * gmls))
                   - 1.25 * eeo * eeo * _sin(f32(2 * gmas))))
    return decl, eqt


def _time_angle(angle, decl, lat):
    """Hours from solar noon to the moment the sun is `angle` degrees below the horizon."""
    x = (-_sin(angle) - _sin(decl) * _sin(lat)) / (_cos(decl) * _cos(lat))
    return f32(1 / 15.0 * _arccos(x))


def calc_day(year, month, day, lat, lon, tz_hours, method="um_alqura"):
    """The six times as float hours, in the clock's order (Fajr, Sunrise, Dhuhr,
    Asr, Maghrib, Isha). A time that does not exist (high latitude) is NaN."""
    lat = f32(lat)
    lng = f32(lon)
    tz = f32(tz_hours)
    decl, eqt = _sun_position(_julian(year, month, day))
    egypt = method == "egyptian"

    noon = f32(f32(f32(12 + tz) - f32(lng / 15)) - eqt)
    fajr = f32(noon - _time_angle(f32(19.5 if egypt else 18.5), decl, lat))
    sunrise = f32(noon - _time_angle(f32(0.833), decl, lat))
    maghrib = f32(noon + _time_angle(f32(0.833), decl, lat))
    asr_angle = f32(-_deg(math.atan(1 / (1 + _tan(abs(f32(lat - decl)))))))
    asr = f32(noon + _time_angle(asr_angle, decl, lat))
    isha = f32(noon + _time_angle(f32(17.5), decl, lat)) if egypt else f32(maghrib + 1.5)
    return (fajr, sunrise, noon, asr, maghrib, isha)


# ---- how the clock turns a float time into something it shows or fires on
def to_seconds(hours, truncate_to_minute=True):
    """Seconds since local midnight, or None if the time does not exist.
    truncate_to_minute=True shows what the clock displays (float_to_hrmin truncates);
    False is what the clock's alarm uses (float_to_time)."""
    if math.isnan(hours) or math.isinf(hours):
        return None
    if not 0 <= hours < 24:
        # Only at extreme latitudes: the clock's uint8_t cast is undefined here. A negative
        # value means "before midnight" and becomes the previous evening via datetime math.
        secs = math.floor(f32(hours * 3600))
        return secs // 60 * 60 if truncate_to_minute else secs
    if truncate_to_minute:
        hr = int(hours)
        mn = int(f32(f32(hours - hr) * 60))
        return hr * 3600 + mn * 60
    return int(f32(hours * 3600))


def day_times(day, lat, lon, tzinfo, method="um_alqura", truncate_to_minute=False):
    """{name: aware datetime} for one local calendar day (None where it does not exist).
    Exact to the second, like the clock's alarm; truncate_to_minute=True gives the clock's display."""
    noon_local = datetime(day.year, day.month, day.day, 12, tzinfo=tzinfo)
    tz_hours = noon_local.utcoffset().total_seconds() / 3600.0
    hours = calc_day(day.year, day.month, day.day, lat, lon, tz_hours, method)
    midnight = datetime(day.year, day.month, day.day, tzinfo=tzinfo)
    out = {}
    for name, h in zip(PRAYER_NAMES, hours):
        secs = to_seconds(h, truncate_to_minute)
        out[name] = None if secs is None else midnight + timedelta(seconds=secs)
    return out


if __name__ == "__main__":
    import argparse
    from zoneinfo import ZoneInfo

    ap = argparse.ArgumentParser(description="Print prayer times like the clock shows them")
    ap.add_argument("--lat", type=float, default=26.2361)
    ap.add_argument("--lon", type=float, default=50.0393)
    ap.add_argument("--tz", default="Asia/Riyadh")
    ap.add_argument("--method", default="um_alqura", choices=["um_alqura", "egyptian"])
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    ap.add_argument("--days", type=int, default=1)
    a = ap.parse_args()
    tzi = ZoneInfo(a.tz)
    d0 = date.fromisoformat(a.date) if a.date else datetime.now(tzi).date()
    for i in range(a.days):
        d = d0 + timedelta(days=i)
        t = day_times(d, a.lat, a.lon, tzi, a.method)
        print(d.isoformat(), "  ".join(
            "%s %s" % (n, t[n].strftime("%H:%M:%S") if t[n] else "--:--:--") for n in PRAYER_NAMES))
