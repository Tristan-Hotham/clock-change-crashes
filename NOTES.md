# clock-change-crashes: working notes and analysis plan

"Do the clocks kill? Road collisions either side of the clock changes". Author Dr Tristan Hotham, Independent researcher.

## Status

- Phase 1 (this section, written first, 2026): data inspected only for structure and annual totals (counts per year, missing codes). **No counts around any clock change have been computed or looked at.** The plan below is pre-specified in a written plan before the outcome. Anything not in it is labelled exploratory.
- Phase 2: analysis, paper and release (log at the end).

## Data facts found in phase 1

- Input: compact aggregates of DfT STATS19 `dft-road-casualty-statistics-collision-1979-latest-published-year.csv` (9,116,617 collisions, 8 malformed rows dropped by the lead). `coll_A.i32` int32 [17532 days from 1979-01-01][25 hour slots][3 severity][3 light] = collisions; `coll_K.i32` the same shape = casualties; `coll_LA.u16` [days][460 slots] collisions by `local_authority_ons_district`.
- The file holds collisions from 1979-01-01 to 2025-12-31 (2025 has 101,525 collisions), so the study covers 1979 to 2025, 47 years, not 1979 to 2024. Hour slot 24 (time missing) is empty: every collision has a time. Light "missing/unknown" is under 0.1% in every year (most in 1989: 779).
- Local authority codes are missing ("-1") for every collision before 1994 and part of 1994 to 1996. Codes for areas abolished in 2009 (Bedfordshire, Cheshire, Durham districts, Buckinghamshire county code) appear only up to 2008. From 2009 every code maps to a 2023 local authority district through mySociety's `uk_local_authority_names_and_codes` (CC BY 4.0, `replaced-by` column: 2019 Dorset, BCP, Suffolk, Somerset West and Taunton; 2020 Buckinghamshire; 2021 Northamptonshire; 2023 Cumberland, Westmorland and Furness, North Yorkshire, Somerset), plus `EHEATHROW` to Hillingdon (E09000017) and the 2025 codes E08000038 (Barnsley) and E08000039 (Sheffield) to E08000016 and E08000019. So all local-authority analysis uses 2009 to 2025.
- Severity: fatal is defined consistently throughout (death within 30 days). The serious/slight split changed as police forces moved to CRASH (from 2012 onwards) and the injury-based method; serious counts rise from 2016. This does not bias within-year comparisons of a few weeks much, but the long-run analysis uses fatal and all-injury collisions only, never serious alone.

## The clock changes

Dates come from the IANA time zone database (`zoneinfo` Europe/London), not hand-typed: spring change = the Sunday on which the UTC offset goes from 0 to +1 hour, autumn change = +1 to 0. 1979: 18 March and 28 October; 1980: 16 March and 26 October; from 1981 the last Sunday of March; autumn on the Sunday after the fourth Saturday of October up to 1995, and the last Sunday of October from 1996 (EU harmonisation). The script prints them all and asserts these anchors. 47 years x 2 = 94 events.

## Pre-specified analysis plan

**Unit.** Event e (a year and a season) x calendar day d x clock hour h (local time as recorded by the police). Counts of reported personal-injury collisions in Great Britain.

**Windows.** Day 0 = the change Sunday. Treatment week = days 0 to 6 (Sunday to Saturday). Comparison weeks = the same weekdays 1 to 3 weeks before (days -21 to -1) and 1 to 3 weeks after (days 7 to 27). Symmetric windows cancel a linear seasonal trend in traffic and daylight. Day-of-week effects are absorbed by event x weekday fixed effects.

**Pre-specified exclusions.** Spring 2020 (the first lockdown began on 23 March 2020, inside the window), autumn 2020 (the second English lockdown began on 5 November 2020, inside the comparison weeks) and spring 2021 (the stay-at-home rule ended in England on 29 March 2021, the day after the change). Main sample: 91 events. Robustness: include them.

**Holidays.** Good Friday, Easter Monday (England and Wales; Easter often falls inside the spring window), the early May and late May bank holidays, and the August bank holiday are flagged by date; whole-day models include a bank-holiday dummy. The hour models use day fixed effects, which absorb any whole-day shock (weather, holidays, strikes).

**Outcomes.** All reported injury collisions (main) and fatal collisions (main, long-run comparable). Casualties as a robustness check.

### H1. Whole-day effect ("do the clocks kill?")
Collisions in the treatment week compared with the comparison weeks. Poisson pseudo-maximum likelihood on daily counts: count ~ treat + bank holiday | event x weekday fixed effects, standard errors clustered by year (spring and autumn events of the same year share a cluster). Rate ratio with 95% CI, spring and autumn separately, fatal and all-injury separately (4 estimates). Secondary: the Monday after the spring change alone (the sleep-loss hypothesis: day 1 vs the comparison Mondays), and the first working week (days 1 to 5).
Against H1: rate ratios whose CIs include 1, or placebo Sundays producing estimates of the same size as often as the real changes.

### H2. Light moves between hours (the mechanism)
Day fixed effects absorb whole-day totals, so only the share of a day's collisions falling in each hour is compared. Pre-specified hour groups (clock time): **evening** 17:00 to 18:59, **morning** 06:00 to 08:59, **reference** 10:00 to 15:59 (light in both weeks), other hours (night 20:00 to 05:59 and the shoulders 09, 16, 19) as a separate group. Model: count ~ treat x group | day + event x group fixed effects, clustered by year. Predictions: autumn evening rate ratio > 1 (evenings get dark), spring evening < 1; morning the reverse (spring morning > 1, autumn morning < 1). Also the full hour-by-hour version (24 coefficients relative to the reference hours) for the figure. Manipulation check: the share of evening (17:00 to 18:59) collisions that the police recorded in darkness, comparison vs treatment weeks.
Against H2: evening and morning ratios with the wrong sign or CIs including 1, fatal and all-injury.

### H3. Darkness risk (secondary, the case/control hour method)
Following the case-hour/control-hour logic of Johansson, Wanvik and Elvik (2009) and Sullivan and Flannagan (2002): for the evening hours, the darkness risk ratio is the ratio of rate ratios (dark period over light period) for the evening hours relative to the reference hours, i.e. combine the autumn ratio (light to dark) and the inverse of the spring ratio (dark to light). Report it with a CI by the delta method on the pooled log coefficients, and divide by the change in the share recorded dark to estimate the per-hour darkness effect (exploratory scaling). Fatal and all-injury.

### H4. Net effect
Do the evening and morning changes cancel? The change in expected collisions per change (evening excess plus morning excess, in counts per treatment week) from H2 coefficients times comparison-week counts, per season. Exploratory arithmetic, not a test.

### Event study (figure)
For each event and day -21 to +27, the log ratio of the day's count to the mean count of the same weekday in the comparison weeks (excluding the day itself), averaged across events, with 95% intervals from a bootstrap over years (2,000 draws). All-injury and fatal; and the same for evening hours relative to reference hours.

### Placebo
Every Sunday whose window (days -21 to +27) does not overlap any real change week (days 0 to 6) nor 18 December to 7 January, treated as a fake change for every year (same models H1 and H2, pooled across years). Report the real estimates' rank in the placebo distribution (two-sided share of placebo |log RR| at least as large).

### Robustness (planned)
1. Comparison weeks only 1 week either side; 2. only weeks before; 3. only weeks after; 4. treatment window days 1 to 5 (working days) only; 5. include the 2020 and 2021 events; 6. casualties instead of collisions; 7. by era: 1979 to 1995, 1996 to 2010, 2011 to 2025; 8. leave one year out (range); 9. drop events with Easter in the window (spring); 10. by nation (England, Scotland, Wales) from the local-authority codes, whole-day only, 2009 to 2025 (hour data are national); 11. negative binomial instead of Poisson for H1; 12. evening defined as 16:00 to 18:59 (autumn) and 18:00 to 19:59 (spring) following each season's sunset.

### Local authorities (map, descriptive)
Whole-day autumn rate ratio per 2023 district (2009 to 2025 events; Poisson as H1 per district), shrunk towards the national estimate by empirical Bayes (normal model on log RR with the between-district variance estimated by the method of moments), with the raw estimate and CI in popups. Also collisions per 100,000 people per year (2015 to 2025, mySociety 2020 population). Expect noise: the map must say how many districts have CIs excluding 1 and how many would by chance.

### What would count against "the clocks kill"
H1 ratios near 1 with tight CIs, and a reallocation in H2 that nets to near zero (H4). The headline will be whatever the planned specifications give.

### Not in the data
The 1968 to 1971 British Standard Time experiment (clocks on GMT+1 all year) predates STATS19 records here; it is discussed from the literature only. No traffic volume by hour is available, so rates are per collision, not per vehicle-kilometre: the design assumes clock-time travel patterns stay the same across the change (people keep to clock time).

## Log

- 2026, phase 2 (after running the plan):
  - Deviation 1: planned robustness 9 ("drop events with Easter in the window") was impossible as written: every spring window (days -21 to 27) contains Good Friday or Easter Monday. Replaced, before looking at its result, by "drop spring events with Good Friday or Easter Monday in the change week" (19 of 47 springs have one).
  - Deviation 2: the negative binomial check drops the holiday dummy in autumn (no bank holidays in any autumn window), as the Poisson models already do.
  - Added after the first run and labelled exploratory: (a) reference hours 10:00 to 13:59 (the planned 10:00 to 15:59 includes the end of the school day; the English October half-term often falls in the week after the autumn change); (b) weekends only for the hour models (no commute or school run).
  - Facts found while running: the change night itself has a missing hour (spring, 01:00 to 01:59) and a doubled hour (autumn), visible in the hour-by-hour profile at 01:00 to 04:00; these fall in the "other" group and do not touch the evening or morning groups. Placebo Sundays pooled by ISO week: 29 weeks with at least 20 years. The hour-group placebo estimates are often far from 1 (school holidays, bank holidays and the start of summer holidays move traffic between hours), which is why every hour result is reported against the placebo distribution.
  - Main results (all in data/results.json): whole-day change-week rate ratios spring 1.008 (0.985 to 1.031), autumn 0.999 (0.977 to 1.021); fatal spring 1.000, autumn 1.042 (0.997 to 1.089; 2 of 29 placebo weeks as large). Autumn evening 17:00 to 18:59 relative to 10:00 to 15:59: 1.039 (1.005 to 1.073), as large in 7 of 29 placebo weeks; darkness share of evening collisions 68% to 88%. Spring evening 1.029 (wrong sign for the darkness hypothesis). Districts: 19 of 349 autumn ratios exclude 1, about 17 expected by chance.
  - Exploratory (added after seeing the event-study figure, code/03b_exploratory.py): the evening share steps up on day 0 in both seasons and keeps rising afterwards. Before-only comparison: autumn evening +19.5%, larger than all 29 placebo weeks (max 13.1%); spring +8.3% (wrong direction for darkness). Reported in the paper (Section 6.3), blog and page as exploratory; the planned symmetric estimate stays the main result.
