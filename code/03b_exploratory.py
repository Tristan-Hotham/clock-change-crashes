"""Step 3b (exploratory, added after the planned results): the evening estimate with comparison weeks BEFORE the change
only, for the real changes and for the placebo Sundays, to see how often ordinary weeks produce a 'before-only' evening
shift as large as the autumn one. Output data/exploratory.json."""
import warnings, importlib.util
import pandas as pd, pyfixest as pf
from common import *
warnings.filterwarnings("ignore")
spec = importlib.util.spec_from_file_location("m", os.path.join(os.path.dirname(__file__), "03_models.py"))
TREAT = tuple(range(0, 7)); BEFORE = tuple(range(-21, 0))
GROUPS_ = GROUPS


def grp(h):
    for g, hs in GROUPS_.items():
        if h in hs: return g
    return "other"


def ev(H, y="n", ctrl=BEFORE):
    H = H.copy(); H["grp"] = H.hour.map(grp)
    G = H.groupby(["event", "rel", "grp"], as_index=False)[y].sum()
    G = G[G.rel.isin(TREAT + ctrl)].copy()
    G["year"] = G.event.str[:4].astype(int); G["treat"] = G.rel.isin(TREAT).astype(int)
    G["day"] = G.event + "_" + G.rel.astype(str); G["evgrp"] = G.event + "_" + G.grp
    for g in ("evening", "morning", "other"):
        G[f"t_{g}"] = ((G.grp == g) & (G.treat == 1)).astype(int)
    m = pf.fepois(f"{y} ~ t_evening + t_morning + t_other | day + evgrp", data=G, vcov={"CRV1": "year"})
    return float(np.exp(m.coef()["t_evening"]))


E = pd.read_csv(f"{DATA}/events.csv")
H0 = pd.read_csv(f"{DATA}/event_hours.csv")
out = {}
for s in ("autumn", "spring"):
    evs = E[(E.season == s) & ~E.excluded].event
    out[f"real_{s}"] = ev(H0[H0.event.isin(evs)])
PH = pd.read_parquet(f"{SCR}/placebo_hours.parquet")
PS = pd.read_csv(f"{DATA}/placebo_sundays.csv"); wk = dict(zip(PS.date, PS.week)); PH["week"] = PH.event.map(wk)
vals = []
for w, g in PH.groupby("week"):
    if g.event.nunique() < 20: continue
    vals.append(ev(g))
vals = np.array(vals)
for s in ("autumn", "spring"):
    lr = abs(math.log(out[f"real_{s}"]))
    out[f"pl_{s}_as_large"] = int((np.abs(np.log(vals)) >= lr).sum())
out["pl_n"] = int(len(vals)); out["pl_max_abs_pc"] = float((np.exp(np.abs(np.log(vals)).max()) - 1) * 100)
out["pl_values"] = vals.round(4).tolist()
jsave(out, f"{DATA}/exploratory.json", indent=1)
print({k: v for k, v in out.items() if k != "pl_values"})
