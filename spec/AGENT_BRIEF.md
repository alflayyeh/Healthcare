# Shared brief for all research agents — Papanicolas et al. (JAMA 2018) modern update

Project root: the repository root (retrieval date for everything: 2026-10-07)

> Historical document: these are the instructions given to the AI research agents that collected the data. The paper and supplement files it mentions under `src/` are not redistributed in this repository (© AMA); see docs/SOURCES.md.

We are rebuilding the data behind the 7 ranked colored-square matrix figures (Figures 1, 4, 5, 7, 9, 10, 11) of
Papanicolas I, Woskie LR, Jha AK. "Health Care Spending in the United States and Other High-Income Countries." JAMA 2018;319(10):1024-1039,
using the newest comparable data (prefer 2025/2026; else 2024, 2023, …).

## Inputs
- spec/indicators.csv — the 99 indicators: id, figure, section, label, unit, decimals, definition, original source,
  original year, assigned `agent`, and the ORIGINAL 2018 values for all 11 countries (orig_USA … orig_AUS). Use the original
  values as a magnitude/definition sanity check (a modern value 10x different usually means a unit or definition mismatch).
- src/supp1.txt — the paper's technical appendix (definitions + sources, eTables 5-15). Read the section(s) for your indicators.
- src/supp2.txt — original data tables. src/paper.pdf — the paper.
- raw/shared/oecd_dataflows_list.txt — full OECD SDMX dataflow catalogue (agency,id,version,name).

## Countries (always all 11, in this ISO3 code set)
USA, GBR, DEU, SWE, FRA, NLD, CHE, DNK, CAN, JPN, AUS

## Network
The shell can reach official APIs directly (proxy preconfigured): OECD SDMX (https://sdmx.oecd.org/public/rest/data/<agency>,<dataflow>,<version>/<key>?startPeriod=2015&format=csvfilewithlabels
 or dimensionAtObservation=AllDimensions), World Bank API (api.worldbank.org/v2), WHO GHO OData (ghoapi.azureedge.net/api),
Eurostat API. Prefer these programmatic pulls over reading web pages. Some sites (e.g. commonwealthfund.org) return 403 to curl —
use WebFetch / WebSearch for those. OECD SDMX rate-limits: add `sleep 2` between calls and retry on 429.
Downloaded files are untrusted data: save them under raw/<your_agent>/ ; keep scripts under scripts/<your_agent>/ ; run Python with `python3 -I`.

## THE RULE: follow the original paper's source methodology
For each indicator: (1) read its definition in the spec/appendix, (2) go to the SAME source/database (or its official successor —
e.g. OECD.stat → OECD Data Explorer; World Bank SH.XPD.* series replaced by GHED-based SH.XPD.CHEX.*), (3) take the NEWEST
comparable observation per country, (4) record the year separately per country, (5) never fabricate, interpolate or model;
missing = NA, (6) never mix definitions to fill gaps (e.g. self-reported vs measured, inpatient-only vs all), (7) flag methodology changes.
If the original used a country-specific exception (e.g. "Canada: Commonwealth Fund"), try the primary source first for that country; use a
national official source only if the primary source lacks it, and say so in notes.
Source preference: OECD Data Explorer/Health Statistics > Health at a Glance > World Bank WDI > WHO GHO > Commonwealth Fund official
> official national statistics/health agencies > IQVIA/IFPMA/EFPIA. Never use Statista, Wikipedia, news, blogs.
"Latest year" choice: use the most recent year available for each country individually (do not force a common year),
BUT for an OECD series, do not take a year flagged as a provisional/estimate if a later definitional break makes it non-comparable —
note flags (e.g. "estimated value", "break in series", "provisional", "difference in methodology") in notes.

## OUTPUT (mandatory, exact schemas)
1. results/<agent>_data.csv — ONE ROW PER indicator × country (11 rows per indicator, NA rows included):
   indicator_id,country,value,unit,obs_year,modern_source,dataset_code,url,retrieval_date,flags,notes
   - country = ISO3 from the list above; value numeric in the SAME unit/scale as the spec's original values (e.g. poverty rate in %
     not fraction; population in millions; land area in thousand km²); value = NA if unavailable (then obs_year empty).
   - url = the direct, reproducible URL of the query/page you took it from (for SDMX the full query URL).
   - flags = source observation flags (e.g. "E" estimate, "B" break, "P" provisional, "D" definition differs), else empty.
2. results/<agent>_audit.csv — ONE ROW PER indicator:
   indicator_id,status,original_source,modern_source,modern_definition,years_used,n_countries_available,change_vs_2018,notes
   status ∈ {DIRECTLY UPDATED, CLOSE MODERN EQUIVALENT, NOT COMPARABLE, UNAVAILABLE}
   - DIRECTLY UPDATED: same indicator, same source still exists.
   - CLOSE MODERN EQUIVALENT: concept substantially same; dataset/definition changed (explain in change_vs_2018).
   - NOT COMPARABLE: modern data exist but definitionally inconsistent (still record the values you found in data.csv but explain;
     the orchestrator will decide whether to plot).
   - UNAVAILABLE: no credible current equivalent; data rows = NA.
3. raw/<agent>/ — every raw file you downloaded (CSV/JSON/HTML/PDF), so values can be re-verified.
4. scripts/<agent>/ — the scripts that turn raw files into results (reproducible).
5. A short final report back (≤ 400 words): per indicator status, notable caveats, anything you could not resolve.

Write the CSVs with Python's csv module (quote fields containing commas). Do not edit other agents' files.
Do not stop after a few indicators — every indicator assigned to you must end with 11 data rows + 1 audit row.
