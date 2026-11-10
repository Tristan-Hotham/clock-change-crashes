"""Step 2: event-window panels from the STATS19 aggregates.
data/event_days.csv     event x day (-21 to 27): all-injury and fatal collisions and casualties, dark counts, holiday flag.
data/event_hours.csv    event x day x clock hour: all-injury and fatal collisions, collisions in darkness.
data/la_event_days.csv  event x day x 2023 district (2009 to 2025, non-zero rows only).
scratch placebo_days.parquet / placebo_hours.parquet  the same for every placebo Sunday (not shipped: rebuilt from code)."""
import pandas as pd
from common import *

A, K = load_arrays()
days = pd.date_range(D0, periods=ND)
E = pd.read_csv(f"{DATA}/events.csv")
P = pd.read_csv(f"{DATA}/placebo_sundays.csv")
Hd = set(pd.read_csv(f"{DATA}/holidays.csv").date)
idx0 = {d.date().isoformat(): i for i, d in enumerate(days)}
REL = np.arange(WIN[0], WIN[1] + 1)

# per day x hour: all, fatal, dark (all severities), dark fatal
allh = A[:, :24].sum((2, 3))
fath = A[:, :24, 0].sum(2)
darkh = A[:, :24, :, 1].sum(2)
lighth = A[:, :24, :, 0].sum(2)
casd = K.sum((1, 2, 3)); casfd = K[:, :, 0].sum((1, 2))
cash = K[:, :24].sum((2, 3)); casfh = K[:, :24, 0].sum(2)


def window(dates, keys):
    rows_d, rows_h = [], []
    for k, d in zip(keys, dates):
        i0 = idx0[d]
        for r in REL:
            i = i0 + r
            day = days[i].date().isoformat()
            rows_d.append((k, r, day, days[i].weekday(), int(day in Hd), int(allh[i].sum()), int(fath[i].sum()),
                           int(casd[i]), int(casfd[i]), int(darkh[i].sum())))
            for h in range(24):
                rows_h.append((k, r, h, int(allh[i, h]), int(fath[i, h]), int(darkh[i, h]), int(lighth[i, h]), int(cash[i, h]), int(casfh[i, h])))
    D = pd.DataFrame(rows_d, columns=["event", "rel", "date", "dow", "holiday", "n", "fatal", "cas", "cas_fatal", "dark"])
    Hh = pd.DataFrame(rows_h, columns=["event", "rel", "hour", "n", "fatal", "dark", "light", "cas", "cas_fatal"])
    return D, Hh


D, Hh = window(E.date, E.event)
D.to_csv(f"{DATA}/event_days.csv", index=False)
Hh.to_csv(f"{DATA}/event_hours.csv", index=False)
print("event days", len(D), "event hours", len(Hh))

Pk = P.date.values
PD, PH = window(P.date, Pk)
PD.to_parquet(f"{SCR}/placebo_days.parquet"); PH.to_parquet(f"{SCR}/placebo_hours.parquet")
print("placebo days", len(PD), "placebo hours", len(PH))

# local authorities: map every code (2009 on) to a 2023 district
L = np.fromfile(f"{RAW}/coll_LA.u16", dtype=np.uint16).reshape(ND, 460)
meta = jload(f"{RAW}/coll_meta.json")["laIdx"]
geo = jload(GEO)
lad23 = {f["properties"]["LAD23CD"]: f["properties"]["LAD23NM"] for f in geo["features"]}
la = pd.read_csv(LACODES)
by_gss = la.set_index("gss-code")
code2gss = dict(zip(la["local-authority-code"], la["gss-code"]))
extra = {"EHEATHROW": "E09000017", "E08000038": "E08000016", "E08000039": "E08000019"}


def succ(g):
    seen = 0
    while g not in lad23:
        if g in extra:
            g = extra[g]; continue
        rep = by_gss.loc[g, "replaced-by"] if g in by_gss.index else None
        if not isinstance(rep, str):
            return None
        g = code2gss[rep]; seen += 1
        assert seen < 4
    return g


i09 = idx0["2009-01-01"]
mapping, unm = {}, {}
for code, slot in meta.items():
    tot = int(L[i09:, slot].sum())
    if tot == 0:
        continue
    s = succ(code)
    if s is None:
        unm[code] = tot
    else:
        mapping[code] = s
assert not unm, unm
jsave({"mapping": mapping, "note": "ONS district code in STATS19 (2009 to 2025) -> 2023 district; via mySociety replaced-by, "
       "plus EHEATHROW -> Hillingdon, E08000038 -> Barnsley E08000016, E08000039 -> Sheffield E08000019"}, f"{DATA}/la_code_map.json", indent=1)
cols = sorted(set(mapping.values()))
ci = {c: j for j, c in enumerate(cols)}
M = np.zeros((460, len(cols)), dtype=np.int32)
for code, s in mapping.items():
    M[meta[code], ci[s]] = 1
L23 = L.astype(np.int32) @ M            # days x districts
np.save(f"{SCR}/L23.npy", L23)
jsave(cols, f"{SCR}/L23_cols.json")
rows = []
for k, d, y in zip(E.event, E.date, E.year):
    if y < 2009:
        continue
    i0 = idx0[d]
    for r in REL:
        v = L23[i0 + r]
        for j in np.nonzero(v)[0]:
            rows.append((k, r, days[i0 + r].weekday(), int(days[i0 + r].date().isoformat() in Hd), cols[j], int(v[j])))
LA = pd.DataFrame(rows, columns=["event", "rel", "dow", "holiday", "lad23", "n"])
LA.to_csv(f"{DATA}/la_event_days.csv", index=False)
# check: district totals equal national totals from 2009
assert int(L23[i09:].sum()) == int(A[i09:].sum())
print("districts", len(cols), "of", len(lad23), "la rows", len(LA))
