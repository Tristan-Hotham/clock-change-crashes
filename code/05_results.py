"""Step 5: data/results.json, every number quoted anywhere (page, paper, blog, collage, post, README).
Adds convenience fields under x (percent changes, rounded) and data (sample facts). Asserts key facts."""
import pandas as pd
from common import *

M = jload(f"{DATA}/models.json")
A, K = load_arrays()
E = pd.read_csv(f"{DATA}/events.csv")
DS = jload(f"{DATA}/districts_summary.json")
days = pd.date_range(D0, periods=ND)
yr = days.year
R = {k: v for k, v in M.items()}
data = {"collisions": int(A.sum()), "fatal": int(A[:, :, 0].sum()), "casualties": int(K.sum()),
        "year0": int(yr[A.sum((1, 2, 3)) > 0].min()), "year1": int(yr[A.sum((1, 2, 3)) > 0].max()),
        "events": int(len(E)), "events_main": int((~E.excluded).sum()), "spring_main": int(((~E.excluded) & (E.season == "spring")).sum()),
        "autumn_main": int(((~E.excluded) & (E.season == "autumn")).sum()),
        "easter_in_change_week": int(E.easter_in_treat_week.sum()),
        "placebo_sundays": int(len(pd.read_csv(f"{DATA}/placebo_sundays.csv"))), "placebo_weeks": int(M["placebo"]["h1_spring_n"]["n"]),
        "light_missing_share_max": float((A[:, :, :, :, ][:, :, :, 2].sum((1, 2)) / np.maximum(1, A.sum((1, 2, 3))))[A.sum((1, 2, 3)) > 0].max()),
        "coll_1979": int(A[yr == 1979].sum()), "coll_2025": int(A[yr == 2025].sum()),
        "fatal_1979": int(A[yr == 1979][:, :, 0].sum()), "fatal_2025": int(A[yr == 2025][:, :, 0].sum())}
win = E[~E.excluded]
D = pd.read_csv(f"{DATA}/event_days.csv")
D = D[D.event.isin(win.event)]
data["window_collisions"] = int(D.n.sum()); data["window_fatal"] = int(D.fatal.sum())
data["change_week_collisions"] = int(D[D.rel.between(0, 6)].n.sum()); data["change_week_fatal"] = int(D[D.rel.between(0, 6)].fatal.sum())
R["data"] = data
R["districts"] = DS
XP = jload(f"{DATA}/exploratory.json"); XP.pop("pl_values", None); R["exploratory"] = XP


def pc(v):
    return (v - 1) * 100


x = {}
for k, v in M["H1"].items():
    x[f"h1_{k}_pc"], x[f"h1_{k}_lo_pc"], x[f"h1_{k}_hi_pc"] = pc(v["rr"]), pc(v["lo"]), pc(v["hi"])
for k, v in M["H1b"].items():
    x[f"h1b_{k}_pc"], x[f"h1b_{k}_lo_pc"], x[f"h1b_{k}_hi_pc"] = pc(v["rr"]), pc(v["lo"]), pc(v["hi"])
for k, v in M["H2"].items():
    x[f"h2_{k}_pc"], x[f"h2_{k}_lo_pc"], x[f"h2_{k}_hi_pc"] = pc(v["rr"]), pc(v["lo"]), pc(v["hi"])
for k, v in M["H3"].items():
    x[f"h3_{k}_pc"], x[f"h3_{k}_lo_pc"], x[f"h3_{k}_hi_pc"] = pc(v["rr"]), pc(v["lo"]), pc(v["hi"])
for k, v in M["dark_share"].items():
    x[f"dark_{k}_ctrl_pc"], x[f"dark_{k}_treat_pc"] = v["ctrl"] * 100, v["treat"] * 100
for k, v in M["placebo"].items():
    x[f"pl_{k}_share_pc"] = v["share_as_large"] * 100
    x[f"pl_{k}_count"] = round(v["share_as_large"] * v["n"])
    x[f"pl_{k}_one_in"] = 1 / v["share_as_large"] if v["share_as_large"] > 0 else None
for k, v in M["H4"].items():
    for kk, vv in v.items():
        x[f"h4_{k}_{kk}"] = vv
for k, v in M["loo"].items():
    for g, (lo, hi) in v.items():
        x[f"loo_{k}_{g}_lo_pc"], x[f"loo_{k}_{g}_hi_pc"] = pc(lo), pc(hi)
rb = M["robust"]
def rbk(lab, s, y, g):
    return rb[f"{lab}|{s}|{y}"][g]
x["wd_autumn_fatal_pc"], x["wd_autumn_fatal_lo_pc"], x["wd_autumn_fatal_hi_pc"] = [pc(rbk("Working days 1 to 5 only", "autumn", "fatal", "h1")[k]) for k in ("rr", "lo", "hi")]
x["we_autumn_evening_pc"], x["we_autumn_evening_lo_pc"], x["we_autumn_evening_hi_pc"] = [pc(rbk("Exploratory: weekends only (no commute or school run)", "autumn", "n", "evening")[k]) for k in ("rr", "lo", "hi")]
x["we_spring_evening_pc"], x["we_spring_evening_lo_pc"], x["we_spring_evening_hi_pc"] = [pc(rbk("Exploratory: weekends only (no commute or school run)", "spring", "n", "evening")[k]) for k in ("rr", "lo", "hi")]
x["scot_autumn_pc"], x["scot_autumn_lo_pc"], x["scot_autumn_hi_pc"] = [pc(rbk("Nation: Scotland", "autumn", "n", "h1")[k]) for k in ("rr", "lo", "hi")]
x["noeaster_spring_pc"], x["noeaster_spring_lo_pc"], x["noeaster_spring_hi_pc"] = [pc(rbk("Spring events without Easter in the change week", "spring", "n", "h1")[k]) for k in ("rr", "lo", "hi")]
x["after_autumn_pc"], x["after_autumn_lo_pc"], x["after_autumn_hi_pc"] = [pc(rbk("Comparison weeks after only", "autumn", "n", "h1")[k]) for k in ("rr", "lo", "hi")]
# whole-week all-injury robustness estimates whose interval excludes 1 (planned checks, nation rows included)
x["rb_h1_n_excl1"] = sum(1 for k, v in rb.items() if "h1" in v and k.endswith("|n") and not k.startswith("Leave") and not k.startswith("Nation: Great")
                         and (v["h1"]["lo"] > 1 or v["h1"]["hi"] < 1))
assert x["rb_h1_n_excl1"] == 3, x["rb_h1_n_excl1"]
# all whole-day robustness estimates for all-injury: range
h1s = [v["h1"]["rr"] for k, v in rb.items() if "h1" in v and k.endswith("|n") and not k.startswith("Nation") and not k.startswith("Leave")]
x["rb_h1_n_min_pc"], x["rb_h1_n_max_pc"] = pc(min(h1s)), pc(max(h1s))
x["rb_n"] = len(set(k.split("|")[0] for k in rb))
x["coll_m"] = data["collisions"] / 1e6
x["per_week_spring"] = M["H4"]["spring_n"]["week_count_per_event"]
x["per_week_autumn"] = M["H4"]["autumn_n"]["week_count_per_event"]
x["dist_excl1"] = DS["autumn"]["excl1"]; x["dist_expected"] = DS["autumn"]["excl1_expected"]
x["xp_aut_before_pc"] = (XP["real_autumn"] - 1) * 100; x["xp_spr_before_pc"] = (XP["real_spring"] - 1) * 100
R["x"] = x

# asserts on headline facts
assert data["collisions"] == 9116617 and data["year0"] == 1979 and data["year1"] == 2025
assert data["events_main"] == 91 and data["events"] == 94
assert M["H1"]["spring_n"]["lo"] < 1 < M["H1"]["spring_n"]["hi"]
assert M["H1"]["autumn_n"]["lo"] < 1 < M["H1"]["autumn_n"]["hi"]
assert M["H1"]["autumn_fatal"]["lo"] < 1 < M["H1"]["autumn_fatal"]["hi"]
assert M["H2"]["autumn_evening_n"]["lo"] > 1
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: round(v, 2) if isinstance(v, float) else v for k, v in x.items() if k.startswith(("h1_", "h2_autumn_evening", "dark_autumn_evening", "pl_h1", "rb_"))}, indent=0)[:3000])
