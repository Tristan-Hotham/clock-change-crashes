"""Reddit collage for clock-change-crashes (r/dataisbeautiful style, light background). Run from the study root:
python3 reddit/collage.py  ->  reddit/clock_change_crashes_collage.png (2400 px wide). Every number from data/results.json."""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MPoly
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from common import DATA, FONTS, jload

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
AUT, SPR, GREY = "#B4442E", "#2F6A9E", "#9C9384"
plt.rcParams.update({"font.family": "Source Serif 4", "font.size": 13, "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.spines.top": False, "axes.spines.right": False, "axes.unicode_minus": False})
R = jload(f"{DATA}/results.json"); X = R["x"]
ES = pd.read_csv(f"{DATA}/event_study.csv")
dark = jload(f"{DATA}/dark_by_hour.json")
PL = pd.read_csv(f"{DATA}/placebo.csv")

fig = plt.figure(figsize=(12, 15.6), dpi=200)
fig.text(0.04, 0.98, "Do the clocks kill?", fontsize=44, color=INK, va="top", family=DISP)
fig.text(0.04, 0.932, f"Every reported injury road collision in Great Britain, 1979 to 2025 ({X['coll_m']:.1f} million).\n"
         f"The week after each of {R['data']['events_main']} clock changes, against the same weekdays three weeks either side.",
         fontsize=15, color=MUT, va="top")

# A: event study
ax = fig.add_axes([0.07, 0.635, 0.88, 0.19])
ax.axhline(0, color=MUT, lw=0.9); ax.axvspan(-0.5, 6.5, color=RULE, alpha=0.6, lw=0)
for s, c, lab in (("spring", SPR, "clocks go forward"), ("autumn", AUT, "clocks go back")):
    e = ES[(ES.season == s) & (ES.outcome == "n")]
    ax.fill_between(e.rel, (e.lo - 1) * 100, (e.hi - 1) * 100, color=c, alpha=0.12, lw=0)
    ax.plot(e.rel, (e.ratio - 1) * 100, color=c, lw=2.2)
ax.set_xlim(-21, 27); ax.set_ylim(-12, 12)
ax.set_ylabel("% vs same weekday"); ax.set_xlabel("days from the clock change (Sunday = day 0)")
ax.text(3, 11.3, "the week after", ha="center", va="top", fontsize=13, color=INK)
fig.text(0.04, 0.885, "A  Day by day: no jump", fontsize=18, color=INK, va="top", family=DISP)
fig.text(0.40, 0.885, f"week after clocks go forward: {X['h1_spring_n_pc']:+.1f}%  (95% CI {X['h1_spring_n_lo_pc']:.1f} to {X['h1_spring_n_hi_pc']:+.1f})", color=SPR, fontsize=12.5, family="IBM Plex Mono", va="top")
fig.text(0.40, 0.862, f"week after clocks go back:    {X['h1_autumn_n_pc']:+.1f}%  (95% CI {X['h1_autumn_n_lo_pc']:.1f} to {X['h1_autumn_n_hi_pc']:+.1f})", color=AUT, fontsize=12.5, family="IBM Plex Mono", va="top")

# B: darkness by hour (autumn)
ax = fig.add_axes([0.08, 0.37, 0.38, 0.17])
hrs = np.arange(24)
ax.plot(hrs, dark["autumn|three weeks either side"], "--", color=AUT, lw=1.8)
ax.plot(hrs, dark["autumn|the week after the change"], "-", color=AUT, lw=2.6)
ax.axvspan(16.5, 18.5, color=RULE, alpha=0.6, lw=0)
ax.set_xticks([0, 6, 12, 18]); ax.set_xticklabels(["00:00", "06:00", "12:00", "18:00"])
ax.set_ylim(0, 105); ax.set_ylabel("% of collisions in the dark")
fig.text(0.04, 0.59, "B  Clocks go back: the dark\n    arrives in the rush hour", fontsize=18, color=INK, va="top", family=DISP)
ax.plot([], [], "--", color=AUT, lw=1.8, label="weeks around"); ax.plot([], [], "-", color=AUT, lw=2.6, label="week after")
ax.legend(frameon=False, fontsize=10.5, loc="center", bbox_to_anchor=(0.47, 0.36), handlelength=1.4)
fig.text(0.08, 0.322, f"17:00 to 18:59: {X['dark_autumn_evening_ctrl_pc']:.0f}% dark before, {X['dark_autumn_evening_treat_pc']:.0f}% after.\n"
         f"Collisions in those hours: {X['h2_autumn_evening_n_pc']:+.1f}% vs midday.", fontsize=12.5, color=INK, va="top")

# C: placebo strip
ax = fig.add_axes([0.62, 0.37, 0.34, 0.17])
rows = [("Week, all", "h1_n", "H1", "spring_n", "autumn_n"), ("Week, fatal", "h1_fatal", "H1", "spring_fatal", "autumn_fatal"),
        ("Evening, all", "h2_evening_n", "H2", "spring_evening_n", "autumn_evening_n")]
rng = np.random.default_rng(1)
for i, (lab, col, h, ks, ka) in enumerate(rows):
    yv = 2 - i
    ax.scatter((PL[col] - 1) * 100, yv + rng.uniform(-0.15, 0.15, len(PL)), s=26, color=GREY, alpha=0.75, lw=0)
    ax.scatter([(R[h][ks]["rr"] - 1) * 100], [yv], s=120, marker="D", color=SPR, edgecolor=INK, lw=0.8, zorder=3)
    ax.scatter([(R[h][ka]["rr"] - 1) * 100], [yv], s=130, marker="o", color=AUT, edgecolor=INK, lw=0.8, zorder=3)
ax.set_yticks([2, 1, 0]); ax.set_yticklabels([r[0] for r in rows]); ax.axvline(0, color=MUT, lw=0.8)
ax.set_xlabel("% change in the week after a Sunday")
fig.text(0.62, 0.322, f"Grey: {R['data']['placebo_weeks']} ordinary Sundays. Only the autumn\nfatal result sits near the edge.", fontsize=12.5, color=INK, va="top"); ax.set_ylim(-0.6, 2.6); ax.set_xlim(-15, 15)
fig.text(0.53, 0.59, "C  Real changes look like\n    ordinary Sundays", fontsize=18, color=INK, va="top", family=DISP)

# D: district map + legend text
geo = jload(f"{DATA}/districts_map.geojson")
tr = Transformer.from_crs(4326, 27700, always_xy=True)
cmap = LinearSegmentedColormap.from_list("d", ["#2F6A9E", "#9DB8CF", "#EDE6D3", "#E3A48F", "#B4442E"]); norm = TwoSlopeNorm(1.0, 0.8, 1.2)
ax = fig.add_axes([0.03, 0.04, 0.30, 0.235]); ax.set_aspect("equal"); ax.axis("off")
P, C, E = [], [], []
for f in geo["features"]:
    p = f["properties"]; g = f["geometry"]
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        xs, ys = tr.transform(*zip(*poly[0]))
        P.append(MPoly(np.c_[xs, ys])); C.append(cmap(norm(p["a_rr"])) if p["a_rr"] else "#DDD")
        E.append(INK if p["a_rr"] and (p["a_lo"] > 1 or p["a_hi"] < 1) else PAPER)
ax.add_collection(PatchCollection(P, facecolor=C, edgecolor=E, linewidth=[0.8 if e == INK else 0.15 for e in E]))
ax.set_xlim(0, 670000); ax.set_ylim(0, 1220000)
d = R["districts"]["autumn"]
fig.text(0.37, 0.27, "D  By district, it's noise", fontsize=17, color=INK, va="top", family=DISP)
fig.text(0.37, 0.235, f"Week after the clocks go back, 2009 to 2025, by local authority district.\n"
         f"Outlined: the {d['excl1']} of {d['districts']} whose 95% interval excludes zero.\n"
         f"Chance alone would give about {d['excl1_expected']:.0f}.", fontsize=13, color=INK, va="top", linespacing=1.4)
cax = fig.add_axes([0.37, 0.14, 0.30, 0.011])
cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap, norm=norm), cax=cax, orientation="horizontal")
cb.set_ticks([0.8, 0.9, 1, 1.1, 1.2]); cb.set_ticklabels(["-20%", "-10%", "0", "+10%", "+20%"]); cb.ax.tick_params(labelsize=11)
cax.set_title("change in collisions, week after vs weeks around", fontsize=11.5, color=MUT, loc="left")
fig.text(0.37, 0.105, f"Legend for A to C: blue diamonds and lines = clocks go forward (spring);\nred dots and lines = clocks go back (autumn); grey dots = {R['data']['placebo_weeks']} ordinary Sundays\n"
         "treated as if the clocks had changed. Shaded bands and CI: 95% intervals.", fontsize=11.5, color=MUT, va="top", linespacing=1.4)
fig.text(0.04, 0.012, "Data: Department for Transport road safety data (STATS19), Open Government Licence v3.0; boundaries ONS. "
         "\nAnalysis and chart: Dr Tristan Hotham · maps.tristanhotham.com/clock-change-crashes", fontsize=10, color=MUT, family="IBM Plex Mono", va="bottom")
out = os.path.join(ROOT, "reddit", "clock_change_crashes_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER); plt.close(fig)
from PIL import Image
print(out, Image.open(out).size)
