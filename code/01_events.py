"""Step 1: clock-change dates (IANA tz database via zoneinfo), bank holidays, placebo Sundays.
Outputs: data/events.csv (real changes), data/placebo_sundays.csv, data/holidays.csv."""
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
from dateutil.easter import easter
from common import *

LON = ZoneInfo("Europe/London")
days = pd.date_range(D0, periods=ND)


def offset(d):
    return dt.datetime(d.year, d.month, d.day, 12, tzinfo=LON).utcoffset().total_seconds() / 3600


ev = []
for y in range(Y0, Y1 + 1):
    yd = [d for d in pd.date_range(f"{y}-01-01", f"{y}-12-31")]
    offs = [offset(d) for d in yd]
    for i in range(1, len(yd)):
        if offs[i] != offs[i - 1]:
            # the change happens at 01:00 UTC on the Sunday, so the noon offset already differs on the change day
            d = yd[i]
            assert d.weekday() == 6, d
            ev.append({"year": y, "season": "spring" if offs[i] > offs[i - 1] else "autumn", "date": d.date().isoformat()})
E = pd.DataFrame(ev)
assert len(E) == 2 * (Y1 - Y0 + 1), len(E)
anchors = {(1979, "spring"): "1979-03-18", (1979, "autumn"): "1979-10-28", (1980, "spring"): "1980-03-16",
           (1980, "autumn"): "1980-10-26", (1995, "autumn"): "1995-10-22", (1996, "autumn"): "1996-10-27",
           (2020, "spring"): "2020-03-29", (2025, "autumn"): "2025-10-26"}
for k, v in anchors.items():
    assert E[(E.year == k[0]) & (E.season == k[1])].date.iloc[0] == v, (k, v)
E["excluded"] = [(y, s) in EXCLUDE for y, s in zip(E.year, E.season)]
E["event"] = E.year.astype(str) + "_" + E.season
print(E.to_string())

# bank holidays in England and Wales (Scotland differs slightly; England and Wales hold most collisions)
H = {}
for y in range(Y0, Y1 + 1):
    e = easter(y)
    H[e - dt.timedelta(days=2)] = "Good Friday"
    H[e + dt.timedelta(days=1)] = "Easter Monday"
    H[dt.date(y, 1, 1)] = "New Year"
    H[dt.date(y, 12, 25)] = "Christmas"
    H[dt.date(y, 12, 26)] = "Boxing Day"
    may = [dt.date(y, 5, d) for d in range(1, 32)]
    mons = [d for d in may if d.weekday() == 0]
    if y >= 1978:
        first = mons[0]
        if y == 1995: first = dt.date(1995, 5, 8)
        if y == 2020: first = dt.date(2020, 5, 8)
        H[first] = "Early May"
    last = mons[-1]
    if y == 2002: last = dt.date(2002, 6, 4)
    if y == 2012: last = dt.date(2012, 6, 4)
    if y == 2022: last = dt.date(2022, 6, 2)
    H[last] = "Spring bank holiday"
    aug = [dt.date(y, 8, d) for d in range(1, 32) if dt.date(y, 8, d).weekday() == 0]
    H[aug[-1]] = "Summer bank holiday"
for d, n in {dt.date(1981, 7, 29): "Royal wedding", dt.date(1999, 12, 31): "Millennium", dt.date(2002, 6, 3): "Golden Jubilee",
             dt.date(2011, 4, 29): "Royal wedding", dt.date(2012, 6, 5): "Diamond Jubilee", dt.date(2022, 6, 3): "Platinum Jubilee",
             dt.date(2022, 9, 19): "State funeral", dt.date(2023, 5, 8): "Coronation"}.items():
    H[d] = n
Hd = pd.DataFrame(sorted((d.isoformat(), n) for d, n in H.items()), columns=["date", "holiday"])
Hd = Hd[(Hd.date >= D0) & (Hd.date <= f"{Y1}-12-31")]
Hd.to_csv(f"{DATA}/holidays.csv", index=False)

# Easter inside a spring window (days -21 to 27)?
def in_win(date, lo=WIN[0], hi=WIN[1]):
    d0 = pd.Timestamp(date)
    return [h for h in Hd.date if lo <= (pd.Timestamp(h) - d0).days <= hi]
E["holidays_in_window"] = [len(in_win(d)) for d in E.date]
E["easter_in_window"] = [any(Hd.set_index("date").loc[h, "holiday"] in ("Good Friday", "Easter Monday") for h in in_win(d)) for d in E.date]
E["easter_in_treat_week"] = [any(Hd.set_index("date").loc[h, "holiday"] in ("Good Friday", "Easter Monday") for h in in_win(d, 0, 6)) for d in E.date]
E.to_csv(f"{DATA}/events.csv", index=False)

# placebo Sundays: window must not touch any real change week (days 0 to 6) or 18 Dec to 7 Jan, and must fit the data
real_weeks = set()
for d in E.date:
    for k in range(7):
        real_weeks.add(pd.Timestamp(d) + pd.Timedelta(days=k))
P = []
for s in days[days.weekday == 6]:
    lo, hi = s + pd.Timedelta(days=WIN[0]), s + pd.Timedelta(days=WIN[1])
    if lo < days[0] or hi > pd.Timestamp(f"{Y1}-12-31"):
        continue
    rng = pd.date_range(lo, hi)
    if any(r in real_weeks for r in rng):
        continue
    if any((r.month == 12 and r.day >= 18) or (r.month == 1 and r.day <= 7) for r in rng):
        continue
    if s.year in (2020, 2021) and s < pd.Timestamp("2021-07-31") and s > pd.Timestamp("2020-02-15"):
        continue  # pandemic restrictions, as for the real events
    P.append({"date": s.date().isoformat(), "year": s.year, "week": int(s.isocalendar()[1])})
P = pd.DataFrame(P)
P.to_csv(f"{DATA}/placebo_sundays.csv", index=False)
print(len(E), "events;", E.excluded.sum(), "excluded;", len(P), "placebo Sundays; weeks", P.week.min(), P.week.max(),
      "; easter in spring window:", int(E.easter_in_window.sum()), "in treatment week:", int(E.easter_in_treat_week.sum()))
