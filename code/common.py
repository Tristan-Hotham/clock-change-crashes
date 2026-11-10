"""Shared paths, constants and helpers for clock-change-crashes ("Do the clocks kill?").

Inputs (read where they sit, never copied into the study):
  RAW/coll_A.i32   int32 [17532 days from 1979-01-01][25 hour slots: 0 to 23, 24 = time missing][3 severity: fatal,
                   serious, slight][3 light: daylight, darkness of any kind, missing] = reported injury collisions,
                   aggregated from DfT Road Safety Data (STATS19) file
                   dft-road-casualty-statistics-collision-1979-latest-published-year.csv, retrieved 2026,
                   Open Government Licence v3.0.
  RAW/coll_K.i32   the same shape, casualties summed.
  RAW/coll_LA.u16  uint16 [days][460 slots] collisions by local_authority_ons_district; RAW/coll_meta.json the slots.
  LACODES          mySociety uk_local_authority_names_and_codes, data/uk_local_authorities.csv (CC BY 4.0), cloned
                   from GitHub into scratch: successor codes and 2020 populations.
  GEO              /home/claude/newdata/raw/geo/lad23_bsc.geojson: local authority districts, December 2023 (ONS,
                   Open Government Licence v3.0).
"""
import json, os, re, math
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
RAW = os.environ.get("CC_RAW", "/home/claude/newdata/raw_new14/collisions")
SCR = os.environ.get("CC_SCRATCH", "/home/claude/scratch/clock-change-crashes")
LACODES = os.path.join(SCR, "lacodes", "data", "uk_local_authorities.csv")
GEO = os.environ.get("CC_GEO", "/home/claude/newdata/raw/geo/lad23_bsc.geojson")
FONTS = os.environ.get("CC_FONTS", "/home/claude/ref/fonts")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "clock-change-crashes"
TITLE = "Do the clocks kill?"
SUBTITLE = "Road collisions either side of the clock changes, Great Britain 1979 to 2025"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
ND, D0 = 17532, "1979-01-01"
Y0, Y1 = 1979, 2025
# pre-specified hour groups (clock time)
EVENING = (17, 18)
MORNING = (6, 7, 8)
REFERENCE = tuple(range(10, 16))
GROUPS = {"evening": EVENING, "morning": MORNING, "reference": REFERENCE}
EXCLUDE = {(2020, "spring"), (2020, "autumn"), (2021, "spring")}
WIN = (-21, 27)


def load_arrays():
    A = np.fromfile(f"{RAW}/coll_A.i32", dtype=np.int32).reshape(ND, 25, 3, 3)
    K = np.fromfile(f"{RAW}/coll_K.i32", dtype=np.int32).reshape(ND, 25, 3, 3)
    return A, K


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    out = _fmt(v, f)
    return out[1:] if re.fullmatch(r"-0(\.0+)?%?", out) else out


def _fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE")
                  else fmt(get(R, m.group(1)), m.group(3)), t)
