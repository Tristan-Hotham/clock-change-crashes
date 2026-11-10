**Title:** [OC] Do the clocks kill? Across 91 clock changes and 9.1 million road collisions in Great Britain (1979 to 2025), the week after the change looks like any other week (+0.8% in spring, -0.1% in autumn)

**Body:**

Every year someone warns that the clock change will bring more crashes. I took every injury collision reported to the police in Great Britain since 1979 and compared the week after each change with the same weekdays three weeks either side, with the plan written down before I looked.

- Week after the clocks go forward: +0.8% (95% CI -1.5 to +3.1).
- Week after the clocks go back: -0.1% (95% CI -2.3 to +2.1).
- The dark really does move: 68% of 5 to 7pm collisions are in the dark around the autumn change, 88% in the week after. But collisions in those hours rise only 3.9% compared with midday, and they rise in spring too, when those hours get lighter.
- Fatal collisions after the clocks go back: +4.2% (CI -0.3 to +8.9). A hint, not a finding: 2 of 29 ordinary Sundays give an estimate as large.
- By district it's noise: 19 of 349 districts stand out, about 17 would by chance.

This is the short-run effect of changing the clocks, not whether permanently lighter winter evenings would be safer.

Interactive map and hour-by-day chart: https://maps.tristanhotham.com/clock-change-crashes/

**Source comment:**

Data: Department for Transport road safety data (STATS19), every reported personal-injury collision in Great Britain 1979 to 2025 (Open Government Licence v3.0); clock-change dates from the IANA tz database; district boundaries ONS. Method: Poisson regressions with change-by-weekday (or day) fixed effects, errors clustered by year, placebo Sundays, plan written before the analysis. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/clock-change-crashes
