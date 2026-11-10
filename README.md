# Do the clocks kill?

Road collisions either side of the clock changes, Great Britain 1979 to 2025. Every personal-injury road collision reported to the police (9,116,617), the week after each clock change against the same weekdays three weeks either side, with an analysis plan written before the outcome was examined.

Interactive page: https://maps.tristanhotham.com/clock-change-crashes/
Paper: https://doi.org/10.5281/zenodo.24112857
Blog post: https://blog.tristanhotham.com/2026/10/31/clock-change-crashes/
Code and data: https://github.com/Tristan-Hotham/clock-change-crashes

## Headline results

- 94 clock changes 1979 to 2025; 91 in the main sample (45 spring, 46 autumn; spring 2020, autumn 2020 and spring 2021 left out in advance because lockdown rules began or ended inside their windows).
- Week after the clocks go forward: all reported injury collisions +0.8% (95% CI -1.5 to 3.1); fatal 0.0% (95% CI -4.8 to 4.9).
- Week after the clocks go back: all collisions -0.1% (95% CI -2.3 to 2.1); fatal +4.2% (95% CI -0.3 to 8.9). 2 of 29 placebo weeks (ordinary Sundays, pooled over years) give a fatal estimate as large.
- Monday after the spring change: +2.8% (95% CI -1.1 to 6.9). Monday after the autumn change: -4.7% (95% CI -8.2 to -1.0) (secondary; not significant after correcting for eight secondary tests).
- Light: the share of 17:00 to 18:59 collisions recorded in darkness goes from 68% to 88% after the autumn change and from 15% to 4% after the spring change.
- Within days (planned, against 10:00 to 15:59): autumn evening +3.9% (95% CI 0.5 to 7.3), as large as 7 of 29 placebo weeks; spring evening +2.9% (95% CI -0.1 to 6.1) (wrong direction for a darkness effect). Combined darkness contrast for the evening: +0.5% (95% CI -1.8 to 2.8).
- Exploratory: against the three weeks before only, the autumn evening rise is 19.5%, larger than any placebo week (largest 13.1%); but spring shows a step in the same direction (8.3%) and the share keeps rising for weeks after, so the step is not clearly due to darkness.
- Robustness: whole-week all-injury estimates between -2.4% and 3.0% across the planned checks, nation splits aside. Three intervals exclude zero: comparison weeks after only, autumn -2.4% (CI -4.5 to -0.2); spring changes without Easter in the change week, +3.0% (CI 0.3 to 5.7); Scotland, 2009 to 2025, autumn +6.5% (CI 1.2 to 12.2).
- Districts (2009 to 2025): 19 of 349 autumn estimates exclude zero, about 17 expected by chance.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; 2023 districts coloured by the autumn or spring change-week ratio or by collisions per head; layers, search, full screen, popups; an hour-by-day chart. |
| `header.png` | Social card, 1200 x 630. |
| `img/` | Figures used on the page. |
| `data/events.csv` | The 94 clock changes (from the IANA tz database), exclusions, Easter flags. |
| `data/holidays.csv`, `data/placebo_sundays.csv` | Bank holidays in England and Wales; the 1,290 placebo Sundays. |
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
- Placebo: every Sunday whose window avoids real change weeks, Christmas and the pandemic, pooled by ISO week (29 weeks with at least 20 years).
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

Hotham, T. (2026) Do the clocks kill? Reported road collisions either side of the clock changes in Great Britain, 1979 to 2025. Zenodo. https://doi.org/10.5281/zenodo.24112857

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
