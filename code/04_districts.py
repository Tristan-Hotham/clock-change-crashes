"""Step 4: local authority districts (2023 boundaries), 2009 to 2025 (descriptive, for the map).
Per district and season: rate ratio of the change week (days 0 to 6) to the six comparison weeks (same weekdays,
days -21 to -1 and 7 to 27), i.e. RR = 6 O / B with SE(log RR) = sqrt(1/O + 1/B) (equal-time Mantel-Haenszel);
empirical-Bayes shrinkage of log RR towards the inverse-variance national mean (DerSimonian-Laird between-district
variance). Also collisions per 100,000 people per year, 2015 to 2025 (mySociety mid-2020 populations).
Outputs: data/districts.csv, data/districts_map.geojson, data/districts_summary.json."""
import pandas as pd
from common import *

E = pd.read_csv(f"{DATA}/events.csv").set_index("event")
LA = pd.read_csv(f"{DATA}/la_event_days.csv")
LA = LA[~LA.event.map(E.excluded)]
LA["season"] = LA.event.map(E.season)
geo = jload(GEO)
names = {f["properties"]["LAD23CD"]: f["properties"]["LAD23NM"] for f in geo["features"]}
la = pd.read_csv(LACODES).set_index("gss-code")
pop = la["pop-2020"]

rows = {}
for c in sorted(set(LA.lad23)):
    rows[c] = {"lad23": c, "name": names[c], "nation": {"E": "England", "S": "Scotland", "W": "Wales"}[c[0]],
               "pop2020": int(pop[c])}
out = {}
for s in ("autumn", "spring"):
    X = LA[LA.season == s]
    O = X[X.rel.between(0, 6)].groupby("lad23").n.sum()
    B = X[(X.rel < 0) | (X.rel >= 7)].groupby("lad23").n.sum()
    df = pd.DataFrame({"O": O, "B": B}).fillna(0)
    df = df[(df.O > 0) & (df.B > 0)]
    df["lrr"] = np.log(6 * df.O / df.B); df["se"] = np.sqrt(1 / df.O + 1 / df.B)
    w = 1 / df.se ** 2
    mu = float((w * df.lrr).sum() / w.sum())
    Q = float((w * (df.lrr - mu) ** 2).sum()); k = len(df)
    tau2 = max(0.0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    Bk = tau2 / (tau2 + df.se ** 2)
    df["lrr_eb"] = mu + Bk * (df.lrr - mu)
    df["excl1"] = ((df.lrr - 1.96 * df.se) > 0) | ((df.lrr + 1.96 * df.se) < 0)
    out[s] = {"districts": k, "mu_rr": math.exp(mu), "tau2": tau2, "Q": Q, "excl1": int(df.excl1.sum()),
              "excl1_expected": 0.05 * k, "above": int(((df.lrr - 1.96 * df.se) > 0).sum()), "below": int(((df.lrr + 1.96 * df.se) < 0).sum()),
              "eb_min": float(np.exp(df.lrr_eb.min())), "eb_max": float(np.exp(df.lrr_eb.max()))}
    for c, r in df.iterrows():
        rows[c].update({f"{s}_O": int(r.O), f"{s}_B": int(r.B), f"{s}_rr": float(np.exp(r.lrr)),
                        f"{s}_lo": float(np.exp(r.lrr - 1.96 * r.se)), f"{s}_hi": float(np.exp(r.lrr + 1.96 * r.se)),
                        f"{s}_rr_eb": float(np.exp(r.lrr_eb))})
    print(s, out[s])

# collisions per 100,000 people per year, 2015 to 2025
L23 = np.load(f"{SCR}/L23.npy"); cols = jload(f"{SCR}/L23_cols.json")
days = pd.date_range(D0, periods=ND)
m = (days.year >= 2015) & (days.year <= 2025)
tot = L23[m].sum(0)
for j, c in enumerate(cols):
    if c in rows:
        rows[c]["coll_2015_2025"] = int(tot[j])
        rows[c]["per100k_year"] = float(tot[j] / 11 / rows[c]["pop2020"] * 1e5)
D = pd.DataFrame(rows.values())
D.to_csv(f"{DATA}/districts.csv", index=False)
out["per100k_median"] = float(D.per100k_year.median())
out["n_districts"] = int(len(D))
jsave(out, f"{DATA}/districts_summary.json", indent=1)

# map geojson: GB districts only, coordinates rounded to 4 decimals
def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [rnd(x) for x in c]


Dk = D.set_index("lad23")
feats = []
for f in geo["features"]:
    c = f["properties"]["LAD23CD"]
    if c not in Dk.index:
        continue
    r = Dk.loc[c]
    p = {"code": c, "name": r["name"], "pop": int(r.pop2020), "per100k": round(float(r.per100k_year), 1)}
    for s in ("autumn", "spring"):
        for k in ("rr", "lo", "hi", "rr_eb"):
            v = r.get(f"{s}_{k}")
            p[f"{s[0]}_{k}"] = None if pd.isna(v) else round(float(v), 3)
        p[f"{s[0]}_O"] = None if pd.isna(r.get(f"{s}_O")) else int(r[f"{s}_O"])
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/districts_map.geojson")
print("map features", len(feats), os.path.getsize(f"{DATA}/districts_map.geojson") // 1024, "KB")
