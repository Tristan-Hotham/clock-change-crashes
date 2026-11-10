"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Clocks_Collisions.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24112857 unless the
environment variable DOI is set:  DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Clocks_Collisions"


def tex(s): return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
def ci(c, d=3): return f"{c['rr']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"


D = R["data"]
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{Data and sample.}\\label{tab:data}\\begin{tabular}{lr}\\toprule Item & Number\\\\\\midrule\n"
      f"Reported injury collisions, 1979 to 2025 & {D['collisions']:,}\\\\\n\\quad fatal collisions & {D['fatal']:,}\\\\\n\\quad casualties & {D['casualties']:,}\\\\\n"
      f"Clock changes, 1979 to 2025 & {D['events']}\\\\\n\\quad excluded in advance (pandemic rules) & {D['events'] - D['events_main']}\\\\\n"
      f"\\quad main sample: spring / autumn & {D['spring_main']} / {D['autumn_main']}\\\\\n"
      f"Collisions in the 49-day windows (main sample) & {D['window_collisions']:,}\\\\\n\\quad of which fatal & {D['window_fatal']:,}\\\\\n"
      f"Collisions in the change weeks (main sample) & {D['change_week_collisions']:,}\\\\\n\\quad of which fatal & {D['change_week_fatal']:,}\\\\\n"
      f"Placebo Sundays / ISO weeks analysed & {D['placebo_sundays']:,} / {D['placebo_weeks']}\\\\\n"
      f"Districts in the local analysis (2009 to 2025) & {R['districts']['n_districts']}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for s, lab in (("spring", "Clocks forward (spring)"), ("autumn", "Clocks back (autumn)")):
    for y, yl in (("n", "all injury"), ("fatal", "fatal")):
        h = R["H1"][f"{s}_{y}"]
        rows += f"{lab}, {yl} & Days 0 to 6 & {ci(h)} & {h['events']} & {h['count']:,} & {h['n']:,}\\\\\n"
    for y, yl in (("n", "all injury"), ("fatal", "fatal")):
        for k, kl in (("monday", "Monday (day 1)"), ("workweek", "Days 1 to 5")):
            h = R["H1b"][f"{s}_{k}_{y}"]
            rows += f"\\quad secondary, {yl} & {kl} & {ci(h)} & {h['events']} & {h['count']:,} & {h['n']:,}\\\\\n"
    rows += "\\midrule\n"
TH1 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{H1: collisions in the week after each change, relative to the same weekdays in the three weeks either side. "
       "Rate ratios from Poisson PPML with change-by-weekday fixed effects and a bank-holiday dummy; 95\\% CI clustered by year. Count = collisions in the treatment days; N = change-days.}\\label{tab:h1}"
       "\\begin{tabular}{llrrrr}\\toprule Change and outcome & Days & Rate ratio [95\\% CI] & Changes & Count & N\\\\\\midrule\n" + rows.rstrip("\\midrule\n") + "\\\\\\bottomrule\\end{tabular}\\end{table}")
TH1 = TH1.replace("\\\\\\\\\\bottomrule", "\\\\\\bottomrule")
rows = ""
for s, lab in (("autumn", "Clocks back (autumn)"), ("spring", "Clocks forward (spring)")):
    for y, yl in (("n", "all injury"), ("fatal", "fatal")):
        for g, gl in (("evening", "Evening 17:00 to 18:59"), ("morning", "Morning 06:00 to 08:59"), ("other", "Other hours")):
            h = R["H2"][f"{s}_{g}_{y}"]
            ds = R["dark_share"].get(f"{s}_{g}")
            dtxt = f"{100*ds['ctrl']:.0f}\\% to {100*ds['treat']:.0f}\\%" if ds else ""
            rows += f"{lab}, {yl} & {gl} & {ci(h)} & {h['count']:,} & {dtxt}\\\\\n"
    rows += "\\midrule\n"
rows += "".join(f"H3 darkness contrast, {'all injury' if y == 'n' else 'fatal'} & {g.capitalize()} & {ci(R['H3'][f'{g}_{y}'])} & & \\\\\n" for y in ("n", "fatal") for g in ("evening", "morning"))
TH2 = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{H2: collisions in each hour group in the change week relative to the reference hours (10:00 to 15:59) and to the comparison weeks. "
       "PPML with day and change-by-group fixed effects; 95\\% CI clustered by year. Dark share: collisions in the group recorded in darkness, comparison weeks to change week. "
       "H3: half the autumn minus spring log difference (evening: towards darkness; morning: towards darkness), from a stacked model.}\\label{tab:h2}"
       "\\begin{tabular}{llrrr}\\toprule Change and outcome & Hours & Rate ratio [95\\% CI] & Count & Dark share\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k, lab in (("h1_spring_n", "Whole week, spring, all injury"), ("h1_autumn_n", "Whole week, autumn, all injury"),
               ("h1_spring_fatal", "Whole week, spring, fatal"), ("h1_autumn_fatal", "Whole week, autumn, fatal"),
               ("h2_spring_evening_n", "Evening, spring, all injury"), ("h2_autumn_evening_n", "Evening, autumn, all injury"),
               ("h2_spring_evening_fatal", "Evening, spring, fatal"), ("h2_autumn_evening_fatal", "Evening, autumn, fatal"),
               ("h2_spring_morning_n", "Morning, spring, all injury"), ("h2_autumn_morning_n", "Morning, autumn, all injury")):
    p = R["placebo"][k]
    parts = k.split("_"); hk = "H1" if parts[0] == "h1" else "H2"
    real = R[hk]["_".join(parts[1:])]["rr"]
    rows += f"{lab} & {real:.3f} & {round(p['share_as_large'] * p['n'])} of {p['n']} & {p['ci_excl_1']} & {p['max_abs_pc']:.1f}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Real estimates against placebo Sundays pooled by ISO week. As large: placebo estimates at least as far from 1 on the log scale. "
      "CI excl.\\ 1: placebo estimates whose own interval excludes 1. Largest: largest absolute placebo change (\\%).}\\label{tab:placebo}"
      "\\begin{tabular}{lrrrr}\\toprule Estimate & Real RR & As large & CI excl.\\ 1 & Largest (\\%)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k, v in R["robust"].items():
    lab, s, y = k.split("|")
    cells = [ci(v[g]) if g in v else "" for g in ("h1", "evening", "morning")]
    rows += f"{tex(lab)} & {s} & {'all' if y == 'n' else 'fatal'} & " + " & ".join(cells) + "\\\\\n"
TR = ("{\\scriptsize\\setlength{\\tabcolsep}{3pt}\\begin{longtable}{p{5.6cm}llrrr}\\caption{Robustness: every planned check (and two exploratory ones), whole week (H1) and evening and morning (H2) rate ratios with 95\\% CI. "
      "Nation rows use district codes, 2009 to 2025, whole-day models only.}\\label{tab:robust}\\\\\\toprule Check & Season & Outcome & Whole week & Evening & Morning\\\\\\midrule\\endhead\n"
      + rows + "\\bottomrule\\end{longtable}}")
rows = ""
for k, v in R["loo"].items():
    s, y = k.split("_")
    rows += f"{s} & {'all' if y == 'n' else 'fatal'} & {v['h1'][0]:.3f} to {v['h1'][1]:.3f} & {v['evening'][0]:.3f} to {v['evening'][1]:.3f} & {v['morning'][0]:.3f} to {v['morning'][1]:.3f}\\\\\n"
TA = ("\\begin{table}[htbp]\\centering\\small\\caption{Leave one year out: range of the planned estimates when each year's change is dropped in turn.}\\label{tab:appx}"
      "\\begin{tabular}{llrrr}\\toprule Season & Outcome & Whole week & Evening & Morning\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(f"{ROOT}/code/paper_template.tex", encoding="utf-8").read()
for k, v in (("TABLE_DATA", TD), ("TABLE_H1", TH1), ("TABLE_H2", TH2), ("TABLE_PLACEBO", TP), ("TABLE_ROBUST", TR), ("TABLE_APPX", TA)):
    t = t.replace("{{" + k + "}}", v)
t = t.replace("{{AI}}", AI)
doi = os.environ.get("DOI")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in ("DOI", "DOI_URL", "BLOG_URL")
           else fmt(get(R, m.group(1)), m.group(3)).replace("%", "\\%"), t)
t_out = t.replace("https://doi.org/10.5281/zenodo.24112857", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t_out.replace("\\{\\{DOI\\_URL\\}\\}", "")
for bad in ("—", "–", "D" "SIT", "D" "CMS", "pre-" "registered", "civil" " serv"):
    assert bad not in t_out, bad
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t_out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
print("undefined refs:", log.count("undefined"), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log),
      "| errors:", log.count("! "))
for e in ("aux", "log", "out"):
    p = f"{OUT}/{NAME}.{e}"
    if os.path.exists(p): os.remove(p)
txt = subprocess.run(["pdftotext", f"{OUT}/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0] if "References" in txt else txt
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
