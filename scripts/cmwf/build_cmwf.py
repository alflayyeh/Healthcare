"""Build results/cmwf_data.csv and results/cmwf_audit.csv from raw/cmwf/ files.
Run: python3 -I scripts/cmwf/build_cmwf.py  (from the repository root)
"""
import csv, os
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "raw/cmwf")
RET = "2026-10-07"
COUNTRIES = ["USA", "GBR", "DEU", "SWE", "FRA", "NLD", "CHE", "DNK", "CAN", "JPN", "AUS"]
CIHI_NAME = {"Australia": "AUS", "Canada": "CAN", "France": "FRA", "Germany": "DEU", "Netherlands": "NLD",
             "New Zealand": "NZL", "Sweden": "SWE", "Switzerland": "CHE", "U.K.": "GBR", "U.S.": "USA"}
NOT_IN = "Country not in CMWF IHP general-adult survey (2016, 2020, 2023)"

CIHI23_URL = "https://www.cihi.ca/sites/default/files/document/cmwf-2023-data-tables-en.xlsx"
GUNJA_URL = "https://www.commonwealthfund.org/sites/default/files/2023-11/PDF_Gunja_cost_of_not_getting_care_intl_affordability_brief_exhibits.pdf"
TOP20_URL = "https://www.commonwealthfund.org/sites/default/files/2020-12/2020_Commonwealth_Fund_International_Survey_Toplines.pdf"


def country_table(sheet):
    wb = openpyxl.load_workbook(os.path.join(RAW, "cmwf-2023-data-tables-en.xlsx"), read_only=True)
    rows = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    hdr_i = next(i for i, r in enumerate(rows) if r[0] and str(r[0]).strip() == "Country")
    hdr = [str(h).replace("\n", "").replace("  ", " ") if h else h for h in rows[hdr_i]]
    out = {}
    for r in rows[hdr_i + 1:]:
        if r[0] in CIHI_NAME:
            out[CIHI_NAME[r[0]]] = dict(zip(hdr, r))
        elif r[0] and str(r[0]).startswith("By province"):
            break
    return hdr, out


rows = []

def add(ind, c, val, unit, yr, src, code, url, flags, notes):
    rows.append(dict(indicator_id=ind, country=c, value=val, unit=unit, obs_year=yr, modern_source=src,
                     dataset_code=code, url=url, retrieval_date=RET, flags=flags, notes=notes))

# ---------- F10_01 same/next-day appointment (2023), CMWF base = excl. 'did not need' ----------
hdr, t9 = country_table("9 Access to care")
for c in COUNTRIES:
    if c in t9:
        d = t9[c]
        same, nxt = d["Same day (%)"], d["Next day (%)"]
        dnn = d["Did not need to make an appointment to see doctor or nurse (%)"]
        v = 100 * (same + nxt) / (100 - dnn)
        add("F10_01", c, round(v, 1), "% of adults", 2023,
            "Commonwealth Fund 2023 International Health Policy Survey (distribution published by CIHI, data tables Q9)",
            "CIHI CMWF 2023 data tables, sheet '9 Access to care' (Q9)", CIHI23_URL, "D",
            f"Derived: (same day {same:.2f} + next day {nxt:.2f}) / (100 - did not need {dnn:.2f}); CMWF base excl. those who did not need an appointment "
            "(base verified vs Health Foundation-published 2023 values NLD 50/DEU 49/GBR 42 and vs CMWF 2020 toplines). 2023 wording adds telephone/video appointments and excludes ED visits; mixed phone/online mode.")
    else:
        add("F10_01", c, "NA", "% of adults", "", "", "", "", "", NOT_IN)

# ---------- F10_02 waited 2+ months for specialist (2023) ----------
hdr, t15 = country_table("15 Access to care")
k2 = [h for h in hdr if h and h.startswith("2 months")][0]
k1y = [h for h in hdr if h and h.startswith("1 year")][0]
for c in COUNTRIES:
    if c in t15:
        d = t15[c]
        v = d[k2] + d[k1y]
        add("F10_02", c, round(v, 1), "% of adults", 2023,
            "Commonwealth Fund 2023 International Health Policy Survey (distribution published by CIHI, data tables Q15)",
            "CIHI CMWF 2023 data tables, sheet '15 Access to care' (Q15)", CIHI23_URL, "D",
            f"Derived: '2 months to <1 year' {d[k2]:.2f} + '1 year or more' {d[k1y]:.2f}; base = adults who saw/needed a specialist in past 2 years "
            "(all responses incl. not sure/never tried in denominator). Mixed phone/online mode in 2023.")
    else:
        add("F10_02", c, "NA", "% of adults", "", "", "", "", "", NOT_IN)

# ---------- F10_04/05/06 health system views: not asked after 2016 ----------
for ind in ["F10_04", "F10_05", "F10_06"]:
    for c in COUNTRIES:
        add(ind, c, "NA", "% of adults", "", "", "", "", "",
            "Overall-view-of-health-system question (minor changes/fundamental changes/rebuild) not asked in 2020 or 2023 CMWF general-adult surveys; 2026 results due Dec 2026"
            + ("" if c not in ("DNK", "JPN") else "; " + NOT_IN))

# ---------- F11_05/06 any cost-related access problem by income ----------
# 2023: Gunja et al. Nov 2023, Exhibit 1 labelled bar values (lower-or-average income / higher income)
g23 = {"GBR": (16, 10), "NLD": (16, 6), "DEU": (16, 8), "FRA": (16, 6), "CAN": (24, 12), "CHE": (28, 18),
       "AUS": (33, 25), "NZL": (34, 16), "USA": (46, 29)}
# 2020: CMWF toplines by income, 'Skipped needed doctor visits, tests, treatments, follow-up, or prescription medicines because of cost'
t20 = {"SWE": (19, 6)}
for ind, idx, lab in [("F11_05", 0, "lower income (self-rated household income somewhat/much below national average)"),
                      ("F11_06", 1, "higher income (self-rated household income somewhat/much above national average)")]:
    for c in COUNTRIES:
        if c in g23:
            add(ind, c, g23[c][idx], "% of adults", 2023,
                "Commonwealth Fund 2023 IHP Survey; Gunja et al., The Cost of Not Getting Care (CMWF, Nov 2023), Exhibit 1",
                "doi:10.26099/jbe9-c870 Exhibit 1", GUNJA_URL, "",
                f"Any cost-related access problem past 12 months (did not visit doctor; skipped test/treatment/follow-up; did not fill Rx or skipped doses), {lab}; published labelled value.")
        elif c in t20:
            add(ind, c, t20[c][idx], "% of adults", 2020,
                "Commonwealth Fund 2020 IHP Survey top-line results by income (Doty et al., Health Affairs Dec 2020)",
                "2020 CMWF IHP toplines, by income", TOP20_URL, "",
                f"Sweden excluded from 2023 income analyses (income data could not be collected under Swedish privacy law); 2020 is latest. Same composite and income grouping, {lab}.")
        else:
            add(ind, c, "NA", "% of adults", "", "", "", "", "", NOT_IN)

os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
with open(os.path.join(ROOT, "results/cmwf_data.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["indicator_id", "country", "value", "unit", "obs_year", "modern_source", "dataset_code",
                                      "url", "retrieval_date", "flags", "notes"])
    w.writeheader(); w.writerows(rows)

ORIG = "Commonwealth Fund IHP Survey 2016 (telephone, 11 countries)"
MODE = "2023 survey mixed mode (phone in most; mostly online in SWE, CHE, USA; ~half online in GBR; registry/ABS samples in SWE/CHE/USA) vs telephone-only 2016."
audit = [
    ("F10_01", "CLOSE MODERN EQUIVALENT", ORIG, "CMWF 2023 IHP Survey (Q9 distribution published in CIHI data tables)",
     "% of adults who got a same- or next-day appointment the last time they were sick/needed care, excl. those who did not need to make an appointment", "2023",
     "Same survey series and base (excl. did-not-need); 2023 wording includes telephone/video appointments and excludes ED; value re-based from published response distribution (CMWF has no 10-country published table with this base). " + MODE,
     "CMWF base verified against Health Foundation 2023 values (NLD 50, DEU 49, GBR 42) and CMWF 2020 toplines. CIHI's published values (e.g. CAN 26, NLD 54) use narrower base excl. never able/not sure. 2020 toplines (AUS 65, CAN 38, FRA 53, DEU 75, NLD 66, SWE 33, CHE 53, GBR 52, USA 49) show a large drop to 2023. Mirror Mirror 2024 measure 7 is same-day among all adults (not comparable)."),
    ("F10_02", "CLOSE MODERN EQUIVALENT", ORIG, "CMWF 2023 IHP Survey (Q15 distribution published in CIHI data tables)",
     "% of adults who saw/needed a specialist in past 2 years who waited 2 months or longer for the appointment", "2023",
     "Same question & base; value = sum of published categories '2 months to <1 year' + '1 year or more'. " + MODE,
     "Large increases vs 2016 (e.g. DEU 3 -> 23, GBR 19 -> 42) partly reflect real deterioration and possibly mode change. Mirror Mirror 2024 uses 'waited <1 week' instead."),
]
for ind, txt in [("F10_04", "'works pretty well, only minor changes needed'"), ("F10_05", "'some good things but fundamental changes needed'"),
                 ("F10_06", "'so much wrong we need to completely rebuild it'")]:
    audit.append((ind, "UNAVAILABLE", ORIG, "none",
                  f"Overall view of health system: {txt}", "",
                  "Question dropped after 2016 from the general-adult IHP survey (absent from 2020 questionnaire/toplines and 2020 & 2023 CIHI full data tables; 2020 has a different 'rate overall performance' item).",
                  "2026 general-adult survey (online) results scheduled Dec 2026 (per Swiss FOPH) - re-check then. Older-adult (2021/2024) and PCP surveys not comparable populations."))
for ind, grp in [("F11_05", "below-average (lower) income"), ("F11_06", "above-average (higher) income")]:
    audit.append((ind, "DIRECTLY UPDATED", ORIG,
                  "CMWF 2023 IHP Survey (Gunja et al. Nov 2023, Exhibit 1); Sweden from CMWF 2020 toplines",
                  f"% of adults with {grp} with any cost-related access problem (did not visit doctor, skipped test/treatment/follow-up, or did not fill Rx/skipped doses because of cost) in past 12 months",
                  "2023 (SWE 2020)",
                  "Same composite and self-rated income-vs-national-average grouping ('somewhat/much below' vs 'somewhat/much above'). CMWF labels lower group 'lower or average income'. " + MODE,
                  "Sweden excluded from 2023 income analyses (income data could not be collected under Swedish privacy law), so SWE uses 2020 toplines (lower 19 / higher 6). 2023 values read from labelled bars in the CMWF exhibit PDF text layer (x-positions checked)."))

with open(os.path.join(ROOT, "results/cmwf_audit.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["indicator_id", "status", "original_source", "modern_source", "modern_definition", "years_used",
                "n_countries_available", "change_vs_2018", "notes"])
    for a in audit:
        n = sum(1 for r in rows if r["indicator_id"] == a[0] and r["value"] != "NA")
        w.writerow([a[0], a[1], a[2], a[3], a[4], a[5], n, a[6], a[7]])
print(len(rows), "rows")
