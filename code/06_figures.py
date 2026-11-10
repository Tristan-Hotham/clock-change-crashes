"""Step 6: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf)
and header.png (1200 x 630). Light paper; autumn = warm red, spring = blue (seasons, fixed order)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
import pandas as pd
from PIL import Image
from pyproj import Transformer
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
AUT, SPR, GREY = "#B4442E", "#2F6A9E", "#9C9384"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json"); X = R["x"]
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD): os.makedirs(d_, exist_ok=True)
SRC = "Data: DfT Road Safety Data (STATS19), every reported injury collision in Great Britain 1979 to 2025 · maps.tristanhotham.com/clock-change-crashes"
E = pd.read_csv(f"{DATA}/events.csv"); EV = E.set_index("event")
MAIN = set(E[~E.excluded].event)
TREAT = range(0, 7); CTRL = list(range(-21, 0)) + list(range(7, 28))


def out(fig, name, page=True, blog=True, paper=True):
    if paper: fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor()); plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, s=None, y=0.975):
    fig.text(0.04, y, t, fontsize=19, color=INK, va="top", family=DISP)
    if s: fig.text(0.04, y - 0.065, s, fontsize=11.5, color=MUT, va="top")
    fig.text(0.04, 0.012, SRC, fontsize=8, color=MUT, family=MONO)


H = pd.read_csv(f"{DATA}/event_hours.csv"); H = H[H.event.isin(MAIN)]
H["season"] = H.event.map(EV.season)

# 1 darkness by clock hour
fig, axs = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)
fig.subplots_adjust(left=0.07, right=0.98, top=0.78, bottom=0.14, wspace=0.08)
dark_tab = {}
for ax, s in zip(axs, ("autumn", "spring")):
    x = H[H.season == s]
    for lab, rels, ls in (("three weeks either side", CTRL, "--"), ("the week after the change", list(TREAT), "-")):
        y = x[x.rel.isin(rels)].groupby("hour")[["dark", "light"]].sum()
        sh = 100 * y.dark / (y.dark + y.light)
        dark_tab[f"{s}|{lab}"] = sh.round(1).tolist()
        ax.plot(sh.index, sh.values, ls, color=AUT if s == "autumn" else SPR, lw=2.2 if ls == "-" else 1.6, label=lab)
    ax.axvspan(16.5, 18.5, color=RULE, alpha=0.5, lw=0); ax.axvspan(5.5, 8.5, color=RULE, alpha=0.5, lw=0)
    ax.text(17.5, 103, "evening\n17:00 to 18:59", ha="center", fontsize=9, color=MUT, va="bottom")
    ax.text(7, 103, "morning\n06:00 to 08:59", ha="center", fontsize=9, color=MUT, va="bottom")
    ax.set_xticks(range(0, 24, 3)); ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)], fontsize=9)
    ax.set_ylim(0, 112); ax.set_xlim(0, 23)
    ax.set_title("Clocks go back (autumn)" if s == "autumn" else "Clocks go forward (spring)", fontsize=12.5, loc="left", color=INK, pad=24)
    ax.legend(frameon=False, fontsize=9.5, loc="lower left")
axs[0].set_ylabel("collisions recorded in darkness (%)")
title(fig, "The dark arrives an hour earlier, on the clock", "Share of reported injury collisions that police recorded as in darkness, by clock hour, 91 changes 1979 to 2025")
out(fig, "dark")
jsave(dark_tab, f"{DATA}/dark_by_hour.json")

# 2 hour-by-hour rate ratios
P = pd.read_csv(f"{DATA}/hour_profile.csv")
fig, axs = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)
fig.subplots_adjust(left=0.07, right=0.98, top=0.78, bottom=0.14, wspace=0.08)
for ax, s in zip(axs, ("autumn", "spring")):
    p = P[(P.season == s) & (P.outcome == "n")]
    c = AUT if s == "autumn" else SPR
    ax.axhline(1, color=MUT, lw=0.8)
    ax.axvspan(16.5, 18.5, color=RULE, alpha=0.5, lw=0); ax.axvspan(5.5, 8.5, color=RULE, alpha=0.5, lw=0)
    ax.axvspan(9.5, 15.5, color="#E8E1CC", alpha=0.6, lw=0)
    ax.text(12.5, 1.33, "reference\nhours", ha="center", fontsize=9, color=MUT, va="top")
    q = p.dropna()
    ax.vlines(q.hour, q.lo, q.hi, color=c, lw=1.6, alpha=0.6)
    ax.plot(q.hour, q.rr, "o", color=c, ms=6, mec=PAPER, mew=1)
    ax.set_xticks(range(0, 24, 3)); ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)], fontsize=9)
    ax.set_ylim(0.6, 1.4); ax.set_xlim(-0.5, 23.5)
    ax.set_title("Clocks go back (autumn)" if s == "autumn" else "Clocks go forward (spring)", fontsize=12.5, loc="left", color=INK)
axs[0].set_ylabel("rate ratio, week after vs weeks around")
axs[0].annotate("the change night's\ndoubled hour", (1, P[(P.season == "autumn") & (P.outcome == "n") & (P.hour == 1)].rr.iloc[0]), (3.2, 1.33),
                fontsize=9, color=MUT, va="top", arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7))
axs[1].annotate("the change night's\nmissing hour", (1, P[(P.season == "spring") & (P.outcome == "n") & (P.hour == 1)].rr.iloc[0]), (2.2, 0.66),
                fontsize=9, color=MUT, va="bottom", arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7))
title(fig, "Hour by hour, small shifts", "Collisions in each clock hour in the week after the change, relative to the same hours in the three weeks either side,\nand to 10:00 to 15:59; 95% intervals; all reported injury collisions")
out(fig, "hours")

# 3 event study (all and fatal)
ES = pd.read_csv(f"{DATA}/event_study.csv")
fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharey=False)
fig.subplots_adjust(left=0.07, right=0.98, top=0.76, bottom=0.16, wspace=0.18)
for ax, y, lab in zip(axs, ("n", "fatal"), ("All reported injury collisions", "Fatal collisions")):
    ax.axhline(1, color=MUT, lw=0.8); ax.axvspan(-0.5, 6.5, color=RULE, alpha=0.5, lw=0)
    for s in ("spring", "autumn"):
        e = ES[(ES.season == s) & (ES.outcome == y)]
        c = AUT if s == "autumn" else SPR
        ax.fill_between(e.rel, e.lo, e.hi, color=c, alpha=0.13, lw=0)
        ax.plot(e.rel, e.ratio, "-", color=c, lw=1.6, label="clocks go back" if s == "autumn" else "clocks go forward")
    ax.set_xlim(-21, 27); ax.set_xlabel("days from the change (Sunday = 0)")
    ax.set_title(lab, fontsize=12.5, loc="left", color=INK)
    ax.set_ylim((0.85, 1.15) if y == "n" else (0.6, 1.4))
    ax.text(3, ax.get_ylim()[1] * 0.995, "the week\nafter", ha="center", va="top", fontsize=9, color=MUT)
axs[0].set_ylabel("ratio to the same weekday, weeks around")
axs[0].legend(frameon=False, fontsize=9.5, loc="lower left")
title(fig, "No jump after the clocks change", "Each day's collisions divided by the average for that weekday in the comparison weeks, pooled over 91 changes;\nshaded: 95% intervals from resampling years")
out(fig, "event")


# 3b evening share event study (exploratory)
fig, ax = plt.subplots(figsize=(11, 5.3))
fig.subplots_adjust(left=0.08, right=0.98, top=0.76, bottom=0.16)
ax.axhline(0, color=MUT, lw=0.8); ax.axvspan(-0.5, 6.5, color=RULE, alpha=0.5, lw=0)
for s in ("spring", "autumn"):
    e = ES[(ES.season == s) & (ES.outcome == "evening_rel")]
    c = AUT if s == "autumn" else SPR
    ax.fill_between(e.rel, (e.lo - 1) * 100, (e.hi - 1) * 100, color=c, alpha=0.13, lw=0)
    ax.plot(e.rel, (e.ratio - 1) * 100, "-", color=c, lw=1.8, label="clocks go back" if s == "autumn" else "clocks go forward")
ax.set_xlim(-21, 27); ax.set_xlabel("days from the change (Sunday = 0)"); ax.set_ylabel("evening share vs comparison weeks (%)")
ax.legend(frameon=False, fontsize=10, loc="upper left")
title(fig, "The evening rush hour's share of the day", "Collisions at 17:00 to 18:59 relative to 10:00 to 15:59, each day against the same weekday in the comparison weeks,\npooled over the changes; 95% intervals from resampling years (exploratory view)")
out(fig, "evening", blog=False)

# 4 placebo
PL = pd.read_csv(f"{DATA}/placebo.csv")
rows = [("Whole week, all collisions", "h1_n", "spring_n", "autumn_n", "H1"),
        ("Whole week, fatal", "h1_fatal", "spring_fatal", "autumn_fatal", "H1"),
        ("Evening 17:00 to 18:59, all", "h2_evening_n", "spring_evening_n", "autumn_evening_n", "H2"),
        ("Evening 17:00 to 18:59, fatal", "h2_evening_fatal", "spring_evening_fatal", "autumn_evening_fatal", "H2")]
fig, ax = plt.subplots(figsize=(11, 5.2))
fig.subplots_adjust(left=0.27, right=0.97, top=0.8, bottom=0.16)
for i, (lab, col, ks, ka, h) in enumerate(rows):
    yv = len(rows) - 1 - i
    v = (PL[col] - 1) * 100
    ax.scatter(v, np.full(len(v), yv) + np.random.default_rng(i).uniform(-0.12, 0.12, len(v)), s=26, color=GREY, alpha=0.75, lw=0, zorder=2)
    for k, c, mk in ((ks, SPR, "D"), (ka, AUT, "o")):
        ax.scatter([(R[h][k]["rr"] - 1) * 100], [yv], s=110, color=c, marker=mk, edgecolor=INK, lw=0.8, zorder=3)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=11)
ax.axvline(0, color=MUT, lw=0.8); ax.set_xlabel("change in the week after a Sunday (%)")
ax.scatter([], [], s=26, color=GREY, label="29 ordinary Sundays (placebo, pooled over years)")
ax.scatter([], [], s=90, color=SPR, marker="D", edgecolor=INK, label="clocks go forward"); ax.scatter([], [], s=90, color=AUT, marker="o", edgecolor=INK, label="clocks go back")
ax.legend(frameon=False, fontsize=9.5, loc="upper center", bbox_to_anchor=(0.45, 1.13), ncol=3)
title(fig, "Clock-change weeks look like ordinary weeks", "The same measure for the real changes and for 29 ordinary Sundays treated as if the clocks had changed", y=0.985)
out(fig, "placebo")

# 5 per-event whole-week ratios by year
D = pd.read_csv(f"{DATA}/event_days.csv"); D = D[D.event.isin(MAIN)]
pe_rows = []
for ev, g in D.groupby("event"):
    t = g[g.rel.between(0, 6)]; c = g[g.rel.isin(CTRL)]
    pe_rows.append((ev, EV.loc[ev, "year"], EV.loc[ev, "season"], t.n.sum() / (c.n.sum() / 6), t.fatal.sum(), c.fatal.sum() / 6))
PE = pd.DataFrame(pe_rows, columns=["event", "year", "season", "ratio", "fatal_t", "fatal_c"])
PE.to_csv(f"{DATA}/event_ratios.csv", index=False)
fig, ax = plt.subplots(figsize=(11, 5))
fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.12)
ax.axhline(0, color=MUT, lw=0.8)
for s, c, mk in (("spring", SPR, "D"), ("autumn", AUT, "o")):
    p = PE[PE.season == s].set_index("year").reindex(range(1979, 2026)).reset_index()
    ax.plot(p.year, (p.ratio - 1) * 100, mk + "-", color=c, ms=5.5, lw=0.9, alpha=0.9, label="clocks go forward" if s == "spring" else "clocks go back")
ax.set_ylabel("change in the week after (%)"); ax.set_xlim(1978, 2026)
ax.legend(frameon=False, fontsize=10, loc="upper left", ncol=2)
title(fig, "Year by year, the change week wobbles around zero", "All reported injury collisions in the week after each change, relative to the same weekdays in the three weeks either side")
out(fig, "years")

# 6 robustness forest
rb = R["robust"]
items = [("Main estimate", R["H1"]["spring_n"], R["H1"]["autumn_n"])]
for lab in ["Comparison weeks 1 week either side only", "Comparison weeks before only", "Comparison weeks after only", "Working days 1 to 5 only",
            "Including 2020 and spring 2021", "Years 1979 to 1995", "Years 1996 to 2010", "Years 2011 to 2025", "Casualties instead of collisions",
            "Negative binomial (whole day)", "Nation: England", "Nation: Scotland", "Nation: Wales"]:
    items.append((lab, rb[f"{lab}|spring|n"]["h1"], rb[f"{lab}|autumn|n"]["h1"]))
fig, ax = plt.subplots(figsize=(11, 7))
fig.subplots_adjust(left=0.36, right=0.97, top=0.86, bottom=0.12)
for i, (lab, sp, au) in enumerate(items):
    yv = len(items) - 1 - i
    for v, c, off, mk in ((sp, SPR, 0.17, "D"), (au, AUT, -0.17, "o")):
        ax.plot([(v["lo"] - 1) * 100, (v["hi"] - 1) * 100], [yv + off] * 2, color=c, lw=1.6)
        ax.plot([(v["rr"] - 1) * 100], [yv + off], mk, color=c, ms=6, mec=PAPER)
ax.axvline(0, color=MUT, lw=0.8)
ax.set_yticks(range(len(items))); ax.set_yticklabels([i[0].replace("Nation: ", "Only ") + (" (2009 to 2025)" if i[0].startswith("Nation") else "") for i in items][::-1], fontsize=10)
ax.set_xlabel("change in all reported injury collisions in the week after (%), 95% interval")
ax.plot([], [], "D-", color=SPR, label="clocks go forward"); ax.plot([], [], "o-", color=AUT, label="clocks go back")
ax.legend(frameon=False, fontsize=10, loc="upper center", bbox_to_anchor=(0.4, 1.08), ncol=2)
title(fig, "Nearly every check gives about zero", "Whole-week change under each planned robustness check (all reported injury collisions)", y=0.985)
out(fig, "robust")

# 7 district map (autumn raw ratio), BNG
geo = jload(f"{DATA}/districts_map.geojson")
tr = Transformer.from_crs(4326, 27700, always_xy=True)
cmap = LinearSegmentedColormap.from_list("d", ["#2F6A9E", "#9DB8CF", "#EDE6D3", "#E3A48F", "#B4442E"])
norm = TwoSlopeNorm(1.0, 0.8, 1.2)
fig = plt.figure(figsize=(8.4, 10.5))
ax = fig.add_axes([0.02, 0.06, 0.96, 0.8]); ax.set_aspect("equal"); ax.axis("off")
patches, cols, edges = [], [], []
for f in geo["features"]:
    p = f["properties"]; g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    v = p["a_rr"]
    sig = v is not None and (p["a_lo"] > 1 or p["a_hi"] < 1)
    for poly in polys:
        xs, ys = tr.transform(*zip(*poly[0]))
        patches.append(MPoly(np.c_[xs, ys], closed=True)); cols.append(cmap(norm(v)) if v else "#DDD"); edges.append(INK if sig else PAPER)
pc_ = PatchCollection(patches, facecolor=cols, edgecolor=edges, linewidth=[0.9 if e == INK else 0.25 for e in edges])
ax.add_collection(pc_); ax.autoscale_view()
ax.set_xlim(-20000, 700000); ax.set_ylim(0, 1230000)
cax = fig.add_axes([0.56, 0.62, 0.36, 0.018])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm); cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_ticks([0.8, 0.9, 1, 1.1, 1.2]); cb.set_ticklabels(["-20%", "-10%", "0", "+10%", "+20%"]); cb.ax.tick_params(labelsize=9)
cax.set_title("Week after the clocks go back,\nvs three weeks either side", fontsize=10, color=INK, loc="left")
fig.text(0.56, 0.535, f"Outlined: the {R['districts']['autumn']['excl1']} of {R['districts']['autumn']['districts']} districts\n"
         f"whose 95% interval excludes zero.\nBy chance alone, about {R['districts']['autumn']['excl1_expected']:.0f} would.\n2009 to 2025, 16 autumn changes.",
         fontsize=10, color=MUT, va="top")
fig.text(0.04, 0.975, "A map of noise", fontsize=21, color=INK, va="top", family=DISP)
fig.text(0.04, 0.935, "Local authority districts (2023 boundaries)", fontsize=12, color=MUT, va="top")
fig.text(0.04, 0.012, "Data: DfT STATS19 (OGL v3.0); boundaries ONS (OGL v3.0) · maps.tristanhotham.com/clock-change-crashes", fontsize=8, color=MUT, family=MONO)
out(fig, "map")

# header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(0.05, 0.86, "Do the clocks kill?", fontsize=46, color=INK, va="top", family=DISP)
fig.text(0.05, 0.69, "Road collisions either side of the clock\nchanges, Great Britain 1979 to 2025", fontsize=19, color=MUT, va="top")
fig.text(0.05, 0.36, f"{X['coll_m']:.1f} million collisions", fontsize=17, color=INK, va="top", family=MONO)
fig.text(0.05, 0.27, f"week after clocks go forward: {X['h1_spring_n_pc']:+.1f}%", fontsize=15, color=SPR, va="top", family=MONO)
fig.text(0.05, 0.20, f"week after clocks go back:    {X['h1_autumn_n_pc']:+.1f}%", fontsize=15, color=AUT, va="top", family=MONO)
fig.text(0.05, 0.07, "Dr Tristan Hotham · maps.tristanhotham.com/clock-change-crashes", fontsize=11, color=MUT, va="bottom", family=MONO)
ax = fig.add_axes([0.62, 0.16, 0.34, 0.66])
for s in ("spring", "autumn"):
    e = ES[(ES.season == s) & (ES.outcome == "n")]
    ax.plot(e.rel, (e.ratio - 1) * 100, color=AUT if s == "autumn" else SPR, lw=2)
ax.axhline(0, color=MUT, lw=0.8); ax.axvspan(-0.5, 6.5, color=RULE, alpha=0.6, lw=0)
ax.set_ylim(-12, 12); ax.set_xlim(-21, 27); ax.set_xlabel("days from the change", fontsize=11); ax.set_ylabel("% vs same weekday", fontsize=11)
ax.text(3, 11, "week\nafter", ha="center", va="top", fontsize=10, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
