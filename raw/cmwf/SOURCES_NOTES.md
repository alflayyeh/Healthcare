# cmwf agent - source notes (retrieved 2026-10-07)

## Which CMWF IHP general-adult (18+) surveys exist since 2016
- 2016 (11 countries: AUS CAN FRA DEU NLD NZL NOR SWE CHE UK US) - original paper.
- 2020 (11 countries: AUS CAN FRA GER NETH NZ NOR SWE SWIZ UK US), telephone mainly. Toplines: 
  https://www.commonwealthfund.org/sites/default/files/2020-12/2020_Commonwealth_Fund_International_Survey_Toplines.pdf (saved; text top2020.txt)
  Questionnaire: .../2020-12/2020_Commonwealth_Fund_International_Survey_Questionnaire.pdf (saved; q2020.txt) -> NO "overall view of health system (minor changes / fundamental changes / rebuild)" question.
  CIHI 2020 data tables (all common questions, 11 countries): https://www.cihi.ca/sites/default/files/document/how-canada-compares-cmwf-survey-2020-data-tables-en.xlsx (saved). Q53 = "rate overall performance of health care system" (different question, 5-point rating) - not the 3-statement views question.
- 2023 (10 countries: AUS CAN FRA GER NETH NZ SWE SWIZ UK US; Norway dropped). Fieldwork Mar 6-Aug 20 2023. Mixed mode: phone (overlapping landline/cell) in most; SWE & CHE registry address-based samples mostly ONLINE; US ABS mostly online; UK ~half online.
  CIHI 2023 data tables: https://www.cihi.ca/sites/default/files/document/cmwf-2023-data-tables-en.xlsx (saved) - full response distributions for all common questions, 10 countries. Health-system-views question NOT asked.
  CIHI 2023 quick stats: https://www.cihi.ca/sites/default/files/document/cmwf-2023-quick-stats-en.xlsx (saved) - Table 7a same/next-day with base excluding never able/did not need/not sure/declined (CIHI convention, differs from CMWF).
  CIHI methodology notes: how-canada-compares-cmwf-survey-2023-meth-notes-en.pdf (saved, meth2023.txt).
- 2026 general population survey: in field; Swiss FOPH (BAG) page https://www.bag.admin.ch/de/ihp-befragungen-wohnbevoelkerung-ab-18-jahren states "International Health Policy Survey 2026 ... Wohnbevölkerung ab 18 Jahren ... Befragung per Web (CAWI) ... Veröffentlichung der Ergebnisse: Dezember 2026" -> NOT yet published at retrieval date. Also: Switzerland stops participating from 2027.
- NOT comparable populations (not used): 2017, 2021, 2024 surveys of adults 65+ (older adults); 2019, 2022, 2025 surveys of primary care physicians (2025 PCP survey: BMG/RKI Germany page "IHP-Survey 2025 - RKI startet Umfrage unter Hausärztinnen und Hausärzten").
- Japan and Denmark never participated in the general-adult IHP surveys 2016-2023 -> NA.

## Mirror, Mirror 2024 (Blumenthal et al., Sept 2024)
- PDF saved: Blumenthal_mirror_mirror_2024_final_v4.pdf (text mm2024_v4.txt), v2 also saved.
- Appendix 4 raw data from 2023 survey: measure 7 "Saw a doctor or nurse on the same or next day, the last time they needed medical care" values (AUS 19, CAN 14, FRA 21, GER 30, NETH 27, NZ 17, SWE 17, SWIZ 21, UK 30, US 21) equal the CIHI "same day" share among ALL respondents -> different measure/base (not used). Measure 8 = waited <1 week for specialist (not 2 months). Measure 1 combines medical + dental cost barriers (not used). No health-system-views measure.
- Income definition (MM2024 methods): "somewhat below"/"much below" average = lower or average income; "somewhat above"/"much above" = higher income. Sweden excluded from income analyses (privacy law prevents collection of income data).

## Gunja et al. Nov 2023 (cost-related access problem by income, 2023 survey) - see gunja2023_page_notes.md, gunja2023_exhibits.pdf/.txt

## Verification of F10_01 base (CMWF convention)
- 2020: CMWF toplines same/next-day (AUS 65, CAN 38, SWE 33, US 49) reproduced from CIHI 2020 distribution as (same+next)/(100 - did not need - went to urgent care) -> CMWF base excludes only those who did not need an appointment (and urgent-care-only); never-able & not-sure stay in denominator.
- 2023: Health Foundation briefing "Feeling the pressure: what the 2023 Commonwealth Fund survey reveals..." (CMWF co-funder; https://www.health.org.uk/reports-and-analysis/briefings/feeling-the-pressure-what-the-2023-commonwealth-fund-survey-reveals) reports same/next-day among adults who needed appointment: NETH 50, GER 49, UK 42. CIHI 2023 Table 9 rebased as (same+next)/(100 - did not need) gives NETH 50.2, GER 49.3, UK 42.3 -> matches. CIHI's own published figures (NETH 54, GER 51, UK 47, CAN 26 ...) use a narrower base (also excl. never able/not sure/declined).
