# Documents used but not redistributed

These documents were used to extract or check values, but they are copyrighted or very large, so they are not included in `raw/`. The values taken from them are recorded in `results/*_data.csv`, with page or table references in the `notes` column.

| Document | Used for (indicator IDs) | Link |
|---|---|---|
| Papanicolas, Woskie & Jha, JAMA 2018, article and supplements (© AMA) | All 2018 values and definitions (`spec/indicators.csv`) | https://doi.org/10.1001/jama.2018.1150 |
| Commonwealth Fund, Gunja et al. 2023, cost-related access exhibits | F11_05, F11_06 | https://www.commonwealthfund.org/sites/default/files/2023-11/PDF_Gunja_cost_of_not_getting_care_intl_affordability_brief_exhibits.pdf |
| Commonwealth Fund 2020 International Survey toplines, questionnaire and chartpack | F11_05/F11_06 (Sweden, 2020); checking whether questions were asked | https://www.commonwealthfund.org/sites/default/files/2020-12/2020_Commonwealth_Fund_International_Survey_Toplines.pdf |
| CIHI, How Canada Compares: CMWF survey methodology notes, 2020 and 2023 | Survey bases and mode changes for F10_01, F10_02 | https://www.cihi.ca/en/commonwealth-fund-survey |
| Commonwealth Fund, Mirror, Mirror 2024 | Checked; not used (different measures) | https://www.commonwealthfund.org/publications/fund-reports/2024/sep/mirror-mirror-2024 |
| OECD (2019), *Health for Everyone? Social Inequalities in Health and Health Systems*, Annex Table 3.A.6 | F11_01 | https://www.oecd.org/content/dam/oecd/en/publications/reports/2019/09/health-for-everyone_ebff9e21/3c8385d0-en.pdf |
| OECD, *Health at a Glance 2025* (the figure spreadsheets via stat.link **are** included in `raw/pharma/`) | F9_01 (not plotted), F9_13 | https://www.oecd.org/en/publications/health-at-a-glance-2025_8f9e3f98-en.html |
| IDF Diabetes Atlas, 11th edition, country pages (age-standardised prevalence 20-79 y, 2024) | F10_14 (values in `raw/oecd_quality/idf_prevalence_2024.csv`) | https://diabetesatlas.org/data-by-location/country/united-states-of-america/ (one page per country) |
| EFPIA, *The Pharmaceutical Industry in Figures 2026* | F9_07 (not plotted) | https://www.efpia.eu/media/owqczcqz/the-pharmaceutical-industry-in-figures-2026.pdf |
| IQVIA Institute, *Global Use of Medicines 2024* | Checked for F9_01; no per-country per-capita data | https://www.iqvia.com/insights/the-iqvia-institute/reports-and-publications |
| ECDC ESAC-Net Annual Epidemiological Report 2024 | F9_13 (EU countries) | https://www.ecdc.europa.eu/sites/default/files/documents/ESAC-Net-AER-2024_rev2.pdf |
| Bloomberg (2015), drug price comparison | F9_03-F9_06 (2018 source; not updated) | https://www.bloomberg.com/graphics/2015-drug-prices/ |
| Medscape Physician Compensation Report 2026, as reported by Advisory Board | F5_05, F5_06 (United States) | https://www.advisory.com/daily-briefing/2026/06/04/physician-compensation |
| KFF State Health Facts: primary care physicians by field; total active physicians | F5_02/F5_03 (US national-definition value, not plotted) | https://www.kff.org/other/state-indicator/primary-care-physicians-by-field/ |
| Japan MHLW, Survey on Economic Conditions in Health Care (25th) | F5_05 (Japan) | https://www.mhlw.go.jp/bunya/iryouhoken/database/zenpan/jittaityousa/dl/25_houkoku_iryoukikan.pdf |
| Japan MHLW, Statistics of Physicians, Dentists and Pharmacists 2024 | F5_02/F5_03 (Japan national value, not plotted) | https://www.mhlw.go.jp/toukei/saikin/hw/ishi/24/dl/R06_1gaikyo.pdf |
| CDC NCHS, NHIS Early Release: Health Insurance Coverage 2025 | F1_17 (United States) | https://www.cdc.gov/nchs/data/nhis/earlyrelease/Health-Insurance-Coverage-Early-Release-of-Estimates-2025.pdf |
| AHRQ HCUP Statistical Briefs 223 and 287 | Checked for F7_13 (US angioplasty incl. outpatient); not available | https://hcup-us.ahrq.gov/reports/statbriefs/sb287-Ambulatory-Surgery-Overview-2019.jsp |
| OECD TL3 regional typology (2019) and Eurostat GISCO NUTS-3 boundaries | Reconstructing urban/rural region classes for F11_09/F11_10 (result in `raw/country/tl3_typology.csv`) | https://www.oecd.org/cfe/regionaldevelopment/territorial-grid.pdf ; https://ec.europa.eu/eurostat/web/gisco |

The raw database extracts in `raw/` come from OECD, the World Bank, WHO, Eurostat, CIHI and the BLS; their query URLs are in `results/*_data.csv`. Some large OECD extracts that the build scripts never read (for example the full OECD "key indicators" tables) were also left out. They can be downloaded again from the same OECD Data Explorer dataflows.
