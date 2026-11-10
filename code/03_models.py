"""Step 3: the pre-specified models (NOTES.md). Output data/models.json (every estimate) and data/event_study.csv,
data/hour_profile.csv, data/placebo.csv.
H1 whole-day: PPML, count ~ treat + holiday | event x weekday, clustered by year.
H2 hours: PPML, count ~ treat x hour group | day + event x group, clustered by year (day FE absorb whole-day shocks)."""
import warnings
import pandas as pd
import pyfixest as pf
from common import *

warnings.filterwarnings("ignore")
E = pd.read_csv(f"{DATA}/events.csv")
D0_ = pd.read_csv(f"{DATA}/event_days.csv")
H0_ = pd.read_csv(f"{DATA}/event_hours.csv")
EV = E.set_index("event")
TREAT = tuple(range(0, 7))
CTRL = tuple(range(-21, 0)) + tuple(range(7, 28))


def prep_days(D, ev_meta=True):
    D = D.copy()
    if ev_meta:
        D["year"] = D.event.map(EV.year); D["season"] = D.event.map(EV.season)
    D["evdow"] = D.event.astype(str) + "_" + D.dow.astype(str)
    return D


def grp_of(h, groups=GROUPS):
    for g, hs in groups.items():
        if h in hs:
            return g
    return "other"


def ci(b, se, n, **kw):
    return dict(rr=math.exp(b), lo=math.exp(b - 1.96 * se), hi=math.exp(b + 1.96 * se), b=b, se=se, n=int(n), **kw)


def h1(D, y="n", treat=TREAT, ctrl=CTRL, holiday=True):
    D = D[D.rel.isin(treat + ctrl)].copy()
    D["treat"] = D.rel.isin(treat).astype(int)
    f = f"{y} ~ treat" + (" + holiday" if holiday and D.holiday.nunique() > 1 else "") + " | evdow"
    m = pf.fepois(f, data=D, vcov={"CRV1": "year"})
    b, se = float(m.coef()["treat"]), float(m.se()["treat"])
    return ci(b, se, len(D), events=int(D.event.nunique()), count=int(D.loc[D.treat == 1, y].sum()))


def group_panel(H, y="n", groups=GROUPS):
    H = H.copy()
    H["grp"] = H.hour.map(lambda h: grp_of(h, groups))
    G = H.groupby(["event", "rel", "grp"], as_index=False)[[y, "dark"] if y != "dark" else [y]].sum()
    return G


def h2(H, y="n", treat=TREAT, ctrl=CTRL, groups=GROUPS, ev_meta=True):
    G = group_panel(H, y, groups)
    G = G[G.rel.isin(treat + ctrl)].copy()
    if ev_meta:
        G["year"] = G.event.map(EV.year)
    G["treat"] = G.rel.isin(treat).astype(int)
    G["day"] = G.event.astype(str) + "_" + G.rel.astype(str)
    G["evgrp"] = G.event.astype(str) + "_" + G.grp
    out = {}
    names = []
    for g in ("evening", "morning", "other"):
        G[f"t_{g}"] = ((G.grp == g) & (G.treat == 1)).astype(int); names.append(f"t_{g}")
    m = pf.fepois(f"{y} ~ " + " + ".join(names) + " | day + evgrp", data=G, vcov={"CRV1": "year"})
    for g in ("evening", "morning", "other"):
        b, se = float(m.coef()[f"t_{g}"]), float(m.se()[f"t_{g}"])
        out[g] = ci(b, se, len(G), events=int(G.event.nunique()),
                    count=int(G.loc[(G.grp == g) & (G.treat == 1), y].sum()))
    out["_vcov"] = m._vcov.tolist() if hasattr(m, "_vcov") else None
    return out


def subset(df, season, include_excluded=False, years=None, extra=None):
    ev = E[(E.season == season)]
    if not include_excluded:
        ev = ev[~ev.excluded]
    if years:
        ev = ev[(ev.year >= years[0]) & (ev.year <= years[1])]
    if extra is not None:
        ev = ev[extra(ev)]
    return df[df.event.isin(ev.event)]


R = {"H1": {}, "H1b": {}, "H2": {}, "robust": {}, "placebo": {}}
D = prep_days(D0_)
# ---- H1
for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        R["H1"][f"{s}_{y}"] = h1(subset(D, s), y)
        print("H1", s, y, {k: round(v, 3) for k, v in R["H1"][f"{s}_{y}"].items() if k in ("rr", "lo", "hi")})
    # secondary: Monday after (day 1), first working week (days 1 to 5)
    for y in ("n", "fatal"):
        mon = h1(subset(D, s), y, treat=(1,), ctrl=tuple(r for r in CTRL if (r - 1) % 7 == 0))
        R["H1b"][f"{s}_monday_{y}"] = mon
        R["H1b"][f"{s}_workweek_{y}"] = h1(subset(D, s), y, treat=(1, 2, 3, 4, 5), ctrl=tuple(r for r in CTRL if r % 7 in (1, 2, 3, 4, 5)))
    print("Monday", s, round(R["H1b"][f"{s}_monday_n"]["rr"], 3), round(R["H1b"][f"{s}_monday_n"]["lo"], 3), round(R["H1b"][f"{s}_monday_n"]["hi"], 3))

# ---- H2
for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        o = h2(subset(H0_, s), y)
        o.pop("_vcov")
        for g, v in o.items():
            R["H2"][f"{s}_{g}_{y}"] = v
        print("H2", s, y, {g: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3)) for g, v in o.items()})

# manipulation check: share of evening collisions recorded in darkness, comparison vs treatment weeks
R["dark_share"] = {}
for s in ("spring", "autumn"):
    Hs = subset(H0_, s)
    for g, hs in GROUPS.items():
        x = Hs[Hs.hour.isin(hs)]
        c = x[x.rel.isin(CTRL)]; t = x[x.rel.isin(TREAT)]
        R["dark_share"][f"{s}_{g}"] = {"ctrl": float(c.dark.sum() / (c.dark.sum() + c.light.sum())),
                                       "treat": float(t.dark.sum() / (t.dark.sum() + t.light.sum()))}
print("dark share", {k: (round(v["ctrl"], 3), round(v["treat"], 3)) for k, v in R["dark_share"].items()})

# ---- H3 darkness: stacked spring and autumn, combined (b_aut - b_spr)/2 with the joint cluster covariance
def h3(y):
    G = group_panel(subset(H0_, "spring").pipe(lambda x: pd.concat([x, subset(H0_, "autumn")])), y)
    G = G[G.rel.isin(TREAT + CTRL)].copy()
    G["year"] = G.event.map(EV.year); G["season"] = G.event.map(EV.season)
    G["treat"] = G.rel.isin(TREAT).astype(int)
    G["day"] = G.event + "_" + G.rel.astype(str); G["evgrp"] = G.event + "_" + G.grp
    names = []
    for g in ("evening", "morning", "other"):
        for s in ("spring", "autumn"):
            G[f"t_{g}_{s}"] = ((G.grp == g) & (G.treat == 1) & (G.season == s)).astype(int); names.append(f"t_{g}_{s}")
    m = pf.fepois(f"{y} ~ " + " + ".join(names) + " | day + evgrp", data=G, vcov={"CRV1": "year"})
    V = pd.DataFrame(m._vcov, index=m.coef().index, columns=m.coef().index)
    out = {}
    for g in ("evening", "morning"):
        a, sp = f"t_{g}_autumn", f"t_{g}_spring"
        # darkness contrast: evening gets dark in autumn, light in spring; morning the reverse
        sign = 1 if g == "evening" else -1
        b = sign * (m.coef()[a] - m.coef()[sp]) / 2
        var = (V.loc[a, a] + V.loc[sp, sp] - 2 * V.loc[a, sp]) / 4
        out[g] = ci(float(b), float(math.sqrt(var)), len(G))
    return out


R["H3"] = {}
for y in ("n", "fatal"):
    o = h3(y)
    for g, v in o.items():
        R["H3"][f"{g}_{y}"] = v
    print("H3", y, {g: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3)) for g, v in o.items()})
# exploratory scaling: per-collision darkness risk ratio theta solving RR = (1 + p1 (theta-1)) / (1 + p0 (theta-1))
R["H3_theta"] = {}
for s in ("autumn", "spring"):
    for y in ("n", "fatal"):
        rr = R["H2"][f"{s}_evening_{y}"]["rr"]
        p0, p1 = R["dark_share"][f"{s}_evening"]["ctrl"], R["dark_share"][f"{s}_evening"]["treat"]
        # rr (1 + p0 x) = 1 + p1 x  ->  x = (rr - 1) / (p1 - rr p0)
        x = (rr - 1) / (p1 - rr * p0)
        R["H3_theta"][f"{s}_{y}"] = {"theta": 1 + x, "p0": p0, "p1": p1}
print("theta", R["H3_theta"])

# ---- H4 net change in collisions per change week (exploratory arithmetic)
R["H4"] = {}
for s in ("spring", "autumn"):
    Hs = subset(H0_, s)
    nev = Hs.event.nunique()
    for y in ("n", "fatal"):
        tot = 0; parts = {}
        for g in ("evening", "morning", "other"):
            rr = R["H2"][f"{s}_{g}_{y}"]["rr"]
            hs = GROUPS.get(g)
            x = Hs[Hs.rel.isin(TREAT)]
            cnt = (x[x.hour.isin(hs)] if hs else x[~x.hour.isin(sum(GROUPS.values(), ()))])[y].sum() / nev
            parts[g] = float(cnt * (1 - 1 / rr)); tot += parts[g]
        whole = R["H1"][f"{s}_{y}"]["rr"]; wk = Hs[Hs.rel.isin(TREAT)][y].sum() / nev
        R["H4"][f"{s}_{y}"] = {**{f"{g}_per_event": v for g, v in parts.items()}, "week_count_per_event": float(wk),
                                "whole_day_change_per_event": float(wk * (1 - 1 / whole))}
print("H4", R["H4"])

# ---- hour-by-hour profile (figure): each hour vs the reference hours
prof = []
for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        Hs = subset(H0_, s); Hs = Hs[Hs.rel.isin(TREAT + CTRL)].copy()
        Hs["year"] = Hs.event.map(EV.year); Hs["treat"] = Hs.rel.isin(TREAT).astype(int)
        Hs["hc"] = np.where(Hs.hour.isin(REFERENCE), -1, Hs.hour)
        Hs = Hs.groupby(["event", "year", "rel", "treat", "hc"], as_index=False)[y].sum()
        Hs["day"] = Hs.event + "_" + Hs.rel.astype(str); Hs["evh"] = Hs.event + "_" + Hs.hc.astype(str)
        names = []
        for h in range(24):
            if h in REFERENCE: continue
            Hs[f"t{h}"] = ((Hs.hc == h) & (Hs.treat == 1)).astype(int); names.append(f"t{h}")
        m = pf.fepois(f"{y} ~ " + " + ".join(names) + " | day + evh", data=Hs, vcov={"CRV1": "year"})
        for h in range(24):
            if h in REFERENCE:
                prof.append((s, y, h, 1.0, np.nan, np.nan)); continue
            b, se = m.coef()[f"t{h}"], m.se()[f"t{h}"]
            prof.append((s, y, h, math.exp(b), math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)))
P = pd.DataFrame(prof, columns=["season", "outcome", "hour", "rr", "lo", "hi"])
P.to_csv(f"{DATA}/hour_profile.csv", index=False)

# ---- event study: pooled ratio of each day's count to the same weekday's comparison mean, bootstrap over years
rng = np.random.default_rng(2026)
es = []
for s in ("spring", "autumn"):
    Ds = subset(D, s)
    Hs = subset(H0_, s)
    ev_hr = Hs.assign(g=Hs.hour.map(grp_of)).pivot_table(index=["event", "rel"], columns="g", values="n", aggfunc="sum").reset_index()
    for y in ("n", "fatal", "evening_rel"):
        if y == "evening_rel":
            X = ev_hr.copy(); X["v"] = X.evening; X["w"] = X.reference
        else:
            X = Ds[["event", "rel", y]].rename(columns={y: "v"}); X["w"] = 1.0
        X["dow"] = X.rel % 7
        X["year"] = X.event.map(EV.year)
        piv_v = X.pivot(index="event", columns="rel", values="v"); piv_w = X.pivot(index="event", columns="rel", values="w")
        evs = piv_v.index.values; years = X.drop_duplicates("event").set_index("event").year.loc[evs].values
        V, W = piv_v.values.astype(float), piv_w.values.astype(float)
        rels = piv_v.columns.values
        ctrl_mask = np.isin(rels, CTRL)

        def curve(ix):
            v, w = V[ix].sum(0), W[ix].sum(0)
            out = []
            for j, r in enumerate(rels):
                cm = ctrl_mask & (rels % 7 == r % 7) & (rels != r)
                if y == "evening_rel":
                    base = v[cm].sum() / w[cm].sum(); out.append((v[j] / w[j]) / base)
                else:
                    out.append(v[j] / v[cm].mean())
            return np.array(out)
        est = curve(np.arange(len(evs)))
        uy = np.unique(years); B = []
        for _ in range(2000):
            pick = rng.choice(uy, len(uy))
            ix = np.concatenate([np.nonzero(years == q)[0] for q in pick])
            B.append(curve(ix))
        B = np.array(B)
        for j, r in enumerate(rels):
            es.append((s, y, int(r), float(est[j]), float(np.percentile(B[:, j], 2.5)), float(np.percentile(B[:, j], 97.5))))
ES = pd.DataFrame(es, columns=["season", "outcome", "rel", "ratio", "lo", "hi"])
ES.to_csv(f"{DATA}/event_study.csv", index=False)

# ---- placebo Sundays, pooled by ISO week across years (same models)
PD = prep_days(pd.read_parquet(f"{SCR}/placebo_days.parquet"), ev_meta=False)
PH = pd.read_parquet(f"{SCR}/placebo_hours.parquet")
PS = pd.read_csv(f"{DATA}/placebo_sundays.csv")
PD["year"] = PD.event.str[:4].astype(int); PH["year"] = PH.event.str[:4].astype(int)
wk = dict(zip(PS.date, PS.week))
PD["week"] = PD.event.map(wk); PH["week"] = PH.event.map(wk)
pl = []
for w, g in PD.groupby("week"):
    if g.event.nunique() < 20:
        continue
    gh = PH[PH.week == w]
    row = {"week": int(w), "events": int(g.event.nunique())}
    for y in ("n", "fatal"):
        a = h1(g, y)
        row[f"h1_{y}"], row[f"h1_{y}_lo"], row[f"h1_{y}_hi"] = a["rr"], a["lo"], a["hi"]
        G = group_panel(gh, y); G = G[G.rel.isin(TREAT + CTRL)].copy()
        G["year"] = G.event.str[:4].astype(int); G["treat"] = G.rel.isin(TREAT).astype(int)
        G["day"] = G.event + "_" + G.rel.astype(str); G["evgrp"] = G.event + "_" + G.grp
        for gg in ("evening", "morning", "other"):
            G[f"t_{gg}"] = ((G.grp == gg) & (G.treat == 1)).astype(int)
        m = pf.fepois(f"{y} ~ t_evening + t_morning + t_other | day + evgrp", data=G, vcov={"CRV1": "year"})
        for gg in ("evening", "morning"):
            b, se = m.coef()[f"t_{gg}"], m.se()[f"t_{gg}"]
            row[f"h2_{gg}_{y}"], row[f"h2_{gg}_{y}_lo"], row[f"h2_{gg}_{y}_hi"] = math.exp(b), math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)
    pl.append(row)
PL = pd.DataFrame(pl)
PL.to_csv(f"{DATA}/placebo.csv", index=False)
print("placebo weeks", len(PL))


def rank(real, col):
    lr = abs(math.log(real)); lp = np.abs(np.log(PL[col].values))
    return {"share_as_large": float((lp >= lr).mean()), "n": int(len(PL)), "max_abs_pc": float((np.exp(lp.max()) - 1) * 100),
            "ci_excl_1": int(((PL[col + "_lo"] > 1) | (PL[col + "_hi"] < 1)).sum())}


for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        R["placebo"][f"h1_{s}_{y}"] = rank(R["H1"][f"{s}_{y}"]["rr"], f"h1_{y}")
        for g in ("evening", "morning"):
            R["placebo"][f"h2_{s}_{g}_{y}"] = rank(R["H2"][f"{s}_{g}_{y}"]["rr"], f"h2_{g}_{y}")
print("placebo", R["placebo"])

# ---- robustness
rb = {}
def both(label, fdays=None, fhours=None, seasons=("spring", "autumn"), **kw):
    for s in seasons:
        for y in ("n", "fatal"):
            key = f"{label}|{s}|{y}"
            r = {}
            if fdays is not None:
                r["h1"] = h1(fdays(s), y, **{k: v for k, v in kw.items() if k in ("treat", "ctrl")})
            if fhours is not None:
                o = h2(fhours(s), y, **{k: v for k, v in kw.items() if k in ("treat", "ctrl", "groups")}); o.pop("_vcov")
                r["evening"], r["morning"] = o["evening"], o["morning"]
            rb[key] = r


both("Comparison weeks 1 week either side only", lambda s: subset(D, s), lambda s: subset(H0_, s), ctrl=tuple(range(-7, 0)) + tuple(range(7, 14)))
both("Comparison weeks before only", lambda s: subset(D, s), lambda s: subset(H0_, s), ctrl=tuple(range(-21, 0)))
both("Comparison weeks after only", lambda s: subset(D, s), lambda s: subset(H0_, s), ctrl=tuple(range(7, 28)))
both("Working days 1 to 5 only", lambda s: subset(D, s), lambda s: subset(H0_, s), treat=(1, 2, 3, 4, 5), ctrl=tuple(r for r in CTRL if r % 7 in (1, 2, 3, 4, 5)))
both("Including 2020 and spring 2021", lambda s: subset(D, s, include_excluded=True), lambda s: subset(H0_, s, include_excluded=True))
for lab, yr in (("1979 to 1995", (1979, 1995)), ("1996 to 2010", (1996, 2010)), ("2011 to 2025", (2011, 2025))):
    both(f"Years {lab}", lambda s, yr=yr: subset(D, s, years=yr), lambda s, yr=yr: subset(H0_, s, years=yr))
both("Spring events without Easter in the change week", lambda s: subset(D, s, extra=lambda e: ~e.easter_in_treat_week),
     lambda s: subset(H0_, s, extra=lambda e: ~e.easter_in_treat_week), seasons=("spring",))
both("Season-specific evening (autumn 16:00 to 18:59, spring 18:00 to 19:59)", None,
     lambda s: subset(H0_, s), groups={"evening": (16, 17, 18), "morning": MORNING, "reference": REFERENCE}, seasons=("autumn",))
both("Season-specific evening (autumn 16:00 to 18:59, spring 18:00 to 19:59)", None,
     lambda s: subset(H0_, s), groups={"evening": (18, 19), "morning": MORNING, "reference": REFERENCE}, seasons=("spring",))
# exploratory (added after the first run, not in the plan): reference hours 10:00 to 13:59, away from the school run
both("Exploratory: reference hours 10:00 to 13:59", None, lambda s: subset(H0_, s),
     groups={"evening": EVENING, "morning": MORNING, "reference": (10, 11, 12, 13)})
both("Exploratory: weekends only (no commute or school run)", None, lambda s: subset(H0_, s),
     treat=(0, 6), ctrl=tuple(r for r in CTRL if r % 7 in (0, 6)))
# casualties
for s in ("spring", "autumn"):
    for y, yy in (("cas", "n"), ("cas_fatal", "fatal")):
        o = h2(subset(H0_, s), y); o.pop("_vcov")
        rb[f"Casualties instead of collisions|{s}|{yy}"] = {"h1": h1(subset(D, s), y), "evening": o["evening"], "morning": o["morning"]}
# negative binomial (H1): statsmodels GLM NB with event x weekday dummies, cluster by year
import statsmodels.formula.api as smf
import statsmodels.api as sm
for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        X = subset(D, s); X = X[X.rel.isin(TREAT + CTRL)].copy(); X["treat"] = X.rel.isin(TREAT).astype(int)
        fh = f"{y} ~ treat" + (" + holiday" if X.holiday.nunique() > 1 else "") + " + C(evdow)"
        pm = smf.glm(fh, data=X, family=sm.families.Poisson()).fit()
        mu = pm.mu; alpha = max(1e-8, float(((X[y] - mu) ** 2 - mu).sum() / (mu ** 2).sum()))
        nb = smf.glm(fh, data=X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(
            cov_type="cluster", cov_kwds={"groups": X.year.values})
        rb[f"Negative binomial (whole day)|{s}|{y}"] = {"h1": ci(float(nb.params["treat"]), float(nb.bse["treat"]), len(X), alpha=alpha)}
# by nation, whole day, 2009 to 2025 (from district codes)
LA = pd.read_csv(f"{DATA}/la_event_days.csv")
LA["nation"] = LA.lad23.str[0].map({"E": "England", "S": "Scotland", "W": "Wales"})
for nat in ("England", "Scotland", "Wales", "Great Britain (2009 to 2025)"):
    X = LA if nat.startswith("Great") else LA[LA.nation == nat]
    X = X.groupby(["event", "rel", "dow", "holiday"], as_index=False).n.sum()
    X = prep_days(X)
    for s in ("spring", "autumn"):
        rb[f"Nation: {nat}|{s}|n"] = {"h1": h1(subset(X, s), "n")}
# leave one nation out
for nat in ("England", "Scotland", "Wales"):
    X = LA[LA.nation != nat].groupby(["event", "rel", "dow", "holiday"], as_index=False).n.sum()
    X = prep_days(X)
    for s in ("spring", "autumn"):
        rb[f"Leave out {nat} (2009 to 2025)|{s}|n"] = {"h1": h1(subset(X, s), "n")}
R["robust"] = rb
# leave one year out (range of estimates)
loo = {}
for s in ("spring", "autumn"):
    for y in ("n", "fatal"):
        vals_h1, vals_ev, vals_mo = [], [], []
        yrs = sorted(subset(D, s).event.map(EV.year).unique())
        for yy in yrs:
            Dd = subset(D, s); Dd = Dd[Dd.year != yy]
            vals_h1.append(h1(Dd, y)["rr"])
            Hd_ = subset(H0_, s); Hd_ = Hd_[Hd_.event.map(EV.year) != yy]
            o = h2(Hd_, y); vals_ev.append(o["evening"]["rr"]); vals_mo.append(o["morning"]["rr"])
        loo[f"{s}_{y}"] = {"h1": [min(vals_h1), max(vals_h1)], "evening": [min(vals_ev), max(vals_ev)], "morning": [min(vals_mo), max(vals_mo)]}
R["loo"] = loo
print("loo", loo)
jsave(R, f"{DATA}/models.json", indent=1)
print("done")
