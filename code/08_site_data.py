"""Step 8: data/site.json for the page: the hour-by-day grid (share of each day's collisions in each clock hour, relative to
the same hour's share in the comparison weeks, pooled over the main-sample changes), the darkness share by hour, and the
hour-by-hour rate ratios."""
import pandas as pd
from common import *

E = pd.read_csv(f"{DATA}/events.csv"); EV = E.set_index("event")
H = pd.read_csv(f"{DATA}/event_hours.csv"); H = H[H.event.map(~EV.excluded)]
H["season"] = H.event.map(EV.season)
CTRL = list(range(-21, 0)) + list(range(7, 28))
out = {"grid": {}, "dark": jload(f"{DATA}/dark_by_hour.json"), "prof": {}}
for s in ("spring", "autumn"):
    x = H[H.season == s]
    t = x.pivot_table(index="rel", columns="hour", values="n", aggfunc="sum")
    share = t.div(t.sum(axis=1), axis=0)
    rel = share.copy()
    for r in share.index:  # same weekday's comparison days (excluding the day itself)
        cm = [c for c in CTRL if (c - r) % 7 == 0 and c != r]
        rel.loc[r] = share.loc[r] / share.loc[cm].mean(axis=0)
    out["grid"][s] = {"rel": [int(r) for r in rel.index], "v": [[round(float(v), 3) for v in row] for row in rel.values]}
P = pd.read_csv(f"{DATA}/hour_profile.csv")
for s in ("spring", "autumn"):
    p = P[(P.season == s) & (P.outcome == "n")].sort_values("hour")
    out["prof"][s] = [[int(r.hour), round(r.rr, 3), None if pd.isna(r.lo) else round(r.lo, 3), None if pd.isna(r.hi) else round(r.hi, 3)] for r in p.itertuples()]
jsave(out, f"{DATA}/site.json")
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
