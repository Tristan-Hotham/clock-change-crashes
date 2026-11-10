"""Step 10: README.md, LICENSE and reddit/post.md, every number from data/results.json.
https://doi.org/10.5281/zenodo.24112857 and https://blog.tristanhotham.com/2026/10/31/clock-change-crashes/ stay for the publisher."""
from common import *

R = jload(f"{DATA}/results.json"); x = R["x"]; D = R["data"]; DS = R["districts"]


def c(v, d=3): return f"{v['rr']:.{d}f} (95% CI {v['lo']:.{d}f} to {v['hi']:.{d}f})"
def p(k):
    v = f"{x[k + '_pc']:+.1f}%"
    v = "0.0%" if v in ("-0.0%", "+0.0%") else v
    return f"{v} (95% CI {x[k + '_lo_pc']:.1f} to {x[k + '_hi_pc']:.1f})"


readme = f"""# Do the clocks kill?

Road collisions either side of the clock changes, Great Britain 1979 to 2025. Every personal-injury road collision reported to the police ({D['collisions']:,}), the week after each clock change against the same weekdays three weeks either side, with an analysis plan written before the outcome was examined.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24112857}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/clock-change-crashes/}}
Code and data: {REPO}

## Headline results

- {D['events']} clock changes 1979 to 2025; {D['events_main']} in the main sample ({D['spring_main']} spring, {D['autumn_main']} autumn; spring 2020, autumn 2020 and spring 2021 left out in advance because lockdown rules began or ended inside their windows).
- Week after the clocks go forward: all reported injury collisions {p('h1_spring_n')}; fatal {p('h1_spring_fatal')}.
- Week after the clocks go back: all collisions {p('h1_autumn_n')}; fatal {p('h1_autumn_fatal')}. {x['pl_h1_autumn_fatal_count']} of {D['placebo_weeks']} placebo weeks (ordinary Sundays, pooled over years) give a fatal estimate as large.
- Monday after the spring change: {p('h1b_spring_monday_n')}. Monday after the autumn change: {p('h1b_autumn_monday_n')} (secondary; not significant after correcting for eight secondary tests).
- Light: the share of 17:00 to 18:59 collisions recorded in darkness goes from {x['dark_autumn_evening_ctrl_pc']:.0f}% to {x['dark_autumn_evening_treat_pc']:.0f}% after the autumn change and from {x['dark_spring_evening_ctrl_pc']:.0f}% to {x['dark_spring_evening_treat_pc']:.0f}% after the spring change.
- Within days (planned, against 10:00 to 15:59): autumn evening {p('h2_autumn_evening_n')}, as large as {x['pl_h2_autumn_evening_n_count']} of {D['placebo_weeks']} placebo weeks; spring evening {p('h2_spring_evening_n')} (wrong direction for a darkness effect). Combined darkness contrast for the evening: {p('h3_evening_n')}.
- Exploratory: against the three weeks before only, the autumn evening rise is {x['xp_aut_before_pc']:.1f}%, larger than any placebo week (largest {R['exploratory']['pl_max_abs_pc']:.1f}%); but spring shows a step in the same direction ({x['xp_spr_before_pc']:.1f}%) and the share keeps rising for weeks after, so the step is not clearly due to darkness.
- Robustness: whole-week all-injury estimates between {x['rb_h1_n_min_pc']:.1f}% and {x['rb_h1_n_max_pc']:.1f}% across the planned checks, nation splits aside. Three intervals exclude zero: comparison weeks after only, autumn {x['after_autumn_pc']:+.1f}% (CI {x['after_autumn_lo_pc']:.1f} to {x['after_autumn_hi_pc']:.1f}); spring changes without Easter in the change week, {x['noeaster_spring_pc']:+.1f}% (CI {x['noeaster_spring_lo_pc']:.1f} to {x['noeaster_spring_hi_pc']:.1f}); Scotland, 2009 to 2025, autumn {x['scot_autumn_pc']:+.1f}% (CI {x['scot_autumn_lo_pc']:.1f} to {x['scot_autumn_hi_pc']:.1f}).
- Districts (2009 to 2025): {DS['autumn']['excl1']} of {DS['autumn']['districts']} autumn estimates exclude zero, about {DS['autumn']['excl1_expected']:.0f} expected by chance.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; 2023 districts coloured by the autumn or spring change-week ratio or by collisions per head; layers, search, full screen, popups; an hour-by-day chart. |
| `header.png` | Social card, 1200 x 630. |
| `img/` | Figures used on the page. |
| `data/events.csv` | The {D['events']} clock changes (from the IANA tz database), exclusions, Easter flags. |
| `data/holidays.csv`, `data/placebo_sundays.csv` | Bank holidays in England and Wales; the {D['placebo_sundays']:,} placebo Sundays. |
| `data/event_days.csv`, `data/event_hours.csv` | Event-window counts (days -21 to 27) by day, and by day and clock hour: all, fatal, dark, light, casualties. |
| `data/la_event_days.csv`, `data/la_code_map.json` | District counts in the windows, 2009 to 2025, and the code mapping to 2023 districts. |
| `data/models.json`, `data/results.json`, `data/exploratory.json` | Every estimate; every number quoted anywhere. |
| `data/hour_profile.csv`, `data/event_study.csv`, `data/event_ratios.csv`, `data/placebo.csv`, `data/dark_by_hour.json` | Figure data. |
| `data/districts.csv`, `data/districts_map.geojson`, `data/districts_summary.json`, `data/site.json` | District results and page data. |
| `code/` | Scripts in order, templates, `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the outcome was examined. |

## Method in brief

- Windows: day 0 is the change Sunday; treatment days 0 to 6; comparison days -21 to -1 and 7 to 27 (same weekdays), symmetric to cancel a linear seasonal trend.
- H1 (whole week): Poisson PPML, count ~ treat + bank holiday | change x weekday, standard errors clustered by year.
- H2 (within day): counts by hour group (evening 17:00 to 18:59, morning 06:00 to 08:59, reference 10:00 to 15:59, other) with day and change x group fixed effects, so whole-day shocks drop out.
- Placebo: every Sunday whose window avoids real change weeks, Christmas and the pandemic, pooled by ISO week ({D['placebo_weeks']} weeks with at least 20 years).
- Twelve planned robustness checks plus two exploratory ones; districts by Mantel-Haenszel ratio with empirical Bayes shrinkage.

## How to rerun

Needs Python 3 with pandas, numpy, pyfixest, statsmodels, python-dateutil, pyproj, matplotlib, Pillow, pyarrow; xelatex; node with Playwright for QA. Inputs are listed in `code/common.py` (the STATS19 aggregates and a clone of mySociety's uk_local_authority_names_and_codes in the scratch folder).

```
python3 code/01_events.py        # clock changes, holidays, placebo Sundays
python3 code/02_panels.py        # event-window panels
python3 code/03_models.py        # all planned models, placebo and robustness
python3 code/03b_exploratory.py  # exploratory before-only evening check
python3 code/04_districts.py     # districts
python3 code/05_results.py       # results.json
python3 code/06_figures.py       # figures and header
python3 code/07_paper.py         # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/08_site_data.py     # page data
python3 code/09_site.py          # index.html
python3 reddit/collage.py
python3 code/10_readme.py        # README, LICENSE, Reddit post
python3 code/11_release.py       # blog post, Zenodo files
```

## Sources and licences

- Collisions: Department for Transport, Road Safety Data (STATS19), dft-road-casualty-statistics-collision-1979-latest-published-year.csv, retrieved 2026. Contains public sector information licensed under the Open Government Licence v3.0.
- Clock-change dates: IANA Time Zone Database (Europe/London), via Python zoneinfo.
- District codes and mid-2020 populations: mySociety, uk_local_authority_names_and_codes (CC BY 4.0). Boundaries: ONS local authority districts, December 2023 (Open Government Licence v3.0).
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL).

## Citation

Hotham, T. (2026) Do the clocks kill? Reported road collisions either side of the clock changes in Great Britain, 1979 to 2025. Zenodo. {{https://doi.org/10.5281/zenodo.24112857}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
lic = """Code (code/, js/, reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
Derived data (data/): CC BY 4.0. Sources: Department for Transport STATS19 (Open Government Licence v3.0), mySociety local authority codes (CC BY 4.0), ONS boundaries (Open Government Licence v3.0).
"""
post = f"""**Title:** [OC] Do the clocks kill? Across {D['events_main']} clock changes and {x['coll_m']:.1f} million road collisions in Great Britain (1979 to 2025), the week after the change looks like any other week ({x['h1_spring_n_pc']:+.1f}% in spring, {x['h1_autumn_n_pc']:+.1f}% in autumn)

**Body:**

Every year someone warns that the clock change will bring more crashes. I took every injury collision reported to the police in Great Britain since 1979 and compared the week after each change with the same weekdays three weeks either side, with the plan written down before I looked.

- Week after the clocks go forward: {x['h1_spring_n_pc']:+.1f}% (95% CI {x['h1_spring_n_lo_pc']:.1f} to {x['h1_spring_n_hi_pc']:+.1f}).
- Week after the clocks go back: {x['h1_autumn_n_pc']:+.1f}% (95% CI {x['h1_autumn_n_lo_pc']:.1f} to {x['h1_autumn_n_hi_pc']:+.1f}).
- The dark really does move: {x['dark_autumn_evening_ctrl_pc']:.0f}% of 5 to 7pm collisions are in the dark around the autumn change, {x['dark_autumn_evening_treat_pc']:.0f}% in the week after. But collisions in those hours rise only {x['h2_autumn_evening_n_pc']:.1f}% compared with midday, and they rise in spring too, when those hours get lighter.
- Fatal collisions after the clocks go back: {x['h1_autumn_fatal_pc']:+.1f}% (CI {x['h1_autumn_fatal_lo_pc']:.1f} to {x['h1_autumn_fatal_hi_pc']:+.1f}). A hint, not a finding: {x['pl_h1_autumn_fatal_count']} of {D['placebo_weeks']} ordinary Sundays give an estimate as large.
- By district it's noise: {DS['autumn']['excl1']} of {DS['autumn']['districts']} districts stand out, about {DS['autumn']['excl1_expected']:.0f} would by chance.

This is the short-run effect of changing the clocks, not whether permanently lighter winter evenings would be safer.

Interactive map and hour-by-day chart: {PAGE}

**Source comment:**

Data: Department for Transport road safety data (STATS19), every reported personal-injury collision in Great Britain 1979 to 2025 (Open Government Licence v3.0); clock-change dates from the IANA tz database; district boundaries ONS. Method: Poisson regressions with change-by-weekday (or day) fixed effects, errors clustered by year, placebo Sundays, plan written before the analysis. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: {REPO}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README, LICENSE, post.md written")
