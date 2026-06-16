"""Pure-standard-library core for the standalone spell app.

No third-party dependencies. This re-implements exactly what the tracker does:
  - generate the rotationally-unique binary necklaces (Ernesti method)
  - map a spell attribute value to its necklace via its line index in the
    attribute_ordering txt files
  - expose vertex geometry + chords so a plain canvas can draw the glyph

Glyph engine logic credit: github.com/GorillaOfDestiny/SpellWriting (MIT).
"""
import math
import os
import sys
from functools import lru_cache

N_POL = 13                      # 2 * 6 attributes + 1
ATTR_ORDER = ["level", "school", "damagetype", "aoe", "range", "duration"]
_FILES = {
    "level": "levels.txt", "school": "school.txt", "damagetype": "damage_types.txt",
    "aoe": "area_types.txt", "range": "range.txt", "duration": "duration.txt",
}


def resource_path(*parts):
    """Resolve a bundled data path, whether running from source or a PyInstaller
    one-file exe (which unpacks to sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


@lru_cache(maxsize=None)
def necklaces(n=N_POL):
    """All rotationally-unique binary necklaces of length n (Ernesti method)."""
    x = 1
    out = ["".join("0" * n)]
    while x < 2 ** n:
        s = bin(x)[2:].zfill(n)
        cyc, smaller = [], False
        for i in range(len(s) - 1):
            rot = s[i:] + s[:i]
            cyc.append(rot)
            if rot < s:
                smaller = True
                break
        if not smaller and min(cyc + [s]) == s:
            out.append(s)
        x += 2
    return [[int(b) for b in word] for word in out]


@lru_cache(maxsize=None)
def _options(attr):
    """Lower-cased, order-preserving list of valid values for an attribute."""
    path = resource_path("data", "attribute_ordering", _FILES[attr])
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip().lower() for ln in f if ln.strip()]


def options_display(attr):
    """Original-case values for dropdowns (re-read so display keeps casing)."""
    path = resource_path("data", "attribute_ordering", _FILES[attr])
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def necklace_for(attr, value):
    """13-bit necklace (list[int]) for a given attribute value, or all-zeros if
    the value isn't in the vocabulary."""
    opts = _options(attr)
    v = str(value).strip().lower()
    if v not in opts:
        return [0] * N_POL
    return necklaces()[opts.index(v)]


def decode(attrs):
    """Per-attribute necklace breakdown for the six glyph attributes."""
    rows = []
    for i, attr in enumerate(ATTR_ORDER):
        bits = necklace_for(attr, attrs.get(attr, ""))
        rows.append({
            "attribute": attr,
            "value": str(attrs.get(attr, "")),
            "skip": i + 1,
            "bits": "".join(str(b) for b in bits),
        })
    return rows


def vertices(cx, cy, r):
    """Pixel coords of the 13 base points, vertex 0 at 12 o'clock.

    Matches the tracker's polygon base (start_angle = -2*pi/n): vertex j sits at
    angle j*2*pi/n with (x, y) = (sin, cos). Canvas y grows downward, so cos is
    subtracted to put vertex 0 at the top."""
    pts = []
    for j in range(N_POL):
        ang = j * 2 * math.pi / N_POL
        pts.append((cx + r * math.sin(ang), cy - r * math.cos(ang)))
    return pts


def chords(attrs):
    """List of (a, b) vertex-index pairs to draw, across all six attributes.
    Row i uses skip k = i+1: each set bit j connects vertex j to (j+k) mod n."""
    out = []
    for i, attr in enumerate(ATTR_ORDER):
        k = i + 1
        bits = necklace_for(attr, attrs.get(attr, ""))
        for j, b in enumerate(bits):
            if b == 1:
                out.append((j, (j + k) % N_POL))
    return out


# --- SRD spell record -> the six glyph attributes (mirrors backend/spells/srd.py)
import re

_DAMAGE_TYPES = [d for d in options_display("damagetype") if d.lower() != "none"]
_RANGE_VALID = {r.lower(): r for r in options_display("range")}
_DUR_VALID = {d.lower(): d for d in options_display("duration")}
_AOE_VALID = {a.lower(): a for a in options_display("aoe")}
_SHAPES = ["cone", "cube", "cylinder", "line", "sphere"]


def _m_level(v):
    return str(v) if str(v) in options_display("level") else "Blank"


def _m_school(v):
    return v if v in options_display("school") else "Blank"


def _m_range(rng):
    low = str(rng).strip().lower()
    if low in _RANGE_VALID:
        return _RANGE_VALID[low]
    if low.startswith("self"):
        return "Self"
    if low.startswith("touch"):
        return "Touch"
    if "sight" in low:
        return "Sight"
    if "unlimited" in low:
        return "Unlimited"
    m = re.search(r"(\d+)\s*feet", low)
    if m and f"{m.group(1)} feet" in _RANGE_VALID:
        return _RANGE_VALID[f"{m.group(1)} feet"]
    m = re.search(r"(\d+)\s*mile", low)
    if m:
        for cand in (f"{m.group(1)} mile", f"{m.group(1)} miles"):
            if cand in _RANGE_VALID:
                return _RANGE_VALID[cand]
    return "Special"


def _m_duration(dur):
    low = (str(dur).strip().lower()
           .replace("concentration, ", "")
           .replace("concentration up to", "up to").strip())
    return _DUR_VALID.get(low, "Special")


def _m_damage(desc):
    text = " ".join(desc or []).lower()
    for dt in _DAMAGE_TYPES:
        if f"{dt.lower()} damage" in text:
            return dt
    return "None"


def _m_aoe(spell):
    blob = (str(spell.get("range", "")) + " " + " ".join(spell.get("desc", []))).lower()
    for shape in _SHAPES:
        for m in re.finditer(r"(\d+)[- ]foot(?:[- ]radius)?[- ]?" + shape, blob):
            cand = f"{shape} ({m.group(1)})"
            if cand in _AOE_VALID:
                return _AOE_VALID[cand]
        for m in re.finditer(shape + r"[^.]{0,15}?(\d+)[- ]?foot", blob):
            cand = f"{shape} ({m.group(1)})"
            if cand in _AOE_VALID:
                return _AOE_VALID[cand]
    return "None"


def srd_to_attrs(spell):
    return {
        "level": _m_level(spell.get("level")),
        "school": _m_school(spell.get("school")),
        "damagetype": _m_damage(spell.get("desc", [])),
        "aoe": _m_aoe(spell),
        "range": _m_range(spell.get("range")),
        "duration": _m_duration(spell.get("duration")),
        "concentration": bool(spell.get("concentration")),
        "ritual": bool(spell.get("ritual")),
    }
